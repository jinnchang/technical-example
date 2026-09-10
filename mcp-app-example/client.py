"""MCP 客户端示例：连接上面的本地笔记服务，跑完「发现 → 调用 → 读资源」的完整回路。

客户端通过 stdio_client 把 server.py 作为子进程拉起，再用 MCP 标准协议与之
交互。注意：被协议占用的是「服务器进程」的 stdout；本客户端本身不是 stdio
服务器，所以 print 到 stdout 安全无碍。
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "server.py"


async def main() -> None:
    # 用当前解释器（仓库根目录 .venv 里的 python）把 server.py 拉成子进程
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER)])

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            # 握手：客户端与服务端交换协议版本、能力信息
            await session.initialize()
            print("== 已连接 MCP 服务器 ==")

            # 1) 发现工具：能力清单是运行时动态拿到的，客户端无需提前硬编码
            tools = await session.list_tools()
            print("\n[工具列表]")
            for tool in tools.tools:
                print(f"  · {tool.name}: {tool.description}")

            # 2) 发现资源
            resources = await session.list_resources()
            print("\n[资源列表]")
            for res in resources.resources:
                print(f"  · {res.uri}")

            # 3) 调用工具：add_note 写入一条，list_notes 再读回标题
            print("\n[调用 add_note]")
            result = await session.call_tool(
                "add_note",
                {"title": "购物清单", "content": "牛奶、鸡蛋、面包"},
            )
            print("  " + result.content[0].text)

            print("\n[调用 list_notes]")
            result = await session.call_tool("list_notes", {})
            print("  " + result.content[0].text.replace("\n", "\n  "))

            # 4) 读取资源：拿到全部笔记的 JSON 文本，验证工具确实落了盘
            print("\n[读取资源 notes://all]")
            result = await session.read_resource("notes://all")
            print(result.contents[0].text)


if __name__ == "__main__":
    asyncio.run(main())