"""Single-step response metrics in caller-selected physical units."""
from dataclasses import asdict, dataclass
import csv
import math
from pathlib import Path
from typing import Optional


def finite(value, name):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be a finite number')
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f'{name} must be a finite number') from error
    if not math.isfinite(number):
        raise ValueError(f'{name} must be finite')
    return number


@dataclass(frozen=True)
class Sample:
    time_sec: float
    command: Optional[float] = None
    position: Optional[float] = None

    def __post_init__(self):
        for name in ('time_sec', 'command', 'position'):
            value = getattr(self, name)
            if name == 'time_sec' or value is not None:
                object.__setattr__(self, name, finite(value, name))


@dataclass(frozen=True)
class Metrics:
    start: Optional[float]
    target: float
    unit: str
    tolerance: float
    step_time_sec: float
    settling_time_sec: Optional[float]
    settled: bool
    overshoot: Optional[float]
    overshoot_percent: Optional[float]
    oscillation_count: int
    actual_sample_count: int
    observed_duration_sec: float
    settled_observation_sec: float

    def as_dict(self):
        return asdict(self)


def read_csv(path):
    """Read time_sec,command,position; blank command/position means unavailable."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader, None)
        if header is None or tuple(c.strip() for c in header) != ('time_sec', 'command', 'position'):
            raise ValueError('CSV header must be time_sec,command,position')
        result = []
        for line, row in enumerate(reader, 2):
            if not row or not any(c.strip() for c in row):
                continue
            if len(row) != 3:
                raise ValueError(f'line {line}: expected three columns')
            try:
                result.append(Sample(row[0], *(None if not v.strip() else v for v in row[1:])))
            except ValueError as error:
                raise ValueError(f'line {line}: {error}') from error
    return result


def write_csv(path, samples):
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('time_sec', 'command', 'position'))
        for sample in samples:
            writer.writerow((sample.time_sec, sample.command, sample.position))


def _oscillations(positions, target, band, minimum):
    # Track reversals near target, resetting outside the window. A reversal must
    # reach the minimum amplitude measured from the preceding extreme.
    count = 0
    extreme = direction = None
    for position in positions:
        if abs(position - target) > band:
            extreme = direction = None
        elif extreme is None:
            extreme = position
        else:
            delta = position - extreme
            if direction is None:
                if delta and abs(delta) >= minimum:
                    direction = 1 if delta > 0 else -1
                    extreme = position
            elif delta * direction >= 0:
                extreme = position
            elif abs(delta) >= minimum:
                direction = -direction
                extreme = position
                count += 1
    return count


def analyze(samples, *, target=None, tolerance=0.02, min_delta=0.005,
            oscillation_window=None, settle_duration=0.0, unit='units'):
    """Analyze one transition, requiring an observed in-band trailing interval.

    Commands can be sparse and are held until the next command. Input order is
    retained; timestamps must not decrease. Multiple transitions are rejected:
    split a multi-step recording before calling this function. Missing positions
    after the step interrupt evidence of a sustained in-band interval.
    """
    samples = list(samples)
    if not samples:
        raise ValueError('no samples')
    for left, right in zip(samples, samples[1:]):
        if right.time_sec < left.time_sec:
            raise ValueError('timestamps must not decrease')
    tolerance = finite(tolerance, 'tolerance')
    min_delta = finite(min_delta, 'min_delta')
    settle_duration = finite(settle_duration, 'settle_duration')
    band = tolerance if oscillation_window is None else finite(oscillation_window, 'oscillation_window')
    if min(tolerance, min_delta, settle_duration, band) < 0:
        raise ValueError('tolerances, duration, and minimum delta must be nonnegative')
    if not isinstance(unit, str):
        raise ValueError('unit must be a string')
    commands = [(i, s.command) for i, s in enumerate(samples) if s.command is not None]
    if not commands:
        raise ValueError('command column contains no target command')
    target = commands[-1][1] if target is None else finite(target, 'target')
    if commands[-1][1] != target:
        raise ValueError('target must equal the final command')
    transitions = [(i, v) for k, (i, v) in enumerate(commands)
                   if k == 0 or v != commands[k-1][1]]
    if len(transitions) > 2:
        raise ValueError('multiple command transitions; split recording into individual steps')
    step_index, _ = transitions[-1]
    start = transitions[0][1] if len(transitions) == 2 else None
    if start is None:
        prior = [s.position for s in samples[:step_index] if s.position is not None]
        start = prior[-1] if prior else None
    step_time = samples[step_index].time_sec
    post = samples[step_index:]
    actual = [s for s in post if s.position is not None]
    if not actual:
        raise ValueError('no actual position samples at or after the step')
    # Missing observations reset the trailing interval; no interpolation is made.
    trailing_start = None
    for sample in post:
        if sample.position is None or abs(sample.position - target) > tolerance:
            trailing_start = None
        elif trailing_start is None:
            trailing_start = sample.time_sec
    observed = 0.0 if trailing_start is None else post[-1].time_sec - trailing_start
    settled = trailing_start is not None and observed + 1e-12 >= settle_duration
    direction = 0 if start is None else (1 if target > start else -1 if target < start else 0)
    distance = None if start is None else abs(target - start)
    if direction:
        overshoot = max(0.0, max((s.position-target)*direction for s in actual))
    else:
        overshoot = None
    percent = overshoot / distance * 100 if distance and overshoot is not None else None
    return Metrics(start, target, unit, tolerance, step_time,
                   trailing_start-step_time if settled else None, settled,
                   overshoot, percent,
                   _oscillations([s.position for s in actual], target, band, min_delta),
                   len(actual), post[-1].time_sec-step_time, observed)
