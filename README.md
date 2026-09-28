<h1 align="center">Sairam Ugge</h1>
<h3 align="center">GenAI &amp; Backend Engineer @Ascendion · Multi-Agent LLM Orchestration · RAG · Event-Driven Backends</h3>
<p align="center">Python · Go · FastAPI · gRPC &nbsp;|&nbsp; Open-Source AI Infrastructure &nbsp;|&nbsp; 📍 Hyderabad, India</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=sairam0424&label=Profile%20views&color=0e75b6&style=flat" alt="Profile views" />
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/sairam0424/sairam0424/output/github-contribution-grid-snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/sairam0424/sairam0424/output/github-contribution-grid-snake.svg" />
  <img alt="GitHub contribution snake" src="https://raw.githubusercontent.com/sairam0424/sairam0424/output/github-contribution-grid-snake.svg" />
</picture>

---

### 🚀 About Me

- 🧠 **GenAI & Backend Engineer @Ascendion** (Jun 2024 – Present) — I build multi-agent LLM systems and event-driven backends that ship to real production traffic.
- 🤖 **Co-built and production-hardened Pensieve**, an AI process-orchestration engine — multi-agent LLM workflows, human-in-the-loop approval gates, real-time streaming, and governed LLM routing across cloud providers. *(2K+ daily users across domains.)*
- 🧩 **AAVA Code (AI coding plugin for VS Code)** — *architected the backend* and re-architected a single-agent prototype into a multi-agent orchestration system (Main-Agent + sub-agent via crewAI flows; 150+ skills, 40+ tools, ~60 commands); also contributed to the VS Code frontend. *(3K+ daily users across 5+ client environments.)*
- 🔁 **Co-built a prompt-driven execution engine** (LLM agent orchestration with RAG + ReAct) — raised first-pass acceptance from 65% to 85% and cut planning from 1.5h to 15min. *(1.5K+ users.)*
- ⚙️ **Owned backend systems end-to-end** (API design, data modeling, event-driven pipelines) — a decoupled Redis Streams + SSE pub/sub replaced client polling, cutting latency to sub-150ms. *(10K+ events/day for 2.5K+ users.)*
- 🎨 Co-built a **GenAI wireframe generator** (PRDs/sketches/prompts → production-ready UI artifacts) and a **prompt-to-React system** (wireframes → modular components + routing); also **led a React → Angular re-architecture** with an SSE-driven real-time backend that cut UI load latency ~30%.
- 🛠️ Open-source builder — author of **[MindForge](https://github.com/sairam0424/MindForge), [trelix](https://github.com/sairam0424/trelix), [Tombstone](https://github.com/sairam0424/Tombstone), Graph-Forge *(private)*, Agent-Forge *(private)*, [ContextOS](https://github.com/sairam0424/ContextOS), [ag-bash](https://github.com/sairam0424/ag-bash) & more** — agent frameworks, code-intelligence engines, production-reliability tooling, and AI-native infrastructure spanning personal projects and the **[kelvran](https://github.com/kelvran)**/**[mcpsmiths](https://github.com/mcpsmiths)** orgs. *(See Featured Projects below.)*
- 🏆 Competitive programmer — **Google Code Jam '23** (AIR 420; 3,687 / 85,000+), **Meta Hacker Cup '22**, **Flipkart GRiD '22** top tier; mentored 250–300 students in DSA.
- 🌱 Currently going deeper on **multi-agent orchestration, RAG, and distributed-systems design**.
- 📫 Reach me at **uggesairam0000@gmail.com** · 📄 [Resume](http://bit.ly/4rTi7s0) · 💼 [LinkedIn](https://linkedin.com/in/sairam0424)

---

### 🧩 Featured Projects

Open-source AI infrastructure I build in the open — agent frameworks, code-intelligence engines, and developer tooling. Commit counts are a build-signal only; each card describes architecture and tech, not adoption.

#### 🧠 Code Intelligence & Engines

| Project | What it is & Tech |
|---------|-------------------|
| **[trelix](https://github.com/sairam0424/trelix)** · `1,453 commits` | Fast, reliable code intelligence — Tree-sitter AST parsing, contextual hybrid search, adaptive query planning, call-graph expansion & LLM synthesis across 20+ languages with zero infra. Ships as a PyPI CLI, a multi-arch Docker image (`ghcr.io/sairam0424/trelix`), MCP/LangChain/LlamaIndex retriever packages, plus a GitHub Action (`trelix-index-action`) for CI-based repo indexing.<br>`Python` · `Tree-sitter` · `BM25` · `CLI` |
| **[gRPC Microservices](https://github.com/sairam0424/gRPC-micro-services)** · `316 commits` — *Order Processing System* | Polyglot event-driven microservices — gRPC internal RPC + REST gateway, **etcd leader election**, **ACID inventory reservations**, a **Saga orchestrator**, metric-based read routing across PostgreSQL replicas, **Debezium/WAL CDC outbox**, Bloom filters, Redis caching, **DLQ + idempotency**, and observability via Envoy L7 (OpenTelemetry/Prometheus/Grafana).<br>`Go` · `Python` · `gRPC` · `PostgreSQL` · `Kafka` · `etcd` |
| **Graph-Forge** · `574 commits` *(private)* | AI-native distributed code-intelligence platform — code modeled as a Neo4j knowledge graph + Chroma semantic embeddings, served by ~19 polyglot microservices over gRPC/REST. Kafka ingestion, Tree-Sitter AST parsing, full OpenTelemetry/Jaeger/Prometheus/Grafana stack via Envoy. RAG over massive codebases.<br>`Go` · `Python` · `gRPC` · `Neo4j` · `Chroma` · `Kafka` · `Next.js` |
| **[ag-bash](https://github.com/sairam0424/ag-bash)** · `510 commits` | AI-native bash interpreter implemented entirely in TypeScript — exposed as the `@ag-bash/bash` shell engine plus an MCP server and an agent terminal bridge. Tree-sitter WASM parser, esbuild (ESM+CJS), WASM runtimes (CPython, QuickJS, SQLite3), and fork-speculation (`bash.fork()`/`bash.speculate()` — parallel speculative execution with copy-on-write branches).<br>`TypeScript` · `WebAssembly` · `MCP` · `Tree-sitter` · `pnpm` |

#### 🛡️ Production Reliability & Delivery

| Project | What it is & Tech |
|---------|-------------------|
| **[Tombstone](https://github.com/sairam0424/Tombstone)** · `974 commits` | Production intelligence layer for feature flags at scale — blast-radius gating, circuit-breaker auto-rollback, Merkle-linked audit log, causal incident correlation ("What Changed?"), and Knight Capital–style tombstoning of stale flags. Polyglot monorepo.<br>`Go` · `Python` · `TypeScript` · `PostgreSQL` · `Redis` |
| **[RateCap](https://github.com/sairam0424/RateCap)** · `347 commits` | Faithful open-source recreation of Stripe's four-tier rate-limiter and load-shedder architecture, built as a hybrid core-engine + sidecar system.<br>`Go` · `API Gateway` · `Distributed Systems` |

#### 🤖 Agent Frameworks & Infrastructure

| Project | What it is & Tech |
|---------|-------------------|
| **[MindForge](https://github.com/sairam0424/MindForge)** · `1,786 commits` | Agentic-intelligence framework for Claude Code — v12.0.0 ships 221 slash commands, 164 specialized subagents, 354 skills, 216 personas, and 35 dynamic workflows, plus hooks, governance, cost-aware model routing, and true wave (parallel) execution. Streaming WebSocket SDK. Ships as `npx mindforge-cc`.<br>`Node.js` · `TypeScript` · `MCP` · `sql.js` |
| **Agent-Forge** · `209 commits` *(private)* | Framework-agnostic, self-improving AI agent infrastructure — a Karpathy-style propose/eval/score/commit-or-revert loop over a mutable markdown agent spec (`AGENT.md`), git-versioned, with an LLM-judge eval harness and held-out validation to guard against overfitting.<br>`Python` · `FastAPI` · `pgvector` · `Celery` · `MCP` · `Docker` |
| **[ContextOS](https://github.com/sairam0424/ContextOS)** · `233 commits` | Intelligence layer for autonomous AI agents — SQLite/vector indexing, multi-agent orchestration, and resilience. Ships as core/CLI/MCP npm packages (`@context-os/*`) plus a spatial dashboard.<br>`TypeScript` · `SQLite` · `vector search` · `MCP` · `React` · `Three.js` |

#### 🏢 Organization Projects — [kelvran](https://github.com/kelvran) & [mcpsmiths](https://github.com/mcpsmiths)

| Project | What it is & Tech |
|---------|-------------------|
| **[kelvran/gateway](https://github.com/kelvran/gateway)** · `700 commits` | Unified AI infrastructure platform — LLM gateway with an embedded multi-layer cache, plus an independently-versioned `evals` subsystem (currently v0.10.1).<br>`Go` |
| **[mcpsmiths/tracehub-mcp](https://github.com/mcpsmiths/tracehub-mcp)** · `185 commits` | MCP server for querying OpenTelemetry traces across multiple observability backends (Jaeger, Tempo, Traceloop, Datadog) for LLM application debugging.<br>`Python` · `MCP` · `OpenTelemetry` |
| **[mcpsmiths/cost-guard-mcp](https://github.com/mcpsmiths/cost-guard-mcp)** · `64 commits` | Pre-flight query cost and result-size guardrails for AI agents across BigQuery, Snowflake, and Databricks.<br>`Python` · `MCP` |

#### 🛠️ Tooling & Lab

| Project | What it is & Tech |
|---------|-------------------|
| **[CommandVault](https://github.com/sairam0424/CommandVault)** · `161 commits` | Universal AI command manager — browse/search/organize slash commands, skills, agents, plugins, rules, and hooks across Claude Code, Cursor, Copilot, Windsurf, and Aider. Indexes 350+ items via a VS Code extension, an 18-command CLI, and a three-tier search engine.<br>`TypeScript` · `VS Code Extension` · `CLI` · `SQLite` |
| **[Inkforge](https://github.com/sairam0424/Inkforge)** · `103 commits` | AI-powered article generation system — notes/topic/code → human-readable Markdown articles, published to Dev.to, Hashnode, Medium & more.<br>`TypeScript` · `Anthropic` · `AWS Bedrock` |
| **[Not-Humans-Lab](https://github.com/sairam0424/not-humans-lab)** | Umbrella docs tying together the Not-Humans-Lab suite: [daily-dose](https://github.com/sairam0424/daily-dose) (`156 commits`, AI-curated tech digest) and [nh-deck](https://github.com/sairam0424/nh-deck) (`58 commits`, Markdown slide-deck CLI), plus nh-skills *(private)*.<br>`TypeScript` · `Astro` · `CLI` |
| **Not-Humans** · `400 commits` *(private)* | Thin root workspace federating independent AI-infra sub-projects (SkillStack, Deep-Research, Agent-Hub, rate-limit-observatory) — polyglot Turborepo/pnpm + Next.js, Python (uv + Temporal + FastAPI), and Go services with a Qdrant vector store.<br>`TypeScript` · `Python` · `Go` · `Temporal` · `Qdrant` |

#### 🌐 Portfolio & Edge Projects

| Project | What it is & Tech |
|---------|-------------------|
| **[anvilry](https://github.com/sairam0424/anvilry)** · `722 commits` | Engineering portfolio with four switchable experiences over one content source — SSG classic site, AI concierge chat (RAG-grounded, AWS Bedrock), WebGL Build Graph, and a keyboard-native developer terminal. Exposes a read-only MCP server.<br>`Next.js 16` · `React 19` · `TypeScript` · `Tailwind v4` · `R3F` |
| **[Thunderboard-Labs](https://github.com/sairam0424/Thunderboard-Labs)** · `38 commits` | On-device TinyML on the Silicon Labs Thunderboard Sense 2 (EFR32MG12, no NPU) — an 85%-accurate IMU gesture recognizer running fully on-chip at ~87.5ms.<br>`Embedded ML` · `Cortex-M4` · `Edge Impulse` |

---

### 🔥 Recent Highlights

- **MindForge v12.0.0** (2026-09-24) — first release cut for real external users; an independent 8-agent security/production audit closed 1 CRITICAL + 4 HIGH findings before the cutover.
- **trelix v3.4.1** (2026-09-27) — closed a CRITICAL symlink-following vulnerability that could leak local secrets to a third-party vision API, alongside shipping new raster-image indexing with LLM vision captioning (v3.4.0).
- **ag-bash** (2026-09-25) — shipped a 9-phase security-hardening backlog to main and reached a fully green cross-platform CI matrix after root-causing deep Windows/macOS path-handling bugs.
- **Tombstone v2.0.1** (2026-09-09) — shipped after live E2E testing against a real Postgres/Kubernetes stack surfaced 10 real production bugs, including severe connection-pooling races.
- **ContextOS (@context-os/core v1.13.2)** — shipped a deliberate breaking change eliminating an unfixable critical CVE (optional embedding peer-dependency) with in-band degradation reporting for MCP agents.
- **kelvran** (2026-09-21 to 09-22) — 5 releases in a week (gateway v0.14.0→v0.14.2, evals v0.10.0→v0.10.1) fixing 2 CRITICAL + a HIGH-severity SSE error-swallowing bug found via back-to-back audits, alongside a live AWS Bedrock production pilot; gateway has since reached v0.15.0.
- **mcpsmiths/cost-guard-mcp** — shipped a third query-cost engine (Databricks, 2026-09-13) and, the next day, closed a CRITICAL secret-redaction bug in a full-repo audit, raising coverage to 98.4%.
- **mcpsmiths/tracehub-mcp v0.5.0** (2026-09-14) — a real end-to-end dry run against a live Jaeger/OTel stack caught a CRITICAL silent-data-loss bug before it reached users; now at v0.12.2.

---

### 📦 Open Source Packages

| Package | Version | Downloads | License | Build |
|---|---|---|---|---|
| [`mindforge-cc`](https://www.npmjs.com/package/mindforge-cc) (npm) | [![npm](https://img.shields.io/npm/v/mindforge-cc.svg)](https://www.npmjs.com/package/mindforge-cc) | [![downloads](https://img.shields.io/npm/dm/mindforge-cc.svg)](https://www.npmjs.com/package/mindforge-cc) | ![license](https://img.shields.io/npm/l/mindforge-cc.svg) | [![CI](https://github.com/sairam0424/MindForge/actions/workflows/mindforge-ci.yml/badge.svg)](https://github.com/sairam0424/MindForge/actions/workflows/mindforge-ci.yml) |
| [`mindforge-mcp-server`](https://www.npmjs.com/package/mindforge-mcp-server) (npm) | [![npm](https://img.shields.io/npm/v/mindforge-mcp-server.svg)](https://www.npmjs.com/package/mindforge-mcp-server) | [![downloads](https://img.shields.io/npm/dm/mindforge-mcp-server.svg)](https://www.npmjs.com/package/mindforge-mcp-server) | ![license](https://img.shields.io/npm/l/mindforge-mcp-server.svg) | *(same pipeline as mindforge-cc)* |
| [`@ag-bash/bash`](https://www.npmjs.com/package/@ag-bash/bash) (npm) | [![npm](https://img.shields.io/npm/v/@ag-bash/bash.svg)](https://www.npmjs.com/package/@ag-bash/bash) | [![downloads](https://img.shields.io/npm/dm/@ag-bash/bash.svg)](https://www.npmjs.com/package/@ag-bash/bash) | ![license](https://img.shields.io/npm/l/@ag-bash/bash.svg) | [![CI](https://github.com/sairam0424/ag-bash/actions/workflows/tests.yml/badge.svg?branch=develop)](https://github.com/sairam0424/ag-bash/actions/workflows/tests.yml) |
| [`@ag-bash/mcp-server`](https://www.npmjs.com/package/@ag-bash/mcp-server) (npm) | [![npm](https://img.shields.io/npm/v/@ag-bash/mcp-server.svg)](https://www.npmjs.com/package/@ag-bash/mcp-server) | [![downloads](https://img.shields.io/npm/dm/@ag-bash/mcp-server.svg)](https://www.npmjs.com/package/@ag-bash/mcp-server) | ![license](https://img.shields.io/npm/l/@ag-bash/mcp-server.svg) | *(same monorepo as @ag-bash/bash)* |
| [`@ag-bash/agent-bridge`](https://www.npmjs.com/package/@ag-bash/agent-bridge) (npm) | [![npm](https://img.shields.io/npm/v/@ag-bash/agent-bridge.svg)](https://www.npmjs.com/package/@ag-bash/agent-bridge) | [![downloads](https://img.shields.io/npm/dm/@ag-bash/agent-bridge.svg)](https://www.npmjs.com/package/@ag-bash/agent-bridge) | ![license](https://img.shields.io/npm/l/@ag-bash/agent-bridge.svg) | *(same monorepo as @ag-bash/bash)* |
| [`@context-os/core`](https://www.npmjs.com/package/@context-os/core) (npm) | [![npm](https://img.shields.io/npm/v/@context-os/core.svg)](https://www.npmjs.com/package/@context-os/core) | [![downloads](https://img.shields.io/npm/dm/@context-os/core.svg)](https://www.npmjs.com/package/@context-os/core) | *(registry `license` field is null — pending fix)* | *(CI omitted — no green run in 10+ attempts across ~11 days; no commits since 2026-09-17)* |
| [`@context-os/cli`](https://www.npmjs.com/package/@context-os/cli) (npm) | [![npm](https://img.shields.io/npm/v/@context-os/cli.svg)](https://www.npmjs.com/package/@context-os/cli) | [![downloads](https://img.shields.io/npm/dm/@context-os/cli.svg)](https://www.npmjs.com/package/@context-os/cli) | *(same registry gap as @context-os/core)* | *(same pipeline as @context-os/core)* |
| [`@context-os/mcp`](https://www.npmjs.com/package/@context-os/mcp) (npm) | [![npm](https://img.shields.io/npm/v/@context-os/mcp.svg)](https://www.npmjs.com/package/@context-os/mcp) | [![downloads](https://img.shields.io/npm/dm/@context-os/mcp.svg)](https://www.npmjs.com/package/@context-os/mcp) | *(same registry gap as @context-os/core)* | *(same pipeline as @context-os/core)* |
| [`trelix`](https://pypi.org/project/trelix/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/trelix.svg)](https://pypi.org/project/trelix/) | [![Downloads](https://static.pepy.tech/badge/trelix)](https://pepy.tech/project/trelix) | ![license](https://img.shields.io/pypi/l/trelix.svg) | [![CI](https://github.com/sairam0424/trelix/actions/workflows/ci.yml/badge.svg)](https://github.com/sairam0424/trelix/actions/workflows/ci.yml) |
| [`trelix-mcp`](https://pypi.org/project/trelix-mcp/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/trelix-mcp.svg)](https://pypi.org/project/trelix-mcp/) | [![Downloads](https://static.pepy.tech/badge/trelix-mcp)](https://pepy.tech/project/trelix-mcp) | ![license](https://img.shields.io/pypi/l/trelix-mcp.svg) | *(same release train as trelix)* |
| [`trelix-langchain`](https://pypi.org/project/trelix-langchain/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/trelix-langchain.svg)](https://pypi.org/project/trelix-langchain/) | [![Downloads](https://static.pepy.tech/badge/trelix-langchain)](https://pepy.tech/project/trelix-langchain) | ![license](https://img.shields.io/pypi/l/trelix-langchain.svg) | *(same release train as trelix)* |
| [`trelix-llama-index`](https://pypi.org/project/trelix-llama-index/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/trelix-llama-index.svg)](https://pypi.org/project/trelix-llama-index/) | [![Downloads](https://static.pepy.tech/badge/trelix-llama-index)](https://pepy.tech/project/trelix-llama-index) | ![license](https://img.shields.io/pypi/l/trelix-llama-index.svg) | *(same release train as trelix)* |
| [`tracehub-mcp`](https://pypi.org/project/tracehub-mcp/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/tracehub-mcp.svg)](https://pypi.org/project/tracehub-mcp/) | [![Downloads](https://static.pepy.tech/badge/tracehub-mcp)](https://pepy.tech/project/tracehub-mcp) | ![license](https://img.shields.io/pypi/l/tracehub-mcp.svg) | *(mcpsmiths org project)* |
| [`cost-guard-mcp`](https://pypi.org/project/cost-guard-mcp/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/cost-guard-mcp.svg)](https://pypi.org/project/cost-guard-mcp/) | [![Downloads](https://static.pepy.tech/badge/cost-guard-mcp)](https://pepy.tech/project/cost-guard-mcp) | ![license](https://img.shields.io/pypi/l/cost-guard-mcp.svg) | *(mcpsmiths org project)* |
| [`@commandvault/cli`](https://www.npmjs.com/package/@commandvault/cli) (npm) | [![npm](https://img.shields.io/npm/v/@commandvault/cli.svg)](https://www.npmjs.com/package/@commandvault/cli) | [![downloads](https://img.shields.io/npm/dm/@commandvault/cli.svg)](https://www.npmjs.com/package/@commandvault/cli) | ![license](https://img.shields.io/npm/l/@commandvault/cli.svg) | *(also on the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=nothumanslabs.commandvault-ai))* |

*Also distributed via: Homebrew (`brew install sairam0424/tap/ag-bash`, `brew install sairam0424/tap/mindforge`) · [MCP Registry](https://registry.modelcontextprotocol.io) (mindforge-mcp-server, @ag-bash/mcp-server, trelix-mcp, tracehub-mcp, cost-guard-mcp).*

---

<h3 align="left">Connect with me:</h3>

<p align="left">
  <a href="https://codepen.io/sairam0000" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/codepen.svg" height="30"/>
  </a>
  <a href="https://dev.to/sai_ram_0000" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/devto.svg" height="30"/>
  </a>
  <a href="https://linkedin.com/in/sairam0424" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/linked-in-alt.svg" height="30"/>
  </a>
  <a href="https://stackoverflow.com/users/18016584/sai-ram" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/stack-overflow.svg" height="30"/>
  </a>
  <a href="https://kaggle.com/sairam0000" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/kaggle.svg" height="30"/>
  </a>
  <a href="https://medium.com/@uggesairam0000" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/medium.svg" height="30"/>
  </a>
  <a href="https://www.codechef.com/users/sairam_056" style="display:inline-block; margin: 0 12px;">
    <img src="https://cdn.jsdelivr.net/npm/simple-icons@3.1.0/icons/codechef.svg" height="30"/>
  </a>
  <a href="https://www.hackerrank.com/uggesairam0000" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/hackerrank.svg" height="30"/>
  </a>
  <a href="https://codeforces.com/profile/sairam_056" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/codeforces.svg" height="30"/>
  </a>
  <a href="https://www.leetcode.com/sairam_056" style="display:inline-block; margin: 0 12px;">
    <img src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/leet-code.svg" height="30"/>
  </a>
</p>

---

### 🛠 Tech Stack

<div>
<table> <tr> <td align="center" width="96"> <!-- Animated supported --> <img src="https://techstack-generator.vercel.app/python-icon.svg" width="65" height="65" /> <br>Python </td> <td align="center" width="96"> <!-- Possibly animated --> <img src="https://techstack-generator.vercel.app/react-icon.svg" width="65" height="65" /> <br>React </td> <td align="center" width="96"> <!-- Possibly animated --> <img src="https://techstack-generator.vercel.app/github-icon.svg" width="65" height="65" /> <br>GitHub </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=go" width="65" height="65" /> <br>Go </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=fastapi" width="65" height="65" /> <br>FastAPI </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=flask" width="65" height="65" /> <br>Flask </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=django" width="65" height="65" /> <br>Django </td> </tr> <tr> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=nodejs" width="65" height="65" /> <br>Node.js </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=graphql" width="65" height="65" /> <br>GraphQL </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=postgres" width="65" height="65" /> <br>PostgreSQL </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=dynamodb" width="65" height="65" /> <br>DynamoDB </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=mongodb" width="65" height="65" /> <br>MongoDB </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=elasticsearch" width="65" height="65" /> <br>Elasticsearch </td> <td align="center" width="96"> <img src="https://techstack-generator.vercel.app/mysql-icon.svg" alt="icon" width="65" height="65" /> <br>MySQL </td> </tr> <tr> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=redis" width="65" height="65" /> <br>Redis </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=kafka" width="65" height="65" /> <br>Kafka </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=docker" width="65" height="65" /> <br>Docker </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=kubernetes" width="65" height="65" /> <br>Kubernetes </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=terraform" width="65" height="65" /> <br>Terraform </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=aws" width="65" height="65" /> <br>AWS </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=azure" width="65" height="65" /> <br>Azure </td> </tr> <tr> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=prometheus" width="65" height="65" /> <br>Prometheus </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=grafana" width="65" height="65" /> <br>Grafana </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=linux" width="65" height="65" /> <br>Linux </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=nginx" width="65" height="65" /> <br>Nginx </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=nextjs" width="65" height="65" /> <br>Next.js </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=angular" width="65" height="65" /> <br>Angular </td> <td align="center" width="96"> <img src="https://skillicons.dev/icons?i=tailwind" width="65" height="65" /> <br>Tailwind CSS </td> </tr>

<tr>
 <td align="center" width="96">
        <img src="https://techstack-generator.vercel.app/js-icon.svg" alt="icon" width="65" height="65" />
      <br>JavaScript
    </td>
    <td align="center" width="96">
        <img src="https://techstack-generator.vercel.app/webpack-icon.svg" alt="icon" width="65" height="65" />
      <br>Webpack
    </td>
    <td align="center" width="96">
        <img src="https://techstack-generator.vercel.app/ts-icon.svg" alt="icon" width="65" height="65" />
      <br>TypeScript
    </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/redux.png"/>
        <br><sub><b>Redux</b></sub>
      </td>
    <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/playwright.png"/>
        <br><sub><b>Playwright</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/rabbitmq.png"/>
        <br><sub><b>RabbitMQ</b></sub>
      </td>
        <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/swagger.png"/>
        <br><sub><b>Swagger</b></sub>
      </td>

</tr>
    <tr>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/websocket.png"/>
        <br><sub><b>WebSocket</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/grpc.png"/>
        <br><sub><b>gRPC</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/git.png"/>
        <br><sub><b>Git</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/postman.png"/>
        <br><sub><b>Postman</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/jira.png"/>
        <br><sub><b>Jira</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/jupyter_notebook.png"/>
        <br><sub><b>Jupyter</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/sass.png"/>
        <br><sub><b>Sass</b></sub>
      </td>
    </tr>
    <tr>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/firebase.png"/>
        <br><sub><b>Firebase</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/supabase.png"/>
        <br><sub><b>Supabase</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/material_ui.png"/>
        <br><sub><b>Material UI</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/shadcn_ui.png"/>
        <br><sub><b>ShadCN UI</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/vue_js.png"/>
        <br><sub><b>Vue.js</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/npm.png"/>
        <br><sub><b>npm</b></sub>
      </td>
        <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/hadoop.png"/>
        <br><sub><b>Hadoop</b></sub>
      </td>
    </tr>
    <tr>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/bun_js.png"/>
        <br><sub><b>Bun.js</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/vite.png"/>
        <br><sub><b>Vite</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/numpy.png"/>
        <br><sub><b>NumPy</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/pandas.png"/>
        <br><sub><b>Pandas</b></sub>
      </td>
        <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/tensorflow.png"/>
        <br><sub><b>TensorFlow</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/neo4j.png"/>
        <br><sub><b>Neo4j</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/cassandra.png"/>
        <br><sub><b>Cassandra</b></sub>
      </td>
    </tr>
    <tr>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/bash.png"/>
        <br><sub><b>Bash</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/loki.png"/>
        <br><sub><b>Loki</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/gcp.png"/>
        <br><sub><b>GCP</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/langchain_icon.png"/>
        <br><sub><b>LangChain</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/apache_spark.png"/>
        <br><sub><b>Apache Spark</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/matlab.png"/>
        <br><sub><b>MATLAB</b></sub>
      </td>
      <td align="center" width="90">
        <img width="65" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/selenium.png"/>
        <br><sub><b>Selenium</b></sub>
      </td>
    </tr>

</table>


</div>

---

### 🏆 Competitive Programming

- 🥇 **Google Code Jam 2023 — AIR 420 (3,687 / 85,000+)**
- 🏅 Meta Hacker Cup 2022 — Global Rank 4,048 / 70,000+
- 🏅 Flipkart Grid 2022 — Rank 1,325 / 40,000+
- 👨‍🏫 Mentored 250+ students in Data Structures & Algorithms

---

### 📊 GitHub Stats

<div align="center">

<img height="180em" src="https://github-stats-extended.vercel.app/api/top-langs/?username=sairam0424&layout=compact&count_private=true&theme=radical&hide_border=true&repo=kelvran/gateway,mcpsmiths/tracehub-mcp,mcpsmiths/cost-guard-mcp" alt="Top languages" />

<br/>

<img src="https://streak-stats.demolab.com?user=sairam0424&theme=radical&hide_border=true" alt="GitHub streak" />

</div>

---

### ✍️ Latest Writing

<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->

---

## 🏅 LeetCode Stats

<p align="center">
  <img src="https://leetcard.jacoblin.cool/sairam_056?theme=dark&font=Baloo%202&ext=heatmap" alt="LeetCode stats" />
</p>

---

### 📫 Connect With Me

- 💼 LinkedIn: https://linkedin.com/in/sairam0424
- 💻 GitHub: https://github.com/sairam0424
- 📧 Email: uggesairam0000@gmail.com

---

### ⚡ Philosophy

> I build systems that scale, stream in real time, and survive production chaos.
> Multi-agent AI orchestration, event-driven backends, and open-source infrastructure are where I live — and competitive programming keeps the fundamentals sharp.

---

### ☕ Support Me

<p><a href="https://www.buymeacoffee.com/sairam"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" height="40" alt="Buy me a coffee"/></a>
<a href="https://ko-fi.com/sairam"> <img src="https://cdn.ko-fi.com/cdn/kofi3.png?v=3" height="40" alt="Ko-fi"/></a></p>
