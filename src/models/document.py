"""文档模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .user import Base

class Document(Base):
    """文档表模型"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("research_tasks.id"), nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(JSON, nullable=True)  # 作者列表
    abstract = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # 关键词列表
    url = Column(String(500), nullable=True)
    source = Column(String(100), nullable=True)  # 来源，如 arxiv, pubmed 等
    publication_date = Column(DateTime(timezone=True), nullable=True)
    content = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True)  # 其他元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    task = relationship("ResearchTask", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"
