"""Stub migration maintained for documentation purposes."""
from __future__ import annotations

revision = "20251005"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover
    """No-op: the in-memory repository does not require migrations."""


def downgrade() -> None:  # pragma: no cover
    """No-op downgrade."""
