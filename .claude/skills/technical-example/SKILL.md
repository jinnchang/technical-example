---
name: technical-example
description: Generate self-contained, runnable tech example projects that teach a single technology — application examples ("how to use X") or principle examples ("how X works under the hood"). Use this skill whenever the user mentions a technology together with words like example, demo, demonstrate, show me, walk through, verify, principle, mechanism, internals, how it works, or how to use — including Chinese phrasings like 例子、示例、演示、写个demo、原理、机制、怎么实现的、原理是什么、给我一个…的例子. Also use it when the user wants to understand a technology through runnable code, or asks to add an example/demo to a repo. Do not use it for pure explanation questions with no code requested.
---

# Tech Example Generation

You are generating a small, self-contained example that teaches one technology. The example's only job is to make that technology easy to understand and easy to run — anything that doesn't serve that goal (extra business logic, boilerplate frameworks, over-abstraction) hurts it.

Two rules shape everything else:

1. **Plan before code.** Present the scenario, step breakdown, and decision points to the user, and wait for their confirmation. Users ask for examples to *learn* — an example that misses what they wanted to learn wastes their time, and the plan is where that gets caught cheaply.
2. **Verified, or not done.** Run what you generate. An example that doesn't run teaches nothing and erodes trust in every other example in the workspace.

## Language

- Communicate with the user in Chinese throughout the process (analysis, plan, decision points, confirmation).
- README content is written in Chinese.
- Code, identifiers, and file names stay in English.

## Two Example Types

First, classify the request. The trigger words in the user's message usually make this obvious:

| Aspect                | Application example                                                 | Principle example                                                                     |
| --------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Purpose**           | "How to use it" — application scenarios and workflows                | "What it is" — internal mechanisms and core concepts                                  |
| **Trigger words**     | example, demo, demonstrate, how to use, show me, walk through, verify | principle, mechanism, concept, internals, how it works, why designed this way       |
| **Comment focus**     | Explain what each key step does                                     | Map key steps to the underlying principle concepts                                    |
| **Directory naming**  | `{tech}-app-example` (kebab-case)                                    | `{tech}-principle-example` (kebab-case)                                               |

If the user's phrasing fits neither type clearly, ask which they want — the two types produce noticeably different outputs.

## Workflow

### 1. Understand the Technology

Clarify what the technology is, its core purpose, and its use cases. When the request is ambiguous (e.g., "a Kafka example" could mean producer/consumer usage or partition/replication internals), ask. For technologies you're unsure about, search official documentation before proceeding — an example built on a wrong mental model misleads the user twice: once when they read it, again when they reuse the pattern.

### 2. Choose a Scenario

- **Application example**: pick the application scenario that best exercises the core usage — the scenario a newcomer is most likely to actually build.
- **Principle example**: first lay out the core concepts for the user (technical essence, main components, key mechanisms, how it differs from related technologies), *then* pick a scenario that makes those concepts visible in running code.

### 3. Generate a Plan — No Code Yet

Break the implementation into clear steps, explaining for each: purpose, how it will be implemented, and why it's needed. Where multiple reasonable approaches exist, present the options and recommend one, in this format:

```markdown
### 决策点 1：XXX 的实现方式

选项 1：XXX
选项 2：XXX

基于 XXX 的考虑，推荐选项 1。
```

Writing code before the user has seen the plan defeats the purpose of the plan. Resist the pull to "just start" — even when the design seems obvious to you.

### 4. Wait for User Confirmation

Present: chosen scenario, step breakdown, recommended approaches, and anything needing the user's call. Then stop and end with exactly:

> 以上方案是否符合你的需求？如有异议请指出，否则将按推荐方案生成代码。

Handle the reply like this:

- **Confirmed** → proceed to step 5.
- **Partially confirmed** → proceed with what was confirmed; use your recommended option for anything unconfirmed. Don't stall waiting for answers you already offered recommendations on.
- **Rejected** → back to step 2 to re-select the scenario.

### 5. Generate Code and README

After confirmation, create the example directory under the current working directory and generate complete, runnable code with a sibling `README.md`:

```
{tech}-app-example/
├── README.md
└── main        (or server + client, or a single file — see below)
```

If you hit an obstacle that blocks implementation (missing runtime, dependency conflict, API unavailable), stop and explain the blocker instead of shipping something that can't run.

### 6. Verify Execution

Run the code and confirm it executes without errors. For server-based examples, start the server and make a test request. Fix issues before reporting completion — an example you haven't run is an example you can't vouch for. Shut down anything you started (servers, watchers) before reporting completion.

## Language & Environment

Choose the language the technology is dominant in (React/Vue → TypeScript, Node.js → JavaScript, Flask/asyncio → Python); default to Python when there's no clear preference.

Before generating code:

- **Verify the runtime exists** (`python3 --version`, `node --version`, …). If it's missing, tell the user what to install instead of generating code that cannot run.
- **Follow the project's existing environment conventions.** Detect the Node package manager from lockfiles (`pnpm-lock.yaml` → pnpm, `package-lock.json` → npm, `yarn.lock` → yarn); use a virtualenv if the project has one. When the project has no established convention, use the language's standard default and say so in the README. Silently installing packages into someone's project with the wrong tool is how examples earn a bad reputation.
- **Never hardcode API keys or endpoints.** If the example calls an external API (e.g., an LLM), read credentials from environment variables and fail at startup with a clear message telling the user which variables to set.

## Files & Dependencies

- Keep each file under ~200 lines, focused on the technology itself.
- Introduce only necessary libraries. Common minimal choices: HTTP service → `flask` (Python) / `express` (Node.js); HTTP requests → `requests` (Python) / built-in `fetch` (Node.js).
- File organization follows the shape of the example: pure algorithm / utility → a single file; HTTP interaction → separate server and client files; multi-role interaction → add a config file.
- Do not modify files outside the example directory.
- README lives alongside the code.

## Code Quality

- Use semantic variable names in the language's own convention — not `do_thing`.
- Catch only exceptions expected in normal use (network timeout, file not found); let unexpected errors surface naturally so they're visible when something is actually wrong.
- Keep input/output concise: show the core logic, not log noise.
- All code must be executable — no placeholders, TODOs, or stubbed functions.
- Comments: module-level explains the example's purpose; key steps explain intent (application example) or map to the underlying principle (principle example); inline comments only for genuinely complex logic.
- Print/output at key points so the execution flow and important decisions are visible when the example runs — an example whose output is silent teaches nothing about what it did.
- Avoid over-abstraction. Three similar lines beat a premature function; the reader is here to see the technology plainly.
- Principle example code serves the principle, not completeness — it's fine to simplify as long as the simplification itself is commented.

## README Structure

Write in Chinese, following the structure for the example type.

**Application example:**

| Section       | Content                                            |
| ------------- | -------------------------------------------------- |
| `## Scenario` | Brief description of the scenario being shown       |
| `## Setup`    | Dependency install commands (in a code block)     |
| `## Run`      | Numbered steps to run                              |

**Principle example:**

| Section             | Content                                            |
| ------------------- | -------------------------------------------------- |
| `## Core Concepts`  | 1–2 sentences on the technical essence              |
| `## Key Mechanisms` | Brief explanation of the core process principles    |
| `## Scenario`       | Brief description of the scenario being shown       |
| `## Setup`          | Dependency install commands (in a code block)      |
| `## Run`            | Numbered steps to run                              |

## Self-Check

Before reporting completion, verify:

- [ ] Only required files generated, no extra files
- [ ] No placeholders, TODOs, or unfinished functions
- [ ] Core flow is executable (and was actually executed — step 6)
- [ ] Comments mark the purpose/principle of key steps
- [ ] Key flows have print/output statements showing execution flow and decisions
- [ ] README conforms to the structure requirements above