from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FatigueState:
    current_rep_min: float = 999.0
    current_rep_max: float = 0.0
    concentric_displacement: float = 0.0
    concentric_frames: int = 0
    baseline_rom: float = 0.0
    baseline_vel: float = 0.0
    reps_observed: int = 0


class FatigueDetector:
    def __init__(self, rom_drop_pct: float = 0.15, velocity_drop_pct: float = 0.20) -> None:
        self.rom_drop_pct = rom_drop_pct
        self.velocity_drop_pct = velocity_drop_pct
        self.state = FatigueState()

    def update_frame(self, angle: float, displacement: float, in_concentric: bool) -> None:
        self.state.current_rep_min = min(self.state.current_rep_min, angle)
        self.state.current_rep_max = max(self.state.current_rep_max, angle)
        if in_concentric:
            self.state.concentric_displacement += displacement
            self.state.concentric_frames += 1

    def close_rep(self) -> tuple[bool, float, float]:
        rom = max(self.state.current_rep_max - self.state.current_rep_min, 0.0)
        vel = (
            self.state.concentric_displacement / self.state.concentric_frames
            if self.state.concentric_frames > 0
            else 0.0
        )
        self.state.reps_observed += 1
        if self.state.reps_observed <= 3:
            self.state.baseline_rom = ((self.state.baseline_rom * (self.state.reps_observed - 1)) + rom) / self.state.reps_observed
            self.state.baseline_vel = ((self.state.baseline_vel * (self.state.reps_observed - 1)) + vel) / self.state.reps_observed
            fatigue = False
        else:
            rom_drop = rom < (1.0 - self.rom_drop_pct) * max(self.state.baseline_rom, 1e-6)
            vel_drop = vel < (1.0 - self.velocity_drop_pct) * max(self.state.baseline_vel, 1e-6)
            fatigue = rom_drop or vel_drop
        self.state.current_rep_min = 999.0
        self.state.current_rep_max = 0.0
        self.state.concentric_displacement = 0.0
        self.state.concentric_frames = 0
        return fatigue, rom, vel

