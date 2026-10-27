# 🛡️ Digital Personal Data Protection (DPDPA) Compliance & Privacy Manifesto

**Document Version:** 2.0  
**Jurisdiction Compliance:** Digital Personal Data Protection Act, 2023 (DPDPA, India), General Data Protection Regulation (GDPR, EU), and California Consumer Privacy Act (CCPA).  
**Effective Date:** October 2026  

---

## 1. Executive Summary & Privacy-by-Design Architecture

**ARIA (Autonomous Resident Intelligence Agent)** is architected around a strict **Local-First, Zero-Telemetry, Data-Sovereignty** paradigm. ARIA operates directly inside your Linux operating system workstation. Unlike conventional cloud-hosted assistants or SaaS AI co-pilots, ARIA stores all memory, episodic context, vector indices, and tool telemetry locally on your machine.

> [!IMPORTANT]
> **No Remote Telemetry:** ARIA contains zero phone-home mechanisms, no analytics trackers, and no background telemetry collectors. Your screen, clipboard, voice, terminal outputs, and file contents are never transmitted to the project maintainers or any third party, other than the specific AI API provider explicitly configured by you.

---

## 2. Classification Under the DPDP Act, 2023

Under the Indian **Digital Personal Data Protection Act, 2023 (DPDPA)**:

| Entity | Role in ARIA Architecture | Legal Description |
|---|---|---|
| **End User** | **Data Principal** | The individual to whom the personal data relates (screen contents, files, voice). |
| **End User's Device** | **Data Fiduciary & Processor** | The computing environment executing data processing. You maintain full ownership and physical control over the software runtime. |
| **Configured AI Provider** | **Data Processor (When Cloud Configured)** | Third-party inference API (e.g., Google AI Studio, OpenAI, Anthropic) selected and authenticated by your personal API credentials. When running in **Ollama (Offline)** mode, third-party data processing is zero. |

---

## 3. Core DPDP Principles & Technical Enforcement

### A. Notice & Lawful Consent (DPDPA Section 5 & 6)
- **Explicit Manual Invocations:** ARIA never records, intercepts, or observes background desktop activities passively. Screen captures and voice recordings are executed **only** upon explicit user request via the global shortcut (`Ctrl+Space`) or direct GUI command execution.
- **Microphone Push-to-Talk:** The voice transcription module (`faster-whisper`) is strictly reactive and toggled manually. The microphone stream is deactivated immediately upon transcription completion.

### B. Purpose Limitation (DPDPA Section 7)
- Screen perception data and audio inputs are processed **solely** to fulfill the specific prompt, inquiry, or task directive instructed by the user.
- Data is never cross-utilized for advertising, profiling, or training external models.

### C. Data Minimization & Ephemeral Processing (DPDPA Section 8)
- **Ephemeral Screen Buffer:** Screen captures generated for multimodal analysis are downscaled in-memory and saved to temporary files that are **immediately unlinked and securely deleted** in POSIX `finally` execution blocks.
- **Ephemeral Voice Buffer:** Audio WAV files written for Whisper transcription are immediately deleted upon transcription.
- **Context Window Caps:** In-memory conversational state is strictly bounded (default: 10 messages) to prevent runaway memory accumulation.

### D. Storage Limitation & Local Data Sovereignty (DPDPA Section 8(7))
- All long-term conversational memory, task summaries, and vector embeddings reside strictly inside your home directory:
  ```
  ~/.aria/
  ├── memory.db          (SQLite relational store)
  ├── chroma/            (Local ChromaDB persistent vector database)
  └── aria.sock          (Local Unix domain IPC socket)
  ```
- **Permission Hardening:** ARIA programmatically enforces strict POSIX file permissions:
  - `~/.aria/`: Mode `0700` (`rwx------` — restricted exclusively to your user account).
  - `.env` credential file: Mode `0600` (`rw-------` — restricted exclusively to your user account).

### E. Fully Air-Gapped / Offline Local AI Execution
For high-security, banking, legal, or confidential enterprise environments, ARIA supports complete **zero-cloud operation**:
1. **Inference Engine:** Select `ollama` with a local vision model (e.g., `llava`, `llama3.2-vision`).
2. **Speech Engine:** Local `faster-whisper` neural network weights executing on local CPU (`int8` quantization).
3. **Data Transmission:** In this configuration, network traffic is `0 bytes/sec` across external internet boundaries.

---

## 4. Rights of the Data Principal (DPDPA Sections 11–14)

ARIA provides native programmatic and GUI facilities enabling Data Principals to exercise their statutory rights without friction:

### 1. Right to Access & Data Portability (Section 11)
Users can export their complete episodic interaction logs, conversation transcripts, and task summaries in standardized JSON format:
```python
from aria.agent.memory import Memory
mem = Memory()
export_data = mem.export_personal_data()
```

### 2. Right to Correction & Erasure ("Right to be Forgotten", Section 12)
Users have the absolute right to purge, erase, and permanently destroy all episodic records:
- **GUI 1-Click Erasure:** Open **Control Center ➔ Settings ➔ 05 // MEMORY ➔ PURGE EPISODIC MEMORY // RESET**.
- **Programmatic API:**
  ```python
  from aria.agent.memory import Memory
  mem = Memory()
  mem.purge_all_data()
  ```
- **Manual CLI Destruction:**
  ```bash
  rm -rf ~/.aria/memory.db ~/.aria/chroma
  ```

### 3. Right of Grievance Redressal (Section 13)
If you identify any unexpected data retention, security regression, or privacy vulnerability, you may file a confidential disclosure via our security reporting channels specified in [SECURITY.md](SECURITY.md).

---

## 5. Security Safeguards & Defense-in-Depth

| Security Vector | Safeguard Implementation |
|---|---|
| **Destructive Command Interception** | Mandatory interactive modal verification barrier before executing `rm`, `sudo`, `dd`, `chmod`, `mkfs`, or modifying sensitive system files. |
| **Non-Root Execution Policy** | ARIA is explicitly prohibited from running as `root` or `sudo`. It operates strictly under standard unprivileged user permissions. |
| **Credential Protection** | API secrets in `.env` are never logged, displayed in plaintext, or transmitted across local socket IPC. |
| **Compositor Sandboxing** | Under Wayland, screen capture requires compositor-granted protocol access (`wlr-screencopy` / `grim`), preventing unprivileged window spying. |

---

## 6. Compliance Certification Summary

ARIA v2.0 adheres to the provisions of the **Digital Personal Data Protection Act, 2023**:
- [x] Clear and unambiguous notice provided before deployment.
- [x] Explicit manual trigger requirement for audio and visual data ingestion.
- [x] Complete local-first data localization.
- [x] Immediate ephemeral deletion of intermediate temporary media.
- [x] Native tools for Data Portability (JSON Export) and Right to Erasure (Purge).
- [x] Zero-telemetry guarantee verified by open-source code audit.
