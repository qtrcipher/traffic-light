# Dev/test image for Traffic Light (Windows & Linux are the ship targets;
# this container mirrors CI so tests run identically everywhere).
FROM python:3.12-slim

# Qt runtime libs + xvfb for headless UI tests
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libegl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0 \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

ENV QT_QPA_PLATFORM=offscreen

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir '.[dev]'

# Compile Qt Linguist catalogs (.ts -> .qm) with PySide6's bundled lrelease
# (explicit filename, not a glob — mirrors CI, where Windows shells don't glob)
RUN pyside6-lrelease src/traffic_light/i18n/traffic_light_ar.ts

COPY tests ./tests
COPY scripts ./scripts
# Qt's offscreen platform runs the UI tests headless — no X server needed.
# (xvfb-run hangs under `docker compose run` on some Docker Desktop versions.)
CMD ["pytest", "-q"]
