# amt-eco.com を AI Engine で接続する手順書（Claude から直接編集できるようにする）

目的：コーポレートサイト `amt-eco.com` の WordPress を Claude のコネクタ（MCP）として接続し、
相互リンクバナーの挿入などを **Claude が直接** 行えるようにする。

前提（実績ある方式）：`in-tex.jp` で使っている **AI Engine（Meow Apps）v3.8.0 の MCP 機能**と同じ仕組みを、
`amt-eco.com` にも用意する。※`in-tex.jp` を設定したときの記録・画面がそのまま参考になります。

---

## ① WordPress 側の設定（amt-eco.com）

1. **AI Engine プラグインを導入**
   - `amt-eco.com` の WordPress 管理画面 →「プラグイン」→「新規追加」→ **AI Engine（作者 Jordy Meow）** をインストール・有効化。
   - すでに入っている場合はバージョンを確認（v3.8.0 以降が望ましい）。

2. **MCP 機能を有効化**
   - 管理画面「**Meow Apps → AI Engine**」を開く。
   - 設定内の **MCP（Model Context Protocol）** の項目を探して **有効化（Enable）**。
     - ※メニュー名・場所は AI Engine のバージョンで異なる場合あり。`in-tex.jp` で有効化したときと同じ画面です。見当たらない場合は AI Engine の「Settings（詳細設定）」や「Dev Tools」系の項目を確認。

3. **接続情報（エンドポイントURL＋認証トークン）を控える**
   - AI Engine の MCP 設定画面に表示される **MCP エンドポイントの URL** と **認証トークン（Bearer Token / API キー）** をコピーして安全に保管。
   - これが claude.ai 側で必要になります。
   - ⚠️ トークンは秘密情報。チャットや公開場所に貼らないでください（設定時は画面上でコピーのみ）。

---

## ② claude.ai 側の設定（コネクタ追加）

1. **[claude.ai/customize/connectors](https://claude.ai/customize/connectors)** を開く。
2. **カスタムコネクタ（MCP）を新規追加**。
   - 接続先 URL＝①で控えた **MCP エンドポイントURL**
   - 認証＝①の **トークン（Bearer）**
3. **コネクタ名を区別できる名前に**する（重要）。
   - 例：`amtwordp`（`in-tex.jp` の `intexwordp` や 片付けサイト用と混同しないため）。
4. 接続が「接続済み」になり、ツール数が表示されればOK（`wp_*` などのツールが使えるようになる）。

---

## ③ 新しいセッションでの確認（必須）

> コネクタは **セッション開始時にだけ読み込まれます。** 追加後は必ず**新しい会話（新規セッション）**を始めてください。今までの会話の続きには反映されません。

1. **新規セッション**を開始。
2. 冒頭で Claude に次を依頼：
   ```
   amt-eco.com のWordPress（AI Engineコネクタ）に接続しました。
   接続先の siteurl が https://amt-eco.com であることを確認したうえで、
   トップページ下部に相互リンクバナー（コーポレート用）をカスタムHTMLとして挿入してください。
   誤って in-tex.jp・katazuke 以外は操作しないこと。
   ```
3. Claude 側で `siteurl` が `https://amt-eco.com` であることを確認 → 一致すれば作業実行。

---

## 接続後に Claude ができること / できないこと

| 作業 | 可否 | 補足 |
|---|---|---|
| 固定ページ・投稿の本文更新（バナー挿入など） | ✅ 可 | `wp_update_post` で本文にカスタムHTMLを挿入 |
| ウィジェット（`widget_block` 等）保存 | ❌ 不可 | AI Engine が保護オプションを拒否 |
| robots.txt 設置 | ❌ 不可 | サーバー上のファイル。MCPでは設置不可（ファイルマネージャ/FTPで対応） |
| サーバーWAFの制約 | 要確認 | `in-tex.jp`（ロリポップ）は一部403。`amt-eco.com` は環境が異なるため実際に試すまで不明（推測） |

---

## 注意点

- **接続先の取り違え防止**：作業前に必ず `siteurl` を確認。`amt-eco.com` 以外（`in-tex.jp` 等）は操作しない。
- **トークンの管理**：認証トークンは秘密。漏れた場合は AI Engine 側で再発行。
- **コネクタ名**：サイトごとに区別できる名前を付ける（`amtwordp` 等）。
- **反映タイミング**：フルページキャッシュ（あれば）により、更新後すぐ front に反映されないことがある。

---

参考：`in-tex.jp` 接続実績
- コネクタ名 `intexwordp` / AI Engine v3.8.0 の MCP 機能で公開
- ツール接頭辞 `mwai_*`（Meow Apps AI）・`wp_*`（WordPress操作）
- 経路：Claude → claude.ai コネクタ → サイトの AI Engine (MCP) → WordPress
