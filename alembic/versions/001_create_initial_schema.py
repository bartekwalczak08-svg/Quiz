# alembic/versions/001_create_initial_schema.py
"""Create initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2024-03-24

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Utwórz tabelę quiz_sessions
    op.create_table(
        'quiz_sessions',
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('session_id'),
        sa.Index('ix_quiz_sessions_user_id', 'user_id')
    )
    
    # Utwórz tabelę questions
    op.create_table(
        'questions',
        sa.Column('question_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('difficulty', sa.String(10), nullable=False),
        sa.Column('question_text', sa.String(2000), nullable=False),
        sa.Column('hint', sa.String(2000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.session_id']),
        sa.PrimaryKeyConstraint('question_id'),
        sa.Index('ix_questions_session_id', 'session_id'),
        sa.Index('ix_questions_topic', 'topic')
    )
    
    # Utwórz tabelę user_answers
    op.create_table(
        'user_answers',
        sa.Column('answer_id', sa.String(36), nullable=False),
        sa.Column('question_id', sa.String(36), nullable=False),
        sa.Column('user_answer', sa.String(2000), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.question_id']),
        sa.PrimaryKeyConstraint('answer_id'),
        sa.Index('ix_user_answers_question_id', 'question_id')
    )
    
    # Utwórz tabelę evaluations
    op.create_table(
        'evaluations',
        sa.Column('evaluation_id', sa.String(36), nullable=False),
        sa.Column('answer_id', sa.String(36), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.String(2000), nullable=False),
        sa.Column('correct_answer', sa.String(2000), nullable=False),
        sa.Column('learning_tip', sa.String(2000), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['user_answers.answer_id']),
        sa.PrimaryKeyConstraint('evaluation_id'),
        sa.Index('ix_evaluations_answer_id', 'answer_id')
    )

def downgrade():
    op.drop_index('ix_evaluations_answer_id', 'evaluations')
    op.drop_table('evaluations')
    op.drop_index('ix_user_answers_question_id', 'user_answers')
    op.drop_table('user_answers')
    op.drop_index('ix_questions_topic', 'questions')
    op.drop_index('ix_questions_session_id', 'questions')
    op.drop_table('questions')
    op.drop_index('ix_quiz_sessions_user_id', 'quiz_sessions')
    op.drop_table('quiz_sessions')
