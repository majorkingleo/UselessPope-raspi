# Database access

The Python side talks to a local MySQL/MariaDB instance through a single module,
`python/config.py`. The database is shared with the C++ `broker`
(`~/UselessPope-Broker`) and the PHP web frontend (`UselessPope-www`).

## Connection details

- Driver: `MySQLdb` (mysqlclient).
- Host: hardcoded `localhost` (uses the default Unix socket
  `/run/mysqld/mysqld.sock`).
- Credentials + instance come from `~/.UselessPope-Broker.ini`:

  ```ini
  [database]
  host = localhost
  username = papst
  password = johannespaul
  instance = papst
  retry_db_timeout = 60
  ```

  `config.py` only reads `username`, `password`, `instance`; `host` in the file
  is currently ignored in favour of the hardcoded `"localhost"`.

- Availability check:

  ```python
  def is_db_available():
      socket = Path('/run/mysqld/mysqld.sock')
      return socket.exists()
  ```

  This is a cheap existence check on the socket file, not a real connection
  probe. Scripts use it to spin-wait for MariaDB before constructing `Config`.

## `config.py` API

```python
from config import Config, is_db_available

config = Config()          # opens a MySQLdb connection, db = papst

value = config.get(key)             # SELECT value FROM CONFIG WHERE `key`=key
config.put(key, value)              # UPDATE CONFIG SET value, hist_ae_* WHERE `key`=key
config.write_stats(key, value)      # UPDATE STATS SET value WHERE `key`=key
stats = config.get_stats(key)       # SELECT value FROM STATS WHERE `key`=key
config.db                           # raw MySQLdb connection (cursor() etc.)
```

Notes on the existing implementation:

- `get()` and `get_stats()` return `None` when the key is not found.
- `put()` also stamps `hist_ae_zeit = CURRENT_TIMESTAMP()` and
  `hist_ae_user = 'papst'`.
- Every read runs a `cursor.execute("commit")` after fetching to reset the
  session state (the connection is created with `AUTOCOMMIT=0`).
- All queries are built with Python `str.format()` string interpolation — there
  is **no SQL escaping**. This is safe only because keys/values are internal and
  trusted. If you add any user-supplied input, switch to parameterized queries
  (`cursor.execute("... WHERE `key`=%s", (key,))`), as the bundled helper does.

## Schema (from `~/UselessPope-Broker/create.sql`)

The tables the Python scripts touch:

### `CONFIG`

Runtime settings. Columns: `idx` (PK, auto-inc), `hist_an_zeit`, `hist_an_user`,
`hist_ae_zeit`, `hist_ae_user`, `hist_lo_zeit`, `hist_lo_user`, `key`
(VARCHAR 50), `value` (VARCHAR 1024).

### `STATS`

Counters / computed stats. Identical structure to `CONFIG` (`key` VARCHAR 50,
`value` VARCHAR 1024), but conceptually read-mostly, updated by animations and
by the broker's `FetchStats` thread.

### `PLAY_QUEUE_ANIMATION`

Queue consumed by the broker to launch an animation. Columns include the same
`hist_*` audit columns plus `file` (VARCHAR 1024). Written directly by
`ring_animation.py` via raw SQL:

```python
cursor = config.db.cursor()
cursor.execute(
    "insert into PLAY_QUEUE_ANIMATION( hist_an_user, hist_ae_user, hist_lo_user, file ) "
    "values( 'papst', 'papst', 'papst', '{0}' )".format(animation_file))
cursor.execute("commit")
```

### Other tables (used by broker/web, not by Python)

`PLAY_QUEUE_CHUNKS`, `PLAY_QUEUE_MUSIC`, `BUTTON_QUEUE`, `USERS_ACTIONS`,
`USERS`, `SERMON`, and the `P_*` prefixed archive tables. `CONFIG` and `STATS`
are the only tables the Python scripts read/write directly.

## Config key inventory

Seeded by `~/UselessPope-Broker/src/main.cc` → `insert_default_values()`:

| key | default | used by |
|-----|---------|---------|
| `brightness` | `0.02` | every animation (polled, 0..~0.8) |
| `current_animation` | `0` | `ring_animation.py` (which animation is active) |
| `fog` | `0` | `ring_fog.py` (fog machine state) |
| `animation0` | `.../pope_default_rotating_color_wheel.py` | broker launches this file |
| `animation1` | `.../pope_red_eyes.py` | |
| `animation2` | `.../matrix_rain.py` | |
| `animation3` | `.../snake_duel.py` | |
| `animation4` | `.../screen_off.py` | |
| `animation5` | `.../text_scroll.py` | text marquee (added outside broker defaults) |
| `scroll_text` | `LAN 2.1` | `text_scroll.py` message to display |
| `animation<N>_title` | e.g. `Johannes Paul II` | web UI titles |

## Stats key inventory

Seeded by the broker and maintained by animations / `FetchStats`:

| key | meaning | written by |
|-----|---------|-----------|
| `umdrehungen` | total rotations (RPM counter) | `pope_*` animations |
| `frequenz` | rotation frequency (RPM) | `pope_*`, `matrix_rain`, `screen_off` |
| `snake_p1_wins` | Snake player 1 wins | `snake_duel.py` |
| `snake_p2_wins` | Snake player 2 wins | `snake_duel.py` |
| `mostplayedsound` | most played sound | broker `FetchStats` |
| `active-leds-data` | active panels mask (e.g. `0123`) | broker |
| `user1`..`user3` | top users | broker `FetchStats` |
| `totalactions` | total button actions | broker `FetchStats` |

## Debugging tips

- "Database not available" hangs → the socket check
  `/run/mysqld/mysqld.sock` is failing; confirm MariaDB is up
  (`systemctl status mariadb` / `mysqladmin ping`).
- If `Config()` raises, check `~/.UselessPope-Broker.ini` exists and has the
  `[database]` section.
- To inspect current values safely without `config.py`'s string interpolation,
  use the bundled `scripts/db_query.py`.
- Note `get()`/`get_stats()` return strings; numeric keys must be cast
  (`float(...)` / `int(...)`) — see the brightness loop in the animations.
