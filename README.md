🌱 S.A.G.E. (Smart Automated Garden Entity)
Plant Disease Prediction: AIoT Cognitive Fusion Framework

📖 Overview
This repository contains the complete software and AI architecture for an advanced Plant Disease Classification system. Moving beyond traditional isolated computer vision, this project introduces a "Cognitive Fusion" framework. It utilizes a localized Convolutional Neural Network (CNN) to visually diagnose plant leaves and cross-references those predictions with live, real-time microclimate telemetry (temperature, humidity, soil moisture) gathered via an edge hardware node.

A Large Multimodal Model (LMM) Arbiter acts as a digital botanist, verifying the CNN's visual hypothesis against the physical constraints of the plant's environment to eliminate false positives caused by abiotic stress (e.g., severe dehydration mimicking an infection).

🔗 Dataset & Pre-trained Model
Dataset: PlantVillage Dataset (Kaggle) - Features 54,305 high-resolution images across 38 distinct crop/disease classes.

Trained CNN Model (.h5): Download the Optimized Model Here (Note: Place this file in the app/trained_model/ directory before running the app).

✨ Key Features
Robust CNN Architecture: Custom-trained Keras model achieving high baseline categorical accuracy for 38 distinct botanical classes.

Dual-Engine AI Arbiter: Integrates Google Gemini 2.0 Flash-Lite with an automated fault-tolerant fallback to Groq's LPU endpoints (Llama 4 Scout) to guarantee zero-downtime inference.

Live IoT Telemetry: Seamlessly fetches real-time environmental data (JSON) asynchronously from an ESP8266 microcontroller over a local WLAN.

Interactive Dashboard: A low-latency Streamlit GUI providing real-time sensor metrics, image uploads, and human-readable, contextually justified remediation plans.

🛠️ Technology Stack
Machine Learning: TensorFlow, Keras, NumPy, Pandas, OpenCV

Generative AI: Google Generative AI SDK, Groq Cloud API

Frontend / UI: Streamlit

Edge Hardware (IoT): NodeMCU ESP8266, DHT11, LM393 Soil Moisture Sensor, LDR, C++ (Arduino IDE)

🚀 Installation & Local Setup
1. Clone the Repository
Bash
git clone https://github.com/YOUR_USERNAME/plant-disease-prediction-cnn-deep-leanring-project.git
cd plant-disease-prediction-cnn-deep-leanring-project
2. Set Up Virtual Environment (Recommended)
Bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
3. Install Dependencies
Bash
pip install -r app/requirements.txt
4. Configure API Keys
You must securely provide your API keys for the Arbiter to function. Create a .streamlit/secrets.toml file in the root directory:

Ini, TOML
GOOGLE_API_KEY = "your_gemini_key_here"
GROQ_API_KEY = "your_groq_key_here"
5. Run the Application
Bash
streamlit run app/main.py
🧠 Hardware Implementation Notes
To replicate the live sensor telemetry, flash the NodeMCU/IoT.ino firmware to an ESP8266. Ensure the NodeMCU is connected to the same local Wi-Fi network as your host machine. Update the NODEMCU_IP variable inside main.py to match the local IP assigned to your microcontroller.