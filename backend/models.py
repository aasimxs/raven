from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    targets = relationship("Target", back_populates="case")
    evidence = relationship("Evidence", back_populates="case")

class Target(Base):
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    seed_type = Column(String)  # username, email, etc.
    seed_value = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    case = relationship("Case", back_populates="targets")

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    source = Column(String) # e.g., 'instagram', 'github', 'haveibeenpwned'
    retrieval_method = Column(String) # e.g., 'web_scrape', 'api'
    data_hash = Column(String)
    confidence = Column(Float)
    storage_url = Column(String) # Local file path relative to workspace
    raw_payload = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    case = relationship("Case", back_populates="evidence")

class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    source_type = Column(String)
    source_value = Column(String)
    target_type = Column(String)
    target_value = Column(String)
    relationship_type = Column(String) # e.g., 'HAS_ACCOUNT', 'RESOLVES_TO'
    confidence = Column(Float)
