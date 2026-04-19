# DMiME
医学医療用語変換辞書「DMiME」の再配布用・保守用レポジトリ

DMiMEはオープンライセンスの医学医療用語変換辞書ファイルです。  
無料で、誰でも使える、学習効率を向上させる入力ツールを目指して作成されました。  
DMiMEは日本医師会総合政策研究機構ORCAの開発するかな漢字変換用医療辞書のVer.0.3を土台として作成されています。  
このかな漢字変換用医療辞書がGPL2ライセンスであることからGPL2を継承し、改変と再配布が可能なオープンライセンスの医療用語変換辞書となります。



## インストール法
[Releases](https://github.com/c-colloid/DMiME/releases)



## 開発者向け
辞書データは `src/` 以下の 16 ファイル (50音×清濁別 TSV) がマスタです。配布物は `python3 scripts/build_release.py` で再生成されます。編集ルールは [CONTRIBUTING.md](CONTRIBUTING.md) 参照。



## 連絡先
Twitter:DMiMEjp


## [免責]
当辞書使用において起きたすべてのことに対して責任を負いません。


## 著作権表示 
Copyright (C) 2016 Kmm, Project DMiME
## ライセンス 
GPL2(GNU General Public License ver.2)
