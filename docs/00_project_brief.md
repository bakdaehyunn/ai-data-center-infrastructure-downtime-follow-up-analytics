# Critical Procurement Bottleneck Analytics

## 1. Project Summary

Critical Procurement Bottleneck Analytics is an operational data system that helps teams understand where critical procurement requests are delayed and which requests should be handled first.

The project is not a purchase request or approval system. It assumes that procurement process data already exists, then ingests, validates, models, and analyzes that data to identify bottlenecks, exceptions, and operational priorities.

## 2. Core Problem

Critical procurement requests often move through several stages before the requested item or service is actually available.

Typical flow:

```text
Purchase Request
-> Budget Review
-> Procurement Review
-> PO Created
-> Vendor Confirmed
-> Delivery Scheduled
-> Goods Received
-> Inspection
-> Closed
```

If one stage is delayed, real work can be blocked.

Examples:

- A maintenance part is delayed and a scheduled repair is blocked.
- A software license is not purchased in time and a project slips.
- A purchase request is approved but the PO is not created.
- A vendor confirmation or delivery delay blocks a critical request.
- Goods are received but inspection is delayed, so the process cannot close.

Core question:

> Which procurement requests are currently blocking important operations, where is the bottleneck, and what should the team act on first?

## 3. Project Goal

The goal is not to show procurement status only. The goal is to reconstruct process state from event history and turn it into operational insight.

The system should answer:

- Which critical requests are currently at risk?
- Which stage creates the most delay?
- Are delays caused by budget review, procurement review, PO creation, vendor confirmation, delivery, receiving, or inspection?
- Which departments, vendors, or item categories repeatedly create delay?
- Are critical requests stuck behind lower-priority work?
- Which requests should be checked today?

## 4. Target Users

Target users:

- Procurement operators
- Operations or site teams
- Budget or finance reviewers
- Department requesters
- Operational data analysts

These users need more than "how many requests are open." They need to know which delayed request matters most and why.

## 5. What This Project Is Not

This project does not aim to build:

- A full purchase request system
- An approval workflow engine
- A real ERP integration
- A supplier portal
- AI or LLM recommendations
- ML-based delivery prediction
- Real-time streaming
- Kubernetes infrastructure
- Complex authentication or authorization
- A generic CRUD portfolio project

## 6. V1 Scope

V1 includes:

- Procurement request, purchase order, vendor, item, receipt, and status event modeling
- Sample source data generation
- PostgreSQL storage
- Python pipeline for raw load, validation, transformation, and analytics build
- Stage lead time calculation
- Bottleneck detection
- Rule-based criticality and priority scoring
- Critical request queue
- Vendor, department, stage, and item category summaries
- FastAPI read-only analytics API
- React dashboard
- Data quality checks
- Pipeline run logs

V1 excludes invoice and payment processing. The first version stops at receipt, inspection, and close.

## 7. Business Value

ERP or procurement systems usually show document status:

```text
PR approved
PO created
Vendor pending
Goods received
```

Operators often need a different view:

```text
Which delayed request matters most?
Why is it delayed?
Which operation is impacted?
Who should act next?
```

When request volume grows and many departments, vendors, and stages are involved, spreadsheets and manual follow-up become slow and unreliable. This system turns procurement process data into a decision-support layer for bottleneck diagnosis.

## 8. Portfolio Positioning

This project demonstrates how stateful business process data can be modeled and analyzed as an operational data system.

It connects experience with approval states, workflow transitions, external system follow-up, and exception handling to a more business-critical internal process: procurement bottleneck analysis.

Skills shown:

- Business process modeling
- Event-based state modeling
- PostgreSQL schema and analytical query design
- Python ETL pipeline design
- Data quality validation
- Pipeline run observability
- FastAPI contract design
- React operational dashboard design
- Operational decision support beyond CRUD

## 9. Success Criteria

V1 is successful when:

- The full procurement state flow can be explained from data.
- Each request's current stage and stage duration can be calculated.
- Bottleneck stages, departments, vendors, and item categories can be identified.
- Critical requests can be ranked by action priority.
- Data quality issues are visible.
- Pipeline execution history is visible.
- API and dashboard use the same analytical model.
- The project clearly reads as procurement bottleneck analytics, not a purchase approval system.
