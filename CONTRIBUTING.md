# DMiME への貢献ガイド

DMiME の辞書データは **`src/` 以下の TSV ファイル群がマスタ** です。配布物である `GoogleIME/DMiME.txt` / `WindowsIME/DMiME.txt` / `Mac/DMiME igakujisho for icloud.plist` はビルド成果物であり、`src/` を編集した上で `python3 scripts/build_release.py` を実行して再生成してください。

## 成果物の配置

| フォルダ | 中身 | 形式 |
| --- | --- | --- |
| `GoogleIME/DMiME.txt` | Google 日本語入力用辞書 | UTF-8 / LF |
| `WindowsIME/DMiME.txt` | Microsoft IME 用辞書 | UTF-16 LE BOM / CRLF |
| `Mac/DMiME igakujisho for icloud.plist` | macOS ユーザ辞書 (iCloud 同期) | UTF-8 plist |

**歴史的経緯について**: 以前は `WindowsIME/DMiME.txt` が Google 日本語入力形式のファイルでしたが、「Windows で使うならフォーマットは Microsoft IME」という思い込みに基づく誤った命名でした。現在はフォルダ名と実ファイル形式が一致しています (`WindowsIME/` = Microsoft IME、`GoogleIME/` = Google 日本語入力)。

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

1. `src/` 配下の該当バケットファイルを編集。同じバケット内は `(よみ, 語)` の辞書順にソートされている状態を保つと review しやすいですが、厳密な順序は自動整列されるので気にしなくて OK です。
2. 変更をコミットして push。**トップレベルのビルド成果物 3 ファイルを手で編集・コミットする必要はありません**。
3. push 後、`.github/workflows/build-split.yml` が自動でトップレベル 3 ファイルを再生成してブランチに追いコミットします (数十秒〜1 分)。以降に手元を最新化するときは `git pull` を忘れずに。

GitHub 上の Web エディタだけで `src/*.tsv` を編集・コミットしても、CI が残りを面倒みます。ローカル Python 環境は必須ではありません。

### ローカルで動作確認したい場合 (任意)

```
python3 scripts/build_release.py
```

`src/` の内容から `GoogleIME/DMiME.txt` / `WindowsIME/DMiME.txt` / `Mac/…plist` を再生成します。生成物をコミットしてもしなくても構いません (CI が同じものを再生成するため冪等)。

特定バージョンのリリースアセット (zip 2 つ + plist) を手元で試しに作りたい場合:

```
python3 scripts/build_release.py --dist=dist/ --version=1.2
```

`dist/DMiME-1.2.zip` / `dist/DMiME-1.2-msime.zip` / `dist/DMiME-1.2 igakujisho for icloud.plist` が出力されます。

### Fork からの PR

GitHub の制約で、upstream の CI は Fork ブランチにコミットできません。Fork 経由で PR を出す場合は以下のいずれかの方法で top-level ファイルが同期されます (やらなくてもマージ後に upstream 側が自動修正します)。

**推奨: Fork 側で GitHub Actions を有効化する**

1. 自分の Fork リポジトリ (例: `あなた/DMiME`) の **Actions** タブを開く
2. `I understand my workflows, go ahead and enable them` ボタンを押す
3. これ以降、Fork のブランチに push すると Fork 側で再生成が自動的に走り、top-level ファイルも一緒に追いコミットされます
4. その状態で upstream へ PR を送れば、PR diff に src/ と top-level が揃った綺麗な状態で並びます

**代替: ローカルで再ビルドしてコミット**

ローカルに Python が入っていれば `python3 scripts/build_release.py` を実行して 3 つの top-level ファイルをコミットに含めてください。

**何もしない場合**

PR 時点では top-level が古いままですが、upstream の CI に黄色い ⚠ 警告が出るだけで CI は緑のまま通ります。マージ後に upstream の main で自動再生成が走り同期されます。レビュワーは src/ の diff で実質的な変更内容を確認できます。

## ビルド成果物のバイトハッシュ

`scripts/build_release.py` は冪等で、同じ `src/` から常に同じバイト列を生成します。

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

## ライセンス

追加エントリも含め、本リポジトリの内容は GPL-2.0 の下で配布されます。
