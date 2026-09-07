"""
backend/tests/test_chromosome.py — Milestone 3.1 Test Suite

Test Cases:
  TC-3.1-01: Random chromosome generation validity within cluster
  TC-3.1-02: Decoder produces structured per-vehicle routes
  TC-3.1-03: Multi-trip chromosome decoding
  TC-3.1-04: Malformed chromosome with missing stops rejected (negative test)
  TC-3.1-05: Chromosome with duplicate stops rejected (negative test)
  TC-3.1-06: Single-stop cluster handled cleanly (edge case)
  TC-3.1-07: Dynamic warehouse tag round-trips correctly
"""


from app.qga.chromosome import (
    BreakGene,
    Chromosome,
    StopGene,
    generate_random_chromosome,
    validate_chromosome,
)
from app.qga.decoder import decode_chromosome


def test_tc_3_1_01_random_chromosome_validity():
    """TC-3.1-01: Verify generated chromosome contains all cluster stops exactly once."""
    stops = [f"PAR-PUNE-{i:04d}" for i in range(1, 21)]
    vehicles = ["VEH-001", "VEH-002", "VEH-003"]

    chrom = generate_random_chromosome(
        stops=stops,
        vehicles=vehicles,
        warehouse_id="WH-PUNE-001",
        seed=42,
    )

    is_valid, err = validate_chromosome(chrom, expected_stops=stops)
    assert is_valid, f"Validation failed: {err}"
    assert set(chrom.stops()) == set(stops)
    assert len(chrom.stops()) == 20


def test_tc_3_1_02_decoder_structured_routes():
    """TC-3.1-02: Verify decoder produces structured routes keyed by vehicle_id."""
    genes = [
        BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id="WH-PUNE-001"),
        StopGene(stop_id="P1"),
        StopGene(stop_id="P2"),
        BreakGene(vehicle_id="VEH-002", trip_number=1, warehouse_id="WH-PUNE-001"),
        StopGene(stop_id="P3"),
    ]
    chrom = Chromosome(genes=genes)
    decoded = decode_chromosome(chrom)

    assert "VEH-001" in decoded
    assert "VEH-002" in decoded
    assert len(decoded["VEH-001"]) == 1
    assert decoded["VEH-001"][0]["stops"] == ["P1", "P2"]
    assert decoded["VEH-002"][0]["stops"] == ["P3"]


def test_tc_3_1_03_multi_trip_decoding():
    """TC-3.1-03: Verify multi-trip chromosome decodes into separate trips per vehicle."""
    genes = [
        BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id="WH-PUNE-001"),
        StopGene(stop_id="P1"),
        StopGene(stop_id="P2"),
        BreakGene(vehicle_id="VEH-001", trip_number=2, warehouse_id="WH-PUNE-002"),
        StopGene(stop_id="P3"),
        StopGene(stop_id="P4"),
    ]
    chrom = Chromosome(genes=genes)
    decoded = decode_chromosome(chrom)

    assert len(decoded["VEH-001"]) == 2
    trip1 = decoded["VEH-001"][0]
    trip2 = decoded["VEH-001"][1]

    assert trip1["trip_number"] == 1
    assert trip1["warehouse_id"] == "WH-PUNE-001"
    assert trip1["stops"] == ["P1", "P2"]

    assert trip2["trip_number"] == 2
    assert trip2["warehouse_id"] == "WH-PUNE-002"
    assert trip2["stops"] == ["P3", "P4"]


def test_tc_3_1_04_missing_stop_rejected():
    """TC-3.1-04 (Negative): Validation catches missing stops."""
    genes = [
        BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id="WH-PUNE-001"),
        StopGene(stop_id="P1"),
        # P2 is missing
    ]
    chrom = Chromosome(genes=genes)
    is_valid, err = validate_chromosome(chrom, expected_stops={"P1", "P2"})

    assert not is_valid
    assert "Missing expected stops" in err


def test_tc_3_1_05_duplicate_stop_rejected():
    """TC-3.1-05 (Negative): Validation catches duplicate stops."""
    genes = [
        BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id="WH-PUNE-001"),
        StopGene(stop_id="P1"),
        StopGene(stop_id="P1"),  # Duplicate!
    ]
    chrom = Chromosome(genes=genes)
    is_valid, err = validate_chromosome(chrom, expected_stops={"P1"})

    assert not is_valid
    assert "Duplicate stops" in err


def test_tc_3_1_06_single_stop_cluster():
    """TC-3.1-06 (Edge Case): Single-stop cluster generates and decodes cleanly."""
    chrom = generate_random_chromosome(
        stops=["P1"],
        vehicles=["VEH-001"],
        warehouse_id="WH-PUNE-001",
    )
    is_valid, err = validate_chromosome(chrom, expected_stops=["P1"])
    assert is_valid

    decoded = decode_chromosome(chrom)
    assert "VEH-001" in decoded
    assert decoded["VEH-001"][0]["stops"] == ["P1"]


def test_tc_3_1_07_warehouse_tag_roundtrip():
    """TC-3.1-07: Dynamic warehouse tags on break markers round-trip through decoder."""
    genes = [
        BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id="WH-PUNE-003"),
        StopGene(stop_id="P1"),
    ]
    chrom = Chromosome(genes=genes)
    decoded = decode_chromosome(chrom)

    assert decoded["VEH-001"][0]["warehouse_id"] == "WH-PUNE-003"
