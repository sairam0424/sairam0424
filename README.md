<h1 align="center">Sairam Ugge</h1>
<h3 align="center">GenAI &amp; Backend Engineer @Ascendion · Multi-Agent LLM Orchestration · RAG · Event-Driven Backends</h3>
<p align="center">Python · Go · FastAPI · gRPC &nbsp;|&nbsp; Open-Source AI Infrastructure &nbsp;|&nbsp; 📍 Hyderabad, India</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=sairam0424&label=Profile%20views&color=0e75b6&style=flat" alt="Profile views" />
</p>

---

### 🚀 About Me

- 🧠 **GenAI & Backend Engineer @Ascendion** (Jun 2024 – Present) — I build multi-agent LLM systems and event-driven backends that ship to real production traffic.
- 🤖 **Co-built and production-hardened Pensieve**, an AI process-orchestration engine — multi-agent LLM workflows, human-in-the-loop approval gates, real-time streaming, and governed LLM routing across cloud providers. *(2K+ daily users across domains.)*
- 🧩 **AAVA Code (AI coding plugin for VS Code)** — *architected the backend* and re-architected a single-agent prototype into a multi-agent orchestration system (Main-Agent + sub-agent via crewAI flows; 150+ skills, 40+ tools, ~60 commands); also contributed to the VS Code frontend. *(3K+ daily users across 5+ client environments.)*
- 🔁 **Co-built a prompt-driven execution engine** (LLM agent orchestration with RAG + ReAct) — raised first-pass acceptance from 65% to 85% and cut planning from 1.5h to 15min. *(1.5K+ users.)*
- ⚙️ **Owned backend systems end-to-end** (API design, data modeling, event-driven pipelines) — a decoupled Redis Streams + SSE pub/sub replaced client polling, cutting latency to sub-150ms. *(10K+ events/day for 2.5K+ users.)*
- 🎨 Co-built a **GenAI wireframe generator** (PRDs/sketches/prompts → production-ready UI artifacts) and a **prompt-to-React system** (wireframes → modular components + routing); also **led a React → Angular re-architecture** with an SSE-driven real-time backend that cut UI load latency ~30%.
- 🛠️ Open-source builder — author of **[MindForge](https://github.com/sairam0424/MindForge), [Graph-Forge](https://github.com/sairam0424/Graph-Forge), [Agent-Forge](https://github.com/sairam0424/Agent-Forge), [ContextOS](https://github.com/sairam0424/ContextOS), [ag-bash](https://github.com/sairam0424/ag-bash) & more** — agent frameworks, code-intelligence engines, and AI-native tooling. *(See Featured Projects below.)*
- 🏆 Competitive programmer — **Google Code Jam '23** (AIR 420; 3,687 / 85,000+), **Meta Hacker Cup '22**, **Flipkart GRiD '22** top tier; mentored 250–300 students in DSA.
- 🌱 Currently going deeper on **multi-agent orchestration, RAG, and distributed-systems design**.
- 📫 Reach me at **uggesairam0000@gmail.com** · 📄 [Resume](http://bit.ly/4rTi7s0) · 💼 [LinkedIn](https://linkedin.com/in/sairam0424)

---

### 🧩 Featured Projects

Open-source AI infrastructure I build in the open — agent frameworks, code-intelligence engines, and developer tooling. Commit counts are a build-signal only; each card describes architecture and tech, not adoption.

#### 🧠 Code Intelligence & Engines

| Project | What it is & Tech |
|---------|-------------------|
| **[gRPC Microservices](https://github.com/sairam0424/gRPC-micro-services)** — *Order Processing System* | Polyglot event-driven microservices — gRPC internal RPC + REST gateway, **etcd leader election**, **ACID inventory reservations**, a **Saga orchestrator**, metric-based read routing across PostgreSQL replicas, **Debezium/WAL CDC outbox**, Bloom filters, Redis caching, **DLQ + idempotency**, and observability via Envoy L7 (OpenTelemetry/Prometheus/Grafana).<br>`Go` · `Python` · `gRPC` · `PostgreSQL` · `Kafka` · `etcd` |
| **[Graph-Forge](https://github.com/sairam0424/Graph-Forge)** · `555 commits` | AI-native distributed code-intelligence platform — code modeled as a Neo4j knowledge graph + Chroma semantic embeddings, served by ~19 polyglot microservices over gRPC/REST. Kafka ingestion, Tree-Sitter AST parsing, full OpenTelemetry/Jaeger/Prometheus/Grafana stack via Envoy. RAG over massive codebases.<br>`Go` · `Python` · `gRPC` · `Neo4j` · `Chroma` · `Kafka` · `Next.js` |
| **[ag-bash](https://github.com/sairam0424/ag-bash)** · `392 commits` | AI-native bash interpreter implemented entirely in TypeScript — exposed as the `@ag-bash/bash` shell engine plus an MCP server and an agent terminal bridge. Tree-sitter WASM parser, esbuild (ESM+CJS), and WASM runtimes (CPython, QuickJS, SQLite3).<br>`TypeScript` · `WebAssembly` · `MCP` · `Tree-sitter` · `pnpm` |


#### 🤖 Agent Frameworks & Infrastructure

| Project | What it is & Tech |
|---------|-------------------|
| **[MindForge](https://github.com/sairam0424/MindForge)** · `1,193 commits` | Agentic-intelligence framework for Claude Code — 174 slash commands, 154 specialized subagents, 73 skills, hooks, governance, cost-aware model routing, and true wave (parallel) execution. Streaming WebSocket SDK. Ships as `npx mindforge-cc`.<br>`Node.js` · `TypeScript` · `MCP` · `sql.js` |
| **[Agent-Forge](https://github.com/sairam0424/Agent-Forge)** · `201 commits` | Framework-agnostic, self-improving AI agent infrastructure — a Karpathy-style propose/eval/score/commit-or-revert loop over a mutable markdown agent spec (`AGENT.md`), git-versioned, with an LLM-judge eval harness and held-out validation to guard against overfitting.<br>`Python` · `FastAPI` · `pgvector` · `Celery` · `MCP` · `Docker` |
| **[ContextOS](https://github.com/sairam0424/ContextOS)** · `175 commits` | Intelligence layer for autonomous AI agents — SQLite/vector indexing, multi-agent orchestration, and resilience. Ships as core/CLI/MCP npm packages (`@context-os/*`) plus a spatial dashboard.<br>`TypeScript` · `SQLite` · `vector search` · `MCP` · `React` · `Three.js` |

#### 🛠️ Tooling & Lab

| Project | What it is & Tech |
|---------|-------------------|
| **[CommandVault](https://github.com/sairam0424/CommandVault)** · `139 commits` | Universal AI command manager — browse/search/organize slash commands, skills, agents, plugins, rules, and hooks across Claude Code, Cursor, Copilot, Windsurf, and Aider. Indexes 350+ items via a VS Code extension, an 18-command CLI, and a three-tier search engine.<br>`TypeScript` · `VS Code Extension` · `CLI` · `SQLite` |
| **[Not-Humans-Lab](https://github.com/sairam0424/not-humans-lab)** · `289 commits` | Thin root workspace federating independent AI-infra sub-projects (SkillStack, Deep-Research, Agent-Hub, rate-limit-observatory) — polyglot Turborepo/pnpm + Next.js, Python (uv + Temporal + FastAPI), and Go services with a Qdrant vector store.<br>`TypeScript` · `Python` · `Go` · `Temporal` · `Qdrant` |

---

### 📦 Open Source Packages

| Package | Version | Downloads | License | Build |
|---|---|---|---|---|
| [`mindforge-cc`](https://www.npmjs.com/package/mindforge-cc) (npm) | [![npm](https://img.shields.io/npm/v/mindforge-cc.svg)](https://www.npmjs.com/package/mindforge-cc) | [![downloads](https://img.shields.io/npm/dm/mindforge-cc.svg)](https://www.npmjs.com/package/mindforge-cc) | ![license](https://img.shields.io/npm/l/mindforge-cc.svg) | [![CI](https://github.com/sairam0424/MindForge/actions/workflows/mindforge-ci.yml/badge.svg)](https://github.com/sairam0424/MindForge/actions/workflows/mindforge-ci.yml) |
| [`@ag-bash/bash`](https://www.npmjs.com/package/@ag-bash/bash) (npm) | [![npm](https://img.shields.io/npm/v/@ag-bash/bash.svg)](https://www.npmjs.com/package/@ag-bash/bash) | [![downloads](https://img.shields.io/npm/dm/@ag-bash/bash.svg)](https://www.npmjs.com/package/@ag-bash/bash) | ![license](https://img.shields.io/npm/l/@ag-bash/bash.svg) | *(CI omitted — default branch currently red)* |
| [`@context-os/core`](https://www.npmjs.com/package/@context-os/core) (npm) | [![npm](https://img.shields.io/npm/v/@context-os/core.svg)](https://www.npmjs.com/package/@context-os/core) | [![downloads](https://img.shields.io/npm/dm/@context-os/core.svg)](https://www.npmjs.com/package/@context-os/core) | *(registry `license` field is null — pending fix)* | *(CI omitted — 3 consecutive red runs)* |
| [`trelix`](https://pypi.org/project/trelix/) (PyPI) | [![PyPI](https://img.shields.io/pypi/v/trelix.svg)](https://pypi.org/project/trelix/) | [![Downloads](https://static.pepy.tech/badge/trelix)](https://pepy.tech/project/trelix) | ![license](https://img.shields.io/pypi/l/trelix.svg) | [![CI](https://github.com/sairam0424/trelix/actions/workflows/ci.yml/badge.svg)](https://github.com/sairam0424/trelix/actions/workflows/ci.yml) |

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
  <a href="https://stackoverflow.com/users/user:18016584" style="display:inline-block; margin: 0 12px;">
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

<img height="180em" src="https://github-stats-extended.vercel.app/api/top-langs/?username=sairam0424&layout=compact&count_private=true&theme=radical&hide_border=true" alt="Top languages" />

<br/>

<img src="https://streak-stats.demolab.com?user=sairam0424&theme=radical&hide_border=true" alt="GitHub streak" />

</div>

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
