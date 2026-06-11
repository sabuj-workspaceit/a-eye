"""Revision script template.

This file is used as a template for Alembic revision scripts.
"""

from alembic import op
import sqlalchemy as sa


revision = "8ea6011e3751"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zone_maps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "protocols",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "zone_regions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("zone_map_id", sa.Integer(), sa.ForeignKey("zone_maps.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("coordinates", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("zone_region_id", sa.Integer(), sa.ForeignKey("zone_regions.id"), nullable=False),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("input_data", sa.Text(), nullable=True),
        sa.Column("result_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("analysis_job_id", sa.Integer(), sa.ForeignKey("analysis_jobs.id"), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("rules.id"), nullable=False),
        sa.Column("zone_region_id", sa.Integer(), sa.ForeignKey("zone_regions.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("finding_id", sa.Integer(), sa.ForeignKey("findings.id"), nullable=False),
        sa.Column("observation_type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("analysis_job_id", sa.Integer(), sa.ForeignKey("analysis_jobs.id"), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "report_sections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("report_sections")
    op.drop_table("reports")
    op.drop_table("observations")
    op.drop_table("findings")
    op.drop_table("analysis_jobs")
    op.drop_table("rules")
    op.drop_table("zone_regions")
    op.drop_table("protocols")
    op.drop_table("zone_maps")
