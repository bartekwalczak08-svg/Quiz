# tests/test_database.py
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, QuizSessionORM, QuestionORM, UserAnswerORM, EvaluationORM
from src.models import Question, UserAnswer, Evaluation, QuizSession
import uuid

@pytest.fixture
def db_session():
    """Fixture dla in-memory SQLite bazy"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_save_and_retrieve_session(db_session):
    """Test zapisu i pobrania sesji quizu"""
    session_id = str(uuid.uuid4())
    user_id = "user_123"
    
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id=user_id,
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    
    retrieved = db_session.query(QuizSessionORM).filter_by(session_id=session_id).first()
    assert retrieved is not None
    assert retrieved.user_id == user_id
    assert retrieved.session_id == session_id

def test_save_question_with_session(db_session):
    """Test zapisu pytania powiązanego z sesją"""
    session_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())
    
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    
    question_orm = QuestionORM(
        question_id=question_id,
        session_id=session_id,
        topic="Python",
        difficulty="easy",
        question_text="Co zwraca len([])?",
        hint="Funkcja len() zwraca długość",
        created_at=datetime.utcnow()
    )
    db_session.add(question_orm)
    db_session.commit()
    
    retrieved = db_session.query(QuestionORM).filter_by(question_id=question_id).first()
    assert retrieved is not None
    assert retrieved.topic == "Python"
    assert retrieved.difficulty == "easy"

def test_save_answer_and_evaluation(db_session):
    """Test zapisu odpowiedzi i oceny"""
    session_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())
    
    # Stwórz sesję i pytanie
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    
    question_orm = QuestionORM(
        question_id=question_id,
        session_id=session_id,
        topic="Python",
        difficulty="easy",
        question_text="Co zwraca len([])?",
        hint="Funkcja len()",
        created_at=datetime.utcnow()
    )
    db_session.add(question_orm)
    db_session.commit()
    
    # Dodaj odpowiedź
    answer_orm = UserAnswerORM(
        answer_id=str(uuid.uuid4()),
        question_id=question_id,
        user_answer="0",
        timestamp=datetime.utcnow(),
        time_spent_seconds=45
    )
    db_session.add(answer_orm)
    db_session.commit()
    
    # Dodaj ocenę
    evaluation_orm = EvaluationORM(
        evaluation_id=str(uuid.uuid4()),
        answer_id=answer_orm.answer_id,
        is_correct=True,
        score=10,
        explanation="Poprawnie!",
        correct_answer="0",
        learning_tip="len() zwraca liczbę elementów"
    )
    db_session.add(evaluation_orm)
    db_session.commit()
    
    # Weryfikacja
    retrieved_answer = db_session.query(UserAnswerORM).filter_by(question_id=question_id).first()
    assert retrieved_answer is not None
    assert retrieved_answer.user_answer == "0"
    
    retrieved_eval = db_session.query(EvaluationORM).filter_by(answer_id=answer_orm.answer_id).first()
    assert retrieved_eval is not None
    assert retrieved_eval.is_correct == True
    assert retrieved_eval.score == 10

def test_get_session_with_questions(db_session):
    """Test pobrania sesji ze wszystkimi pytaniami"""
    session_id = str(uuid.uuid4())
    
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    
    # Dodaj 3 pytania
    for i in range(3):
        question_orm = QuestionORM(
            question_id=str(uuid.uuid4()),
            session_id=session_id,
            topic="Python",
            difficulty="easy",
            question_text=f"Pytanie {i+1}?",
            hint=f"Podpowiedź {i+1}",
            created_at=datetime.utcnow()
        )
        db_session.add(question_orm)
    db_session.commit()
    
    questions = db_session.query(QuestionORM).filter_by(session_id=session_id).all()
    assert len(questions) == 3

def test_get_stats_by_topic(db_session):
    """Test statystyk dla danego tematu"""
    session_id = str(uuid.uuid4())
    user_id = "user_123"
    
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id=user_id,
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    
    # Dodaj pytania i oceny
    test_data = [
        ("Python", "easy", True, 8),
        ("Python", "medium", False, 3),
        ("SQL", "hard", True, 10)
    ]
    
    for topic, difficulty, is_correct, score in test_data:
        question_id = str(uuid.uuid4())
        question_orm = QuestionORM(
            question_id=question_id,
            session_id=session_id,
            topic=topic,
            difficulty=difficulty,
            question_text="Test?",
            hint="Test",
            created_at=datetime.utcnow()
        )
        db_session.add(question_orm)
        db_session.commit()
        
        answer_orm = UserAnswerORM(
            answer_id=str(uuid.uuid4()),
            question_id=question_id,
            user_answer="answer",
            timestamp=datetime.utcnow()
        )
        db_session.add(answer_orm)
        db_session.commit()
        
        evaluation_orm = EvaluationORM(
            evaluation_id=str(uuid.uuid4()),
            answer_id=answer_orm.answer_id,
            is_correct=is_correct,
            score=score,
            explanation="Test",
            correct_answer="correct",
            learning_tip="tip"
        )
        db_session.add(evaluation_orm)
    db_session.commit()
    
    # Weryfikacja statystyk dla Pythona
    python_questions = db_session.query(QuestionORM).filter_by(topic="Python").all()
    assert len(python_questions) == 2
    
    python_correct = sum(
        1 for q in python_questions
        for a in db_session.query(UserAnswerORM).filter_by(question_id=q.question_id).all()
        for e in db_session.query(EvaluationORM).filter_by(answer_id=a.answer_id).all()
        if e.is_correct
    )
    assert python_correct == 1
