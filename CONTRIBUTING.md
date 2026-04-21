# DMiME への貢献ガイド

辞書データは `src/` 以下の TSV ファイル群がマスタです。編集はここだけで行ってください。

## src/ のファイル構成

よみの **先頭 1 文字** で 50音バケットに振り分けます。拗音 (例「きゅう」) は先頭が「き」なので `ka.tsv` に入ります。

```
src/
  a.tsv        あ行 (あいうえお + 小書き + ゔ)
  ka.tsv       か行 (清音)
  ga.tsv       が行 (濁音)
  sa.tsv       さ行 (清音)
  za.tsv       ざ行 (濁音)
  ta.tsv       た行 (清音 + っ)
  da.tsv       だ行 (濁音)
  na.tsv       な行
  ha.tsv       は行 (清音)
  ba.tsv       ば行 (濁音)
  pa.tsv       ぱ行 (半濁音)
  ma.tsv       ま行
  ya.tsv       や行 (や・ゆ・よ + 小書き)
  ra.tsv       ら行
  wa.tsv       わ行 (わ・ゐ・ゑ・を・ん)
  _ascii.tsv   半角/全角英数字・記号で始まるエントリ
  _special.tsv 特殊挙動の品詞 (短縮よみ / 抑制単語 / サジェストのみ)
```

`#` で始まる行と空行はパーサが無視するので、注釈や区切りとして使えます。

## TSV フォーマット (4 列)

```
よみ<TAB>語<TAB>platform<TAB>品詞
```

| 列 | 内容 |
| --- | --- |
| `よみ` | ひらがな or 英数字 |
| `語` | 変換結果 |
| `platform` | `both` (推奨) / `ime` / `mac` |
| `品詞` | `名詞` (基本) / `固有名詞` / `名詞サ変` / `短縮よみ` / `抑制単語` / `サジェストのみ` |

`platform` は配布チャネル:

| タグ | 載るチャネル |
| --- | --- |
| `both` | IME 辞書 (Google + MS IME) と Mac ユーザ辞書の両方 |
| `ime` | IME 辞書のみ |
| `mac` | Mac ユーザ辞書のみ |

`品詞` は `名詞` を基本に、必要に応じて他を使用。`短縮よみ` / `抑制単語` / `サジェストのみ` は `_special.tsv` に、それ以外 (`名詞` / `固有名詞` / `名詞サ変`) は 50音バケットに入れてください。品詞名は Google 日本語入力の正式名で書き、MS IME 版への変換 (`名詞サ変` → `サ変名詞` 等) はビルド時に自動適用されます。

## 追加・編集

1. 該当の `src/*.tsv` を編集
2. commit → push
3. CI (`validate-src`) がパースとビルドを検証

GitHub Web エディタだけで完結します。ローカル Python は必須ではありません。

## ローカルで内容を確認する場合 (任意)

```
python3 scripts/build_release.py
```

作業ツリーに `GoogleIME/DMiME.txt` / `WindowsIME/DMiME.txt` / `Mac/…plist` が生成されます (`.gitignore` 対象、コミット不要)。実 IME に import してのテストに使えます。

リリース用の zip/plist を手元で作る場合:

```
python3 scripts/build_release.py --dist=dist/ --version=1.2
```

## リリース

`v<X.Y>` のタグを push すると `build-release.yml` が自動でビルド・公開します:

- `DMiME-<X.Y>.zip` — Google 日本語入力用
- `DMiME-<X.Y>-msime.zip` — Microsoft IME 用
- `DMiME-<X.Y> igakujisho for icloud.plist` — Mac ユーザ辞書用

```
git tag v1.2
git push origin v1.2
```

## ライセンス

GPL-2.0。
