"""add judge_comparisons table

Revision ID: f4a1c9e7b6d3
Revises: a3f9c1d8e2b7
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a1c9e7b6d3'
down_revision: Union[str, Sequence[str], None] = 'a3f9c1d8e2b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('judge_comparisons',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('output_id', sa.Integer(), nullable=False),
    sa.Column('model_name', sa.String(), nullable=False),
    sa.Column('repeat_index', sa.Integer(), nullable=False),
    sa.Column('judge_gpt5mini_score_percent', sa.Float(), nullable=True),
    sa.Column('judge_gpt5mini_confidence', sa.Float(), nullable=True),
    sa.Column('judge_gpt5mini_token_input', sa.Integer(), nullable=True),
    sa.Column('judge_gpt5mini_token_output', sa.Integer(), nullable=True),
    sa.Column('judge_gpt5mini_notes', sa.Text(), nullable=True),
    sa.Column('judge_gpt5mini_evaluated_at', sa.DateTime(), nullable=True),
    sa.Column('judge_gpt56luna_score_percent', sa.Float(), nullable=True),
    sa.Column('judge_gpt56luna_confidence', sa.Float(), nullable=True),
    sa.Column('judge_gpt56luna_token_input', sa.Integer(), nullable=True),
    sa.Column('judge_gpt56luna_token_output', sa.Integer(), nullable=True),
    sa.Column('judge_gpt56luna_notes', sa.Text(), nullable=True),
    sa.Column('judge_gpt56luna_evaluated_at', sa.DateTime(), nullable=True),
    sa.Column('judge_claudesonnet5_score_percent', sa.Float(), nullable=True),
    sa.Column('judge_claudesonnet5_confidence', sa.Float(), nullable=True),
    sa.Column('judge_claudesonnet5_token_input', sa.Integer(), nullable=True),
    sa.Column('judge_claudesonnet5_token_output', sa.Integer(), nullable=True),
    sa.Column('judge_claudesonnet5_notes', sa.Text(), nullable=True),
    sa.Column('judge_claudesonnet5_evaluated_at', sa.DateTime(), nullable=True),
    sa.Column('judge_deepseekv4flash_score_percent', sa.Float(), nullable=True),
    sa.Column('judge_deepseekv4flash_confidence', sa.Float(), nullable=True),
    sa.Column('judge_deepseekv4flash_token_input', sa.Integer(), nullable=True),
    sa.Column('judge_deepseekv4flash_token_output', sa.Integer(), nullable=True),
    sa.Column('judge_deepseekv4flash_notes', sa.Text(), nullable=True),
    sa.Column('judge_deepseekv4flash_evaluated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['benchmark_tasks.id'], ),
    sa.ForeignKeyConstraint(['output_id'], ['benchmark_outputs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('output_id', 'repeat_index', name='uq_judge_comparisons_output_repeat')
    )
    op.create_index(op.f('ix_judge_comparisons_task_id'), 'judge_comparisons', ['task_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_judge_comparisons_task_id'), table_name='judge_comparisons')
    op.drop_table('judge_comparisons')
