"""initial schema - regulatory knowledge model

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-07

Creates all 10 tables for the ResearchMind regulatory knowledge model:
jurisdictions, authorities, regulatory_documents, document_versions,
amendments, clauses, clause_relationships, applicability_rules,
evidence_chunks, ingestion_jobs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Jurisdictions
    op.create_table(
        "jurisdictions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column(
            "parent_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=True,
        ),
        sa.Column("country_code", sa.String(10), nullable=False),
        sa.Column("state_code", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_jurisdictions_code", "jurisdictions", ["code"], unique=True)

    # 2. Authorities
    op.create_table(
        "authorities",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("abbreviation", sa.String(50), nullable=False),
        sa.Column(
            "jurisdiction_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=False,
        ),
        sa.Column("authority_type", sa.String(100), nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_authorities_abbreviation", "authorities", ["abbreviation"])

    # 3. Regulatory Documents
    op.create_table(
        "regulatory_documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("short_title", sa.String(100), nullable=True),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column(
            "authority_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("authorities.id"),
            nullable=False,
        ),
        sa.Column(
            "jurisdiction_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=False,
        ),
        sa.Column("subject_area", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 4. Document Versions
    op.create_table(
        "document_versions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("regulatory_documents.id"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(200), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("superseded_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_document_versions_doc_status",
        "document_versions",
        ["document_id", "status"],
    )

    # 5. Amendments
    op.create_table(
        "amendments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id"),
            nullable=False,
        ),
        sa.Column("amendment_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 6. Clauses
    op.create_table(
        "clauses",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id"),
            nullable=False,
        ),
        sa.Column("clause_number", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "parent_clause_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id"),
            nullable=True,
        ),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("clause_type", sa.String(50), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("start_page", sa.Integer(), nullable=True),
        sa.Column("end_page", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_clauses_path", "clauses", ["path"])
    op.create_index("ix_clauses_clause_number", "clauses", ["clause_number"])
    op.execute(
        "CREATE INDEX ix_clauses_content_fts ON clauses "
        "USING gin(to_tsvector('english', content))"
    )

    # 7. Clause Relationships
    op.create_table(
        "clause_relationships",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_clause_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id"),
            nullable=False,
        ),
        sa.Column(
            "target_clause_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_clause_relationships_source", "clause_relationships", ["source_clause_id"]
    )
    op.create_index(
        "ix_clause_relationships_target", "clause_relationships", ["target_clause_id"]
    )

    # 8. Applicability Rules
    op.create_table(
        "applicability_rules",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clause_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id"),
            nullable=False,
        ),
        sa.Column(
            "jurisdiction_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=True,
        ),
        sa.Column("building_type", sa.String(100), nullable=True),
        sa.Column("occupancy_type", sa.String(100), nullable=True),
        sa.Column("plot_area_min", sa.Float(), nullable=True),
        sa.Column("plot_area_max", sa.Float(), nullable=True),
        sa.Column("height_min", sa.Float(), nullable=True),
        sa.Column("height_max", sa.Float(), nullable=True),
        sa.Column("special_zone", sa.String(100), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_applicability_rules_clause", "applicability_rules", ["clause_id"]
    )
    op.create_index(
        "ix_applicability_rules_jurisdiction",
        "applicability_rules",
        ["jurisdiction_id"],
    )
    op.create_index(
        "ix_applicability_rules_building_type",
        "applicability_rules",
        ["building_type"],
    )

    # 9. Evidence Chunks
    op.create_table(
        "evidence_chunks",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clause_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id"),
            nullable=False,
        ),
        sa.Column(
            "document_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        # Structured queryable fields
        sa.Column(
            "jurisdiction_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=True,
        ),
        sa.Column("building_type", sa.String(100), nullable=True),
        sa.Column("occupancy_type", sa.String(100), nullable=True),
        sa.Column("topic", sa.String(200), nullable=True),
        # Page-level provenance
        sa.Column("start_page", sa.Integer(), nullable=True),
        sa.Column("end_page", sa.Integer(), nullable=True),
        sa.Column("bbox_json", sa.Text(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        # Vector store reference
        sa.Column("embedding_id", sa.String(100), nullable=True),
        # Parser metadata
        sa.Column("parser_metadata", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_evidence_chunks_clause", "evidence_chunks", ["clause_id"])
    op.create_index(
        "ix_evidence_chunks_jurisdiction", "evidence_chunks", ["jurisdiction_id"]
    )
    op.create_index("ix_evidence_chunks_topic", "evidence_chunks", ["topic"])

    # 10. Ingestion Jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("current_stage", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_stage", sa.String(50), nullable=True),
        sa.Column(
            "retry_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "parser_version", sa.String(50), nullable=False, server_default="0.1.0"
        ),
        sa.Column("pages_processed", sa.Integer(), nullable=True),
        sa.Column("pages_total", sa.Integer(), nullable=True),
        sa.Column("clauses_extracted", sa.Integer(), nullable=True),
        sa.Column("chunks_created", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ingestion_jobs_version", "ingestion_jobs", ["document_version_id"]
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.drop_table("evidence_chunks")
    op.drop_table("applicability_rules")
    op.drop_table("clause_relationships")
    op.drop_table("clauses")
    op.drop_table("amendments")
    op.drop_table("document_versions")
    op.drop_table("regulatory_documents")
    op.drop_table("authorities")
    op.drop_table("jurisdictions")
