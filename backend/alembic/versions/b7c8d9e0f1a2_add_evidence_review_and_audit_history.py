"""Add evidence review and audit history

Revision ID: b7c8d9e0f1a2
Revises: a8f9e0c1d2b3
Create Date: 2026-11-08 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a8f9e0c1d2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'document_field_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('original_value', sa.JSON(), nullable=True),
        sa.Column('reviewed_value', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('reviewer_id', sa.String(length=100), nullable=True),
        sa.Column('review_timestamp', sa.DateTime(), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('extraction_method', sa.String(length=100), nullable=True),
        sa.Column('original_document_sha256', sa.String(length=64), nullable=True),
        sa.Column('extraction_version', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'field_name', name='uq_document_field_review')
    )
    op.create_index('ix_document_field_reviews_id', 'document_field_reviews', ['id'], unique=False)
    op.create_index('ix_document_field_reviews_document_id', 'document_field_reviews', ['document_id'], unique=False)
    op.create_index('ix_document_field_reviews_field_name', 'document_field_reviews', ['field_name'], unique=False)
    op.create_index('ix_document_field_reviews_status', 'document_field_reviews', ['status'], unique=False)

    op.create_table(
        'field_review_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('field_review_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('previous_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('reviewer_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('action_timestamp', sa.DateTime(), nullable=False),
        sa.Column('document_sha256', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_review_id'], ['document_field_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_field_review_history_id', 'field_review_history', ['id'], unique=False)
    op.create_index('ix_field_review_history_field_review_id', 'field_review_history', ['field_review_id'], unique=False)
    op.create_index('ix_field_review_history_document_id', 'field_review_history', ['document_id'], unique=False)
    op.create_index('ix_field_review_history_field_name', 'field_review_history', ['field_name'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_field_review_history_field_name', table_name='field_review_history')
    op.drop_index('ix_field_review_history_document_id', table_name='field_review_history')
    op.drop_index('ix_field_review_history_field_review_id', table_name='field_review_history')
    op.drop_index('ix_field_review_history_id', table_name='field_review_history')
    op.drop_table('field_review_history')

    op.drop_index('ix_document_field_reviews_status', table_name='document_field_reviews')
    op.drop_index('ix_document_field_reviews_field_name', table_name='document_field_reviews')
    op.drop_index('ix_document_field_reviews_document_id', table_name='document_field_reviews')
    op.drop_index('ix_document_field_reviews_id', table_name='document_field_reviews')
    op.drop_table('document_field_reviews')
