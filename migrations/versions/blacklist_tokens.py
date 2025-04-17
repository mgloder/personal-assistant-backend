"""create blacklisted_tokens table

Revision ID: blacklist_tokens
Revises: 20240417_initial
Create Date: 2024-04-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'blacklist_tokens'
down_revision = '20240417_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'blacklisted_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('blacklisted_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blacklisted_tokens_id'), 'blacklisted_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_blacklisted_tokens_token'), 'blacklisted_tokens', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_blacklisted_tokens_token'), table_name='blacklisted_tokens')
    op.drop_index(op.f('ix_blacklisted_tokens_id'), table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens') 