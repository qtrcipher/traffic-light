# Traffic Light — Phase 0 Design

Date: 2026-08-15 · Status: validated with product owner

Open-source traffic light app for Windows and Linux (Docker for local dev). Not iOS.

## Product

Three pillars, built in this order:

1. **Intersection simulator** (MVP) — single 4-way intersection, animated cars,
   configurable light cycle.
2. **Status dashboard** — reads the simulator's live state.
3. **Hardware controller** — mirrors state to a real light (serial/USB), last.

- Users: education / classroom (teachers demonstrating how signalized intersections work).
- Success: adoption metrics — GitHub stars/forks, release downloads, issues/PRs.

## Market check (2026-08-15)

Verdict: build. SUMO/PTV Vissim own the pro segment (too complex for classrooms);
education has only toys (mobile apps, HTML5 pages) and expensive PLC trainers
(De Lorenzo). No polished free desktop classroom sim for Win+Linux.
Gaps we own: desktop classroom app, no-code cycle config, software→hardware bridge.
Keywords: traffic light simulator · intersection simulator · traffic signal education ·
محاكاة إشارات المرور.
Risk: niche discovery depends on teacher word-of-mouth; hardware fragmentation deferred
to pillar 3.

## UX

Three screens:

1. **Simulator (main)** — top-down 4-way canvas (cars, 4 signal heads), right panel
   with phase timings, play/pause, speed 0.5×–4×; toolbar with presets
   (default / rush hour / night-flash), save/load plan JSON, fullscreen presentation mode.
2. **Plan editor (dialog)** — per-phase durations, add/remove phases, inline validation,
   Apply disabled until valid.
3. **Settings (dialog)** — language EN/AR, theme light/dark.

Flow: launch → language picker (first run only) → sim running default plan → tweak →
fullscreen for the class.

Four states per screen: Simulator — running / applying plan / no plan (CTA: load
default) / invalid plan file (message + restore default). Plan editor — form / n/a /
new blank phase guided / inline field errors. Settings — values / write-failure toast
(non-blocking).

## Design direction

Flat + soft rounding (16px, chunky controls); flat high-contrast canvas readable from
the back of a classroom. Indigo chrome `#4F46E5`; fixed signal colors red `#DC2626`,
amber `#F59E0B`, green `#16A34A`; accent `#EA580C`. Light theme and dark "asphalt"
theme. Atkinson Hyperlegible + IBM Plex Sans Arabic (RTL mirrored layout). Lucide SVG
icons, 150–300ms motion, `prefers-reduced-motion` respected, keyboard navigable
(space = play/pause).

## Architecture

Python + PySide6 (Qt). Contributor-friendly for an open-source education project;
pyserial/QSerialPort ready for pillar 3; one codebase for Win+Linux.

```
src/traffic_light/
├── core/            # pure Python, zero Qt — headless-testable
│   ├── engine.py    # SimulationEngine.tick(dt), deterministic clock, seeded RNG
│   ├── cycle.py     # Phase, TimingPlan, validation (amber ≥1s, cycle ≥5s)
│   ├── signal.py    # SignalState enum, SignalHead
│   ├── traffic.py   # car spawning, queues, movement
│   └── presets.py   # default / rush-hour / night-flash
├── ui/              # PySide6; renders engine state, owns no logic
│   ├── main_window.py · canvas.py (QPainter) · panels.py
│   ├── plan_editor.py · settings.py · theme.py
├── hardware/
│   └── base.py      # HardwareSink protocol — pillars 2/3 plug in here
├── i18n/            # Qt Linguist .ts, EN/AR + RTL
└── app.py
tests/               # pytest; core headless, UI via xvfb
Dockerfile + docker-compose.yml   # dev/test env, mirrors CI
```

Decisions: engine advances by `dt` (speed slider scales it) → identical behavior at any
speed, reproducible tests. One-way flow: engine state → render; UI edits → validated
plan → applied between phases. `HardwareSink` interface defined now, implemented later.

## Data model (local, no backend)

- **TimingPlan** JSON (save/load/share): `{name, phases: [{ns, ew, duration_s}, …]}`,
  signals `red|amber|green|off`; validation in `core/cycle.py`.
- **Settings** via QSettings: language, theme, last plan.
- Nothing else persists in v1.

## Testing

pytest for `core/` (headless, deterministic with seeded RNG); Qt UI tests under xvfb
in Docker, mirroring CI. Tests written with each feature.
