# 常用漢字の全グリフ線長を測定するチュートリアル

このチュートリアルでは、配布フォント「[機械彫刻用標準書体JIS（中）](https://font.kim/ki-cho-jis_0310.zip)」を対象に、本リポジトリの `joyo2svg` コマンドを使って常用漢字 2136 文字の単線化した総延長を一括で算出します。実際に計測コマンドを実行し、成果物として降順に並べた線長リストを公開します。

## 前提条件

- Python 3.11 以上がインストールされていること
- `git`、`curl`、`unzip` が利用できること
- 十分な空きディスク（SVG とレポートで 200MB 程度）と CPU コアを確保できること

## 1. リポジトリの取得と依存関係のインストール

```bash
# リポジトリを取得
 git clone https://github.com/<your-account>/font-length.git
 cd font-length

# 依存関係をインストール（開発モード）
 pip install -e .
```

## 2. フォントのダウンロードと展開

```bash
# フォントのダウンロード
 curl -L -o /tmp/ki-cho-jis_0310.zip https://font.kim/ki-cho-jis_0310.zip

# 展開（OTF ファイルを取り出す）
 unzip -o /tmp/ki-cho-jis_0310.zip -d /tmp/ki-cho-jis
```

展開先に `KikaiChokokuJIS-Md.otf` が生成されます。以降、このパスを指定して計測します。

## 3. 常用漢字 2136 文字を一括測定

以下のコマンドを実行すると、常用漢字リスト全体がマルチプロセスで処理され、各文字の線の総延長、ポリライン数、細線化ピクセル数などが CSV と JSON に書き出されます。

```bash
joyo2svg \
  --font /tmp/ki-cho-jis/KikaiChokokuJIS-Md.otf \
  --out-dir ./out/ki-cho-jis \
  --point-px 640 \
  --canvas-px 960 \
  --margin-px 64 \
  --workers 8
```

- `--point-px`, `--canvas-px`, `--margin-px` は本チュートリアルで実際に使用したラスタライズ設定です。高解像度が必要であれば値を大きくしてくださいが、処理時間は長くなります。
- `--workers` で同時実行プロセス数を指定します。CPU コア数に応じて調整してください。

実行時にはプログレスバーが表示され、今回の環境では約 2 分 18 秒で 2136 文字すべての処理が完了しました。

```text
INFO:font_length.runner:Loaded 2136 characters
INFO:font_length.runner:Using 8 worker(s)
Processing: 100% 2136/2136 [02:17<00:00, 15.49char/s]
INFO:font_length.runner:Processed 2136 glyphs (failures=0) in 137.87s
INFO:font_length.runner:Top character by stroke length: 醸 4777.433
INFO:font_length.cli:Finished conversion: processed=2136 failures=0
```

## 4. 出力物の確認

`--out-dir` で指定したディレクトリには次のファイルが生成されます。

- `UXXXX.svg`: 各文字の単線化 SVG（例: `U91B8.svg` は「醸」）
- `stroke_length_report.csv`: 計測値を Unicode 順に並べた CSV レポート
- `summary.json`: 処理時間や上位文字を含むサマリー

さらに、本チュートリアルでは `stroke_length_report.csv` を線長の降順で並び替えた `stroke_length_report_desc.csv` を追加で生成しました。

```bash
python - <<'PY'
import csv
from pathlib import Path
rows = list(csv.DictReader(open('out/ki-cho-jis/stroke_length_report.csv', newline='', encoding='utf-8')))
rows.sort(key=lambda r: float(r['total_length_px']), reverse=True)
with open('out/ki-cho-jis/stroke_length_report_desc.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
PY
```

## 5. 線長トップ 10 の確認

`summary.json` と並べ替え済み CSV を参照すると、線長が長い文字の傾向を簡単に把握できます。今回のトップ 10 は次の通りです。

| 順位 | 文字 | Unicode | 総延長 (px) |
| ---: | :--- | :------ | ----------: |
| 1 | 醸 | U+91B8 | 4777.433 |
| 2 | 覇 | U+8987 | 4772.458 |
| 3 | 響 | U+97FF | 4730.374 |
| 4 | 醜 | U+919C | 4651.815 |
| 5 | 量 | U+91CF | 4612.078 |
| 6 | 膚 | U+819A | 4607.500 |
| 7 | 襲 | U+8972 | 4599.242 |
| 8 | 薫 | U+85AB | 4573.181 |
| 9 | 欄 | U+6B04 | 4538.188 |
| 10 | 魔 | U+9B54 | 4500.746 |

## 6. 降順リストの公開

常用漢字 2136 文字すべての線長を降順で掲載した Markdown ファイルを `docs/joyo_lengths_ki-cho-jis_desc.md` に追加しました。必要に応じて Excel や BI ツールに読み込んで分析してください。

- [機械彫刻用標準書体JIS（中） 常用漢字 線長リスト（降順）](joyo_lengths_ki-cho-jis_desc.md)

## 7. 応用: 任意のフォントで再利用するには

1. 解析したいフォントを用意し、`--font` にパスを指定します。
2. 解像度やノイズ除去の設定は `joyo2svg --help` で確認し、フォントのデザインに合わせて調整します。
3. 出力された CSV を同様に並び替えれば、別フォントでも降順リストを得られます。

以上で、常用漢字の各グリフの線長を実際に算出し、降順リストを得るチュートリアルは完了です。
