DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./watermark_bot.db")

# Fix for Render.com PostgreSQL URL format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
