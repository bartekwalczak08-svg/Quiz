
import os
import sys
import uuid
from pathlib import Path

# Dodaj src do sys.path jeśli nie ma
SRC_PATH = str(Path(__file__).parent / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
from datetime import datetime

from database import (
    get_database, 
    QuizSessionORM, 
    QuestionORM, 
    UserAnswerORM, 
    EvaluationORM
)
from llm_service import generate_question, evaluate_answer


class QuizApp:
    def __init__(self, user_id: str = None):
        self.db = get_database()
        self.user_id = user_id or os.getenv("USER_ID", "default_user")
        self.current_session_id = None
        self.running = True

        # Sprawdź czy API key jest ustawiony
        if not os.getenv("OPENROUTER_API_KEY"):
            print("⚠️  Uwaga: OPENROUTER_API_KEY nie jest ustawiony!")
            print("   Quiz może nie działać poprawnie.\n")

    def _start_session(self) -> str:
        """Utwórz nową sesję quizu"""
        session_orm = QuizSessionORM(
            session_id=str(uuid.uuid4()),
            user_id=self.user_id,
            started_at=datetime.now()
        )
        self.db.save_session(session_orm)
        self.current_session_id = session_orm.session_id
        return self.current_session_id

    def _end_session(self, total_score: float = None):
        """Zakończ bieżącą sesję"""
        if self.current_session_id:
            session = self.db.get_session()
            try:
                session_orm = session.query(QuizSessionORM).filter_by(
                    session_id=self.current_session_id
                ).first()
                if session_orm:
                    session_orm.finished_at = datetime.now()
                    session_orm.total_score = total_score
                    session.commit()
            finally:
                session.close()
            self.current_session_id = None

    def display_header(self):
        """Wyświetl nagłówek aplikacji"""
        print("\n" + "=" * 60)
        print("🎓 AI QUIZ MASTER — Inteligentny system quizów")
        print("=" * 60 + "\n")

    def display_menu(self):
        """Wyświetl menu główne"""
        print("\n--- MENU ---")
        print("1️⃣  Rozpocznij quiz")
        print("2️⃣  Historia wyników")
        print("3️⃣  Statystyki")
        print("4️⃣  Wyjście")
        print("-" * 30)

    def get_valid_choice(self, prompt: str, valid_options: list) -> str:
        """Pobierz walidowany wybór od użytkownika"""
        while True:
            choice = input(prompt).strip()
            if choice in valid_options:
                return choice
            print(f"❌ Nieprawidłowy wybór. Wybierz z: {', '.join(valid_options)}")

    def run_quiz(self):
        """Uruchom quiz"""
        print("\n📝 NOWY QUIZ\n")

        # Pobierz temat
        topic = input("Temat (Python/SQL/Pydantic/Inne): ").strip()
        if not topic:
            print("❌ Temat nie może być pusty!")
            return

        # Pobierz poziom trudności
        difficulty = self.get_valid_choice(
            "Poziom (easy/medium/hard): ",
            ["easy", "medium", "hard"]
        )

        print("\n⏳ Generuję pytanie...\n")

        try:
            # Rozpocznij sesję
            self._start_session()

            # Generuj pytanie
            question = generate_question(topic, difficulty)

            # Zapisz pytanie do bazy
            question_id = str(uuid.uuid4())
            question_orm = QuestionORM(
                question_id=question_id,
                session_id=self.current_session_id,
                topic=question.topic,
                difficulty=question.difficulty,
                question_text=question.question_text,
                hint=question.hint,
                created_at=datetime.now()
            )
            self.db.save_question(question_orm)

            print(f"📌 Temat: {question.topic}")
            print(f"📊 Poziom: {question.difficulty.upper()}")
            print(f"\n📝 Pytanie:\n{question.question_text}\n")
            print(f"💡 Podpowiedź: {question.hint}\n")

            # Pobierz odpowiedź
            user_answer = input("Twoja odpowiedź: ").strip()
            if not user_answer:
                print("❌ Odpowiedź nie może być pusta!")
                self._end_session()
                return

            print("\n⏳ Oceniam odpowiedź...\n")

            # Zapisz odpowiedź do bazy
            answer_id = str(uuid.uuid4())
            answer_orm = UserAnswerORM(
                answer_id=answer_id,
                question_id=question_id,
                user_answer=user_answer,
                timestamp=datetime.now()
            )
            self.db.save_answer(answer_orm)

            # Oceń odpowiedź
            evaluation = evaluate_answer(question.question_text, user_answer)

            # Zapisz ocenę do bazy
            evaluation_orm = EvaluationORM(
                evaluation_id=str(uuid.uuid4()),
                answer_id=answer_id,
                is_correct=evaluation.is_correct,
                score=evaluation.score,
                explanation=evaluation.explanation,
                correct_answer=evaluation.correct_answer,
                learning_tip=evaluation.learning_tip
            )
            self.db.save_evaluation(evaluation_orm)

            # Wyświetl wynik
            emoji = "✅" if evaluation.is_correct else "❌"
            print(f"{emoji} WYNIK: {evaluation.score}/10")
            print(f"\n📖 Wyjaśnienie:")
            print(f"{evaluation.explanation}\n")
            print(f"🎯 Wskazówka edukacyjna:")
            print(f"{evaluation.learning_tip}\n")
            print(f"📌 Poprawna odpowiedź/Pełne wyjaśnienie:")
            print(f"{evaluation.correct_answer}\n")

            # Zakończ sesję
            self._end_session(total_score=evaluation.score)
            print("✅ Wynik zapisany do bazy danych!\n")

        except ValueError as e:
            print(f"❌ Błąd walidacji: {e}")
            self._end_session()
        except Exception as e:
            print(f"❌ Błąd: {e}")
            self._end_session()

    def show_history(self):
        """Wyświetl historię wyników"""
        print("\n📋 HISTORIA WYNIKÓW\n")

        db_session = self.db.get_session()
        try:
            sessions = (
                db_session.query(QuizSessionORM)
                .filter_by(user_id=self.user_id)
                .order_by(QuizSessionORM.started_at.desc())
                .limit(50)
                .all()
            )

            if not sessions:
                print("📭 Brak wyników w historii\n")
                return

            print(f"{'Data':<20} {'Temat':<12} {'Pytanie':<30} {'Wynik':<8} {'Status':<6}")
            print("-" * 80)

            for quiz_session in sessions:
                questions = db_session.query(QuestionORM).filter_by(
                    session_id=quiz_session.session_id
                ).all()

                for q in questions:
                    answer = db_session.query(UserAnswerORM).filter_by(
                        question_id=q.question_id
                    ).first()

                    if answer and answer.evaluation:
                        timestamp = q.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        topic = q.topic[:12]
                        question_text = q.question_text[:28]
                        score = f"{answer.evaluation.score}/10"
                        status = "✅" if answer.evaluation.is_correct else "❌"

                        print(f"{timestamp:<20} {topic:<12} {question_text:<30} {score:<8} {status:<6}")
        finally:
            db_session.close()

        print()

    def show_statistics(self):
        """Wyświetl statystyki"""
        print("\n📊 STATYSTYKI\n")

        stats = self.db.get_stats_by_user(self.user_id)

        if stats["total_questions"] == 0:
            print("📭 Brak danych do wyświetlenia\n")
            return

        print(f"👤 Użytkownik: {stats['user_id']}")
        print(f"📝 Liczba sesji: {stats['total_sessions']}")
        print(f"❓ Liczba pytań: {stats['total_questions']}")
        print(f"✅ Poprawnych odpowiedzi: {stats['total_correct']}")
        print(f"📈 Średni wynik: {stats['avg_score']}/10")
        print(f"🎯 Skuteczność: {stats['success_rate']}%")
        print()

    def run(self):
        """Główna pętla aplikacji"""
        self.display_header()

        while self.running:
            self.display_menu()
            choice = input("\nWybierz opcję (1-4): ").strip()

            if choice == "1":
                self.run_quiz()
            elif choice == "2":
                self.show_history()
            elif choice == "3":
                self.show_statistics()
            elif choice == "4":
                self.shutdown()
            else:
                print("❌ Nieprawidłowy wybór. Spróbuj ponownie.\n")

    def shutdown(self):
        """Zamknij aplikację"""
        print("\n👋 Do zobaczenia! Dziękuję za użytkowanie AI Quiz Master!\n")
        self.running = False


if __name__ == "__main__":
    app = QuizApp()
    app.run()
