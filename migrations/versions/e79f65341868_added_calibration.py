"""added calibration

Revision ID: e79f65341868
Revises: 76afd823e8bb
Create Date: 2020-02-25 20:34:52.973699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e79f65341868'
down_revision = '76afd823e8bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drone', sa.Column('calibration', sa.PickleType(), nullable=True))
    op.drop_column('drone', 'cal_file')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drone', sa.Column('cal_file', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('drone', 'calibration')
    # ### end Alembic commands ###
