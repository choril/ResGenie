#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ResGenie 智能体基类测试脚本

该脚本全面测试 base.py 模块中的所有类和方法，包括：
- AgentStatus 枚举类
- AgentState TypedDict
- AgentError 异常类及其子类
- BaseAgent 抽象基类的所有方法

测试输出包含详细的 DEBUG 信息，便于定位问题。
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from src.agents import (
    AgentError,
    AgentState,
    AgentStatus,
    BaseAgent,
    StateValidationError,
    ToolExecutionError,
    ToolNotFoundError,
)


class TestStats:
    """测试统计类"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
    
    def add_pass(self):
        self.total += 1
        self.passed += 1
    
    def add_fail(self):
        self.total += 1
        self.failed += 1
    
    def summary(self) -> str:
        return f"\n{'='*60}\n测试总结: 总计 {self.total} 个测试, 通过 {self.passed} 个, 失败 {self.failed} 个\n{'='*60}"


stats = TestStats()


def print_header(title: str) -> None:
    """打印测试区块标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_test(func_name: str, input_info: str, actual: Any, expected: Any = None, passed: bool = True) -> None:
    """打印测试详情"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"\n[测试] {func_name}")
    print(f"  输入: {input_info}")
    print(f"  实际输出: {actual}")
    if expected is not None:
        print(f"  预期输出: {expected}")
    print(f"  状态: {status}")
    
    if passed:
        stats.add_pass()
    else:
        stats.add_fail()


def assert_equal(actual: Any, expected: Any, func_name: str, input_info: str) -> bool:
    """断言相等"""
    passed = actual == expected
    print_test(func_name, input_info, actual, expected, passed)
    return passed


def assert_true(condition: bool, func_name: str, input_info: str, actual: Any) -> bool:
    """断言为真"""
    print_test(func_name, input_info, actual, passed=condition)
    return condition


def assert_raises(exception_class: type, func_name: str, input_info: str, func, *args, **kwargs) -> bool:
    """断言抛出异常"""
    try:
        func(*args, **kwargs)
        print_test(func_name, input_info, "未抛出异常", f"应抛出 {exception_class.__name__}", passed=False)
        stats.add_fail()
        return False
    except exception_class as e:
        print_test(func_name, input_info, f"抛出 {type(e).__name__}: {e}", f"应抛出 {exception_class.__name__}", passed=True)
        stats.add_pass()
        return True
    except Exception as e:
        print_test(func_name, input_info, f"抛出 {type(e).__name__}: {e}", f"应抛出 {exception_class.__name__}", passed=False)
        stats.add_fail()
        return False


class MockAgent(BaseAgent):
    """测试用模拟智能体"""
    
    @property
    def name(self) -> str:
        return "mock_agent"
    
    @property
    def description(self) -> str:
        return "用于测试的模拟智能体"
    
    async def run(self, state: AgentState) -> AgentState:
        state["status"] = AgentStatus.COMPLETED
        return state


@tool
def sample_search_tool(query: str) -> str:
    """示例搜索工具"""
    return f"搜索结果: {query}"


@tool
def failing_tool(query: str) -> str:
    """总是失败的工具"""
    raise RuntimeError("工具执行失败")


def test_agent_status():
    """测试 AgentStatus 枚举类"""
    print_header("测试 AgentStatus 枚举类")
    
    assert_equal(AgentStatus.IDLE.value, "idle", "AgentStatus.IDLE.value", "AgentStatus.IDLE")
    assert_equal(AgentStatus.RUNNING.value, "running", "AgentStatus.RUNNING.value", "AgentStatus.RUNNING")
    assert_equal(AgentStatus.WAITING.value, "waiting", "AgentStatus.WAITING.value", "AgentStatus.WAITING")
    assert_equal(AgentStatus.COMPLETED.value, "completed", "AgentStatus.COMPLETED.value", "AgentStatus.COMPLETED")
    assert_equal(AgentStatus.FAILED.value, "failed", "AgentStatus.FAILED.value", "AgentStatus.FAILED")
    
    assert_true(AgentStatus.IDLE == "idle", "AgentStatus 字符串比较", "AgentStatus.IDLE == 'idle'", AgentStatus.IDLE == "idle")
    
    status = AgentStatus.RUNNING
    assert_equal(f"状态: {status}", "状态: running", "AgentStatus 字符串格式化", "状态: running")


def test_agent_state():
    """测试 AgentState TypedDict"""
    print_header("测试 AgentState TypedDict")
    
    state: AgentState = AgentState(
        messages=[],
        current_task="测试任务",
        agent_type="test",
        status=AgentStatus.IDLE,
        tools_output={},
        context={},
        error="",
        metadata={}
    )
    
    assert_equal(state["current_task"], "测试任务", "AgentState 字段访问", "测试任务")
    assert_equal(state["status"], AgentStatus.IDLE, "AgentState status 字段", AgentStatus.IDLE)
    
    state["messages"] = [HumanMessage(content="你好")]
    assert_equal(len(state["messages"]), 1, "AgentState messages 添加", 1)


def test_agent_error():
    """测试 AgentError 异常类"""
    print_header("测试 AgentError 异常类")
    
    e1 = AgentError("测试错误")
    assert_equal(str(e1), "测试错误", "AgentError 基本消息", "测试错误")
    
    e2 = AgentError("测试错误", agent_name="test_agent")
    assert_equal(str(e2), "[test_agent] | 测试错误", "AgentError 带智能体名称", "[test_agent] | 测试错误")
    
    try:
        raise ValueError("原始错误")
    except ValueError as original:
        e3 = AgentError("测试错误", agent_name="test_agent", original_error=original)
        expected = "[test_agent] | 测试错误 | 原因: 原始错误"
        assert_equal(str(e3), expected, "AgentError 带原始异常", expected)


def test_tool_not_found_error():
    """测试 ToolNotFoundError 异常类"""
    print_header("测试 ToolNotFoundError 异常类")
    
    e = ToolNotFoundError("工具不存在", agent_name="mock_agent")
    assert_true("[mock_agent]" in str(e), "ToolNotFoundError 消息格式", str(e), "[mock_agent]" in str(e))


def test_tool_execution_error():
    """测试 ToolExecutionError 异常类"""
    print_header("测试 ToolExecutionError 异常类")
    
    original = RuntimeError("连接超时")
    e = ToolExecutionError("执行失败", agent_name="mock_agent", original_error=original)
    assert_true("执行失败" in str(e), "ToolExecutionError 消息", str(e), "执行失败" in str(e))
    assert_true("连接超时" in str(e), "ToolExecutionError 原始错误", str(e), "连接超时" in str(e))


def test_state_validation_error():
    """测试 StateValidationError 异常类"""
    print_header("测试 StateValidationError 异常类")
    
    e = StateValidationError("状态无效", agent_name="mock_agent")
    assert_true("状态无效" in str(e), "StateValidationError 消息", str(e), "状态无效" in str(e))


def test_base_agent_init():
    """测试 BaseAgent 初始化"""
    print_header("测试 BaseAgent 初始化")
    
    agent = MockAgent()
    assert_equal(agent.name, "mock_agent", "agent.name", "mock_agent")
    assert_equal(agent.description, "用于测试的模拟智能体", "agent.description", "用于测试的模拟智能体")
    assert_equal(agent.max_retries, 3, "agent.max_retries 默认值", 3)
    assert_equal(agent.timeout, 30.0, "agent.timeout 默认值", 30.0)
    assert_equal(agent.tools, [], "agent.tools 默认空列表", [])
    assert_equal(agent.state["status"], AgentStatus.IDLE, "agent.state['status']", AgentStatus.IDLE)
    
    agent2 = MockAgent(max_retries=5, timeout=60.0)
    assert_equal(agent2.max_retries, 5, "agent.max_retries 自定义值", 5)
    assert_equal(agent2.timeout, 60.0, "agent.timeout 自定义值", 60.0)


def test_base_agent_repr_str():
    """测试 BaseAgent __repr__ 和 __str__"""
    print_header("测试 BaseAgent __repr__ 和 __str__")
    
    agent = MockAgent()
    
    repr_result = repr(agent)
    assert_true("MockAgent" in repr_result, "__repr__ 包含类名", repr_result, "MockAgent" in repr_result)
    assert_true("mock_agent" in repr_result, "__repr__ 包含名称", repr_result, "mock_agent" in repr_result)
    
    str_result = str(agent)
    assert_equal(str_result, "[mock_agent] 用于测试的模拟智能体", "__str__ 输出", "[mock_agent] 用于测试的模拟智能体")


def test_state_management():
    """测试状态管理方法"""
    print_header("测试状态管理方法")
    
    agent = MockAgent()
    
    agent.update_state(status=AgentStatus.RUNNING, current_task="测试任务")
    assert_equal(agent.state["status"], AgentStatus.RUNNING, "update_state 更新 status", AgentStatus.RUNNING)
    assert_equal(agent.state["current_task"], "测试任务", "update_state 更新 current_task", "测试任务")
    
    agent.update_state(invalid_key="无效值")
    assert_true("invalid_key" not in agent.state, "update_state 忽略无效字段", "invalid_key not in state", "invalid_key" not in agent.state)
    
    agent.reset_state()
    assert_equal(agent.state["status"], AgentStatus.IDLE, "reset_state 重置状态", AgentStatus.IDLE)
    assert_equal(agent.state["current_task"], "", "reset_state 清空任务", "")
    
    result = agent.validate_state()
    assert_true(result, "validate_state 验证有效状态", result, result)


def test_tool_registration():
    """测试工具注册方法"""
    print_header("测试工具注册方法")
    
    agent = MockAgent()
    
    agent.register_tool(sample_search_tool)
    assert_equal(len(agent.tools), 1, "register_tool 注册工具", 1)
    assert_equal(agent.tool_names, ["sample_search_tool"], "tool_names", ["sample_search_tool"])
    
    def custom_tool(x: int) -> int:
        """自定义工具"""
        return x * 2
    
    agent.register_tool(custom_tool, name="double")
    assert_equal(agent.tool_names, ["sample_search_tool", "double"], "register_tool 注册函数", ["sample_search_tool", "double"])
    
    assert_raises(
        ValueError,
        "register_tool 重复注册（无 overwrite）",
        "sample_search_tool",
        agent.register_tool,
        sample_search_tool
    )
    
    agent.register_tool(sample_search_tool, overwrite=True)
    assert_equal(len(agent.tools), 2, "register_tool 覆盖注册", 2)
    
    result = agent.unregister_tool("double")
    assert_true(result, "unregister_tool 成功注销", result, result)
    assert_equal(agent.tool_names, ["sample_search_tool"], "注销后工具列表", ["sample_search_tool"])
    
    result = agent.unregister_tool("non_existent")
    assert_true(not result, "unregister_tool 注销不存在的工具", result, not result)
    
    tool = agent.get_tool("sample_search_tool")
    assert_true(tool is not None, "get_tool 获取存在的工具", tool, tool is not None)
    
    tool = agent.get_tool("non_existent")
    assert_true(tool is None, "get_tool 获取不存在的工具", tool, tool is None)


def test_tool_invocation_sync():
    """测试同步工具调用"""
    print_header("测试同步工具调用")
    
    agent = MockAgent(tools=[sample_search_tool])
    
    result = agent.invoke_tool_sync("sample_search_tool", {"query": "测试查询"})
    assert_equal(result, "搜索结果: 测试查询", "invoke_tool_sync 正常调用", "搜索结果: 测试查询")
    
    assert_true("sample_search_tool" in agent.state["tools_output"], "工具结果缓存", agent.state["tools_output"], "sample_search_tool" in agent.state["tools_output"])
    
    assert_raises(
        ToolNotFoundError,
        "invoke_tool_sync 工具不存在",
        "non_existent",
        agent.invoke_tool_sync,
        "non_existent"
    )


def test_tool_invocation_async():
    """测试异步工具调用"""
    print_header("测试异步工具调用")
    
    async def run_async_tests():
        agent = MockAgent(tools=[sample_search_tool])
        
        result = await agent.invoke_tool("sample_search_tool", {"query": "异步测试"})
        assert_equal(result, "搜索结果: 异步测试", "invoke_tool 异步调用", "搜索结果: 异步测试")
        
        try:
            await agent.invoke_tool("non_existent")
            print_test("invoke_tool 工具不存在", "non_existent", "未抛出异常", passed=False)
            stats.add_fail()
        except ToolNotFoundError:
            print_test("invoke_tool 工具不存在", "non_existent", "抛出 ToolNotFoundError", passed=True)
            stats.add_pass()
    
    asyncio.run(run_async_tests())


def test_tool_retry():
    """测试工具重试机制"""
    print_header("测试工具重试机制")
    
    agent = MockAgent(tools=[failing_tool], max_retries=2)
    
    assert_raises(
        ToolExecutionError,
        "invoke_tool_sync 失败重试",
        "failing_tool",
        agent.invoke_tool_sync,
        "failing_tool",
        {"query": "测试"}
    )


def test_message_management():
    """测试消息管理方法"""
    print_header("测试消息管理方法")
    
    agent = MockAgent()
    
    agent.add_system_message("系统消息")
    assert_equal(len(agent.state["messages"]), 1, "add_system_message", 1)
    assert_true(isinstance(agent.state["messages"][0], SystemMessage), "消息类型为 SystemMessage", type(agent.state["messages"][0]).__name__, isinstance(agent.state["messages"][0], SystemMessage))
    
    agent.add_human_message("用户消息")
    assert_equal(len(agent.state["messages"]), 2, "add_human_message", 2)
    assert_true(isinstance(agent.state["messages"][1], HumanMessage), "消息类型为 HumanMessage", type(agent.state["messages"][1]).__name__, isinstance(agent.state["messages"][1], HumanMessage))
    
    agent.add_ai_message("AI消息")
    assert_equal(len(agent.state["messages"]), 3, "add_ai_message", 3)
    assert_true(isinstance(agent.state["messages"][2], AIMessage), "消息类型为 AIMessage", type(agent.state["messages"][2]).__name__, isinstance(agent.state["messages"][2], AIMessage))
    
    agent.add_tool_message("工具结果", tool_call_id="call_123")
    assert_equal(len(agent.state["messages"]), 4, "add_tool_message", 4)
    assert_true(isinstance(agent.state["messages"][3], ToolMessage), "消息类型为 ToolMessage", type(agent.state["messages"][3]).__name__, isinstance(agent.state["messages"][3], ToolMessage))
    
    messages = agent.get_messages()
    assert_equal(len(messages), 4, "get_messages 全部消息", 4)
    
    messages_no_system = agent.get_messages(include_system=False)
    assert_equal(len(messages_no_system), 3, "get_messages 排除系统消息", 3)
    
    last = agent.get_last_message()
    assert_true(last is not None, "get_last_message 返回消息", last, last is not None)
    
    agent.clear_messages()
    assert_equal(len(agent.state["messages"]), 0, "clear_messages 清空消息", 0)
    
    last = agent.get_last_message()
    assert_true(last is None, "get_last_message 空消息列表", last, last is None)


def test_context_management():
    """测试上下文管理方法"""
    print_header("测试上下文管理方法")
    
    agent = MockAgent()
    
    agent.set_context("key1", "value1")
    agent.set_context("key2", {"nested": "data"})
    
    assert_equal(agent.get_context("key1"), "value1", "get_context 获取字符串", "value1")
    assert_equal(agent.get_context("key2"), {"nested": "data"}, "get_context 获取字典", {"nested": "data"})
    assert_equal(agent.get_context("non_existent"), None, "get_context 不存在的键", None)
    assert_equal(agent.get_context("non_existent", default="默认值"), "默认值", "get_context 带默认值", "默认值")


def test_metadata_management():
    """测试元数据管理方法"""
    print_header("测试元数据管理方法")
    
    agent = MockAgent()
    
    agent.set_metadata("task_id", 123)
    agent.set_metadata("user_id", "user_001")
    
    assert_equal(agent.get_metadata("task_id"), 123, "get_metadata 获取 task_id", 123)
    assert_equal(agent.get_metadata("user_id"), "user_001", "get_metadata 获取 user_id", "user_001")
    assert_equal(agent.get_metadata("non_existent"), None, "get_metadata 不存在的键", None)
    assert_equal(agent.get_metadata("non_existent", default=0), 0, "get_metadata 带默认值", 0)


def test_error_handling():
    """测试错误处理方法"""
    print_header("测试错误处理方法")
    
    agent = MockAgent()
    
    agent.set_error("测试错误信息")
    assert_equal(agent.state["error"], "测试错误信息", "set_error 设置错误信息", "测试错误信息")
    assert_equal(agent.state["status"], AgentStatus.FAILED, "set_error 状态变为 FAILED", AgentStatus.FAILED)


def test_prepare_messages_for_llm():
    """测试 LLM 消息准备"""
    print_header("测试 LLM 消息准备")
    
    agent = MockAgent(system_prompt="你是一个测试智能体")
    agent.add_human_message("你好")
    agent.add_ai_message("你好！有什么可以帮助你的？")
    
    messages = agent.prepare_messages_for_llm()
    
    assert_equal(len(messages), 3, "prepare_messages_for_llm 消息数量", 3)
    assert_true(isinstance(messages[0], SystemMessage), "第一条是系统消息", type(messages[0]).__name__, isinstance(messages[0], SystemMessage))
    assert_equal(messages[0].content, "你是一个测试智能体", "系统消息内容", "你是一个测试智能体")


def test_get_summary():
    """测试状态摘要"""
    print_header("测试状态摘要")
    
    agent = MockAgent()
    long_task = "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的任务描述，用于测试截断功能是否正常工作"
    agent.update_state(current_task=long_task)
    agent.add_human_message("测试消息")
    agent.register_tool(sample_search_tool)
    
    summary = agent.get_states_summary()
    
    assert_equal(summary["name"], "mock_agent", "summary name", "mock_agent")
    assert_equal(summary["status"], AgentStatus.IDLE, "summary status", AgentStatus.IDLE)
    assert_equal(summary["message_count"], 1, "summary message_count", 1)
    assert_equal(summary["tool_count"], 1, "summary tool_count", 1)
    assert_equal(summary["has_error"], False, "summary has_error", False)
    assert_true("..." in summary["current_task"], "summary current_task 截断", summary["current_task"], "..." in summary["current_task"])


def test_run_method():
    """测试 run 方法"""
    print_header("测试 run 方法")
    
    async def run_test():
        agent = MockAgent()
        state = AgentState(
            messages=[],
            current_task="测试",
            agent_type="mock",
            status=AgentStatus.IDLE,
            tools_output={},
            context={},
            error="",
            metadata={}
        )
        
        result = await agent.run(state)
        assert_equal(result["status"], AgentStatus.COMPLETED, "run 方法执行", AgentStatus.COMPLETED)
    
    asyncio.run(run_test())


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  ResGenie 智能体基类测试脚本")
    print("  测试文件: src/agents/base.py")
    print("="*60)
    
    test_agent_status()
    test_agent_state()
    test_agent_error()
    test_tool_not_found_error()
    test_tool_execution_error()
    test_state_validation_error()
    test_base_agent_init()
    test_base_agent_repr_str()
    test_state_management()
    test_tool_registration()
    test_tool_invocation_sync()
    test_tool_invocation_async()
    test_tool_retry()
    test_message_management()
    test_context_management()
    test_metadata_management()
    test_error_handling()
    test_prepare_messages_for_llm()
    test_get_summary()
    test_run_method()
    
    print(stats.summary())
    
    if stats.failed > 0:
        print("\n⚠️  存在失败的测试，请检查上述输出")
        return 1
    else:
        print("\n🎉 所有测试通过！")
        return 0


if __name__ == "__main__":
    exit(run_all_tests())
