# tests/test_database_broken.py
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, QuizSessionORM, QuestionORM, UserAnswerORM, EvaluationORM
import uuid

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# BŁĄD 1: Brak commit — poprawiony
def test_save_session_no_commit(db_session):
    session_orm = QuizSessionORM(
        session_id=str(uuid.uuid4()),
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()  # Poprawka: commit
    retrieved = db_session.query(QuizSessionORM).first()
    assert retrieved is not None

# BŁĄD 2: Typ mismatch — poprawiony
def test_question_field_type_mismatch(db_session):
    session_orm = QuizSessionORM(
        session_id=str(uuid.uuid4()),
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    question_orm = QuestionORM(
        question_id=str(uuid.uuid4()),
        session_id=session_orm.session_id,
        topic="Python",
        difficulty="easy",
        question_text="Test?",
        hint="Test",
        created_at=datetime.utcnow()
    )
    db_session.add(question_orm)
    db_session.commit()
    retrieved = db_session.query(QuestionORM).first()
    assert isinstance(retrieved.created_at, datetime)  # Poprawka: sprawdzamy typ

# BŁĄD 3: FK — poprawiony
def test_evaluation_without_answer(db_session):
    # Najpierw tworzę UserAnswerORM
    answer_orm = UserAnswerORM(
        answer_id=str(uuid.uuid4()),
        question_id=str(uuid.uuid4()),
        user_answer="answer",
        timestamp=datetime.utcnow()
    )
    db_session.add(answer_orm)
    db_session.commit()
    evaluation_orm = EvaluationORM(
        evaluation_id=str(uuid.uuid4()),
        answer_id=answer_orm.answer_id,
        is_correct=True,
        score=10,
        explanation="Test",
        correct_answer="Test",
        learning_tip="Test"
    )
    db_session.add(evaluation_orm)
    db_session.commit()
    retrieved = db_session.query(EvaluationORM).filter_by(answer_id=answer_orm.answer_id).first()
    assert retrieved is not None

# BŁĄD 4: Logika odwrotna — poprawiony
def test_get_correct_answers_reverse_logic(db_session):
    session_id = str(uuid.uuid4())
    session_orm = QuizSessionORM(
        session_id=session_id,
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    for is_correct in [True, False]:
        question_id = str(uuid.uuid4())
        q_orm = QuestionORM(
            question_id=question_id,
            session_id=session_id,
            topic="Python",
            difficulty="easy",
            question_text="Test?",
            hint="Test",
            created_at=datetime.utcnow()
        )
        db_session.add(q_orm)
        db_session.commit()
        a_orm = UserAnswerORM(
            answer_id=str(uuid.uuid4()),
            question_id=question_id,
            user_answer="answer",
            timestamp=datetime.utcnow()
        )
        db_session.add(a_orm)
        db_session.commit()
        e_orm = EvaluationORM(
            evaluation_id=str(uuid.uuid4()),
            answer_id=a_orm.answer_id,
            is_correct=is_correct,
            score=8,
            explanation="Test",
            correct_answer="correct",
            learning_tip="tip"
        )
        db_session.add(e_orm)
    db_session.commit()
    correct_evaluations = db_session.query(EvaluationORM).filter_by(is_correct=True).all()
    assert len(correct_evaluations) == 1  # Poprawka: powinno być 1

# BŁĄD 5: Brak asercji — poprawiony
def test_save_and_retrieve_no_assertion(db_session):
    session_orm = QuizSessionORM(
        session_id=str(uuid.uuid4()),
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    retrieved = db_session.query(QuizSessionORM).first()
    assert retrieved is not None  # Poprawka: dodano asercję

# BŁĄD 6: Nieistniejące pole — poprawiony
def test_answer_missing_field(db_session):
    session_orm = QuizSessionORM(
        session_id=str(uuid.uuid4()),
        user_id="user_123",
        started_at=datetime.utcnow()
    )
    db_session.add(session_orm)
    db_session.commit()
    question_orm = QuestionORM(
        question_id=str(uuid.uuid4()),
        session_id=session_orm.session_id,
        topic="Python",
        difficulty="easy",
        question_text="Test?",
        hint="Test",
        created_at=datetime.utcnow()
    )
    db_session.add(question_orm)
    db_session.commit()
    answer_orm = UserAnswerORM(
        answer_id=str(uuid.uuid4()),
        question_id=question_orm.question_id,
        user_answer="answer",
        timestamp=datetime.utcnow()
    )
    db_session.add(answer_orm)
    db_session.commit()
    retrieved = db_session.query(UserAnswerORM).first()
    assert hasattr(retrieved, "question_id")  # Poprawka: pole istniejące
