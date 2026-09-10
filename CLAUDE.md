# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of small, self-contained, runnable examples — each directory teaches a single technology. Every example is a complete teaching unit: code plus a sibling `README.md` (written in Chinese). Examples are generated and governed by the `technical-example` skill at `.claude/skills/technical-example/SKILL.md` — read it before adding or editing an example.

## Running examples

There is no build system, linter, test suite, or packaging. Running an example means executing its entry point directly, from inside that example's directory. Each README's run section gives the exact command and interpreter path — follow it rather than assuming a language or file name.

All examples share one environment at the repo root; there is no `requirements.txt` or lockfile, and each README lists its own install line, with dependencies accumulating in the shared environment. Treat the language as per-example, not repo-wide — future examples may target other runtimes (e.g. Node.js) with their own runners.

The LLM-using examples require these env vars first and fail with a clear message at startup if any is missing; they accept any OpenAI-compatible endpoint:

```bash
export OPENAI_API_KEY=... OPENAI_MODEL=... OPENAI_BASE_URL=...
```

## Architecture

Each example directory is fully independent — no shared code or cross-imports between examples (they only share the environment). Two example *kinds* exist, distinguished by directory suffix (described in the skill):

- `{tech}-app-example` — "how to use it": application scenario and workflow.
- `{tech}-principle-example` — "how it works": internals and mechanisms.

## Conventions for new or changed examples (from the skill)

- Plan before writing code, and verify the example actually runs (shutting down anything you started, e.g. servers) before reporting done.
- READMEs are written in Chinese; code, identifiers, and file names stay in English.
- Keep files small and focused on the one technology; no placeholders or TODOs; don't modify files outside the example directory.
- Never hardcode API keys or endpoints — read credentials from env vars and fail at startup with a clear message.