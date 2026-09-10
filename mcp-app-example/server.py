"""本地笔记服务的 MCP 服务器示例。

把「本地记笔记」这一能力封装成 MCP server，让任何 MCP 客户端
（Claude Code、Cursor 等）都能用统一的协议发现并调用它，
而无需为每个客户端各写一套适配代码。

本服务器暴露 MCP 的两类核心能力：

- 工具（Tools，可执行、有副作用的动作）：add_note / list_notes
- 资源（Resources，只读的数据）：notes://all

关键机制：stdio 传输下，服务器进程的 stdout 被 JSON-RPC 协议独占。
若用 print() 往 stdout 写普通文字，会混进协议报文、直接把通信打挂，
因此服务器的运行日志只能走 stderr（见下方日志配置）。
"""

import json
import logging
import sys
from pathlib import Path

from mcp.server import MCPServer

# 关键：stdio 服务器日志必须写到 stderr，stdout 留给 JSON-RPC 协议。
# 给本模块的 logger 独立挂一个 stderr handler，避免受全局日志配置影响。
log = logging.getLogger("notes-server")
log.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("[server] %(message)s"))
log.addHandler(handler)
log.propagate = False

mcp = MCPServer("notes")

# 笔记持久化文件，与 server.py 同目录
NOTES_PATH = Path(__file__).resolve().parent / "notes.json"


def _load_notes() -> dict[str, str]:
    """读取全部笔记（标题 -> 正文）；文件不存在时返回空字典。"""
    if not NOTES_PATH.exists():
        return {}
    return json.loads(NOTES_PATH.read_text(encoding="utf-8"))


def _save_notes(notes: dict[str, str]) -> None:
    """把全部笔记写回磁盘。"""
    NOTES_PATH.write_text(
        json.dumps(notes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@mcp.tool()
def add_note(title: str, content: str) -> str:
    """新增或覆盖一条笔记。

    Args:
        title: 笔记标题（唯一标识，同名会覆盖旧内容）。
        content: 笔记正文。
    """
    notes = _load_notes()
    notes[title] = content
    _save_notes(notes)
    log.info("写入笔记：%s", title)  # 走向 stderr，不会污染协议
    return f"已保存笔记「{title}」"


@mcp.tool()
def list_notes() -> str:
    """列出当前保存的全部笔记标题。"""
    notes = _load_notes()
    if not notes:
        return "暂无笔记。"
    return "\n".join(f"- {title}" for title in notes)


@mcp.resource("notes://all")
def all_notes() -> str:
    """把全部笔记以 JSON 文本形式暴露为只读资源。"""
    return json.dumps(_load_notes(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")