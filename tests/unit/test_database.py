"""测试Postgresql数据库模块功能"""
# python -m tests.unit.test_database
from src.core.database import engine, _get_database_url, get_db, get_db_context, init_db, drop_db, reset_db, get_engine_info, check_connection, close_all_connections
from sqlalchemy import inspect

def test_get_database_url():
    """测试数据库URL获取函数"""
    print("=== 测试数据库URL获取函数 ===")

    url = _get_database_url()
    print(f"数据库URL: {url}")
    assert url.startswith("postgresql://"), "URL协议错误"
    assert "localhost" in url, "URL主机错误"
    assert "5432" in url, "URL端口错误"
    assert "resgenie" in url, "URL数据库名错误"
    print("√ 数据库URL测试通过")

def test_get_db():
    """测试数据库会话获取函数"""
    print("=== 测试数据库会话获取函数 ===")

    db = next(get_db())
    assert db is not None, "数据库会话获取失败"
    db.close()
    print("√ 数据库会话测试通过")

def test_get_db_context():
    """测试数据库上下文获取函数"""
    print("=== 测试数据库上下文获取函数 ===")

    with get_db_context() as db:
        assert db is not None, "数据库上下文获取失败"
    print("√ 数据库上下文测试通过")

def test_init_db():
    """测试数据库初始化函数"""
    print("=== 测试数据库初始化函数 ===")

    init_db()

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table_name in tables:
        print(f"\n表: {table_name}")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    
    assert "users" in tables, "users表未创建"
    assert "research_tasks" in tables, "research_tasks表未创建"
    assert "documents" in tables, "documents表未创建"
    assert "agent_executions" in tables, "agent_executions表未创建"
    assert "reports" in tables, "reports表未创建"

    drop_db()
    print("√ 数据库初始化测试通过")

def test_drop_db():
    """测试数据库清理函数"""
    print("=== 测试数据库清理函数 ===")

    init_db()
    drop_db()

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" not in tables, "users表未删除"
    assert "research_tasks" not in tables, "research_tasks表未删除"
    assert "documents" not in tables, "documents表未删除"
    assert "agent_executions" not in tables, "agent_executions表未删除"
    assert "reports" not in tables, "reports表未删除"

    print("√ 数据库清理测试通过")

def test_reset_db():
    """测试数据库重置函数"""
    print("=== 测试数据库重置函数 ===")

    init_db()
    reset_db()

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables, "users表未创建"
    assert "research_tasks" in tables, "research_tasks表未创建"
    assert "documents" in tables, "documents表未创建"
    assert "agent_executions" in tables, "agent_executions表未创建"
    assert "reports" in tables, "reports表未创建"

    print("√ 数据库重置测试通过")

def test_get_engine_info():
    """测试数据库引擎信息获取函数"""
    print("=== 测试数据库引擎信息获取函数 ===")

    info = get_engine_info()
    print(info)
    assert info['database_url'] == _get_database_url().replace("dev_password", "***"), "数据库URL不匹配"
    print("√ 数据库引擎信息测试通过")

def test_check_connection():
    """测试数据库连接检查函数"""
    print("=== 测试数据库连接检查函数 ===")

    assert check_connection() == True, "数据库连接检查失败"
    print("√ 数据库连接检查测试通过")

def test_close_all_connections():
    """测试关闭所有数据库连接函数"""
    print("=== 测试关闭所有数据库连接函数 ===")

    # 建立持久连接（不使用 with，手动管理）
    conn = engine.connect()
    
    # 获取引擎信息
    info_before = get_engine_info()
    print(f"建立连接后 - 已检出连接: {info_before['checked_out']}")
    assert info_before['checked_out'] >= 1, "连接未建立"
    
    # 关闭所有连接
    close_all_connections()
    
    # 检查连接池状态（已检出连接应为 0）
    info_after = get_engine_info()
    print(f"关闭后 - 已检出连接: {info_after['checked_out']}")
    
    # 验证连接池已清空
    assert info_after['checked_out'] == 0, "连接池未清空"
    # 验证引擎仍然可以创建新连接（dispose 后引擎仍可用）
    assert check_connection() == True, "引擎无法创建新连接"
    
    print("√ 数据库连接关闭测试通过")

if __name__ == "__main__":
    test_get_database_url()
    test_get_db()
    test_get_db_context()
    test_init_db()
    test_drop_db()
    test_reset_db()
    test_get_engine_info()
    test_check_connection()
    test_close_all_connections()
