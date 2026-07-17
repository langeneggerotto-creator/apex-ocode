# OCODE Law Guardian and Policy Compiler v0.1

**Status:** DESIGNED_CANDIDATE__IMPLEMENTATION_REQUIRED  
**Scope:** OCODE and every APEX module that consumes Core OS laws, rules, principles, standards, controls, or temporary operating constraints  
**Truth boundary:** This document defines governance behavior. It does not prove the guardian, compiler, burden scoring, conflict detection, or runtime enforcement has been implemented or validated.

## 1. Purpose

OCODE must not become a blind enforcer that applies every law, rule, principle, checklist, and control to every task. That would create governance paralysis and make APEX harder to use than the risks it is intended to prevent.

OCODE therefore serves two linked roles:

1. **Universal Code and Execution Wrapper** — translate governed intent into target-language, platform, test, deployment, evidence, and handoff artifacts.
2. **Law Guardian and Policy Compiler** — identify the smallest applicable set of governance requirements needed for the actual task, risk, dreamer, environment, and lifecycle stage.

The guardian protects both sides:

- too little governance, which creates unsupported claims, unsafe execution, lost ownership, and unmaintainable systems;
- too much governance, which creates delay, confusion, excessive cost, duplicated work, and inability to make progress.

## 2. Governing meta-law

> **Governance must produce more verified protection and decision value than the burden it creates. OCODE must activate only the minimum sufficient, risk-proportionate, non-duplicative set of laws required for the current context, while preserving constitutional truth, safety, human control, evidence, ownership, and repairability.**

## 3. Law hierarchy

OCODE classifies every requirement before applying it.

| Tier | Class | Meaning | Default behavior |
|---|---|---|---|
| 0 | Constitutional invariants | Truth, human control, consent, safety, evidence, ownership, reversibility/repairability where applicable | Always active when relevant; cannot be silently disabled |
| 1 | Universal operating laws | Cross-project feasibility, readiness, maintainability, anti-paralysis, continuity | Activated by lifecycle and decision type |
| 2 | Domain laws | Software, medical, legal, financial, physical, data, security, research, learning, etc. | Activated only when the domain applies |
| 3 | Project and module rules | Local architecture, workflow, test, delivery, and interface constraints | Activated only inside declared scope |
| 4 | Temporary controls | Pilot, incident, migration, experiment, exception, or remediation rules | Must include owner and expiry/review date |
| 5 | Advisory principles | Heuristics, metaphors, book-derived lessons, optional best practices | Recommend; do not block unless promoted with evidence |

## 4. Policy compilation process

For every material task, OCODE compiles an **Active Law Set**:

```text
Task / dream / build request
→ identify outcome, risk, domain, lifecycle stage, authority, and affected parties
→ load constitutional invariants
→ activate only applicable universal and domain laws
→ load scoped project and temporary rules
→ detect duplicates, contradictions, obsolete rules, and unsupported candidates
→ estimate governance burden and risk reduction
→ simplify, merge, suspend, or escalate rules
→ produce the minimum executable control set
→ show the human what is active, why, and what is not active
→ execute, test, record evidence, and reassess
```

## 5. Required guardian functions

### 5.1 Applicability filter

A rule is active only when its trigger conditions match the current task, domain, risk, stage, and authority boundary.

### 5.2 Duplicate and overlap detector

Rules expressing the same required behavior must be merged into one executable control with traceability back to all source laws.

### 5.3 Conflict detector

Conflicting laws or controls must not be silently resolved. OCODE must apply declared precedence, expose the conflict, and escalate material unresolved conflicts for human decision.

### 5.4 Burden estimator

OCODE estimates the cost of compliance in time, money, cognitive load, delay, tooling, evidence collection, and maintenance.

### 5.5 Risk-reduction estimator

OCODE estimates the failure modes, severity, likelihood, reversibility, affected people, and evidence value addressed by each control.

### 5.6 Law compiler

High-level laws must compile into the smallest concrete behavior, field, test, gate, evidence record, or human decision necessary. A law that does not alter behavior is documentation, not enforcement.

### 5.7 Consolidation and retirement engine

OCODE proposes merging, simplifying, downgrading, suspending, or retiring laws that are duplicative, obsolete, ineffective, or disproportionately burdensome.

### 5.8 Human-visible active set

The dreamer, owner, or operator can inspect:

- active laws and why they apply;
- blocking versus advisory rules;
- controls generated from each law;
- estimated burden and risk reduction;
- conflicts and exceptions;
- suspended or non-applicable laws;
- review and appeal routes.

## 6. Governance burden rule

OCODE calculates a qualitative or quantitative governance value:

```text
Net Governance Value
=
Expected risk reduction
+ truth/evidence value
+ ownership/maintainability value
+ decision clarity
-
implementation cost
-
operating cost
-
cognitive burden
-
delay
-
duplication
```

A control with negative or unknown net governance value must be simplified, tested, time-bounded, downgraded to advisory status, or escalated for review unless it protects a constitutional invariant or a mandatory external requirement.

## 7. Rule admission gate

No new Core OS law should be promoted merely because it sounds wise. A candidate must identify:

1. the recurring failure mode it prevents;
2. the scope and trigger conditions;
3. the concrete behavior it changes;
4. the evidence or rationale supporting it;
5. its expected burden;
6. overlap with existing laws;
7. conflicts and precedence;
8. the smallest implementation mechanism;
9. test and effectiveness criteria;
10. owner and review/sunset condition.

## 8. Law economy rules

### Minimum Sufficient Governance Law

Use the smallest set of controls that adequately protects truth, people, ownership, evidence, feasibility, and recovery for the present risk.

### Risk-Proportional Governance Law

Governance burden must scale with severity, irreversibility, uncertainty, affected parties, cost, and authority—not with the number of available rules.

### No Rule Without a Failure Mode Law

A binding rule must name the material failure it prevents or the essential value it protects.

### No Duplicate Enforcement Law

Multiple laws may support one control, but the user should not be forced through repeated equivalent checks.

### Law-to-Behavior Compilation Law

A law is operational only when it compiles into an observable behavior, field, gate, test, evidence record, or approval.

### Review and Sunset Law

Temporary and project-specific rules require a review or expiry condition. Universal laws require periodic effectiveness and burden review.

### Governance Appeal Law

A human may challenge the applicability, burden, interpretation, or conflict of a rule. Constitutional invariants and mandatory external requirements cannot be bypassed silently; any exception must be explicit, evidenced, scoped, approved, and time-bounded.

## 9. Operating modes

| Mode | Intended use | Governance profile |
|---|---|---|
| Explore | Early ideation and learning | Minimal non-blocking rules; truth and safety still active |
| Prototype | Small reversible proof | Feasibility, ownership, evidence, cost, and stop rules |
| Build | Implement bounded capability | Requirements, tests, security, maintainability, continuity |
| Pilot | Real users or environment | Consent, privacy, support, monitoring, incident and evidence controls |
| Production | Sustained operation | Full applicable operational, security, legal, recovery, and maintenance controls |
| High-stakes | Medical, legal, financial, physical, safety-critical | Qualified authority, stronger evidence, explicit human approval and restricted autonomy |

The law set must change as the mode changes. Production controls must not automatically burden early exploration, and exploratory shortcuts must not silently survive into production.

## 10. OCODE outputs

Each governed operation should produce a compact policy receipt:

```text
Task:
Mode:
Risk tier:
Active constitutional laws:
Active universal/domain/project rules:
Compiled controls:
Blocking conditions:
Advisory guidance:
Rules merged or suppressed as duplicates:
Conflicts:
Exceptions:
Estimated governance burden:
Expected protection/value:
Human decision required:
Reassessment trigger:
Evidence location:
```

## 11. Acceptance tests

1. A low-risk reversible prototype does not receive the full production control set.
2. A high-stakes or irreversible action cannot be downgraded merely to reduce burden.
3. Duplicate rules compile into one user-facing check.
4. A binding law without a named failure mode is rejected or downgraded.
5. Temporary controls cannot remain active indefinitely without review.
6. Conflicting rules are surfaced with precedence and human escalation.
7. The active law set is visible and understandable to the dreamer or operator.
8. Governance produces a decision, protection, evidence, or executable control rather than paperwork alone.
9. The guardian may recommend simplification or retirement but cannot silently remove constitutional protections.
10. The effectiveness and burden of the active controls are recorded after execution.

## 12. Relationship to Core OS

The Core OS remains the canonical authority. OCODE does not rewrite constitutional law independently. It compiles, scopes, tests, and recommends improvements. Promotion, repeal, or constitutional exceptions require the Core OS governance process and human approval.

## 13. Current implementation boundary

```text
Design and responsibilities: CAPTURED
Runtime law inventory: NOT YET IMPLEMENTED
Applicability engine: NOT YET IMPLEMENTED
Duplicate/conflict detection: NOT YET IMPLEMENTED
Burden/risk scoring: NOT YET IMPLEMENTED
Policy compiler: NOT YET IMPLEMENTED
Human-visible active-law receipt: NOT YET IMPLEMENTED
Law retirement/sunset workflow: NOT YET IMPLEMENTED
```
