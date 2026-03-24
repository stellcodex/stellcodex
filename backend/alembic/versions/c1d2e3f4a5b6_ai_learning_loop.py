"""ai learning loop tables

Revision ID: c1d2e3f4a5b6
Revises: b7e1c2d3f4a5
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b7e1c2d3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_case_logs",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("file_id", sa.String(40), nullable=False),
        sa.Column("project_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("run_type", sa.String(48), nullable=False, server_default="session_sync"),
        sa.Column("normalized_problem_signature", sa.Text(), nullable=False),
        sa.Column("similarity_index_key", sa.String(255), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("decision_output", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("execution_trace", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("final_status", sa.String(16), nullable=False, server_default="blocked"),
        sa.Column("error_trace", postgresql.JSONB(), nullable=True),
        sa.Column("failure_class", sa.String(32), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("drive_snapshot_path", sa.Text(), nullable=True),
        sa.Column("drive_snapshot_status", sa.String(16), nullable=False, server_default="disabled"),
        sa.Column("drive_snapshot_error", sa.Text(), nullable=True),
        sa.Column("retrieved_context_summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_case_logs_tenant_id", "ai_case_logs", ["tenant_id"])
    op.create_index("ix_ai_case_logs_file_id", "ai_case_logs", ["file_id"])
    op.create_index("ix_ai_case_logs_project_id", "ai_case_logs", ["project_id"])
    op.create_index("ix_ai_case_logs_session_id", "ai_case_logs", ["session_id"])
    op.create_index("ix_ai_case_logs_run_type", "ai_case_logs", ["run_type"])
    op.create_index("ix_ai_case_logs_normalized_problem_signature", "ai_case_logs", ["normalized_problem_signature"])
    op.create_index("ix_ai_case_logs_similarity_index_key", "ai_case_logs", ["similarity_index_key"])
    op.create_index("ix_ai_case_logs_final_status", "ai_case_logs", ["final_status"])
    op.create_index("ix_ai_case_logs_failure_class", "ai_case_logs", ["failure_class"])
    op.create_index("ix_ai_case_logs_created_at", "ai_case_logs", ["created_at"])

    op.create_table(
        "ai_snapshot_jobs",
        sa.Column("snapshot_job_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("local_snapshot_path", sa.Text(), nullable=False),
        sa.Column("drive_target_path", sa.Text(), nullable=True),
        sa.Column("upload_status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(128), nullable=True),
        sa.Column("last_rq_job_id", sa.String(64), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_snapshot_jobs_case_id", "ai_snapshot_jobs", ["case_id"])
    op.create_index("ix_ai_snapshot_jobs_tenant_id", "ai_snapshot_jobs", ["tenant_id"])
    op.create_index("ix_ai_snapshot_jobs_upload_status", "ai_snapshot_jobs", ["upload_status"])
    op.create_index("ix_ai_snapshot_jobs_next_retry_at", "ai_snapshot_jobs", ["next_retry_at"])
    op.create_index("ix_ai_snapshot_jobs_last_rq_job_id", "ai_snapshot_jobs", ["last_rq_job_id"])
    op.create_index("ix_ai_snapshot_jobs_uploaded_at", "ai_snapshot_jobs", ["uploaded_at"])

    op.create_table(
        "ai_eval_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("normalized_problem_signature", sa.Text(), nullable=False),
        sa.Column("similarity_index_key", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("decision_taken", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evaluation", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("failure_class", sa.String(32), nullable=True),
        sa.Column("resolution_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_resolution_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_eval_results_case_id", "ai_eval_results", ["case_id"])
    op.create_index("ix_ai_eval_results_tenant_id", "ai_eval_results", ["tenant_id"])
    op.create_index("ix_ai_eval_results_normalized_problem_signature", "ai_eval_results", ["normalized_problem_signature"])
    op.create_index("ix_ai_eval_results_similarity_index_key", "ai_eval_results", ["similarity_index_key"])
    op.create_index("ix_ai_eval_results_outcome", "ai_eval_results", ["outcome"])
    op.create_index("ix_ai_eval_results_failure_class", "ai_eval_results", ["failure_class"])
    op.create_index("ix_ai_eval_results_created_at", "ai_eval_results", ["created_at"])

    for table_name in ("solved_cases", "failed_cases", "blocked_cases", "recovered_cases"):
        op.create_table(
            table_name,
            sa.Column(
                "case_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("tenant_id", sa.BigInteger(), nullable=False),
            sa.Column("file_id", sa.String(40), nullable=False),
            sa.Column("project_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("normalized_problem_signature", sa.Text(), nullable=False),
            sa.Column("similarity_index_key", sa.String(255), nullable=False),
            sa.Column("decision_taken", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("outcome", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"])
        op.create_index(f"ix_{table_name}_file_id", table_name, ["file_id"])
        op.create_index(f"ix_{table_name}_project_id", table_name, ["project_id"])
        op.create_index(f"ix_{table_name}_normalized_problem_signature", table_name, ["normalized_problem_signature"])
        op.create_index(f"ix_{table_name}_similarity_index_key", table_name, ["similarity_index_key"])
        op.create_index(f"ix_{table_name}_created_at", table_name, ["created_at"])

    op.create_table(
        "ai_pattern_signals",
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("normalized_problem_signature", sa.Text(), nullable=False),
        sa.Column("similarity_index_key", sa.String(255), nullable=False),
        sa.Column("failure_class", sa.String(32), nullable=True),
        sa.Column("signal_payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_pattern_signals_tenant_id", "ai_pattern_signals", ["tenant_id"])
    op.create_index("ix_ai_pattern_signals_signal_type", "ai_pattern_signals", ["signal_type"])
    op.create_index("ix_ai_pattern_signals_normalized_problem_signature", "ai_pattern_signals", ["normalized_problem_signature"])
    op.create_index("ix_ai_pattern_signals_similarity_index_key", "ai_pattern_signals", ["similarity_index_key"])
    op.create_index("ix_ai_pattern_signals_failure_class", "ai_pattern_signals", ["failure_class"])
    op.create_index("ix_ai_pattern_signals_created_at", "ai_pattern_signals", ["created_at"])

    op.create_table(
        "experience_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("task_query", sa.Text(), nullable=False),
        sa.Column("successful_plan", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("feedback_from_owner", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "decision_logs",
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("lane", sa.String(64), nullable=False),
        sa.Column("executor", sa.String(128), nullable=False),
        sa.Column("decision_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("decision_logs")
    op.drop_table("experience_ledger")
    op.drop_table("ai_pattern_signals")
    for table_name in ("recovered_cases", "blocked_cases", "failed_cases", "solved_cases"):
        op.drop_table(table_name)
    op.drop_table("ai_eval_results")
    op.drop_table("ai_snapshot_jobs")
    op.drop_table("ai_case_logs")
