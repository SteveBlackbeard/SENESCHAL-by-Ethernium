# Seneschal

[![PyPI](https://img.shields.io/pypi/v/seneschal?label=pypi&color=blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal は、AI 作業をより安全かつ低コストにするためのローカルファーストの制御レイヤーです。

どのコンテキストを送るか、何をローカルに留めるか、何を遮断するか、そしてそのタスクがより強力なモデルに値するかを判断します。目的は実際のトークン節約です。リポジトリ全体の貼り付けを減らし、リトライを減らし、プロンプトを小さくし、ツールの権限範囲を安全にし、タスクの受け渡しを明確にします。

> セネシャル（家令）は家の資源を管理し、主君に代わって行動を承認する役職でした。このツールの役割もまさに同じです。**支出を配分し**、**能力を承認します**。

## 主な機能

- 特定のプロバイダーに縛られないトークン予算の見積もり
- 明示的な予算内でのリポジトリコンテキストの梱包
- タスクに対して十分な範囲で最も安価なモデル経路の推奨
- コンテキストのスナップショット保存により、未変更ファイルの再送信を回避
- BM25 による語彙的関連度を用いた、最も関連性の高い周辺コンテキストの選択
- 信頼できないテキストやファイルに対するプロンプトインジェクションおよび機密情報の検査
- **Ed25519 で署名された**最小権限のケイパビリティ付与の検証

## インストール

```bash
pip install seneschal
seneschal --help
```

オプションの追加機能:

```bash
pip install "seneschal[measure]"    # 実測トークナイザー (tiktoken)
pip install "seneschal[security]"   # 署名付き付与 (cryptography)
```

## 署名付きケイパビリティ付与

署名のない付与は、どのプロセスでも編集できる単なる JSON ファイルです。エージェントが自分自身の権限を偽造できてしまいます。Ed25519 署名により、ブローカーは次のいずれかに該当する付与をフェイルクローズドで拒否します。有効な署名がない、信頼されない鍵で署名されている、署名後に改変されている（権限昇格）、または有効期限が切れている。

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## これは何ではないか

サンドボックスでもエージェント実行エンジンでもありません。モデルを**呼ぶかどうか**と、**どのコンテキストを送るか**を決めるだけであり、そのモデルやエージェントが付与された権限で何を行うかまでは制御しません。

## ステータス

コアはランタイム依存関係ゼロ。MIT ライセンス。テレメトリなし。

リポジトリ: https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
