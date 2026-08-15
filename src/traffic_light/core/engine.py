"""Simulation engine. Implemented in Phase 2 — see PROGRESS.md.

Contract (fixed now so UI and hardware code can target it):

- ``SimulationEngine(plan, seed=...)`` — deterministic; seeded RNG for traffic.
- ``engine.tick(dt_s)`` — advance by a real-time delta; the UI's speed slider
  scales ``dt_s`` so behavior is identical at any speed.
- ``engine.state`` — current phase, per-head SignalStates, car positions.
- ``engine.set_plan(plan)`` — applies a validated TimingPlan at the next phase
  boundary, never mid-phase.
"""
