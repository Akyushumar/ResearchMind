"""Add chunk structure and FTS

Revision ID: edf6907b2c17
Revises: 001_initial_schema
Create Date: 2026-09-09 05:46:58.751336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edf6907b2c17'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from sqlalchemy.sql.expression import text
from researchmind.models.evidence_chunk import TSVectorType

def upgrade() -> None:
    op.add_column('evidence_chunks', sa.Column('chunk_type', sa.String(length=50), nullable=True))
    op.add_column('evidence_chunks', sa.Column('embedding_model', sa.String(length=100), nullable=True))
    op.add_column('evidence_chunks', sa.Column('embedding_dimension', sa.Integer(), nullable=True))
    op.add_column('evidence_chunks', sa.Column('embedding_status', sa.String(length=50), nullable=True))
    op.add_column('evidence_chunks', sa.Column('clause_path', sa.String(length=255), nullable=True))
    op.add_column('evidence_chunks', sa.Column('hierarchy_context', sa.Text(), nullable=True))
    op.add_column('evidence_chunks', sa.Column('search_vector', TSVectorType(), sa.Computed(
        "setweight(to_tsvector('english', coalesce(clause_path, '')), 'A') || "
        "setweight(to_tsvector('english', coalesce(hierarchy_context, '')), 'B') || "
        "setweight(to_tsvector('english', coalesce(content, '')), 'C')",
        persisted=True), nullable=True))
    op.create_index('ix_evidence_chunks_search_vector', 'evidence_chunks', ['search_vector'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_evidence_chunks_search_vector', table_name='evidence_chunks', postgresql_using='gin')
    op.drop_column('evidence_chunks', 'search_vector')
    op.drop_column('evidence_chunks', 'hierarchy_context')
    op.drop_column('evidence_chunks', 'clause_path')
    op.drop_column('evidence_chunks', 'embedding_status')
    op.drop_column('evidence_chunks', 'embedding_dimension')
    op.drop_column('evidence_chunks', 'embedding_model')
    op.drop_column('evidence_chunks', 'chunk_type')
