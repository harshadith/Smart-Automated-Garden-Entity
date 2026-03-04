# 🌱 S.A.G.E. (Smart Automated Garden Entity)
> **An AIoT Cognitive Fusion Framework for Plant Disease Prediction**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0%2B-orange.svg)](https://www.tensorflow.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-red.svg)](https://streamlit.io/)
[![Hardware](https://img.shields.io/badge/Hardware-NodeMCU_ESP8266-lightgrey.svg)]()

---

## 📖 Overview
This repository contains the complete software and hardware architecture for an advanced Plant Disease Classification system. Moving beyond traditional, isolated computer vision, S.A.G.E. introduces a **"Cognitive Fusion"** framework. 

It utilizes a localized Convolutional Neural Network (CNN) to visually diagnose plant leaves and mathematically cross-references those predictions with live microclimate telemetry (temperature, humidity, soil moisture) gathered via an edge hardware node. A Generative AI Arbiter acts as a digital botanist, verifying the CNN's visual hypothesis against the physical constraints of the environment to eliminate false positives caused by abiotic stress.

---

## 🔗 Dataset & Pre-trained Model
* **Dataset:** [PlantVillage Dataset (Kaggle)](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset) - Features 54,305 high-resolution images across 38 distinct crop/disease classes.
* **Trained CNN Model (.h5):** [Download the Optimized Model Here](https://drive.google.com/file/d/1OTql7BlDWAeyRXr5UAk3UUxpCnwBacA4/view?usp=sharing) 
  * *(Note: Place this `.h5` file inside the `app/trained_model/` directory before running the application).*

---

## ✨ Key Technical Features
* **Robust CNN Architecture:** Custom-trained Keras model achieving high baseline categorical accuracy for 38 distinct botanical classes.
* **Dual-Engine AI Arbiter:** Integrates Google Gemini 2.0 Flash-Lite with an automated fault-tolerant fallback to Groq's LPU endpoints (Meta Llama 4 Scout) to guarantee zero-downtime diagnostic reasoning.
* **Live IoT Telemetry:** Seamlessly fetches real-time environmental data (JSON payload) asynchronously from an ESP8266 microcontroller over a local WLAN.
* **Hardware Optimization:** Implements a dynamic voltage-switching protocol at the edge node, reducing the active duty cycle of resistive soil sensors to 5% to prevent galvanic corrosion.

---

## 🛠️ Technology Stack
| Domain | Technologies Used |
| :--- | :--- |
| **Machine Learning** | TensorFlow, Keras, NumPy, OpenCV |
| **Generative AI** | Google Generative AI SDK, Groq Cloud API (Llama 3.2/4 Vision) |
| **Frontend UI** | Streamlit |
| **Edge Hardware** | NodeMCU ESP8266, DHT11, LM393 Soil Moisture Sensor, C++ |

---

## 🚀 Local Setup & Installation

**1. Clone the Repository**
```bash
git clone [https://github.com/harshadith/Smart-Automated-Garden-Entity.git](https://github.com/harshadith/Smart-Automated-Garden-Entity.git)
cd Smart-Automated-Garden-Entity
```

**2. Set Up Virtual Environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
```

**3. Install Dependencies**
```Bash
pip install -r app/requirements.txt
```

**4. Configure API Keys (Critical)**
Create a .streamlit/secrets.toml file in the root directory to store your LMM API keys securely:

```Ini, TOML
GOOGLE_API_KEY = "your_gemini_key_here"
GROQ_API_KEY = "your_groq_key_here"
```

**5. Launch the Dashboard**
```Bash
streamlit run app/main.py
```

# Hardware Implementation Notes
To replicate the live sensor telemetry, flash the NodeMCU/IoT.ino firmware to a standard ESP8266 board. Ensure the NodeMCU is connected to the same local Wi-Fi network as your host machine. Update the NODEMCU_IP string variable inside app/main.py to match the local IP assigned to your microcontroller.