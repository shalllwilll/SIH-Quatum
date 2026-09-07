# Leiden Community Detection Pre-Clustering Design

## 1. Context & Motivation

In last-mile logistics with 100–120 parcels and 20–25 delivery vehicles, optimizing a single giant route or running Quantum Genetic Algorithm (QGA) on the unpartitioned global search space ($120! \approx 6.7 \times 10^{198}$) is computationally intractable within sub-minute SLAs.

Per spec §3d and Deliverable #9, we pre-cluster delivery stops using the **Leiden community detection algorithm** before handing partitioned sub-problems to QGA.

---

## 2. Graph Construction & Edge Weighting

1. **Subproblem Scope:** Clustering is performed on the active delivery stops and warehouse locations, not the entire city road network.
2. **Topology:** A $K$-nearest neighbor proximity graph ($K = \min(8, N-1)$) is constructed between all active stops based on pairwise spatial distance.
3. **Weighting Function:**
   $$W_{ij} = \frac{1.0}{d_{ij} + \epsilon}$$
   where $d_{ij}$ is the haversine road-approximated distance in km, and $\epsilon = 0.2\text{ km}$ is a smoothing factor preventing division by zero for colocated parcels.

---

## 3. Resolution Parameter Tuning

- **Algorithm:** `leidenalg.RBConfigurationVertexPartition` (Reichardt & Bornholdt model with configuration null model).
- **Default Resolution ($\gamma = 1.0$):**
  - For $N = 100\text{--}120$ parcels across the Pune metro area, $\gamma = 1.0$ produces approximately 4 to 8 geographic delivery zones (averaging 15–25 parcels per cluster).
  - This maps cleanly to dispatching 2–4 vehicles per cluster.
- **Determinism:** `seed=42` is passed to `leidenalg.find_partition()` ensuring deterministic reproducibility.

---

## 4. Edge Cases & Fallbacks

- **Empty Input ($N = 0$):** Returns `ClusteringResult(clusters={}, assignments={}, cluster_count=0)`.
- **Small Input ($N < 4$):** Falls back to a single cluster containing all stops without invoking graph community detection overhead.
