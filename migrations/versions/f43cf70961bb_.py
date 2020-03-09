"""empty message

Revision ID: f43cf70961bb
Revises: 2e034d73923e
Create Date: 2020-03-02 17:05:12.869523

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f43cf70961bb'
down_revision = '2e034d73923e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drone', 'last_update')
    op.drop_column('project', 'last_update')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('last_update', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('drone', sa.Column('last_update', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
