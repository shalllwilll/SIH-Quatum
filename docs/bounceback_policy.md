# QGA↔QPSO Feedback Loop & Infeasibility Bounce-Back Policy

## 1. Objective & Architectural Role

Per spec §3d and §9, the hybrid routing engine combines:
1. **Discrete / Combinatorial Layer (QGA):** Optimizes stop sequencing and vehicle partitioning.
2. **Continuous / Timing Layer (QPSO):** Optimizes vehicle dispatch departure times to satisfy hard delivery SLA time windows under traffic congestion.

When QPSO determines that a route is **infeasible** (i.e., no continuous departure time within operating hours can satisfy the strict SLA windows for all stops on a vehicle trip), the engine triggers an **Infeasibility Bounce-Back** to QGA for structural re-optimization.

---

## 2. Bounce-Back Protocol

```
+------------------+         +------------------+
|  Leiden Cluster  | ------> |    QGA Search    |
+------------------+         +------------------+
                                       |
                                       v
                             +------------------+
                             |   QPSO Timing    |
                             +------------------+
                                  /          \
                       [Feasible]/            \[Infeasible]
                                /              \
                               v                v
                     +----------------+   +-------------------+
                     | Final Schedule |   | Bounce-Back Retry |
                     +----------------+   | (Targeted QGA)    |
                                          +-------------------+
                                                    |
                                       [Retry Cap Exceeded]
                                                    |
                                                    v
                                          +-------------------+
                                          | Best-Effort Route |
                                          | (Flag Violation)  |
                                          +-------------------+
```

1. **Targeted Cluster Scope:**
   - The bounce-back is isolated to the affected Leiden cluster.
   - Unaffected clusters retain their optimal schedules, avoiding full global re-runs.

2. **Structural Mitigation Strategies:**
   - **Strategy A (Fleet Expansion):** Allocate an additional vehicle to the affected cluster to split stop density.
   - **Strategy B (Combinatorial Perturbation):** Increase QGA exploration parameters (e.g. population, mutation rate, alternative break splits).

3. **Bounce-Back Retry Cap ($N_{\text{max}} = 3$):**
   - The loop attempts up to 3 targeted re-optimization passes per cluster.
   - This prevents unbounded infinite ping-pong while providing high probability of resolving structural conflicts.

---

## 3. Best-Effort SLA Fallback

If a parcel is fundamentally over-constrained (e.g., SLA window duration is shorter than minimum physical travel time from any warehouse, or severe gridlock makes on-time delivery physically impossible):
- **Never Drop Parcels:** Every active parcel is assigned to a vehicle route.
- **Explicit Infeasibility Flagging:** The route is flagged with `fallback_applied: true`, and the exact lateness in minutes is recorded in the session summary and driver delivery manifest.
- **Operator Visibility:** The Admin React frontend (Phase 7) displays an alert for fallback routes with predicted delay.
