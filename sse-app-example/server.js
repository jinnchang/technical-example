// SSE（Server-Sent Events）应用示例：实时构建进度推送。
//
// 用 Node 内置 `http` 模块实现一个零第三方依赖的 SSE 服务器，
// 在一条 HTTP 长连接上向所有已连接的浏览器单向推送「构建任务」进度。
//
// SSE 的全部要点都原样写在下面的代码里：
//   1. 响应头（Content-Type: text/event-stream 等）——见 handleEvents()
//   2. 事件帧格式（id: / event: / data: 行，空行分隔）——见 formatFrame()
//
// 客户端是浏览器原生 EventSource（见 index.html），自动处理重连、
// 并在重连时带上 Last-Event-ID 请求头，配合本服务器的 history 完成断点续传。

const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 8000;

// 最近已发送的事件（含 id），用于响应 Last-Event-ID 断点续传的回放。
const history = [];
const HISTORY_LIMIT = 100;
let nextId = 0;

// 当前所有已连接的客户端 response。SSE 是「一对多广播」：一份 feed，所有人共享。
const clients = new Set();

// 把一条事件按 SSE 帧格式序列化：每帧若干 id:/event:/data: 行，帧之间以空行分隔。
function formatFrame(ev) {
  const lines = [`id: ${ev.id}`];
  if (ev.event) lines.push(`event: ${ev.event}`);
  for (const line of ev.data.split("\n")) lines.push(`data: ${line}`);
  return lines.join("\n") + "\n\n";
}

// 广播一条事件：编号 → 写入每个已连接客户端 → 记入 history 供后续回放。
// event 传 null 时不写 event: 行，即浏览器 EventSource 的默认 message 事件。
function broadcast(event, data) {
  const ev = { id: ++nextId, event: event || null, data: String(data) };
  const payload = formatFrame(ev);
  for (const res of clients) {
    if (!res.destroyed) res.write(payload);
  }
  history.push(ev);
  if (history.length > HISTORY_LIMIT) history.shift();
  console.log(`[broadcast] #${ev.id} ${ev.event || "message"} :: ${ev.data}`);
}

// 模拟「构建任务」：每个周期推进 25%，在 0% 发 notice、100% 发默认 message 事件。
// 三类事件（notice / progress / 默认 message）复用同一条连接，是 SSE 的典型用法。
let round = 1;
let percent = 0;
function tick() {
  if (percent === 0) broadcast("notice", `第 ${round} 次构建开始`);
  percent += 25;
  broadcast("progress", `${percent}`);
  if (percent === 100) {
    broadcast(null, `第 ${round} 次构建完成，产物已发布`);
    percent = 0;
    round += 1;
  }
}

function handleEvents(req, res) {
  // 这几个响应头是「单向长连接」成立的关键，尤其是 Content-Type。
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  // retry: 告诉客户端重连间隔（毫秒）；":" 开头是注释/心跳行，浏览器会忽略。
  res.write("retry: 3000\n");
  res.write(": 连接建立\n\n");

  // 断点续传：客户端重连时会带上 Last-Event-ID，回放它之后的所有事件。
  const lastId = Number(req.headers["last-event-id"]);
  if (Number.isInteger(lastId)) {
    for (const ev of history) {
      if (ev.id > lastId) res.write(formatFrame(ev));
    }
  }

  clients.add(res);
  req.on("close", () => clients.delete(res));
}

function serveIndex(res) {
  const html = fs.readFileSync(path.join(__dirname, "index.html"));
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(html);
}

const server = http.createServer((req, res) => {
  const { pathname } = new URL(req.url, `http://localhost:${PORT}`);
  if (pathname === "/events") handleEvents(req, res);
  else if (pathname === "/") serveIndex(res);
  else {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("not found");
  }
});

server.listen(PORT, () => {
  console.log(`SSE 服务器已启动：http://localhost:${PORT}/`);
  console.log(`事件流地址：http://localhost:${PORT}/events`);
});

// 无论有无客户端连接都持续推进，保证新客户端一接入就能看到新鲜事件。
setInterval(tick, 600);