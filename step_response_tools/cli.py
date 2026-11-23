"""Command-line CSV analysis and machine-readable reports."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys
from .analysis import analyze, read_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description='Analyze a single-step response CSV without sending robot commands.')
    parser.add_argument('csv', type=Path)
    parser.add_argument('--target', type=float)
    parser.add_argument('--tolerance', type=float, default=0.02)
    parser.add_argument('--min-delta', type=float, default=0.005)
    parser.add_argument('--oscillation-window', type=float)
    parser.add_argument('--settle-duration', type=float, default=0.0)
    parser.add_argument('--unit', default='units')
    parser.add_argument('--format', choices=['json', 'csv', 'text'], default='json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        metrics = analyze(read_csv(args.csv), target=args.target, tolerance=args.tolerance,
                          min_delta=args.min_delta, oscillation_window=args.oscillation_window,
                          settle_duration=args.settle_duration, unit=args.unit).as_dict()
        if args.format == 'json':
            report = json.dumps(metrics, indent=2, allow_nan=False) + '\n'
        elif args.format == 'csv':
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=list(metrics))
            writer.writeheader()
            writer.writerow(metrics)
            report = out.getvalue()
        else:
            report = '\n'.join(f'{key}: {value}' for key, value in metrics.items()) + '\n'
        if args.output:
            args.output.write_text(report, encoding='utf-8')
        else:
            print(report, end='')
    except (OSError, ValueError) as error:
        print(f'step-response: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
