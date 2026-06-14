from app.core.config import Settings


def test_cors_origins_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://lbschool.phlab.dev,http://localhost:8401")

    settings = Settings()

    assert settings.cors_origins == ["https://lbschool.phlab.dev", "http://localhost:8401"]


def test_mercadopago_webhook_secret_required_in_stage(monkeypatch):
    monkeypatch.setenv("APP_ENV", "stage")
    monkeypatch.setenv("MERCADOPAGO_NOTIFICATION_URL", "https://lbschool.phlab.dev/api/v1/payments/webhook/mp")
    monkeypatch.delenv("MERCADOPAGO_WEBHOOK_SECRET", raising=False)

    settings = Settings()

    assert settings.require_mercadopago_webhook_secret is True


def test_mercadopago_webhook_secret_not_required_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("MERCADOPAGO_NOTIFICATION_URL", "https://lbschool.phlab.dev/api/v1/payments/webhook/mp")
    monkeypatch.delenv("MERCADOPAGO_WEBHOOK_SECRET", raising=False)

    settings = Settings()

    assert settings.require_mercadopago_webhook_secret is False
