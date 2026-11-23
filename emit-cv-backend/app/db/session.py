from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_kwargs: dict = {}
if settings.database_url.startswith("sqlite"):
    _kwargs["connect_args"] = {"check_same_thread": False}
else:  # PostgreSQL : pool borné pour ne pas saturer le serveur de base de données
    _kwargs.update(pool_pre_ping=True, pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow,
                   pool_recycle=settings.db_pool_recycle_s)

engine = create_engine(settings.database_url, **_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """Dépendance FastAPI : une session par requête, toujours fermée."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
