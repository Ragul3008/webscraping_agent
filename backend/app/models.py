import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from backend.app.core.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    downloads = relationship("DownloadTask", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    saved_searches = relationship("SavedSearch", back_populates="project", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="project", cascade="all, delete-orphan")

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    query = Column(String, nullable=False)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="saved_searches")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False) # e.g. "Kaggle", "HuggingFace", "Google Images"
    download_size = Column(String, nullable=True) # e.g. "250MB"
    image_count = Column(Integer, default=0)
    
    # AI Metric Scores
    trust_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    popularity = Column(String, default="Medium")
    license = Column(String, default="Unknown")
    duplicate_ratio = Column(Float, default=0.0)
    missing_labels = Column(Boolean, default=False)
    
    # Recommendations stored as text JSON
    recommendations_json = Column(Text, nullable=True) # Recommended model, expected accuracy, training difficulty, etc.
    metadata_json = Column(Text, nullable=True) # raw metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    images = relationship("PreviewImage", back_populates="dataset", cascade="all, delete-orphan")
    downloads = relationship("DownloadTask", back_populates="dataset", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="dataset", cascade="all, delete-orphan")

class PreviewImage(Base):
    __tablename__ = "preview_images"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    local_path = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True) # list of tags/classes
    phash = Column(String, nullable=True) # Perceptual hash for duplicates
    
    # Quality metrics
    nsfw_score = Column(Float, default=0.0)
    blur_score = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dataset = relationship("Dataset", back_populates="images")
    bookmarks = relationship("Bookmark", back_populates="preview_image", cascade="all, delete-orphan")

class DownloadTask(Base):
    __tablename__ = "download_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="PENDING") # PENDING, RUNNING, PAUSED, COMPLETED, FAILED
    progress = Column(Float, default=0.0) # 0 to 100
    speed = Column(String, default="0 KB/s")
    eta = Column(String, default="Unknown")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="downloads")
    dataset = relationship("Dataset", back_populates="downloads")

class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True)
    preview_image_id = Column(Integer, ForeignKey("preview_images.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="bookmarks")
    project = relationship("Project", back_populates="bookmarks")
    dataset = relationship("Dataset", back_populates="bookmarks")
    preview_image = relationship("PreviewImage", back_populates="bookmarks")
