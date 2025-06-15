# Database configuration with fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite as fallback if PostgreSQL not available
    DATABASE_URL = "sqlite:///./watermark_bot.db"
    print("Warning: Using SQLite fallback database")

# Fix for Render.com PostgreSQL URL format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"Fixed PostgreSQL URL format")
