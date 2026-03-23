





import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models import Question, UserAnswer, Evaluation, QuizSession


# ============================================
# TESTY MODELU Question
# ============================================

def test_question_valid():
    q = Question(
        topic="Python",
        difficulty="easy",
        question_text="Co zwraca len([])?",
        hint="Pomyśl o pustej liście"
    )
    assert q.topic == "Python"
    assert q.difficulty == "easy"
    assert q.question_text == "Co zwraca len([])?"
    assert q.hint == "Pomyśl o pustej liście"


def test_question_invalid_difficulty():
    with pytest.raises(ValidationError):
        Question(
            topic="Python",
            difficulty="extreme",
            question_text="test",
            hint="test"
        )


def test_question_with_optional_fields():
    q = Question(
        topic="REST API",
        difficulty="medium",
        question_text="Co to REST?",
        hint="Representational State Transfer",
        id="q_123",
        created_at=datetime.now()
    )
    assert q.id == "q_123"
    assert q.created_at is not None


def test_question_missing_required_field():
    with pytest.raises(ValidationError):
        Question(
            topic="Python",
            difficulty="easy"
        )


# ============================================
# TESTY MODELU UserAnswer
# ============================================

def test_user_answer_valid():
    ua = UserAnswer(
        question_id="q_1",
        user_answer="0",
        timestamp=datetime.now()
    )
    assert ua.question_id == "q_1"
    assert ua.user_answer == "0"


def test_user_answer_with_time_spent():
    ua = UserAnswer(
        question_id="q_1",
        user_answer="print('hello')",
        timestamp=datetime.now(),
        time_spent_seconds=45
    )
    assert ua.time_spent_seconds == 45


def test_user_answer_missing_timestamp():
    with pytest.raises(ValidationError):
        UserAnswer(
            question_id="q_1",
            user_answer="test"
        )


# ============================================
# TESTY MODELU Evaluation
# ============================================

def test_evaluation_valid():
    e = Evaluation(
        is_correct=True,
        score=8,
        explanation="Dobra odpowiedź",
        correct_answer="0",
        learning_tip="Pamiętaj o len()"
    )
    assert e.is_correct is True
    assert e.score == 8


def test_evaluation_score_too_high():
    with pytest.raises(ValidationError):
        Evaluation(
            is_correct=True,
            score=11,
            explanation="test",
            correct_answer="test",
            learning_tip="test"
        )


def test_evaluation_score_negative():
    with pytest.raises(ValidationError):
        Evaluation(
            is_correct=False,
            score=-1,
            explanation="test",
            correct_answer="test",
            learning_tip="test"
        )


def test_evaluation_incorrect_answer():
    e = Evaluation(
        is_correct=False,
        score=3,
        explanation="Zła odpowiedź",
        correct_answer="print('hello')",
        learning_tip="Spróbuj jeszcze raz"
    )
    assert e.is_correct is False
    assert e.score < 5


# ============================================
# TESTY MODELU QuizSession
# ============================================

def test_quiz_session_valid():
    q = Question(
        topic="Python",
        difficulty="easy",
        question_text="Test?",
        hint="test"
    )
    ua = UserAnswer(
        question_id="q_1",
        user_answer="answer",
        timestamp=datetime.now()
    )
    e = Evaluation(
        is_correct=True,
        score=10,
        explanation="Perfect",
        correct_answer="answer",
        learning_tip="Good"
    )

    session = QuizSession(
        session_id="s_1",
        user_id="u_1",
        questions=[q],
        answers=[ua],
        evaluations=[e],
        started_at=datetime.now()
    )

    assert session.session_id == "s_1"
    assert len(session.questions) == 1
    assert session.finished_at is None


def test_quiz_session_with_end_time():
    now = datetime.now()
    session = QuizSession(
        session_id="s_2",
        user_id="u_2",
        questions=[],
        answers=[],
        evaluations=[],
        started_at=now,
        finished_at=now,
        total_score=8.5
    )
    assert session.finished_at is not None
    assert session.total_score == 8.5


def test_quiz_session_empty_lists():
    session = QuizSession(
        session_id="s_3",
        user_id="u_3",
        questions=[],
        answers=[],
        evaluations=[],
        started_at=datetime.now()
    )
    assert len(session.questions) == 0
    assert len(session.answers) == 0


def test_quiz_session_missing_required_field():
    with pytest.raises(ValidationError):
        QuizSession(
            session_id="s_4",
            user_id="u_4",
            questions=[],
            answers=[],
            evaluations=[]
        )