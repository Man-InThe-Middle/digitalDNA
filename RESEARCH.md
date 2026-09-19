# # DigitalDNA — Research & Technical Approach

**Team:** Cypher
**Hackathon:** DigitalDNA Hackathon 3.0
**Domain:** AI in Cybersecurity

---

# 1. Research Objective

The central research question behind DigitalDNA is:

> **How can fragmented public information be correlated into a defensible identity model without treating weak similarity signals as proof?**

The problem combines several technical areas:

1. Public-source discovery
2. Entity extraction
3. Entity resolution
4. Record linkage
5. Evidence/provenance management
6. Knowledge graphs
7. Conflict detection
8. Temporal reasoning
9. Human-in-the-loop verification

The project therefore treats identity intelligence as an **evidence correlation problem**, rather than simply a search problem.

---

# 2. Why Generic OSINT Search Is Insufficient

Traditional username enumeration answers:

> "Does this username appear on this website?"

That is useful for discovery but insufficient for identity resolution.

Consider:

```text
Rahul Sharma
rahul_dev
rahulsharma23
rsharma
```

These may belong to:

* one person
* multiple people
* unrelated accounts

A discovery engine cannot safely resolve this by username similarity alone.

The system therefore requires a second layer:

```text
Discovery
    ↓
Candidate Records
    ↓
Entity Resolution
    ↓
Evidence Verification
```

---

# 3. Research Area: Entity Resolution

Entity resolution attempts to determine whether records from different datasets refer to the same real-world entity.

The classical problem can be represented as:

```text
Record A ──────?
                │
                ├── SAME ENTITY
                │
Record B ──────?
```

For DigitalDNA:

```text
LinkedIn Profile
        │
        ?
        │
GitHub Profile
```

The decision should depend on multiple attributes rather than a single exact match.

Relevant signals include:

* names
* aliases
* usernames
* organizations
* locations
* biographies
* URLs
* projects
* events
* timestamps

---

# 4. Multi-Signal Resolution

DigitalDNA uses a multi-signal approach.

A simplified conceptual score is:

```text
S =
w₁(Name)
+ w₂(Username)
+ w₃(Organization)
+ w₄(Location)
+ w₅(Semantic Similarity)
+ w₆(Cross-Link)
+ w₇(Project/Event Overlap)
```

The weights are configurable.

The important architectural principle is:

> **No individual weak signal should automatically establish identity.**

For example:

```text
Same name
+
Same city
```

is weaker than:

```text
Same name
+
Same organization
+
Personal website links GitHub
+
GitHub links personal website
+
Same project
```

---

# 5. Evidence Independence

An important consideration is whether multiple signals actually represent independent evidence.

For example:

```text
LinkedIn
    │
    └── Website URL
             │
             └── GitHub
```

These three pages do not necessarily represent three independent confirmations.

They may all originate from the same self-published information.

Therefore DigitalDNA records source relationships and provenance instead of simply counting URLs.

---

# 6. Provenance

A relationship should retain its source.

Conceptually:

```text
ENTITY A
   │
   │ relationship
   │
   ▼
ENTITY B

Evidence:
- Source URL
- Source type
- Extracted statement
- Observation timestamp
- Extraction method
- Confidence
```

This makes the system auditable.

The current OpenOSINT graph architecture provides a useful open-source reference for statement-level provenance, append-only graph storage and human review of potential `same_as` relationships.

DigitalDNA adopts the **architectural principle** of provenance-aware resolution rather than treating an external graph implementation as the application's identity engine.

---

# 7. Research Area: Knowledge Graphs

A knowledge graph represents entities and relationships explicitly.

Example:

```text
(Person)
Rahul Sharma
     │
     ├── WORKS_AT ──► XYZ Labs
     │
     ├── CREATED ───► Project X
     │
     ├── PARTICIPATED_IN ──► ABC Hackathon
     │
     └── POSSIBLE_IDENTITY ──► GitHub Account
```

This representation enables:

* graph traversal
* relationship inspection
* evidence attachment
* timeline construction
* conflict detection
* candidate comparison

---

# 8. Research Area: Temporal Reasoning

Identity information changes over time.

A person can:

```text
2023 → Student
2024 → Engineer
2025 → Founder
2026 → Advisor
```

Therefore a relationship should not necessarily be represented as an eternal fact.

Instead:

```text
WORKS_AT
Person → Company

Valid:
2024-06 → 2025-08
```

Timeline information can therefore become an additional identity-resolution signal.

For example, a conference profile claiming someone worked at Company X in 2024 provides stronger evidence for a candidate who has matching Company X affiliation during the same period.

---

# 9. Conflict Detection

Conflict is not necessarily an error.

Different sources may describe different points in time.

Example:

```text
2024:
Company A

2026:
Company B
```

This is not necessarily contradictory.

However:

```text
LinkedIn:
Founder — Company A

Company A website:
Founder — Person B
```

requires investigation.

DigitalDNA therefore distinguishes:

```text
Temporal difference
        ≠
Logical conflict
```

---

# 10. Discovery Architecture

Public discovery mechanisms are treated as adapters.

```text
                  Discovery Interface
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Search API     Username DB    Public Pages
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Normalized Records
```

The resolution layer does not depend on one particular discovery provider.

This allows the discovery subsystem to evolve independently.

---

# 11. Open-Source Research

Several open-source projects were examined for architectural ideas.

## OpenOSINT

OpenOSINT provides an OSINT agent architecture and, in its graph module, statement-level provenance, entity graphs and human review for candidate identity relationships.

**Research takeaway:**

Provenance and review should be part of the data model rather than added as an afterthought.

---

## Maigret

Maigret provides large-scale username discovery and profile information extraction across thousands of public sites. It can also perform recursive discovery from discovered identifiers.

**Research takeaway:**

Large-scale discovery is best treated as a candidate-generation layer.

DigitalDNA does not equate:

```text
username found
```

with:

```text
identity confirmed
```

---

## Entity Resolution Graph OSINT

An open-source project demonstrates a localized AI-driven entity-resolution pipeline combining structured extraction, entity resolution and graph storage.

**Research takeaway:**

Local models and graph-based entity resolution can be combined to reduce dependency on external AI services.

---

# 12. Why DigitalDNA Is Different

The system is not intended to be:

```text
Search → scrape → summarize
```

Instead:

```text
Search
  ↓
Discover
  ↓
Normalize
  ↓
Extract
  ↓
Generate Candidates
  ↓
Resolve
  ↓
Correlate Evidence
  ↓
Detect Conflicts
  ↓
Build Graph
  ↓
Explain Result
```

The central engineering contribution is the **resolution and evidence layer**.

External discovery mechanisms provide raw material.

DigitalDNA determines how those fragments relate.

---

# 13. Human-in-the-Loop Design

Fully automatic identity resolution can produce false associations.

DigitalDNA therefore supports human review.

A candidate relationship can be presented as:

```text
Candidate Relationship

Person A
     ↓
Possible identity
     ↓
Account B

Supporting Evidence
✓ Same organization
✓ Website cross-link
✓ Same project

Conflicting Evidence
⚠ Different location

System Status
PROBABLE

[ ACCEPT ] [ REJECT ] [ REVIEW ]
```

This makes the system useful for investigation without requiring blind trust in an AI output.

---

# 14. Confidence Semantics

One important design decision is to avoid presenting every numerical score as a probability.

A score produced by a rule-based resolver means:

> "How strongly do our configured matching rules support this association?"

It does not automatically mean:

> "There is an X% probability that these are the same person."

This distinction is also emphasized in OpenOSINT's current graph documentation, which separates heuristic extractor confidence, resolution scores and review thresholds.

DigitalDNA therefore uses semantic statuses alongside numerical scores.

---

# 15. Security Model

The system is designed around authorized public information.

The following are outside the intended system boundary:

```text
Private accounts
Credential theft
Leaked datasets
Authentication bypass
Access-control bypass
Unauthorized private information
```

The architecture assumes that the input subject and investigation scope have been authorized by the organizer.

---

# 16. Research Hypothesis

The project's working hypothesis is:

> **Identity resolution accuracy can be improved by combining heterogeneous, provenance-aware public evidence instead of relying primarily on name or username similarity.**

The system can evaluate this hypothesis by comparing:

### Baseline

```text
Name / Username Match
```

against:

### DigitalDNA

```text
Name
+
Username
+
Organization
+
Location
+
Semantic Similarity
+
Cross-Links
+
Project/Event Overlap
+
Temporal Consistency
+
Source Evidence
```

---

# 17. Evaluation Metrics

The prototype can be evaluated using:

### Identity Precision

How many resolved identity relationships are correct?

### Identity Recall

How many relevant relationships are successfully discovered?

### Evidence Coverage

What proportion of material claims have supporting evidence?

### Conflict Detection

How many known inconsistencies are surfaced?

### False Association Rate

How frequently does the system incorrectly merge unrelated identities?

### Review Efficiency

How much investigation work can be reduced by presenting ranked candidates and supporting evidence?

---

# 18. Expected Outcome

The final system should produce:

1. Candidate identities
2. Public profiles
3. Organizations and affiliations
4. Projects and products
5. Events and participation
6. Publications and contributions
7. Timeline
8. Identity graph
9. Evidence for material claims
10. Confidence and uncertainty
11. Conflicting information
12. Human-reviewable conclusions

---

# 19. Conclusion

DigitalDNA treats public digital footprint intelligence as an **entity-resolution and evidence-correlation problem**.

The objective is not to collect the maximum number of pages.

The objective is to construct the most defensible relationship between fragmented public records while preserving:

* provenance
* uncertainty
* temporal context
* conflicting evidence
* human review

The resulting system is intended to answer not merely:

> **"What did we find?"**

but:

> **"What do we believe is connected, why do we believe it, and what evidence supports that conclusion?"**

---

## References

* OpenOSINT — graph architecture and provenance research.
* OpenOSINT — current graph/review implementation and changelog.
* Maigret — public username discovery and profile extraction.
* Entity Resolution Graph OSINT — graph-based AI entity resolution reference implementation.
 — Research & Technical Approach

**Team:** Cypher
**Hackathon:** DigitalDNA Hackathon 3.0
**Domain:** AI in Cybersecurity

---

# 1. Research Objective

The central research question behind DigitalDNA is:

> **How can fragmented public information be correlated into a defensible identity model without treating weak similarity signals as proof?**

The problem combines several technical areas:

1. Public-source discovery
2. Entity extraction
3. Entity resolution
4. Record linkage
5. Evidence/provenance management
6. Knowledge graphs
7. Conflict detection
8. Temporal reasoning
9. Human-in-the-loop verification

The project therefore treats identity intelligence as an **evidence correlation problem**, rather than simply a search problem.

---

# 2. Why Generic OSINT Search Is Insufficient

Traditional username enumeration answers:

> "Does this username appear on this website?"

That is useful for discovery but insufficient for identity resolution.

Consider:

```text
Rahul Sharma
rahul_dev
rahulsharma23
rsharma
```

These may belong to:

* one person
* multiple people
* unrelated accounts

A discovery engine cannot safely resolve this by username similarity alone.

The system therefore requires a second layer:

```text
Discovery
    ↓
Candidate Records
    ↓
Entity Resolution
    ↓
Evidence Verification
```

---

# 3. Research Area: Entity Resolution

Entity resolution attempts to determine whether records from different datasets refer to the same real-world entity.

The classical problem can be represented as:

```text
Record A ──────?
                │
                ├── SAME ENTITY
                │
Record B ──────?
```

For DigitalDNA:

```text
LinkedIn Profile
        │
        ?
        │
GitHub Profile
```

The decision should depend on multiple attributes rather than a single exact match.

Relevant signals include:

* names
* aliases
* usernames
* organizations
* locations
* biographies
* URLs
* projects
* events
* timestamps

---

# 4. Multi-Signal Resolution

DigitalDNA uses a multi-signal approach.

A simplified conceptual score is:

```text
S =
w₁(Name)
+ w₂(Username)
+ w₃(Organization)
+ w₄(Location)
+ w₅(Semantic Similarity)
+ w₆(Cross-Link)
+ w₇(Project/Event Overlap)
```

The weights are configurable.

The important architectural principle is:

> **No individual weak signal should automatically establish identity.**

For example:

```text
Same name
+
Same city
```

is weaker than:

```text
Same name
+
Same organization
+
Personal website links GitHub
+
GitHub links personal website
+
Same project
```

---

# 5. Evidence Independence

An important consideration is whether multiple signals actually represent independent evidence.

For example:

```text
LinkedIn
    │
    └── Website URL
             │
             └── GitHub
```

These three pages do not necessarily represent three independent confirmations.

They may all originate from the same self-published information.

Therefore DigitalDNA records source relationships and provenance instead of simply counting URLs.

---

# 6. Provenance

A relationship should retain its source.

Conceptually:

```text
ENTITY A
   │
   │ relationship
   │
   ▼
ENTITY B

Evidence:
- Source URL
- Source type
- Extracted statement
- Observation timestamp
- Extraction method
- Confidence
```

This makes the system auditable.

The current OpenOSINT graph architecture provides a useful open-source reference for statement-level provenance, append-only graph storage and human review of potential `same_as` relationships.

DigitalDNA adopts the **architectural principle** of provenance-aware resolution rather than treating an external graph implementation as the application's identity engine.

---

# 7. Research Area: Knowledge Graphs

A knowledge graph represents entities and relationships explicitly.

Example:

```text
(Person)
Rahul Sharma
     │
     ├── WORKS_AT ──► XYZ Labs
     │
     ├── CREATED ───► Project X
     │
     ├── PARTICIPATED_IN ──► ABC Hackathon
     │
     └── POSSIBLE_IDENTITY ──► GitHub Account
```

This representation enables:

* graph traversal
* relationship inspection
* evidence attachment
* timeline construction
* conflict detection
* candidate comparison

---

# 8. Research Area: Temporal Reasoning

Identity information changes over time.

A person can:

```text
2023 → Student
2024 → Engineer
2025 → Founder
2026 → Advisor
```

Therefore a relationship should not necessarily be represented as an eternal fact.

Instead:

```text
WORKS_AT
Person → Company

Valid:
2024-06 → 2025-08
```

Timeline information can therefore become an additional identity-resolution signal.

For example, a conference profile claiming someone worked at Company X in 2024 provides stronger evidence for a candidate who has matching Company X affiliation during the same period.

---

# 9. Conflict Detection

Conflict is not necessarily an error.

Different sources may describe different points in time.

Example:

```text
2024:
Company A

2026:
Company B
```

This is not necessarily contradictory.

However:

```text
LinkedIn:
Founder — Company A

Company A website:
Founder — Person B
```

requires investigation.

DigitalDNA therefore distinguishes:

```text
Temporal difference
        ≠
Logical conflict
```

---

# 10. Discovery Architecture

Public discovery mechanisms are treated as adapters.

```text
                  Discovery Interface
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Search API     Username DB    Public Pages
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Normalized Records
```

The resolution layer does not depend on one particular discovery provider.

This allows the discovery subsystem to evolve independently.

---

# 11. Open-Source Research

Several open-source projects were examined for architectural ideas.

## OpenOSINT

OpenOSINT provides an OSINT agent architecture and, in its graph module, statement-level provenance, entity graphs and human review for candidate identity relationships.

**Research takeaway:**

Provenance and review should be part of the data model rather than added as an afterthought.

---

## Maigret

Maigret provides large-scale username discovery and profile information extraction across thousands of public sites. It can also perform recursive discovery from discovered identifiers.

**Research takeaway:**

Large-scale discovery is best treated as a candidate-generation layer.

DigitalDNA does not equate:

```text
username found
```

with:

```text
identity confirmed
```

---

## Entity Resolution Graph OSINT

An open-source project demonstrates a localized AI-driven entity-resolution pipeline combining structured extraction, entity resolution and graph storage.

**Research takeaway:**

Local models and graph-based entity resolution can be combined to reduce dependency on external AI services.

---

# 12. Why DigitalDNA Is Different

The system is not intended to be:

```text
Search → scrape → summarize
```

Instead:

```text
Search
  ↓
Discover
  ↓
Normalize
  ↓
Extract
  ↓
Generate Candidates
  ↓
Resolve
  ↓
Correlate Evidence
  ↓
Detect Conflicts
  ↓
Build Graph
  ↓
Explain Result
```

The central engineering contribution is the **resolution and evidence layer**.

External discovery mechanisms provide raw material.

DigitalDNA determines how those fragments relate.

---

# 13. Human-in-the-Loop Design

Fully automatic identity resolution can produce false associations.

DigitalDNA therefore supports human review.

A candidate relationship can be presented as:

```text
Candidate Relationship

Person A
     ↓
Possible identity
     ↓
Account B

Supporting Evidence
✓ Same organization
✓ Website cross-link
✓ Same project

Conflicting Evidence
⚠ Different location

System Status
PROBABLE

[ ACCEPT ] [ REJECT ] [ REVIEW ]
```

This makes the system useful for investigation without requiring blind trust in an AI output.

---

# 14. Confidence Semantics

One important design decision is to avoid presenting every numerical score as a probability.

A score produced by a rule-based resolver means:

> "How strongly do our configured matching rules support this association?"

It does not automatically mean:

> "There is an X% probability that these are the same person."

This distinction is also emphasized in OpenOSINT's current graph documentation, which separates heuristic extractor confidence, resolution scores and review thresholds.

DigitalDNA therefore uses semantic statuses alongside numerical scores.

---

# 15. Security Model

The system is designed around authorized public information.

The following are outside the intended system boundary:

```text
Private accounts
Credential theft
Leaked datasets
Authentication bypass
Access-control bypass
Unauthorized private information
```

The architecture assumes that the input subject and investigation scope have been authorized by the organizer.

---

# 16. Research Hypothesis

The project's working hypothesis is:

> **Identity resolution accuracy can be improved by combining heterogeneous, provenance-aware public evidence instead of relying primarily on name or username similarity.**

The system can evaluate this hypothesis by comparing:

### Baseline

```text
Name / Username Match
```

against:

### DigitalDNA

```text
Name
+
Username
+
Organization
+
Location
+
Semantic Similarity
+
Cross-Links
+
Project/Event Overlap
+
Temporal Consistency
+
Source Evidence
```

---

# 17. Evaluation Metrics

The prototype can be evaluated using:

### Identity Precision

How many resolved identity relationships are correct?

### Identity Recall

How many relevant relationships are successfully discovered?

### Evidence Coverage

What proportion of material claims have supporting evidence?

### Conflict Detection

How many known inconsistencies are surfaced?

### False Association Rate

How frequently does the system incorrectly merge unrelated identities?

### Review Efficiency

How much investigation work can be reduced by presenting ranked candidates and supporting evidence?

---

# 18. Expected Outcome

The final system should produce:

1. Candidate identities
2. Public profiles
3. Organizations and affiliations
4. Projects and products
5. Events and participation
6. Publications and contributions
7. Timeline
8. Identity graph
9. Evidence for material claims
10. Confidence and uncertainty
11. Conflicting information
12. Human-reviewable conclusions

---

# 19. Conclusion

DigitalDNA treats public digital footprint intelligence as an **entity-resolution and evidence-correlation problem**.

The objective is not to collect the maximum number of pages.

The objective is to construct the most defensible relationship between fragmented public records while preserving:

* provenance
* uncertainty
* temporal context
* conflicting evidence
* human review

The resulting system is intended to answer not merely:

> **"What did we find?"**

but:

> **"What do we believe is connected, why do we believe it, and what evidence supports that conclusion?"**

---

## References

* OpenOSINT — graph architecture and provenance research.
* OpenOSINT — current graph/review implementation and changelog.
* Maigret — public username discovery and profile extraction.
* Entity Resolution Graph OSINT — graph-based AI entity resolution reference implementation.
