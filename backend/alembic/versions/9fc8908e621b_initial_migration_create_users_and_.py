"""Initial migration: create users and knowledge_relations tables

Revision ID: 9fc8908e621b
Revises: 
Create Date: 2025-06-10 02:14:10.843352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9fc8908e621b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 创建users表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 创建索引
    op.create_index('ix_users_name', 'users', ['name'])
    op.create_index('ix_users_email', 'users', ['email'])

    # 创建knowledge_relations表
    op.create_table(
        'knowledge_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_note_id', sa.String(length=24), nullable=False),
        sa.Column('related_note_ids', postgresql.ARRAY(sa.String(length=24)), nullable=False, default=[]),
        sa.Column('relation_strength', sa.Float(), nullable=False, default=0.0),
        sa.Column('relation_context', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_knowledge_relations_source_note_id', 'knowledge_relations', ['source_note_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 删除索引
    op.drop_index('ix_knowledge_relations_source_note_id', 'knowledge_relations')
    op.drop_index('ix_users_email', 'users')
    op.drop_index('ix_users_name', 'users')

    # 删除表
    op.drop_table('knowledge_relations')
    op.drop_table('users')
