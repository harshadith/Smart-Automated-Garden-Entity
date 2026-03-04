import os
import json
import numpy as np
import tensorflow as tf
import streamlit as st
from PIL import Image
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None
import time
import base64
import io
from groq import Groq
import requests

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="Smart Automated Garden Entity",
    page_icon="🌿",
    layout="wide"
)

# --- LIVE TELEMETRY DASHBOARD ---
st.sidebar.header("📡 Live S.A.G.E. Telemetry")

# Allow dynamic IP input in the sidebar (defaults to localhost if empty, to prevent crashes)
nodemcu_ip_input = st.sidebar.text_input(
    "NodeMCU IP Address", 
    value="", 
    placeholder="e.g., 192.168.1.10"
)

# --- 5. DATA FETCHING ---
def get_arduino_data(ip_address):
    """
    Fetches live JSON data wirelessly from the NodeMCU web server using the provided IP.
    """
    if not ip_address:
        st.sidebar.warning("Please enter a NodeMCU IP address above.")
        return None

    url = f"http://{ip_address}/data"
    
    try:
        # Send an HTTP GET request to the NodeMCU
        response = requests.get(url, timeout=3)
        
        # If successful (HTTP 200), return the parsed JSON
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        # This catches errors if the NodeMCU is turned off, wrong IP, or disconnected
        st.sidebar.error("Wireless Connection Failed. Assuming standard indoor conditions.")
        return None

# Add a button to manually refresh the live data
if st.sidebar.button("🔄 Refresh Sensors", use_container_width=True):
    with st.spinner("Connecting to S.A.G.E. Node..."):
        # Pass the dynamic IP input to the function
        live_data = get_arduino_data(nodemcu_ip_input)
        
    if live_data:
        # Update the global sensor_data variable so the AI can use it later
        st.session_state['sensor_data'] = live_data 
        
        # Display beautiful metrics in the sidebar
        st.sidebar.success("Connection Established!")
        st.sidebar.metric(label="🌡️ Temperature", value=f"{live_data.get('temp', 'N/A')} °C")
        st.sidebar.metric(label="💧 Humidity", value=f"{live_data.get('humidity', 'N/A')} %")
        st.sidebar.metric(label="🌱 Soil Moisture", value=f"{live_data.get('soil', 'N/A')} %")
        st.sidebar.metric(label="☀️ Light Level", value=f"{live_data.get('light', 'N/A')}")
    else:
        st.sidebar.error("NodeMCU Offline or Invalid IP.")

# Initialize the sensor data in Streamlit's session state if it doesn't exist yet
if 'sensor_data' not in st.session_state:
    st.session_state['sensor_data'] = None

working_dir = os.path.dirname(os.path.abspath(__file__))
model_path = f"{working_dir}/trained_model/plant_disease_prediction_model.h5"

# --- 2. GOOGLE GEMINI SETUP ---
# Try to get the key from .streamlit/secrets.toml
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    # If not found, allow manual entry in sidebar for testing
    api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if api_key and genai is not None:
    genai.configure(api_key=api_key)

# --- 3. LOAD MODEL & CLASSES ---
@st.cache_resource
def load_local_model():
    # compile=False prevents warnings about optimizer state
    return tf.keras.models.load_model(model_path, compile=False)

try:
    model = load_local_model()
except Exception as e:
    st.error(f"Error loading model: {e}")

# Load class indices
try:
    class_indices = json.load(open(f"{working_dir}/class_indices.json"))
except Exception as e:
    st.error(f"Error loading class_indices.json: {e}")
    class_indices = {}

# --- 4. PREPROCESSING & PREDICTION FUNCTIONS ---
def load_and_preprocess_image(image_file, target_size=(224, 224)):
    """
    Loads an image file object, resizes, and preprocesses it for the model.
    """
    img = Image.open(image_file)
    img = img.resize(target_size)
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array.astype('float32') / 255.
    return img_array

def predict_image_class(model, image_file, class_indices):
    preprocessed_img = load_and_preprocess_image(image_file)
    predictions = model.predict(preprocessed_img)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    
    # Retrieve class name from JSON (assuming keys are strings like "0", "1")
    predicted_class_name = class_indices.get(str(predicted_class_index), "Unknown Disease")
    confidence = np.max(predictions)
    return predicted_class_name, confidence

# --- 6. GEMINI + GROQ FALLBACK AI ADVICE (THE ARBITER) ---
def get_expert_advice(disease_name, confidence, image_file, sensors):
    """
    Tries Gemini first. If it hits a rate limit (429), it instantly 
    converts the image and sends it to Groq (Llama 4 Vision) as a fallback.
    """
    google_key = st.secrets.get("GOOGLE_API_KEY")
    groq_key = st.secrets.get("GROQ_API_KEY")

    # 1. Format Sensor Context
    if sensors:
        sensor_context = f"Soil Moisture: {sensors.get('soil', 'N/A')}%, Temp: {sensors.get('temp', 'N/A')}°C, Humidity: {sensors.get('humidity', 'N/A')}%"
    else:
        sensor_context = "Not Connected (Assume standard indoor conditions)."

    # 2. The Arbiter Prompt
    prompt = f"""
    You are S.A.G.E., an expert AI plant pathologist.
    
    **INPUTS:**
    1. **Local CNN Prediction:** {disease_name} (Confidence: {confidence*100:.1f}%)
    2. **Live Sensors:** {sensor_context}

    **YOUR TASK:**
    Look at the attached image. Do not just accept the CNN prediction blindly. Evaluate it against the image and the sensors.
    - If the CNN says 'Wilt' but soil moisture is very low (< 20%), overrule it and diagnose 'Dehydration'.
    - If the CNN says a Fungal disease, verify if the humidity is high enough to support fungus.
    - If the CNN is clearly wrong based on your visual analysis of the image, correct it.

    **Provide the BEST, FINAL output using EXACTLY this markdown structure:**
    
    ### 🏆 Final Diagnosis: [State the true condition clearly]
    **System Agreement:** [State either: "Aligned with CNN" / "Overruled CNN due to Sensor Data" / "Overruled CNN due to Visual Evidence"]
    
    ### 🔬 Reasoning
    [1-2 sentences explaining exactly how you combined the image, CNN, and sensors to reach this conclusion.]

    ### 💊 S.A.G.E. Action Plan
    - **Immediate:** [Specific step 1]
    - **Environmental:** [Specific step 2 involving water/temp/light]
    """

    # Prepare Image
    image_file.seek(0)
    img = Image.open(image_file)

    # ==========================================
    # ATTEMPT 1: GOOGLE GEMINI
    # ==========================================
    gemini_error = None
    if genai is not None and google_key:
        try:
            model_gemini = genai.GenerativeModel('gemini-2.0-flash-lite')
            response = model_gemini.generate_content([prompt, img])
            return response.text
        except Exception as error:
            gemini_error = error
    else:
        if genai is None:
            gemini_error = "google-generativeai is not available in the active Python interpreter."
        elif not google_key:
            gemini_error = "GOOGLE_API_KEY is missing."

    if not groq_key:
        return f"⚠️ **Gemini unavailable:** {gemini_error}\n\n*(No Groq API key found to trigger fallback.)*"

    # ==========================================
    # ATTEMPT 2: GROQ FALLBACK (Llama 4 Vision)
    # ==========================================
    try:
        client = Groq(api_key=groq_key)
        
        # Groq requires the image to be Base64 encoded
        buffered = io.BytesIO()
        if img.mode != 'RGB':
            img = img.convert('RGB') # Fix for PNGs with transparency
        img.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.2, # Low temperature for factual medical advice
        )
        
        groq_response = chat_completion.choices[0].message.content
        if groq_response:
            return groq_response + "\n\n--- \n*⚡ S.A.G.E. Fallback Engaged: Report generated via Groq (Llama 4 Vision) because Gemini was unavailable.*"
        else:
            return "⚠️ **Groq returned empty response.**"
        
    except Exception as groq_error:
            return f"⚠️ **Total System Failure.**\nGemini Error: {gemini_error}\nGroq Error: {groq_error}"

# --- 7. STREAMLIT APP LAYOUT ---
st.title('🌿 S.A.G.E. | Plant Disease Classifier')

uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])

if uploaded_image is not None:
    # Display the image
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = Image.open(uploaded_image)
        # Resize for display only
        resized_img = image.resize((300, 300)) 
        st.image(resized_img, caption="Uploaded Leaf")

    with col2:
        if st.button("🔍 Run Full S.A.G.E. Diagnostics", type="primary", use_container_width=True):
            
            # --- PROGRESS BAR UX ---
            progress_text = "Step 1: Running Local CNN..."
            my_bar = st.progress(0, text=progress_text)
            
            # 1. Get CNN Prediction silently
            prediction, conf = predict_image_class(model, uploaded_image, class_indices)
            my_bar.progress(40, text="Step 2: Fetching Sensor Telemetry...")
            
            # ==========================================
            # FETCH LIVE WIRELESS DATA FROM NODEMCU
            # ==========================================
            # Fetch data right before analysis, using the dynamic IP
            current_sensor_data = get_arduino_data(nodemcu_ip_input)
            
            # 2. Add slight delay for UX (Optional, looks cool)
            time.sleep(0.5)
            my_bar.progress(70, text="Step 3: AI Fusing Vision + Sensors...")

            # 3. Get the Ultimate Fused Output from Gemini/Groq
            final_report = get_expert_advice(prediction, conf, uploaded_image, current_sensor_data)
            
            my_bar.progress(100, text="Diagnostics Complete!")
            time.sleep(0.5)
            my_bar.empty() # Remove the progress bar
            
            # --- DISPLAY THE BEST OUTPUT ---
            st.success("✅ Analysis Complete")
            
            # Display the Fused AI Output as the main result
            st.markdown(final_report)

            # Keep the raw CNN data hidden in an expander for transparency/debugging
            with st.expander("⚙️ View Raw CNN & Sensor Data"):
                st.write(f"**Raw CNN Prediction:** {prediction}")
                st.write(f"**CNN Confidence:** {conf*100:.2f}%")
                if current_sensor_data:
                    st.json(current_sensor_data)
                else:
                    st.write("No active sensor connection. Assumed standard indoor conditions.")