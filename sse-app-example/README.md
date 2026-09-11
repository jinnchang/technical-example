# SSE 应用示例：实时构建进度推送

一个最小可运行的 **SSE（Server-Sent Events）** 示例——服务器用 Node 内置 `http` 模块（零第三方依赖）在一条 HTTP 长连接上推送「构建任务」的实时进度，浏览器用原生 `EventSource` 接收并渲染。

## 场景

我们要做一个「构建任务实时进度」看板：服务器模拟一次次构建，每完成一步就向所有已连接的客户端**单向推送**进度。示例在一条连接上推送三类事件，正好覆盖 SSE 的核心用法：

1. **命名事件 `notice`**（阶段通知）：`第 N 次构建开始`；
2. **命名事件 `progress`**（进度百分比）：`25` → `50` → `75` → `100`；
3. **默认 `message` 事件**（帧里没有 `event:` 行，作用于 `onmessage`）：`第 N 次构建完成`。

每一帧都带递增的 `id`，用于演示 SSE 的**断点续传**：客户端重连时自动携带 `Last-Event-ID`，服务器据此回放漏掉的事件。此外，浏览器 `EventSource` 断线后会自动重连，与「手动轮询」相比这正是 SSE 的核心卖点。

> SSE 的本质就两件事，在代码里都原样可读：**响应头**（`Content-Type: text/event-stream` 等，见 `server.js` 的 `handleEvents()`）加**事件帧格式**（`id:`/`event:`/`data:` 行、空行分隔，见 `formatFrame()`）。不要被「推流」吓到，它只是 HTTP 长连接 + 文本帧格式。

## 安装

无需安装任何依赖：服务器用 Node 内置 `http` 模块，客户端用浏览器原生 `EventSource`。只需要 Node（≥ v18 即可）：

```bash
node --version
```

## 运行

从 `sse-app-example` 目录执行：

1. 启动服务器：

```bash
node server.js
```

2. 在浏览器打开 <http://localhost:8000/>，看到进度条滚动、事件日志逐条追加即成功。

3. 用 `curl` 在终端验收**原始事件帧**（`-N` 关闭缓冲，逐行打印；`Ctrl+C` 退出）：

```bash
curl -N http://localhost:8000/events
```

观察输出里的 `id:`、`event:`、`data:` 行、空行分隔，以及前面的 `retry:`、`: 连接建立` 两行。

4. 演示**断点续传**：带上 `Last-Event-ID` 请求头，服务器会先回放该 id 之后的历史事件，再续上实时事件：

```bash
curl -N -H "Last-Event-ID: 5" http://localhost:8000/events
```

5. 演示**自动重连**：`Ctrl+C` 停掉服务器，隔几秒再 `node server.js` 重启，浏览器页面会自动重连并显示「已连接」。

## 文件结构

```
sse-app-example/
├── README.md
├── server.js    # 零依赖 SSE 服务器：内置 http 模块，手写响应头与事件帧
└── index.html   # 浏览器 EventSource 客户端：监听默认/命名事件并渲染
```