"""Configuration centralisée, lue depuis les variables d'environnement / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EMIT - CV intelligent"
    environment: str = "development"  # development | production

    # Base de données (PostgreSQL en production, SQLite acceptée pour le dev/test)
    database_url: str = "sqlite:///./dev.db"

    # JWT
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    # Cookie du refresh token (SameSite=none + Secure si front et API sont sur des domaines différents)
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # CORS : liste JSON, ex. ["https://mon-front.vercel.app"]
    cors_origins: list[str] = ["http://localhost:5173"]

    # Fichiers
    upload_dir: str = "./uploads"
    max_cv_mb: int = 5
    max_photo_mb: int = 2

    # Anti brute-force sur la connexion
    login_rate_limit: int = 10  # tentatives / minute / (IP, e-mail)
    login_rate_window_s: int = 60

    # Base de données : pool de connexions (production)
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_recycle_s: int = 1800

    # E-mail (vérification d'adresse) : console (dev/test, écrit dans les logs) | smtp
    email_backend: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = True
    email_from: str = "EMIT CV <no-reply@emit.example>"
    public_url: str = "http://localhost:5173"  # base des liens envoyés par e-mail
    verif_token_minutes: int = 60
    verif_max_tentatives: int = 5

    # Protection contre les abus (compteurs en base : valables avec plusieurs workers)
    inscription_limit: int = 5            # tentatives / heure / IP
    inscription_limit_matricule: int = 5  # tentatives / heure / matricule
    verif_limit: int = 10                 # confirmations / 10 min / IP
    login_echecs_compte: int = 8          # échecs / 15 min / compte avant blocage temporaire

    # File de tâches : inline (traitement après la réponse, par le serveur web) | worker (processus `python -m app.worker`)
    taches_mode: str = "inline"
    worker_batch: int = 20
    worker_poll_s: float = 2.0
    worker_verrou_s: int = 900
    tache_max_tentatives: int = 3
    scoring_chunk: int = 500
    log_json: bool = False  # journaux JSON (une ligne par évènement) pour l'agrégation en production
    ocr_enabled: bool = False  # la détection des PDF scannés est toujours active ; l'OCR n'est pas fourni

    # IA : auto | tfidf | transformers
    ai_backend: str = "auto"
    ai_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ai_notify_threshold: float = 60.0  # score mini pour notifier un étudiant d'une nouvelle offre


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
