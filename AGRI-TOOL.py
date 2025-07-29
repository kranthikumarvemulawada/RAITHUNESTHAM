import streamlit as st
from PIL import Image
import io
import speech_recognition as sr
from google import generativeai as genai
import requests
from gtts import gTTS
import tempfile
import datetime
import geocoder

# --- Configure Gemini API ---
genai.configure(api_key="AIzaSyADAFye4AdI16sPJoxIx9KtnuZQTg3dmwI")
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Configure WeatherAPI.com ---
WEATHERAPI_KEY = "2385b7a7051045f382d62111252807"

# --- Set Page Config ---
st.set_page_config(page_title="🌾 AGRI-TOOL", layout="wide")

# --- Inject Custom Colorful CSS ---
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            border-right: 2px solid #64b5f6;
            background: linear-gradient(to top, #d9fbd3, #e3f2fd);
        }

        body {
            background: linear-gradient(to right, #e3f2fd, #d9fbd3, #ffffff);
        }

        .st-emotion-cache-1v0mbdj h1, .st-emotion-cache-1v0mbdj h2 {
            color: #2b6b4f;
        }

        .stButton>button {
            background-color: #64b5f6;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #42a5f5;
        }

        input, textarea {
            background-color: #f0fbff !important;
            border: 1px solid #a0d9a7 !important;
        }

        @keyframes slideIn {
            0% {transform: translateY(30px); opacity: 0;}
            100% {transform: translateY(0); opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# --- Title & Intro ---
st.title("🌾 AGRI-TOOL – AI Assistant for Farmers")
st.markdown("Empowering Farmers with AI — Disease Detection, Weather Alerts, Farming Advice, and More!")

# --- Language Selection ---
lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Telugu", "Hindi"])
lang_map = {
    "English": "Respond in English.",
    "Telugu": "స్పష్టంగా తెలుగులో స్పందించండి.",
    "Hindi": "कृपया स्पष्ट हिंदी में उत्तर दें।"
}

def get_gtts_lang_code(selected_lang):
    return {
        "English": "en",
        "Telugu": "te",
        "Hindi": "hi"
    }.get(selected_lang, "en")

def speak(text):
    try:
        tts = gTTS(text=text, lang=get_gtts_lang_code(lang))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning(f"TTS failed: {e}")

def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening...")
        audio = r.listen(source, phrase_time_limit=6)
    try:
        query = r.recognize_google(audio)
        st.success(f"You said: {query}")
        return query
    except:
        st.error("Could not recognize speech.")
        return None

def gemini_text_response(user_input, system_prompt, lang_instruction):
    prompt = f"{system_prompt}\n\n{lang_instruction}\n\nUser: {user_input}"
    response = model.generate_content(prompt)
    return response.text

def gemini_image_analysis(image_bytes):
    prompt = (
        "Analyze this image and identify if there's any crop disease, pest, or soil issue. "
        "Suggest treatment including pesticides, fertilizers, or best practices. "
        f"{lang_map[lang]}"
    )
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_bytes},
        prompt
    ])
    return response.text

def get_weather_advisory(location):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={location}&aqi=no"
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            return "❌ Location not found or weather service error."

        location_name = data["location"]["name"]
        condition = data["current"]["condition"]["text"]
        temp_c = data["current"]["temp_c"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]
        rainfall = data["current"].get("precip_mm", 0)

        advisory = f"""
📍 **Weather in {location_name}**:
- 🌡️ Temperature: {temp_c}°C
- 🌫️ Condition: {condition}
- 💧 Humidity: {humidity}%
- 💨 Wind Speed: {wind_kph} km/h
- 🌧️ Rainfall: {rainfall} mm

📢 **Farming Advice**:
- {"Delay irrigation due to rainfall." if rainfall > 2 else "Consider light irrigation today."}
- Monitor for fungal diseases in humid conditions.
- {"Ideal" if 20 < temp_c < 30 else "Caution advised"} temperature for most crops.
"""
        return advisory

    except Exception as e:
        return f"⚠️ Error fetching weather data: {e}"

def get_user_location():
    try:
        g = geocoder.ip('me')
        return g.city or g.address or ""
    except:
        return ""

user_location = get_user_location()

# --- Sidebar Navigation ---
option = st.sidebar.radio("📋 Choose a Service", [
    "🌿 Crop & Disease Detection",
    "🤖 AI Farming Chatbot",
    "🌦 Weather-Based Advisory",
    "🧪 Soil & Fertilizer Analysis",
    "🏛 Government Schemes",
    "📆 Crop Calendar",
    "👨‍🌾 Contact Agriculture Officer"
])

# --- Main UI ---
with st.container():
    if option == "🌿 Crop & Disease Detection":
        st.header("🌿 Upload a Photo of the Crop")
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG')
            result = gemini_image_analysis(image_bytes.getvalue())
            st.success("🧪 Analysis Result:")
            st.write(result)
            speak(result)

    elif option == "🤖 AI Farming Chatbot":
        st.header("🤖 Ask your farming questions")
        user_query = st.text_input("Type or speak your query:")
        if st.button("🎤 Speak"):
            user_query = recognize_speech()
        if user_query:
            response = gemini_text_response(user_query, "You are a helpful AI farming assistant.", lang_map[lang])
            st.success("💡 Response:")
            st.write(response)
            speak(response)

    elif option == "🌦 Weather-Based Advisory":
        st.header("🌦 Get Weather-Based Farming Advice")
        location = st.text_input("Enter your village or town:", user_location)
        if st.button("🎤 Speak Location"):
            speech_input = recognize_speech()
            if speech_input:
                location = speech_input
        if location:
            result = get_weather_advisory(location)
            st.success("🌤️ Advisory:")
            st.write(result)
            speak(result)

    elif option == "🧪 Soil & Fertilizer Analysis":
        st.header("🧪 🧫 Input Soil Parameters for Fertilizer Suggestion")
        ph = st.slider("🌡️ Soil pH", 3.5, 9.0, 6.5)
        nitrogen = st.number_input("🌱 Nitrogen (N) level (ppm)", value=50)
        phosphorus = st.number_input("🌾 Phosphorus (P) level (ppm)", value=30)
        potassium = st.number_input("🍠 Potassium (K) level (ppm)", value=40)
        if st.button("🧮 Get Fertilizer Plan"):
            query = (
                f"My soil has pH {ph}, Nitrogen {nitrogen} ppm, Phosphorus {phosphorus} ppm, Potassium {potassium} ppm. "
                "Suggest best fertilizer strategy and also organic options."
            )
            result = gemini_text_response(query,
                                          system_prompt="You are a soil expert helping farmers with personalized fertilizer suggestions.",
                                          lang_instruction=lang_map[lang]
                                          )
            st.success("🧪 Fertilizer Recommendation:")
            st.write(result)
            speak(result)


    elif option == "🏛 Government Schemes":
        st.header("🏛 Government Scheme Info")
        scheme_query = st.text_input("Enter crop name or keyword (e.g., insurance, subsidy):")
        if st.button("🎤 Speak Keyword"):
            scheme_query = recognize_speech()
        if scheme_query:
            response = gemini_text_response(scheme_query, "You are an agriculture government scheme guide.", lang_map[lang])
            st.success("🏛 Available Schemes:")
            st.write(response)
            speak(response)

    elif option == "📆 Crop Calendar":
        st.header("📅 Seasonal Crop Calendar for Your Region")
        district = st.text_input("📍 Enter your district or region:", user_location)
        if st.button("🎤 Speak District"):
            speech_input = recognize_speech()
            if speech_input:
                district = speech_input
        month = datetime.datetime.now().strftime("%B")
        if district:
            prompt = f"Suggest best crops to grow in {district} during the month of {month}. Also suggest climate suitability. {lang_map[lang]}"
            response = gemini_text_response(prompt, "You are a regional crop planning assistant.", lang_map[lang])
            st.success(f"📅 Recommended Crops for {month}:")
            st.write(response)
            speak(response)

    elif option == "👨‍🌾 Contact Agriculture Officer":
        st.header("👨‍🌾 Nearest Agriculture Department Contacts")
        location = st.text_input("📍 Enter your district or city:", user_location)
        if st.button("🎤 Speak Location"):
            speech_input = recognize_speech()
            if speech_input:
                location = speech_input
        if location:
            prompt = f"Give agriculture officer contact info, Krishi Vigyan Kendra, and local farmer helpline numbers for {location}. {lang_map[lang]}"
            response = gemini_text_response(prompt, "You are a government contact assistant.", lang_map[lang])
            st.success("📞 Contact Info:")
            st.write(response)
            speak(response)

# --- Footer ---
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.caption(f"🌐 Language: {lang} | Voice + AI Enabled | Powered by Gemini AI + WeatherAPI | Built for Farmers 👨‍🌾")
