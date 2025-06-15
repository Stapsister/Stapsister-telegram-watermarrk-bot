import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    ContextTypes, filters
)
from telegram.constants import ParseMode
from media_processor import MediaProcessor
from database import get_db_session
from models import User, WatermarkSettings
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleBotHandler:
    def __init__(self):
        self.media_processor = MediaProcessor()
    
    def setup_handlers(self, application):
        """Setup all bot handlers."""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("settings", self.settings_command))
        application.add_handler(CommandHandler("menu", self.menu_command))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        user_id = str(user.id)
        
        # Create or get user from database
        db = get_db_session()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_id).first()
            if not db_user:
                # Create new user
                db_user = User(
                    telegram_id=user_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.add(db_user)
                db.commit()
                
                # Create default watermark settings
                watermark_settings = WatermarkSettings(
                    user_id=db_user.id,
                    **config.DEFAULT_WATERMARK_SETTINGS
                )
                db.add(watermark_settings)
                db.commit()
                
                welcome_text = f"""
🎉 Welcome to Watermark Bot, {user.first_name}!

I can add custom watermarks to your photos and videos.

📸 Send me a photo or video to get started!
⚙️ Use /settings to customize your watermark
❓ Use /help for more information
"""
            else:
                welcome_text = f"""
👋 Welcome back, {user.first_name}!

I'm ready to add watermarks to your photos and videos.

📸 Send me a photo or video to get started!
⚙️ Use /settings to customize your watermark
❓ Use /help for more information
"""
        finally:
            db.close()
        
        await update.message.reply_text(welcome_text)
        await self.show_main_menu(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🤖 **Watermark Bot Help**

**Commands:**
/start - Start the bot
/help - Show this help message
/settings - Customize watermark settings

**How to use:**
1. Send me a photo or video
2. I'll add your custom watermark
3. Download the processed file

**Watermark customization:**
- Text content
- Font size
- Opacity (transparency)
- Position on image/video
- Color

**Supported formats:**
📷 Images: JPG, PNG, BMP, TIFF
🎬 Videos: MP4, AVI, MOV, MKV

**File size limit:** 50MB
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command."""
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu with navigation options."""
        user_id = str(update.effective_user.id)
        
        # Get current user settings
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
            if not settings:
                return
        finally:
            db.close()
        
        keyboard = [
            [
                InlineKeyboardButton("📷 Add Watermark", callback_data="menu_upload"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ],
            [
                InlineKeyboardButton("📊 Current Settings", callback_data="menu_current"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ],
            [
                InlineKeyboardButton("📝 Quick Text Change", callback_data="menu_quick_text")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = f"""
🎯 **Watermark Bot Main Menu**

**Current Settings Preview:**
📝 Text: `{settings.text}`
📏 Size: `{settings.font_size}px`
👻 Opacity: `{int((settings.opacity/255)*100)}%`
📍 Position: `{settings.position.replace('_', ' ').title()}`
🎨 Color: `{settings.color.title()}`

Choose an option below or send a photo/video to start:
"""
        
        await update.message.reply_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        user_id = str(update.effective_user.id)
        
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("Please start the bot first with /start")
                return
            
            settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
            if not settings:
                settings = WatermarkSettings(user_id=user.id, **config.DEFAULT_WATERMARK_SETTINGS)
                db.add(settings)
                db.commit()
        finally:
            db.close()
        
        keyboard = [
            [InlineKeyboardButton("📝 Change Text", callback_data="setting_text")],
            [InlineKeyboardButton("📏 Font Size", callback_data="setting_font_size")],
            [InlineKeyboardButton("👻 Opacity", callback_data="setting_opacity")],
            [InlineKeyboardButton("📍 Position", callback_data="setting_position")],
            [InlineKeyboardButton("🎨 Color", callback_data="setting_color")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = f"""
⚙️ **Current Watermark Settings**

📝 Text: `{settings.text}`
📏 Font Size: `{settings.font_size}`
👻 Opacity: `{settings.opacity}/255`
📍 Position: `{settings.position}`
🎨 Color: `{settings.color}`

Choose what you want to change:
"""
        
        await update.message.reply_text(
            settings_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages."""
        # Clear any previous pending media to avoid confusion
        if 'pending_video' in context.user_data:
            del context.user_data['pending_video']
            
        # Store photo info for later processing
        photo = update.message.photo[-1]
        context.user_data['pending_photo'] = photo.file_id
        
        # Get current user settings
        user_id = str(update.effective_user.id)
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
                if not settings:
                    settings = WatermarkSettings(user_id=user.id, **config.DEFAULT_WATERMARK_SETTINGS)
                    db.add(settings)
                    db.commit()
            else:
                # Create user if doesn't exist
                await self.start_command(update, context)
                return
        finally:
            db.close()
        
        # Show customization options
        keyboard = [
            [
                InlineKeyboardButton("✅ Apply Watermark", callback_data="apply_watermark"),
                InlineKeyboardButton("📝 Change Text", callback_data="quick_text")
            ],
            [
                InlineKeyboardButton("📏 Font Size", callback_data="quick_font_size"),
                InlineKeyboardButton("📍 Position", callback_data="quick_position")
            ],
            [
                InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                InlineKeyboardButton("👻 Opacity", callback_data="quick_opacity")
            ],
            [
                InlineKeyboardButton("⚙️ Advanced Settings", callback_data="settings_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        preview_text = f"""
📸 **Image received!**

**Current watermark settings:**
📝 Text: `{settings.text}`
📏 Font Size: `{settings.font_size}`
📍 Position: `{settings.position.replace('_', ' ').title()}`
🎨 Color: `{settings.color.title()}`
👻 Opacity: `{settings.opacity}/255`

Choose an option below:
"""
        
        await update.message.reply_text(
            preview_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages."""
        video = update.message.video
        if video and video.file_size and video.file_size > config.MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ File too large. Maximum size is {config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
            return
        
        # Clear any previous pending media to avoid confusion
        if 'pending_photo' in context.user_data:
            del context.user_data['pending_photo']
        
        # Store video info for later processing
        context.user_data['pending_video'] = video.file_id
        
        # Get current user settings
        user_id = str(update.effective_user.id)
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
                if not settings:
                    settings = WatermarkSettings(user_id=user.id, **config.DEFAULT_WATERMARK_SETTINGS)
                    db.add(settings)
                    db.commit()
            else:
                # Create user if doesn't exist
                await self.start_command(update, context)
                return
        finally:
            db.close()
        
        # Show customization options (same as photo)
        keyboard = [
            [
                InlineKeyboardButton("✅ Apply Watermark", callback_data="apply_watermark"),
                InlineKeyboardButton("📝 Change Text", callback_data="quick_text")
            ],
            [
                InlineKeyboardButton("📏 Font Size", callback_data="quick_font_size"),
                InlineKeyboardButton("📍 Position", callback_data="quick_position")
            ],
            [
                InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                InlineKeyboardButton("👻 Opacity", callback_data="quick_opacity")
            ],
            [
                InlineKeyboardButton("⚙️ Advanced Settings", callback_data="settings_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        preview_text = f"""
🎬 **Video received!**

**Current watermark settings:**
📝 Text: `{settings.text}`
📏 Font Size: `{settings.font_size}`
📍 Position: `{settings.position.replace('_', ' ').title()}`
🎨 Color: `{settings.color.title()}`
👻 Opacity: `{settings.opacity}/255`

Choose an option below:
"""
        
        await update.message.reply_text(
            preview_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for watermark text updates."""
        if context.user_data and 'setting_text' in context.user_data:
            user_id = str(update.effective_user.id)
            new_text = update.message.text
            
            db = get_db_session()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
                    if settings:
                        settings.text = new_text
                        db.commit()
                        
                        # Show editing options after text update
                        keyboard = []
                        
                        # If there's pending media, show apply option first
                        if 'pending_photo' in context.user_data or 'pending_video' in context.user_data:
                            keyboard.extend([
                                [InlineKeyboardButton("✅ Apply Watermark", callback_data="apply_watermark")],
                                [InlineKeyboardButton("📏 Font Size", callback_data="quick_font_size"),
                                 InlineKeyboardButton("📍 Position", callback_data="quick_position")],
                                [InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                                 InlineKeyboardButton("👻 Opacity", callback_data="quick_opacity")],
                                [InlineKeyboardButton("🔙 More Options", callback_data="back_to_media")]
                            ])
                        else:
                            # No pending media, show general editing options
                            keyboard.extend([
                                [InlineKeyboardButton("📏 Font Size", callback_data="setting_font_size"),
                                 InlineKeyboardButton("📍 Position", callback_data="setting_position")],
                                [InlineKeyboardButton("🎨 Color", callback_data="setting_color"),
                                 InlineKeyboardButton("👻 Opacity", callback_data="setting_opacity")],
                                [InlineKeyboardButton("⚙️ All Settings", callback_data="settings_menu")]
                            ])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        response_text = f"✅ Watermark text updated to: '{new_text}'\n\nWhat would you like to edit next?"
                        
                        await update.message.reply_text(
                            response_text,
                            reply_markup=reply_markup
                        )
                        del context.user_data['setting_text']
            finally:
                db.close()
        else:
            await update.message.reply_text(
                "👋 Send me a photo or video to add a watermark!\n"
                "Use /help for more information."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "apply_watermark":
            await self.process_pending_media(update, context)
        elif data in ["quick_text", "quick_size", "quick_font_size", "quick_position", "quick_color", "quick_opacity"]:
            await self.handle_quick_setting(update, context, data)
        elif data == "done_editing":
            await query.edit_message_text("✅ All done! Send another photo or video to add watermarks.")
        elif data == "reprocess_last":
            await query.edit_message_text("🔄 Please send the same image or video again to see the updated watermark.")
        elif data == "settings_menu":
            await self.settings_command(update, context)
        elif data == "back_to_media":
            await self.show_media_options(update, context)
        elif data and data.startswith("setting_"):
            await self.handle_setting_callback(update, context, data)
        elif data and data.startswith("menu_"):
            await self.handle_menu_callback(update, context, data)
        elif data and (data.startswith("fontsize_") or data.startswith("opacity_") or 
                     data.startswith("position_") or data.startswith("color_")):
            await self.update_setting(update, data)
            # After updating setting, show apply watermark option
            await self.show_apply_option(update, context)
    
    async def handle_setting_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle settings callback queries."""
        setting_type = data.replace("setting_", "")
        
        if setting_type == "text":
            context.user_data['setting_text'] = True
            await update.callback_query.edit_message_text(
                "📝 Please send me the new watermark text:"
            )
        elif setting_type == "font_size":
            keyboard = [
                [InlineKeyboardButton("Small (32)", callback_data="fontsize_32")],
                [InlineKeyboardButton("Medium (64)", callback_data="fontsize_64")],
                [InlineKeyboardButton("Large (96)", callback_data="fontsize_96")],
                [InlineKeyboardButton("Extra Large (128)", callback_data="fontsize_128")],
                [InlineKeyboardButton("Huge (160)", callback_data="fontsize_160")],
                [InlineKeyboardButton("Massive (200)", callback_data="fontsize_200")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "📏 Choose font size:",
                reply_markup=reply_markup
            )
        elif setting_type == "opacity":
            keyboard = [
                [InlineKeyboardButton("5% ░", callback_data="opacity_13"), InlineKeyboardButton("10% ░", callback_data="opacity_26")],
                [InlineKeyboardButton("15% ▒", callback_data="opacity_38"), InlineKeyboardButton("20% ▒", callback_data="opacity_51")],
                [InlineKeyboardButton("25% ▒", callback_data="opacity_64"), InlineKeyboardButton("30% ▓", callback_data="opacity_77")],
                [InlineKeyboardButton("35% ▓", callback_data="opacity_89"), InlineKeyboardButton("40% ▓", callback_data="opacity_102")],
                [InlineKeyboardButton("45% ▓", callback_data="opacity_115"), InlineKeyboardButton("50% █", callback_data="opacity_128")],
                [InlineKeyboardButton("55% █", callback_data="opacity_140"), InlineKeyboardButton("60% █", callback_data="opacity_153")],
                [InlineKeyboardButton("65% █", callback_data="opacity_166"), InlineKeyboardButton("70% █", callback_data="opacity_179")],
                [InlineKeyboardButton("75% █", callback_data="opacity_191"), InlineKeyboardButton("80% █", callback_data="opacity_204")],
                [InlineKeyboardButton("85% █", callback_data="opacity_217"), InlineKeyboardButton("90% █", callback_data="opacity_230")],
                [InlineKeyboardButton("95% █", callback_data="opacity_242"), InlineKeyboardButton("100% █", callback_data="opacity_255")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "👻 Choose opacity level:\n░ = Very transparent\n▒ = Light\n▓ = Medium\n█ = Strong",
                reply_markup=reply_markup
            )
        elif setting_type == "position":
            keyboard = [
                [InlineKeyboardButton("Top Left", callback_data="position_top_left")],
                [InlineKeyboardButton("Top Right", callback_data="position_top_right")],
                [InlineKeyboardButton("Center", callback_data="position_center")],
                [InlineKeyboardButton("Bottom Left", callback_data="position_bottom_left")],
                [InlineKeyboardButton("Bottom Right", callback_data="position_bottom_right")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "📍 Choose position:",
                reply_markup=reply_markup
            )
        elif setting_type == "color":
            keyboard = [
                [InlineKeyboardButton("White", callback_data="color_white")],
                [InlineKeyboardButton("Black", callback_data="color_black")],
                [InlineKeyboardButton("Red", callback_data="color_red")],
                [InlineKeyboardButton("Blue", callback_data="color_blue")],
                [InlineKeyboardButton("Green", callback_data="color_green")],
                [InlineKeyboardButton("Yellow", callback_data="color_yellow")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "🎨 Choose color:",
                reply_markup=reply_markup
            )
        
        # Handle setting value changes
        if data.startswith("fontsize_") or data.startswith("opacity_") or data.startswith("position_") or data.startswith("color_"):
            await self.update_setting(update, data)
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle main menu callback queries."""
        menu_action = data.replace("menu_", "")
        
        if menu_action == "upload":
            await update.callback_query.edit_message_text(
                "📷 **Ready to add watermarks!**\n\n"
                "Send me a photo or video and I'll add your watermark with current settings.\n\n"
                "You can customize the watermark after processing using quick edit buttons.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif menu_action == "settings":
            await self.settings_command(update, context)
        elif menu_action == "current":
            user_id = str(update.effective_user.id)
            
            db = get_db_session()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    return
                
                settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
                if not settings:
                    return
                
                settings_text = f"""
📊 **Current Watermark Settings**

📝 **Text:** `{settings.text}`
📏 **Font Size:** `{settings.font_size}px`
👻 **Opacity:** `{int((settings.opacity/255)*100)}%` (transparency)
📍 **Position:** `{settings.position.replace('_', ' ').title()}`
🎨 **Color:** `{settings.color.title()}`

Send a photo or video to apply these settings!
"""
                
                keyboard = [
                    [InlineKeyboardButton("⚙️ Change Settings", callback_data="menu_settings")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    settings_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            finally:
                db.close()
        
        elif menu_action == "help":
            help_text = """
❓ **Help & Instructions**

**How to use the bot:**
1. Send me a photo or video
2. I'll add your watermark automatically
3. Use quick edit buttons to customize
4. Download your watermarked media

**Available customizations:**
• Text content and font size
• Opacity (transparency level)
• Position on the media
• Text color

**Commands:**
/start - Show welcome and main menu
/menu - Show main menu anytime
/settings - Open settings panel
/help - Show this help

**Supported formats:**
📷 Images: JPG, PNG, BMP, TIFF
🎬 Videos: MP4, AVI, MOV, MKV
"""
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                help_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif menu_action == "quick_text":
            context.user_data['setting_text'] = True
            await update.callback_query.edit_message_text(
                "📝 **Quick Text Change**\n\n"
                "Please send me the new watermark text:",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "back_to_main_menu":
            await self.show_main_menu_edit(update, context)
    
    async def show_main_menu_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu using edit_message_text for callback queries."""
        user_id = str(update.effective_user.id)
        
        # Get current user settings
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
            if not settings:
                return
        finally:
            db.close()
        
        keyboard = [
            [
                InlineKeyboardButton("📷 Add Watermark", callback_data="menu_upload"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ],
            [
                InlineKeyboardButton("📊 Current Settings", callback_data="menu_current"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ],
            [
                InlineKeyboardButton("📝 Quick Text Change", callback_data="menu_quick_text")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = f"""
🎯 **Watermark Bot Main Menu**

**Current Settings Preview:**
📝 Text: `{settings.text}`
📏 Size: `{settings.font_size}px`
👻 Opacity: `{int((settings.opacity/255)*100)}%`
📍 Position: `{settings.position.replace('_', ' ').title()}`
🎨 Color: `{settings.color.title()}`

Choose an option below or send a photo/video to start:
"""
        
        await update.callback_query.edit_message_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_quick_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE, setting_type: str):
        """Handle quick setting changes."""
        if setting_type == "quick_text":
            context.user_data['setting_text'] = True
            await update.callback_query.message.reply_text(
                "📝 Please send me the new watermark text:"
            )
        elif setting_type in ["quick_size", "quick_font_size"]:
            keyboard = [
                [InlineKeyboardButton("Small (32)", callback_data="fontsize_32")],
                [InlineKeyboardButton("Medium (64)", callback_data="fontsize_64")],
                [InlineKeyboardButton("Large (96)", callback_data="fontsize_96")],
                [InlineKeyboardButton("Extra Large (128)", callback_data="fontsize_128")],
                [InlineKeyboardButton("Huge (160)", callback_data="fontsize_160")],
                [InlineKeyboardButton("Massive (200)", callback_data="fontsize_200")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                "📏 Choose font size:",
                reply_markup=reply_markup
            )
        elif setting_type == "quick_position":
            keyboard = [
                [InlineKeyboardButton("Top Left", callback_data="position_top_left")],
                [InlineKeyboardButton("Top Right", callback_data="position_top_right")],
                [InlineKeyboardButton("Center", callback_data="position_center")],
                [InlineKeyboardButton("Bottom Left", callback_data="position_bottom_left")],
                [InlineKeyboardButton("Bottom Right", callback_data="position_bottom_right")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                "📍 Choose position:",
                reply_markup=reply_markup
            )
        elif setting_type == "quick_color":
            keyboard = [
                [InlineKeyboardButton("White", callback_data="color_white"), InlineKeyboardButton("Black", callback_data="color_black")],
                [InlineKeyboardButton("Red", callback_data="color_red"), InlineKeyboardButton("Blue", callback_data="color_blue")],
                [InlineKeyboardButton("Green", callback_data="color_green"), InlineKeyboardButton("Yellow", callback_data="color_yellow")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                "🎨 Choose color:",
                reply_markup=reply_markup
            )
        elif setting_type == "quick_opacity":
            keyboard = [
                [InlineKeyboardButton("5% ░", callback_data="opacity_13"), InlineKeyboardButton("10% ░", callback_data="opacity_26")],
                [InlineKeyboardButton("15% ▒", callback_data="opacity_38"), InlineKeyboardButton("20% ▒", callback_data="opacity_51")],
                [InlineKeyboardButton("25% ▒", callback_data="opacity_64"), InlineKeyboardButton("30% ▓", callback_data="opacity_77")],
                [InlineKeyboardButton("35% ▓", callback_data="opacity_89"), InlineKeyboardButton("40% ▓", callback_data="opacity_102")],
                [InlineKeyboardButton("45% ▓", callback_data="opacity_115"), InlineKeyboardButton("50% █", callback_data="opacity_128")],
                [InlineKeyboardButton("55% █", callback_data="opacity_140"), InlineKeyboardButton("60% █", callback_data="opacity_153")],
                [InlineKeyboardButton("65% █", callback_data="opacity_166"), InlineKeyboardButton("70% █", callback_data="opacity_179")],
                [InlineKeyboardButton("75% █", callback_data="opacity_191"), InlineKeyboardButton("80% █", callback_data="opacity_204")],
                [InlineKeyboardButton("85% █", callback_data="opacity_217"), InlineKeyboardButton("90% █", callback_data="opacity_230")],
                [InlineKeyboardButton("95% █", callback_data="opacity_242"), InlineKeyboardButton("100% █", callback_data="opacity_255")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                "👻 Choose opacity level:\n░ = Very transparent\n▒ = Light\n▓ = Medium\n█ = Strong",
                reply_markup=reply_markup
            )
    
    async def process_pending_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the pending photo or video with current settings."""
        if 'pending_photo' in context.user_data:
            await self.process_photo_with_settings(update, context, context.user_data['pending_photo'])
        elif 'pending_video' in context.user_data:
            await self.process_video_with_settings(update, context, context.user_data['pending_video'])
        else:
            await update.callback_query.edit_message_text(
                "❌ No pending media found. Please send a new photo or video."
            )
    
    async def process_photo_with_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
        """Process photo with current watermark settings."""
        await update.callback_query.edit_message_text("🔄 Processing your image...")
        
        try:
            file = await context.bot.get_file(file_id)
            
            # Download file
            file_path = f"temp/{file_id}.jpg"
            await file.download_to_drive(file_path)
            
            # Process image
            user_id = str(update.effective_user.id)
            processed_path = await self.media_processor.process_image(file_path, user_id)
            
            # Send processed image with edit options
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Edit Text", callback_data="quick_text"),
                    InlineKeyboardButton("🔧 Font Size", callback_data="quick_size")
                ],
                [
                    InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                    InlineKeyboardButton("📍 Position", callback_data="quick_position")
                ],
                [
                    InlineKeyboardButton("💫 Opacity", callback_data="quick_opacity"),
                    InlineKeyboardButton("✅ Done", callback_data="done_editing")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            with open(processed_path, 'rb') as f:
                await update.callback_query.message.reply_photo(
                    photo=f,
                    caption="✅ Watermark applied successfully!\n\n🔧 Need adjustments? Use the buttons below to make quick changes:",
                    reply_markup=reply_markup
                )
            
            # Clean up
            os.remove(file_path)
            os.remove(processed_path)
            
            # Keep media for quick edits instead of clearing
            # del context.user_data['pending_photo']
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await update.callback_query.edit_message_text(
                "❌ Sorry, there was an error processing your image. Please try again."
            )
    
    async def process_video_with_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
        """Process video with current watermark settings."""
        await update.callback_query.edit_message_text("🔄 Processing your video... This may take a while.")
        
        try:
            file = await context.bot.get_file(file_id)
            
            # Download file
            file_path = f"temp/{file_id}.mp4"
            await file.download_to_drive(file_path)
            
            # Process video
            user_id = str(update.effective_user.id)
            processed_path = await self.media_processor.process_video(file_path, user_id)
            
            # Send processed video with edit options
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Edit Text", callback_data="quick_text"),
                    InlineKeyboardButton("🔧 Font Size", callback_data="quick_size")
                ],
                [
                    InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                    InlineKeyboardButton("📍 Position", callback_data="quick_position")
                ],
                [
                    InlineKeyboardButton("💫 Opacity", callback_data="quick_opacity"),
                    InlineKeyboardButton("✅ Done", callback_data="done_editing")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            with open(processed_path, 'rb') as f:
                await update.callback_query.message.reply_video(
                    video=f,
                    caption="✅ Watermark applied successfully!\n\n🔧 Need adjustments? Use the buttons below to make quick changes:",
                    reply_markup=reply_markup
                )
            
            # Clean up
            os.remove(file_path)
            os.remove(processed_path)
            
            # Keep media for quick edits instead of clearing
            # del context.user_data['pending_video']
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await update.callback_query.edit_message_text(
                "❌ Sorry, there was an error processing your video. Please try again."
            )
    
    async def show_apply_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show apply watermark option after setting change."""
        keyboard = [
            [InlineKeyboardButton("✅ Apply Watermark", callback_data="apply_watermark")],
            [InlineKeyboardButton("🔙 More Options", callback_data="back_to_media")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "✅ Setting updated! Ready to apply watermark?",
            reply_markup=reply_markup
        )
    
    async def update_setting(self, update: Update, data: str):
        """Update a specific setting based on callback data."""
        user_id = str(update.effective_user.id)
        
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
            if not settings:
                return
            
            message = ""
            if data.startswith("fontsize_"):
                font_size = int(data.split("_")[1])
                settings.font_size = font_size
                message = f"✅ Font size updated to: {font_size}"
            elif data.startswith("opacity_"):
                opacity = int(data.split("_")[1])
                settings.opacity = opacity
                message = f"✅ Opacity updated to: {opacity}/255"
            elif data.startswith("position_"):
                position = data.replace("position_", "")
                settings.position = position
                message = f"✅ Position updated to: {position.replace('_', ' ')}"
            elif data.startswith("color_"):
                color = data.split("_")[1]
                settings.color = color
                message = f"✅ Color updated to: {color}"
            
            db.commit()
            
            # Show updated setting and option to reprocess
            keyboard = [
                [InlineKeyboardButton("🔄 Apply Changes", callback_data="reprocess_last")],
                [InlineKeyboardButton("✅ Done", callback_data="done_editing")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"{message}\n\n🔄 Want to see the changes? Apply them to your last image/video:",
                reply_markup=reply_markup
            )
            
        finally:
            db.close()
    
    async def show_media_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show media customization options again."""
        user_id = str(update.effective_user.id)
        
        db = get_db_session()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                settings = db.query(WatermarkSettings).filter(WatermarkSettings.user_id == user.id).first()
                if not settings:
                    settings = WatermarkSettings(user_id=user.id, **config.DEFAULT_WATERMARK_SETTINGS)
                    db.add(settings)
                    db.commit()
            else:
                return
        finally:
            db.close()
        
        # Show customization options
        keyboard = [
            [
                InlineKeyboardButton("✅ Apply Watermark", callback_data="apply_watermark"),
                InlineKeyboardButton("📝 Change Text", callback_data="quick_text")
            ],
            [
                InlineKeyboardButton("📏 Font Size", callback_data="quick_font_size"),
                InlineKeyboardButton("📍 Position", callback_data="quick_position")
            ],
            [
                InlineKeyboardButton("🎨 Color", callback_data="quick_color"),
                InlineKeyboardButton("👻 Opacity", callback_data="quick_opacity")
            ],
            [
                InlineKeyboardButton("⚙️ Advanced Settings", callback_data="settings_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        media_type = "📸 Image" if 'pending_photo' in context.user_data else "🎬 Video"
        
        preview_text = f"""
{media_type} ready for processing!

**Current watermark settings:**
📝 Text: `{settings.text}`
📏 Font Size: `{settings.font_size}`
📍 Position: `{settings.position.replace('_', ' ').title()}`
🎨 Color: `{settings.color.title()}`
👻 Opacity: `{settings.opacity}/255`

Choose an option below:
"""
        
        await update.callback_query.edit_message_text(
            preview_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )