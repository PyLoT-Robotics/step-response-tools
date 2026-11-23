import pytest
from step_response_tools import Sample, analyze


def test_fractional_negative_step_and_observed_settling():
    result = analyze([Sample(0, 1, 1), Sample(1, -1, 1), Sample(2, -1, -1.2),
                      Sample(3, -1, -1.01), Sample(4, -1, -1)], tolerance=0.02,
                     settle_duration=1)
    assert result.settling_time_sec == 2
    assert result.overshoot == pytest.approx(0.2)
    assert result.overshoot_percent == pytest.approx(10)


def test_no_sustained_observation_is_not_settled():
    result = analyze([Sample(0, 0, 0), Sample(1, 1, 0), Sample(2, 1, 1)],
                     tolerance=0.1, settle_duration=1)
    assert not result.settled


def test_positive_overshoot_and_oscillation_reversals():
    samples = [Sample(0, 0, 0), Sample(1, 1, 0), Sample(2, 1, 1.1),
               Sample(3, 1, .99), Sample(4, 1, 1.01), Sample(5, 1, .99)]
    result = analyze(samples, tolerance=.02)
    assert result.overshoot == pytest.approx(.1)
    assert result.overshoot_percent == pytest.approx(10)
    assert result.oscillation_count == 1
    assert result.settling_time_sec == 2


def test_missing_observation_interrupts_settling():
    result = analyze([Sample(0, 0, 0), Sample(1, 1, 1), Sample(2, None, None),
                      Sample(3, None, 1), Sample(3.5, None, 1)], settle_duration=1)
    assert not result.settled
    assert result.settled_observation_sec == .5


def test_final_missing_observation_does_not_declare_settled():
    result = analyze([Sample(0, 0, 0), Sample(1, 1, 1), Sample(2, 1, None)])
    assert not result.settled


def test_sparse_commands_are_held():
    result = analyze([Sample(0, 0, 0), Sample(1, 1, 0), Sample(2, None, 1), Sample(3, None, 1)])
    assert result.settling_time_sec == 1
    assert result.observed_duration_sec == 2


def test_unknown_start_has_unknown_overshoot():
    result = analyze([Sample(0, 1, .5), Sample(1, 1, 1)])
    assert result.overshoot is None
    assert result.overshoot_percent is None


@pytest.mark.parametrize('samples', [[], [Sample(0, None, 0)], [Sample(0, 1, None)],
    [Sample(1, 0, 0), Sample(0, 1, 1)],
    [Sample(0, 0, 0), Sample(1, 1, 1), Sample(2, 0, 0), Sample(3, 1, 1)]])
def test_invalid_or_multistep_records_are_rejected(samples):
    with pytest.raises(ValueError):
        analyze(samples)


@pytest.mark.parametrize('options', [{'tolerance': -1}, {'min_delta': -1},
    {'settle_duration': -1}, {'oscillation_window': -1}, {'tolerance': float('nan')},
    {'settle_duration': True}, {'target': 2}])
def test_invalid_options(options):
    with pytest.raises(ValueError):
        analyze([Sample(0, 0, 0), Sample(1, 1, 1)], **options)


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), 'bad'])
def test_nonfinite_samples(value):
    with pytest.raises(ValueError):
        Sample(value, 1, 1)


def test_csv_roundtrip_and_cli_formats(tmp_path, capsys):
    import json, csv
    from step_response_tools import read_csv, write_csv
    from step_response_tools.cli import main
    path = tmp_path / 'input.csv'
    samples = [Sample(0, 0, 0), Sample(1, 1, 0), Sample(2, None, 1), Sample(3, None, 1)]
    write_csv(path, samples)
    assert read_csv(path) == samples
    assert main([str(path), '--tolerance', '.01', '--settle-duration', '1', '--unit', 'rad']) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['unit'] == 'rad'
    assert report['settling_time_sec'] == 1
    output = tmp_path / 'report.csv'
    assert main([str(path), '--format', 'csv', '--output', str(output)]) == 0
    with output.open() as stream:
        assert next(csv.DictReader(stream))['settled'] == 'True'
    assert main([str(path), '--format', 'text']) == 0
    assert 'settling_time_sec: 1.0' in capsys.readouterr().out


@pytest.mark.parametrize('text', ['', 'bad,headers\n', 'time_sec,command,position\n0,1\n',
                                 'time_sec,command,position\n0,1,nan\n'])
def test_cli_input_errors(tmp_path, capsys, text):
    from step_response_tools.cli import main
    path = tmp_path / 'bad.csv'
    path.write_text(text)
    assert main([str(path)]) == 2
    assert 'step-response:' in capsys.readouterr().err
