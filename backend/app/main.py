# app/main.py
import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
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
async def upload_form(file: UploadFile = File(...), language: str = "en"):
    """Upload a form image and extract text."""
    form_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(UPLOAD_DIR, f"{form_id}{file_ext}")

    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Extract text from the form
    text = extract_text(save_path, language)
    
    # Infer fields from extracted text
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
    """Explain the form content in the user's language."""
    if req.form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")

    form_data = FORMS[req.form_id]
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

    # Use provided fields or get from stored form
    fields = req.fields if req.fields else FORMS[req.form_id].get("fields", [])
    
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
