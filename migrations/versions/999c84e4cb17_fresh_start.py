"""Fresh start

Revision ID: 999c84e4cb17
Revises: 1d49ddb8de24
Create Date: 2025-05-24 15:34:14.645130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '999c84e4cb17'
down_revision = '1d49ddb8de24'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('landmark', schema=None) as batch_op:
        batch_op.drop_column('image')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('landmark', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.VARCHAR(length=150), nullable=False))

    # ### end Alembic commands ###
