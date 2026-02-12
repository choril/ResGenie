"""报告模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .user import Base

class Report(Base):
    """报告表模型"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("research_tasks.id"), nullable=False, unique=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    format = Column(String(20), nullable=False, default="markdown")  # markdown, pdf
    statistics = Column(JSON, nullable=True)  # 统计信息
    visualizations = Column(JSON, nullable=True)  # 可视化数据
    citations = Column(JSON, nullable=True)  # 引用信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    task = relationship("ResearchTask", back_populates="report")  # 报告所属研究任务， back_populates="report" 表示在 ResearchTask 模型中添加一个 report 属性，用于访问该研究任务的报告记录
    
    def __repr__(self):
        return f"<Report(id={self.id}, title='{self.title[:50]}...', format='{self.format}')>"
