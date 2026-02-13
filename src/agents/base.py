"""ResGenie 智能体基类模块

该模块定义了智能体的基础抽象类，提供：
- 统一的状态管理机制（基于 LangGraph TypedDict）
- 工具调用接口（基于 LangChain Tool）
- 消息传递机制（基于 LangChain Message）
- 完善的日志记录和错误处理
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, StructuredTool

from ..core.logging import get_logger

logger = get_logger(__name__)

class AgentStatus(str, Enum):
    """智能体运行状态枚举
    
    定义了智能体在不同场景下的运行状态，用于状态管理和流程控制。

    Attributes:
        IDLE: 智能体空闲状态，等待任务
        RUNNING: 智能体正在执行任务
        WAITING: 智能体等待工具调用结果
        COMPLETED: 任务执行成功完成
        FAILED: 任务执行过程中发生异常
    """
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentState(TypedDict, total=False):
    """智能体状态定义
    
    该状态类用于在 LangGraph 工作流中传递和跟踪智能体的执行状态。
    所有字段都是可选的（total=False），以支持增量更新。
    
    Attributes:
        messages: 消息历史列表，记录智能体与用户、其他智能体之间的对话
        current_task: 当前正在处理的任务描述
        agent_type: 智能体类型标识（planner/researcher/analyzer/writer）
        status: 智能体当前运行状态
        tools_output: 工具调用结果缓存
        context: 额外的上下文信息，用于在智能体间传递数据
        error: 错误信息，记录执行过程中的异常
        metadata: 元数据，存储任务ID、用户ID等附加信息
    """
    messages: List[BaseMessage]
    current_task: str
    agent_type: str
    status: AgentStatus
    tools_output: Dict[str, Any]
    context: Dict[str, Any]
    error: str
    metadata: Dict[str, Any]

class AgentError(Exception):
    """智能体异常基类
    
    所有智能体相关的异常都应继承此类，便于统一异常处理。
    
    Attributes:
        agent_name: 发生异常的智能体名称
        message: 错误消息
        original_error: 原始异常（如果有）
    """
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        logger.error(self._format_message())      # 记录异常日志
        super().__init__(self._format_message())  # 初始化父类异常，包含格式化后的消息

    
    def _format_message(self) -> str:
        parts = []
        if self.agent_name:
            parts.append(f"[{self.agent_name}]")
        parts.append(self.message)
        if self.original_error:
            parts.append(f"原因: {str(self.original_error)}")
        return " | ".join(parts)

class ToolNotFoundError(AgentError):
    """工具未找到异常"""
    pass

class ToolExecutionError(AgentError):
    """工具执行异常"""
    pass

class StateValidationError(AgentError):
    """状态验证异常"""
    pass

class BaseAgent(ABC):
    """智能体抽象基类
    
    所有具体智能体（Planner/Researcher/Analyzer/Writer）都应继承此类。
    该基类提供：
    - 统一的状态管理接口
    - 工具注册和调用机制
    - 消息处理工具方法
    - 完善的日志记录
    - 异常处理机制
    
    Attributes:
        name: 智能体名称（抽象属性，子类必须实现）
        description: 智能体功能描述（抽象属性，子类必须实现）
        tools: 已注册的工具列表
        state: 当前智能体状态
        max_retries: 工具调用最大重试次数
        timeout: 工具调用超时时间（秒）
    
    Example:
        >>> class MyAgent(BaseAgent):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_agent"
        ...     
        ...     @property
        ...     def description(self) -> str:
        ...         return "A custom agent"
        ...     
        ...     async def run(self, state: AgentState) -> AgentState:
        ...         # 实现具体逻辑
        ...         return state
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        tools: Optional[List[Union[BaseTool, Callable]]] = None,
        system_prompt: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None
    ):
        """初始化智能体
        
        Args:
            llm: 语言模型实例（LangChain LLM 或 ChatModel）
            tools: 工具列表，可以是 BaseTool 实例或可调用函数
            system_prompt: 系统提示词，用于设定智能体角色和行为
            state: 初始状态, 用于初始化智能体的状态
            max_retries: 工具调用最大重试次数，默认从配置读取
            timeout: 工具调用超时时间（秒），默认从配置读取
        """
        self._llm = llm
        self._tools: Dict[str, BaseTool] = {}
        self._system_prompt = system_prompt or self.default_system_prompt
        self._state: AgentState = self._init_state()
        self._max_retries = max_retries if max_retries is not None else 3
        self._timeout = timeout if timeout is not None else 30.0
        
        if tools:
            for tool in tools:
                self.register_tool(tool)
        
        logger.debug(
            "智能体初始化完成: name=%s, "
            "tools:{'count': %d, 'names': %s}, max_retries=%d "
            % (self.name, len(self._tools), self.tool_names, self._max_retries)
        )
    
    @property
    @abstractmethod
    def name(self) -> str:
        """智能体名称（子类必须实现）"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """智能体功能描述（子类必须实现）"""
        pass
    
    @property
    def default_system_prompt(self) -> str:
        """默认系统提示词"""
        return f"You are {self.name}. {self.description}"
    
    @property
    def tools(self) -> List[BaseTool]:
        """获取已注册的工具列表"""
        return list(self._tools.values())
    
    @property
    def tool_names(self) -> List[str]:
        """获取已注册的工具名称列表"""
        return list(self._tools.keys())
    
    @property
    def state(self) -> AgentState:
        """获取当前状态"""
        return self._state
    
    @property
    def max_retries(self) -> int:
        """获取最大重试次数"""
        return self._max_retries
    
    @property
    def timeout(self) -> float:
        """获取超时时间"""
        return self._timeout
    
    def _init_state(self) -> AgentState:
        """初始化智能体状态
        
        Returns:
            初始化后的 AgentState 实例
        """
        return AgentState(
            messages=[],
            current_task="",
            agent_type=self.name,
            status=AgentStatus.IDLE,
            tools_output={},
            context={},
            error="",
            metadata={}
        )
    
    def reset_state(self) -> None:
        """重置智能体状态到初始状态
        
        清空所有消息、上下文和工具输出，状态重置为 IDLE。
        """
        logger.info(f"[{self.name}] 重置智能体状态")
        self._state = self._init_state()
    
    def update_state(self, **kwargs) -> None:
        """更新智能体状态
        
        只允许更新 AgentState 中定义的字段，其他字段会被忽略。
        
        Args:
            **kwargs: 要更新的状态字段
        """
        updated_states = {}
        for key, value in kwargs.items():
            if key in AgentState.__annotations__:
                self._state[key] = value
                updated_states[key] = value
            else:
                logger.warning(f"[{self.name}] 忽略未知状态字段: {key}")
        
        if self.validate_state() and updated_states:
            logger.debug(f"[{self.name}] 状态验证通过，更新状态: {updated_states}")
    
    def validate_state(self) -> bool:
        """验证当前状态是否有效
        
        Returns:
            bool: 状态是否有效
        
        Raises:
            StateValidationError: 如果状态无效
        """
        if self._state.get("status") is None:
            raise StateValidationError(
                "状态缺少 status 字段",
                agent_name=self.name
            )
        
        if not isinstance(self._state.get("messages", []), list):
            raise StateValidationError(
                "messages 必须是列表类型",
                agent_name=self.name
            )
        
        return True
    
    def register_tool(
        self,
        tool: Union[BaseTool, Callable],
        name: Optional[str] = None,
        overwrite: bool = False
    ) -> None:
        """注册工具
        
        将工具添加到智能体的工具列表中。支持 BaseTool 实例或普通可调用函数。
        普通函数会自动转换为 StructuredTool。
        
        Args:
            tool: 工具实例或可调用函数
            name: 工具名称（可选，用于覆盖默认名称）
            overwrite: 是否覆盖已存在的同名工具
        
        Raises:
            ValueError: 如果工具类型不支持
            ValueError: 如果工具名称已存在且未设置 overwrite
        """
        if isinstance(tool, BaseTool):
            tool_name = name or tool.name
        elif callable(tool):
            tool_name = name or tool.__name__
            tool = StructuredTool.from_function(tool)
        else:
            logger.error(f"[{self.name}] 不支持的工具类型: {type(tool)}，必须是 BaseTool 实例或可调用函数")
            raise ValueError(f"不支持的工具类型: {type(tool)}，必须是 BaseTool 实例或可调用函数")
        
        if tool_name in self._tools:
            if not overwrite:
                logger.error(f"[{self.name}] 工具 '{tool_name}' 已存在，使用 overwrite=True 来覆盖")
                raise ValueError(f"工具 '{tool_name}' 已存在，使用 overwrite=True 来覆盖")
            logger.warning(f"[{self.name}] 工具 '{tool_name}' 将被覆盖")
        
        self._tools[tool_name] = tool
        logger.info(f"[{self.name}] 注册工具: {tool_name}")
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具
        
        从智能体的工具列表中移除指定工具。
        
        Args:
            name: 工具名称
        
        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"[{self.name}] 注销工具: {name}")
            return True
        
        logger.warning(f"[{self.name}] 工具 `{name}` 不存在，无法注销")
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取指定名称的工具
        
        Args:
            name: 工具名称
        
        Returns:
            BaseTool 或 None（如果工具不存在）
        """
        return self._tools.get(name)
    
    async def invoke_tool(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        """异步调用工具
        
        使用异步方式调用指定工具，支持重试机制。
        
        Args:
            name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            工具执行结果
        
        Raises:
            ToolNotFoundError: 工具不存在
            ToolExecutionError: 工具执行失败
        """
        tool = self.get_tool(name)
        if not tool:
            raise ToolNotFoundError(f"工具 '{name}' 未找到", agent_name=self.name)
        
        logger.debug(f"[{self.name}] 调用工具: {name}, args={args}, kwargs={kwargs}")
        
        last_error = None  # 记录多次重试下的最后一个错误，用于异常抛出
        for attempt in range(self._max_retries):
            try:
                result = await tool.ainvoke(*args, **kwargs)  # 异步调用工具
                
                if self._state.get("tools_output") is None:
                    self._state["tools_output"] = {}
                self._state["tools_output"][name] = result
                
                logger.debug(f"[{self.name}] 工具调用成功: {name}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.name}] 工具调用失败 (尝试 {attempt + 1}/{self._max_retries}): "
                    f"{name}, 错误: {str(e)}"
                )
        
        raise ToolExecutionError(
            f"工具 '{name}' 执行失败，已重试 {self._max_retries} 次",
            agent_name=self.name,
            original_error=last_error
        )
    
    def invoke_tool_sync(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        """同步调用工具
        
        使用同步方式调用指定工具，支持重试机制。
        
        Args:
            name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            工具执行结果
        
        Raises:
            ToolNotFoundError: 工具不存在
            ToolExecutionError: 工具执行失败
        """
        tool = self.get_tool(name)
        if not tool:
            raise ToolNotFoundError(
                f"工具 '{name}' 未找到",
                agent_name=self.name
            )
        
        logger.debug(f"[{self.name}] 同步调用工具: {name}, args={args}, kwargs={kwargs}")
        
        last_error = None
        for attempt in range(self._max_retries):
            try:
                result = tool.invoke(*args, **kwargs)
                
                if self._state.get("tools_output") is None:
                    self._state["tools_output"] = {}
                self._state["tools_output"][name] = result
                
                logger.debug(f"[{self.name}] 工具调用成功: {name}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.name}] 工具调用失败 (尝试 {attempt + 1}/{self._max_retries}): "
                    f"{name}, 错误: {str(e)}"
                )
        
        raise ToolExecutionError(
            f"工具 '{name}' 执行失败，已重试 {self._max_retries} 次",
            agent_name=self.name,
            original_error=last_error
        )
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息到消息历史
        
        Args:
            message: 消息实例（BaseMessage 子类）
        """
        if self._state.get("messages") is None:
            self._state["messages"] = []
        self._state["messages"].append(message)

        message_view = f"content='{message.content[:50]}...', " if len(str(message.content)) > 50 else f"content='{message.content}', "
        logger.debug(
            f"[{self.name}] 添加消息: type={type(message).__name__}, "
            f"{message_view}"  # 预览前50个字符
            f"content_length={len(str(message.content))}" 
        )
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息
        
        系统消息通常用于设定智能体的角色和行为规范。
        
        Args:
            content: 消息内容
        """
        self.add_message(SystemMessage(content=content))
    
    def add_human_message(self, content: str) -> None:
        """添加用户消息
        
        Args:
            content: 消息内容
        """
        self.add_message(HumanMessage(content=content))
    
    def add_ai_message(self, content: str) -> None:
        """添加 AI 消息
        
        Args:
            content: 消息内容
        """
        self.add_message(AIMessage(content=content))
    
    def add_tool_message(self, content: str, tool_call_id: str) -> None:
        """添加工具消息
        
        工具消息用于记录工具调用的返回结果。
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID（与 LLM 的 tool_call 关联）
        """
        self.add_message(ToolMessage(content=content, tool_call_id=tool_call_id))

    def get_messages(self, include_system: bool = True) -> List[BaseMessage]:
        """获取消息历史
        
        Args:
            include_system: 是否包含系统消息
        
        Returns:
            消息列表
        """
        messages = self._state.get("messages", [])
        if not include_system:
            return [m for m in messages if not isinstance(m, SystemMessage)]
        return messages
    
    def get_last_message(self) -> Optional[BaseMessage]:
        """获取最后一条消息
        
        Returns:
            最后一条消息或 None（如果消息历史为空）
        """
        messages = self._state.get("messages", [])
        return messages[-1] if messages else None
    
    def clear_messages(self) -> None:
        """清空消息历史"""
        self._state["messages"] = []
        logger.debug(f"[{self.name}] 消息历史已清空")
    
    def set_error(self, error: str, exception: Optional[Exception] = None) -> None:
        """设置错误信息
        
        记录错误信息并将状态设置为 FAILED。
        
        Args:
            error: 错误描述
            exception: 原始异常（可选）
        """
        self._state["error"] = error
        self._state["status"] = AgentStatus.FAILED
        
        if exception:
            logger.error(f"[{self.name}] 发生错误: {error}", exc_info=exception)
        else:
            logger.error(f"[{self.name}] 发生错误: {error}")
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文信息
        
        上下文用于在智能体执行过程中存储和传递临时数据。
        
        Args:
            key: 键名
            value: 值（可以是任意类型）
        """
        if self._state.get("context") is None:
            self._state["context"] = {}
        self._state["context"][key] = value
        logger.debug(f"[{self.name}] 设置上下文: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息
        
        Args:
            key: 键名
            default: 默认值（键不存在时返回）
        
        Returns:
            上下文值或默认值
        """
        context = self._state.get("context", {})
        return context.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        元数据用于存储任务相关的标识信息，如任务ID、用户ID等。
        
        Args:
            key: 键名
            value: 值
        """
        if self._state.get("metadata") is None:
            self._state["metadata"] = {}
        self._state["metadata"][key] = value
        logger.debug(f"[{self.name}] 设置元数据: {key}:{value}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键名
            default: 默认值
        
        Returns:
            元数据值或默认值
        """
        metadata = self._state.get("metadata", {})
        return metadata.get(key, default)
    
    def prepare_messages_for_llm(self) -> List[BaseMessage]:
        """准备发送给 LLM 的消息列表
        
        确保系统提示词在消息列表开头，并合并现有消息历史。
        
        Returns:
            准备好的消息列表，可直接传递给 LLM
        """
        messages = []
        
        if self._system_prompt:
            messages.append(SystemMessage(content=self._system_prompt))
        
        existing_messages = self._state.get("messages", [])
        messages.extend(existing_messages)
        
        messages_view = f'{messages[:10]}' if len(messages) > 10 else messages
        
        logger.debug(
            f"[{self.name}] 准备 LLM 消息: messages={messages_view}, "
            f"with_system={bool(self._system_prompt)}"
        )
        
        return messages
    
    def get_states_summary(self) -> Dict[str, Any]:
        """获取智能体状态摘要
        
        返回智能体的关键状态信息，用于日志记录和调试。
        
        Returns:
            状态摘要字典
        """
        return {
            "name": self.name,
            "status": self._state.get("status"),
            "message_count": len(self._state.get("messages", [])),
            "tool_count": len(self._tools),
            "has_error": bool(self._state.get("error")),
            "current_task": self._state.get("current_task", "")[:50] + "..."
            if len(self._state.get("current_task", "")) > 50
            else self._state.get("current_task", "")
        }
    
    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """执行智能体主逻辑（子类必须实现）
        
        这是智能体的核心执行方法，在 LangGraph 工作流中作为节点函数被调用。
        子类应该实现具体的业务逻辑，并确保正确处理状态更新和异常。
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        
        Example:
            >>> async def run(self, state: AgentState) -> AgentState:
            ...     state["status"] = AgentStatus.RUNNING
            ...     try:
            ...         # 执行具体逻辑
            ...         result = await self.invoke_tool("search", query="test")
            ...         state["context"]["result"] = result
            ...         state["status"] = AgentStatus.COMPLETED
            ...     except Exception as e:
            ...         state["error"] = str(e)
            ...         state["status"] = AgentStatus.FAILED
            ...     return state
        """
        pass
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"tools={self.tool_names}, "
            f"status={self._state.get('status')})"
        )
    
    def __str__(self) -> str:
        return f"[{self.name}] {self.description}"