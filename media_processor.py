import os
import cv2
import asyncio
from PIL import Image, ImageDraw, ImageFont
from database import get_db_session
from models import User, WatermarkSettings
import config

class MediaProcessor:
    def __init__(self):
        self.ensure_temp_dir()
    
    def ensure_temp_dir(self):
        """Ensure temp directory exists."""
        os.makedirs(config.TEMP_DIR, exist_ok=True)
    
    async def process_image(self, file_path: str, user_id: str) -> str:
        """Process image and add watermark."""
        # Get user watermark settings
        settings = self.get_user_settings(user_id)
        
        print(f"Processing image for user {user_id}")
        print(f"Settings - Text: {settings['text']}, Font: {settings['font_size']}, Color: {settings['color']}, Opacity: {settings['opacity']}, Position: {settings['position']}")
        
        # Open image
        image = Image.open(file_path)
        
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create transparent overlay
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Load font
        font = self.load_font(settings['font_family'], settings['font_size'])
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), settings['text'], font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        print(f"Text dimensions: {text_width}x{text_height}")
        
        # Calculate position
        x, y = self.calculate_position(
            image.size[0], image.size[1], 
            int(text_width), int(text_height), 
            settings['position']
        )
        
        print(f"Text position: ({x}, {y})")
        
        # Parse color
        color = self.parse_color(settings['color'], settings['opacity'])
        print(f"Text color: {color}")
        
        # Draw simple text without effects
        draw.text((x, y), settings['text'], font=font, fill=color)
        
        # Composite the overlay onto the original image
        watermarked = Image.alpha_composite(image, overlay)
        
        # Convert back to RGB if needed
        if watermarked.mode == 'RGBA':
            watermarked = watermarked.convert('RGB')
        
        # Save processed image
        output_path = f"{config.TEMP_DIR}/watermarked_{os.path.basename(file_path)}"
        watermarked.save(output_path, quality=95)
        
        return output_path
    
    async def process_video(self, file_path: str, user_id: str) -> str:
        """Process video and add watermark."""
        # Get user watermark settings
        settings = self.get_user_settings(user_id)
        
        print(f"Processing video for user {user_id}")
        print(f"Settings - Text: {settings['text']}, Font: {settings['font_size']}, Color: {settings['color']}, Opacity: {settings['opacity']}, Position: {settings['position']}")
        
        # Open video
        cap = cv2.VideoCapture(file_path)
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create output video writer
        output_path = f"{config.TEMP_DIR}/watermarked_{os.path.basename(file_path)}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Load font (OpenCV uses different font system)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = settings['font_size'] / 50  # Adjust scale
        
        # Parse color for OpenCV (BGR format)
        color = self.parse_color_opencv(settings['color'])
        
        # Calculate position
        text_size = cv2.getTextSize(settings['text'], font, font_scale, 2)[0]
        x, y = self.calculate_position(width, height, text_size[0], text_size[1], settings['position'])
        
        # Process each frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Create overlay for transparency
            overlay = frame.copy()
            
            # Add text to overlay
            cv2.putText(overlay, settings['text'], (x, y), font, font_scale, color, 2, cv2.LINE_AA)
            
            # Blend overlay with original frame for transparency effect
            alpha = settings['opacity'] / 255.0
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            # Write frame
            out.write(frame)
        
        # Release everything
        cap.release()
        out.release()
        
        return output_path
    
    def get_user_settings(self, user_id: str) -> dict:
        """Get user watermark settings from database."""
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                # Return default settings if user not found
                return config.DEFAULT_WATERMARK_SETTINGS
            
            settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
            if not settings:
                # Create default settings if not exist
                settings = WatermarkSettings(user_id=user.id, **config.DEFAULT_WATERMARK_SETTINGS)
                db.add(settings)
                db.commit()
                return config.DEFAULT_WATERMARK_SETTINGS
            
            # Extract actual values from SQLAlchemy model
            return {
                'text': settings.text,
                'font_size': settings.font_size,
                'opacity': settings.opacity,
                'position': settings.position,
                'color': settings.color,
                'font_family': settings.font_family
            }
        finally:
            db.close()
    
    def load_font(self, font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
        """Load font for PIL."""
        try:
            # Try multiple font paths for better compatibility
            font_paths = [
                f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                f"/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                f"/System/Library/Fonts/Arial.ttf",  # macOS
                f"/Windows/Fonts/arial.ttf",  # Windows
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    print(f"Loading font: {font_path} with size {font_size}")
                    return ImageFont.truetype(font_path, font_size)
            
            # Create default with proper size support
            print(f"Using default font with size {font_size}")
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                return ImageFont.load_default()
        except Exception as e:
            print(f"Font loading error: {e}")
            return ImageFont.load_default()
    
    def calculate_position(self, image_width: int, image_height: int, 
                          text_width: int, text_height: int, position: str) -> tuple:
        """Calculate text position based on position setting."""
        margin = 20  # Margin from edges
        
        if position == "top_left":
            return (margin, margin)
        elif position == "top_right":
            return (image_width - text_width - margin, margin)
        elif position == "bottom_left":
            return (margin, image_height - text_height - margin)
        elif position == "bottom_right":
            return (image_width - text_width - margin, image_height - text_height - margin)
        elif position == "center":
            return ((image_width - text_width) // 2, (image_height - text_height) // 2)
        else:
            # Default to bottom right
            return (image_width - text_width - margin, image_height - text_height - margin)
    
    def parse_color(self, color_name: str, opacity: int) -> tuple:
        """Parse color name to RGBA tuple for PIL."""
        color_map = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
        }
        
        rgb = color_map.get(color_name.lower(), (255, 255, 255))  # Default to white
        return rgb + (opacity,)  # Add alpha channel
    
    def parse_color_opencv(self, color_name: str) -> tuple:
        """Parse color name to BGR tuple for OpenCV."""
        color_map = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (0, 0, 255),  # BGR format
            "green": (0, 255, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "cyan": (255, 255, 0),
            "magenta": (255, 0, 255),
        }
        
        return color_map.get(color_name.lower(), (255, 255, 255))  # Default to white
