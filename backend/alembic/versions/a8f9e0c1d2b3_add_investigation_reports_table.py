"""Add investigation reports snapshot architecture

Revision ID: a8f9e0c1d2b3
Revises: e7a2b910c43d
Create Date: 2026-11-08 13:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a8f9e0c1d2b3'
down_revision: Union[str, Sequence[str], None] = 'e7a2b910c43d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'investigation_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('investigation_id', sa.Integer(), nullable=False),
        sa.Column('report_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('report_status', sa.String(length=50), nullable=False, server_default='FINAL'),
        sa.Column('report_title', sa.String(length=255), nullable=False),
        sa.Column('generation_timestamp', sa.DateTime(), nullable=False),
        sa.Column('reporting_schema_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('methodology_version', sa.String(length=100), nullable=False, server_default='VaultPilot-Audit-Methodology-2.0'),
        sa.Column('investigation_scope', sa.String(length=500), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('financial_summary', sa.JSON(), nullable=False),
        sa.Column('investigation_limitations', sa.Text(), nullable=True),
        sa.Column('requires_human_review', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('snapshot_payload', sa.JSON(), nullable=False),
        sa.Column('snapshot_integrity_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investigation_reports_id', 'investigation_reports', ['id'], unique=False)
    op.create_index('ix_investigation_reports_investigation_id', 'investigation_reports', ['investigation_id'], unique=False)
    op.create_index('ix_investigation_reports_project_id', 'investigation_reports', ['project_id'], unique=False)
    op.create_index('ix_reports_investigation_version', 'investigation_reports', ['investigation_id', 'report_version'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_reports_investigation_version', table_name='investigation_reports')
    op.drop_index('ix_investigation_reports_project_id', table_name='investigation_reports')
    op.drop_index('ix_investigation_reports_investigation_id', table_name='investigation_reports')
    op.drop_index('ix_investigation_reports_id', table_name='investigation_reports')
    op.drop_table('investigation_reports')
