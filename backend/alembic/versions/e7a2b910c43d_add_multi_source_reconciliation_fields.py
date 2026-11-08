"""Add multi source reconciliation fields

Revision ID: e7a2b910c43d
Revises: d5f81829e3a1
Create Date: 2026-11-08 13:06:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7a2b910c43d'
down_revision: Union[str, Sequence[str], None] = 'd5f81829e3a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('evidence_ledger_entries', sa.Column('transaction_id', sa.String(length=100), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('supplier_name', sa.String(length=255), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('paid_amount', sa.Float(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('approved_variation_amount', sa.Float(), server_default='0.0', nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('variance_amount', sa.Float(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('variance_reason', sa.String(length=500), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('match_confidence', sa.String(length=50), server_default='EXACT_MATCH', nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('requires_human_review', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('human_review_reason', sa.String(length=500), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('multiple_invoices_breakdown', sa.JSON(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('multiple_receipts_breakdown', sa.JSON(), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('project_report_reference', sa.String(length=100), nullable=True))
    op.add_column('evidence_ledger_entries', sa.Column('report_reconciled', sa.Boolean(), server_default='0', nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('evidence_ledger_entries') as batch_op:
        batch_op.drop_column('report_reconciled')
        batch_op.drop_column('project_report_reference')
        batch_op.drop_column('multiple_receipts_breakdown')
        batch_op.drop_column('multiple_invoices_breakdown')
        batch_op.drop_column('human_review_reason')
        batch_op.drop_column('requires_human_review')
        batch_op.drop_column('match_confidence')
        batch_op.drop_column('variance_reason')
        batch_op.drop_column('variance_amount')
        batch_op.drop_column('approved_variation_amount')
        batch_op.drop_column('paid_amount')
        batch_op.drop_column('supplier_name')
        batch_op.drop_column('transaction_id')
