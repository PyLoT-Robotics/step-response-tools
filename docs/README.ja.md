# Step Response Tools

[English](../README.md) | 日本語

CSVに記録した1回のステップ応答から、観測内の整定時間・行き過ぎ量・行き過ぎ率・目標付近の振動方向の反転回数を計算するCLIとPythonライブラリです。角度・距離・速度・サーボtickなど一貫した単位で利用でき、小数の許容幅を指定できます。

Python 3.10以上で動き、ROSや外部の実行時依存はありません。モータへの指令や実機録画は行いません。

## インストールと実行

リポジトリ直下で実行します。

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
step-response examples/response.csv --unit rad --tolerance 0.02 --settle-duration 0.5
step-response examples/response.csv --format csv --output report.csv
python -m pytest -q
```

`python -m step_response_tools.cli`でも実行できます。[同梱例](../examples/response.csv)は合成データで、1.0秒に指令が0から1へ変わり、行き過ぎ0.1（10%）、整定時間0.6秒、最終許容帯内の観測期間0.6秒を得ます。実機の性能測定ではありません。

## 入力

CSVの列は`time_sec,command,position`です。指令と実位置は同じ単位、時刻は秒です。

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

時刻は有限で非減少とし、同時刻の行はファイル順で扱います。指令の空欄は直前の指令を保持、位置の空欄は未観測を示します。空行は無視し、列数の不正やNaN/Infはエラーにします。ヘッダー前後の空白とUTF-8 BOMは許容します。

初期指令から目標への1回の遷移を記録してください。複数ステップは自動混合せずエラーにするため、あらかじめ分割してください。初期指令がなければ、目標指令前の実位置があれば開始値に使います。開始値が不明、または振幅ゼロの場合、行き過ぎ量・率は`null`です。

## 指標

- `settling_time_sec`：目標指令から、最後まで許容帯内に留まる観測区間の先頭までの秒数。未確認なら`null`。
- `settled`：最終許容帯内区間が`--settle-duration`以上あるか。
- `overshoot` / `overshoot_percent`：上昇・下降の向きに合わせた最大行き過ぎ量と、指令変化幅に対する百分率。
- `oscillation_count`：目標付近で最小変化量以上の向きの反転回数。完全な振動周期数ではありません。
- `actual_sample_count`：目標指令以後の実位置サンプル数。
- `observed_duration_sec`：目標指令から記録末尾までの秒数。
- `settled_observation_sec`：末尾の途切れない許容帯内観測期間。

位置が欠測した行は整定区間をリセットします。`--settle-duration`の既定は0なので、最後の1点が帯内でも整定扱いになります。確認期間が必要なら正の秒数を指定してください。サンプル間の位置は補間・検証しません。ここでの整定は記録内の確認であり、将来の安定や未観測区間を保証しません。

## オプション

| オプション | 既定 | 意味 |
|---|---|---|
| `--target` | 最後の指令 | 最終指令と一致する目標値 |
| `--tolerance` | `0.02` | 目標±Nの絶対許容幅 |
| `--min-delta` | `0.005` | 振動の反転と数える最小変化量 |
| `--oscillation-window` | 許容幅と同じ | 振動を数える目標付近の範囲 |
| `--settle-duration` | `0.0` | 最終許容帯内の必要観測期間（秒） |
| `--unit` | `units` | 単位ラベル。換算は行わない |
| `--format` | `json` | `json` / `csv` / `text` |
| `--output` | 標準出力 | 出力ファイル。親ディレクトリは事前作成 |

帯外に出ると振動方向の追跡をリセットし、行き過ぎの山を振動そのものとは数えません。正常解析は未整定も含め終了コード0、入出力エラーは2です。未取得の指標はJSONで`null`、CSVで空欄になります。

Pythonでは`Sample`、`analyze`、`read_csv`、`write_csv`を利用できます。使用例は[英語README](../README.md)を参照してください。上昇・下降応答、小数、欠測、複数ステップ拒否、CSV往復、CLI各形式をテストしています。

## ライセンス

Apache-2.0。[LICENSE](../LICENSE)、[出典と変更範囲](../PROVENANCE.md)を参照してください。
