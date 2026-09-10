# MCP 应用示例：本地笔记服务（工具 + 资源）

一个最小可运行的 **MCP（Model Context Protocol）** server 示例——把「本地记笔记」包装成 MCP 能力，再用一个最小客户端跑通「发现工具 → 调用工具 → 读取资源」的完整回路。

## 场景

我们要做一个「本地笔记服务」：把「记笔记」这个本地动作暴露给任何 MCP 客户端（Claude Code / Cursor 等），让它们无需专门适配即可读写笔记。

示例重点演示 MCP 的两类核心能力：

1. **工具（Tools）**：`add_note` / `list_notes`——可执行、有副作用的动作（写入、读取笔记），笔记持久化到本地 `notes.json`；
2. **资源（Resources）**：`notes://all`——把全部笔记作为只读数据暴露给客户端读取。

`client.py` 扮演「任意一个 MCP 客户端」的角色，用官方 SDK 连上 server，演示标准交互流程：`initialize` 握手 → `list_tools` / `list_resources` 发现能力 → `call_tool` 调用工具 → `read_resource` 读取资源。

> MCP 的核心价值：server 只需实现一次该协议，任何客户端就能用统一方式接入，无需为每个客户端各写一套接口。

## 安装

> 本仓库所有示例共用**仓库根目录**的统一环境。

在**仓库根目录**创建并安装（本示例只需 `mcp[cli]`，其中 `[cli]` 附带 `mcp` 命令行工具）：

```bash
python3 -m venv .venv        # 若已存在则跳过
source .venv/bin/activate
pip install "mcp[cli]"
```

根目录 `.venv` 已存在时可直接跳到「运行」。

## 运行

从 `mcp-app-example` 目录执行：

```bash
../.venv/bin/python client.py   # client 会内部拉起 server.py 子进程
```

观察输出，依次是：

1. 握手后打印**工具列表**（`add_note` / `list_notes` 及其描述）与**资源列表**（`notes://all`）；
2. `call_tool("add_note", …)` 写入一条笔记，`call_tool("list_notes", …)` 读回标题；
3. `read_resource("notes://all")` 打印全部笔记的 JSON 内容。

运行结束后，示例目录下的 `notes.json` 里就存着刚写入的笔记；这里 `[server]` 开头的日志来自 server 进程的 stderr，正好验证了「stdio 服务器不能写 stdout」这一点。

## 在其它 Agent 中使用

上面的 `client.py` 只是「教学用」的最小客户端。真实场景下，写好的 `server.py` 会被接入主流 Agent——它们都遵循 MCP 的 stdio 配置约定：给一个启动命令 + 参数，agent 负责启动进程并以 JSON-RPC 通信。

以 **Claude Code** 为例，推荐写进项目根的 `.mcp.json`（随仓库走、团队共享）：

```json
{
  "mcpServers": {
    "notes": {
      "command": "<仓库绝对路径>/.venv/bin/python",
      "args": ["<仓库绝对路径>/mcp-app-example/server.py"]
    }
  }
}
```

或者用一条命令添加（写入用户级配置）：

```bash
claude mcp add notes -- <仓库绝对路径>/.venv/bin/python <仓库绝对路径>/mcp-app-example/server.py
```

其它 Agent 接入方式大同小异（配置格式略有差别，但都是「command + args」这一 stdio 约定）。

> 注意：`command` / `args` 必须写**绝对路径**——agent 会从它自己的工作目录启动该进程，相对路径可能找不到 `server.py`。保存后重开对应 Agent 的会话（Claude Code 重开会话），就能在它的工具列表里看到 `add_note`、`list_notes` 并正常调用。

## 文件结构

```
mcp-app-example/
├── README.md
├── server.py     # MCP 服务器：两个工具 + 一个资源，stdio 传输
└── client.py     # 最小 MCP 客户端：连接 server 并跑完完整回路
```