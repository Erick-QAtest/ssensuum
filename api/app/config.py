from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ssensuum.db"
    web_origin: str = "http://localhost:3000"
    # URL pública del sitio: se usa para los regresos y el webhook de Mercado Pago.
    public_base_url: str = "http://localhost:3000"
    mp_access_token: str = ""
    # Las credenciales de prueba nuevas empiezan con APP_USR igual que las reales:
    # con esto se fuerza el checkout de pruebas (sandbox) de Mercado Pago.
    mp_sandbox: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
