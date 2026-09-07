"""
QGA package — Quantum Genetic Algorithm (Milestones 3.1–3.3).
Combinatorial layer for multi-vehicle multi-trip route optimization.
"""

from app.qga.chromosome import (
    BreakGene,
    Chromosome,
    Gene,
    GeneType,
    StopGene,
    generate_random_chromosome,
    validate_chromosome,
)
from app.qga.decoder import decode_chromosome
from app.qga.fitness import (
    calculate_qga_fitness,
    capacity_penalty,
    load_imbalance_penalty,
)
from app.qga.operators import (
    mutate_chromosome,
    order_crossover,
    tournament_selection,
)
from app.qga.qubit_encoding import QubitChromosome
from app.qga.run_qga import QGAResult, run_qga

__all__ = [
    "BreakGene",
    "Chromosome",
    "Gene",
    "GeneType",
    "QGAResult",
    "QubitChromosome",
    "StopGene",
    "calculate_qga_fitness",
    "capacity_penalty",
    "decode_chromosome",
    "generate_random_chromosome",
    "load_imbalance_penalty",
    "mutate_chromosome",
    "order_crossover",
    "run_qga",
    "tournament_selection",
    "validate_chromosome",
]
