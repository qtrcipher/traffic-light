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
- [ ] API security; debug token DEBUG-only — `security-checklist`
- [ ] Crash reporting — `error-monitoring`
- [ ] Privacy manifest covering every SDK
- [ ] Slack alerts (info→digest, warning/critical→alerts) — `slack-alerts`
- [ ] Server-side simulation for restore-purchase etc. — `firebase-backend-engineer` agent

## Phase 4 — Monetization
- [ ] Model: free/open-source — `monetization-frameworks`
- [ ] Paywall after value, not before — `payments-expert` agent
- [ ] IAP Test + sandbox scheme (never main) — `storekit-testing-patterns`
- [ ] Ads? Full UMP→ATT compliance chain — `admob-integration`

## Phase 5 — Testing (fleet bar)
- [ ] UI tests written WITH each feature (not after)
- [ ] Every control × every state: disabled, loading, empty, error
- [ ] Snapshots: AR/EN × light/dark
- [ ] Accessibility assertions: labels, traits, order
- [ ] Arabic copy: 6 plurals, numerals, dates — `arabic-localization`
- [ ] Suite green: Linux/Windows CI, then real install
- [ ] Bugs found → root-cause first — `systematic-debugging`

## Phase 6 — Release & ship
- [ ] Privacy policy: own public GitHub Pages repo, bilingual, Arabic first — `privacy-support-pages`
- [ ] Store/release privacy declarations — `privacy-support-pages`
- [ ] Release metadata: age rating, review info, accessibility labels — `ios-ship-gate`
- [ ] Screenshots + store copy, both languages — `app-store-optimization`
- [ ] Release notes (from v2 on)
- [ ] SHIP: run the release gate in order — `ios-ship-gate` (the steps live in that skill; load it, don't improvise them)

## Session log
Format, newest first, one line per session: `YYYY-MM-DD — what changed — next: <task>`
- 2026-08-15 — Phase 2 done: deterministic engine + traffic, QPainter intersection canvas, control panel, plan editor w/ coded validation, save/load JSON, presentation mode, quick-guide onboarding, a11y pass (contrast fix), debug menu; 64 tests green local+Docker — next: Phase 3 (mostly N/A for local app — review) or Phase 5 hardening
