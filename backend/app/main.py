# app/main.py
import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

from .models import (
    UploadResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    Question,
    SubmitAnswersRequest,
    AnnotatedFormResponse,
    ExplainFormRequest,
    ExplainFormResponse,
    SuggestFieldsRequest,
    SuggestFieldsResponse
)
from .ocr import extract_text, infer_fields_from_text, extract_text_with_boxes
from .gemini import explain_form_with_vision, generate_questions_with_vision
from .aws_services import (
    extract_text_with_textract, 
    analyze_form_with_bedrock, 
    generate_questions_with_bedrock,
    explain_form_multilingual,
    generate_questions_for_form_multilingual
)
from .llm import generate_questions_from_fields, explain_form, suggest_fields_from_text
from .annotation import generate_annotations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# simple in-memory store for demo
FORMS: Dict[str, Dict] = {}  # form_id -> {"path": ..., "fields": [...], "questions": [...], "text": ...}


@app.post("/upload_form", response_model=UploadResponse)
async def upload_form(file: UploadFile = File(...), language: str = "en", use_aws: bool = True):
    """Upload a form image and extract text. Set use_aws=True to use AWS Textract."""
    form_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(UPLOAD_DIR, f"{form_id}{file_ext}")

    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Extract text from the form
    if use_aws:
        # Use AWS Textract for better OCR
        try:
            textract_result = extract_text_with_textract(save_path)
            text = textract_result.get('text', '')
            form_data = textract_result.get('form_data', {})
            
            # Combine form data into fields
            fields = list(form_data.keys()) if form_data else []
            if not fields:
                fields = infer_fields_from_text(text, language)
        except Exception as e:
            print(f"Textract error: {e}")
            text = extract_text(save_path, language)
            fields = infer_fields_from_text(text, language)
    else:
        # Use Tesseract OCR
        text = extract_text(save_path, language)
        fields = infer_fields_from_text(text, language)

    FORMS[form_id] = {
        "path": save_path,
        "text": text,
        "fields": fields,
        "questions": [],
        "language": language
    }

    return UploadResponse(form_id=form_id, fields=fields)


@app.post("/explain_form", response_model=ExplainFormResponse)
async def explain_form_endpoint(req: ExplainFormRequest):
    """Explain the form content in the user's language using Gemini Vision."""
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")

    form_data = FORMS[req.form_id]
    form_path = form_data.get("path", "")
    form_text = form_data.get("text", "")
    
    # Try AWS Bedrock first (if configured)
    try:
        explanation = analyze_form_with_bedrock(form_path, req.language, form_text)
        if explanation and explanation.get("form_type"):
            return ExplainFormResponse(
                form_id=req.form_id,
                form_type=explanation.get("form_type", "Form"),
                purpose=explanation.get("purpose", ""),
                sections=explanation.get("sections", []),
                summary=explanation.get("summary", "")
            )
    except Exception as e:
        print(f"AWS Bedrock error: {e}")
    
    # Fall back to Gemini
    try:
        # Use Gemini Vision for better understanding
        explanation = explain_form_with_vision(form_path, req.language, form_text)
        
        return ExplainFormResponse(
            form_id=req.form_id,
            form_type=explanation.get("form_type", "Form"),
            purpose=explanation.get("purpose", ""),
            sections=explanation.get("sections", []),
            summary=explanation.get("summary", "")
        )
    except Exception as e:
        print(f"Gemini error: {e}")
        
        return ExplainFormResponse(
            form_id=req.form_id,
            form_type=explanation.get("form_type", "Form"),
            purpose=explanation.get("purpose", ""),
            sections=explanation.get("sections", []),
            summary=explanation.get("summary", "")
        )
    except Exception as e:
        print(f"Error in explain_form: {e}")
        # Fallback to text-based explanation
        form_text = form_data.get("text", "")
        explanation = explain_form(form_text, req.language)
        
        return ExplainFormResponse(
            form_id=req.form_id,
            form_type=explanation.get("form_type", "Form"),
            purpose=explanation.get("purpose", ""),
            sections=explanation.get("sections", []),
            summary=explanation.get("summary", "")
        )


@app.post("/suggest_fields", response_model=SuggestFieldsResponse)
async def suggest_fields_endpoint(req: SuggestFieldsRequest):
    """Use LLM to intelligently suggest form fields."""
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")

    form_data = FORMS[req.form_id]
    form_text = form_data.get("text", "")
    
    fields = suggest_fields_from_text(form_text, req.language)
    
    # Update form fields
    FORMS[req.form_id]["fields"] = fields
    
    return SuggestFieldsResponse(
        form_id=req.form_id,
        fields=fields
    )


@app.post("/generate_questions", response_model=GenerateQuestionsResponse)
async def generate_questions(req: GenerateQuestionsRequest):
    """Generate questions from form fields in the user's language."""
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")

    form_data = FORMS[req.form_id]
    form_path = form_data.get("path", "")
    form_text = form_data.get("text", "")
    
    # Try AWS Bedrock first (if configured)
    try:
        questions_raw = generate_questions_with_bedrock(form_path, req.language, form_text)
        if questions_raw:
            questions = []
            for item in questions_raw:
                q_id = item.get("id") or str(uuid.uuid4())
                q = Question(
                    id=q_id,
                    field_name=item.get("field_name", ""),
                    question_text=item.get("question_text", "")
                )
                questions.append(q)

            FORMS[req.form_id]["questions"] = [q.dict() for q in questions]
            return GenerateQuestionsResponse(questions=questions)
    except Exception as e:
        print(f"AWS Bedrock questions error: {e}")
    
    # Try Gemini Vision for better questions
    try:
        questions_raw = generate_questions_with_vision(form_path, req.language, form_text)
        if questions_raw:
            questions = []
            for item in questions_raw:
                q_id = item.get("id") or str(uuid.uuid4())
                q = Question(
                    id=q_id,
                    field_name=item.get("field_name", ""),
                    question_text=item.get("question_text", "")
                )
                questions.append(q)

            FORMS[req.form_id]["questions"] = [q.dict() for q in questions]
            return GenerateQuestionsResponse(questions=questions)
    except Exception as e:
        print(f"Gemini questions error: {e}")
    
    # Fallback to text-based
    fields = req.fields if req.fields else form_data.get("fields", [])
    questions_raw = generate_questions_from_fields(fields, req.language)

    questions = []
    for item in questions_raw:
        q_id = item.get("id") or str(uuid.uuid4())
        q = Question(
            id=q_id,
            field_name=item.get("field_name", ""),
            question_text=item.get("question_text", "")
        )
        questions.append(q)

    FORMS[req.form_id]["questions"] = [q.dict() for q in questions]
    return GenerateQuestionsResponse(questions=questions)


@app.post("/submit_answers", response_model=AnnotatedFormResponse)
async def submit_answers(req: SubmitAnswersRequest):
    """Submit user answers and generate annotated form."""
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")

    form_data = FORMS[req.form_id]
    questions = form_data.get("questions", [])

    questions_map = {q["id"]: q["field_name"] for q in questions}
    annotated_fields = generate_annotations(req.form_id, req.answers, questions_map)

    return AnnotatedFormResponse(
        form_id=req.form_id,
        annotated_fields=annotated_fields
    )


@app.get("/form/{form_id}")
async def get_form(form_id: str):
    """Get form data by ID."""
    if form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    return FORMS[form_id]


# ============== NEW MULTILINGUAL ENDPOINTS ==============

from pydantic import BaseModel

class MultilingualExplainRequest(BaseModel):
    form_id: str
    source_language: str  # Language of the form (e.g., "hi" for Hindi)
    target_language: str  # Language for explanation (e.g., "mr" for Marathi)


class MultilingualExplainResponse(BaseModel):
    form_id: str
    form_type: str
    form_category: str
    form_type_explanation: str
    purpose: str
    issuing_authority: str
    sections: List[Dict]
    required_information: List[str]
    required_documents: List[str]
    explanation_in_target_language: str
    important_notes: List[str]


@app.post("/explain_form_multilingual", response_model=MultilingualExplainResponse)
async def explain_form_multilingual_endpoint(req: MultilingualExplainRequest):
    """
    Explain form in a different language than the form.
    
    Example: Form in Hindi (source) → Explanation in Marathi (target)
    
    This endpoint:
    1. Identifies the form type (Property Agreement, KYC, etc.)
    2. Explains the form purpose in target language
    3. Lists all sections and required fields
    """
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    
    form_data = FORMS[req.form_id]
    form_text = form_data.get("text", "")
    form_path = form_data.get("path", "")
    
    # If no text but have image path, try to extract text again
    if not form_text and form_path:
        try:
            from .ocr import extract_text
            form_text = extract_text(form_path)
            # Update the stored text
            FORMS[req.form_id]["text"] = form_text
        except Exception as e:
            print(f"Error re-extracting text: {e}")
    
    if not form_text:
        # Try using image directly with Bedrock if we have the image path
        if form_path:
            try:
                from .aws_services import analyze_form_with_bedrock
                analysis = analyze_form_with_bedrock(form_path, req.target_language, "")
                # Build response from image analysis
                return MultilingualExplainResponse(
                    form_id=req.form_id,
                    form_type=analysis.get("form_type", "Unknown Form"),
                    form_category=analysis.get("form_category", "Unknown"),
                    form_type_explanation="",
                    purpose=analysis.get("purpose", ""),
                    issuing_authority=analysis.get("issuing_authority", ""),
                    sections=[
                        {"title": s, "description": "", "fields": []} 
                        for s in analysis.get("sections", [])
                    ],
                    required_information=[],
                    required_documents=analysis.get("required_documents", []),
                    explanation_in_target_language=analysis.get("summary", ""),
                    important_notes=[]
                )
            except Exception as e:
                print(f"Bedrock image analysis error: {e}")
        
        raise HTTPException(status_code=400, detail="Form text not found. Please upload a clearer image of the form.")
    
    try:
        # Use the new multilingual explanation function
        explanation = explain_form_multilingual(
            form_text=form_text,
            source_lang=req.source_language,
            target_lang=req.target_language
        )
        
        return MultilingualExplainResponse(
            form_id=req.form_id,
            form_type=explanation.get("form_type", "Unknown Form"),
            form_category=explanation.get("form_category", "Unknown"),
            form_type_explanation=explanation.get("form_type_explanation", ""),
            purpose=explanation.get("purpose", ""),
            issuing_authority=explanation.get("issuing_authority", ""),
            sections=explanation.get("sections", []),
            required_information=explanation.get("required_information", []),
            required_documents=explanation.get("required_documents", []),
            explanation_in_target_language=explanation.get("explanation_in_target_language", ""),
            important_notes=explanation.get("important_notes", [])
        )
    except Exception as e:
        print(f"Multilingual explain error: {e}")
        raise HTTPException(status_code=500, detail=f"Error explaining form: {str(e)}")


class MultilingualQuestionsRequest(BaseModel):
    form_id: str
    target_language: str  # Language for questions


@app.post("/generate_questions_multilingual", response_model=GenerateQuestionsResponse)
async def generate_questions_multilingual(req: MultilingualQuestionsRequest):
    """
    Generate questions in a specific language based on form analysis.
    
    This generates user-friendly questions in the target language.
    """
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    
    form_data = FORMS[req.form_id]
    form_text = form_data.get("text", "")
    
    if not form_text:
        raise HTTPException(status_code=400, detail="Form text not found")
    
    try:
        # First, get form analysis
        form_analysis = explain_form_multilingual(
            form_text=form_text,
            source_lang="en",  # Default to English for analysis
            target_lang=req.target_language
        )
        
        # Then generate questions based on analysis
        questions_data = generate_questions_for_form_multilingual(
            form_text=form_text,
            form_analysis=form_analysis,
            target_lang=req.target_language
        )
        
        # If no questions from Bedrock, generate from fields
        if not questions_data:
            fields = form_data.get("fields", [])
            if fields:
                from .llm import generate_questions_from_fields
                questions_data = generate_questions_from_fields(fields, req.target_language)
        
        # Convert to Question objects
        questions = []
        for item in questions_data:
            q_id = item.get("question_id") or item.get("id") or str(uuid.uuid4())
            q = Question(
                id=q_id,
                field_name=item.get("field_reference") or item.get("field_name", ""),
                question_text=item.get("question") or item.get("question_text", "")
            )
            questions.append(q)
        
        FORMS[req.form_id]["questions"] = [q.dict() for q in questions]
        return GenerateQuestionsResponse(questions=questions)
        
    except Exception as e:
        print(f"Multilingual questions error: {e}")
        # Fallback to field-based questions
        try:
            fields = form_data.get("fields", [])
            from .llm import generate_questions_from_fields
            questions_data = generate_questions_from_fields(fields, req.target_language)
            
            questions = []
            for item in questions_data:
                q_id = item.get("id") or str(uuid.uuid4())
                q = Question(
                    id=q_id,
                    field_name=item.get("field_name", ""),
                    question_text=item.get("question_text", "")
                )
                questions.append(q)
            
            FORMS[req.form_id]["questions"] = [q.dict() for q in questions]
            return GenerateQuestionsResponse(questions=questions)
        except Exception as fallback_error:
            print(f"Fallback questions error: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
