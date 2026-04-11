from __future__ import annotations


def validate_startup_config(
    env: str,
    jwt_secret: str,
    stripe_secret_key: str,
    stripe_webhook_secret: str,
    allow_insecure_dev_billing: bool,
) -> None:
    normalized_env = (env or "dev").lower()
    is_prod_like = normalized_env in {"prod", "production", "staging"}
    missing_required: list[str] = []

    if is_prod_like and not jwt_secret:
        missing_required.append("JWT_SECRET")
    if is_prod_like and not stripe_secret_key:
        missing_required.append("STRIPE_SECRET_KEY")
    if is_prod_like and not stripe_webhook_secret:
        missing_required.append("STRIPE_WEBHOOK_SECRET")

    if missing_required:
        raise RuntimeError(
            "Missing required environment variables for "
            f"{normalized_env}: {', '.join(missing_required)}"
        )

    if normalized_env == "dev" and not allow_insecure_dev_billing:
        dev_missing_billing: list[str] = []
        if not stripe_secret_key:
            dev_missing_billing.append("STRIPE_SECRET_KEY")
        if not stripe_webhook_secret:
            dev_missing_billing.append("STRIPE_WEBHOOK_SECRET")
        if dev_missing_billing:
            raise RuntimeError(
                "Missing required development billing environment variables: "
                f"{', '.join(dev_missing_billing)}. "
                "Set real Stripe values or explicitly set "
                "ALLOW_INSECURE_DEV_BILLING=1 to use local mock billing."
            )
