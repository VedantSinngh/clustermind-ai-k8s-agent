# ClusterMind — AI Kubernetes Troubleshooting Agent

**Developer:** Vedant Singh  
**Architecture:** Production-Grade Multi-Cluster AI Agent  
**Backend:** FastAPI (Python) on Azure Container Apps  
**Frontend:** Next.js 14 (App Router) + Tailwind CSS on Vercel  
**Database:** Azure Database for PostgreSQL (Flexible Server)  
**AI Inference Engine:** Groq LPU (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)  
**Secrets Management:** Azure Key Vault  

---

## 1. Executive Summary

Kubernetes is the modern gold standard for application and Machine Learning workloads, but diagnosing cluster anomalies (`CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff`, service endpoints disconnects) requires deep operational experience.

**ClusterMind** empowers developers and SREs to self-diagnose cluster issues in seconds. It collects multi-layered telemetry directly from the Kubernetes API server (pods status, container stderr logs, warning events, deployment replica states, network endpoints), passes the evidence to a defensively managed Groq LLM reasoning engine, and returns:
- **Root Cause Diagnosis**
- **Actionable Step-by-Step Resolution Strategy**
- **Radial Confidence Score (0–100%)**
- **Non-Destructive Executable `kubectl` Command**
- **Human-in-the-Loop Remediation Execution (RBAC-enforced)**
- **Audit Trail History**

---

## 2. Real-World Architectural Design

Unlike single-cluster proof-of-concept scripts, ClusterMind is architected for enterprise production deployment:

1. **RBAC & Multi-Tenancy**: Every request verifies user authorization via `user_cluster_access` table with `viewer` vs `operator` role scoping.
2. **Zero Plaintext Secrets**: Kubeconfigs and API credentials are never stored in database tables or sent to the frontend. They are referenced by Azure Key Vault secret names (`kubeconfig_secret_ref`) and decrypted in-memory inside the backend container.
3. **Read-Only by Default**: The telemetry agent is read-only. Modifying resource states requires explicit human confirmation via an `operator` role and logs an immutable audit trail in `remediation_actions`.
4. **Groq Cost & Rate Limit Shielding**: Incorporates a 5-minute SHA256 evidence TTL cache to prevent redundant LLM calls. On 429/503 rate-limits or timeouts, it gracefully degrades to return raw telemetry rather than throwing a system failure.
5. **Groq Model Fallback**: Primary model defaults to `llama-3.3-70b-versatile`, with automated failover to `llama-3.1-8b-instant`.

---

## 3. Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    kubeconfig_secret_ref TEXT NOT NULL,
    org_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_cluster_access (
    user_id UUID REFERENCES users(id),
    cluster_id UUID REFERENCES clusters(id),
    role TEXT CHECK (role IN ('viewer', 'operator')) DEFAULT 'viewer',
    PRIMARY KEY (user_id, cluster_id)
);

CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    cluster_id UUID REFERENCES clusters(id),
    namespace TEXT,
    root_cause TEXT,
    suggested_fix TEXT,
    suggested_command TEXT,
    confidence_score INT,
    raw_evidence JSONB,
    llm_response JSONB,
    status TEXT CHECK (status IN ('running','completed','failed')) DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE investigation_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(id),
    step TEXT,           -- 'checking_pods', 'reading_logs', 'analyzing_events', 'ai_reasoning', 'completed'
    status TEXT,         -- 'started', 'completed'
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE remediation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(id),
    approved_by UUID REFERENCES users(id),
    command_executed TEXT,
    result TEXT,
    executed_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Quickstart — Local Development

### Option A: Using Docker Compose (Recommended)
```bash
# Set your Groq API Key (Optional — fallback mode active if omitted)
export GROQ_API_KEY="your-groq-api-key"

# Launch database, FastAPI backend, and Next.js frontend
docker-compose up --build
```
Access the application at `http://localhost:3000`.

### Option B: Local Native Setup

#### Backend Setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

---

## 5. Agile SDLC Increments

- **Increment 1 — Evidence Collector**: Core FastAPI service with `kubernetes` python client inspectors (`pod_inspector`, `logs_collector`, `event_analyzer`, `deployment_inspector`, `network_inspector`).
- **Increment 2 — Groq LLM Reasoning Engine**: SRE system prompt, Groq chat completion client, TTL caching, defensive JSON parsing, model fallback.
- **Increment 3 — Auth & Multi-Tenancy**: JWT auth, bcrypt hashing, PostgreSQL schema, rate-limiting (20 requests/user/hour).
- **Increment 4 — Next.js 14 Minimalist UI**: Sleek near-black design system (`#0A0A0B`), live step-by-step progress stepper, radial confidence score ring, copyable fix block, audit dashboard.
- **Increment 5 — Production Hardening**: Azure Key Vault secret binding, read-only enforcement, human-in-the-loop confirmation modal.
- **Increment 6 — CI/CD & Deployment**: Multi-stage Docker builds, GitHub Actions workflows for Azure Container Apps and Vercel.

---

## 6. Footer & Credit

Designed & Developed by **Vedant Singh**  
ClusterMind — Enterprise AI Kubernetes Troubleshooting Agent
