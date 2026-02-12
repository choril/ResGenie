"""智能体执行模型"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON, Enum, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .user import Base

class AgentType(str, enum.Enum):
    """智能体类型枚举"""
    PLANNER = "planner"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    WRITER = "writer"

class AgentStatus(str, enum.Enum):
    """智能体执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentExecution(Base):
    """智能体执行表模型"""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("research_tasks.id"), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.PENDING)
    input_data = Column(JSON, nullable=True)  # 智能体输入
    output_data = Column(JSON, nullable=True)  # 智能体输出
    execution_log = Column(Text, nullable=True)  # 执行日志
    error_message = Column(Text, nullable=True)  # 错误信息
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    task = relationship("ResearchTask", back_populates="agent_executions")
    
    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_type='{self.agent_type}', status='{self.status}', context_id='{self.context_id}')>"
