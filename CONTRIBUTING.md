# DMiME への貢献ガイド

DMiME の辞書データは **`src/` 以下の 16 個の TSV ファイルがマスタ** です。配布物である `WindowsIME/DMiME-1.1.txt` と `Mac/DMiME1.1 igakujisho for icloud.plist` はビルド成果物であり、`src/` を編集した上で `python3 scripts/build_release.py` を実行して再生成してください。

## ファイル構成

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

追加したいよみの **先頭 1 文字** を基準にバケットを選んでください。拗音 (例「きゅう」) は先頭が「き」なので `ka.tsv` に入ります。

## TSV フォーマット (4 列)

```
よみ<TAB>語<TAB>platform<TAB>品詞
```

| 列 | 内容 |
| --- | --- |
| `よみ` | ひらがな or 英数字。入力するひらがな表記 |
| `語` | 変換結果の文字列 |
| `platform` | `win` / `mac` / `both` のいずれか |
| `品詞` | 基本は `名詞`。原典に由来する例外として `サジェストのみ`, `短縮よみ`, `名詞サ変`, `抑制単語`, `固有名詞` あり |

### `platform` タグの選び方

- **`both`** (推奨): Windows でも macOS でも使いたいエントリ。新規追加はまず `both` を選ぶ。
- **`win`**: macOS 標準 IME でそのまま変換できるので DMiME 側には不要、または Mac 版への還流待ち。
- **`mac`**: Microsoft IME での変換は別手段でカバーされているか、Windows 版への還流待ち。

迷ったら `both` にしてください。将来 Mac/Win の中身を収束させる方向です。

## 追加・編集の手順

1. `src/` 配下の該当バケットファイルを編集。同じバケット内は `(よみ, 語)` の辞書順にソートされている状態を保つと review しやすいですが、CI 上は順序を気にしません (build 時に自動整列)。
2. 再ビルド:
   ```
   python3 scripts/build_release.py
   ```
3. トップレベルの 2 ファイル (`WindowsIME/DMiME-1.1.txt`, `Mac/…plist`) も含めてコミット。`.github/workflows/verify-split.yml` が PR でこれを再確認します。

## ビルド成果物のバイトハッシュ

`python3 scripts/build_release.py` は冪等で、同じ `src/` から常に同じバイト列を生成します。CI の verify-split ジョブは「再ビルド後に `WindowsIME/DMiME-1.1.txt` と `Mac/…plist` が変化しない」ことを検査します。

## リリース

タグ (`v*`) を push すると `.github/workflows/build-release.yml` が自動でビルドし、GitHub Release に以下を添付します:

- `DMiME-1.1.txt` (Windows IME 用)
- `DMiME1.1 igakujisho for icloud.plist` (Mac / iCloud ユーザ辞書用)

インストール手順は README の Releases セクションを参照してください (利用者向け導線は分割前後で不変です)。

## ライセンス

追加エントリも含め、本リポジトリの内容は GPL-2.0 の下で配布されます。
