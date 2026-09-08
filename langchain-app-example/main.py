"""LangChain 1.x 应用示例：用 LCEL 搭一条「影评分析」链，产出结构化结果。

本示例聚焦 langchain 包区别于 LangGraph（编排层）的「组件层」能力：

1. ChatPromptTemplate：把角色与输入占位符组织成消息模板；
2. LCEL（| 算子）：把「提示词 → 模型 → 解析」串成一条 Runnable 链；
3. with_structured_output + Pydantic：让模型直接返回类型化对象，而非纯文本；
4. Runnable 接口：同一条链既能 invoke（单条）、batch（批量），也能 stream（流式）。

运行前需设置环境变量 OPENAI_API_KEY、OPENAI_MODEL、OPENAI_BASE_URL。
"""

import os
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 结构化输出模型：告诉模型「按这个形状回答」，而不是自由发挥
# ---------------------------------------------------------------------------

class ReviewAnalysis(BaseModel):
    """对一条电影短评的结构化分析结果。"""

    sentiment: Literal["正面", "负面", "中性"] = Field(description="整体评价倾向")
    summary: str = Field(description="一句话概括评论核心观点")
    keywords: list[str] = Field(description="最能代表这条评论的 2~4 个关键词")
    score: int = Field(ge=1, le=5, description="按评论语气推断的 1~5 星评分")


SYSTEM_PROMPT = (
    "你是专业的影评分析助手。对用户给出的电影短评做结构化分析："
    "判断情感倾向（正面/负面/中性）、概括一句话摘要、提炼 2~4 个关键词、并推断 1~5 星评分。"
)

# 提示词模板：human 消息里的 {review} 是运行时才填的占位符
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "请分析这条电影短评：\n{review}"),
    ]
)


def build_model():
    """从环境变量读取配置并实例化 ChatOpenAI；缺少任一变量直接报错退出。"""
    required = ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            f"缺少必要的环境变量（{', '.join(missing)}），无法调用 LLM。请设置后重试：\n"
            "  export OPENAI_API_KEY=<你的密钥>\n"
            "  export OPENAI_MODEL=<模型名>\n"
            "  export OPENAI_BASE_URL=<OpenAI 兼容端点>\n"
            "说明：任何 OpenAI 兼容的 LLM（OpenAI / DeepSeek / Kimi / GLM / Qwen …）都能用。"
        )
    return ChatOpenAI(
        model=os.environ["OPENAI_MODEL"],
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )


def main():
    model = build_model()

    # LCEL 链 1：产出结构化对象 —— 用于 invoke / batch
    analysis_chain = prompt | model.with_structured_output(ReviewAnalysis)

    # LCEL 链 2：产出纯文本 —— 用于演示流式逐字输出（StrOutputParser 只取 message 的正文）
    stream_chain = prompt | model | StrOutputParser()

    reviews = {
        "正面": "特效炸裂，笑点密集，演员演技在线，绝对值回票价！",
        "负面": "剧情稀烂，节奏拖沓，看得我昏昏欲睡，散场只想退钱。",
        "中性": "中规中矩的续作，没有惊喜但也不难看，打发时间可以。",
    }

    print("=== 1) invoke：分析单条评论（返回类型化对象）===")
    result = analysis_chain.invoke({"review": reviews["正面"]})
    print(f"类型: {type(result).__name__}")
    print(result)

    print("\n=== 2) batch：批量分析三条评论 ===")
    results = analysis_chain.batch([{"review": r} for r in reviews.values()])
    for label, item in zip(reviews, results):
        print(f"[{label}] {item.sentiment}  {item.score} 星  |  {item.summary}  |  关键词: {'、'.join(item.keywords)}")

    print("\n=== 3) stream：流式输出文本（逐 token 打印）===")
    for chunk in stream_chain.stream({"review": reviews["负面"]}):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()