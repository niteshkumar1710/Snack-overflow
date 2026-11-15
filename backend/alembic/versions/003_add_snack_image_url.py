"""add optional image_url to snacks table

Revision ID: 003_add_snack_image_url
Revises: 002_add_idempotency_keys
Create Date: 2026-11-15 21:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_add_snack_image_url"
down_revision: Union[str, None] = "002_add_idempotency_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "snacks",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("snacks", "image_url")
