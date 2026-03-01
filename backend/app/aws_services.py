# app/aws_services.py
import boto3
from botocore.exceptions import ClientError
import json
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration - using default credentials from environment
# Make sure to set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
# or use aws configure

# Get AWS region from environment
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Language names mapping
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}


def get_textract_client():
    """Get AWS Textract client."""
    return boto3.client('textract', region_name=AWS_REGION)


def get_bedrock_client():
    """Get AWS Bedrock runtime client."""
    return boto3.client('bedrock-runtime', region_name=AWS_REGION)


def extract_text_with_textract(image_path: str) -> Dict:
    """
    Extract text and form data using Amazon Textract.
    Textract is much better than Tesseract for forms!
    """
    try:
        client = get_textract_client()
        
        # Read image
        with open(image_path, 'rb') as document:
            image_bytes = document.read()
        
        # Analyze document (extracts text and form data)
        response = client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        # Extract text
        text_blocks = []
        form_data = {}
        
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
            
            # Extract form key-value pairs
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key = block.get('Text', 'Unknown')
                    value = ''
                    # Try to find the value
                    for rel in block.get('Relationships', []):
                        if rel['Type'] == 'VALUE':
                            for value_id in rel['Ids']:
                                for v_block in response['Blocks']:
                                    if v_block['Id'] == value_id:
                                        value = v_block.get('Text', '')
                                        break
                    if key and key != 'Unknown':
                        form_data[key] = value
        
        full_text = '\n'.join(text_blocks)
        
        return {
            'text': full_text,
            'form_data': form_data,
            'blocks': response['Blocks']
        }
        
    except ClientError as e:
        print(f"AWS Textract error: {e}")
        return {
            'text': '',
            'form_data': {},
            'blocks': []
        }


def analyze_form_with_bedrock(image_path: str, user_language: str, ocr_text: str = "") -> Dict:
    """
    Use Amazon Bedrock with Llama to analyze the form.
    """
    lang_code = user_language.lower()[:2] if isinstance(user_language, str) else "en"
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    try:
        client = get_bedrock_client()
        
        # Read image
        with open(image_path, 'rb') as document:
            image_bytes = document.read()
        
        # Convert to base64
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create prompt
        prompts = {
            "hi": f"""इस फॉर्म का बहुत विस्तार से विश्लेषण करें। 

OCR से निकला हुआ टेक्स्ट:
{ocr_text[:1500]}

निम्न जानकारी दें:
1. फॉर्म का सही प्रकार
2. जारी करने वाला प्राधिकारी
3. फॉर्म का उद्देश्य
4. मुख्य खंड
5. सभी फ़ील्ड जो भरने हैं
6. क्या दस्तावेज़ चाहिए

हिंदी में बहुत विस्तार से जानकारी दें।

JSON:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}""",
            
            "mr": f"""या फॉर्मचे खूप सविस्तर विश्लेषण करा.

OCR ते निघालेला टेक्स्ट:
{ocr_text[:1500]}

खालील माहिती द्या:
1. फॉर्मचा योग्य प्रकार
2. जारी करणारी संस्था
3. फॉर्मचा उद्देश्य
4. मुख्य भाग
5. सर्व फील्ड जी भरण्यास लागते
6. कोणते दस्तावेज लागती

मराठीमध्ये खूप सविस्तर माहिती द्या.

JSON:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}""",
            
            "en": f"""Analyze this form in very great detail.

OCR extracted text:
{ocr_text[:1500]}

Provide:
1. Exact form type
2. Issuing authority
3. Purpose
4. Main sections
5. ALL fields that need to be filled
6. Required documents

Very detailed info in {lang_name}.

JSON:
{{"form_type": "...", "issuing_authority": "...", "purpose": "...", "sections": [...], "fields": [...], "required_documents": [...], "summary": "..."}}"""
        }
        
        prompt = prompts.get(lang_code, prompts["en"])
        
        # Using Llama 3 on Bedrock
        # Note: You need to enable Llama 3 in Bedrock first
        model_id = "meta.llama3-70b-instruct-v1:0"
        
        # For vision, we'd need to use a different approach
        # For now, use text-only with OCR
        payload = {
            "prompt": f"<s>[INST] {prompt} [/INST]",
            "max_gen_len": 2048,
            "temperature": 0.5,
            "top_p": 0.9
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        text = response_body.get('generation', '')
        
        # Extract JSON
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
            else:
                result = {
                    "form_type": "Form",
                    "issuing_authority": "Unknown",
                    "purpose": "Information collection",
                    "sections": [],
                    "fields": [],
                    "required_documents": [],
                    "summary": text[:500]
                }
        except:
            result = {
                "form_type": "Form",
                "issuing_authority": "Unknown",
                "purpose": "Information collection",
                "sections": [],
                "fields": [],
                "required_documents": [],
                "summary": text[:500] if text else "Form analysis"
            }
        
        return result
        
    except ClientError as e:
        print(f"AWS Bedrock error: {e}")
        return {
            "form_type": "Form",
            "form_category": "Unknown",
            "issuing_authority": "Unknown",
            "purpose": "Information collection",
            "sections": [],
            "fields": [],
            "required_documents": [],
            "summary": "Unable to analyze form"
        }
    except Exception as e:
        print(f"Bedrock error: {e}")
        return {
            "form_type": "Form",
            "form_category": "Unknown",
            "issuing_authority": "Unknown",
            "purpose": "Information collection",
            "sections": [],
            "fields": [],
            "required_documents": [],
            "summary": f"Error: {str(e)}"
        }


# Additional language names for multilingual support
LANGUAGE_NAMES_EXTENDED = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "pa": "Punjabi"
}


def explain_form_multilingual(form_text: str, source_lang: str, target_lang: str) -> Dict:
    """
    Understand form in source language and explain in target language.
    Example: Form in Hindi (source) → Explanation in Marathi (target)
    
    This function:
    1. Identifies the form type (Property Agreement, KYC, Passport, etc.)
    2. Explains the form purpose in the target language
    3. Lists all sections and required fields
    4. Provides a comprehensive explanation
    """
    client = get_bedrock_client()
    
    # Get language names
    source = LANGUAGE_NAMES_EXTENDED.get(source_lang, source_lang)
    target = LANGUAGE_NAMES_EXTENDED.get(target_lang, target_lang)
    
    # Build the prompt for multilingual understanding
    prompt = f"""You are an expert at analyzing legal and official forms from India.

INSTRUCTIONS:
1. Analyze the form text provided below
2. Determine the form type (e.g., Property Agreement/Sale Deed, KYC Form, Passport Application, Bank Form, Ration Card, Voter ID, Income Certificate, Caste Certificate, etc.)
3. Explain what this form is about in {target} language
4. List all sections and fields in the form
5. Explain what information is required from the applicant

SOURCE LANGUAGE (form is in): {source}
TARGET LANGUAGE (explain in): {target}

FORM TEXT:
{form_text[:4000]}

Respond ONLY in this JSON format:
{{
    "form_type": "Type of form (e.g., Property Agreement, KYC Form, Passport Application)",
    "form_category": "Category (e.g., Legal, Government, Banking, Identity)",
    "form_type_explanation": "Brief explanation of what this form is for",
    "purpose": "Why this form is needed",
    "issuing_authority": "Who issues this form (e.g., Sub-Registrar, Bank, Government)",
    "sections": [
        {{"title": "Section name", "description": "What this section asks for", "fields": ["field1", "field2"]}}
    ],
    "required_information": ["List of required fields/information"],
    "required_documents": ["Documents typically needed with this form"],
    "explanation_in_target_language": "Full explanation in {target} language - explain what the form is, its purpose, sections, and what user needs to fill",
    "important_notes": ["Any important notes or tips for filling this form"]
}}"""

    try:
        # Using Claude 3 Haiku - great for multilingual tasks and cost-effective
        # For better reasoning, you can use: "anthropic.claude-3-sonnet-20240229-v1:0"
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.5,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }
        
        response = client.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read().decode('utf-8'))
        return parse_claude_response(result, target)
        
    except ClientError as e:
        print(f"AWS Bedrock error: {e}")
        return get_default_form_response(target)
    except Exception as e:
        print(f"Multilingual explanation error: {e}")
        return get_default_form_response(target)


def parse_claude_response(response: Dict, target_lang: str) -> Dict:
    """Parse Claude's response into structured format."""
    try:
        content = response.get('content', [])
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get('text', '{}')
            return json.loads(text)
        elif isinstance(content, str):
            return json.loads(content)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Parse error: {e}")
    
    return get_default_form_response(target_lang)


def get_default_form_response(target_lang: str) -> Dict:
    """Return default response when parsing fails."""
    return {
        "form_type": "Unknown Form",
        "form_category": "Unknown",
        "form_type_explanation": "Could not analyze the form",
        "purpose": "",
        "issuing_authority": "",
        "sections": [],
        "required_information": [],
        "required_documents": [],
        "explanation_in_target_language": "Unable to analyze form. Please try again.",
        "important_notes": []
    }


def generate_questions_for_form_multilingual(form_text: str, form_analysis: Dict, target_lang: str) -> List[Dict]:
    """
    Generate user-friendly questions based on form analysis in the target language.
    """
    client = get_bedrock_client()
    
    target = LANGUAGE_NAMES_EXTENDED.get(target_lang, target_lang)
    
    # Build context from form analysis
    form_type = form_analysis.get('form_type', 'Unknown')
    sections = form_analysis.get('sections', [])
    required_info = form_analysis.get('required_information', [])
    
    sections_text = "\n".join([f"- {s.get('title', '')}: {s.get('description', '')}" for s in sections])
    required_text = "\n".join([f"- {info}" for info in required_info])
    
    prompt = f"""Generate clear, simple questions that a user needs to answer to fill this {form_type} form.

The form has these sections:
{sections_text}

Required information:
{required_text}

Generate questions in {target} language. Each question should:
1. Be simple and easy to understand
2. Ask for one piece of information at a time
3. Include helpful context about what the field is for

Respond as JSON array:
[
    {{
        "question_id": "q1",
        "question": "Question in {target}",
        "field_reference": "Which form field this maps to",
        "field_type": "text/date/select/etc",
        "help_text": "Optional help text in {target}",
        "example": "Example answer (optional)"
    }}
]"""

    try:
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "temperature": 0.5,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }
        
        response = client.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read().decode('utf-8'))
        content = result.get('content', [])
        
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get('text', '[]')
            # Try to extract valid JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError as je:
                print(f"JSON parse error: {je}")
                # Try to find JSON in the text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start >= 0 and end > start:
                    try:
                        return json.loads(text[start:end])
                    except:
                        pass
                return []
        
    except Exception as e:
        print(f"Question generation error: {e}")
    
    return []


# Keep the old function for backward compatibility
def generate_questions_with_bedrock(image_path: str, user_language: str, ocr_text: str = "") -> List[Dict]:
    """
    Use Amazon Bedrock with Llama to generate questions from form fields.
    """
    lang_code = user_language.lower()[:2] if isinstance(user_language, str) else "en"
    lang_name = LANGUAGE_NAMES.get(lang_code, "English")
    
    try:
        client = get_bedrock_client()
        
        prompts = {
            "hi": f"""इस फॉर्म की सभी फ़ील्ड के लिए स्पष्ट प्रश्न बनाएं:

{ocr_text[:1000]}

हिंदी में प्रश्न बनाएं।
JSON:""",
            
            "mr": f"""या फॉर्मच्या सर्व फील्डसाठी स्पष्ट प्रश्न तयार करा:

{ocr_text[:1000]}

मराठीमध्ये प्रश्न तयार करा.
JSON:""",
            
            "en": f"""Create clear questions for each field in this form:

{ocr_text[:1000]}

Questions in {lang_name}.
JSON:"""
        }
        
        prompt = prompts.get(lang_code, prompts["en"])
        
        model_id = "meta.llama3-70b-instruct-v1:0"
        
        payload = {
            "prompt": f"<s>[INST] {prompt} [/INST]",
            "max_gen_len": 2048,
            "temperature": 0.5,
            "top_p": 0.9
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        text = response_body.get('generation', '')
        
        # Extract JSON
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                questions = json.loads(json_str)
            else:
                questions = []
        except:
            questions = []
        
        return questions if isinstance(questions, list) else []
        
    except Exception as e:
        print(f"Bedrock questions error: {e}")
        return []
