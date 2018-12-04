"""empty message

Revision ID: e0bf58591d51
Revises: 
Create Date: 2018-12-04 15:26:08.063082

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0bf58591d51'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('salt', sa.String(length=32), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('recovery_code_hash', sa.String(length=128), nullable=True),
    sa.Column('two_factor_login', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('user_update_signal',
    sa.Column('user_update_signal_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('user_update_signal_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_update_signal')
    op.drop_table('user')
    # ### end Alembic commands ###