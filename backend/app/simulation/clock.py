"""
backend/app/simulation/clock.py — Milestone 9.1

Accelerated-Clock Simulation Engine:
Maintains simulated time (in minutes since midnight) running faster than wall-clock
at a configurable acceleration ratio (e.g. 1 real minute = 60 simulated minutes).
"""

from __future__ import annotations

import os
import time


class SimulationClock:
    """
    Simulation clock providing accelerated time progression relative to wall-clock.
    Time is tracked in canonical canonical units: float minutes since midnight (0.0 - 1440.0).
    """

    def __init__(
        self,
        start_time_min: float = 540.0,  # 09:00 AM
        acceleration_ratio: float | None = None,
    ):
        """
        Initialize simulation clock.

        Args:
            start_time_min: Initial simulated time in minutes since midnight (default: 540 = 09:00).
            acceleration_ratio: Multiplier (e.g. 60.0 means 1 real second = 1 sim minute).
        """
        if acceleration_ratio is None:
            env_val = os.getenv("SIMULATION_SPEED_MULTIPLIER", os.getenv("SIMULATION_CLOCK_SPEED", "60.0"))
            try:
                acceleration_ratio = float(env_val)
            except ValueError:
                acceleration_ratio = 60.0

        self.start_time_min = start_time_min
        self.acceleration_ratio = acceleration_ratio
        self._wall_start = time.perf_counter()
        self._paused = False
        self._paused_sim_time: float | None = None

    def get_current_time_min(self) -> float:
        """Get current simulated time in minutes since midnight."""
        if self._paused and self._paused_sim_time is not None:
            return self._paused_sim_time

        elapsed_wall_sec = time.perf_counter() - self._wall_start
        # If acceleration_ratio is 60: 1 real second = (60 / 60) = 1 sim minute
        # In general: elapsed_sim_min = (elapsed_wall_sec * acceleration_ratio) / 60.0
        elapsed_sim_min = (elapsed_wall_sec * self.acceleration_ratio) / 60.0
        current_time = (self.start_time_min + elapsed_sim_min) % 1440.0
        return current_time

    def set_time(self, time_min: float) -> None:
        """Set or jump the simulation clock to a specific minute since midnight."""
        self.start_time_min = time_min % 1440.0
        self._wall_start = time.perf_counter()
        if self._paused:
            self._paused_sim_time = self.start_time_min

    def set_acceleration_ratio(self, ratio: float) -> None:
        """Update clock acceleration ratio dynamically."""
        current_sim_time = self.get_current_time_min()
        self.acceleration_ratio = max(0.1, float(ratio))
        self.start_time_min = current_sim_time
        self._wall_start = time.perf_counter()

    def reset(self, start_time_min: float = 540.0) -> None:
        """Reset simulation clock to initial starting time."""
        self.start_time_min = start_time_min
        self._wall_start = time.perf_counter()
        self._paused = False
        self._paused_sim_time = None

    def pause(self) -> None:
        """Pause the simulation clock."""
        if not self._paused:
            self._paused_sim_time = self.get_current_time_min()
            self._paused = True

    def resume(self) -> None:
        """Resume the simulation clock."""
        if self._paused and self._paused_sim_time is not None:
            self.start_time_min = self._paused_sim_time
            self._wall_start = time.perf_counter()
            self._paused = False
            self._paused_sim_time = None


# Global simulation clock singleton
sim_clock = SimulationClock()
