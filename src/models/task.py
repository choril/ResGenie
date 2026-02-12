"""研究任务模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .user import Base

class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 待处理
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败

class ResearchTask(Base):
    """研究任务表模型"""
    __tablename__ = "research_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 研究任务所属用户ID， nullable=True 表示研究任务可以不关联任何用户
    query = Column(Text, nullable=False)  # 研究任务的查询语句
    depth = Column(String(20), nullable=False)  # 研究任务的深度，可选值为 shallow, moderate, deep
    language = Column(String(10), nullable=False, default="zh")  # 研究任务的语言，可选值为 zh, en
    max_documents = Column(Integer, nullable=False, default=100)  # 研究任务的最大文档数，默认值为 100
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)  # 研究任务的状态，默认值为 PENDING
    progress = Column(Integer, nullable=False, default=0)  # 研究任务的进度，默认值为 0
    result_url = Column(String(500), nullable=True)  # 研究任务的结果URL， nullable=True 表示研究任务可以不生成结果URL
    error_message = Column(Text, nullable=True)  # 研究任务的错误信息， nullable=True 表示研究任务可以不包含错误信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 研究任务的完成时间， nullable=True 表示研究任务可以不包含完成时间
    
    # 关系
    user = relationship("User", backref="tasks")  # 研究任务所属用户， backref="tasks" 表示在 User 模型中添加一个 tasks 属性，用于访问该用户的所有研究任务
    agent_executions = relationship("AgentExecution", back_populates="task")  # 研究任务的智能体执行记录， back_populates="task" 表示在 AgentExecution 模型中添加一个 task 属性，用于访问该智能体执行记录所属的研究任务
    documents = relationship("Document", back_populates="task")  # 研究任务的文档记录， back_populates="task" 表示在 Document 模型中添加一个 task 属性，用于访问该文档记录所属的研究任务
    report = relationship("Report", back_populates="task", uselist=False)  # 研究任务的报告记录， back_populates="task" 表示在 Report 模型中添加一个 task 属性，用于访问该报告记录所属的研究任务
    
    def __repr__(self):
        return f"<ResearchTask(id={self.id}, query='{self.query[:50]}...', status='{self.status}')>"
