"""Add analysis tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251005_add_analysis_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_analysis_snapshot_id"), "analysis", ["snapshot_id"], unique=False)

    op.create_table(
        "analysis_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_analysis_item_analysis_id"), "analysis_item", ["analysis_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_item_analysis_id"), table_name="analysis_item")
    op.drop_table("analysis_item")
    op.drop_index(op.f("ix_analysis_snapshot_id"), table_name="analysis")
    op.drop_table("analysis")
