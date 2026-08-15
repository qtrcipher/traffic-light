# App Roadmap — Traffic Light

> Open-source traffic light app for Windows and Linux. Docker for local dev. Not iOS.
> THE todo list. Paste into any session (or keep as the app's `PROGRESS.md`).
> Checkboxes = where I am. Tag convention: bare `` `name` `` = skill; `` `name` `` agent = subagent;
> a tag on a phase HEADER applies to every item in that phase.
> House rules (RTL, light/dark, no manual testing, session start/end routine, ASC
> constants) load automatically from AGENTS.md — deliberately not duplicated here.
> Work top to bottom; phases are in order. AI: read this first — if a task is checked,
> confirm before redoing it; update this file and commit at session end.

## Phase 0 — Plan (GATE: no implementation code until every item below is checked)
- [x] Problem, users, MVP scope, success metrics — `product-strategist` agent · `product-frameworks` · `brainstorming`
  - Decision: intersection simulator + status dashboard + hardware controller; MVP = simulator (single 4-way intersection, animated cars, configurable cycle); users = education/classroom; success = adoption metrics (stars, downloads, issues/PRs)
- [x] Market check: competitors, demand, keywords — `app-market-research`
  - Verdict: build. SUMO/PTV own pro, toys/hardware own education; no polished free desktop classroom sim for Win+Linux. Gaps: desktop classroom app, no-code cycle config, software→hardware bridge. Keywords: traffic light simulator, intersection simulator, محاكاة إشارات المرور
- [x] Screens, flows, all four UI states per screen — `ux-designer` agent
  - 3 screens: Simulator (canvas + timing panel + presentation mode), Plan editor (dialog, inline validation), Settings (EN/AR, light/dark). Flow: launch → language picker (first run) → sim running default plan → tweak → fullscreen. All four states defined per screen
- [x] Design direction: style, palette, typography — `ui-ux-pro-max`
  - Flat + soft rounding (16px, chunky controls), flat high-contrast canvas; indigo chrome #4F46E5, signal colors fixed (red #DC2626 / amber #F59E0B / green #16A34A), accent #EA580C; Atkinson Hyperlegible + IBM Plex Sans Arabic; dark = asphalt theme; Lucide icons, 150–300ms motion, reduced-motion respected
- [x] Architecture + module plan — `technical-architect` agent
  - Python + PySide6. core/ (pure Python, deterministic dt-engine) / ui/ (PySide6, no logic) / hardware/ (HardwareSink protocol, stubbed for pillars 2–3). Docker dev/test with xvfb. Full plan: docs/plans/2026-08-15-traffic-light-design.md
- [x] Data model + persistence design — `firebase-backend-engineer` agent · `database-design-patterns`
  - No backend (local desktop app). TimingPlan JSON {name, phases:[{ns, ew, duration_s}]} validated in core/cycle.py; QSettings for language/theme/last plan

## Phase 1 — Foundation
- [x] Public GitHub repo (open source); `.gitignore` covers secrets BEFORE first commit
  - https://github.com/qtrcipher/traffic-light (public, pushed 2026-08-15); .gitignore with secrets block committed first
- [x] Project scaffold, dependencies — `xcode-specialist` agent
  - src-layout PySide6 package (pyproject.toml), core/{signal,cycle,presets} implemented + engine/traffic contracts stubbed, ui/{theme,settings,language_dialog,main_window}, hardware/base.py HardwareSink, Dockerfile + compose (xvfb tests), 13 pytest tests
- [x] One-time language picker at first launch (EN/AR), persisted — `i18n-patterns` · `arabic-localization`
  - LanguageDialog on first run, QSettings-persisted, RTL layout direction + Qt Linguist .ts catalog (ar), English source strings
- [x] App icon + splash — `icon-design-guide` · `art-asset-designer` agent
  - assets/icon.svg + rendered PNGs (scripts/make_icon.py), set as window icon. Splash deliberately skipped: app starts <1s, a splash would only flash
- [x] Scaffold this file into the repo as `PROGRESS.md` — `ios-ship-gate` (template in its references/)

## Phase 2 — Features
- [x] Core features: simulation engine (deterministic dt-tick, seeded RNG), intersection canvas, control panel (play/pause/speed/presets), plan editor, save/load plan JSON, presentation mode — `frontend-ios` agent · `state-management` · `persistence-patterns`
  - Engine sub-steps at phase boundaries, set_plan applies at boundary only; TrafficModel queues/clears; QPainter canvas; plan editor with coded validation issues (translatable); F11 presentation, spacebar play/pause; invalid plan file → error + restore default
- [x] Deep links / widgets / charts if needed — `deep-linking` · `widgetkit-patterns` · `swift-charts-patterns`
  - Not needed for v1: desktop classroom app, no mobile widgets/deep links; stats overlay deferred
- [x] Onboarding + in-app guides
  - Quick-guide dialog (shortcuts, plan sharing) auto-shows until dismissed, Help menu + About
- [x] Accessibility — `accessibility-specialist` agent
  - accessibleNames/descriptions incl. live canvas phase description, explicit tab order, focus rings, WCAG AA contrast locked by tests (fixed failing error-color tokens)
- [x] In-app account deletion (required if accounts exist)
  - N/A — no accounts, fully local app
- [x] Developer debug menu — DEBUG builds only
  - TRAFFIC_LIGHT_DEBUG=1 gates Debug menu: step one phase, spawn car burst

## Phase 3 — Backend & AI
- [x] API security; debug token DEBUG-only — `security-checklist`
  - N/A — no backend/API; fully local app
- [x] Crash reporting — `error-monitoring`
  - Deliberately none: zero telemetry is a feature for a classroom app used by kids; bugs via GitHub issues
- [x] Privacy manifest covering every SDK
  - N/A (Apple-specific); README states "data collected: none"
- [x] Slack alerts (info→digest, warning/critical→alerts) — `slack-alerts`
  - N/A — no server-side component
- [x] Server-side simulation for restore-purchase etc. — `firebase-backend-engineer` agent
  - N/A — no purchases/server

## Phase 4 — Monetization
- [x] Model: free/open-source — `monetization-frameworks`
  - Free, MIT-licensed, no monetization — classroom/education product
- [x] Paywall after value, not before — `payments-expert` agent
  - N/A — no paywall
- [x] IAP Test + sandbox scheme (never main) — `storekit-testing-patterns`
  - N/A — no IAP
- [x] Ads? Full UMP→ATT compliance chain — `admob-integration`
  - N/A — no ads

## Phase 5 — Testing (fleet bar)
- [x] UI tests written WITH each feature (not after)
  - Every feature landed with tests since Phase 1 (83 total)
- [x] Every control × every state: disabled, loading, empty, error
  - tests/test_states.py: plan-editor empty, load-error recovery, presentation toggle, speed extremes, pause/timer
- [x] Snapshots: AR/EN × light/dark
  - 5 reference renders (4 combos + AR guide), deterministic fixed-seed, font-tolerant compare, scripts/regen_snapshots.py
- [x] Accessibility assertions: labels, traits, order
  - tests/test_a11y.py + contrast tests (WCAG AA locked)
- [x] Arabic copy: 6 plurals, numerals, dates — `arabic-localization`
  - No plural strings exist (none needed); timing readouts locked to Latin digits under ar, tested; RTL verified in snapshots
- [x] Suite green: Linux/Windows CI, then real install
  - GitHub Actions matrix ubuntu+windows green (run 31884788506); Windows leg doubles as the real-install check (pip install -e + pytest), Linux real install via Docker image
- [x] Bugs found → root-cause first — `systematic-debugging`
  - Applied throughout (timer-flake root-caused to QElapsedTimer zero-read → _advance refactor; contrast failure → token fix)

## Phase 6 — Release & ship
- [x] Privacy policy: own public GitHub Pages repo, bilingual, Arabic first — `privacy-support-pages`
  - https://qtrcipher.github.io/traffic-light-privacy/ (repo: qtrcipher/traffic-light-privacy, cloned at traffic-light-privacy/ per house rule; RTL previewed before push)
- [x] Store/release privacy declarations — `privacy-support-pages`
  - No stores; declaration = the privacy page + README "data collected: none". Zero-collection is truthful: no SDKs, no network, no accounts
- [x] Release metadata: age rating, review info, accessibility labels — `ios-ship-gate`
  - No ASC; repo metadata set instead: 10 topics, homepage → privacy page, bilingual README with features/screenshots
- [x] Screenshots + store copy, both languages — `app-store-optimization`
  - README shows EN-light + AR-dark renders from the snapshot suite; bilingual feature list
- [x] Release notes (from v2 on)
  - N/A — v1.0.0 is the first release
- [x] SHIP: run the release gate in order — `ios-ship-gate` (the steps live in that skill; load it, don't improvise them)
  - Gate adapted for desktop OSS: version bump 1.0.0 · 83-test suite green both platforms · snapshot/QA review AR+EN · audit sweep clean (no TODO/FIXME, debug menu gated, zero telemetry) · frozen bundle launch-verified · tag v1.0.0 · release CI built + attached traffic-light-linux (80MB) and traffic-light-windows.exe (49MB) · published (not draft): https://github.com/qtrcipher/traffic-light/releases/tag/v1.0.0

## Phase 7 — Pillar 2: Status dashboard
- [x] Dashboard window: large glanceable status lights per head (N/S/E/W), live from the engine — via the `HardwareSink` seam
  - StateBridge (ui/bridge.py) fans engine snapshots to sinks on change only; DashboardWindow consumes it as a HardwareSink
- [x] Open from View menu / toolbar; works alongside the simulator
  - Checkable action, non-modal, lazy-created, replays current state on open
- [x] Phase + elapsed readout in large classroom-legible type
  - 36px bold phase/elapsed beneath the 2×2 compass lamp grid
- [x] Accessible names on all status lights; AR/RTL + both themes
  - Live names ("North signal: green" / إشارة الشمال: أخضر), RTL-mirrored grid, follows app theme
- [x] Tests + snapshot coverage (incl. AR dark dashboard)
  - 14 new tests (97 total): bridge change-only firing, lamps, a11y names, 4 dashboard snapshots (10% budget for 36px labels)

## Session log
Format, newest first, one line per session: `YYYY-MM-DD — what changed — next: <task>`
- 2026-08-15 — Phase 7 done: pillar 2 status dashboard (StateBridge on HardwareSink seam, 2×2 big-lamp board, 36px phase/elapsed, live a11y names, AR/RTL + themes); 97 tests incl. 4 dashboard snapshots; Docker image gained fonts-noto-core (container was rendering Arabic as tofu — root-caused via AR dashboard snapshot diffs); fonts now BUNDLED (Atkinson Hyperlegible + IBM Plex Sans Arabic, OFL) so glyphs render identically on every OS — CI green ubuntu+windows — next: pillar 3 (hardware) or v1.1.0 tag
