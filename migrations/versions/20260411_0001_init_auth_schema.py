"""init auth schema

Revision ID: 20260411_0001
Revises:
Create Date: 2026-04-11 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260411_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=True),
        sa.Column("email_verify_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=64), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=64), nullable=True),
        sa.Column("plan", sa.String(length=32), nullable=True),
        sa.Column("plan_status", sa.String(length=32), nullable=True),
        sa.Column("plan_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("plan_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("wallet_address", sa.String(length=42), nullable=True),
        sa.Column("executor_contract", sa.String(length=42), nullable=True),
        sa.Column("vault_registered", sa.Boolean(), nullable=True),
        sa.Column("bot_deployed", sa.Boolean(), nullable=True),
        sa.Column("enabled_strategies", sa.String(length=500), nullable=True),
        sa.Column("total_gross_profit", sa.Float(), nullable=True),
        sa.Column("total_user_profit", sa.Float(), nullable=True),
        sa.Column("total_platform_cut", sa.Float(), nullable=True),
        sa.Column("last_profit_collect", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referral_code", sa.String(length=16), nullable=True),
        sa.Column("referred_by", sa.String(length=16), nullable=True),
        sa.Column("referral_earnings", sa.Float(), nullable=True),
        sa.Column("is_signal_public", sa.Boolean(), nullable=True),
        sa.Column("social_rank", sa.Integer(), nullable=True),
        sa.Column("copy_followers_count", sa.Integer(), nullable=True),
        sa.Column("email_on_trade", sa.Boolean(), nullable=True),
        sa.Column("email_on_milestone", sa.Boolean(), nullable=True),
        sa.Column("telegram_chat_id", sa.String(length=32), nullable=True),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=False)

    op.create_table(
        "profit_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("gross_usd", sa.Float(), nullable=False),
        sa.Column("user_usd", sa.Float(), nullable=False),
        sa.Column("platform_usd", sa.Float(), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=True),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("chain", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index("ix_profit_records_id", "profit_records", ["id"], unique=False)

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=True),
        sa.Column("plan", sa.String(length=32), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("stripe_event_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint("stripe_event_id"),
    )
    op.create_index("ix_subscription_events_id", "subscription_events", ["id"], unique=False)

    op.create_table(
        "referral_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("referred_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("bonus_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("referral_records")
    op.drop_index("ix_subscription_events_id", table_name="subscription_events")
    op.drop_table("subscription_events")
    op.drop_index("ix_profit_records_id", table_name="profit_records")
    op.drop_table("profit_records")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
