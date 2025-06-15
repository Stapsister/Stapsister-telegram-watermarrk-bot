import os

# Bot configuration
BOT_TOKEN = os.getenv("7862951291:AAFLCXBgekpq_do1yl63TIFvgtCADjCr66k")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/watermark_bot")

# File paths
TEMP_DIR = "temp"
FONTS_DIR = "fonts"

# Subscription plans (simplified without payment integration)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "monthly_limit": 50,  # Increased limit for better experience
        "price": 0,
        "features": ["Basic watermarking", "Standard fonts", "5 colors"]
    },
    "premium": {
        "name": "Premium",
        "monthly_limit": -1,  # Unlimited for now
        "price": 0,  # Free for now, UPI integration later
        "features": ["Unlimited watermarking", "All fonts", "Custom colors", "Advanced positioning"]
    }
}

# Default watermark settings
DEFAULT_WATERMARK_SETTINGS = {
    "text": "Watermark",
    "font_size": 128,  # Massive size for maximum visibility
    "opacity": 220,  # Very high opacity for strong visibility
    "position": "center",  # Center position for maximum impact
    "color": "white",
    "font_family": "arial"
}

# Supported file formats
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
