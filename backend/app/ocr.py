# app/ocr.py
from PIL import Image
import pytesseract
from typing import List, Dict, Optional

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Supported languages (prototype: English + Hindi/Marathi patterns)
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]

# Language display names
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}

# Common form field patterns in Hindi and Marathi (Roman script)
FIELD_PATTERNS = {
    "hi": [
        # Name fields
        "naam", "purana naam", "poora naam", "first name", "last name", "surname",
        # Date/Birth
        "janam tariq", "janam din", "dob", "birth date", "date of birth",
        # Address
        "pata", "address", "rahega", "current address", "permanent address",
        # Contact
        "phone", "mobile", "telephone", "number", "contact",
        "email", "e-mail", "mail",
        # Personal
        "gender", "sex", "ling",
        "nationality", "desh", "country",
        "occupation", "kaam", "job", "profession",
        "income", "kamai", "salary",
        # Documents
        "aadhar", "pan", "passport", "license", "voter id",
        # Other
        "signature", "hastakshar", "date", "tarikh", "place", "sthan"
    ],
    "mr": [
        # Name fields
        "nav", "purnav", "first name", "last name", "surname",
        # Date/Birth
        "janmadin", "janam", "dob", "birth date", "tariq",
        # Address
        "pata", "address", "raheela", "current address", "permanent address",
        # Contact
        "phone", "mobile", "number", "contact",
        "email", "mail",
        # Personal
        "gender", "sex", "ling",
        "nationality", "desh", "country",
        "occupation", "kas", "job", "profession",
        "income", "salary",
        # Documents
        "aadhar", "pan", "passport", "license",
        # Other
        "sachin", "date", "tarikh", "place", "thikan"
    ]
}

# Common Hindi/Marathi field names in English (for bilingual forms)
BILINGUAL_FIELDS = {
    "hi": {
        "name": "नाम",
        "full name": "पूरा नाम",
        "first name": "पहला नाम",
        "last name": "अंतिम नाम",
        "date of birth": "जन्म तिथि",
        "address": "पता",
        "phone number": "फ़ोन नंबर",
        "mobile number": "मोबाइल नंबर",
        "email": "ईमेल",
        "gender": "लिंग",
        "nationality": "राष्ट्रीयता",
        "occupation": "व्यवसाय",
        "aadhar number": "आधार नंबर",
        "pan number": "पैन नंबर"
    },
    "mr": {
        "name": "नाव",
        "full name": "पूर्ण नाव",
        "first name": "पहिले नाव",
        "last name": "शेवटचे नाव",
        "date of birth": "जन्मतारीख",
        "address": "पत्ता",
        "phone number": "फोन नंबर",
        "mobile number": "मोबाइल नंबर",
        "email": "ईमेल",
        "gender": "लिंग",
        "nationality": "राष्ट्रीयता",
        "occupation": "व्यवसाय",
        "aadhar number": "आधार नंबर",
        "pan number": "पैन नंबर"
    }
}


def extract_text(image_path: str, language: str = "en") -> str:
    """Extract text from image using Tesseract OCR."""
    img = Image.open(image_path)
    
    # Try with English first (most reliable)
    text = pytesseract.image_to_string(img, lang="eng")
    
    # If no text, try with other languages or combination
    if not text.strip():
        # Try with multiple languages combined
        text = pytesseract.image_to_string(img, lang="eng+hin")
    
    return text


def extract_text_with_boxes(image_path: str) -> Dict:
    """Extract text with bounding box coordinates."""
    img = Image.open(image_path)
    
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    
    words = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > 0:
            word = data['text'][i]
            if word.strip():
                words.append({
                    "text": word,
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i],
                    "confidence": data['conf'][i]
                })
    
    return {
        "full_text": pytesseract.image_to_string(img, lang="eng"),
        "words": words
    }


def infer_fields_from_text(text: str, language: str = "en") -> List[str]:
    """Infer form fields from extracted text using pattern matching."""
    text_lower = text.lower()
    found_fields = set()
    
    # Get patterns for the specified language
    lang_code = language.lower()[:2]  # "English" -> "en", "Hindi" -> "hi"
    patterns = FIELD_PATTERNS.get(lang_code, FIELD_PATTERNS["hi"])
    
    for pattern in patterns:
        if pattern in text_lower:
            # Convert to readable field name
            field_name = pattern.title()
            found_fields.add(field_name)
    
    # If no fields found, return default fields based on language
    lang_code = language.lower()[:2]
    if not found_fields:
        if lang_code == "mr":
            return ["पूर्ण नाव", "जन्मतारीख", "पत्ता", "मोबाइल नंबर", "ईमेल"]
        elif lang_code == "hi":
            return ["पूरा नाम", "जन्म तिथि", "पता", "मोबाइल नंबर", "ईमेल"]
        else:
            return ["Full Name", "Date of Birth", "Address", "Mobile Number", "Email"]
    
    return list(found_fields)


def get_field_translation(field: str, language: str) -> str:
    """Get translation of field name in the target language."""
    field_lower = field.lower()
    translations = BILINGUAL_FIELDS.get(language, {})
    return translations.get(field_lower, field)
