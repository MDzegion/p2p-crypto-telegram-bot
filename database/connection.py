from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings

# Determine DB URL
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    # SQLite requires check_same_thread=False for multi-thread access.
    # WAL + busy_timeout: banyak handler nulis bersamaan tidak boleh
    # memicu "database is locked" (bottleneck utama saat traffic tinggi).
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()
else:
    engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
