# CYPHER

## DigitalDNA — Evidence-Driven Public Identity Intelligence

**Team:** Cypher
**Hackathon:** NEURAX Hackathon 3.0
**Domain:** AI in Cybersecurity
**Problem:** Public Profile & Digital Footprint Intelligence

---

## 1. Overview

DigitalDNA is an evidence-driven public identity intelligence system developed by **Cypher**.

The system analyzes an organizer-authorized image and limited contextual information to identify the most likely public identity and reconstruct the person's publicly documented digital footprint.

Instead of treating identity discovery as a simple search problem, CYPHER approaches it as an **entity-resolution problem under uncertainty**.

It discovers candidate profiles, extracts structured information, correlates entities across independent public sources, evaluates supporting evidence, detects conflicts, and presents the resulting relationships through an interactive intelligence graph and timeline.

### Core principle

> **Discovery finds candidates. Correlation connects evidence. Resolution determines relationships.**

---

# 2. Problem

A person's public digital presence is fragmented across independent platforms.

The same individual may appear under:

* different usernames
* abbreviated names
* alternate spellings
* different profile photographs
* incomplete biographies
* different professional affiliations

Relevant information may also be distributed across:

* professional profiles
* developer platforms
* company websites
* conferences
* hackathons
* interviews
* publications
* projects
* products
* patents and innovation records

Manually connecting these fragments is slow and error-prone.

A system that simply searches for usernames or scrapes websites does not solve the core problem.

The central challenge is:

> **Determine which publicly available fragments are likely associated with the same identity, while preserving the evidence and uncertainty behind each relationship.**

---

# 3. Solution

DigitalDNA builds an evidence-backed identity graph.

```text
Authorized Input
       │
       ▼
Candidate Generation
       │
       ▼
Public Discovery
       │
       ▼
Entity Extraction
       │
       ▼
Identity Resolution
       │
       ▼
Evidence Correlation
       │
       ▼
Conflict Detection
       │
       ▼
Identity Graph
       │
       ├──────────────┐
       ▼              ▼
   Timeline      Intelligence Report
```

The system deliberately separates:

### Discovery

Finding potentially relevant public information.

### Resolution

Determining whether information likely belongs to the same person.

### Verification

Connecting each conclusion to its supporting evidence.

This separation is central to the architecture.

---

# 4. Key Features

## Identity Resolution

DigitalDNA generates multiple candidate identities and evaluates them using multiple signals.

Signals can include:

* name similarity
* username similarity
* organization overlap
* location overlap
* biography similarity
* project overlap
* event overlap
* website relationships
* cross-platform links
* authorized visual similarity

No single signal is treated as sufficient proof.

---

## Evidence Graph

Every material relationship can be traced back to its supporting sources.

Example:

```text
Rahul Sharma
      │
      │ possible_identity
      ▼
GitHub: rsharma23
      │
      ├── Same organization
      ├── Website cross-link
      ├── Shared project
      └── Username similarity
```

The graph therefore represents not only **what the system believes**, but **why it believes it**.

---

## Confidence & Uncertainty

DigitalDNA distinguishes between:

```text
VERIFIED
PROBABLE
POSSIBLE
CONFLICT
INSUFFICIENT EVIDENCE
```

Confidence is treated as an evidence-assessment mechanism rather than a declaration of truth.

---

## Conflict Detection

If public sources disagree, DigitalDNA preserves the disagreement.

Example:

```text
LOCATION CONFLICT

Hyderabad
├── LinkedIn
└── GitHub

Bangalore
└── Conference Profile

Status: UNRESOLVED
```

The system does not silently select one source.

---

## Digital Footprint Discovery

The system is designed to work with approved public sources including:

* professional profiles
* developer profiles
* social platforms
* personal websites
* company websites
* conferences
* hackathons
* events
* interviews
* publications
* projects
* products
* public innovation records

---

## Relationship Graph

Relevant entities can be represented as:

```text
Person
 ├── User Account
 ├── Organization
 ├── Project
 ├── Event
 ├── Publication
 ├── Product
 └── Website
```

Relationships may include:

```text
WORKS_AT
FOUNDED
CREATED
PARTICIPATED_IN
SPOKE_AT
AUTHORED
MEMBER_OF
LINKS_TO
POSSIBLE_IDENTITY
```

---

## Timeline

Public activities are organized chronologically.

```text
2023
 ├── University
 └── Hackathon

2024
 ├── Project
 └── Conference

2025
 ├── Company
 └── Product

2026
 └── Public Event
```

Every timeline entry retains its supporting evidence.

---

# 5. System Architecture

```text
┌───────────────────────────────────────────────┐
│                 CYPHER / DigitalDNA              │
├───────────────────────────────────────────────┤
│                                               │
│              Investigation UI                 │
│                                               │
├───────────────────────────────────────────────┤
│                   API Layer                   │
├───────────────────────────────────────────────┤
│                                               │
│ Discovery ──► Extraction ──► Resolution       │
│                              │                │
│                              ▼                │
│                       Correlation             │
│                              │                │
│               ┌──────────────┼─────────────┐  │
│               ▼              ▼             ▼  │
│           Evidence         Graph        Timeline│
│               │              │             │  │
│               └──────────────┼─────────────┘  │
│                              ▼                │
│                    Intelligence Report        │
│                                               │
└───────────────────────────────────────────────┘
```

---

# 6. Identity Resolution Model

Candidate identities are evaluated using independent evidence.

Conceptually:

```text
Identity Score =
    Name Signal
  + Username Signal
  + Organization Signal
  + Context Signal
  + Semantic Signal
  + Cross-Link Signal
  + Evidence Agreement
```

The scoring engine is deliberately separated from the discovery layer.

This means discovery tools can change without changing the identity-resolution architecture.

---

# 7. Evidence Model

A material claim is represented conceptually as:

```json
{
  "claim": "Person X founded Company Y",
  "source": "public-source",
  "source_type": "company",
  "evidence": "structured-extracted-fact",
  "confidence": "high",
  "observed_at": "timestamp"
}
```

This enables:

* provenance tracking
* source comparison
* conflict detection
* evidence inspection
* human review

---

# 8. Technology Stack

### Backend

* Python
* FastAPI
* Pydantic

### Intelligence

* LLM-based structured extraction
* Embeddings
* Fuzzy matching
* Deterministic matching
* Entity resolution
* Evidence scoring

### Storage

* PostgreSQL / JSONB
* Graph representation
* Evidence/provenance storage

### Frontend

* React
* TypeScript
* Interactive graph visualization
* Timeline visualization

---

# 9. Project Structure

```text
cypher/
│
├── app/
│   ├── api/
│   ├── core/
│   │   ├── discovery/
│   │   ├── extraction/
│   │   ├── resolution/
│   │   ├── correlation/
│   │   ├── evidence/
│   │   ├── graph/
│   │   └── timeline/
│   │
│   └── models/
│
├── frontend/
│
├── tests/
│
├── docs/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── RESEARCH.md
└── README.md
```

The architecture intentionally separates **Cypher's intelligence layer** from external discovery adapters.

---

# 10. Setup

## Requirements

* Python 3.11+
* Node.js 20+
* Git
* PostgreSQL or configured local database
* Optional local LLM runtime

---

## Backend

```bash
git clone <repository-url>
cd cypher

python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Populate the required configuration values.

Start the API:

```bash
uvicorn app.api.main:app --reload
```

---

# 11. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will display the investigation interface.

---

# 12. Environment Configuration

Environment variables are documented in `.env.example`.

Typical configuration includes:

```env
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000

DATABASE_URL=

LLM_PROVIDER=local
LLM_BASE_URL=
LLM_MODEL=

SEARCH_PROVIDER=
SEARCH_API_KEY=

GRAPH_BACKEND=
```

**Never commit `.env` or API credentials.**

---

# 13. Security & Authorization

DigitalDNA is designed for organizer-authorized, consented and publicly available information.

The system does not require or support:

* private-account access
* credential harvesting
* leaked datasets
* stolen credentials
* authentication bypass
* access-control circumvention
* unauthorized private information collection

The discovery layer operates only against approved public information sources.

---

# 14. Responsible Intelligence

DigitalDNA intentionally distinguishes between:

```text
Observed fact
      ↓
Extracted claim
      ↓
Correlated evidence
      ↓
Identity hypothesis
```

An AI-generated conclusion is never treated as equivalent to a verified fact.

Where evidence is insufficient, the system reports uncertainty.

Where sources conflict, the conflict is surfaced.

Where identity association is weak, the system does not present it as established.

---

# 15. External Research & Components

DigitalDNA builds on established research and open-source infrastructure where appropriate.

Public discovery mechanisms can provide candidate profiles and source material.

Entity-resolution research provides methods for comparing fragmented records.

Graph technologies provide a structure for representing relationships and provenance.

These components are **not the DigitalDNA product**.

They are replaceable infrastructure surrounding the core intelligence pipeline:

```text
Discovery
    ↓
Entity Extraction
    ↓
Identity Resolution
    ↓
Evidence Correlation
    ↓
Conflict Analysis
    ↓
Intelligence Graph
```

---

# 16. Current Development Status

### Core

* [ ] Investigation model
* [ ] Entity schema
* [ ] Evidence schema
* [ ] Relationship schema

### Resolution

* [ ] Name matching
* [ ] Username matching
* [ ] Organization matching
* [ ] Semantic matching
* [ ] Cross-source scoring

### Intelligence

* [ ] Entity extraction
* [ ] Evidence aggregation
* [ ] Conflict detection
* [ ] Timeline generation

### Graph

* [ ] Entity graph
* [ ] Relationship graph
* [ ] Evidence-linked edges
* [ ] Interactive visualization

### Interface

* [ ] Investigation creation
* [ ] Candidate comparison
* [ ] Graph workspace
* [ ] Evidence panel
* [ ] Timeline
* [ ] Intelligence report

---

# 17. Vision

The public web contains thousands of disconnected fragments describing the same people.

DigitalDNA turns those fragments into a structured, explainable intelligence model.

> **We don't just find profiles.**
>
> **We resolve identities through evidence.**

---

## Team

### Cypher

**NEURAX Hackathon 3.0**

**Domain:** AI in Cybersecurity

**Problem:** Public Profile & Digital Footprint Intelligence
