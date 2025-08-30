from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

# Variáveis globais para o motor do banco de dados e a sessão local
engine = None
SessionLocal = None

def initialize_database():
    """Inicializa o motor do banco de dados e a sessão local com base nas configurações."""
    global engine, SessionLocal
    if engine is None:
        settings = get_settings()
        SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
        connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependência para obter uma sessão de banco de dados."""
    # Garante que o banco de dados seja inicializado na primeira requisição
    if SessionLocal is None:
        initialize_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
