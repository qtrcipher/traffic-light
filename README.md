# Traffic Light

[![test](https://github.com/qtrcipher/traffic-light/actions/workflows/test.yml/badge.svg)](https://github.com/qtrcipher/traffic-light/actions/workflows/test.yml)

Open-source traffic light intersection simulator for classrooms — Windows & Linux.

Three pillars, built in order: intersection **simulator** (MVP), status **dashboard**,
**hardware controller** (drive a real light over serial/USB).

Status: Phase 1 (foundation). Roadmap and session log in [PROGRESS.md](PROGRESS.md);
validated design in [docs/plans/2026-08-15-traffic-light-design.md](docs/plans/2026-08-15-traffic-light-design.md).

## Develop

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest                 # headless core tests
traffic-light          # run the app (or: python -m traffic_light.app)
```

## Docker (mirrors CI)

```sh
docker compose run --rm --build test    # headless pytest (Qt offscreen platform)
docker compose run --rm app             # shell in the dev container
```

## Privacy

Data collected: **none**. The app runs fully offline — no accounts, no
analytics, no network calls. Plans you save stay on your machine as JSON files;
settings (language, theme) are stored locally via QSettings.

## License

MIT — see [LICENSE](LICENSE).
