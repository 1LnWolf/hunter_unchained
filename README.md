# Hunter Unchained

> **Autonomous, self‑learning red‑team assistant — fully local, no cloud, no tokens.**

Hunter Unchained is a modular AI‑driven security testing platform that plans, executes, and reports on offensive security engagements. It combines a local large language model (LLM) with tool orchestration, continuous learning, multi‑method vulnerability discovery, human‑in‑the‑loop safety, and automatic report generation.

It runs entirely on your hardware. No API keys, no subscriptions, no data leaving your machine.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Capabilities](#capabilities)
- [Stealth & Operational Security](#stealth--operational-security)
- [Safety & Human-in-the-Loop](#safety--human-in-the-loop)
- [Zero-Day Discovery](#zero-day-discovery)
- [Continuous Learning](#continuous-learning)
- [Reports](#reports)
- [Switching Model Backends](#switching-model-backends)
- [Fine-Tuning the Model](#fine-tuning-the-model)
- [Resource Requirements](#resource-requirements)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Legal & Ethical Notice](#legal--ethical-notice)
- [License](#license)
- [Credits](#credits)

---

## Features

- **100% Local** – Uses Ollama or llama.cpp for LLM inference. No cloud, no tokens, no leaks.
- **Autonomous Mission Execution** – Give a high‑level objective; Hunter plans and executes the attack chain.
- **Human-in-the-Loop** – Mission approval, critical checkpoints, tool install confirmation, debug fix approval.
- **Tool Mastery** – Auto‑discovers every executable on `PATH`, installs missing tools from `apt`, `pip`, or GitHub (with permission).
- **Continuous Learning** – Ingests CVEs (NVD), CISA KEV, GitHub Advisories, security RSS feeds, and custom URLs in the background.
- **Hybrid Retrieval** – BM25 (keyword) + dense embeddings (semantic) for best‑of‑both retrieval.
- **Episodic Memory** – SQLite + vector store remembers past missions and reuses successful techniques.
- **On‑Demand Research** – `research <topic>` searches the web and ingests articles into the knowledge base.
- **Multi‑Method Zero‑Day Discovery** – Fuzzing (AFL++), static analysis, symbolic execution (angr), patch diffing, taint analysis, and LLM code review.
- **Innovation Engine** – LLM‑driven mutation of existing exploits to create new variants, validated in sandbox.
- **Debugging Engine** – Diagnoses mission failures and proposes fixes (with your approval).
- **Automatic Reports** – Markdown reports with executive summary, methodology, findings, and remediation.
- **Stealth** – Process masquerading, randomized delays, optional SOCKS5 proxy.
- **Safety** – GPG master authentication, scope enforcement, self‑defense, Docker sandbox, encrypted logs, kill switch.
- **Dual LLM Backend** – Ollama (dev) and llama.cpp (field ops), with automatic detection.
- **Extensible** – Every module is independent; add new tools, learning sources, or discovery methods without breaking the core.

---

## Architecture Overview

```
┌──────────────┐   ┌───────────────┐   ┌──────────────┐
│  Console UI  │──▶│  Agent Core   │──▶│  Local LLM   │
└──────┬───────┘   └───────┬───────┘   └──────────────┘
       │                   │
       │            ┌──────┴───────┐
       │            │  Knowledge   │  (ChromaDB + BM25)
       │            │  Base        │
       │            └──────┬───────┘
       │                   │
       │            ┌──────┴───────┐   ┌───────────────┐
       │            │   Memory     │◀─▶│  Live Learner │
       │            │ (SQLite+Vec) │   │  (CVE, RSS)   │
       │            └──────┬───────┘   └───────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌───────────────┐   ┌──────────────┐
│ Permission   │◀─▶│ Tool          │──▶│  Sandbox     │
│ Gate         │   │ Orchestrator  │   │  (Docker)    │
└──────────────┘   └───────┬───────┘   └──────────────┘
                           │
                    ┌──────┴────────┐
                    │ Zero-Day      │
                    │ Discovery     │  (fuzzing, angr, static)
                    └───────────────┘
```

- **UI** – Rich console prompt loop.
- **Agent Core** – LLM planner + RAG + memory + clarification.
- **Tool Orchestrator** – Executes tools safely, installs missing ones.
- **Permission Gate** – Mission approval + critical checkpoints.
- **Knowledge Base** – Hybrid vector + keyword retrieval.
- **Memory** – Episodic memory for experience reuse.
- **Live Learner** – Continuous background ingestion.
- **Sandbox** – Isolated Docker container for untrusted code.
- **Zero-Day Engine** – Fuzzing, static analysis, symbolic execution.

---

## Requirements

### Hardware

| Profile | CPU | RAM | GPU | Disk |
|---------|-----|-----|-----|------|
| Minimal (no fuzzing) | 4 cores | 16 GB | optional | 30 GB |
| Balanced | 8 cores | 32 GB | 8–12 GB VRAM | 100 GB |
| Zero-day research | 16+ cores | 64 GB+ | 24 GB VRAM | 200 GB+ |

### Software

- **Linux** (Ubuntu 22.04+ recommended; other distros work with apt equivalents)
- **Python 3.11+**
- **Docker** (for sandbox and fuzzing)
- **GPG** (for master authentication)
- **Tor** (optional, for stealth)
- **Ollama** or **llama.cpp** (for local LLM)

---

## Installation

### 1. Clone or Create the Project

Create the directory structure and place all files as shown in [Directory Structure](#directory-structure). Or clone from your repository:

```bash
git clone https://github.com/1LnWolf/hunter_unchained
cd hunter_unchained
```

### 2. Run the Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The script will:

1. Install system packages (Python, pip, GPG, Docker, Tor, wget, curl).
2. Create a Python virtual environment in `venv/`.
3. Install Python dependencies.
4. Ask you to choose a model backend:
   - **1) Ollama** – easy, GPU‑friendly, needs a background server.
   - **2) llama.cpp** – fully embedded, no server, stealthy.
   - **3) Auto** – tries Ollama first, falls back to llama.cpp.
5. Pull or download the model.
6. Start Tor.
7. Build the sandbox Docker image.
8. Generate a GPG key if one does not exist.
9. Download initial CVE data to populate the knowledge base.

### 3. (Optional) Fuzzing Setup

```bash
chmod +x scripts/setup_fuzzing.sh
./scripts/setup_fuzzing.sh
```

Installs AFL++, angr, pwntools, and builds the fuzzer Docker image.

### 4. Activate the Virtual Environment

```bash
source venv/bin/activate
```

---

## Configuration

All settings live in `hunter_unchained.yaml`. Key sections:

### Authentication

```yaml
master:
  auth_method: "gpg"
  gpg_key_fingerprint: "YOUR_FINGERPRINT"
```

Replace `YOUR_FINGERPRINT` with the fingerprint printed by the setup script.

### Scope

```yaml
scope:
  networks: ["10.0.0.0/24"]    # allowed IP ranges
  domains: []                  # allowed domains (e.g. "*.example.com")
  exclude: []                  # never touch these
```

Set to `["0.0.0.0/0"]` to allow all IPs (removes restrictions).

### Model Backend

```yaml
model:
  provider: "auto"             # auto / ollama / llama_cpp
  temperature: 0.2
  max_tokens: 4096
```

### Human-in-the-Loop

```yaml
execution:
  approval_mode: "mission"
  critical_checkpoints:
    - "exploit"
    - "lateral_movement"
    - "credential_dump"
    - "critical"
```

Remove entries to reduce pauses, add more to increase oversight.

### Stealth

```yaml
stealth:
  enable: true
  process_masquerade: true
  proxies:
    socks5: "socks5://127.0.0.1:9050"
```

### Learning

```yaml
learning:
  search_provider: "duckduckgo"    # no API key required
  auto_research: false             # set true to research before each mission
  custom_scrape_urls: []
```

### Fuzzing & Discovery

```yaml
fuzzing:
  enabled: true
  max_campaign_time: 3600
  use_docker: true

discovery:
  static_analysis: true
  symbolic_execution: false        # heavy, enable if you have RAM
  llm_code_review: true
```

### Self-Defense

```yaml
self_defense:
  protected_hosts: ["127.0.0.1", "::1", "localhost"]
  protected_files: ["/etc/shadow", "/home/user/.ssh"]
  require_second_factor: true
```

---

## Usage

### Start Hunter

```bash
hunter
```

### Authenticate

Hunter will print a random challenge string. Sign it with your GPG key:

```bash
echo -n "<challenge>" | gpg --clearsign
```

Paste the entire signed message back into Hunter. If the fingerprint matches, Hunter starts.

### Give a Mission Objective

At the prompt, type a plain‑language objective. Examples:

```
Perform internal network reconnaissance on 10.0.0.0/24 and find exploitable services.
```

```
Scan https://shop.example.com for all vulnerabilities.
```

```
Decompile /path/to/app.apk and review every source file for hardcoded secrets and logic flaws.
```

Hunter will:

1. Ask for clarification if needed.
2. Optionally research the topic.
3. Present a task plan.
4. Ask for mission approval.
5. Execute, pausing at critical checkpoints.
6. Install missing tools (with your approval).
7. Generate a Markdown report.

### Special Commands

| Command | Description |
|---------|-------------|
| `research <topic>` | Search the web and ingest articles into the knowledge base. |
| `ingest <path>` | Ingest local `.txt`, `.md`, or `.pdf` files into the knowledge base. |
| `exit` | Exit Hunter cleanly. |
| `Ctrl+C` | Graceful shutdown (encrypts logs and stops background tasks). |

### Critical Checkpoints

When a task has a risk level that matches `critical_checkpoints`, Hunter pauses:

```
Critical checkpoint: sqlmap ['-u', 'https://...', '--batch']. Proceed? (y/n)
```

Approve to run, deny to skip.

### Tool Installation

If a missing tool is needed:

```
Missing tool: ['nuclei']. Install?
Install missing tools? (y/n)
```

Approve to install. Hunter tries `apt`, then `pip`, then GitHub (with a URL prompt if needed).

### Kill Switch

In an emergency:

```bash
./scripts/kill_switch.sh
```

Kills all Hunter processes, stops related Docker containers, and wipes temporary files.

---

## How It Works

1. **Mission input** – You give a plain‑language objective.
2. **Clarification** – The LLM asks for missing details if needed.
3. **Research (optional)** – Hunter fetches and ingests relevant web pages.
4. **Retrieval** – Hunter pulls relevant facts from its knowledge base (hybrid BM25 + vector) and similar past missions from memory.
5. **Planning** – The LLM produces a JSON task list with tool, arguments, reason, and risk.
6. **Approval** – You review and approve the mission.
7. **Execution** – Tasks run through the tool orchestrator; missing tools are installed with permission; high‑risk actions pause.
8. **Learning** – Every result is stored in memory; successful techniques bias future plans.
9. **Reporting** – A Markdown report is generated with findings and remediation.

---

## Capabilities

### Offensive

- Network reconnaissance and service enumeration (nmap, masscan).
- Web application testing (gobuster, sqlmap, ffuf, nikto, nuclei).
- Exploitation via Metasploit modules (with stealth wrapping).
- Credential attacks (hydra, crackmapexec).
- Post‑exploitation (impacket, secretsdump).
- Custom exploit generation (msfvenom, LLM‑written scripts).

### Defensive

- System monitoring and log analysis (`journalctl`, `ps`, `netstat`).
- Detecting suspicious activity and proposing mitigations.
- Blocking attackers (with your approval).
- Learning IOCs and TTPs from incidents.

### Research

- On‑demand web research.
- Local file ingestion (txt, md, pdf).
- Continuous CVE/RSS/KEV/GH ingestion.
- Fine‑tuning guidance for specialized LLMs.

### Reporting

- Markdown with executive summary, methodology, findings, evidence, recommendations.
- Saved to `data/reports/`.

---

## Stealth & Operational Security

- **Process masquerading** – Renames tools to innocuous names like `kworker`.
- **Randomized delays** – Breaks timing analysis.
- **Optional SOCKS5** – Configure in YAML; not automatic.
- **Tor** – Started by setup script; use a system‑wide transparent proxy or `torsocks` to route all traffic.
- **Recommended: VPN** – For maximum IP protection, use a system‑wide VPN or Tor.

**Note:** Out of the box, Hunter does **not** route tools through Tor automatically. You must configure a system‑wide proxy or modify commands.

---

## Safety & Human-in-the-Loop

Hunter is autonomous but always under your control:

1. **GPG Authentication** – Only you can start it.
2. **Mission Approval** – You approve the plan before execution.
3. **Critical Checkpoints** – High‑risk actions pause for confirmation.
4. **Tool Install Approval** – Every install is confirmed.
5. **Debug Fix Approval** – Fixes are proposed and only applied with your consent.
6. **Scope Enforcement** – Targets outside your defined networks/domains are rejected.
7. **Self‑Defense** – Never attacks localhost or protected files.
8. **Sandbox** – Untrusted code runs in Docker with no network.
9. **Encrypted Logs** – Session logs are GPG‑encrypted.
10. **Kill Switch** – One command stops everything.

---

## Zero-Day Discovery

Hunter can combine multiple methods to find unknown vulnerabilities:

| Method | Tool | Purpose |
|--------|------|---------|
| Fuzzing | AFL++, libFuzzer | Feed malformed inputs to find crashes. |
| Crash Analysis | GDB + Exploitable | Classify exploitability. |
| Exploit Synthesis | angr | Symbolic execution to build exploit. |
| Static Analysis | semgrep, bandit | Find patterns without running code. |
| Taint Analysis | taintgrind | Track untrusted input to sinks. |
| Patch Diffing | BinDiff, Diaphora | Compare patched/unpatched binaries. |
| LLM Code Review | Local LLM | Read source line by line, find logic flaws. |

Each method is selectable via `discovery` config. Resource‑heavy methods ask for approval.

---

## Continuous Learning

Hunter learns in several ways:

1. **Background feeds** – NVD, CISA KEV, GitHub Advisories, security RSS, custom URLs.
2. **On‑demand research** – `research <topic>` fetches and ingests web pages.
3. **Local ingestion** – `ingest <path>` adds your own documents.
4. **Episodic memory** – Every mission step is stored; similar past missions are reused.
5. **Innovation engine** – LLM rewrites existing exploits to create variants.
6. **Fuzzing findings** – New crashes are added to the knowledge base.

No cloud, no retraining required for daily operation.

---

## Reports

After each mission, Hunter generates a Markdown report:

```
data/reports/report_YYYYMMDD_HHMMSS.md
```

Includes:

- Executive Summary
- Methodology
- Findings (with evidence)
- Recommendations

Reports are plain Markdown—view in any editor, print, or convert to PDF.

---

## Switching Model Backends

Change `model.provider` in `hunter_unchained.yaml`:

- `"ollama"` – Uses Ollama server (needs `ollama serve` running).
- `"llama_cpp"` – Uses embedded llama.cpp (no server, no network).
- `"auto"` – Tries Ollama first, falls back to llama.cpp.

No code changes needed. Restart Hunter after editing.

---

## Fine-Tuning the Model

If you want to specialize the LLM on security data:

1. Prepare a dataset in JSONL format with `instruction` and `output` fields.
2. Run:

```bash
python scripts/fine_tune.py --data_path my_data.jsonl --model_name mistralai/Mistral-7B-v0.1 --output_dir ./fine_tuned
```

3. Convert the output to GGUF (for llama.cpp) or import it into Ollama.
4. Point `model.llama_cpp.model_path` or `model.ollama.model_name` to the new model.

Requires a GPU with at least 16 GB VRAM.

---

## Resource Requirements

- **Baseline (no fuzzing, CPU inference)**: 8–10 GB RAM, 10–15 GB disk.
- **With fuzzing/symbolic execution**: 32+ GB RAM, multiple CPU cores, GPU recommended.
- **Full research setup**: 64 GB RAM, 200 GB disk, 24 GB GPU.

Disk grows with the knowledge base (CVEs, articles, fuzzing findings). Plan for 5–10 GB/year of continuous learning.

---

## Directory Structure

```
hunter_unchained/
├── hunter_unchained.yaml
├── pyproject.toml
├── .env.example
├── README.md
├── Dockerfile.sandbox
├── Dockerfile.fuzzer
├── hunter/
│   ├── __init__.py
│   ├── main.py
│   ├── config_loader.py
│   ├── master_auth.py
│   ├── agent_core.py
│   ├── tool_orchestrator.py
│   ├── tool_installer.py
│   ├── stealth_wrapper.py
│   ├── permission_gate.py
│   ├── safety.py
│   ├── self_defense.py
│   ├── knowledge_base.py
│   ├── memory.py
│   ├── learning_pipeline.py
│   ├── topic_researcher.py
│   ├── sandbox.py
│   ├── fuzzing_engine.py
│   ├── crash_analyzer.py
│   ├── exploit_generator.py
│   ├── payload_builder.py
│   ├── innovation_engine.py
│   ├── vuln_discovery_engine.py
│   ├── report_generator.py
│   ├── debug_engine.py
│   ├── ui.py
│   └── models/
│       ├── __init__.py
│       ├── base.py
│       ├── ollama_model.py
│       ├── llama_cpp_model.py
│       └── tool_parsers.py
├── tools/
│   ├── tool_index.yaml
│   └── github_repos.yaml
├── scripts/
│   ├── setup.sh
│   ├── setup_fuzzing.sh
│   ├── kill_switch.sh
│   ├── cve_ingest.py
│   └── fine_tune.py
└── tests/
    ├── test_stealth.py
    └── test_auth.py
```

---

## Troubleshooting

### "Authentication failed"

- Ensure the fingerprint in `hunter_unchained.yaml` matches your GPG key.
- Make sure you signed the exact challenge string.
- Use `gpg --list-keys --with-colons | grep fpr` to verify the fingerprint.

### "Ollama server not reachable"

- Start Ollama: `ollama serve`
- Or set `model.provider: "llama_cpp"` to skip Ollama.

### "Model not found"

- For Ollama: `ollama list` to confirm the model is pulled.
- For llama.cpp: verify the GGUF file exists at the path in config.

### "Out of scope"

- Add the target to `scope.networks` or `scope.domains`.
- Or set `scope.networks: ["0.0.0.0/0"]` to disable restrictions.

### Slow planning

- First inference on CPU is slow. Subsequent calls are faster.
- GPU offload (`n_gpu_layers: 35`) dramatically speeds up llama.cpp.

### Docker sandbox errors

- If you don't need sandboxing, set `sandbox_validation: false`.
- Ensure Docker is installed and running.

### Tool installation fails

- Check `apt` and `pip` availability.
- For GitHub installs, ensure `git` is installed.
- Provide a valid URL when prompted.

### IP exposure

- Hunter does not hide your IP by default. Use a system‑wide VPN, Tor transparent proxy, or `torsocks` for tools.

### Kill switch not working

- Run with `sudo` if needed.
- Ensure `pkill` is available (part of `procps`).

---

## Testing

Run the unit tests:

```bash
python -m unittest discover tests
```

Currently tests cover `StealthWrapper` and GPG authentication. Extend them as you add features.

Tests are optional for daily use. They help catch regressions when modifying code.

---

## Roadmap

- **Enhanced stealth** – Automatic Tor routing for subprocesses.
- **Web dashboard** – Browser‑based live monitoring and mission control.
- **Distributed execution** – Split LLM, memory, and tools across machines.
- **Multi‑user support** – Roles, scoped permissions, audit trails.
- **Integrations** – Sliver, Mythic, BloodHound, CrackMapExec as first‑class tools.
- **Report enhancements** – PDF/HTML export, timeline visualizations.
- **LLM support** – vLLM, LM Studio, text-generation-webui backends.
- **Model ensemble** – Different LLMs for planning vs. execution.

---

## Legal & Ethical Notice

**Hunter Unchained is a powerful offensive security tool**
**Do not use Hunter against systems you do not own or have explicit written permission to test.** Unauthorized use is illegal in most jurisdictions and may result in criminal prosecution. You are solely responsible for your actions and their consequences.

Hunter includes safety mechanisms (authentication, scope, self‑defense, permission gates) but they are configurable. Even with safety mechanisms, the operator remains fully responsible.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Credits

Built by an operator, for operators, on a very bad day. Powered by open‑source LLMs, open‑source tooling, and open‑source rage.

Special thanks to the projects that make this possible: Ollama, llama.cpp, ChromaDB, sentence‑transformers, AFL++, angr, pwntools, and the entire infosec community.

---

**Hunter Unchained is a multi-edged sword. Keep it sheathed unless you own the target.**
