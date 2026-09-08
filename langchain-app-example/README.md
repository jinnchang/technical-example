# LangChain 应用示例：LCEL 链 + 结构化输出

一个最小可运行的 **LangChain 1.x**（当前 1.4.0）示例——用 LCEL（`|` 算子）把「提示词 → 模型 → 解析」串成一条链，对电影短评输出**结构化结果**（Pydantic 对象），并演示 Runnable 的三种调用方式。

> 与仓库里的 `langgraph-app-example` 是**互补的两层**：LangGraph 是编排层（状态、图、循环），LangChain 是组件层（模板、链、解析）。二者共用一个 `langchain-openai` / `langchain-core` 底座，本示例展示后者。

## 场景

我们要做一个「影评分析助手」：输入一条中文电影短评，输出结构化的分析结果（情感倾向 / 一句话摘要 / 关键词 / 1–5 星评分）。

示例重点演示 LangChain 的三个核心能力：

1. **提示词模板**：`ChatPromptTemplate` 用 `{review}` 占位符把运行时输入拼进消息；
2. **LCEL 组合**：`prompt | model | parser` 用 `|` 串成一条 `Runnable` 链，组件可自由替换；
3. **结构化输出**：`.with_structured_output(Pydantic)` 直接返回类型化对象，而非让模型自由发挥、再手动解析 JSON。

模型层用 `ChatOpenAI`，任何 OpenAI 兼容的 LLM 都能直接替换，不动链本身。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install langchain langchain-openai
```

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
.venv/bin/python main.py
```

3. 观察输出：程序依次演示三种调用——`invoke` 分析单条短评并打印类型化对象、`batch` 批量分析三条短评、`stream` 逐 token 流式打印长文本。

> 提示：部分 OpenAI 兼容端点（如火山方舟 coding 计划）对密集连续请求有限流，连续多次运行时偶发短暂的 400 或卡顿属正常现象，稍等约 1 分钟重试即可，与代码无关。

## 文件结构

```
langchain-app-example/
├── README.md
└── main.py        # Pydantic 输出模型 + 提示词模板 + 两条 LCEL 链 + 三种调用演示
```