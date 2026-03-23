from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class Question(BaseModel):
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    question_text: str
    hint: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None


class UserAnswer(BaseModel):
    question_id: str
    user_answer: str
    timestamp: datetime
    time_spent_seconds: Optional[int] = None


class Evaluation(BaseModel):
    is_correct: bool
    score: int = Field(..., ge=0, le=10)
    explanation: str
    correct_answer: str
    learning_tip: str


class QuizSession(BaseModel):
    session_id: str
    user_id: str
    questions: List[Question]
    answers: List[UserAnswer]
    evaluations: List[Evaluation]
    started_at: datetime
    finished_at: Optional[datetime] = None
    total_score: Optional[float] = None 