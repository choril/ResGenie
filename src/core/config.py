"""ResGenie 配置管理模块"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class ResGenieSettings(BaseSettings):
    """ResGenie 系统配置类"""
    # 基础配置
    resgenie_env: str = Field(default="development", description="运行环境: development, testing, production")
    log_level: str = Field(default="INFO", description="日志级别")
    cache_ttl: int = Field(default=3600, description="缓存过期时间(秒)")
    max_workers: int = Field(default=4, description="最大工作线程数")
    
    # 数据库配置
    dev_database_url: str = Field(default="postgresql://dev_user:dev_password@localhost:5432/resgenie_dev", description="开发环境数据库连接URL")
    test_database_url: str = Field(default="postgresql://test_user:test_password@localhost:5432/resgenie_test", description="测试环境数据库连接URL")
    prod_database_url: str = Field(default="postgresql://prod_user:prod_password@localhost:5432/resgenie_prod", description="生产环境数据库连接URL")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    
    # LLM API配置
    # OpenAI API (可选)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API密钥")
    
    # Ollama配置 (本地部署)
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API基础URL")
    ollama_model: str = Field(default="qwen:7b", description="Ollama使用的模型")
    
    # 学术API配置
    arxiv_email: Optional[str] = Field(default=None, description="arXiv API邮箱")
    semantic_scholar_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API密钥")
    crossref_email: Optional[str] = Field(default=None, description="CrossRef API邮箱")
    
    # Google Custom Search API
    google_api_key: Optional[str] = Field(default=None, description="Google API密钥")
    google_cse_id: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    
    # API配置
    api_key: str = Field(default="your_api_key", description="API访问密钥")
    api_host: str = Field(default="0.0.0.0", description="API服务主机")
    api_port: int = Field(default=8000, description="API服务端口")
    
    # 前端配置
    frontend_host: str = Field(default="0.0.0.0", description="前端服务主机")
    frontend_port: int = Field(default=8501, description="前端服务端口")
    
    # 安全配置
    secret_key: str = Field(default="your_secret_key", description="安全密钥")
    cors_origins: str = Field(default="http://localhost:8501,http://127.0.0.1:8501", description="CORS允许的源")
    
    # 路径配置
    data_dir: str = Field(default="./data", description="数据目录")
    cache_dir: str = Field(default="./data/cache", description="缓存目录")
    vector_store_dir: str = Field(default="./data/vector_store", description="向量存储目录")
    log_dir: str = Field(default="./logs", description="日志目录")
    
    # pydantic_settings.BaseSettings配置
    model_config = ConfigDict(
        env_file=".env",  # 从.env文件加载环境变量
        env_file_encoding="utf-8",
        case_sensitive=False  # 不区分环境变量大小写
    )

def get_settings(env: Optional[str] = None) -> ResGenieSettings:
    """根据环境获取配置
    
    Args:
        env: 环境名称，可选值: development, testing, production
            如果为None，则使用环境变量中的RESGENIE_ENV值
    
    Returns:
        ResGenieSettings: 配置对象
    """
    settings = ResGenieSettings()
    
    # 如果指定了环境，覆盖配置中的环境值
    if env is not None:
        settings.resgenie_env = env
    
    return settings

# 默认配置实例
settings = get_settings()