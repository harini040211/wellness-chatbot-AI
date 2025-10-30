import streamlit as st
import hashlib
import sqlite3
from datetime import datetime, timedelta
import random
import re
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('milestone4_wellness_chatbot.db')
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

def db_exec(query, params=(), fetch=None):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if fetch == 'one': return cur.fetchone()
        if fetch == 'all': return cur.fetchall()
        return cur.lastrowid

def safe_db(query, params=(), fetch=None, default=None):
    try:
        return db_exec(query, params, fetch)
    except Exception as e:
        st.error(f"DB error: {e}")
        return default if default else ([] if fetch == 'all' else None)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed

# Admin credentials (in production, this should be in a secure database)
ADMIN_CREDENTIALS = {
    "admin@wellness.com": "admin123"  # Change this in production
}

def is_admin(email):
    return email in ADMIN_CREDENTIALS

def authenticate_admin(email, password):
    return email in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[email] == password

# Complete Knowledge Base with ALL symptoms and first aid
WELLNESS_KB = {
    "symptoms": {
        "headache": {
            "english": """**For Headache Relief:**

• Drink plenty of water - dehydration is a common cause

• Rest in a quiet, dark room away from bright lights

• Apply a cold compress to your forehead for 15 minutes

• Avoid screens (phone, computer, TV) for at least 30 minutes

• Try gentle neck and shoulder stretches

• Consider over-the-counter pain relievers if needed

• If severe or persistent for more than 24 hours, consult a doctor""",
            "hindi": """**सिरदर्द के लिए:**

• खूब पानी पिएं - निर्जलीकरण एक आम कारण है

• अंधेरे, शांत कमरे में आराम करें

• माथे पर 15 मिनट के लिए ठंडा सेक लगाएं

• कम से कम 30 मिनट के लिए स्क्रीन से बचें

• हल्के गर्दन और कंधे की स्ट्रेचिंग करें

• जरूरत पड़ने पर दर्द निवारक दवा लें

• अगर 24 घंटे से अधिक समय तक रहे तो डॉक्टर से परामर्श करें"""
        }, 
       "fever": {
            "english": """**For Fever Management:**

• Stay well-hydrated with water, clear broths, or electrolyte drinks

• Rest completely and avoid physical activities

• Wear light, breathable clothing

• Use a cool, damp washcloth on forehead and wrists

• Take temperature regularly and monitor changes

• Consider fever-reducing medication if over 101°F (38.3°C)

• Seek medical attention if fever exceeds 103°F (39.4°C)

• Call doctor immediately if accompanied by severe symptoms""",
            "hindi": """**बुखार प्रबंधन के लिए:**

• पानी, साफ शोरबा या इलेक्ट्रोलाइट पेय के साथ हाइड्रेटेड रहें

• पूरी तरह से आराम करें और शारीरिक गतिविधियों से बचें

• हल्के, सांस लेने योग्य कपड़े पहनें

• माथे और कलाइयों पर ठंडा, नम कपड़ा रखें

• नियमित रूप से तापमान लें और परिवर्तनों की निगरानी करें

• यदि 101°F (38.3°C) से अधिक हो तो बुखार कम करने वाली दवा लें"""
        },
        "fatigue": {
            "english": """**To Combat Fatigue:**

• Ensure 7-9 hours of quality sleep each night

• Maintain a consistent sleep schedule, even on weekends

• Eat balanced meals with complex carbohydrates and lean proteins

• Stay hydrated throughout the day

• Take short 10-15 minute walks to boost energy

• Limit caffeine intake after 2 PM

• Practice stress-reduction techniques like deep breathing

• If persistent for weeks, consult healthcare provider""",
            "hindi": """**थकान से निपटने के लिए:**

• प्रति रात 7-9 घंटे की गुणवत्तापूर्ण नींद सुनिश्चित करें

• सप्ताहांत पर भी नींद का सुसंगत कार्यक्रम बनाए रखें

• जटिल कार्बोहाइड्रेट और लीन प्रोटीन के साथ संतुलित भोजन खाएं

• दिन भर हाइड्रेटेड रहें

• ऊर्जा बढ़ाने के लिए 10-15 मिनट की छोटी सैर करें"""
        },    
    "stress": {
            "english": """**For Stress Management:**

• Practice deep breathing exercises (4-7-8 technique)

• Try progressive muscle relaxation starting from toes to head

• Engage in 20-30 minutes of physical activity daily

• Limit caffeine and alcohol consumption

• Maintain regular meal times and avoid skipping meals

• Connect with supportive friends or family members

• Consider mindfulness meditation or yoga

• If overwhelming, seek professional counseling support""",
            "hindi": """**तनाव प्रबंधन के लिए:**

• गहरी सांस लेने के व्यायाम का अभ्यास करें (4-7-8 तकनीक)

• पैर की उंगलियों से सिर तक प्रगतिशील मांसपेशी विश्राम का प्रयास करें

• रोजाना 20-30 मिनट की शारीरिक गतिविधि में संलग्न हों

• कैफीन और शराब की खपत सीमित करें"""
        },
        "anxiety": {
            "english": """**To Manage Anxiety:**

• Use grounding techniques: name 5 things you see, 4 you hear, 3 you touch

• Practice slow, controlled breathing (inhale 4 counts, exhale 6 counts)

• Challenge negative thoughts with realistic perspectives

• Limit news and social media exposure

• Maintain regular exercise routine

• Avoid excessive caffeine and sugar

• Consider talking to a trusted friend or counselor

• If panic attacks occur, seek immediate professional help""",
            "hindi": """**चिंता प्रबंधन के लिए:**

• ग्राउंडिंग तकनीक का उपयोग करें: 5 चीजें जो आप देखते हैं, 4 जो आप सुनते हैं, 3 जो आप छूते हैं

• धीमी, नियंत्रित सांस का अभ्यास करें (4 गिनती में सांस लें, 6 में छोड़ें)

• नकारात्मक विचारों को यथार्थवादी दृष्टिकोण से चुनौती दें"""
        }
    },

    "first_aid": {
        "burn": {
            "english": """**First Aid for Burns:**

**MINOR BURNS (1st degree - red, painful skin):**

• Immediately cool the burn with cool running water for 10-15 minutes

• Remove jewelry or tight clothing before swelling begins

• Do NOT apply ice, butter, or home remedies

• Cover with sterile, non-adhesive bandage or clean cloth

• Take over-the-counter pain medication if needed

• Apply aloe vera gel after cooling

**SERIOUS BURNS (2nd/3rd degree - blistering, charred skin):**

• Call 911 immediately - do not delay

• Do not remove clothing stuck to burn area

• Cover burn with cool, moist cloth while waiting for help

• Do not break blisters or apply creams to severe burns

• Monitor for signs of shock: pale skin, rapid breathing""",
            "hindi": """**जलने के लिए प्राथमिक चिकित्सा:**

**छोटी जलन (1st डिग्री - लाल, दर्दनाक त्वचा):**

• तुरंत 10-15 मिनट के लिए ठंडे बहते पानी से जलन को ठंडा करें

• सूजन शुरू होने से पहले गहने या तंग कपड़े हटा दें

• बर्फ, मक्खन, या घरेलू उपचार न लगाएं"""
        }
    },

    "wellness_tips": [
        {
            "english": "💧 HYDRATION: Drink 8-10 glasses of water daily. Carry a reusable bottle and eat water-rich foods.",
            "hindi": "💧 हाइड्रेशन: प्रतिदिन 8-10 गिलास पानी पिएं। पुन: प्रयोज्य बोतल ले जाएं।"
        },
        {
            "english": "😴 SLEEP: Maintain 7-9 hours of quality sleep with consistent bedtime and wake-up times.",
            "hindi": "😴 नींद: सुसंगत सोने के समय और जागने के समय के साथ 7-9 घंटे की गुणवत्तापूर्ण नींद बनाए रखें।"
        }
    ],

    "greetings": [
        {
            "hindi": "**नमस्ते! 🌿 मैं आपका स्वास्थ्य मार्गदर्शक बॉट हूं**\n\nमैं इनमें मदद कर सकता हूं:\n\n• सामान्य लक्षण और देखभाल सलाह\n\n• प्राथमिक चिकित्सा प्रक्रियाएं\n\n• दैनिक स्वास्थ्य सुझाव\n\n• मानसिक स्वास्थ्य सहायता\n\n**आज आप किस स्वास्थ्य विषय पर चर्चा करना चाहेंगे?**",
            "english": "**Hello! 🌿 I'm your Wellness Guide Bot**\n\nI can help with:\n\n• Common symptoms and care advice\n\n• First aid procedures\n\n• Daily wellness tips\n\n• Mental health support\n\n**What health topic would you like to explore today?**"
        }
    ],

    "farewells": [
        {
            "hindi": "**अपना ख्याल रखें! 🌿**\n\nयाद रखें:\n\n• हाइड्रेटेड रहें और पर्याप्त आराम करें\n\n• अपने शरीर की सुनें\n\n• जरूरत पड़ने पर पेशेवर चिकित्सा देखभाल लें\n\n**स्वस्थ रहें!**",
            "english": "**Take care! 🌿**\n\nRemember:\n\n• Stay hydrated and get adequate rest\n\n• Listen to your body\n\n• Seek professional medical care when needed\n\n**Stay healthy!**"
        }
    ]
}

# Enhanced health entities for extraction including Hinglish
HEALTH_ENTITIES = {
    "symptoms": ["headache", "fever", "fatigue", "stress", "anxiety", "cold", "cough", "stomach", "back_pain", "back pain", "nausea", 
                "pain", "ache", "tired", "sick", "dizzy", "weak", "sore", "hurt", "vomit", "diarrhea"],
    "body_parts": ["head", "throat", "chest", "stomach", "back", "neck", "shoulder", "leg", "arm", "eye", "ear", "nose", 
                   "mouth", "tooth", "teeth", "hand", "foot", "knee", "elbow"],
    "conditions": ["diabetes", "hypertension", "asthma", "allergy", "infection", "flu", "migraine", "cold", "fever", "covid"]
}

# Enhanced Hindi-English entity mapping including Hinglish
HINDI_ENTITIES = {
    # Hindi Devanagari
    "बुखार": "fever", "सिरदर्द": "headache", "खांसी": "cough", "पेट": "stomach", "दर्द": "pain",
    "गला": "throat", "आंख": "eye", "कान": "ear", "नाक": "nose", "सिर": "head",
    "थकान": "fatigue", "तनाव": "stress", "चिंता": "anxiety", "सर्दी": "cold",
    "पीठ": "back", "मतली": "nausea", "कमजोर": "weak", "चक्कर": "dizzy",

    # Hinglish (Hindi words in English script)
    "bukaar": "fever", "bukhaar": "fever", "bukhar": "fever", "bukhhar": "fever",
    "sir": "head", "sir dard": "headache", "sirdard": "headache", 
    "pet": "stomach", "pet dard": "stomach", "petdard": "stomach",
    "khansi": "cough", "khasi": "cough",
    "gala": "throat", "galaa": "throat",
    "paani": "water", "pani": "water", 
    "thakan": "fatigue", "thakaan": "fatigue",
    "tanav": "stress", "tension": "stress",
    "chinta": "anxiety", "pareshan": "anxiety",
    "kamjor": "weak", "kamjori": "weak",
    "chakkar": "dizzy", "chakker": "dizzy",
    "peeth": "back", "pith": "back",
    "nazla": "cold", "zukam": "cold", "jukam": "cold"
}

def detect_language(text):
    """FIXED language detection - English stays English, Hindi stays Hindi"""
    # Check for Devanagari script (Hindi)
    hindi_chars = re.findall(r'[ऀ-ॿ]', text)
    if len(hindi_chars) > 3:  # Need more than 3 Hindi characters to be considered Hindi
        return 'hindi'

    # Check for Hinglish - ONLY specific Hinglish words, not common English
    text_lower = text.lower()
    hinglish_specific = ["bukaar", "bukhaar", "bukhar", "sirdard", "petdard", "khansi", "mujhe", "merko", "batao", "bataiye"]

    # Only consider Hinglish if it has SPECIFIC Hinglish words
    hinglish_count = sum(1 for word in hinglish_specific if word in text_lower)
    if hinglish_count >= 1:
        return 'hinglish'

    # Default to English for everything else
    return 'english'

def extract_health_entities(text):
    """Extract health-related entities from text including Hinglish"""
    text_lower = text.lower()
    entities = {
        "symptoms": [],
        "body_parts": [],
        "conditions": []
    }

    # Extract using keyword matching
    for category, keywords in HEALTH_ENTITIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                entities[category].append(keyword)

    # Extract Hindi/Hinglish entities
    for hindi_word, english_word in HINDI_ENTITIES.items():
        if hindi_word.lower() in text_lower:
            if english_word in HEALTH_ENTITIES["symptoms"]:
                entities["symptoms"].append(english_word)
            elif english_word in HEALTH_ENTITIES["body_parts"]:
                entities["body_parts"].append(english_word)
            elif english_word in HEALTH_ENTITIES["conditions"]:
                entities["conditions"].append(english_word)

    # Remove duplicates
    for category in entities:
        entities[category] = list(set(entities[category]))

    return entities

def classify_intent(message):
    """Enhanced intent classification with entity extraction"""
    message_lower = message.lower()
    entities = extract_health_entities(message)

    # Check for greetings (including Hinglish)
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste', 'namaskar', 'नमस्ते', 'good morning', 'good evening']):
        return 'greeting', entities

    # Check for farewells (including Hinglish)
    elif any(word in message_lower for word in ['bye', 'goodbye', 'alvida', 'अलविदा', 'thanks', 'thank you', 'धन्यवाद']):
        return 'farewell', entities

    # Check for first aid - PRIORITY CHECK
    elif any(word in message_lower for word in ['choking', 'choke', 'ghut', 'cut', 'kat', 'burn', 'jal', 'bleeding', 'khoon', 
                                                 'injury', 'accident', 'emergency', 'wound', 'sprain', 'nosebleed', 'allergic']):
        return 'first_aid', entities

    # Check for symptoms (including Hinglish)
    elif entities["symptoms"] or any(word in message_lower for word in ['feel', 'have', 'experiencing', 'suffering', 'problem']):
        return 'symptom', entities

    # Check for wellness tips
    elif any(word in message_lower for word in ['tips', 'advice', 'healthy', 'wellness', 'exercise', 'nutrition', 'diet', 'fitness']):
        return 'wellness_tips', entities

    else:
        return 'general', entities

def generate_safe_response(intent, entities, original_message, is_hindi_hinglish=False):
    """Generate safe, ethical responses with disclaimers"""

    disclaimer = "\n\n⚠️ **Medical Disclaimer:** This is general wellness information only, not professional medical advice. Please consult a qualified healthcare provider for proper diagnosis and treatment."
    hindi_disclaimer = "\n\n⚠️ **चिकित्सा अस्वीकरण:** यह केवल सामान्य स्वास्थ्य जानकारी है, पेशेवर चिकित्सा सलाह नहीं। कृपया उचित निदान और उपचार के लिए योग्य स्वास्थ्य सेवा प्रदाता से परामर्श लें।"

    if intent == 'greeting':
        greeting_item = random.choice(WELLNESS_KB['greetings'])
        return greeting_item['hindi'] if is_hindi_hinglish else greeting_item['english']

    elif intent == 'farewell':
        farewell_item = random.choice(WELLNESS_KB['farewells'])
        return farewell_item['hindi'] if is_hindi_hinglish else farewell_item['english']

    elif intent == 'first_aid':
        # Check specific first aid keywords in message
        message_lower = original_message.lower()

        if 'burn' in message_lower or 'jal' in message_lower:
            response_text = WELLNESS_KB['first_aid']['burn']['hindi' if is_hindi_hinglish else 'english']
            return response_text + (hindi_disclaimer if is_hindi_hinglish else disclaimer)

        else:
            if is_hindi_hinglish:
                return f"मैं जलने, कटने, मोच, नकसीर, घुटन और एलर्जिक प्रतिक्रियाओं के लिए प्राथमिक चिकित्सा मार्गदर्शन प्रदान कर सकता हूं। कृपया आपातकाल के प्रकार को निर्दिष्ट करें।{hindi_disclaimer}"
            return f"I can provide first aid guidance for burns, cuts, sprains, nosebleeds, choking, and allergic reactions. Please specify the type of emergency.{disclaimer}"

    elif intent == 'symptom':
        if entities["symptoms"]:
            responses = []
            for symptom in entities["symptoms"]:
                symptom_clean = symptom.replace('_', ' ').replace(' ', '_')
                if symptom_clean in WELLNESS_KB['symptoms']:
                    info = WELLNESS_KB['symptoms'][symptom_clean]
                    response_text = info['hindi' if is_hindi_hinglish else 'english']
                    responses.append(response_text)

            if responses:
                final_response = "\n\n---\n\n".join(responses)
                final_response += hindi_disclaimer if is_hindi_hinglish else disclaimer
                return final_response

        if is_hindi_hinglish:
            return f"मैं समझता हूं कि आप लक्षणों का अनुभव कर रहे हैं। कृपया अपने लक्षणों को और अधिक विशेष रूप से वर्णन करें ताकि मैं बेहतर मार्गदर्शन प्रदान कर सकूं।{hindi_disclaimer}"
        return f"I understand you're experiencing symptoms. Please describe your symptoms more specifically so I can provide better guidance.{disclaimer}"

    elif intent == 'wellness_tips':
        tip_item = random.choice(WELLNESS_KB['wellness_tips'])
        tip = tip_item['hindi' if is_hindi_hinglish else 'english']
        return f"{tip}{hindi_disclaimer if is_hindi_hinglish else disclaimer}"

    else:
        if is_hindi_hinglish:
            return f"मैं स्वास्थ्य और कल्याण के सवालों में मदद करने के लिए यहां हूं। मुझसे लक्षण, प्राथमिक चिकित्सा, या स्वास्थ्य सुझाव के बारे में पूछें।{hindi_disclaimer}"
        return f"I'm here to help with health and wellness questions. Ask me about symptoms, first aid, or wellness tips.{disclaimer}"

def load_css():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #E6D5F5 0%, #C8A2E0 100%); }
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        color: white; padding: 1.5rem; text-align: center;
        font-size: 2.5rem; font-weight: bold; margin-bottom: 2rem;
        border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-family: 'Arial Black', sans-serif; letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .admin-header {
        background: linear-gradient(90deg, #FF6B6B, #FF8E53, #FF6B6B);
        color: white; padding: 1.5rem; text-align: center;
        font-size: 2.5rem; font-weight: bold; margin-bottom: 2rem;
        border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-family: 'Arial Black', sans-serif; letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white; border: none; border-radius: 8px;
        padding: 1.5rem; font-weight: bold; width: 100%;
        transition: transform 0.2s;
        font-size: 1.5rem;
        line-height: 1.8;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .admin-button > button {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem; font-weight: bold; width: 100%;
        transition: transform 0.2s;
    }
    .metric-card {
        background: rgba(255,255,255,0.9);
        border-radius: 10px; padding: 1.5rem;
        margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        color: black !important;
    }
    .stChatMessage {
        background: rgba(255,255,255,0.9);
        border-radius: 10px; padding: 1rem;
        margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        color: black !important;
    }
    .profile-section {
        background: rgba(255,255,255,0.9);
        border-radius: 10px; padding: 1rem; margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        color: black !important;
    }
    
    /* Make chatbot response text black */
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        color: black !important;
    }
    
    /* Make success and error messages text black */
    .stSuccess, .stError, .stWarning, .stInfo {
        color: black !important;
    }
    .stSuccess > div, .stError > div, .stWarning > div, .stInfo > div {
        color: black !important;
    }
    .stSuccess p, .stError p, .stWarning p, .stInfo p {
        color: black !important;
    }
    div[data-testid="stNotification"] {
        color: black !important;
    }
    div[data-testid="stNotification"] p {
        color: black !important;
    }
    
    /* Metric boxes with colored backgrounds */
    .metric-box {
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin: 10px;
    }
    .metric-box h3, .metric-box p {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

def init_database():
    conn = sqlite3.connect('milestone4_wellness_chatbot.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            preferred_language TEXT DEFAULT 'english',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            age INTEGER,
            gender TEXT,
            height_cm INTEGER,
            weight_kg REAL,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            health_goals TEXT,
            medical_conditions TEXT,
            allergies TEXT,
            emergency_contact TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            detected_entities TEXT,
            intent TEXT,
            language TEXT DEFAULT 'english',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            context TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Admin-specific tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_email TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Knowledge Base Management Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            topic_key TEXT NOT NULL UNIQUE,
            topic_name TEXT NOT NULL,
            english_content TEXT NOT NULL,
            hindi_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            feedback_type TEXT NOT NULL,
            rating INTEGER,
            comments TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_message_id INTEGER,
            feedback_type TEXT NOT NULL,
            rating INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

def create_user(email, password, full_name, preferred_language='english'):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, preferred_language)
            VALUES (?, ?, ?, ?)
        """, (email, password_hash, full_name, preferred_language))
        conn.commit()
        conn.close()
        return True, "Account created successfully"
    except sqlite3.IntegrityError:
        return False, "Email already exists"
    except Exception as e:
        return False, f"Error: {str(e)}"

def authenticate_user(email, password):
    try:
        result = db_exec("""
            SELECT id, password_hash, full_name, preferred_language, 
                   age, gender, height_cm, weight_kg, 
                   blood_pressure_systolic, blood_pressure_diastolic, 
                   health_goals, medical_conditions, 
                   allergies, emergency_contact FROM users WHERE email = ?
        """, (email,), 'one')
        if result and verify_password(password, result[1]):
            return True, {
                'id': result[0], 
                'email': email, 
                'full_name': result[2],
                'preferred_language': result[3] if result[3] else 'english',
                'age': result[4],
                'gender': result[5],
                'height_cm': result[6],
                'weight_kg': result[7],
                'bp_systolic': result[8],
                'bp_diastolic': result[9],
                'health_goals': result[10],
                'medical_conditions': result[11],
                'allergies': result[12],
                'emergency_contact': result[13]
            }
        return False, None
    except Exception as e:
        return False, f"Error: {str(e)}"

# Admin Functions
def get_admin_dashboard_data():
    """Get comprehensive dashboard data for admin"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # New users this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (week_ago,))
        new_users_week = cursor.fetchone()[0]
        
        # Total conversations
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        total_conversations = cursor.fetchone()[0]
        
        # Active users (users who chatted in last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM chat_history 
            WHERE timestamp >= ?
        """, (week_ago,))
        active_users = cursor.fetchone()[0]
        
        # Most common symptoms
        cursor.execute("""
            SELECT entity_value, COUNT(*) as count 
            FROM entity_logs 
            WHERE entity_type = 'symptoms' 
            GROUP BY entity_value 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_symptoms = cursor.fetchall()
        
        # Language distribution
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM chat_history 
            GROUP BY language 
            ORDER BY count DESC
        """)
        language_dist = cursor.fetchall()
        
        # Intent distribution
        cursor.execute("""
            SELECT intent, COUNT(*) as count 
            FROM chat_history 
            GROUP BY intent 
            ORDER BY count DESC
        """)
        intent_dist = cursor.fetchall()
        
        # Daily chat volume (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM chat_history 
            WHERE DATE(timestamp) >= ? 
            GROUP BY DATE(timestamp) 
            ORDER BY date
        """, (thirty_days_ago,))
        daily_chats = cursor.fetchall()
        
        # User demographics
        cursor.execute("""
            SELECT gender, COUNT(*) as count 
            FROM users 
            WHERE gender IS NOT NULL 
            GROUP BY gender
        """)
        gender_dist = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN age < 18 THEN 'Under 18'
                    WHEN age BETWEEN 18 AND 25 THEN '18-25'
                    WHEN age BETWEEN 26 AND 35 THEN '26-35'
                    WHEN age BETWEEN 36 AND 50 THEN '36-50'
                    WHEN age > 50 THEN 'Over 50'
                    ELSE 'Unknown'
                END as age_group,
                COUNT(*) as count
            FROM users 
            GROUP BY age_group
        """)
        age_dist = cursor.fetchall()
        
        # Response feedback metrics
        cursor.execute("""
            SELECT feedback_type, COUNT(*) as count 
            FROM response_feedback 
            GROUP BY feedback_type
        """)
        feedback_metrics = cursor.fetchall()
        
        # Recent feedback (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM response_feedback 
            WHERE timestamp >= ?
        """, (week_ago,))
        recent_feedback = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'new_users_week': new_users_week,
            'total_conversations': total_conversations,
            'active_users': active_users,
            'top_symptoms': top_symptoms,
            'language_dist': language_dist,
            'intent_dist': intent_dist,
            'daily_chats': daily_chats,
            'gender_dist': gender_dist,
            'age_dist': age_dist,
            'feedback_metrics': feedback_metrics,
            'recent_feedback': recent_feedback
        }
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
        return None

def get_user_management_data():
    """Get user data for management"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.preferred_language, 
                   u.created_at, COUNT(ch.id) as chat_count,
                   MAX(ch.timestamp) as last_activity
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id
            GROUP BY u.id, u.email, u.full_name, u.preferred_language, u.created_at
            ORDER BY u.created_at DESC
        """)
        
        users_data = cursor.fetchall()
        conn.close()
        
        return users_data
    except Exception as e:
        st.error(f"Error fetching user data: {str(e)}")
        return []

def log_admin_action(admin_email, action, details=""):
    """Log admin actions"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admin_logs (admin_email, action, details)
            VALUES (?, ?, ?)
        """, (admin_email, action, details))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error logging admin action: {str(e)}")

def add_kb_entry(content_type, topic_key, topic_name, english_content, hindi_content, admin_email):
    """Add new knowledge base entry to database"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_base 
            (content_type, topic_key, topic_name, english_content, hindi_content, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (content_type, topic_key, topic_name, english_content, hindi_content, admin_email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        st.error(f"Error adding entry: {str(e)}")
        return False

def update_kb_entry(entry_id, topic_name, english_content, hindi_content):
    """Update existing knowledge base entry"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE knowledge_base 
            SET topic_name = ?, english_content = ?, hindi_content = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (topic_name, english_content, hindi_content, entry_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating entry: {str(e)}")
        return False

def delete_kb_entry(entry_id):
    """Delete knowledge base entry"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_base WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting entry: {str(e)}")
        return False

def get_all_kb_entries():
    """Get all knowledge base entries from database"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content_type, topic_key, topic_name, 
                   english_content, hindi_content, created_at, updated_at
            FROM knowledge_base
            ORDER BY content_type, topic_name
        """)
        entries = cursor.fetchall()
        conn.close()
        return entries
    except Exception as e:
        st.error(f"Error fetching entries: {str(e)}")
        return []

def get_kb_entry_by_id(entry_id):
    """Get single knowledge base entry by ID"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content_type, topic_key, topic_name, 
                   english_content, hindi_content
            FROM knowledge_base
            WHERE id = ?
        """, (entry_id,))
        entry = cursor.fetchone()
        conn.close()
        return entry
    except Exception as e:
        st.error(f"Error fetching entry: {str(e)}")
        return None

def show_admin_dashboard():
    """Display the admin dashboard"""
    st.markdown('<div class="admin-header">🔧 Admin Dashboard - Wellness Chatbot Analytics</div>', unsafe_allow_html=True)
    
    # Get dashboard data
    data = get_admin_dashboard_data()
    if not data:
        st.error("Unable to load dashboard data")
        return
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #FF6B6B; margin: 0;">👥 Total Users</h3>
            <h1 style="color: #333; margin: 10px 0;">{data['total_users']:,}</h1>
            <p style="color: #666; margin: 0;">Registered Users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4ECDC4; margin: 0;">📈 New Users</h3>
            <h1 style="color: #333; margin: 10px 0;">{data['new_users_week']:,}</h1>
            <p style="color: #666; margin: 0;">This Week</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #45B7D1; margin: 0;">💬 Conversations</h3>
            <h1 style="color: #333; margin: 10px 0;">{data['total_conversations']:,}</h1>
            <p style="color: #666; margin: 0;">Total Chats</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #96CEB4; margin: 0;">🔥 Active Users</h3>
            <h1 style="color: #333; margin: 10px 0;">{data['active_users']:,}</h1>
            <p style="color: #666; margin: 0;">Last 7 Days</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Calculate satisfaction rate
        feedback_metrics = data.get('feedback_metrics', [])
        total_feedback = sum([count for _, count in feedback_metrics])
        thumbs_up = next((count for feedback_type, count in feedback_metrics if feedback_type == 'thumbs_up'), 0)
        satisfaction_rate = (thumbs_up / total_feedback * 100) if total_feedback > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4CAF50; margin: 0;">👍 Satisfaction</h3>
            <h1 style="color: #333; margin: 10px 0;">{satisfaction_rate:.1f}%</h1>
            <p style="color: #666; margin: 0;">{data['recent_feedback']} This Week</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top Health Concerns")
        if data['top_symptoms']:
            symptoms_df = pd.DataFrame(data['top_symptoms'], columns=['Symptom', 'Count'])
            fig = px.bar(symptoms_df, x='Count', y='Symptom', orientation='h',
                        color='Count', color_continuous_scale='Viridis',
                        title="Most Discussed Symptoms")
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No symptom data available yet")
    
    with col2:
        st.subheader("🌍 Language Usage")
        if data['language_dist']:
            lang_df = pd.DataFrame(data['language_dist'], columns=['Language', 'Count'])
            fig = px.pie(lang_df, values='Count', names='Language',
                        title="Language Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No language data available yet")
    
    # Query Types, Daily Activity, and Age Distribution sections removed as requested
    
    # Response Feedback Summary
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT feedback_type, COUNT(*) as count 
            FROM response_feedback 
            GROUP BY feedback_type
        """)
        
        feedback_summary = cursor.fetchall()
        
        if feedback_summary:
            st.subheader("👍👎 Response Feedback Summary")
            
            col1, col2 = st.columns(2)
            
            feedback_df = pd.DataFrame(feedback_summary, columns=['Feedback', 'Count'])
            total_feedback = feedback_df['Count'].sum()
            thumbs_up = feedback_df[feedback_df['Feedback'] == 'thumbs_up']['Count'].sum() if len(feedback_df[feedback_df['Feedback'] == 'thumbs_up']) > 0 else 0
            satisfaction_rate = (thumbs_up / total_feedback * 100) if total_feedback > 0 else 0
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #4CAF50; margin: 0;">👍 User Satisfaction</h3>
                    <h1 style="color: #333; margin: 10px 0;">{satisfaction_rate:.1f}%</h1>
                    <p style="color: #666; margin: 0;">{thumbs_up} positive / {total_feedback} total</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                fig = px.pie(feedback_df, values='Count', names='Feedback',
                           title="Response Ratings",
                           color_discrete_map={'thumbs_up': '#4CAF50', 'thumbs_down': '#F44336'})
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading feedback summary: {str(e)}")

def show_user_management():
    """Display user management interface"""
    st.subheader("👥 User Management")
    
    users_data = get_user_management_data()
    
    if users_data:
        # Convert to DataFrame for better display
        df = pd.DataFrame(users_data, columns=[
            'ID', 'Email', 'Full Name', 'Language', 'Created At', 'Chat Count', 'Last Activity'
        ])
        
        # Format dates
        df['Created At'] = pd.to_datetime(df['Created At']).dt.strftime('%Y-%m-%d %H:%M')
        df['Last Activity'] = pd.to_datetime(df['Last Activity']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", len(df))
        with col2:
            st.metric("Active Users (7 days)", len(df[df['Chat Count'] > 0]))
        with col3:
            avg_chats = df['Chat Count'].mean()
            st.metric("Avg Chats per User", f"{avg_chats:.1f}")
        
        # Search and filter
        search_term = st.text_input("🔍 Search users by email or name:")
        if search_term:
            df = df[df['Email'].str.contains(search_term, case=False) | 
                   df['Full Name'].str.contains(search_term, case=False)]
        
        # Display users table
        st.dataframe(df, use_container_width=True, height=400)
        
        # User details section
        st.subheader("📋 User Details")
        selected_email = st.selectbox("Select user to view details:", df['Email'].tolist())
        
        if selected_email:
            user_details = get_user_details(selected_email)
            if user_details:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Personal Information:**")
                    st.write(f"Name: {user_details.get('full_name', 'N/A')}")
                    st.write(f"Email: {user_details.get('email', 'N/A')}")
                    st.write(f"Age: {user_details.get('age', 'N/A')}")
                    st.write(f"Gender: {user_details.get('gender', 'N/A')}")
                    st.write(f"Language: {user_details.get('preferred_language', 'N/A')}")
                
                with col2:
                    st.write("**Health Information:**")
                    st.write(f"Height: {user_details.get('height_cm', 'N/A')} cm")
                    st.write(f"Weight: {user_details.get('weight_kg', 'N/A')} kg")
                    st.write(f"BP: {user_details.get('bp_systolic', 'N/A')}/{user_details.get('bp_diastolic', 'N/A')}")
                    st.write(f"Emergency Contact: {user_details.get('emergency_contact', 'N/A')}")
                
                if user_details.get('health_goals'):
                    st.write("**Health Goals:**")
                    st.write(user_details['health_goals'])
                
                if user_details.get('medical_conditions'):
                    st.write("**Medical Conditions:**")
                    st.write(user_details['medical_conditions'])
                
                if user_details.get('allergies'):
                    st.write("**Allergies:**")
                    st.write(user_details['allergies'])
    else:
        st.info("No users found in the system.")

def get_user_details(email):
    """Get detailed user information"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    except Exception as e:
        st.error(f"Error fetching user details: {str(e)}")
        return None

def show_system_analytics():
    """Display detailed system analytics"""
    st.subheader("📈 System Analytics")
    
    # Time range selector
    time_range = st.selectbox("Select time range:", 
                             ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
    
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": None
    }
    
    days = days_map[time_range]
    
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        
        # Base query condition
        time_condition = ""
        params = []
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            time_condition = "WHERE timestamp >= ?"
            params = [cutoff_date]
        
        # Query execution with time filter
        cursor.execute(f"""
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM chat_history 
            {time_condition}
            GROUP BY DATE(timestamp) 
            ORDER BY date
        """, params)
        
        daily_data = cursor.fetchall()
        
        if daily_data:
            df = pd.DataFrame(daily_data, columns=['Date', 'Messages'])
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Line chart
            fig = px.line(df, x='Date', y='Messages', 
                         title=f"Daily Message Volume - {time_range}")
            fig.update_traces(line_color='#4ECDC4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Messages", df['Messages'].sum())
            with col2:
                st.metric("Average Daily", f"{df['Messages'].mean():.1f}")
            with col3:
                st.metric("Peak Day", df['Messages'].max())
            with col4:
                st.metric("Active Days", len(df))
        
        # Most active hours
        cursor.execute(f"""
            SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as count 
            FROM chat_history 
            {time_condition}
            GROUP BY hour 
            ORDER BY hour
        """, params)
        
        hourly_data = cursor.fetchall()
        
        if hourly_data:
            st.subheader("🕐 Peak Usage Hours")
            hourly_df = pd.DataFrame(hourly_data, columns=['Hour', 'Messages'])
            
            fig = px.bar(hourly_df, x='Hour', y='Messages',
                        title="Messages by Hour of Day",
                        color='Messages', color_continuous_scale='Viridis')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}")

def show_content_management():
    """Display content management interface"""
    st.subheader("📝 Content Management")
    
    tab1, tab2 = st.tabs(["Knowledge Base", "Feedback"])
    
    with tab1:
        st.write("### 📚 Knowledge Base Management")
        
        # Action selector
        action = st.radio("Select Action:", ["View All", "Add New", "Edit", "Delete"], horizontal=True)
        
        st.markdown("---")
        
        # VIEW ALL ENTRIES
        if action == "View All":
            st.subheader("📋 All Knowledge Base Entries")
            
            entries = get_all_kb_entries()
            
            if entries:
                st.success(f"✅ Found {len(entries)} custom knowledge base entries")
                
                # Display as expandable sections
                for entry in entries:
                    entry_id, content_type, topic_key, topic_name, english, hindi, created, updated = entry
                    
                    with st.expander(f"🔹 {content_type}: {topic_name}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**English Content:**")
                            st.info(english)
                        
                        with col2:
                            st.write("**Hindi Content:**")
                            st.info(hindi)
                        
                        st.caption(f"Topic Key: `{topic_key}` | Created: {created} | Updated: {updated}")
            else:
                st.info("No custom knowledge base entries found. Add your first entry!")
                
            # Also show built-in KB
            st.markdown("---")
            st.write("**Built-in Knowledge Base Topics:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Symptoms Covered:**")
            
    
    with tab2:
        st.write("**User Feedback Management:**")
        
        try:
            conn = sqlite3.connect('milestone4_wellness_chatbot.db')
            cursor = conn.cursor()
            
            # Get detailed feedback with user info
            cursor.execute("""
                SELECT u.full_name, u.email, rf.feedback_type, rf.rating, rf.timestamp,
                       ch.message, ch.response
                FROM response_feedback rf
                JOIN users u ON rf.user_id = u.id
                LEFT JOIN chat_history ch ON rf.chat_message_id = ch.id
                ORDER BY rf.timestamp DESC
                LIMIT 50
            """)
            
            detailed_feedback = cursor.fetchall()
            
            if detailed_feedback:
                # Display feedback in normal form (not table)
                st.write("**Recent Feedback Entries:**")
                
                for idx, feedback in enumerate(detailed_feedback[:10], 1):
                    user_name, email, feedback_type, rating, timestamp, user_msg, bot_response = feedback
                    
                    with st.expander(f"🔹 Feedback #{idx} - {user_name} ({feedback_type})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**User:** {user_name}")
                            st.write(f"**Email:** {email}")
                            st.write(f"**Feedback:** {feedback_type}")
                        
                        with col2:
                            st.write(f"**Rating:** {'⭐' * (rating if rating else 0)}")
                            st.write(f"**Time:** {timestamp}")
                        
                        if user_msg:
                            st.write(f"**User Message:** {user_msg[:200]}...")
                        if bot_response:
                            st.write(f"**Bot Response:** {bot_response[:200]}...")
                
                st.markdown("---")
                
                # Feedback summary in colored boxes
                st.write("### 📊 Feedback Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_feedback = len(detailed_feedback)
                    st.markdown(f"""
                    <div class="metric-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <h3 style="color: black !important; margin: 0;">📊 Total Feedback</h3>
                        <p style="color: black !important; font-size: 2.5rem; font-weight: bold; margin: 10px 0;">{total_feedback}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    thumbs_up_count = sum(1 for f in detailed_feedback if f[2] == 'thumbs_up')
                    satisfaction_rate = (thumbs_up_count / total_feedback * 100) if total_feedback > 0 else 0
                    st.markdown(f"""
                    <div class="metric-box" style="background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);">
                        <h3 style="color: black !important; margin: 0;">😊 Satisfaction Rate</h3>
                        <p style="color: black !important; font-size: 2.5rem; font-weight: bold; margin: 10px 0;">{satisfaction_rate:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    thumbs_down = total_feedback - thumbs_up_count
                    st.markdown(f"""
                    <div class="metric-box" style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);">
                        <h3 style="color: black !important; margin: 0;">👎 Thumbs Down</h3>
                        <p style="color: black !important; font-size: 2.5rem; font-weight: bold; margin: 10px 0;">{thumbs_down}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No feedback data available yet. Users need to rate chatbot responses.")
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error loading feedback data: {str(e)}")

def show_admin_settings():
    """Display admin settings and database management"""
    st.subheader("⚙️ System Settings")
    
    tab1, tab2 = st.tabs(["Database Management", "User Management"])
    
    with tab1:
        st.write("**Database Operations:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Database Statistics")
            try:
                conn = sqlite3.connect('milestone4_wellness_chatbot.db')
                cursor = conn.cursor()
                
                # Get table statistics
                tables = ['users', 'chat_history', 'entity_logs', 'response_feedback', 'system_feedback', 'admin_logs']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    st.metric(f"{table.replace('_', ' ').title()}", count)
                
                conn.close()
                
            except Exception as e:
                st.error(f"Error getting database stats: {str(e)}")
        
        with col2:
            st.subheader("🗑️ Database Cleanup")
            
            if st.button("🗑️ Clear All Chat History", type="secondary"):
                if st.session_state.get('confirm_clear_chats', False):
                    try:
                        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM chat_history")
                        cursor.execute("DELETE FROM entity_logs")
                        cursor.execute("DELETE FROM response_feedback")
                        conn.commit()
                        conn.close()
                        st.success("All chat history cleared!")
                        log_admin_action(st.session_state.get('admin_email', 'admin'), 
                                       "Cleared all chat history", "Database cleanup")
                        st.session_state.confirm_clear_chats = False
                    except Exception as e:
                        st.error(f"Error clearing chat history: {str(e)}")
                else:
                    st.session_state.confirm_clear_chats = True
                    st.warning("⚠️ Click again to confirm deletion of ALL chat history!")
            
            if st.button("🗑️ Clear All Feedback", type="secondary"):
                if st.session_state.get('confirm_clear_feedback', False):
                    try:
                        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM response_feedback")
                        cursor.execute("DELETE FROM system_feedback")
                        conn.commit()
                        conn.close()
                        st.success("All feedback cleared!")
                        log_admin_action(st.session_state.get('admin_email', 'admin'), 
                                       "Cleared all feedback", "Database cleanup")
                        st.session_state.confirm_clear_feedback = False
                    except Exception as e:
                        st.error(f"Error clearing feedback: {str(e)}")
                else:
                    st.session_state.confirm_clear_feedback = True
                    st.warning("⚠️ Click again to confirm deletion of ALL feedback!")
    
    with tab2:
        st.write("**User Account Management:**")
        
        # Delete user account
        st.subheader("🗑️ Delete User Account")
        user_email = st.text_input("Enter user email to delete:")
        
        if st.button("🗑️ Delete User Account", type="secondary"):
            if user_email and st.session_state.get('confirm_delete_user', False):
                try:
                    conn = sqlite3.connect('milestone4_wellness_chatbot.db')
                    cursor = conn.cursor()
                    
                    # Get user ID first
                    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
                    user_result = cursor.fetchone()
                    
                    if user_result:
                        user_id = user_result[0]
                        
                        # Delete all user data
                        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM entity_logs WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM response_feedback WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM system_feedback WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"User account {user_email} and all associated data deleted!")
                        log_admin_action(st.session_state.get('admin_email', 'admin'), 
                                       f"Deleted user account", f"Email: {user_email}")
                        st.session_state.confirm_delete_user = False
                    else:
                        st.error("User not found!")
                        
                except Exception as e:
                    st.error(f"Error deleting user: {str(e)}")
            elif user_email:
                st.session_state.confirm_delete_user = True
                st.warning(f"⚠️ Click again to confirm deletion of user: {user_email}")
        
        # Reset user password
        st.subheader("🔑 Reset User Password")
        reset_email = st.text_input("Enter user email for password reset:")
        new_password = st.text_input("New password:", type="password")
        
        if st.button("🔑 Reset Password"):
            if reset_email and new_password:
                try:
                    conn = sqlite3.connect('milestone4_wellness_chatbot.db')
                    cursor = conn.cursor()
                    
                    password_hash = hash_password(new_password)
                    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", 
                                 (password_hash, reset_email))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        st.success(f"Password reset for {reset_email}")
                        log_admin_action(st.session_state.get('admin_email', 'admin'), 
                                       f"Reset password", f"Email: {reset_email}")
                    else:
                        st.error("User not found!")
                    
                    conn.close()
                    
                except Exception as e:
                    st.error(f"Error resetting password: {str(e)}")
    


def save_chat_message(user_id, message, response, entities, intent, language):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        entities_json = json.dumps(entities) if entities else None
        cursor.execute("""
            INSERT INTO chat_history (user_id, message, response, detected_entities, intent, language) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, message, response, entities_json, intent, language))
        
        chat_id = cursor.lastrowid

        if entities:
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    cursor.execute("""
                        INSERT INTO entity_logs (user_id, entity_type, entity_value, context)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, entity_type, entity, message))

        conn.commit()
        conn.close()
        return chat_id
    except Exception as e:
        return False

def save_response_feedback(user_id, chat_message_id, feedback_type):
    """Save user feedback for chatbot responses"""
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        
        # Check if feedback already exists for this message
        cursor.execute("""
            SELECT id FROM response_feedback 
            WHERE user_id = ? AND chat_message_id = ?
        """, (user_id, chat_message_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing feedback
            cursor.execute("""
                UPDATE response_feedback 
                SET feedback_type = ?, timestamp = CURRENT_TIMESTAMP
                WHERE user_id = ? AND chat_message_id = ?
            """, (feedback_type, user_id, chat_message_id))
        else:
            # Insert new feedback
            cursor.execute("""
                INSERT INTO response_feedback (user_id, chat_message_id, feedback_type, rating)
                VALUES (?, ?, ?, ?)
            """, (user_id, chat_message_id, feedback_type, 1 if feedback_type == 'thumbs_up' else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving feedback: {str(e)}")
        return False

def get_chat_history(user_id, limit=20):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message, response, detected_entities, intent, language, timestamp 
            FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
        """, (user_id, limit))
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        return []

def get_user_entity_stats(user_id):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT entity_type, entity_value, COUNT(*) as frequency
            FROM entity_logs WHERE user_id = ?
            GROUP BY entity_type, entity_value
            ORDER BY frequency DESC LIMIT 10
        """, (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        return []

def clear_chat_history(user_id):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM entity_logs WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def update_user_profile(user_id, profile_data):
    try:
        conn = sqlite3.connect('milestone4_wellness_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET 
                full_name = ?, preferred_language = ?, age = ?, gender = ?, height_cm = ?, weight_kg = ?,
                blood_pressure_systolic = ?, blood_pressure_diastolic = ?, health_goals = ?, 
                medical_conditions = ?, allergies = ?, emergency_contact = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (profile_data['full_name'], profile_data['preferred_language'], profile_data['age'], 
              profile_data['gender'], profile_data['height_cm'], profile_data['weight_kg'],
              profile_data['bp_systolic'], profile_data['bp_diastolic'], profile_data['health_goals'],
              profile_data['medical_conditions'], profile_data['allergies'], profile_data['emergency_contact'], user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Profile update error: {str(e)}")
        return False

def main():
    st.set_page_config(
        page_title="Wellness Assistant Chatbot",
        page_icon="🌿",
        layout="wide"
    )

    load_css()
    init_database()

    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False
    if 'show_analytics' not in st.session_state:
        st.session_state.show_analytics = False
    if 'show_profile' not in st.session_state:
        st.session_state.show_profile = False
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'dashboard'

    # Admin Panel Check
    if st.session_state.admin_authenticated:
        # Admin Interface
        st.markdown('<div class="admin-header">🔧 Admin Panel - Wellness Chatbot Management</div>', unsafe_allow_html=True)
        
        # Navigation buttons with large icons
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            if st.button("📊\n\nDashboard", key="nav_dashboard", use_container_width=True, help="View Dashboard"):
                st.session_state.admin_view = 'dashboard'
        
        with col2:
            if st.button("👥\n\nUsers", key="nav_users", use_container_width=True, help="Manage Users"):
                st.session_state.admin_view = 'users'
        
        with col3:
            if st.button("📈\n\nAnalytics", key="nav_analytics", use_container_width=True, help="View Analytics"):
                st.session_state.admin_view = 'analytics'
        
        with col4:
            if st.button("📝\n\nContent", key="nav_content", use_container_width=True, help="Manage Content"):
                st.session_state.admin_view = 'content'
        
        with col5:
            if st.button("⚙️\n\nSettings", key="nav_settings", use_container_width=True, help="System Settings"):
                st.session_state.admin_view = 'settings'
        
        with col6:
            if st.button("🔓\n\nLogout", key="nav_logout", use_container_width=True, help="Logout"):
                st.session_state.admin_authenticated = False
                st.session_state.admin_email = None
                st.success("Logged out from admin panel")
                st.rerun()
        
        st.markdown("---")
        
        # Initialize admin view
        if 'admin_view' not in st.session_state:
            st.session_state.admin_view = 'dashboard'
        
        # Show selected view
        if st.session_state.admin_view == 'dashboard':
            show_admin_dashboard()
        elif st.session_state.admin_view == 'users':
            show_user_management()
        elif st.session_state.admin_view == 'analytics':
            show_system_analytics()
        elif st.session_state.admin_view == 'content':
            show_content_management()
        elif st.session_state.admin_view == 'settings':
            show_admin_settings()
        
        return

    # Regular User Authentication
    if not st.session_state.authenticated:
        st.markdown('<div class="main-header">🌿 Wellness Assistant Chatbot</div>', unsafe_allow_html=True)

        # Add Admin Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔧 Admin Panel", key="admin_access", help="Access admin dashboard"):
                st.session_state.show_admin_login = True

        # Admin Login Modal
        if st.session_state.get('show_admin_login', False):
            st.subheader("🔐 Admin Login")
            with st.form("admin_login_form"):
                admin_email = st.text_input("Admin Email", placeholder="admin@wellness.com")
                admin_password = st.text_input("Admin Password", type="password")
                col1, col2 = st.columns(2)
                
                with col1:
                    admin_submit = st.form_submit_button("🔐 Login as Admin", use_container_width=True)
                with col2:
                    cancel_admin = st.form_submit_button("❌ Cancel", use_container_width=True)

                if admin_submit and admin_email and admin_password:
                    if authenticate_admin(admin_email, admin_password):
                        st.session_state.admin_authenticated = True
                        st.session_state.admin_email = admin_email
                        st.session_state.show_admin_login = False
                        log_admin_action(admin_email, "Admin Login", "Successful login")
                        st.success(f"Welcome Admin!")
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials.")
                
                if cancel_admin:
                    st.session_state.show_admin_login = False
                    st.rerun()

        # Regular user login/register tabs
        if not st.session_state.get('show_admin_login', False):
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

            with tab1:
                with st.form("login_form"):
                    st.subheader("Login to Your Account")
                    email = st.text_input("Email", placeholder="user@example.com")
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("🔐 Login", use_container_width=True)

                    if submit and email and password:
                        success, user_data = authenticate_user(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_data = user_data
                            st.session_state.messages = []
                            st.success(f"Welcome back, {user_data['full_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

            with tab2:
                with st.form("register_form"):
                    st.subheader("Create New Account")
                    name = st.text_input("Full Name")
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    confirm = st.text_input("Confirm Password", type="password")
                    language = st.selectbox("Preferred Language", ["english", "hindi", "hinglish", "both"])
                    submit = st.form_submit_button("📝 Create Account", use_container_width=True)

                    if submit and name and email and password and confirm:
                        if password == confirm:
                            success, message = create_user(email, password, name, language)
                            if success:
                                st.success("Account created! Please login.")
                            else:
                                st.error(message)
                        else:
                            st.error("Passwords do not match.")

    else:
        # Regular User Interface (same as before)
        st.markdown('<div class="main-header">🌿 Wellness Assistant Chatbot</div>', unsafe_allow_html=True)
        st.markdown(f"**Welcome, {st.session_state.user_data['full_name']}!** Your intelligent multilingual health guide is ready.")

        with st.sidebar:
            st.subheader("💬 Chat Controls")

            if st.button("🆕 New Chat"):
                st.session_state.messages = []
                st.session_state.show_history = False
                st.session_state.show_analytics = False
                st.session_state.show_profile = False
                st.success("Started new chat!")

            if st.button("📜 View History"):
                st.session_state.show_history = not st.session_state.show_history
                st.session_state.show_analytics = False
                st.session_state.show_profile = False

            if st.button("📊 View Analytics"):
                st.session_state.show_analytics = not st.session_state.show_analytics
                st.session_state.show_history = False
                st.session_state.show_profile = False

            if st.button("👤 Edit Profile"):
                st.session_state.show_profile = not st.session_state.show_profile
                st.session_state.show_history = False
                st.session_state.show_analytics = False

            if st.button("🗑️ Clear All History"):
                if clear_chat_history(st.session_state.user_data['id']):
                    st.success("History cleared!")
                    st.session_state.messages = []

            if st.button("🔓 Logout"):
                st.session_state.authenticated = False
                st.session_state.user_data = None
                st.session_state.messages = []
                st.rerun()

            st.markdown("---")
            st.subheader("ℹ️ Account Info")
            st.write(f"**Name:** {st.session_state.user_data['full_name']}")
            st.write(f"**Email:** {st.session_state.user_data['email']}")
            st.write(f"**Language:** {st.session_state.user_data['preferred_language']}")

            st.markdown("---")
            st.subheader("🆘 Quick Help")
            st.markdown("""
            **Available Topics:**

            🩺 **Symptoms & Care**
            • Headache, Fever, Fatigue
            • Stress, Anxiety, Cold, Cough
            • Stomach pain, Nausea, Back pain

            🚨 **First Aid Procedures**  
            • Burns (minor and severe)
            • Cuts and wounds
            • Sprains and strains
            • Nosebleeds, Choking
            • Allergic reactions

            💡 **Wellness Tips**
            • Hydration and nutrition
            • Sleep and exercise
            • Mental health support
            """)

        # User Profile Management
        if st.session_state.show_profile:
            st.subheader("👤 Edit Your Health Profile")

            with st.form("profile_form"):
                col1, col2 = st.columns(2)

                with col1:
                    name = st.text_input("Full Name", value=st.session_state.user_data['full_name'] or "")
                    age = st.number_input("Age", min_value=1, max_value=120, value=st.session_state.user_data['age'] if st.session_state.user_data['age'] else 25)
                    gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], 
                                        index=["Male", "Female", "Other", "Prefer not to say"].index(st.session_state.user_data['gender']) if st.session_state.user_data['gender'] in ["Male", "Female", "Other", "Prefer not to say"] else 0)
                    height = st.number_input("Height (cm)", min_value=50, max_value=250, value=st.session_state.user_data['height_cm'] if st.session_state.user_data['height_cm'] else 170)
                    weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=float(st.session_state.user_data['weight_kg']) if st.session_state.user_data['weight_kg'] else 70.0, step=0.1)

                with col2:
                    language = st.selectbox("Preferred Language", ["english", "hindi", "hinglish", "both"], 
                                          index=["english", "hindi", "hinglish", "both"].index(st.session_state.user_data['preferred_language']) if st.session_state.user_data['preferred_language'] in ["english", "hindi", "hinglish", "both"] else 0)
                    bp_systolic = st.number_input("Blood Pressure (Systolic)", min_value=70, max_value=250, 
                                                 value=st.session_state.user_data['bp_systolic'] if st.session_state.user_data['bp_systolic'] else 120)
                    bp_diastolic = st.number_input("Blood Pressure (Diastolic)", min_value=40, max_value=150, 
                                                  value=st.session_state.user_data['bp_diastolic'] if st.session_state.user_data['bp_diastolic'] else 80)
                    emergency_contact = st.text_input("Emergency Contact", value=st.session_state.user_data['emergency_contact'] if st.session_state.user_data['emergency_contact'] else "")

                health_goals = st.text_area("Health Goals", value=st.session_state.user_data['health_goals'] if st.session_state.user_data['health_goals'] else "", 
                                          placeholder="e.g., Lose weight, Manage stress, Improve fitness")
                medical_conditions = st.text_area("Medical Conditions", value=st.session_state.user_data['medical_conditions'] if st.session_state.user_data['medical_conditions'] else "", 
                                                 placeholder="e.g., Diabetes, Hypertension, Asthma")
                allergies = st.text_area("Allergies", value=st.session_state.user_data['allergies'] if st.session_state.user_data['allergies'] else "", 
                                        placeholder="e.g., Peanuts, Shellfish, Medications")

                if st.form_submit_button("💾 Update Profile", use_container_width=True):
                    profile_data = {
                        'full_name': name, 'preferred_language': language, 'age': age, 'gender': gender,
                        'height_cm': height, 'weight_kg': weight, 'bp_systolic': bp_systolic,
                        'bp_diastolic': bp_diastolic, 'health_goals': health_goals,
                        'medical_conditions': medical_conditions, 'allergies': allergies,
                        'emergency_contact': emergency_contact
                    }

                    if update_user_profile(st.session_state.user_data['id'], profile_data):
                        st.session_state.user_data.update(profile_data)
                        st.success("Profile updated successfully!")
                    else:
                        st.error("Error updating profile. Please try again.")

        # Chat History
        elif st.session_state.show_history:
            st.subheader("📜 Chat History")
            history = get_chat_history(st.session_state.user_data['id'])

            if not history:
                st.info("No chat history found.")
            else:
                for i, (msg, resp, entities_json, intent, lang, timestamp) in enumerate(history):
                    with st.expander(f"Chat {i+1}: {msg[:50]}... ({timestamp.split()[0]}) - {intent.upper()}"):
                        st.write(f"**You ({lang}):** {msg}")
                        st.write(f"**Bot:** {resp}")

        # User Analytics
        elif st.session_state.show_analytics:
            st.subheader("📊 Your Health Analytics")

            entity_stats = get_user_entity_stats(st.session_state.user_data['id'])

            if entity_stats:
                st.write("**Most Discussed Health Topics:**")
                for entity_type, entity_value, frequency in entity_stats:
                    st.write(f"• **{entity_value}** ({entity_type}): {frequency} times")

                col1, col2, col3 = st.columns(3)
                with col1:
                    symptoms = [item for item in entity_stats if item[0] == 'symptoms']
                    if symptoms:
                        st.write("**Top Symptoms:**")
                        for _, symptom, freq in symptoms[:5]:
                            st.write(f"• {symptom}: {freq}")

                with col2:
                    body_parts = [item for item in entity_stats if item[0] == 'body_parts']
                    if body_parts:
                        st.write("**Body Parts Mentioned:**")
                        for _, part, freq in body_parts[:5]:
                            st.write(f"• {part}: {freq}")

                with col3:
                    conditions = [item for item in entity_stats if item[0] == 'conditions']
                    if conditions:
                        st.write("**Conditions Discussed:**")
                        for _, condition, freq in conditions[:5]:
                            st.write(f"• {condition}: {freq}")
            else:
                st.info("No analytics data available yet. Start chatting to see your health discussion patterns!")

        # Main Chat Interface
        else:
            st.subheader("💬 Chat with Your Advanced Wellness Assistant")

            # Display chat messages with feedback buttons
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Add feedback buttons for assistant responses
                    if message["role"] == "assistant" and "chat_id" in message:
                        col1, col2, col3 = st.columns([1, 1, 8])
                        
                        with col1:
                            if st.button("👍", key=f"thumbs_up_{i}", help="This response was helpful"):
                                if save_response_feedback(st.session_state.user_data['id'], message["chat_id"], "thumbs_up"):
                                    st.success("Thank you for your feedback!")
                                    st.rerun()
                        
                        with col2:
                            if st.button("👎", key=f"thumbs_down_{i}", help="This response was not helpful"):
                                if save_response_feedback(st.session_state.user_data['id'], message["chat_id"], "thumbs_down"):
                                    st.info("Thank you for your feedback. We'll work to improve!")
                                    st.rerun()

            if prompt := st.chat_input("Ask me about health in English, Hindi, or Hinglish... / स्वास्थ्य के बारे में पूछें..."):
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Processing your health query..."):
                        detected_lang = detect_language(prompt)

                        processed_text = prompt
                        if detected_lang in ['hindi', 'hinglish']:
                            processed_text = prompt  # Keep original for better processing

                        intent, entities = classify_intent(processed_text)

                        response = generate_safe_response(intent, entities, processed_text, detected_lang in ['hindi', 'hinglish'])

                        st.markdown(response)

                # Save chat message and get the chat ID
                chat_id = save_chat_message(
                    st.session_state.user_data['id'], 
                    prompt, 
                    response, 
                    entities, 
                    intent, 
                    detected_lang
                )

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "entities": entities,
                    "intent": intent,
                    "chat_id": chat_id
                })
                
                # Show feedback buttons for the latest response
                col1, col2, col3 = st.columns([1, 1, 8])
                
                with col1:
                    if st.button("👍", key="latest_thumbs_up", help="This response was helpful"):
                        if save_response_feedback(st.session_state.user_data['id'], chat_id, "thumbs_up"):
                            st.success("Thank you for your feedback!")
                            st.rerun()
                
                with col2:
                    if st.button("👎", key="latest_thumbs_down", help="This response was not helpful"):
                        if save_response_feedback(st.session_state.user_data['id'], chat_id, "thumbs_down"):
                            st.info("Thank you for your feedback. We'll work to improve!")
                            st.rerun()

if __name__ == "__main__":
    main()