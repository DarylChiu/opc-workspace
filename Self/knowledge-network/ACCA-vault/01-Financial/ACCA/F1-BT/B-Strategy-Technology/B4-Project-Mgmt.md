---
title: B4 Project Management
created: 2026-06-14
tags: [acca, f1, module-B, cross-ref]
mastery: 0
---

# B4 — Project Management

---

## 📐 Project vs BAU (Business As Usual)

| Feature | Project | BAU (Ongoing Operations) |
|:---|:---|:---|
| **Nature** | Temporary (definite start & end) | Ongoing (continuous) |
| **Output** | Unique (one-off deliverable) | Repetitive |
| **Team** | Assembled temporarily | Permanent team |
| **Budget** | One-off | Annual budget |
| **Risk** | High (greater uncertainty) | Relatively predictable |

---

## 🔄 Project Lifecycle

```mermaid
graph LR
    I[Initiation] --> P[Planning] --> E[Execution] --> MC[Monitoring & Control] --> C[Closure]
    
    MC -.->|Feedback loop| E
    MC -.->|Corrective action| P
    
    classDef phase fill:#7fba00,color:#fff
    class I,P,E,MC,C phase
```

---

## 🔺 Triple Constraint

```mermaid
graph TB
    T[Time]
    C[Cost]
    S[Scope]
    Q[Quality]
    
    T --- C --- S --- T
    S --- Q
    
    classDef const fill:#ed7d31,color:#fff
    classDef qual fill:#ff5252,color:#fff
    class T,C,S const
    class Q qual
```

> ⚠️ **Iron Triangle Law**: Time, cost, and scope are mutually constraining. Changing one inevitably affects the others. Quality is determined by all three.

---

## 📊 Project Management Tools

### Gantt Chart

```
Task A: ████████░░░░░░░░░░░░░░
Task B: ░░░░██████████░░░░░░░░
Task C: ░░░░░░░░████████████░░
Task D: ░░░░░░░░░░░░░░████████
```

### Critical Path Method (CPM)

```mermaid
graph LR
    Start --> A[Task A<br/>3 days]
    Start --> B[Task B<br/>5 days]
    A --> C[Task C<br/>4 days]
    B --> C
    C --> D[Task D<br/>2 days]
    D --> End
    
    classDef critical stroke:#ff5252,stroke-width:3px
    class B,C,D critical
```

- **Critical Path**: Longest path through the project = minimum completion time
- In this example: Start → B(5) → C(4) → D(2) = 11 days (critical path)
- **Float/Slack**: Time a non-critical task can be delayed (Task A has 2 days of float)

---

## 🎯 Project Risk Management

```mermaid
graph LR
    I2[Identify Risks] --> A2[Assess: Probability × Impact]
    A2 --> R2[Respond: Strategy Selection]
    R2 --> M2[Monitor Continuously]
    
    classDef risk fill:#7fba00,color:#fff
    class I2,A2,R2,M2 risk
```

### Risk Response Strategies (TARA Framework)

| Strategy | Meaning | Appropriate For |
|:---|:---|:---|
| **Transfer** | Shift risk (insurance, outsourcing) | High impact, low probability |
| **Avoid** | Eliminate the risk entirely | High impact, high probability |
| **Reduce** | Mitigate likelihood or impact | Medium impact |
| **Accept** | Acknowledge and reserve contingency | Low impact |

---

## 🌀 Agile vs Waterfall

|  | Waterfall | Agile |
|:---|:---|:---|
| **Approach** | Linear sequential | Iterative incremental |
| **Requirements** | Defined upfront | Flexible, evolving |
| **Delivery** | Single final delivery | Continuous small batches |
| **Best For** | Clear requirements, low change | Uncertain requirements, rapid change |
| **User Involvement** | Start and end only | Continuous throughout |

---

## 🔗 Links

- Project Teams → [[../D-Leadership/D3-Teams|D3 Team Dynamics]]
- Risk Management → Finance Domain Risk Management
- Stakeholder Management → [[../A-Business-Organisation/A2-Stakeholders|A2 Stakeholders]]
- Agile → AI Technology Domain (agile LLM application development)

---

> Return to [[B-Home|Module B Home]]
