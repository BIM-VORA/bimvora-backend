from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    port: int = 8000
    environment: str = "production"
    debug: bool = False

    # Database — async URL for app (asyncpg)
    # Format: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
    database_url: str

    # Supabase Storage
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "bimvora-files"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "orders@bimvora.com"

    # Frontend (CORS + redirect URLs)
    frontend_url: str = "https://bimvora.com"

    # Internal shared secret (must match frontend API_INTERNAL_SECRET)
    internal_secret: str = "changeme"

    # Server-side tracking
    meta_pixel_id: str = ""
    meta_access_token: str = ""
    tiktok_pixel_id: str = ""
    tiktok_access_token: str = ""
    linkedin_partner_id: str = ""
    linkedin_access_token: str = ""
    linkedin_conversion_id: str = ""
    ga4_measurement_id: str = ""
    ga4_api_secret: str = ""

    # Google Sheets (optional)
    sheets_webhook_url: str = ""
    sheets_secret: str = ""

    # Admin
    admin_api_key: str = "changeme"

    @property
    def sync_database_url(self) -> str:
        """
        Synchronous database URL for Alembic migrations.
        Replaces asyncpg driver with psycopg2 to avoid the MissingGreenlet error.
        """
        return self.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        ).replace(
            "postgresql://", "postgresql+psycopg2://"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
