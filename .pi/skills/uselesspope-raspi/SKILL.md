---
name: uselesspope-raspi
description: Working knowledge of the UselessPope Raspberry Pi project — the Python LED/NeoPixel animation and GPIO scripts, the MySQL/MariaDB access layer (config.py), and the broker. Use when reading, modifying, or extending the Python scripts under python/, adding a new animation, changing config/stats keys, or debugging database access in this repo.
---

# UselessPope Raspi

A Raspberry Pi drives an animatronic "Pope" (German: *Papst*): a 32×32
NeoPixel LED matrix (4 panels of 16×16 = 1024 pixels), GPIO inputs/outputs for a
fog machine and buttons, and a separate C++ `broker` daemon that plays sounds,
music, and runs animations. The Python scripts in this repo are the LED
animations, GPIO handlers, and the database glue.

Everything lives in `python/`. The canonical database schema and default config
values live in the sibling project `~/UselessPope-Broker` (not this repo), but
the Python side connects to the same database.

## When to use this skill

- Reading or explaining any file in `python/`.
- Adding, modifying, or debugging a NeoPixel/LED animation.
- Changing how config or stats are read/written to MySQL.
- Understanding the `CONFIG` / `STATS` / `PLAY_QUEUE_*` tables.
- Wiring up a new GPIO input (button / ring detection) or output (fog).

## Quick orientation

| Area | File(s) | Purpose |
|------|---------|---------|
| DB access layer | `python/config.py` | `Config` class + `is_db_available()` — the *only* Python code that talks to MySQL. |
| LED driver | `python/LEDMatrix.py` | `LEDMatrix` / `Pi5Pixelbuf`, 4-panel mapping to a 32×32 buffer. |
| GPIO helpers | `python/GpiodBase.py`, `python/fog.py` | libgpiod v2 line lookup, fog on/off/toggle. |
| Input → action | `python/ring*.py`, `python/ring_animation.py` | GPIO triggers that read/write config, toggle fog, or enqueue animations. |
| Animations | `pope_default_rotating_color_wheel.py`, `pope_red_eyes.py`, `matrix_rain.py`, `snake_duel.py`, `screen_off.py`, `led_animation.py` | The actual displays (selected by `CONFIG.current_animation`). |
| Image display | `python/send_image.py` | Render a static image or animated GIF to the matrix. |
| SPI variant | `python/led_spi.py`, `light_chain_*.py` | Alternate/experimental SPI and single-chain LED code (not DB-connected). |

## Key facts to remember

1. **All DB access goes through `config.py`.** Scripts never import `MySQLdb`
   directly (only `config.py` does). Scripts `import config` and either call
   `config.is_db_available()` or instantiate `config.Config()`.
2. **DB credentials are not in this repo.** They come from
   `~/.UselessPope-Broker.ini`, section `[database]`: `username`, `password`,
   `instance` (host is hardcoded `localhost`).
3. **Startup guard pattern** — LED scripts wait for MariaDB before connecting:
   ```python
   while not config.is_db_available():
       time.sleep(0.3)
   config = config.Config()
   ```
   `is_db_available()` just checks that `/run/mysqld/mysqld.sock` exists.
4. **Two key/value tables** are used: `CONFIG` (settings like `brightness`,
   `fog`, `current_animation`, `animation0`…) and `STATS` (counters like
   `umdrehungen`, `frequenz`, `snake_p1_wins`).
5. **Brightness hot-reload** — animations poll `config.get('brightness')` every
   0.5 s and recreate the `LEDMatrix` object when it changes.

For details see:
- [references/database.md](references/database.md) — schema, `config.py` methods, config/stats key inventory, SQL injection caveat.
- [references/animations.md](references/animations.md) — how animations are structured, the 32×32 buffer, brightness pattern, and how to add a new animation.
- [references/gpio.md](references/gpio.md) — libgpiod v2 usage, `GpiodBase`, fog and ring handlers.

## Common tasks

### Read/write a config or stats value from the CLI

Use the bundled helper (safe, parameterized queries):

```bash
python3 .pi/skills/uselesspope-raspi/scripts/db_query.py get brightness
python3 .pi/skills/uselesspope-raspi/scripts/db_query.py set brightness 0.10
python3 .pi/skills/uselesspope-raspi/scripts/db_query.py get-stat umdrehungen
python3 .pi/skills/uselesspope-raspi/scripts/db_query.py list
```

### Add a new animation

1. Create `python/<name>.py` following the brightness-polling loop pattern in
   `pope_default_rotating_color_wheel.py` (see references/animations.md).
2. Register it in the broker's `insert_default_values()` (in
   `~/UselessPope-Broker/src/main.cc`) as `animation<N>` + `animation<N>_title`,
   or insert a row into `CONFIG` directly:
   ```sql
   INSERT INTO CONFIG (key, value, hist_an_user, hist_ae_user, hist_lo_user)
   VALUES ('animation5', '/home/papst/UselessPope-raspi/python/my_new.py', 'papst','papst','papst');
   ```
3. `ring_animation.py` cycles `current_animation` and enqueues the file into
   `PLAY_QUEUE_ANIMATION`; the broker actually spawns it.

### Track a new counter

`STATS` rows are free-form (`key`, `value`). Write with
`config.write_stats("my_counter", str(n))` and read back with
`config.get_stats("my_counter")`. The broker's `FetchStats` (see
`~/UselessPope-Broker/src/FetchStats.h`) exposes several keys to the web UI, so
extend that too if the value must appear in the frontend.
