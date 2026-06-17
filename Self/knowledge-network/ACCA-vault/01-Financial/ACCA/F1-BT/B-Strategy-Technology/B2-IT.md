---
title: B2 Information Technology
created: 2026-06-14
tags: [acca, f1, module-B, cross-ref]
mastery: 0
---

# B2 — Information Technology

> Conceptual module | Understanding IT's role in business

---

## 🖥️ Three-Level Role of IT in Business

```mermaid
graph TB
    STRAT[Strategic Level<br/>"IT drives business model innovation"]
    MGMT[Managerial Level<br/>"IT supports decisions & control"]
    OPS[Operational Level<br/>"IT automates daily operations"]
    
    STRAT --> MGMT --> OPS
    
    STRAT -.- EX1["e.g. Netflix: DVD → Streaming"]
    MGMT -.- EX2["e.g. ERP systems, management dashboards"]
    OPS -.- EX3["e.g. POS systems, inventory management"]
    
    classDef it fill:#7fba00,color:#fff
    class STRAT,MGMT,OPS it
```

---

## 📊 Big Data — The 4V Model

```mermaid
graph TB
    BD[Big Data]
    BD --> V1[Volume<br/>"Scale of data<br/>TB → PB"]
    BD --> V2[Velocity<br/>"Speed of generation & processing<br/>Real-time streaming"]
    BD --> V3[Variety<br/>"Diverse formats<br/>Structured / Semi / Unstructured"]
    BD --> V4[Veracity<br/>"Data quality<br/>Noise / Bias / Uncertainty"]
    
    classDef bigdata fill:#7fba00,color:#fff
    class BD,V1,V2,V3,V4 bigdata
```

| V | Meaning | Business Challenge |
|:---|:---|:---|
| Volume | Massive data scale | Storage cost, processing capacity |
| Velocity | Real-time generation and processing needs | Real-time analytics capability |
| Variety | Multiple formats (structured + unstructured) | Data integration |
| Veracity | Data accuracy and trustworthiness | Data quality, trust |

---

## ☁️ Cloud Computing

| Service Model | Full Name | User Manages | Provider Manages | Example |
|:---|:---|:---|:---|:---|
| **SaaS** | Software as a Service | Use only | Everything | Gmail, Office 365 |
| **PaaS** | Platform as a Service | Apps + Data | Infrastructure + Platform | Google App Engine |
| **IaaS** | Infrastructure as a Service | Apps + Data + OS | Hardware + Network | AWS EC2, Azure VM |

⚠️ **Cost advantage**: Shifts from CapEx (capital expenditure) to OpEx (operating expenditure)

---

## 🔒 Cybersecurity

| Threat | Description |
|:---|:---|
| **Malware** | Malicious software (viruses, worms, trojans) |
| **Phishing** | Deceptive emails to extract information |
| **Ransomware** | Encrypts data and demands payment |
| **DDoS** | Distributed Denial of Service attacks |
| **Insider Threat** | Malicious or negligent internal actors |

### IT Controls

| Type | Measures |
|:---|:---|
| **Access Controls** | Passwords, MFA, permission management |
| **Backup** | Regular backups, offsite storage |
| **Disaster Recovery** | BCP, recovery plans |
| **Encryption** | Data encryption (in transit + at rest) |

---

## 🛡️ Data Protection (GDPR)

Core Principles:
1. **Lawfulness, fairness & transparency**
2. **Purpose limitation**
3. **Data minimisation**
4. **Accuracy**
5. **Storage limitation**
6. **Integrity & confidentiality**
7. **Accountability**

💬 **Key Rights**: Right to be forgotten, Data portability

---

## 🔗 Links

- Big Data → [[B3-BI-Data|B3 BI & Data Analytics]]
- IT Strategy → [[B1-Strategy|B1 Strategic Management]]
- Cloud → AI Technology Domain (LLM deployment infrastructure)
- GDPR → [[../E-Ethics/E2-Code-of-Conduct|E2 Confidentiality Principle]]

---

> Return to [[B-Home|Module B Home]]
