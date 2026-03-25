-- schema.sql: ręczne utworzenie schematu bazy na podstawie migracji Alembic

CREATE TABLE quiz_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    total_score FLOAT,
    CONSTRAINT ix_quiz_sessions_user_id UNIQUE (user_id)
);
CREATE INDEX ix_quiz_sessions_user_id ON quiz_sessions (user_id);

CREATE TABLE questions (
    question_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(10) NOT NULL,
    question_text VARCHAR(2000) NOT NULL,
    hint VARCHAR(2000) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_questions_session_id FOREIGN KEY(session_id) REFERENCES quiz_sessions(session_id)
);
CREATE INDEX ix_questions_session_id ON questions (session_id);
CREATE INDEX ix_questions_topic ON questions (topic);

CREATE TABLE user_answers (
    answer_id VARCHAR(36) PRIMARY KEY,
    question_id VARCHAR(36) NOT NULL,
    user_answer VARCHAR(2000) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    time_spent_seconds INTEGER,
    CONSTRAINT fk_user_answers_question_id FOREIGN KEY(question_id) REFERENCES questions(question_id)
);
CREATE INDEX ix_user_answers_question_id ON user_answers (question_id);

CREATE TABLE evaluations (
    evaluation_id VARCHAR(36) PRIMARY KEY,
    answer_id VARCHAR(36) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    score INTEGER NOT NULL,
    explanation VARCHAR(2000) NOT NULL,
    correct_answer VARCHAR(2000) NOT NULL,
    learning_tip VARCHAR(2000) NOT NULL,
    CONSTRAINT fk_evaluations_answer_id FOREIGN KEY(answer_id) REFERENCES user_answers(answer_id)
);
CREATE INDEX ix_evaluations_answer_id ON evaluations (answer_id);
