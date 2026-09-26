# katazuke.amt-eco.com おうちのお片付け隊ページ 引継ぎ書

作成日: 2026-09-26
同梱ファイル:
- `index.html` … トップページ（単一HTMLファイル・CSS埋め込み・そのまま開ける）
- `assets/extra.css` … デザインシステム本体（WordPressの「追加CSS」に貼るCSS）
- `assets/pages/*.html` … 下層ページ本体（WordPress投稿へ貼る wp:html ブロック）
- `assets/pages/manifest.json` … 上記ページの一覧（base64同梱）
- `assets/build_pages.py` … 上記すべてを生成する単一スクリプト（内容の修正はここで行う）

---

## 1. 目的・概要

- 株式会社AMTの **片付け・不用品回収事業の独立サイト** をサブドメイン `https://katazuke.amt-eco.com/` で公開する。
- 目的：AMTを「片付け・不用品回収・残置物撤去もやっている会社」として打ち出す。特に **解体前の残置物撤去** など、解体事業（kaitai.amt-eco.com）と連携する案件の受け皿にする。
- 本体のコーポレートサイトは `https://amt-eco.com/`。このページは本体とは別デザイン（**黄色系統**）。
- 作り方は **解体サイト（kaitai.amt-eco.com）と同じ方式**。AMT共通デザインシステム（`.amt-katazuke` スコープのCSS変数＋共通パーツ）を黄色に置き換えて使用する。

## 2. 確定事項（変更しないこと）

| 項目 | 内容 |
|---|---|
| 会社名 | 株式会社AMT |
| 代表者 | 代表取締役　鈴木 敏也 |
| 所在地 | 〒428-0013　静岡県島田市金谷東2丁目3483-290 |
| 電話 | 0547-39-3750（**掲載する電話番号はこれのみ**。他の番号・携帯番号は載せない） |
| メール | katazuke@amt-eco.com |
| 許認可・登録 | **なし**（保有していないため、サイトに資格・許認可欄は置かない） |
| 保有資格 | **なし** |
| 言語 | 日本語のみ |
| デザイン | 黄色メイン＋濃いスレート（チャコール）を構造色（黄色を強く） |
| 対応業務 | 家の片付け／不用品回収／解体前の残置物撤去／倉庫の片付け／農機具の買取り（個人・法人どちらも対応：BtoB・BtoC） |
| 対応エリア | 静岡県内中心（解体サイトと同じ市町名） |

## 3. サーバー環境

**下表は解体サイト（kaitai.amt-eco.com）と同一サーバー構成を前提とした想定。実際のパス・SSL・サブドメイン追加の状況は要確認。**

| 項目 | 内容 |
|---|---|
| ホスティング | Xserver（サーバー: sv16843.xserver.jp）※解体サイトと同一想定 |
| IP | 85.131.213.169（amt-eco.com と同一IPへ解決される想定。要確認） |
| DNS管理 | Xserver |
| サブドメイン | `katazuke.amt-eco.com` をサーバーパネルで追加する（**未実施。実施日・実施者を記録すること**） |
| ドキュメントルート（想定） | `/home/<サーバーID>/amt-eco.com/public_html/katazuke.amt-eco.com/` ※Xserver標準構成からの想定。実際のパスは要確認 |
| WordPress | 本サイトはWordPress（解体サイトと同じ **Lightning テーマ＋VK Blocks** の想定）で運用する。ページ本文は wp:html ブロックで貼り、共通CSSは「追加CSS」に登録する |
| メール | amt-eco.com のMXは変更しないこと。`katazuke@amt-eco.com` の受信箱を作成済みか要確認 |

> ⚠️ 注意：現在このリポジトリ作業環境に接続されているWordPress（MCP）は **in-tex.jp（株式会社インテックス）** で、本件とは無関係。**katazuke/AMTの作業を in-tex.jp に対して行わないこと。** AMTのWordPressに接続してから作業する。

## 4. 現状と未解決事項（2026-09-26 時点）

- [ ] `katazuke@amt-eco.com` メールボックスの作成確認
- [ ] サブドメイン `katazuke.amt-eco.com` の追加
- [ ] 独自SSL（無料）の適用
- [ ] WordPress（Lightning）セットアップ／「追加CSS」に `assets/extra.css` を登録
- [ ] 各ページ（トップ＋下層11ページ）の作成・公開
- [ ] `robots.txt` / `sitemap.xml` の確認（sitemapのURLは `https://katazuke.amt-eco.com/`）
- [ ] ブラウザでの表示確認（PC・スマホ）
- [ ] 許認可の要否確認（下記「7. 注意事項」参照）

## 5. ページ構成

### デザインシステム（共通）
- スコープ `.amt-katazuke`。各ページ本文はこの `<div class="amt-katazuke">…</div>` で囲む（`build_pages.py` が自動で付与）。
- WordPressでは「外観 > カスタマイズ > 追加CSS」に `assets/extra.css` の内容を貼る。
- フォント: Google Fonts「Noto Sans JP」（400/500/700/900）。
- 主要CSS変数（色）:
  - `--primary:#f7b500`（ブランド黄）/ `--primary-dark:#e0a000` / `--primary-bright:#ffd23f` / `--primary-light:#fff5d6`
  - `--dark:#2f3a41`（構造色スレート。白文字を載せる）/ `--dark-2:#212a30`
  - `--ink:#2a2724`（本文）/ `--gray:#f6f5f2` / `--white:#ffffff` / `--link:#9a6a00`
- 共通パーツ: ヘッダー（ロゴマーク＋電話ピル＋上部グラデ帯）/ グローバルナビ（スマホはハンバーガー）/ パンくず / ページヒーロー / 本文（prose）/ FAQ / 関連ページ / 下部CTA帯 / リッチフッター。

### トップ（index.html）
ヒーロー → 対応業務（5枚）→ 選ばれる理由（3枚）→ ご利用の流れ（5ステップ）→ 対応エリア → 会社概要 → CTA → フッター。
meta description / OGP（title・description・type・url）設定済み。JSON-LD（LocalBusiness）埋め込み済み。OGP画像は未設定。

### 下層ページ（assets/pages/ 全11ページ）
| slug | ページ | 種別 |
|---|---|---|
| katazuke | 家のお片付け | サービス |
| fuyouhin | 不用品の回収 | サービス |
| zanchibutsu | 解体前の残置物撤去 | サービス |
| souko | 倉庫の片付け | サービス |
| nouki-kaitori | 農機具の買取り | サービス |
| ryoukin | 料金・費用について | 案内 |
| flow | ご利用の流れ | 案内 |
| company | 会社概要 | 案内 |
| area | 対応エリア | 案内 |
| faq | よくある質問 | 案内 |
| contact | お問い合わせ | 案内 |

各ページに JSON-LD（Service / BreadcrumbList / FAQPage）を埋め込み済み。

## 6. 作業指示（優先順）

1. **内容の修正は `assets/build_pages.py` で行い、`python assets/build_pages.py` を実行して再生成する**（`index.html`・`extra.css`・`pages/*` が一括で作り直される）。生成物を直接手直ししない。
2. WordPress（Lightning）を用意し、「追加CSS」に `assets/extra.css` を貼る。
3. 各ページを固定ページとして作成し、本文に `assets/pages/<slug>.html` の内容（wp:html ブロック）を貼る。パーマリンクは slug に合わせる（例: `/katazuke/`）。
4. トップは `index.html` の内容を使う（固定ページ本文へ貼るか、テーマのトップに設定）。
5. 表示確認：`https://katazuke.amt-eco.com/` がSSL付きでPC・スマホとも正常表示されるか確認する。
6. `robots.txt` と `sitemap.xml` を追加。
7. お問い合わせフォーム（Contact Form 7 等）を `/contact/` ページに差し込む（本文の該当位置に注記あり）。
8. OGP画像の追加（任意。画像は社長の確認をとってから）。
9. 本体サイト amt-eco.com、および解体サイト kaitai.amt-eco.com（残置物撤去の導線）からの相互リンクを検討（本体側を触る前に社長に確認）。

## 7. 注意事項

- 許認可番号・資格・実績・価格などは **推測で書かない**。確定事項の表にない情報を追加するときは、必ず社長に確認する。
- **許認可の要否は公開前に確認する。** 一般家庭から出る不用品を有料で収集運搬する場合は市町村の「一般廃棄物収集運搬業許可」、農機具などの中古品買取は「古物商許可」が必要とされるのが一般的。現在のサイト文言は許可を名乗らない書き方にしているが、実際の運用に許可が必要かは要確認。
- 「施工実績◯件」「業界最安」などの根拠のない表現は使わない。
- 具体的な料金表・目安額は掲載しない（現地条件で変わるため「無料でお見積り」に統一）。
- 掲載する電話番号は 0547-39-3750 のみ。メールは katazuke@amt-eco.com のみ。
- 他事業（解体・金属買取など）や他社名義の許認可番号を、このサイトに流用しない。
- ファイルの編集・作成の前には、変更内容をリストで社長に確認してから作業する。
- 呼びかけは「社長」。
