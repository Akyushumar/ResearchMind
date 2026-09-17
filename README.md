# ResearchMind

> **Regulatory Intelligence Infrastructure for Evidence-Grounded Research, Reasoning, and Decision Support**

ResearchMind is a research and regulatory intelligence platform designed to move beyond conventional RAG systems.

Instead of treating regulations as unstructured documents that are simply chunked, embedded, and passed to an LLM, ResearchMind models regulatory knowledge as **structured, traceable, and verifiable information**.

The system combines:

- Structure-aware document ingestion
- Hybrid lexical + semantic retrieval
- Regulatory evidence and provenance
- Structured regulatory facts
- Applicability conditions and exceptions
- Deterministic numerical rule evaluation
- Bounded relationship traversal
- Agentic reasoning and orchestration
- Citation and grounding validation
- Version and amendment intelligence
- Multi-jurisdiction regulatory knowledge

The initial domain is **architectural development control regulations (DCRs)**, with the architecture designed to generalize to other regulatory and technical knowledge domains.

---

## Aim

The aim of ResearchMind is to build an **evidence-grounded regulatory intelligence layer** that can transform complex regulatory documents into structured knowledge and use that knowledge to answer real-world questions with traceable evidence.

The long-term system should be able to answer questions such as:

> "Can this building satisfy the applicable parking requirements?"

not merely by retrieving a paragraph, but by determining:

1. Which regulation applies
2. Which clauses govern the case
3. What conditions and exceptions apply
4. Which numerical parameters are relevant
5. Which referenced clauses or tables must be followed
6. What calculations are required
7. Whether the available evidence is sufficient
8. Which source clauses support the conclusion
9. Where uncertainty or conflict remains

The core principle is:

> **The regulatory source remains the source of truth. The LLM interprets, orchestrates, and synthesizes. Deterministic systems handle rules, calculations, conditions, provenance, and validation wherever possible.**

---

# Why ResearchMind?

A conventional regulatory RAG pipeline often looks like:

```text
PDF
 ↓
Text Extraction
 ↓
Chunks
 ↓
Embeddings
 ↓
Vector Search
 ↓
LLM
 ↓
Answer

This works reasonably well for document search, but regulatory reasoning introduces additional problems:

* Hierarchical clauses
* Definitions and cross-references
* Applicability conditions
* Exceptions and exemptions
* Numerical requirements
* Tables
* Formulas
* Version differences
* Amendments
* Conflicting provisions
* Missing evidence
* Citation integrity
* Unsupported conclusions

ResearchMind therefore follows a different architecture:

```text
USER QUERY
    ↓
QUERY / AGENT ORCHESTRATION
    ↓
RETRIEVAL
    ↓
REGULATORY EVIDENCE
    ↓
STRUCTURED REGULATORY FACTS
    ↓
APPLICABILITY & CONDITIONS
    ↓
DETERMINISTIC RULE EVALUATION
    ↓
RELATIONSHIP TRAVERSAL
    ↓
REASONING SYNTHESIS
    ↓
VALIDATION
    ↓
GROUNDED ANSWER + CITATIONS
```

---

# Design Philosophy

## 1. Regulations are the source of truth

The system should never treat the LLM's generated knowledge as authoritative regulatory information.

Every substantive conclusion should be traceable to regulatory evidence.

## 2. Deterministic wherever possible

Rules, calculations, applicability conditions, provenance, and validation should be implemented deterministically where practical.

LLMs should not be used as calculators or unrestricted rule engines.

## 3. Evidence before reasoning

The system first establishes the relevant evidence and structured facts before attempting reasoning.

```text
Evidence → Facts → Conditions → Rules → Reasoning → Answer
```

rather than:

```text
Question → LLM intuition → Answer
```

## 4. Preserve uncertainty

If the evidence is incomplete or contradictory, the system should represent that explicitly.

Unknown should remain unknown.

## 5. Bounded agent behaviour

Agents operate through a controlled tool registry and execution budget.

The system does not allow unrestricted recursive agents or arbitrary code execution.

## 6. Verifiable reasoning

ResearchMind does not attempt to expose private chain-of-thought.

Instead, it produces externally verifiable structured reasoning records containing:

* Source facts
* Derived facts
* Interpretations
* Assumptions
* Unknowns
* Conflicts
* Evidence references
* Deterministic operation traces

---

# Current Architecture

```text
                         ┌──────────────────┐
                         │    User Query    │
                         └────────┬─────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │ Query Understanding │
                       │  / Agent Control    │
                       └──────────┬──────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   Hybrid Retrieval       │
                    │                          │
                    │ PostgreSQL FTS           │
                    │ Qdrant Semantic Search   │
                    │ RRF Fusion               │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Regulatory Evidence    │
                    │                          │
                    │ Clause + Page + Source   │
                    │ + Provenance + Metadata  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Structured Regulatory    │
                    │ Facts & Parameters       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Applicability &          │
                    │ Boolean Conditions       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Deterministic Rule       │
                    │ Evaluation               │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Bounded Relationship     │
                    │ Traversal                │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Reasoning Synthesis      │
                    │ + Validation             │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Grounded Answer          │
                    │ + Citations              │
                    │ + Confidence             │
                    └──────────────────────────┘
```

---

# Technology Stack

| Layer                  | Technology                   |
| ---------------------- | ---------------------------- |
| Language               | Python                       |
| API                    | FastAPI                      |
| ORM                    | SQLAlchemy                   |
| Database               | PostgreSQL                   |
| Migrations             | Alembic                      |
| Validation             | Pydantic                     |
| PDF Processing         | PyMuPDF                      |
| Lexical Search         | PostgreSQL Full-Text Search  |
| Semantic Search        | Qdrant                       |
| Retrieval Fusion       | Reciprocal Rank Fusion       |
| LLM Provider           | Provider abstraction         |
| Primary External LLM   | Gemini / Vertex AI           |
| Optional LLM Providers | OpenAI, Ollama               |
| Embeddings             | Provider abstraction         |
| Frontend               | Next.js + React + TypeScript |
| Styling                | Tailwind CSS                 |
| Testing                | pytest / pytest-asyncio      |
| Infrastructure         | Docker Compose               |
| Development            | Local-first                  |

---

# Regulatory Knowledge Model

ResearchMind models regulations using a hierarchy rather than treating documents as flat text.

```text
Jurisdiction
    │
    └── Regulatory Document
            │
            └── Document Version
                    │
                    ├── Amendment
                    │
                    └── Clauses
                            │
                            ├── Parent / Child Hierarchy
                            ├── Cross-References
                            ├── Applicability Conditions
                            ├── Regulatory Parameters
                            └── Evidence Chunks
```

Important entities include:

* `Jurisdiction`
* `RegulatoryDocument`
* `DocumentVersion`
* `Amendment`
* `Clause`
* `ClauseRelationship`
* `ApplicabilityCondition`
* `RegulatoryParameter`
* `EvidenceChunk`
* `IngestionJob`

---

# Development Roadmap

```text
PHASE 0
Foundation & Architecture
                    ✅ COMPLETE

PHASE 1A
Regulatory Structure Extraction
                    ✅ COMPLETE

PHASE 1B
Structure-Aware Retrieval Intelligence
                    ✅ COMPLETE

PHASE 1C
Regulatory QA / DCR Agent
                    ✅ RELEASED — v0.4.0

PHASE 2
Regulatory Intelligence & Reasoning
                    🚧 IN PROGRESS

    ├── 2A Regulatory Intelligence Contracts
    │                         ✅ COMPLETE
    │
    ├── 2B Deterministic Rule Evaluation
    │                         ⏳ NEXT
    │
    ├── 2C LLM-Assisted Fact Extraction
    │                         ⏳
    │
    ├── 2D Bounded Relationship Traversal
    │                         ⏳
    │
    ├── 2E Agent Orchestration
    │                         ⏳
    │
    └── 2F Evaluation
                              ⏳

PHASE 3
Temporal / Amendment / Version Intelligence
                    ⏳ PLANNED

PHASE 4
Multi-Jurisdiction + Regulatory Knowledge Graph
                    ⏳ PLANNED

PHASE 5
Production Platform + Large-Scale Evaluation
                    ⏳ PLANNED
```

---

# Completed Work

## Phase 0 — Foundation & Architecture

**Status: ✅ COMPLETE**

Established the initial ResearchMind architecture and development foundation.

Implemented:

* FastAPI application structure
* PostgreSQL data model
* SQLAlchemy ORM
* Alembic migrations
* Qdrant integration
* Docker Compose infrastructure
* Structured logging
* Provider abstraction
* Initial regulatory data model
* API health checks
* Jurisdiction APIs
* Regulatory document APIs
* Document version APIs
* Clause APIs
* Ingestion job APIs
* Initial test infrastructure

The regulatory model was designed around:

```text
RegulatoryDocument
        ↓
DocumentVersion
        ↓
Clauses
        ↓
Relationships
        ↓
Evidence
```

---

## Phase 1A — Regulatory Structure Extraction

**Status: ✅ COMPLETE**

Objective:

> Convert regulatory PDFs into a structured clause hierarchy while preserving source provenance.

Implemented:

* `ClauseNumberParser`
* `HeadingClassifier`
* `DCRStructureDetector`
* `DCRClauseExtractor`
* Relationship extraction
* Source page provenance
* Clause hierarchy
* Parent-child relationships
* Structure-aware ingestion
* Benchmark fixtures
* Regression tests

Initial controlled benchmark:

```text
Clause Recall: 91.67%
```

The first controlled corpus focused on **UDCPR 2020 Chapter 8: Parking**.

Release:

```text
v0.2.0-sprint1a
```

---

## Phase 1B — Structure-Aware Retrieval Intelligence

**Status: ✅ COMPLETE**

Implemented hybrid regulatory retrieval using:

```text
PostgreSQL FTS
      +
Qdrant Semantic Retrieval
      ↓
RRF Fusion
```

Features:

* Lexical retrieval
* Semantic retrieval
* Hybrid retrieval
* Metadata filtering
* Reciprocal Rank Fusion
* Structure-aware chunks
* Clause hierarchy context
* Evidence provenance
* Retrieval benchmarking
* Recall@1
* Recall@3
* Recall@5
* MRR

Provider abstractions were also introduced so embedding and LLM providers can be changed without redesigning the application.

Release:

```text
v0.3.0
```

---

## Phase 1C — Regulatory QA / DCR Agent

**Status: ✅ RELEASED — v0.4.0**

ResearchMind evolved from a retrieval system into a bounded regulatory QA agent.

Current agent tools include:

```text
search_regulations()
get_clause()
get_clause_children()
get_clause_relationships()
```

Agent execution is bounded using:

```text
MAX_TOOL_CALLS = 5
```

The agent architecture is:

```text
USER
 ↓
DCR AGENT
 ↓
TOOL SELECTION
 ├── search()
 ├── get_clause()
 └── relationships()
 ↓
EVIDENCE SET
 ↓
GROUNDED LLM
 ↓
GROUNDING VALIDATION
 ├── PASS → Answer + Citations
 └── FAIL → Insufficient Evidence
```

Implemented:

* Manual tool execution
* Tool registry
* Canonical evidence schema
* Evidence caching
* Citation validation
* Grounding validation
* Unsupported citation rejection
* Insufficient-evidence fallback
* Confidence representation
* Debug execution traces
* QA API endpoint

Release:

```text
v0.4.0
```

`v0.4.0` is the immutable Phase 1C baseline.

---

# Phase 2A — Regulatory Intelligence Contracts

**Status: ✅ COMPLETE**

Phase 2 introduces explicit representations for regulatory reasoning.

## Regulatory Parameters

Regulatory numerical requirements are represented using structured parameters:

```text
RegulatoryParameter
├── parameter_name
├── value_type
├── base_value
├── unit
├── rounding_behavior
├── formula_ast
├── validation_status
├── extraction_method
└── provenance
```

Supported value types include:

```text
numeric
percentage
formula
```

---

## Applicability Conditions

The previous flat applicability model was replaced with a recursive Boolean condition tree.

```text
ApplicabilityCondition
        │
        ├── AND
        │    ├── height >= 15m
        │    └── occupancy = residential
        │
        ├── OR
        │
        ├── NOT
        │
        └── LEAF
```

Condition states:

```text
TRUE
FALSE
UNKNOWN
```

This allows the system to represent incomplete information rather than forcing binary conclusions.

---

## Typed Formula AST

Numerical rules are represented using a typed Abstract Syntax Tree.

Conceptually:

```text
AST
├── Constant
├── Variable
├── BinaryOperation
└── UnaryOperation
```

The architecture deliberately avoids:

```text
eval()
exec()
LLM-generated executable code
```

The objective is to make numerical reasoning deterministic and auditable.

---

# Current Milestone — L2 Real Corpus Ingestion

**Status: 🚧 ACTIVE HARDENING**

The project is transitioning from a small controlled corpus to a real UDCPR corpus:

```text
data/corpus/UDCPR_compressed_2.pdf
```

Corpus scale:

```text
~492 pages
~1.06M characters
~9,600 source text blocks
```

The purpose of L2 is not simply to increase document size.

The goal is to establish that the ingestion pipeline can preserve meaningful regulatory information from a real-world document without silently losing or corrupting source content.

---

# L2 Validation

Current validation focuses on:

### Source Preservation

```text
PDF block
   ↓
Detected structure
   ↓
Clause
   ↓
Chunk
```

Every substantive source block should be traceable through this pipeline.

### Structural Integrity

Validate:

* Clause hierarchy
* Parent-child relationships
* Decimal clauses
* Lettered clauses
* Roman-numbered clauses
* Notes
* Provisos
* Tables

### Page Number Detection

Standalone page numbers must not become regulatory clauses.

### Chunk Integrity

Check for:

* Missing content
* Duplicate content
* Incorrect clause association
* Front-matter bleed
* Broken hierarchy context
* Excessive fragmentation

### Table Handling

Tables require special treatment because flattened PDF text can destroy:

* Row relationships
* Column relationships
* Headers
* Units
* Cell associations

Table handling is therefore being validated independently rather than assuming that text extraction is sufficient.

---

# Ingestion Review UI

An internal diagnostic interface is being developed at:

```text
/ingestion
```

It is intended as an engineering validation instrument rather than the final ResearchMind product interface.

Current sections include:

```text
Corpus Overview
Clause Explorer
Chunk Explorer
Table Inspector
Validation Gate
```

The purpose is to allow inspection of the extracted regulatory structure before the corpus is trusted for downstream retrieval and reasoning.

---

# Current L2 Gate

```text
L2 REAL CORPUS
       │
       ├── Source preservation       🚧
       ├── Hierarchy integrity      🚧
       ├── Page-number filtering    🚧
       ├── Clause → chunk trace     🚧
       ├── Empty-node audit         🚧
       └── Table 8B reconstruction   🚧
       
       ↓

       NOT READY
```

The current development priority is to resolve ingestion correctness before using the real corpus for substantive retrieval benchmarking.

A larger corpus is not useful if the ingestion layer silently corrupts the information being retrieved.

---

# Next Steps

## Phase 2B — Deterministic Rule Evaluation

**Next major implementation milestone.**

Objective:

> Evaluate regulatory rules deterministically using structured parameters, conditions, and typed formula ASTs.

Target architecture:

```text
Regulatory Evidence
        ↓
Structured Facts
        ↓
Applicability Conditions
        ↓
Rule / Formula AST
        ↓
Deterministic Evaluation
        ↓
Evaluation Result
        ↓
Provenance + Operation Trace
```

The LLM should provide variable mapping and reasoning orchestration, while the deterministic engine performs the actual calculation.

---

## Phase 2C — LLM-Assisted Fact Extraction

The LLM will be used for candidate fact extraction from regulatory text.

However:

```text
LLM Extraction
      ↓
Validation
      ↓
Structured Fact
```

rather than:

```text
LLM
 ↓
Unverified Fact
 ↓
Answer
```

Every extracted fact should retain:

* Source clause
* Page number
* Exact source text
* Extraction method
* Validation status

---

## Phase 2D — Bounded Relationship Traversal

Regulations frequently reference other clauses.

ResearchMind will support bounded traversal:

```text
Clause A
   ↓
REFERS_TO
   ↓
Clause B
   ↓
REFERS_TO
   ↓
Clause C
```

Traversal will use:

* Configurable depth
* Maximum traversal budget
* Visited-node tracking
* Cycle prevention
* Relationship traces

Default target depth:

```text
MAX_RELATIONSHIP_DEPTH = 2
```

with a hard maximum of 3.

---

## Phase 2E — Agent Orchestration

The agent will combine:

```text
Retrieval
+
Fact Extraction
+
Applicability
+
Rule Evaluation
+
Relationship Traversal
+
Reasoning Synthesis
+
Validation
```

The objective is to create an agent that can perform multi-step regulatory investigations while remaining bounded and auditable.

---

## Phase 2F — Evaluation

Evaluation will move beyond retrieval metrics.

Planned evaluation dimensions include:

* Fact extraction accuracy
* Applicability accuracy
* Numerical calculation correctness
* Cross-reference resolution
* Unsupported claim detection
* Citation correctness
* Grounding
* Insufficient-evidence handling
* Conflict detection
* End-to-end regulatory QA

The evaluation framework will distinguish between:

```text
Retrieval failure
Extraction failure
Applicability failure
Calculation failure
Reasoning failure
Citation failure
```

rather than reducing everything to a single score.

---

# Future Roadmap

## Phase 3 — Temporal & Amendment Intelligence

Planned capabilities:

* Document versions
* Amendments
* Effective dates
* Superseded provisions
* Historical queries
* Temporal applicability
* Amendment-aware retrieval

Target capability:

> Determine not only what a regulation says, but which version of the regulation applies to a particular point in time.

---

## Phase 4 — Multi-Jurisdiction & Regulatory Knowledge Graph

Planned expansion:

```text
Jurisdiction
     │
     ├── National
     ├── State
     ├── Regional
     ├── Municipal
     └── Institutional
```

Knowledge graph capabilities will connect:

```text
Clauses
Rules
Parameters
Definitions
Exceptions
Authorities
Jurisdictions
Documents
Amendments
Cross-References
```

This will allow regulatory relationships to be queried across jurisdictions.

---

## Phase 5 — Production Platform

Long-term objectives include:

* Production-grade APIs
* Authentication and authorization
* Large-scale document ingestion
* Observability
* Evaluation dashboards
* Corpus management
* Version management
* Regulatory change detection
* Multi-user research workflows
* Scalable retrieval infrastructure
* Production deployment

---

# Cost & Infrastructure Philosophy

ResearchMind is intentionally being developed using a **local-first and cost-conscious architecture**.

Priorities:

```text
1. Local execution
2. Open-source software
3. Free tiers
4. Provider abstraction
5. Paid APIs only when necessary
6. No recurring paid infrastructure during development
```

External APIs should remain replaceable.

Current provider architecture:

```text
BaseLLMProvider
├── GeminiLLMProvider
├── OpenAILLMProvider
└── OllamaLLMProvider
```

and:

```text
BaseEmbeddingProvider
├── GeminiEmbeddingProvider
├── OpenAIEmbeddingProvider
└── OllamaEmbeddingProvider
```

This allows experimentation without coupling ResearchMind to a single AI provider.

---

# Development Principles

ResearchMind follows several engineering principles.

### Evidence First

No evidence means no grounded regulatory conclusion.

### Deterministic Core

Calculations and rule evaluation should not depend on stochastic LLM behaviour.

### Explicit Provenance

Every important fact should be traceable to its source.

### Bounded Agents

Agent execution must have explicit limits.

### Structured Uncertainty

Unknown and conflicting evidence should be represented explicitly.

### Provider Independence

LLM and embedding providers should be replaceable.

### Regression Safety

Every major architectural change should be backed by automated tests.

### Real Corpus Before Real Claims

A benchmark is only meaningful when the underlying corpus has been validated.

---

# Current Status

```text
Foundation & Architecture             ✅ COMPLETE
Structural Extraction                 ✅ COMPLETE
Hybrid Retrieval                      ✅ COMPLETE
Regulatory QA Agent                   ✅ COMPLETE
Phase 2A Intelligence Contracts       ✅ COMPLETE
Vertex AI Integration                 ✅ COMPLETE
Real Corpus Ingestion                 🚧 HARDENING
Ingestion Review UI                   🚧 ACTIVE
Deterministic Rule Engine             ⏳ NEXT
Fact Extraction                       ⏳
Relationship Traversal                ⏳
Advanced Agent Orchestration          ⏳
Temporal Intelligence                 ⏳
Knowledge Graph                       ⏳
Production Platform                   ⏳
```

---

# Guiding Architecture

The central design boundary of ResearchMind is:

```text
                 LLM
        ┌────────────────────┐
        │ Interpret          │
        │ Orchestrate        │
        │ Extract candidates │
        │ Synthesize         │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │ Deterministic Core │
        │                    │
        │ Evidence           │
        │ Rules              │
        │ Conditions         │
        │ Calculations       │
        │ Provenance         │
        │ Validation         │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │ Regulatory Source  │
        │   = Source Truth   │
        └────────────────────┘
```

ResearchMind is ultimately intended to become more than a regulatory chatbot.

The long-term objective is to build **infrastructure for machines to reason over complex, changing, evidence-backed regulatory knowledge while keeping every important conclusion traceable to its source.**

---

# Repository Structure

```text
ResearchMind/
│
├── src/
│   └── researchmind/
│       ├── api/
│       ├── agents/
│       ├── ingestion/
│       ├── models/
│       ├── retrieval/
│       ├── providers/
│       ├── reasoning/
│       └── validation/
│
├── frontend/
│   └── src/
│       └── app/
│
├── data/
│   ├── benchmarks/
│   └── corpus/
│
├── docs/
│
├── tests/
│
├── alembic/
│
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# Project Releases

| Release           | Milestone                         | Status |
| ----------------- | --------------------------------- | ------ |
| `v0.2.0-sprint1a` | Regulatory Structure Extraction   | ✅      |
| `v0.3.0`          | Structure-Aware Retrieval         | ✅      |
| `v0.4.0`          | Regulatory QA / DCR Agent         | ✅      |
| Phase 2A          | Regulatory Intelligence Contracts | ✅      |
| Phase 2B          | Deterministic Rule Evaluation     | ⏳      |
| Phase 2C          | LLM-Assisted Fact Extraction      | ⏳      |
| Phase 2D          | Relationship Traversal            | ⏳      |
| Phase 2E          | Agent Orchestration               | ⏳      |
| Phase 2F          | Evaluation                        | ⏳      |

---

# Status

ResearchMind is currently in active development.

The immediate engineering priority is:

```text
L2 Corpus Hardening
        ↓
Real Corpus Retrieval Benchmark
        ↓
Phase 2B Deterministic Rule Evaluation
        ↓
Phase 2C–2F Regulatory Intelligence
```

The project deliberately prioritizes **correctness, provenance, reproducibility, and verifiability over premature feature expansion**.

