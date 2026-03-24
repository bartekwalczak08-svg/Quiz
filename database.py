# database.py
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

class QuizSessionORM(Base):
    """Model sesji quizu — odpowiada Pydantic QuizSession"""
    __tablename__ = "quiz_sessions"
    
    session_id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    total_score = Column(Float, nullable=True)
    
    # Relacje
    questions = relationship("QuestionORM", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuizSession(session_id='{self.session_id}', user_id='{self.user_id}')>"


class QuestionORM(Base):
    """Model pytania — odpowiada Pydantic Question"""
    __tablename__ = "questions"
    
    question_id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("quiz_sessions.session_id"), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    difficulty = Column(String(10), nullable=False)  # easy, medium, hard
    question_text = Column(String(2000), nullable=False)
    hint = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacje
    session = relationship("QuizSessionORM", back_populates="questions")
    answers = relationship("UserAnswerORM", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question(question_id='{self.question_id}', topic='{self.topic}', difficulty='{self.difficulty}')>"


class UserAnswerORM(Base):
    """Model odpowiedzi użytkownika — odpowiada Pydantic UserAnswer"""
    __tablename__ = "user_answers"
    
    answer_id = Column(String(36), primary_key=True)  # UUID
    question_id = Column(String(36), ForeignKey("questions.question_id"), nullable=False, index=True)
    user_answer = Column(String(2000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    
    # Relacje
    question = relationship("QuestionORM", back_populates="answers")
    evaluation = relationship("EvaluationORM", back_populates="answer", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserAnswer(answer_id='{self.answer_id}', user_answer='{self.user_answer[:20]}...')>"


class EvaluationORM(Base):
    """Model oceny — odpowiada Pydantic Evaluation"""
    __tablename__ = "evaluations"
    
    evaluation_id = Column(String(36), primary_key=True)  # UUID
    answer_id = Column(String(36), ForeignKey("user_answers.answer_id"), nullable=False, unique=True, index=True)
    is_correct = Column(Boolean, nullable=False)
    score = Column(Integer, nullable=False)  # 0-10
    explanation = Column(String(2000), nullable=False)
    correct_answer = Column(String(2000), nullable=False)
    learning_tip = Column(String(2000), nullable=False)
    
    # Relacje
    answer = relationship("UserAnswerORM", back_populates="evaluation")
    
    def __repr__(self):
        return f"<Evaluation(evaluation_id='{self.evaluation_id}', score={self.score}, correct={self.is_correct})>"


class Database:
    """Warstwa dostępu do bazy danych z SQLAlchemy"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///quiz.db"
            )
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Inicjalizuj bazę (utwórz tabele)"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Pobierz nową sesję"""
        return self.SessionLocal()
    
    def save_session(self, session_orm: QuizSessionORM) -> str:
        """Zapisz sesję quizu do bazy"""
        session = self.get_session()
        try:
            session.add(session_orm)
            session.commit()
            session_id = session_orm.session_id
            return session_id
        finally:
            session.close()
    
    def get_session_by_id(self, session_id: str) -> QuizSessionORM:
        """Pobierz sesję po ID"""
        session = self.get_session()
        try:
            return session.query(QuizSessionORM).filter_by(session_id=session_id).first()
        finally:
            session.close()
    
    def save_question(self, question_orm: QuestionORM) -> str:
        """Zapisz pytanie do bazy"""
        session = self.get_session()
        try:
            session.add(question_orm)
            session.commit()
            return question_orm.question_id
        finally:
            session.close()
    
    def save_answer(self, answer_orm: UserAnswerORM) -> str:
        """Zapisz odpowiedź do bazy"""
        session = self.get_session()
        try:
            session.add(answer_orm)
            session.commit()
            return answer_orm.answer_id
        finally:
            session.close()
    
    def save_evaluation(self, evaluation_orm: EvaluationORM) -> str:
        """Zapisz ocenę do bazy"""
        session = self.get_session()
        try:
            session.add(evaluation_orm)
            session.commit()
            return evaluation_orm.evaluation_id
        finally:
            session.close()
    
    def get_session_history(self, user_id: str, limit: int = 50) -> list:
        """Pobierz historię sesji dla użytkownika"""
        session = self.get_session()
        try:
            results = (
                session.query(QuizSessionORM)
                .filter_by(user_id=user_id)
                .order_by(QuizSessionORM.started_at.desc())
                .limit(limit)
                .all()
            )
            return results
        finally:
            session.close()
    
    def get_stats_by_topic(self, session_id: str) -> dict:
        """Pobierz statystyki dla sesji pogrupowane po tematach"""
        session = self.get_session()
        try:
            questions = (
                session.query(QuestionORM)
                .filter_by(session_id=session_id)
                .all()
            )
            
            stats = {}
            for q in questions:
                topic = q.topic
                if topic not in stats:
                    stats[topic] = {
                        "total": 0,
                        "correct": 0,
                        "avg_score": 0.0,
                        "max_score": 0,
                        "min_score": 10,
                        "scores": []
                    }
                
                stats[topic]["total"] += 1
                
                # Pobierz ocenę dla tego pytania
                answer = session.query(UserAnswerORM).filter_by(question_id=q.question_id).first()
                if answer and answer.evaluation:
                    evaluation = answer.evaluation
                    if evaluation.is_correct:
                        stats[topic]["correct"] += 1
                    stats[topic]["scores"].append(evaluation.score)
                    stats[topic]["max_score"] = max(stats[topic]["max_score"], evaluation.score)
                    stats[topic]["min_score"] = min(stats[topic]["min_score"], evaluation.score)
            
            # Oblicz średnią
            for topic in stats:
                if stats[topic]["scores"]:
                    stats[topic]["avg_score"] = round(
                        sum(stats[topic]["scores"]) / len(stats[topic]["scores"]),
                        2
                    )
                del stats[topic]["scores"]  # Usuń listę scores z wyniku
            
            return stats
        finally:
            session.close()
    
    def get_stats_by_user(self, user_id: str) -> dict:
        """Pobierz statystyki dla użytkownika"""
        session = self.get_session()
        try:
            sessions = (
                session.query(QuizSessionORM)
                .filter_by(user_id=user_id)
                .all()
            )
            
            total_sessions = len(sessions)
            total_questions = 0
            total_correct = 0
            all_scores = []
            
            for s in sessions:
                questions = session.query(QuestionORM).filter_by(session_id=s.session_id).all()
                for q in questions:
                    total_questions += 1
                    answer = session.query(UserAnswerORM).filter_by(question_id=q.question_id).first()
                    if answer and answer.evaluation:
                        evaluation = answer.evaluation
                        if evaluation.is_correct:
                            total_correct += 1
                        all_scores.append(evaluation.score)
            
            avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
            
            return {
                "user_id": user_id,
                "total_sessions": total_sessions,
                "total_questions": total_questions,
                "total_correct": total_correct,
                "avg_score": avg_score,
                "success_rate": round((total_correct / total_questions * 100), 2) if total_questions > 0 else 0
            }
        finally:
            session.close()
    
    def clear_all(self):
        """Wyczyść całą bazę (dla testów)"""
        session = self.get_session()
        try:
            session.query(EvaluationORM).delete()
            session.query(UserAnswerORM).delete()
            session.query(QuestionORM).delete()
            session.query(QuizSessionORM).delete()
            session.commit()
        finally:
            session.close()


# Globalna instancja
_db: Database = None

def get_database() -> Database:
    """Pobierz globalną instancję bazy"""
    global _db
    if _db is None:
        _db = Database()
        _db.init_db()
    return _db
