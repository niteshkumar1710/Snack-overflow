from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Build engine with connection arguments. A 5-second timeout ensures that
# cold starts or pooler handshakes succeed reliably while still preventing indefinite hangs.
connect_args = {}
if "postgresql" in settings.DATABASE_URL:
    connect_args["connect_timeout"] = 5

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session for requests.
    
    Guarantees that the session is closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str]:
    """Test database connectivity with a lightweight ping query.
    
    Returns:
        (is_connected, message)
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except Exception as exc:
        return False, f"Database connection failed: {str(exc)}"
