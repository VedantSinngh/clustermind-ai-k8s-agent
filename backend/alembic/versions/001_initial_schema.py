"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table(
        'clusters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('kubeconfig_secret_ref', sa.String(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'user_cluster_access',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('cluster_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'cluster_id')
    )
    op.create_table(
        'investigations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('cluster_id', sa.UUID(), nullable=False),
        sa.Column('namespace', sa.String(), nullable=True),
        sa.Column('root_cause', sa.String(), nullable=True),
        sa.Column('suggested_fix', sa.String(), nullable=True),
        sa.Column('suggested_command', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('raw_evidence', sa.JSON(), nullable=True),
        sa.Column('llm_response', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'investigation_progress',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('investigation_id', sa.UUID(), nullable=False),
        sa.Column('step', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'remediation_actions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('investigation_id', sa.UUID(), nullable=False),
        sa.Column('approved_by', sa.UUID(), nullable=False),
        sa.Column('command_executed', sa.String(), nullable=False),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('remediation_actions')
    op.drop_table('investigation_progress')
    op.drop_table('investigations')
    op.drop_table('user_cluster_access')
    op.drop_table('clusters')
    op.drop_table('users')
