# Historical Seed Data Narrative: Progressive Optimization

This document outlines the demo narrative and underlying data progression established in `backend/scripts/seed_historical_sessions.py` per spec §9 and §10.

---

## 1. The Story: From Baseline to High-Precision Dispatch

To demonstrate how the Abraxas platform progressively refines last-mile routing efficiency across successive operational cycles, four historical dispatch sessions have been seeded:

| Day | Optimization Mode | Total Fleet Distance | SLA Compliance | Fuel Efficiency Index | Key Operational Milestone |
|---|---|---|---|---|---|
| **Day -4** | Baseline Balanced | 148.5 km | **74.2%** | 65.0 | High SLA miss rate in congested station corridors; capacity overburdening on Van-1. |
| **Day -3** | Minimize Distance | 132.0 km | **81.5%** | 73.5 | Leiden clustering tightened spatial stop grouping, cutting total mileage by 11%. |
| **Day -2** | Green & Min Fuel | 124.8 km | **88.0%** | 84.0 | Live traffic congestion avoidance reduced vehicle idling during peak afternoon rush. |
| **Day -1** | Strict SLA Priority | 116.4 km | **95.8%** | 92.5 | QPSO continuous timing optimization eliminated bottleneck delays; near-perfect SLA achievement. |

---

## 2. Linked Delivery Events & Outcome Variance

Each session contains 17–19 distinct delivery stops across 3 vehicles (`Van-1`, `Van-2`, `Van-3`) with realistic field outcomes:
- **On-Time Deliveries**: Progressive increase from 13/17 on Day -4 to 18/19 on Day -1.
- **Late Deliveries**: Reduced from 4 occurrences on Day -4 to 1 on Day -1.
- **Failed Deliveries**: Eliminated from 4 failures on Day -4 to 0 on Day -1.

---

## 3. Clear Data Segregation

All pre-generated historical documents carry the explicit database flag:
```json
{
  "seeded": true
}
```
This guarantees that historical analytics trends are clearly distinguishable from live sessions created by evaluators on demo day.
