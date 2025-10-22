# 「鬱」の線の長さを算出するチュートリアル

このチュートリアルでは、配布されているフォント「[機械彫刻用標準書体JIS（中）](https://font.kim/ki-cho-jis_0310.zip)」を使って、漢字「鬱」の単線化した総延長を本リポジトリのツールで実際に計測します。

## 前提条件

- Python 3.11 以上がインストールされていること
- `git` と `curl`、`unzip` が利用できること

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

# 展開（OTF ファイルを取り出します）
 unzip -o /tmp/ki-cho-jis_0310.zip -d /tmp/ki-cho-jis
```

展開先の `/tmp/ki-cho-jis` に `KikaiChokokuJIS-Md.otf` が生成されます。

## 3. 単一文字を計測するスクリプトの実行

本リポジトリには任意の 1 文字を計測する `examples/measure_character.py` を用意しています。次のコマンドで「鬱」を測定します。

```bash
python examples/measure_character.py 鬱 /tmp/ki-cho-jis/KikaiChokokuJIS-Md.otf --out-svg ./utsu.svg
```

主なオプションは以下の通りです。

- `鬱`: 計測したい文字を 1 文字で指定します。
- `/tmp/ki-cho-jis/KikaiChokokuJIS-Md.otf`: 計測に使用するフォントファイルへのパスです。
- `--out-svg ./utsu.svg`: 単線化した結果を SVG として保存したい場合に指定します（任意）。

## 4. 実行結果の確認

上記のコマンドを実行すると、次のような出力が得られます。

```text
Character: 鬱
Total stroke length (px): 9429.945
Bounds (min_x, min_y, width, height): (192.0, 192.0, 1350.0, 1530.0)
Polyline count: 11
Wrote SVG to utsu.svg
```

`Total stroke length (px)` が計測された線の総延長で、この例では約 **9429.945 ピクセル** です。`Bounds` は描画時の座標範囲、`Polyline count` は単線化後のポリライン数を表しています。`--out-svg` を指定した場合、カレントディレクトリに `utsu.svg` が生成され、線の形状を確認できます。

## 5. パラメータの調整

必要に応じて以下のオプションで計測条件を変更できます。

- `--point-px`: ラスタライズ時のフォントサイズ（ピクセル）
- `--canvas-px`: レンダリングキャンバスの大きさ（ピクセル）
- `--margin-px`: キャンバス外周の余白（ピクセル）
- `--binarize`: 2 値化手法（`otsu` または `fixed`）
- `--binary-threshold`: 固定しきい値を使う場合の値
- `--min-obj-area`: ノイズとして除去する最小領域（ピクセル数）
- `--spur-prune`: 細線化後に除去するスパーの長さ（ピクセル）
- `--simplify-eps`: Ramer–Douglas–Peucker 法による線分単純化の許容誤差

各オプションを調整し、必要な解像度や表現に合わせて再計測してください。

これで「鬱」の線の長さを算出する手順は完了です。
