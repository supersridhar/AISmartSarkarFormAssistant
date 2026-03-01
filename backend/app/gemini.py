# app/gemini.py
import google.generativeai as genai
import os
from typing import List, Dict
import base64

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBMwbCT003BWHiPBAeGseXSwV7QJSjcLnA"
genai.configure(api_key=GEMINI_API_KEY)

# Use gemini-1.5-flash for fast vision analysis
MODEL_NAME = "gemini-1.5-flash"

# Language names
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}


def explain_form_with_vision(image_path: str, user_language: str, ocr_text: str = "") -> Dict:
    """
    Use Google Gemini Vision to understand the form directly from image.
    Also includes OCR text for better context.
    """
    lang_code = user_language.lower()[:2] if isinstance(user_language, str) else "en"
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Create model
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Create detailed prompt with OCR text for context
    prompts = {
        "hi": f"""इस फॉर्म का बहुत विस्तार से विश्लेषण करें। 

OCR से निकला हुआ टेक्स्ट:
{ocr_text[:1000]}

अब निम्न जानकारी बहुत विस्तार से दें:
1. फॉर्म का सही प्रकार (जैसे: जन्म प्रमाण पत्र, मृत्यु प्रमाण पत्र, पहचान पत्र, KYC फॉर्म, बैंक फॉर्म, आवेदन पत्र, राशन कार्ड, पासपोर्ट फॉर्म, वोटर आईडी, ड्राइविंग लाइसेंस, स्कूल फॉर्म, कॉलेज फॉर्म, नौकरी फॉर्म, बीमा फॉर्म, आदि)
2. यह फॉर्म किसके लिए है (कौन सा विभाग/संस्था इसे जारी करता है)
3. इस फॉर्म का उद्देश्य क्या है
4. इसमें कौन से मुख्य खंड/भाग हैं
5. कौन सी सभी जानकारी/फ़ील्ड भरनी है (नाम, तारीख, पता, आदि सहित)
6. क्या कोई दस्तावेज़ संलग्न करने हैं

जानकारी हिंदी में बहुत विस्तार से दें।

JSON फॉर्मेट में उत्तर दें:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}""",
        
        "mr": f"""या फॉर्मचे खूप सविस्तर विश्लेषण करा.

OCR ते निघालेला टेक्स्ट:
{ocr_text[:1000]}

आता खालील माहिती खूप सविस्तर द्या:
1. फॉर्मचा योग्य प्रकार (जसे: जन्म प्रमाणपत्र, मृत्यु प्रमाणपत्र, ओळखपत्र, KYC फॉर्म, बँक फॉर्म, अर्ज, रेशन कार्ड, पासपोर्ट फॉर्म, वोटर आयडी, ड्रायव्हिंग लायसेंस, शाळा फॉर्म, महाविद्यालय फॉर्म, नोकरी फॉर्म, विमा फॉर्म, इ)
2. हा फॉर्म कोणासाठी आहे (कोणता विभाग/संस्था हा जारी करते)
3. या फॉर्मचा उद्देश्य काय आहे
4. यात कौनते मुख्य भाग आहेत
5. कोणती सर्व माहिती/फील्ड भरण्यास लागते (नाव, तारीख, पत्ता, इ)
6. कोणते दस्तावेज जोडणे आवश्यक आहेत

माहिती मराठीमध्ये खूप सविस्तर द्या.

JSON फॉर्मेटमध्ये उत्तर द्या:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}""",
        
        "en": f"""Analyze this form in very great detail.

OCR extracted text:
{ocr_text[:1000]}

Now provide very detailed information:
1. Exact form type (e.g., birth certificate, death certificate, ID card, KYC form, bank form, application form, ration card, passport form, voter ID, driving license, school form, college form, job form, insurance form, etc.)
2. Which authority/department issues this form
3. Purpose of this form
4. Main sections/parts in the form
5. ALL fields that need to be filled (including name, date, address, etc.)
6. What documents need to be attached

Provide very detailed information in {lang_name}.

Respond in JSON format:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}"""
    }
    
    prompt = prompts.get(lang_code, prompts["en"])
    
    try:
        # Send to Gemini with image
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},
            prompt
        ])
        
        # Parse response
        import json
        text = response.text
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
            else:
                result = json.loads(text)
        except:
            # If JSON parsing fails, create a summary from text
            result = {
                "form_type": "Form",
                "issuing_authority": "Unknown",
                "purpose": "Information collection",
                "sections": ["Personal Information"],
                "fields": ["Name", "Date", "Address"],
                "required_documents": [],
                "summary": text[:500] if text else "This form collects your information."
            }
        
        return result
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "form_type": "Form",
            "issuing_authority": "Unknown",
            "purpose": "Information collection form",
            "sections": ["Personal Information"],
            "fields": ["Name", "Date of Birth", "Address"],
            "required_documents": [],
            "summary": "This form collects your information."
        }


def generate_questions_with_vision(image_path: str, user_language: str, ocr_text: str = "") -> List[Dict]:
    """
    Use Google Gemini Vision to generate questions directly from the form image.
    """
    lang_code = user_language.lower()[:2] if isinstance(user_language, str) else "en"
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Create model
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Create prompt
    prompts = {
        "hi": f"""इस फॉर्म में दिए गए सभी फ़ील्ड के लिए बहुत स्पष्ट और सीधे प्रश्न बनाएं जो उपयोगकर्ता से जानकारी एकत्र करने के लिए पूछे जा सकें।

OCR टेक्स्ट (अतिरिक्त संदर्भ के लिए):
{ocr_text[:500]}

प्रश्न हिंदी में बनाएं। प्रश्न छोटे, स्पष्ट और व्यावहारिक होने चाहिए।
JSON फॉर्मेट में उत्तर दें:
[{{"id": "q1", "field_name": "...", "question_text": "...", "field_type": "text"}}, ...]""",
        
        "mr": f"""या फॉर्ममधील सर्व फील्डसाठी खूप स्पष्ट आणि सरळ प्रश्न तयार करा जे वापरकर्त्याकडून माहिती गोळाकण्यासाठी विचारले जाऊ शकतात.

OCR टेक्स्ट (अतिरिक्त संदर्भासाठी):
{ocr_text[:500]}

प्रश्न मराठीमध्ये तयार करा. प्रश्न लहान, स्पष्ट आणि व्यावहारिक असावेत.
JSON फॉर्मेटमध्ये उत्तर द्या:
[{{"id": "q1", "field_name": "...", "question_text": "...", "field_type": "text"}}, ...]""",
        
        "en": f"""Create very clear and direct questions for each field in this form that can be asked to collect information from the user.

OCR text (for additional context):
{ocr_text[:500]}

Questions should be in {lang_name}. Make questions short, clear, and practical.
Respond in JSON format:
[{{"id": "q1", "field_name": "...", "question_text": "...", "field_type": "text"}}, ...]"""
    }
    
    prompt = prompts.get(lang_code, prompts["en"])
    
    try:
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},
            prompt
        ])
        
        import json
        text = response.text
        
        # Try to extract JSON
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                questions = json.loads(json_str)
            else:
                questions = json.loads(text)
        except:
            questions = []
        
        return questions if isinstance(questions, list) else []
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return []
