"""create bugs table"""
revision = "0001"
down_revision = None

import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    op.create_table(
        "bugs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("component", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("reported_on", sa.Date, nullable=False),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("bugs")
