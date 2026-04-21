# DMiME への貢献ガイド

DMiME の辞書データは **`src/` 以下の TSV ファイル群が唯一のマスタ** です。IME 別の配布用ファイル (Google 日本語入力・Microsoft IME・Mac ユーザ辞書用) は `scripts/build_release.py` が `src/` から生成する **一時的な成果物** であり、git には含めず Releases を通じてのみ配布します。

## なぜ成果物を git に入れないのか

- `src/` だけがマスタなので、成果物との drift が構造的に発生しない
- 成果物を誤編集しても「CI に静かに上書きされて消える」footgun が起きない
- リリースは Git タグ (`v<X.Y>`) が唯一のトリガ。README も Releases への導線で統一されている

手元で内容を確認したいときは `python3 scripts/build_release.py` を実行すると `GoogleIME/` / `WindowsIME/` / `Mac/` フォルダが作業ツリーに生成されます (`.gitignore` 済み、コミット対象外)。

## src/ ファイル構成

通常変換の単語は **よみの先頭 1 文字** で 50音バケットに振り分けます:

```
src/
  a.tsv    あ行 (あいうえお + 小書き + ゔ)
  ka.tsv   か行 (清音)
  ga.tsv   が行 (濁音)
  sa.tsv   さ行 (清音)
  za.tsv   ざ行 (濁音)
  ta.tsv   た行 (清音 + っ)
  da.tsv   だ行 (濁音)
  na.tsv   な行
  ha.tsv   は行 (清音)
  ba.tsv   ば行 (濁音)
  pa.tsv   ぱ行 (半濁音)
  ma.tsv   ま行
  ya.tsv   や行 (や・ゆ・よ + 小書き)
  ra.tsv   ら行
  wa.tsv   わ行 (わ・ゐ・ゑ・を・ん)
  _ascii.tsv   半角/全角英数字・記号で始まるエントリ
```

拗音 (例「きゅう」) は先頭が「き」なので `ka.tsv` に入ります。

**通常変換でないエントリは専用ファイルにまとめます:**

```
  _special.tsv   特殊挙動の単語 (短縮よみ / 抑制単語 / サジェストのみ)
```

これらは「よみを打つとふつうに変換候補に出る」とは異なる挙動 (単独時のみ展開・抑制・サジェスト専用) のため、件数は少ないもののレビューしやすいよう 1 ファイルに集約しています。新しく対応する特殊品詞 (原典にはないが将来追加したいもの) もここに入れてください。一方 `名詞` / `固有名詞` / `名詞サ変` は通常変換なので 50音バケットに入ります。

ビルド時に `_special.tsv` のエントリは自動的にそのよみの 50音バケットに合流して出力されるので、配布ファイル上の並び順は変わりません。ファイル内部ではカテゴリ (短縮よみ / サジェストのみ / 抑制単語) ごとにセクションを分け、先頭 `#` のコメント行で見出しを付けています。`#` 始まりの行と空行はパーサが無視するので、注釈や区切りとして自由に使えます (50音バケットファイルでも同様)。

## TSV フォーマット (4 列)

```
よみ<TAB>語<TAB>platform<TAB>品詞
```

| 列 | 内容 |
| --- | --- |
| `よみ` | ひらがな or 英数字。入力するひらがな表記 |
| `語` | 変換結果の文字列 |
| `platform` | `ime` / `mac` / `both` のいずれか (下表参照) |
| `品詞` | 基本は `名詞`。原典に由来する例外として `固有名詞` / `名詞サ変` (以上は 50音バケットに入れる) / `短縮よみ` / `抑制単語` / `サジェストのみ` (以上は `_special.tsv` に入れる) あり |

### `platform` タグの選び方

`platform` は **どの配布チャネルに載せるか** を表します。OS ではなく配布形式 (IME 辞書 TSV か / Mac ユーザ辞書 plist か) の区別です。

| タグ | 載るチャネル |
| --- | --- |
| **`both`** (推奨) | IME 辞書 (GoogleIME + WindowsIME) と Mac ユーザ辞書の両方 |
| **`ime`** | IME 辞書のみ (GoogleIME と WindowsIME 双方) |
| **`mac`** | Mac ユーザ辞書のみ |

`ime` は同じ 1 ソースから Google 日本語入力形式と Microsoft IME 形式の両方が自動派生します (ビルドが形式変換します)。新規追加は原則 `both` を選んでください。`ime` または `mac` を使うのは「他方のチャネル側でその語がすでにカバーされている」などの明確な理由があるときのみです。

## 追加・編集の手順

1. `src/` 配下の該当バケットファイル (または `_special.tsv`) を編集。同じバケット内は `(よみ, 語)` の辞書順にソートされている状態を保つと review しやすいですが、厳密な順序は build 時に自動整列されるので気にしなくて OK です。
2. 変更をコミットして push。
3. CI (`validate-src`) が `src/` をパースして build が通ることを検証します。失敗していれば修正してください。

GitHub 上の Web エディタだけで `src/*.tsv` を編集・コミットしても構いません。ローカル Python 環境は必須ではありません。

### ローカルで動作確認したい場合 (任意)

```
python3 scripts/build_release.py
```

`src/` の内容から `GoogleIME/DMiME.txt` / `WindowsIME/DMiME.txt` / `Mac/…plist` を作業ツリーに書き出します。これらのファイルは `.gitignore` 対象なのでコミットされません。生成物を使って実 IME に import しての動作確認などに利用してください。

特定バージョンのリリースアセット (zip 2 つ + plist) を手元で作る場合:

```
python3 scripts/build_release.py --dist=dist/ --version=1.2
```

`dist/DMiME-1.2.zip` / `dist/DMiME-1.2-msime.zip` / `dist/DMiME-1.2 igakujisho for icloud.plist` が出力されます。

## リリース

バージョンは **Git タグ** を唯一の正として管理します。`v<X.Y>` 形式のタグを push すると `.github/workflows/build-release.yml` が自動でビルドし、GitHub Release に以下 3 アセットを添付します:

- `DMiME-<X.Y>.zip` — Google 日本語入力用 (UTF-8, LF)
- `DMiME-<X.Y>-msime.zip` — Microsoft IME 用 (UTF-16 LE BOM, CRLF)
- `DMiME-<X.Y> igakujisho for icloud.plist` — Mac ユーザ辞書 (iCloud 同期) 用

例:

```
git tag v1.2
git push origin v1.2
```

でタグを打つと Release `v1.2` が作成され上記 3 つがアセットとしてアップロードされます。インストール手順は README の「インストール法」を参照してください (Release body から自動リンクされます)。

### 品詞タグの書式について

`src/*.tsv` の品詞列は **Google 日本語入力の正式名** で書いてください:

- `名詞` / `固有名詞` / `短縮よみ` / `名詞サ変` / `抑制単語` / `サジェストのみ`

MS IME 版を生成する際、`scripts/build_release.py` が以下のマッピングを自動適用します:

| Google (src に書く) | → MS IME 出力 |
| --- | --- |
| 名詞 | 名詞 |
| 固有名詞 | 固有名詞 |
| 短縮よみ | 短縮よみ |
| 名詞サ変 | サ変名詞 (語順反転) |
| 抑制単語 | 抑制単語 |
| サジェストのみ | (MS IME に相当なしのため除外) |

## ビルドの再現性

`scripts/build_release.py` は冪等で、同じ `src/` から常に同じバイト列を生成します。

## ライセンス

追加エントリも含め、本リポジトリの内容は GPL-2.0 の下で配布されます。
