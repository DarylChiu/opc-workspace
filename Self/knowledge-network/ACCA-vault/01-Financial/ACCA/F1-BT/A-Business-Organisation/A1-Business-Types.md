---
title: A1 Business Types & Structure
created: 2026-06-14
tags: [acca, f1, module-A]
mastery: 0
---

# A1 — Business Types & Structure

> ⭐ Foundational, high-frequency | Panoramic classification of business organisations

---

## 📖 Types of Business Organisation

```mermaid
graph TB
    ORG[Business Organisations]
    ORG --> PS[Public Sector]
    ORG --> PR[Private Sector]
    ORG --> NGO[Non-Profit / NGO]
    
    PR --> ST[Sole Trader]
    PR --> PT[Partnership]
    PR --> LC[Limited Company]
    
    LC --> PVT[Private Limited<br/>Ltd]
    LC --> PUB[Public Limited<br/>PLC]
    
    classDef public fill:#4472c4,color:#fff
    classDef private fill:#ed7d31,color:#fff
    classDef ngo fill:#7fba00,color:#fff
    
    class PS public
    class ST,PT,LC,PVT,PUB private
    class NGO ngo
```

### Detailed Comparison

| Feature | Sole Trader | Partnership | Private Ltd (Ltd) | Public Ltd (PLC) |
|:---|:---|:---|:---|:---|
| **Owners** | 1 person | 2-20 (typical) | 1+ shareholders | 2+ shareholders |
| **Liability** | Unlimited | Unlimited (usually) | Limited | Limited |
| **Capital Raising** | Low | Medium | Medium-High | High (stock market) |
| **Regulation** | Minimal | Low | Medium | High (public disclosure) |
| **Transfer of Ownership** | Difficult | Requires partner consent | Relatively easy | Easy (share market) |
| **Typical Examples** | Small shops, freelancers | Law firms, clinics | Family businesses | Listed companies |

---

## 🌍 Business Environment Analysis

### PEST Analysis

```mermaid
graph LR
    subgraph PEST Framework
        P[Political]
        E[Economic]
        S[Social]
        T[Technological]
    end
    
    P --> P1["Government policy / Tax / Trade barriers"]
    E --> E1["GDP / Interest rates / FX / Inflation"]
    S --> S1["Demographics / Culture / Education / Consumption"]
    T --> T1["Automation / AI / Digital transformation"]
    
    classDef pest fill:#4472c4,color:#fff
    class P,E,S,T pest
```

> ⚠️ **Extended version**: PESTLE = PEST + Legal + Environmental

### Porter's Five Forces

```mermaid
graph TB
    subgraph Five Forces
        center[Industry Rivalry<br/>Competitive Intensity]
        new[Threat of New Entrants]
        sub[Threat of Substitutes]
        buyer[Bargaining Power of Buyers]
        supplier[Bargaining Power of Suppliers]
    end
    
    new --> center
    sub --> center
    buyer --> center
    supplier --> center
    
    classDef center fill:#ff5252,color:#fff
    classDef force fill:#4472c4,color:#fff
    class center center
    class new,sub,buyer,supplier force
```

| Force | High-Threat Conditions | Low-Threat Conditions |
|:---|:---|:---|
| **New Entrants** | Low capital needs, no patents, low brand loyalty | High barriers, strong regulation |
| **Substitutes** | Good value substitutes, low switching costs | No substitutes, high switching costs |
| **Buyers** | Concentrated buyers, standardised products | Fragmented buyers, differentiated products |
| **Suppliers** | Concentrated suppliers, no alternatives | Fragmented suppliers, backward integration possible |
| **Rivalry** | Slow growth, high exit barriers, commoditised | High growth, differentiated, low fixed costs |

---

## 📈 Business Lifecycle

```mermaid
graph LR
    S[Startup] --> G[Growth] --> M[Maturity] --> D[Decline]
    D -.->|Innovation / Pivot| R[Renewal]
    
    classDef stage fill:#7fba00,color:#fff
    class S,G,M,D,R stage
```

| Stage | Characteristics | Strategic Focus |
|:---|:---|:---|
| Startup | High investment, negative/low profit, validating business model | Product-Market Fit (PMF) |
| Growth | Rapid expansion, revenue growth, brand building | Market share, scaling |
| Maturity | Slowing growth, stable profit, intense competition | Efficiency, cost control |
| Decline | Shrinking market, declining profit | Harvest / Divest / Transform |

---

## 🔗 Links

- Porter's Five Forces → [[../../B-Strategy-Technology/B1-Strategy|B1 Strategic Management]]
- Business Types → F4 Corporate Law (legal structures)
- PEST → F9 Financial Management (macro environment impact on investment)

---

> Return to [[A-Home|Module A Home]]
