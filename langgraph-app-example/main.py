"""LangGraph 1.x 应用示例：手写 StateGraph 搭一个带工具调用与记忆的 ReAct 智能体。

本示例只用 LangGraph 的核心原语（不经过 langchain.agents 的上层封装）：

1. StateGraph + MessagesState：显式定义「状态」与「图」；
2. 节点 model / tools + 一条条件边：model 输出带 tool_calls 时路由到 tools，
   tools 执行完再回到 model，形成「思考 → 调工具 → 再看结果」的循环；
3. MemorySaver 检查点 + thread_id：跨轮次记忆与断点恢复。

运行前需设置环境变量 OPENAI_API_KEY、OPENAI_MODEL（可选 OPENAI_BASE_URL）。
"""

import os

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph


# ---------------------------------------------------------------------------
# 工具定义：两个无外部依赖的确定性工具，用于演示模型如何自主选择并调用
# ---------------------------------------------------------------------------

@tool
def multiply(a: int, b: int) -> int:
    """计算两个整数的乘积。例如 multiply(37, 58) 返回 2146。"""
    return a * b


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。city 为中文城市名。

    示例返回固定假数据，仅用于演示工具调用；真实场景应替换为天气 API。
    """
    weather_db = {"北京": "晴，24°C", "上海": "多云，26°C", "深圳": "阵雨，28°C"}
    return f"{city}：{weather_db.get(city, '暂无数据，请换一个城市')}"


TOOLS = [multiply, get_weather]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}  # 供 tools 节点按名字路由到具体工具

SYSTEM_PROMPT = "你是一个乐于助人的助手。遇到乘法计算请用 multiply 工具，遇到天气问题请用 get_weather 工具，然后基于工具结果回答。"


# ---------------------------------------------------------------------------
# 图：两个节点 + 一条条件边
# ---------------------------------------------------------------------------

def should_continue(state):
    """条件路由函数：读最后一条消息，决定下一步回 tools 还是结束。

    返回 "tools"（继续调用工具）或 END（结束，语言层面的 END 即 "__end__"）。
    """
    last = state["messages"][-1]
    return "tools" if last.tool_calls else END


def tool_node(state):
    """'tools' 节点：执行上一条 AI 消息里的工具调用，把结果写成 ToolMessage 回填到状态。"""
    results = []
    for call in state["messages"][-1].tool_calls:
        tool_fn = TOOLS_BY_NAME[call["name"]]
        results.append(
            ToolMessage(
                content=str(tool_fn.invoke(call["args"])),
                name=call["name"],
                tool_call_id=call["id"],
            )
        )
    return {"messages": results}


def build_agent():
    """用 StateGraph 手写 ReAct 图：model 与 tools 两个节点循环，直到 model 不再调工具。"""
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_MODEL"):
        raise SystemExit(
            "缺少必要的环境变量（OPENAI_API_KEY / OPENAI_MODEL），无法调用 LLM。请设置后重试：\n"
            "  export OPENAI_API_KEY=<你的密钥>\n"
            "  export OPENAI_MODEL=<模型名>\n"
            "  export OPENAI_BASE_URL=<OpenAI 兼容端点，可选>\n"
            "说明：任何 OpenAI 兼容的 LLM（OpenAI / DeepSeek / Kimi / GLM / Qwen …）都能用。"
        )

    model = ChatOpenAI(
        model=os.environ["OPENAI_MODEL"],
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model_with_tools = model.bind_tools(TOOLS)  # 绑定工具：模型会返回带 tool_calls 的 AIMessage

    def call_model(state):
        """'model' 节点：调用 LLM。需要工具时返回 tool_calls，否则返回最终文本回答。"""
        return {"messages": [model_with_tools.invoke(state["messages"])]}

    builder = StateGraph(MessagesState)  # MessagesState：消息列表状态，自动用 add_messages 累加
    builder.add_node("model", call_model)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "model")  # 入口直接进 model 节点
    builder.add_conditional_edges(
        "model",
        should_continue,
        {"tools": "tools", END: END},  # 返回 "tools" → 去 tools 节点；返回 END → 结束
    )
    builder.add_edge("tools", "model")  # tools 执行完回到 model，形成循环

    checkpointer = MemorySaver()  # 会话状态按 thread_id 持久化到内存
    return builder.compile(checkpointer=checkpointer)


def print_trace(messages):
    """按顺序打印一轮对话中每个角色的动作，让「决策 → 工具调用 → 结果」循环可见。"""
    for msg in messages:
        if msg.type == "human":
            print(f"[用户]   {msg.content}")
        elif msg.type == "ai":
            for call in getattr(msg, "tool_calls", []) or []:
                print(f"[决策]   调用工具 {call['name']}({call['args']})")
            if msg.content:
                print(f"[助手]   {msg.content}")
        elif msg.type == "tool":
            print(f"[工具结果] {msg.content}")


def main():
    graph = build_agent()

    print("=== 手写 StateGraph 的图结构 ===")
    try:
        print(graph.get_graph().draw_ascii())
    except ImportError:
        print("（未安装 grandalf，跳过图绘制：pip install grandalf 后可打印图）")

    # 同一个 thread_id 让多轮对话共享同一份会话状态，从而实现「记忆」
    config = {"configurable": {"thread_id": "demo-1"}}

    turns = [
        "先查一下深圳的天气，再帮我算 37 × 58 等于多少。",
        "把刚才算出来的结果再乘 100 是多少？",
    ]

    for i, question in enumerate(turns, 1):
        print(f"\n=== 第 {i} 轮 ===")
        messages = [("user", question)]
        if i == 1:
            # 系统提示词只在第一轮注入一次，之后靠 checkpointer 记住
            messages.insert(0, ("system", SYSTEM_PROMPT))
        result = graph.invoke({"messages": messages}, config=config)
        print_trace(result["messages"])


if __name__ == "__main__":
    main()