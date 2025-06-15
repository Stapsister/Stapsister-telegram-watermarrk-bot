from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import json

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    usage_records = relationship("Usage", back_populates="user")
    watermark_settings = relationship("WatermarkSettings", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_type = Column(String, nullable=False)  # free, basic, premium, unlimited
    status = Column(String, default="active")  # active, expired, cancelled
    stripe_subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")

class Usage(Base):
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_type = Column(String, nullable=False)  # image, video
    processed_at = Column(DateTime, server_default=func.now())
    file_size = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_records")

class WatermarkSettings(Base):
    __tablename__ = "watermark_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, default="Watermark")
    font_size = Column(Integer, default=36)
    opacity = Column(Integer, default=128)  # 0-255
    position = Column(String, default="bottom_right")
    color = Column(String, default="white")
    font_family = Column(String, default="arial")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watermark_settings")
