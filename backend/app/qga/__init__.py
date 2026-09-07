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

__all__ = [
    "BreakGene",
    "Chromosome",
    "Gene",
    "GeneType",
    "StopGene",
    "decode_chromosome",
    "generate_random_chromosome",
    "validate_chromosome",
]
