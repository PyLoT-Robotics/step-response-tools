# Step Response Tools

English | [日本語](docs/README.ja.md)

Analyze a recorded **single-step response** from CSV: observed settling time, directional overshoot, overshoot percentage, and small-amplitude oscillation reversals. Works with angle, distance, speed, servo ticks, or any consistent unit. No ROS, hardware connection, or runtime dependencies beyond Python 3.10+.

Adapted from PyLoT's pan-servo evaluation tooling, with fractional tolerances and explicit observation-duration checks instead of machine-specific tick limits.

## Install and try

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
step-response examples/response.csv --unit rad --tolerance 0.02 --settle-duration 0.5
step-response examples/response.csv --format csv --output report.csv
python -m pytest -q
```

`python -m step_response_tools.cli` is equivalent to `step-response`. The example is synthetic: its command changes from 0 to 1 at 1.0 s, overshoots by 0.1 (10%), and enters the final ±0.02 band at 1.6 s. The reported settling time is 0.6 s, with 0.6 s of subsequent observed in-band response. It is not a benchmark of a physical servo.

## Input CSV

```csv
time_sec,command,position
0,0,0
1,1,0
1.2,,0.6
1.4,,1.1
1.6,,0.99
1.8,,1.01
2.0,,1.0
2.2,,1.0
```

The header must be exactly these three columns, in this order (surrounding whitespace and a UTF-8 BOM are accepted). `time_sec` must be finite and nondecreasing; equal timestamps retain file order. Blank command values mean the previous command remains active. A blank position means an unavailable observation. Blank rows are ignored; malformed rows and NaN/Inf are rejected.

Record the initial command, then one target transition. A file with more than one command transition is rejected: split multi-step logs first. With no initial command, a position recorded before the first target command is used as the start when available. If the starting value is unknown, overshoot and overshoot percentage are `null`.

## Metrics and their limits

| Output | Meaning |
|---|---|
| `step_time_sec` | Timestamp of the target command's first row in the single transition |
| `settling_time_sec` | Time from that command to the first sample in the final observed in-band interval; `null` if unconfirmed |
| `settled` | Final interval is in-band and spans at least `--settle-duration` seconds |
| `overshoot` | Maximum excursion beyond the target in the step direction, in the selected unit |
| `overshoot_percent` | Overshoot / absolute initial-to-target command change × 100 |
| `oscillation_count` | Near-target direction reversals exceeding `--min-delta`; this is a reversal count, not full cycles |
| `actual_sample_count` | Number of measured positions at or after the target command |
| `observed_duration_sec` | Time from target command to the end of the record |
| `settled_observation_sec` | Length of the final uninterrupted observed in-band interval |

Missing positions reset the final in-band interval. `--settle-duration` defaults to 0: a final in-band sample is enough in this mode. Set a positive duration to require a longer observed suffix. The analyzer does not interpolate or verify positions between samples; sparse sampling can hide motion. Settled means sustained **within the available recording**, not a guarantee about future behavior. A zero-amplitude step has undefined overshoot (`null`).

The oscillation window defaults to the settling tolerance. Samples outside it reset direction tracking, so the overshoot peak is not itself counted as a near-target oscillation.

## CLI options

| Option | Default | Purpose |
|---|---|---|
| `--target` | Last nonblank command | Explicit target; must match the final command |
| `--tolerance` | `0.02` | Nonnegative absolute target-band half-width |
| `--min-delta` | `0.005` | Minimum change to count an oscillation reversal |
| `--oscillation-window` | Same as tolerance | Near-target band used for reversal counting |
| `--settle-duration` | `0.0` | Minimum observed trailing in-band duration, seconds |
| `--unit` | `units` | Label only; values are not converted |
| `--format` | `json` | `json`, `csv`, or `text` |
| `--output` | stdout | Save the report to an existing parent directory |

Success returns exit code 0, including a valid but unsettled response. Input/output errors return 2 with a message on stderr. JSON uses `null` for unavailable metrics; CSV uses empty fields.

## Python API

```python
from step_response_tools import Sample, analyze

metrics = analyze([
    Sample(0, 0, 0), Sample(1, 1, 0),
    Sample(2, None, 1.01), Sample(3, None, 1.0),
], tolerance=0.02, settle_duration=1.0, unit="rad")
assert metrics.settling_time_sec == 1.0
print(metrics.as_dict())
```

`read_csv()` and `write_csv()` use the same `Sample` format. Tests include positive/negative steps, fractional tolerance, overshoot, reversals, missing observations, unknown start, multi-step rejection, invalid data, CSV round trips, and CLI JSON/CSV/text output.

## License and origin

Apache-2.0. See [LICENSE](LICENSE) and [PROVENANCE.md](PROVENANCE.md). This tool only analyzes existing data; it never commands a motor or records hardware.
