<div align="center">

# 🌀 AgentFlow

### Multi-Tenant, Multi-Agent Voice & Chat Platform with Intelligent Document Understanding

**Upload your knowledge base. Describe your business. Get an embeddable AI assistant in minutes.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F55036?style=for-the-badge)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-Short--Term%20Memory-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-9B59B6?style=for-the-badge)](https://www.trychroma.com)

[![License](https://img.shields.io/badge/License-Proprietary-lightgrey?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Active%20Development-success?style=flat-square)]()
[![Multi--Tenant](https://img.shields.io/badge/Architecture-Multi--Tenant%20SaaS-blueviolet?style=flat-square)]()

</div>

<br>

<div align="center">
<table>
<tr>
<td align="center" width="140"><h2>💬</h2><b>Chat</b><br><sub>Text-based assistant</sub></td>
<td align="center" width="140"><h2>🎤</h2><b>Voice</b><br><sub>Speech in, speech out</sub></td>
<td align="center" width="140"><h2>📄</h2><b>RAG</b><br><sub>Smart doc understanding</sub></td>
<td align="center" width="140"><h2>🏢</h2><b>Multi-Tenant</b><br><sub>Isolated per business</sub></td>
<td align="center" width="140"><h2>🔌</h2><b>Embeddable</b><br><sub>One script tag</sub></td>
</tr>
</table>
</div>

<br>

---

## 📖 Table of Contents

<table>
<tr>
<td width="33%" valign="top">

**Understanding the System**
- [Overview](#-overview)
- [Core Capabilities](#-core-capabilities)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)

</td>
<td width="33%" valign="top">

**How It Works**
- [System Flow](#-system-flow)
- [Multi-Tenancy Model](#-multi-tenancy-model)
- [Memory Architecture](#-memory-architecture)
- [Document Intelligence](#-document-intelligence-pipeline)
- [LangGraph Orchestration](#-orchestration-langgraph)

</td>
<td width="33%" valign="top">

**Using AgentFlow**
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Design Trade-offs](#-design-decisions--trade-offs)
- [Limitations & Roadmap](#-known-limitations)

</td>
</tr>
</table>

---

## 🔭 Overview

> AgentFlow is a **SaaS platform**, not a single chatbot.

One codebase. One deployment. Unlimited independent businesses ("tenants") — each with fully isolated data, conversations, and knowledge.

Every tenant:

```
  ①  Registers   →   business name, type, description
  ②  Uploads     →   entire knowledge base, in one bulk step
  ③  Receives    →   a unique embed token baked into a ready CDN <script> tag
  ④  Gets        →   a fully branded widget — colors, persona, greeting, position
```

Every downstream interaction — chat, retrieval, tool calls, memory — is scoped to that tenant's `organization_id`, enforced at **both** the relational-database layer and the vector-store layer.

---

## ⚡ Core Capabilities

<table>
<tr><th align="left" width="70%">Capability</th><th align="center">Status</th></tr>
<tr><td>Text chat + voice chat sharing one orchestration brain</td><td align="center">✅</td></tr>
<tr><td>CDN-embeddable widget — single <code>&lt;script&gt;</code>, self-configuring</td><td align="center">✅</td></tr>
<tr><td>Automatic document analysis → chunking strategy recommendation</td><td align="center">✅</td></tr>
<tr><td>Multiple specialized agents (document, retrieval, tools, voice, onboarding)</td><td align="center">✅</td></tr>
<tr><td>Short-term memory — session-scoped, Redis</td><td align="center">✅</td></tr>
<tr><td>Long-term memory — cross-session, loaded automatically by name + email</td><td align="center">✅</td></tr>
<tr><td>Multi-tenant isolation — row-scoping + <i>per-tenant vector collections</i></td><td align="center">✅</td></tr>
<tr><td>Bulk knowledge-base upload at onboarding</td><td align="center">✅</td></tr>
<tr><td>OTP email verification before chat access</td><td align="center">✅</td></tr>
<tr><td>OCR, table extraction, and image captioning on uploaded documents</td><td align="center">✅</td></tr>
<tr><td>Tool calling (MCP-pattern)</td><td align="center">✅</td></tr>
<tr><td>Per-tenant branding & persona customization</td><td align="center">✅</td></tr>
</table>

---

## 🏗️ Architecture

```mermaid
flowchart TD
    A[🏢 Business Owner] -->|business info + docs| B["POST /admin/onboard"]
    B --> C[Persona Generator<br/><sub>LLM writes assistant tone</sub>]
    B --> D[Document Pipeline<br/><sub>parse → analyze → chunk → embed</sub>]
    C --> E[Organization created<br/>embed_token issued]
    D --> E
    E --> F["&lt;script src=widget.js<br/>data-embed-token=...&gt;"]
    F --> G[🌐 Embedded on business website]
    G --> H[👤 Website Visitor]
    H -->|💬 text or 🎤 voice| I[widget.js resolves org<br/>via /widget-config]
    I --> J[name + email → OTP → verified]
    J --> K["POST /chat"]
    K --> L{LangGraph Orchestrator}
    L --> M[supervisor_node]
    M -->|needs retrieval?| N[retrieve_node]
    M --> O[tool_node]
    N --> O
    O --> P[generate_node<br/><sub>persona + context + history</sub>]
    P --> Q[(Redis + Postgres)]
    P --> R[Response to widget]

    style A fill:#6C5CE7,color:#fff
    style H fill:#00B894,color:#fff
    style L fill:#2D3436,color:#fff
    style Q fill:#0984E3,color:#fff
```

### 🔒 Two Independent Isolation Layers

<table>
<tr>
<td width="50%" valign="top">

**Relational Layer — PostgreSQL**

Every table (`users`, `documents`, `chunks`, `conversations`, `messages`) carries an `organization_id` foreign key, filtered on **every** query.

</td>
<td width="50%" valign="top">

**Vector Layer — ChromaDB**

Each organization owns a **physically separate collection** (`org_{id}`). Cross-tenant retrieval isn't just blocked by logic — it's structurally impossible.

</td>
</tr>
</table>

---

## 🧰 Tech Stack

<table>
<tr><th>Layer</th><th>Technology</th><th>Why</th></tr>
<tr>
<td><b>LLM Inference</b></td>
<td><img src="https://img.shields.io/badge/Groq-F55036?style=flat-square" /></td>
<td>Fast, cheap, OpenAI-compatible API surface</td>
</tr>
<tr>
<td><b>Orchestration</b></td>
<td><img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square" /></td>
<td>State-machine multi-agent orchestration, conditional routing</td>
</tr>
<tr>
<td><b>Framework Layer</b></td>
<td><img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square" /></td>
<td>Standardized LLM interface across graph nodes</td>
</tr>
<tr>
<td><b>Relational DB</b></td>
<td><img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" /></td>
<td>Source of truth — tenants, users, long-term memory</td>
</tr>
<tr>
<td><b>Vector DB</b></td>
<td><img src="https://img.shields.io/badge/ChromaDB-9B59B6?style=flat-square" /></td>
<td>Per-tenant embedding storage & similarity search</td>
</tr>
<tr>
<td><b>Embeddings</b></td>
<td><img src="https://img.shields.io/badge/sentence--transformers-FFCA28?style=flat-square" /></td>
<td>Free, local, zero external API dependency</td>
</tr>
<tr>
<td><b>Short-Term Memory</b></td>
<td><img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" /></td>
<td>Sub-millisecond session-scoped conversation buffer</td>
</tr>
<tr>
<td><b>Speech-to-Text</b></td>
<td><img src="https://img.shields.io/badge/Groq%20Whisper-F55036?style=flat-square" /></td>
<td>Fast hosted transcription</td>
</tr>
<tr>
<td><b>Text-to-Speech</b></td>
<td><img src="https://img.shields.io/badge/edge--tts-0078D4?style=flat-square" /></td>
<td>Free, local, no billing-tier restrictions</td>
</tr>
<tr>
<td><b>Document Parsing</b></td>
<td><img src="https://img.shields.io/badge/PyMuPDF%20%7C%20pdfplumber%20%7C%20docx-333?style=flat-square" /></td>
<td>Native text/table extraction across PDF, DOCX, XLSX, CSV</td>
</tr>
<tr>
<td><b>OCR</b></td>
<td><img src="https://img.shields.io/badge/EasyOCR-000?style=flat-square" /></td>
<td>Pure-Python, zero external binary dependencies</td>
</tr>
<tr>
<td><b>Image Captioning</b></td>
<td><img src="https://img.shields.io/badge/Groq%20Vision-F55036?style=flat-square" /></td>
<td>Describes embedded images/diagrams for searchability</td>
</tr>
<tr>
<td><b>Backend Server</b></td>
<td><img src="https://img.shields.io/badge/http.server-3776AB?style=flat-square&logo=python&logoColor=white" /></td>
<td>Deliberately dependency-light REST layer</td>
</tr>
<tr>
<td><b>Frontend Widget</b></td>
<td><img src="https://img.shields.io/badge/Vanilla%20JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black" /></td>
<td>Zero-build, single-file — genuinely CDN-embeddable</td>
</tr>
<tr>
<td><b>OTP Delivery</b></td>
<td><img src="https://img.shields.io/badge/SMTP%20(Gmail)-EA4335?style=flat-square&logo=gmail&logoColor=white" /></td>
<td>Verifies user identity before session creation</td>
</tr>
</table>

> **Deliberate constraint:** the backend is plain Python with a minimal dependency surface — no FastAPI, no ORM, no Docker requirement. Every choice favors transparency over framework convenience.

---

## 🔄 System Flow

### ① Tenant Onboarding

```mermaid
sequenceDiagram
    participant Owner as 🏢 Business Owner
    participant API as POST /admin/onboard
    participant Persona as Persona Agent
    participant Pipeline as Document Pipeline
    participant DB as Postgres + Chroma

    Owner->>API: business info + N files
    API->>Persona: generate tone from description
    Persona-->>API: persona instruction
    API->>DB: create organization + embed_token
    loop for each uploaded file
        API->>Pipeline: parse_document()
        Pipeline->>Pipeline: extract text/tables/images<br/>OCR fallback if needed
        Pipeline->>Pipeline: analyze_document() → strategy
        Pipeline->>Pipeline: chunk per recommended strategy
        Pipeline->>DB: save chunks (org-scoped)
        Pipeline->>DB: embed → Chroma collection "org_{id}"
    end
    API-->>Owner: embed_token + embed_snippet
```

### ② Visitor Session

```mermaid
sequenceDiagram
    participant V as 👤 Visitor
    participant W as widget.js
    participant API as Backend

    W->>API: POST /widget-config (embed_token)
    API-->>W: organization_id, persona, branding
    V->>W: enters name + email
    W->>API: POST /auth/send-otp
    API-->>V: 📧 6-digit code
    V->>W: enters code
    W->>API: POST /auth/verify-otp
    API-->>W: verified ✅
    W->>API: POST /user/lookup
    API->>API: get_or_create_user()<br/>load history<br/>seed Redis
    API-->>W: session_id, conversation_id
```

### ③ Message Turn — Text or Voice

```mermaid
flowchart LR
    A["🎤 Voice input"] -.->|Groq Whisper| B[transcribed text]
    B --> C["POST /chat"]
    D["💬 Text input"] --> C
    C --> E[persist to Redis + Postgres]
    E --> F[supervisor_node]
    F -->|trivial greeting| H[skip retrieval]
    F -->|needs lookup| G[retrieve_node<br/>org-scoped Chroma search]
    G --> I[tool_node]
    H --> I
    I --> J[generate_node<br/>persona + context + history]
    J --> K[persist reply]
    K --> L["💬 Text reply"]
    K -.->|edge-tts| M["🔊 Audio reply"]

    style F fill:#6C5CE7,color:#fff
    style J fill:#00B894,color:#fff
```

---

## 📁 Project Structure

```
AgentFlow/
│
├── 🖥️  backend/
│   ├── main.py                      HTTP server — all REST endpoints
│   ├── config.py                    environment configuration
│   ├── db.py                        schema definition + migrations
│   ├── graph.py                     LangGraph orchestration ⭐
│   ├── mcp_client.py                 local tool registry (MCP pattern)
│   ├── reset_chroma.py               utility — wipe a tenant's vectors
│   │
│   ├── 🤖 agents/
│   │   ├── document_agent.py        chunking-strategy recommendation
│   │   ├── tool_agent.py            tool-call decision + execution
│   │   ├── voice_agent.py           STT (Whisper) + TTS (edge-tts)
│   │   ├── image_captioning.py      vision-model image description
│   │   ├── onboarding_agent.py      persona generation + embed token
│   │   └── otp_agent.py             OTP generation, email, verification
│   │
│   ├── 📚 rag/
│   │   ├── ingest.py                multi-format parsing, OCR, tables
│   │   ├── chunking.py              fixed_size / recursive / structure
│   │   ├── document_store.py        Postgres persistence
│   │   └── vector_store.py          Chroma embed + per-tenant search
│   │
│   └── 🧠 memory/
│       ├── short_term.py            Redis conversation buffer
│       └── long_term.py             orgs/users/history + isolation
│
├── 🎨 widget/
│   ├── widget.js                    embeddable widget — zero build
│   └── test.html                    local embed test harness
│
└── ⚙️  .env                          GROQ_API_KEY, DATABASE_URL, ...
```

---

## 🏢 Multi-Tenancy Model

AgentFlow uses a **shared-database, tenant-scoped-row** model — the same pattern Slack, Notion, and most B2B platforms started with.

```sql
organizations (id, name, business_type, description, agent_persona,
                embed_token UNIQUE, greeting_message,
                widget_primary_color, widget_theme, widget_bubble_style,
                widget_position, widget_icon)

users          (id, organization_id → organizations.id, name, email UNIQUE)
conversations  (id, user_id → users.id, session_id)
messages       (id, conversation_id → conversations.id, role, content)

documents      (id, organization_id → organizations.id, filename,
                chunking_strategy, status)
chunks         (id, document_id → documents.id,
                organization_id → organizations.id, content, chunk_index)

otp_verifications (email, organization_id, otp_code, verified, expires_at)
```

<table>
<tr><td width="24">🔐</td><td>One email belongs to exactly <b>one</b> organization — reuse under a different <code>organization_id</code> raises an explicit error rather than silently merging accounts.</td></tr>
<tr><td width="24">🗄️</td><td>Every RAG query is scoped via a <b>dedicated Chroma collection per tenant</b> — not a shared collection with a filter — eliminating an entire class of "forgot the filter" data-leak bugs.</td></tr>
<tr><td width="24">🎫</td><td>End users never choose or type their organization. It's cryptographically fixed by the <code>embed_token</code> baked into the <code>&lt;script&gt;</code> tag at onboarding time.</td></tr>
</table>

---

## 🧠 Memory Architecture

<div align="center">

| | ⚡ Short-Term Memory | 🗄️ Long-Term Memory |
|---|:---:|:---:|
| **Store** | Redis | PostgreSQL |
| **Scope** | Current session | All history, forever |
| **Speed** | Sub-millisecond | Queried once at login |
| **Trigger** | Every message | `name` + `email` at session start |
| **Purpose** | Coherent multi-turn dialogue | Personalization across visits |

</div>

At login, `get_user_history()` pulls a user's past messages from Postgres and **seeds them into Redis** — the very first reply of a brand-new session already has full context of everything the user said, potentially days earlier.

---

## 📄 Document Intelligence Pipeline

No fixed chunking strategy is applied blindly. A **Document Analysis Agent** inspects each file's actual structure and recommends the best fit:

<table>
<tr><th>Strategy</th><th>Best For</th><th>Mechanism</th></tr>
<tr>
<td><code>fixed_size</code></td>
<td>Short, uniform content (FAQs)</td>
<td>Equal-length character splits</td>
</tr>
<tr>
<td><code>recursive</code></td>
<td>Prose, articles, essays</td>
<td>Splits on paragraph → sentence → word boundaries</td>
</tr>
<tr>
<td><code>structure_based</code></td>
<td>Resumes, contracts, reports</td>
<td>Detects headers/sections; safe fallback with a hard size cap</td>
</tr>
</table>

**Unified multi-format ingestion** — one entry point, `parse_document()`:

```
📄 PDF    → native text (PyMuPDF) + tables (pdfplumber)
             + image extraction → Groq vision captions
             + automatic OCR fallback for scanned pages
📝 DOCX   → paragraphs + table-to-text conversion
📊 XLSX   → sheet-by-sheet row extraction
📋 CSV    → row extraction
🖼️  Image  → direct OCR
```

---

## 🕸️ Orchestration: LangGraph

The chat brain is a **compiled state graph** — not one monolithic prompt.

```mermaid
flowchart LR
    S([supervisor]) -->|needs retrieval?| R[retrieve]
    S -->|no| T[tool_check]
    R --> T
    T --> G[generate]
    G --> E([END])

    style S fill:#6C5CE7,color:#fff
    style G fill:#00B894,color:#fff
    style E fill:#2D3436,color:#fff
```

| Node | Responsibility |
|---|---|
| `supervisor_node` | Deterministically skips retrieval for trivial greetings; otherwise a single LLM yes/no judgment |
| `retrieve_node` | Semantic search — scoped to the caller's own tenant collection only |
| `tool_node` | Always evaluated; LLM decides whether a registered tool applies |
| `generate_node` | Merges persona + tool results + retrieved context under explicit style constraints: concise, no fabrication, no unsolicited padding |

Splitting the problem into independent, inspectable decisions — rather than one prompt doing everything — is what makes the system debuggable and extensible.

---

## 🔐 Security

<table>
<tr><td width="28">📧</td><td><b>OTP email verification</b> — no session is created until the visitor proves ownership of their email</td></tr>
<tr><td width="28">🎫</td><td><b>Unguessable embed tokens</b> — <code>secrets.token_urlsafe</code>, not sequential IDs</td></tr>
<tr><td width="28">🚫</td><td><b>One-email-one-organization enforcement</b> — explicit rejection of cross-tenant reuse</td></tr>
<tr><td width="28">🌍</td><td><b>CORS-enabled, origin-agnostic API</b> — embeddable anywhere, still validated against real tenant data</td></tr>
</table>

---

## 🚀 Getting Started

### Prerequisites

```
✔ Python 3.11+
✔ PostgreSQL
✔ Redis
✔ Groq API key       → console.groq.com
✔ Gmail App Password  → myaccount.google.com/apppasswords
```

### Installation

```bash
git clone https://github.com/<your-username>/AgentFlow.git
cd AgentFlow/backend
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` in the project root:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/agentflow
REDIS_URL=redis://localhost:6379
SMTP_EMAIL=youraddress@gmail.com
SMTP_APP_PASSWORD=your_gmail_app_password
```

### Initialize & Run

```bash
python db.py        # create schema
python main.py       # start server → http://localhost:8000
```

### Onboard Your First Tenant

`POST /admin/onboard` with business details + knowledge-base files → receive an `embed_snippet`:

```html
<script src="widget.js" data-embed-token="YOUR_TOKEN_HERE"></script>
```

Open `widget/test.html` to see it live. 🎉

---

## 🔌 API Reference

<table>
<tr><th>Endpoint</th><th>Method</th><th>Purpose</th></tr>
<tr><td><code>/admin/onboard</code></td><td><code>POST</code></td><td>Register a tenant, bulk-upload knowledge base, receive embed snippet</td></tr>
<tr><td><code>/widget-config</code></td><td><code>POST</code></td><td>Widget self-configuration from <code>embed_token</code></td></tr>
<tr><td><code>/auth/send-otp</code></td><td><code>POST</code></td><td>Send a 6-digit verification code</td></tr>
<tr><td><code>/auth/verify-otp</code></td><td><code>POST</code></td><td>Validate a submitted OTP code</td></tr>
<tr><td><code>/user/lookup</code></td><td><code>POST</code></td><td>Create/resume a user session (requires OTP verification)</td></tr>
<tr><td><code>/chat</code></td><td><code>POST</code></td><td>Send a message through the LangGraph pipeline</td></tr>
<tr><td><code>/upload</code></td><td><code>POST</code></td><td>Upload an additional document post-onboarding</td></tr>
<tr><td><code>/voice/transcribe</code></td><td><code>POST</code></td><td>Audio → text (Groq Whisper)</td></tr>
<tr><td><code>/voice/speak</code></td><td><code>POST</code></td><td>Text → audio (edge-tts)</td></tr>
</table>

---

## ⚖️ Design Decisions & Trade-offs

<table>
<tr><th>Decision</th><th>Reasoning</th></tr>
<tr>
<td>Per-tenant Chroma collections vs. shared + filtered</td>
<td>Structural isolation — a missing filter can never leak cross-tenant data</td>
</tr>
<tr>
<td>Plain <code>http.server</code> vs. FastAPI</td>
<td>Minimal dependency surface, full transparency into request handling</td>
</tr>
<tr>
<td>ChromaDB vs. pgvector</td>
<td>Native Windows pgvector required a build toolchain unavailable locally; ChromaDB is pure-Python via pip</td>
</tr>
<tr>
<td>Local <code>sentence-transformers</code> vs. an embeddings API</td>
<td>Zero per-call cost on a step that runs on every document upload</td>
</tr>
<tr>
<td><code>edge-tts</code> vs. a paid TTS provider</td>
<td>Free-tier billing restrictions blocked programmatic access to premade voices</td>
</tr>
<tr>
<td>Deterministic greeting bypass in the supervisor</td>
<td>LLM yes/no classification is reliable but not perfectly deterministic; trivial cases are hard-coded</td>
</tr>
<tr>
<td>Persona explicitly instructed toward conciseness</td>
<td>Unconstrained auto-generated personas trended promotional and verbose, measurably degrading response quality</td>
</tr>
</table>

---

## ⚠️ Known Limitations

> This is a functionally complete prototype, not a hardened production deployment.

- ❌ No password-based authentication — OTP verifies per-session email ownership, not persistent accounts
- ❌ No database-level Row-Level Security — isolation is enforced in application code, not a hard Postgres guarantee
- ❌ No connection pooling — sufficient for demo load, not high-concurrency production traffic
- ❌ Tool-calling follows the MCP *pattern* — local functions, not yet connected to external MCP servers
- ❌ Not yet deployed — runs locally; production needs a real CDN + HTTPS + public domain

---

## 🗺️ Roadmap

- [ ] Persistent authentication layer (password + session tokens)
- [ ] Postgres Row-Level Security as defense-in-depth
- [ ] Connection pooling for concurrent request handling
- [ ] Real external MCP server integrations (calendar, CRM, email)
- [ ] Per-tenant admin dashboard (analytics, history, knowledge-base management)
- [ ] Production deployment — CDN-hosted widget, containerized backend, managed Postgres/Redis

---

<div align="center">

### 📜 License

**Proprietary** — internal project (AgentFlow / Matrix AE)

<br>

*Built as a hands-on exploration of multi-agent orchestration, multi-tenant SaaS architecture,*
*and retrieval-augmented generation — every dependency chosen for transparency over convenience.*

<br>

⭐ **AgentFlow** ⭐

</div>
