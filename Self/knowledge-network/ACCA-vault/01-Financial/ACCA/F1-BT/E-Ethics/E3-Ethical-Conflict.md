---
title: E3 Ethical Conflict & Resolution
created: 2026-06-14
tags: [acca, f1, module-E]
mastery: 0
---

# E3 — Ethical Conflict & Resolution

---

## 🔀 Ethical Dilemma

> When two or more ethical principles (or interests) conflict, and any choice has a moral cost

### Typical Scenarios

```mermaid
graph TB
    DILEMMA[Ethical Dilemmas]
    DILEMMA --> D1["Boss asks to adjust financial figures<br/>Confidentiality vs Integrity"]
    DILEMMA --> D2["Discover client tax evasion<br/>Confidentiality vs Public Interest"]
    DILEMMA --> D3["Colleague's fraudulent behaviour<br/>Loyalty vs Objectivity"]
    DILEMMA --> D4["Conflict between client and employer interests"]
    
    classDef dilemma fill:#ff5252,color:#fff
    class DILEMMA,D1,D2,D3,D4 dilemma
```

---

## 🧭 AAA Ethical Decision-Making Framework

```mermaid
graph LR
    A1[Analyse]
    A2[Act]
    A3[Account]
    
    A1 --> A2 --> A3
    
    A1 -.- A1D["• Identify facts and ethical issues<br/>• Who is affected?<br/>• Which principles conflict?<br/>• What are the options?"]
    A2 -.- A2D["• Choose the best option<br/>• Execute the decision<br/>• Document the reasoning"]
    A3 -.- A3D["• Can you defend this decision?<br/>• How would the public view it?<br/>• Would your professional body approve?"]
    
    classDef aaa fill:#ff5252,color:#fff
    class A1,A2,A3 aaa
```

---

## 🛤️ Conflict Resolution Pathway

```mermaid
graph TB
    START[Encounter Ethical Conflict]
    START --> CHECK1{Internal resolution<br/>mechanisms exist?}
    CHECK1 -->|Yes| INTERNAL[Use internal channels<br/>Hotline / Compliance dept]
    CHECK1 -->|No| CHECK2{Can approach<br/>direct superior?}
    CHECK2 -->|Yes| SUPERIOR[Report to direct superior]
    CHECK2 -->|No| CHECK3{Superior is part<br/>of the problem?}
    CHECK3 -->|Yes| ESCALATE[Escalate to higher level<br/>Board / Audit Committee]
    CHECK3 -->|No| CHECK4{All internal<br/>avenues exhausted?}
    CHECK4 -->|Yes| EXTERNAL[Consider external disclosure<br/>ACCA / Regulator<br/>⚠️ As last resort]
    CHECK4 -->|No| DOCUMENT[Document decision process<br/>Preserve evidence]
    
    classDef start fill:#ff5252,color:#fff
    classDef action fill:#7fba00,color:#fff
    class START start
    class INTERNAL,SUPERIOR,ESCALATE,DOCUMENT action
    class EXTERNAL action
```

---

## 🗣️ Whistleblowing — Practical Considerations

### Steps
1. **Gather evidence** — Document facts (dates, individuals, actions)
2. **Internal channels** — Hotline, compliance, audit committee
3. **Professional body** — ACCA can provide guidance
4. **Legal protection** — Understand the protection laws in your jurisdiction
5. **External disclosure** — Last resort (media, regulator)

⚠️ **Reality check**: Many whistleblowers face professional and personal costs. Protection mechanisms are strong on paper, fragile in practice.

---

## 🔍 Professional Scepticism

> A questioning mind, alert to conditions that may indicate possible misstatement or fraud

| What It Is | What It Is Not |
|:---|:---|
| ✅ Questioning, verifying, thinking critically | ❌ Distrusting everything |
| ✅ Seeking evidence to support assertions | ❌ Cynicism |
| ✅ Staying alert to anomalies | ❌ Assuming everyone is lying |

---

## ⚖️ Consequences of Violating the ACCA Code

| Severity | Consequence |
|:---|:---|
| Minor violation | Warning, required corrective action |
| Moderate violation | Fine, additional CPD hours |
| Serious violation | Suspension of membership |
| Extremely serious | Permanent revocation of ACCA membership |

---

## 🔗 Links

- AAA Model → [[../D-Leadership/D1-Leadership|D1 Ethical Leadership]]
- Whistleblowing → [[../A-Business-Organisation/A3-Governance|A3 Audit Committee as key recipient]]
- Professional Scepticism → F8 Audit core
- Ethical Conflict → [[E1-Ethical-Considerations|E1 Three theories applied to actual decisions]]

---

> Return to [[E-Home|Module E Home]]
