"""add next check timestamp to monitors"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bd143a4ad122'
down_revision: Union[str, Sequence[str], None] = '694be93d8405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Add nullable column first
    op.add_column(
        "monitors",
        sa.Column(
            "next_check_at",
            sa.DateTime(),
            nullable=True
        )
    )

    # Backfill existing records
    op.execute(
        """
        UPDATE monitors
        SET next_check_at = UTC_TIMESTAMP()
        WHERE next_check_at IS NULL
        """
    )

    # Make column non-nullable
    op.alter_column(
        "monitors",
        "next_check_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    # Create index
    op.create_index(
        "ix_monitors_next_check_at",
        "monitors",
        ["next_check_at"],
        unique=False
    )


def downgrade() -> None:

    op.drop_index(
        "ix_monitors_next_check_at",
        table_name="monitors"
    )

    op.drop_column(
        "monitors",
        "next_check_at"
    )