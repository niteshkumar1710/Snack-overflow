"""create users snacks votes and activities tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-14 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='member', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'member')", name='ck_users_role'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Snacks Table
    op.create_table(
        'snacks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('low_stock_threshold', sa.Integer(), server_default='5', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity >= 0', name='ck_snacks_quantity_non_negative'),
        sa.CheckConstraint('low_stock_threshold >= 0', name='ck_snacks_threshold_non_negative'),
        sa.CheckConstraint("category IN ('sweet', 'savoury', 'drink', 'healthy-ish')", name='ck_snacks_category'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_snacks_name'), 'snacks', ['name'], unique=True)

    # 3. Votes Table
    op.create_table(
        'votes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snack_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['snack_id'], ['snacks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'snack_id', name='uq_user_snack_vote'),
    )
    op.create_index(op.f('ix_votes_snack_id'), 'votes', ['snack_id'], unique=False)
    op.create_index(op.f('ix_votes_user_id'), 'votes', ['user_id'], unique=False)

    # 4. Activities Table
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snack_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("action IN ('consumed', 'restocked')", name='ck_activities_action'),
        sa.CheckConstraint('amount > 0', name='ck_activities_amount_positive'),
        sa.ForeignKeyConstraint(['snack_id'], ['snacks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_activities_snack_id'), 'activities', ['snack_id'], unique=False)
    op.create_index(op.f('ix_activities_user_id'), 'activities', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_activities_user_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_snack_id'), table_name='activities')
    op.drop_table('activities')

    op.drop_index(op.f('ix_votes_user_id'), table_name='votes')
    op.drop_index(op.f('ix_votes_snack_id'), table_name='votes')
    op.drop_table('votes')

    op.drop_index(op.f('ix_snacks_name'), table_name='snacks')
    op.drop_table('snacks')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
