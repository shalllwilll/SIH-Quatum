from fastapi import APIRouter
from app.simulation.clock import sim_clock

router = APIRouter(prefix="/simulation", tags=["Simulation Controls"])

@router.post("/pause")
def pause_simulation():
    """Pause the simulation clock."""
    sim_clock.pause()
    return {"status": "paused"}

@router.post("/resume")
def resume_simulation():
    """Resume the simulation clock."""
    sim_clock.resume()
    return {"status": "running"}

@router.post("/speed")
def set_simulation_speed(speed: float):
    """Set the simulation speed multiplier."""
    sim_clock.set_acceleration_ratio(speed)
    return {"status": "success", "speed": speed}

@router.get("/state")
def get_simulation_state():
    """Get current simulation clock state."""
    from app.simulation.engine import get_active_session
    session = get_active_session()
    return {
        "time_min": round(sim_clock.get_current_time_min(), 2),
        "multiplier": sim_clock.acceleration_ratio,
        "paused": sim_clock._paused,
        "has_active_session": session is not None,
        "session_id": session.get("id", "") if session else None,
    }

