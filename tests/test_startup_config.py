import pytest

from backend.startup_config import validate_startup_config


@pytest.mark.parametrize(
    "env,jwt,stripe,webhook,expected_missing",
    [
        ("prod", "", "", "", ["JWT_SECRET", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]),
        ("production", "jwt", "", "", ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]),
        ("staging", "", "sk", "whsec", ["JWT_SECRET"]),
    ],
)
def test_prod_like_requires_all_secrets(env, jwt, stripe, webhook, expected_missing):
    with pytest.raises(RuntimeError) as exc:
        validate_startup_config(
            env=env,
            jwt_secret=jwt,
            stripe_secret_key=stripe,
            stripe_webhook_secret=webhook,
            allow_insecure_dev_billing=False,
        )

    message = str(exc.value)
    for var in expected_missing:
        assert var in message


def test_dev_requires_explicit_flag_for_mock_billing():
    with pytest.raises(RuntimeError) as exc:
        validate_startup_config(
            env="dev",
            jwt_secret="",
            stripe_secret_key="",
            stripe_webhook_secret="",
            allow_insecure_dev_billing=False,
        )

    message = str(exc.value)
    assert "STRIPE_SECRET_KEY" in message
    assert "STRIPE_WEBHOOK_SECRET" in message
    assert "ALLOW_INSECURE_DEV_BILLING=1" in message


@pytest.mark.parametrize(
    "env,jwt,stripe,webhook,allow_insecure",
    [
        ("dev", "", "", "", True),
        ("dev", "", "sk_test", "whsec_test", False),
        ("dev", "jwt", "sk_test", "whsec_test", False),
    ],
)
def test_dev_permutations_allowed(env, jwt, stripe, webhook, allow_insecure):
    validate_startup_config(
        env=env,
        jwt_secret=jwt,
        stripe_secret_key=stripe,
        stripe_webhook_secret=webhook,
        allow_insecure_dev_billing=allow_insecure,
    )
