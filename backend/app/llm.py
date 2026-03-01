# app/llm.py
import requests
from typing import List, Dict, Optional
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mistral"

# Supported languages for prototype
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]

# Get language code (handle "English" -> "en", "Hindi" -> "hi", etc.)
def get_lang_code(language):
    lang_map = {
        "english": "en",
        "hindi": "hi",
        "marathi": "mr"
    }
    return lang_map.get(language.lower()[:2], "en")

# Language names for prompts
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}

# Supported languages for prototype
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]


def explain_form(form_text: str, user_language: str) -> Dict:
    """
    Use LLM to understand the form and explain it in user's local language.
    """
    # Convert language to code
    lang_code = get_lang_code(user_language)
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    system_prompt = (
        "You are an expert at analyzing forms and documents. "
        "Analyze the provided form text and explain what the form is for, "
        f"its different sections, and what information is being asked in {lang_name}. "
        "You must respond ONLY in valid JSON with this format: "
        "{\"form_type\": \"...\", \"purpose\": \"...\", \"sections\": [...], \"summary\": \"...\"}"
    )

    # Language-specific prompts
    prompts = {
        "hi": (
            f"फॉर्म टेक्स्ट का विश्लेषण करें:\n{form_text[:1500]}\n\n"
            f"इस फॉर्म को {lang_name} (हिंदी) में समझाएं। "
            "फॉर्म का प्रकार (जैसे KYC, आवेदन, पंजीकरण), उद्देश्य, "
            "मुख्य खंड और कौन सी जानकारी आवश्यक है बताएं।"
        ),
        "mr": (
            f"फॉर्म टेक्स्टचे विश्लेषण करा:\n{form_text[:1500]}\n\n"
            f"हा फॉर्म {lang_name} (मराठी) मध्ये स्पष्ट करा। "
            "फॉर्मचा प्रकार (जसे KYC, अर्ज, नोंदणी), उद्देश्य, "
            "मुख्य विभाग आणि कोणती माहिती आवश्यक आहे सांगा."
        ),
        "en": (
            f"Analyze this form text:\n{form_text[:1500]}\n\n"
            f"Explain this form in {lang_name}. "
            "Provide: form type (e.g., KYC, application, registration), "
            "purpose, key sections, and what information is required."
        )
    }
    
    user_prompt = prompts.get(lang_code, prompts["en"])

    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        
        explanation = json.loads(content)
    except Exception as e:
        # Fallback explanation
        explanation = {
            "form_type": "Form",
            "purpose": "Information collection form",
            "sections": ["Personal Information", "Contact Details"],
            "summary": "This form collects various information fields."
        }
    
    return explanation


def suggest_fields_from_text(form_text: str, language: str) -> List[str]:
    """Use LLM to intelligently suggest form fields from extracted text."""
    lang_code = get_lang_code(language)
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    system_prompt = (
        "You are an expert at identifying form fields from document text. "
        "Analyze the form text and identify all the fields that need to be filled. "
        "You must respond ONLY in valid JSON as an array of field names."
    )

    prompts = {
        "hi": f"फॉर्म टेक्स्ट:\n{form_text[:1500]}\n\nसभी फॉर्म फ़ील्ड की सूची बनाएं।",
        "mr": f"फॉर्म टेक्स्ट:\n{form_text[:1500]}\n\nसर्व फॉर्म फील्डची यादी बनवा.",
        "en": f"Form text:\n{form_text[:1500]}\n\nList all the form fields."
    }
    
    user_prompt = prompts.get(lang_code, prompts["en"])

    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        
        fields = json.loads(content)
        if isinstance(fields, list):
            return fields
    except Exception:
        pass
    
    # Fallback
    return ["Full Name", "Date of Birth", "Address", "Mobile Number", "Email"]


def generate_questions_from_fields(fields: List[str], language: str) -> List[Dict]:
    """
    Generate user-friendly questions from form fields in Hindi or Marathi.
    """
    lang_code = get_lang_code(language)
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    # Language-specific system prompts
    system_prompts = {
        "hi": (
            f"आप एक सहायक असिस्टेंट हैं जो फॉर्म भरने के लिए उपयोगकर्ता के अनुकूल प्रश्न बनाते हैं।"
            f"प्रश्न {lang_name} (हिंदी) में बनाएं।"
            "केवल वैध JSON में उत्तर दें।"
            "प्रारूप: [{\"id\": \"q1\", \"field_name\": \"Full Name\", \"question_text\": \"...\", \"field_type\": \"text\"}, ...]"
        ),
        "mr": (
            f"आपण एक सहायक आहात जो फॉर्म भरण्यासाठी वापरकर्ता-अनुकूल प्रश्न तयार करतात।"
            f"प्रश्न {lang_name} (मराठी) मध्ये तयार करा।"
            "केवल वैध JSON मध्ये उत्तर द्या."
            "प्रारूप: [{\"id\": \"q1\", \"field_name\": \"Full Name\", \"question_text\": \"...\", \"field_type\": \"text\"}, ...]"
        ),
        "en": (
            f"You are a helpful assistant that creates user-friendly questions to collect information for filling out a form. "
            f"Generate questions in {lang_name} language. "
            "You must respond ONLY in valid JSON. "
            "Output format: [{\"id\": \"q1\", \"field_name\": \"Full Name\", \"question_text\": \"...\", \"field_type\": \"text\"}, ...]"
        )
    }
    
    # Language-specific user prompts
    user_prompts = {
        "hi": (
            f"फ़ील्ड: {fields}\nभाषा: {lang_name}\n\n"
            "प्रत्येक फ़ील्ड के लिए एक स्पष्ट प्रश्न बनाएं जिसका उपयोगकर्ता आसानी से उत्तर दे सके।"
            "प्रश्न छोटे और विनम्र रखें।"
        ),
        "mr": (
            f"फील्ड: {fields}\nभाषा: {lang_name}\n\n"
            "प्रत्येक फील्डसाठी एक स्पष्ट प्रश्न बनवा ज्याचे वापरकर्ता सहज उत्तर देऊ शकेल."
            "प्रश्न लहान आणि विनम्र ठेवा."
        ),
        "en": (
            f"Fields: {fields}\nLanguage: {lang_name}\n\n"
            "For each field, create ONE clear question that a normal person can answer. "
            "Keep questions short and polite."
        )
    }
    
    system_prompt = system_prompts.get(lang_code, system_prompts["en"])
    user_prompt = user_prompts.get(lang_code, user_prompts["en"])

    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]

        questions = json.loads(content)
    except Exception as e:
        # Fallback questions in Hindi/Marathi
        questions = []
        fallback_texts = {
            "hi": {
                "Full Name": "आपका पूरा नाम क्या है?",
                "Date of Birth": "आपकी जन्म तिथि क्या है?",
                "Address": "आपका पता क्या है?",
                "Mobile Number": "आपका मोबाइल नंबर क्या है?",
                "Email": "आपका ईमेल पता क्या है?",
                "Gender": "आपका लिंग क्या है?",
                "Nationality": "आपकी राष्ट्रीयता क्या है?",
                "Occupation": "आपका व्यवसाय क्या है?"
            },
            "mr": {
                "Full Name": "तुमचे पूर्ण नाव काय आहे?",
                "Date of Birth": "तुमची जन्मतारीख काय आहे?",
                "Address": "तुमचा पत्ता काय आहे?",
                "Mobile Number": "तुमचा मोबाइल नंबर काय आहे?",
                "Email": "तुमचा ईमेल पत्ता काय आहे?",
                "Gender": "तुमचा लिंग काय आहे?",
                "Nationality": "तुमची राष्ट्रीयता काय आहे?",
                "Occupation": "तुमचा व्यवसाय काय आहे?"
            }
        }
        
        texts = fallback_texts.get(lang_code, fallback_texts["hi"])
        for i, field in enumerate(fields):
            questions.append({
                "id": f"q{i+1}",
                "field_name": field,
                "question_text": texts.get(field, f"What is your {field}?"),
                "field_type": "text"
            })
    
    return questions
