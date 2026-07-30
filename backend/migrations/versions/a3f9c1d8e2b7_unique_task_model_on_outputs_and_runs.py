"""unique (task_id, model_name) on benchmark_outputs and benchmark_runs

Revision ID: a3f9c1d8e2b7
Revises: 8d0fd5f5c95b
Create Date: 2026-07-28 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3f9c1d8e2b7'
down_revision: Union[str, Sequence[str], None] = '8d0fd5f5c95b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite requires batch mode to add a constraint to an existing table.
    with op.batch_alter_table('benchmark_outputs') as batch_op:
        batch_op.create_unique_constraint(
            'uq_benchmark_outputs_task_model', ['task_id', 'model_name']
        )
    with op.batch_alter_table('benchmark_runs') as batch_op:
        batch_op.create_unique_constraint(
            'uq_benchmark_runs_task_model', ['task_id', 'model_name']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('benchmark_runs') as batch_op:
        batch_op.drop_constraint('uq_benchmark_runs_task_model', type_='unique')
    with op.batch_alter_table('benchmark_outputs') as batch_op:
        batch_op.drop_constraint('uq_benchmark_outputs_task_model', type_='unique')
