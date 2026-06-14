import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ph.lab.subscriptionportal"
    DEBUG: bool = True
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "1433")
    DB_NAME: str = os.getenv("DB_NAME", "phlab_subscriptionportal")
    DB_USER: str = os.getenv("DB_USER", "sa")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "CHANGE_ME")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:8401,http://localhost:3000")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")

    MERCADOPAGO_ACCESS_TOKEN: str | None = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    MERCADOPAGO_PUBLIC_KEY: str | None = os.getenv("MERCADOPAGO_PUBLIC_KEY")
    MERCADOPAGO_NOTIFICATION_URL: str | None = os.getenv("MERCADOPAGO_NOTIFICATION_URL")
    MERCADOPAGO_WEBHOOK_SECRET: str | None = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")

    S3_ENDPOINT: str | None = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY: str | None = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str | None = os.getenv("S3_SECRET_KEY")
    S3_BUCKET: str | None = os.getenv("S3_BUCKET")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    S3_USE_SSL: bool = os.getenv("S3_USE_SSL", "true").lower() in {"1", "true", "yes", "on"}

    SECURITY_PROVIDER: str = os.getenv("SECURITY_PROVIDER", "auth0")
    OIDC_ISSUER: str | None = os.getenv("OIDC_ISSUER")
    OIDC_CLIENT_ID: str | None = os.getenv("OIDC_CLIENT_ID")
    OIDC_AUDIENCE: str | None = os.getenv("OIDC_AUDIENCE")
    OIDC_JWKS_URL: str | None = os.getenv("OIDC_JWKS_URL")
    OIDC_USERINFO_URL: str | None = os.getenv("OIDC_USERINFO_URL")
    OIDC_ALGORITHMS: str = os.getenv("OIDC_ALGORITHMS", "RS256")

    AUTH0_DOMAIN: str | None = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID: str | None = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_AUDIENCE: str | None = os.getenv("AUTH0_AUDIENCE")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_deployed_environment(self) -> bool:
        return self.APP_ENV.lower() in {"stage", "staging", "prod", "production"}

    @property
    def require_mercadopago_webhook_secret(self) -> bool:
        return self.is_deployed_environment and bool(self.MERCADOPAGO_NOTIFICATION_URL)

    @property
    def oidc_issuer(self) -> str | None:
        if self.OIDC_ISSUER:
            return self.OIDC_ISSUER.rstrip("/") + "/"
        if self.AUTH0_DOMAIN:
            return f"https://{self.AUTH0_DOMAIN}/"
        return None

    @property
    def oidc_client_id(self) -> str | None:
        return self.OIDC_CLIENT_ID or self.AUTH0_CLIENT_ID

    @property
    def oidc_audience(self) -> str | None:
        return self.OIDC_AUDIENCE or self.AUTH0_AUDIENCE or self.oidc_client_id

    @property
    def oidc_jwks_url(self) -> str | None:
        if self.OIDC_JWKS_URL:
            return self.OIDC_JWKS_URL
        if self.oidc_issuer:
            return f"{self.oidc_issuer}.well-known/jwks.json"
        return None

    @property
    def oidc_userinfo_url(self) -> str | None:
        if self.OIDC_USERINFO_URL:
            return self.OIDC_USERINFO_URL
        if self.oidc_issuer:
            return f"{self.oidc_issuer}userinfo"
        return None

    @property
    def oidc_algorithms(self) -> list[str]:
        return [alg.strip() for alg in self.OIDC_ALGORITHMS.split(",") if alg.strip()]

    @property
    def database_url(self) -> str:
        driver = "ODBC+Driver+18+for+SQL+Server"
        return (
            f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?driver={driver}&TrustServerCertificate=yes"
        )


settings = Settings()
