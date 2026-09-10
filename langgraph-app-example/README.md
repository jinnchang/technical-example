# LangGraph 应用示例：手写 StateGraph 的带工具调用与记忆智能体

一个最小可运行的**纯 LangGraph** 1.x 示例——不经过 `langchain.agents` 上层封装，直接用 `StateGraph` 手写图，搭出一个能调用工具、并记住多轮上下文的 ReAct 智能体。

## 场景

我们要做一个「小助手」：它自主决定调用哪个工具来回答问题——

- `multiply`：两个整数相乘；
- `get_weather`：查询城市天气（示例返回固定数据，仅为演示工具调用）。

示例重点演示 LangGraph 的三个核心原语：

1. **状态（State）**：`MessagesState`——所有消息都在一个「消息列表」里流转，节点往里追加、条件函数从里面读取；
2. **节点与边（Node / Edge）**：两个节点 `model`（调 LLM）和 `tools`（执行工具），条件边根据「上一条 AI 消息是否含 `tool_calls`」决定回 `tools` 还是结束；
3. **检查点（Checkpoint）**：`MemorySaver` + `thread_id`，跨轮次记忆与断点恢复。

模型层用 LangChain 的 `ChatOpenAI`，任何 OpenAI 兼容的 LLM 都能直接替换（OpenAI / DeepSeek / Kimi / GLM / Qwen 等），不动图本身。

## 安装

> 本仓库所有示例共用**仓库根目录**的统一环境。

在**仓库根目录**创建并安装（本示例只需 `langgraph`、`langchain-openai`、`grandalf`）：

```bash
python3 -m venv .venv        # 若已存在则跳过
source .venv/bin/activate
pip install langgraph langchain-openai grandalf
```

根目录 `.venv` 已存在时可直接跳到「运行」。

## 运行

1. 设置环境变量：

```bash
export OPENAI_API_KEY=<你的密钥>
export OPENAI_MODEL=<模型名>
export OPENAI_BASE_URL=<OpenAI 兼容端点>
```

缺少 `OPENAI_API_KEY`、`OPENAI_MODEL` 或 `OPENAI_BASE_URL` 中任意一个时，程序会在启动时给出清晰的错误提示并退出。

2. 运行：

```bash
../.venv/bin/python main.py   # 从示例目录运行，使用仓库根目录的统一 venv
```

3. 观察输出：程序先打印你亲手搭的图 `__start__ → model → tools(可选) → model → __end__`；第一轮模型并行调用 `get_weather` 和 `multiply` 两个工具后作答；第二轮仅凭 `thread_id` 记忆回忆上一轮算出的 2146，算出 214600。

## 文件结构

```
langgraph-app-example/
├── README.md
└── main.py        # 工具定义 + 手写 StateGraph + 多轮运行
```