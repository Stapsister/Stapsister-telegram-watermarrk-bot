# Database setup with error handling
try:
    DATABASE_URL = config.DATABASE_URL
    print(f"Using database: {DATABASE_URL[:20]}...")
    
    # Ensure PostgreSQL URL is properly formatted for SQLAlchemy
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print("Fixed PostgreSQL URL format")
except Exception as e:
    print(f"Database configuration error: {e}")
    DATABASE_URL = "sqlite:///./watermark_bot.db"

try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL,
            poolclass=StaticPool,
            echo=False
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_recycle=300,
            pool_pre_ping=True,
            echo=False
        )
    print("Database engine created successfully")
except Exception as e:
    print(f"Database engine creation error: {e}")
    # Fallback to SQLite
    engine = create_engine("sqlite:///./watermark_bot.db", poolclass=StaticPool, echo=False)
