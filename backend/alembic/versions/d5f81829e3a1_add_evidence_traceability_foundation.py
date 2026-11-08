"""Add evidence traceability foundation

Revision ID: d5f81829e3a1
Revises: c4e78374f5c2
Create Date: 2026-11-08 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5f81829e3a1'
down_revision: Union[str, Sequence[str], None] = 'c4e78374f5c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update documents
    op.add_column('documents', sa.Column('investigation_id', sa.Integer(), nullable=True))

    # 2. Update findings
    op.add_column('findings', sa.Column('source_document_ids', sa.JSON(), nullable=True))
    op.add_column('findings', sa.Column('extracted_fields_used', sa.JSON(), nullable=True))
    op.add_column('findings', sa.Column('comparison_details', sa.JSON(), nullable=True))
    op.add_column('findings', sa.Column('evidence_limitations', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('missing_evidence_details', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('classification_rationale', sa.Text(), nullable=True))

    # 3. Update evidence_ledger_entries
    op.add_column('evidence_ledger_entries', sa.Column('po_document_id', sa.Integer(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('invoice_document_id', sa.Integer(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('receipt_document_id', sa.Integer(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('source_document_ids', sa.JSON(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('matching_criteria', sa.JSON(), nullable=True))

    # 4. Create association table for finding to document traceability
    op.create_table(
        'finding_documents',
        sa.Column('finding_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('finding_id', 'document_id')
    )

def downgrade() -> None:
    op.drop_table('finding_documents')
    # Note: SQLite does not support drop column directly without batch mode
    with op.batch_alter_table('evidence_ledger_entries') as batch_op:
        batch_op.drop_column('matching_criteria')
        batch_op.drop_column('source_document_ids')
        batch_op.drop_column('receipt_document_id')
        batch_op.drop_column('invoice_document_id')
        batch_op.drop_column('po_document_id')

    with op.batch_alter_table('findings') as batch_op:
        batch_op.drop_column('classification_rationale')
        batch_op.drop_column('missing_evidence_details')
        batch_op.drop_column('evidence_limitations')
        batch_op.drop_column('comparison_details')
        batch_op.drop_column('extracted_fields_used')
        batch_op.drop_column('source_document_ids')

    with op.batch_alter_table('documents') as batch_op:
        batch_op.drop_column('investigation_id')
