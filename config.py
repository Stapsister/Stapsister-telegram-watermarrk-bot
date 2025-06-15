# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./watermark_bot.db")

# Fix PostgreSQL URL format for Render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
