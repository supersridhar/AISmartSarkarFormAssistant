# app/models.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}


class UploadResponse(BaseModel):
    form_id: str
    fields: List[str]


class ExplainFormRequest(BaseModel):
    form_id: str
    language: str = "en"  # Language to explain in


class ExplainFormResponse(BaseModel):
    form_id: str
    form_type: str
    purpose: str
    sections: List[str]
    summary: str


class SuggestFieldsRequest(BaseModel):
    form_id: str
    language: str = "en"


class SuggestFieldsResponse(BaseModel):
    form_id: str
    fields: List[str]


class GenerateQuestionsRequest(BaseModel):
    form_id: str
    language: str
    fields: Optional[List[str]] = None  # Optional: use extracted fields if not provided


class Question(BaseModel):
    id: str
    field_name: str
    question_text: str
    field_type: Optional[str] = "text"


class GenerateQuestionsResponse(BaseModel):
    questions: List[Question]


class SubmitAnswersRequest(BaseModel):
    form_id: str
    answers: Dict[str, str]  # key = question.id


class AnnotatedField(BaseModel):
    field_name: str
    value: str
    x: int
    y: int


class AnnotatedFormResponse(BaseModel):
    form_id: str
    annotated_fields: List[AnnotatedField]
