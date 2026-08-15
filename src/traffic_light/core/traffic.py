"""Car spawning, queues and movement. Implemented in Phase 2 — see PROGRESS.md.

Movement model: simple point-mass cars per approach; a car advances when the
signal is green and the car ahead is far enough. Seeded RNG (from the engine)
drives spawn intervals so simulations are reproducible in tests.
"""
