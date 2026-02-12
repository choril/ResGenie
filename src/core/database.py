"""数据库连接和初始化模块"""
from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# 根据环境选择数据库URL
def _get_database_url() -> str:
    """根据环境获取数据库URL"""
    env = settings.resgenie_env
    if env == "development":
        return settings.dev_database_url
    elif env == "testing":
        return settings.test_database_url
    elif env == "production":
        return settings.prod_database_url
    else:
        return settings.dev_database_url

# 创建数据库引擎
engine = create_engine(
    _get_database_url(),
    pool_pre_ping=True,           # 连接池预ping，确保连接有效
    pool_size=10,                 # 连接池大小
    max_overflow=20,              # 最大溢出连接数
    pool_timeout=30,              # 获取连接超时时间（秒）
    pool_recycle=3600,            # 连接回收时间（秒），1小时后回收连接
    pool_use_lifo=True,           # 使用LIFO策略，优先使用最近使用的连接
    echo=False,                   # 不输出SQL日志
    echo_pool=False,              # 不输出连接池日志
    connect_args={
        "connect_timeout": 20,    # 连接超时时间
        "options": "-c timezone=utc",  # 使用UTC时区
    } if settings.resgenie_env == "production" else {}
)

# 添加连接池事件监听器
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """连接建立时的回调"""
    logger.debug("数据库连接已建立")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """从连接池获取连接时的回调"""
    logger.debug("从连接池获取连接")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """连接归还到连接池时的回调"""
    logger.debug("连接归还到连接池")

# 创建数据库会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 提交后不使对象过期，减少查询
)

# 定义数据库模型的基类
Base = declarative_base()

# 懒加载模型导入（避免循环依赖）
_models_imported = False

def _ensure_models_imported():
    """确保所有模型已导入并注册"""
    global _models_imported
    if not _models_imported:
        try:
            from ..models import User, ResearchTask, Document, AgentExecution, Report
            _models_imported = True
            logger.debug("数据库模型已导入")
        except ImportError as e:
            logger.error(f"导入数据库模型失败: {e}")
            raise

def get_db() -> Generator[Session, None, None]:
    """
    数据库会话生成器，用于依赖注入场景。
    
    主要用于 Web 框架（如 FastAPI）的依赖注入系统，
    确保每个请求获得独立的数据库会话，并在请求结束后自动关闭。
    
    特点：
    - 不自动提交事务，需要手动调用 db.commit()
    - 异常时自动回滚事务
    - 确保会话被正确关闭
    
    Yields:
        Session: 数据库会话对象
        
    Example:
        # FastAPI 依赖注入
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        logger.debug("数据库会话已创建")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"数据库操作错误: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"未知错误: {e}")
        db.rollback()
        raise
    finally:
        try:
            db.close()
            logger.debug("数据库会话已关闭")
        except Exception as e:
            logger.error(f"关闭数据库会话时出错: {e}")

@contextmanager
def get_db_context():
    """
    上下文管理器，使用with语句管理数据库会话
    
    使用示例：
        with get_db_context() as db:
            db.execute("SELECT * FROM users")
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        logger.debug("数据库会话已创建")
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"数据库操作错误: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"未知错误: {e}")
        db.rollback()
        raise
    finally:
        try:
            db.close()
            logger.debug("数据库会话已关闭")
        except Exception as e:
            logger.error(f"关闭数据库会话时出错: {e}")

def init_db() -> None:
    """
    初始化数据库，创建所有表
    
    Raises:
        SQLAlchemyError: 数据库操作失败时抛出
    """
    try:
        logger.info("开始初始化数据库...")
        # 确保模型已导入
        _ensure_models_imported()
        # 创建所有表
        Base.metadata.create_all(bind=engine, checkfirst=True)
        # 显示已创建的表
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"数据库初始化成功，已创建表: {tables}")
    except SQLAlchemyError as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    except Exception as e:
        logger.error(f"初始化数据库时发生未知错误: {e}")
        raise

def drop_db() -> None:
    """
    删除所有表（仅用于测试）
    
    Raises:
        SQLAlchemyError: 数据库操作失败时抛出
        RuntimeError: 在生产环境中调用时抛出
    """
    # 安全检查：防止在生产环境中删除表
    if settings.resgenie_env == "production":
        raise RuntimeError("不允许在生产环境中删除数据库表")
    try:
        logger.warning("开始删除数据库表...")
        # 确保模型已导入
        _ensure_models_imported()
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表已删除")
    except SQLAlchemyError as e:
        logger.error(f"删除数据库表失败: {e}")
        raise
    except Exception as e:
        logger.error(f"删除数据库表时发生未知错误: {e}")
        raise

def reset_db() -> None:
    """
    重置数据库：删除所有表并重新创建（仅用于测试）
    
    Raises:
        SQLAlchemyError: 数据库操作失败时抛出
        RuntimeError: 在生产环境中调用时抛出
    """
    # 安全检查
    if settings.resgenie_env == "production":
        raise RuntimeError("不允许在生产环境中重置数据库")
    
    try:
        logger.info("开始重置数据库...")
        drop_db()
        init_db()
        logger.info("数据库重置成功")
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        raise

def get_engine_info() -> dict:
    """
    获取数据库引擎信息（用于监控和调试）
    
    Returns:
        dict: 包含引擎配置和状态的字典
    """
    pool = engine.pool
    
    return {
        "database_url": str(engine.url).replace(
            engine.url.password or "", "***"
        ) if engine.url.password else str(engine.url),
        "pool_size": pool.size(),
        "max_overflow": pool._max_overflow,
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "timeout": pool._timeout,
        "recycle": pool._recycle,
        "pool_pre_ping": pool._pre_ping,
    }

def check_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True，否则返回False
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False

def close_all_connections() -> None:
    """
    关闭所有数据库连接
    """
    try:
        logger.info("关闭所有数据库连接...")
        engine.dispose()
        logger.info("所有数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")
        raise
