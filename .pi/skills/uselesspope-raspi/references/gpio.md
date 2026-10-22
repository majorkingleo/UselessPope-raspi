# GPIO (libgpiod v2)

The GPIO code uses **libgpiod v2** (`import gpiod`, `import gpiod.line`) — the
modern object API, not the deprecated v1 `gpiod.Chip("...")` string API.

## `GpiodBase.py`

```python
class GpiodBase:
    def generate_gpio_chips(self):
        for entry in os.scandir("/dev/"):
            if gpiod.is_gpiochip_device(entry.path):
                yield entry.path

    def find_line_by_name(self, line_name):
        # returns (chip_path, offset) for the first line matching line_name
```

`find_line_by_name` scans all `/dev/gpiochip*` devices and resolves a line by
name (e.g. `"GPIO23"`). Raises `RuntimeError` if not found.

## Input pattern (button / ring detection)

`ring.py`, `ring_animation.py`, `ring_brightness.py` share this shape:

```python
class Ring(GpiodBase.GpiodBase):
    PIN_NAME = "GPIO24"          # or GPIO23 etc.
    def __init__(self, gpio_pin: str):
        super().__init__()
        (self.chip, self.offset) = self.find_line_by_name(gpio_pin)
        self.config = {self.offset: gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)}
        self.request = gpiod.request_lines(self.chip, config=self.config)

    def detect_ringing(self):
        if self.request.get_value(self.offset) == gpiod.line.Value.ACTIVE:
            self.is_ringing = True

    def run(self):
        while True:
            self.detect_ringing()
            if self.is_ringing:
                # ... do action ...
                sleep(0.3)
            self.is_ringing = False
            sleep(0.05)
```

CLI contract (each `if __name__ == "__main__"`):

```text
Usage: python <file>.py <GPIO_PIN_NAME> [GPIO1,GPIO7,GPIO8,GPIO16,GPIO25]
```

## Output pattern (fog machine)

`fog.py`:

```python
class Fog(GpiodBase.GpiodBase):
    Fog_PIN_NAME = "GPIO23"
    def __init__(self):
        (self.Fog_chip, self.Fog_offset) = self.find_line_by_name(self.Fog_PIN_NAME)
        self.Fog_config = {self.Fog_offset: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)}
        self.Fog_request = gpiod.request_lines(self.Fog_chip, config=self.Fog_config)

    def on(self):  self.Fog_request.set_value(self.Fog_offset, gpiod.line.Value.ACTIVE)
    def off(self): self.Fog_request.set_value(self.Fog_offset, gpiod.line.Value.INACTIVE)
    def toggle(self):
        # returns 1 if now on, 0 if now off
```

## GPIO-triggered actions

| script | trigger (pin) | action |
|--------|---------------|--------|
| `ring.py` | input | enqueue a random sound chunk via broker `-enqueue-chunk` |
| `ring_animation.py` | input (default GPIO24) | cycle `current_animation`, enqueue into `PLAY_QUEUE_ANIMATION` |
| `ring_brightness.py` | input | step `brightness` (0.1 increments, wraps at 0.8 → 0.02) |
| `ring_motor.py` | input | enqueue music via broker `-enqueue-music` |
| `ring_fog.py` | input | toggle fog + reconcile with `CONFIG.fog` (also auto-applies remote fog changes every 0.5 s) |

`ring_fog.py` polls `CONFIG.fog` every 0.5 s and toggles the relay when the
value differs from the local state, so the fog machine can be controlled both by
the physical button and by writing the `fog` key remotely.

## Notes / gotchas

- `ring.py` and `ring_motor.py` shell out to the broker with
  `os.system(...)`, passing JSON-encoded (or plain) file paths. They assume the
  broker binary is at `/home/papst/UselessPope-Broker/broker`.
- `ring.py` searches `/var/www/share/Soundboard` recursively for chunks;
  `ring_motor.py` lists `/home/papst/audio_motor` non-recursively.
- Pins are resolved by name, so the literal `GPIO23`/`GPIO24` defaults in the
  class attributes are overridden by the constructor argument in the input
  scripts.
