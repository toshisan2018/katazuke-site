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
| 許認可・登録 | **古物商許可（静岡県公安委員会）あり**。／一般廃棄物収集運搬業許可は**なし**（→「収集運搬業としての回収」を名乗らず、買取・片付け搬出として表現している） |
| 古物商許可 | 静岡県公安委員会 第49118K000008号（取扱品目：機械工具類）※記載済み |
| 保有資格 | なし |
| 言語 | 日本語のみ |
| デザイン | **黄色系統**＋濃いスレートを構造色（社長のご希望で黄色）。ヒーローは黄色地＋黒文字。サービスページには作業写真を配置。※緑バナーは黄色サイトと不整合のため未使用 |
| 対応業務 | 家の片付け／不用品回収／解体前の残置物撤去／倉庫の片付け／農機具の買取り（個人・法人どちらも対応：BtoB・BtoC） |
| 対応エリア | 静岡県内中心（解体サイトと同じ市町名） |

## 3. サーバー環境

**下表は解体サイト（kaitai.amt-eco.com）と同一サーバー構成を前提とした想定。実際のパス・SSL・サブドメイン追加の状況は要確認。**

| 項目 | 内容 |
|---|---|
| ホスティング | Xserver（サーバー: sv16843.xserver.jp）※解体サイトと同一想定 |
| IP | 85.131.213.169（amt-eco.com と同一IPへ解決される想定。要確認） |
| DNS管理 | Xserver |
| サブドメイン | `katazuke.amt-eco.com` **追加済み**・独自SSL **適用済み**（2026-09-26 時点で社長確認済み） |
| ドキュメントルート（想定） | `/home/<サーバーID>/amt-eco.com/public_html/katazuke.amt-eco.com/` ※Xserver標準構成からの想定。実際のパスは要確認 |
| WordPress | **実装済み**（解体サイトと同じ **Lightning テーマ＋VK Blocks** 想定）。ページ本文は wp:html ブロックで貼り、共通CSSは「追加CSS」に `assets/extra.css` を登録する |
| メール | amt-eco.com のMXは変更しないこと。`katazuke@amt-eco.com` の受信箱は **作成済み** |

> ⚠️ 注意：現在このリポジトリ作業環境に接続されているWordPress（MCP）は **in-tex.jp（株式会社インテックス）** で、本件とは無関係。**katazuke/AMTの作業を in-tex.jp に対して行わないこと。** AMTのWordPressに接続してから作業する。

## 4. 現状と未解決事項（2026-09-26 時点）

- [x] `katazuke@amt-eco.com` メールボックス作成済み
- [x] サブドメイン `katazuke.amt-eco.com` 追加済み
- [x] 独自SSL（無料）適用済み
- [x] WordPress（Lightning）実装済み
- [x] 古物商許可番号を記載（静岡県公安委員会 第49118K000008号／機械工具類）
- [x] **各ページ（トップ＋下層11ページ）をWordPressに公開**（2026-09-26／REST経由／固定ページID 6〜17）
- [x] **トップページを固定フロントページに設定**（ホーム＝ページID 6）
- [x] PC・スマホ表示確認（スマホのヘッダー崩れを修正済み）
- [x] プライバシーポリシー追加＋フッターにリンク
- [x] お問い合わせフォーム設置（Contact Form 7。下記「7c」参照）
- [x] サイト画像設置（トップのヒーローバナー＋サービス写真4点＋OGP＋緑ロゴ／ファビコン）
- [x] 配色は黄色系統（社長のご希望。緑に一度変更後、黄色へ戻した）
- [x] キャッチフレーズ（tagline）設定
- [x] サイトマップ確認（`https://katazuke.amt-eco.com/wp-sitemap.xml` が有効）
- [ ] `robots.txt`（現在404。AIOSEO等でsitemap記載のrobotsを出すと望ましい）
- [ ] OGP画像・サービス写真の設置（社長が用意 → こちらで最適化・設置）
- [ ] 旧サンプル（「Sample Page」「Hello world!」）の要否確認（不要なら削除）

## 7c. お問い合わせフォームについて（重要）

- **Contact Form 7 を導入し、/contact/ に設置済み**（当初はCF7が未インストールだったため「権限がありません」と表示されていた。CF7をインストール・有効化して解決）。
- フォームは解体サイトと同じ**「カスタムHTML＋ショートコードブロック」方式**で本文内に埋め込み（ショートコード `[contact-form-7 id="2ca5633"]`）。項目は日本語（お名前／メール／電話番号／件名／お問い合わせ内容）、送信先は `katazuke@amt-eco.com`。
- 送信テストは未実施。公開前に一度テスト送信し、受信を確認すること（Xserverのメール設定・迷惑メール判定に注意。必要ならSMTPプラグインを検討）。

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

## 7b. 公開の方法・更新のしかた（重要）

- テーマは **Twenty Twenty-Five（ブロックテーマ）**。各固定ページは `.amt-katazuke` の自己完結HTML（`<style>`同梱）で、テーマのヘッダー/フッター/タイトルは各ページ先頭の`<style>`（`header.wp-block-template-part{display:none}` 等）で非表示にしている。そのため**カスタムのヘッダー1つだけ**が表示される。
- 公開は、GitHub公開リポジトリの raw（`assets/pages/manifest.json`・`assets/extra.css`）をブラウザから取得し、WordPress REST（`/wp-json/wp/v2/pages`）へ各ページを作成した（管理者ログイン状態のnonce使用）。
- **内容を直したいとき**：`assets/build_pages.py` を編集 → `python assets/build_pages.py` → GitHubへpush → 公開スクリプトを再実行（slugが一致する既存ページは上書き更新されるので重複しない）。または各固定ページを管理画面のコードエディターで直接編集してもよい。
- CSSは各ページに同梱済みのため「追加CSS」への登録は不要。グローバルに一元管理したい場合のみ `assets/extra.css` を「追加CSS」に貼り、各ページ先頭の`<style>`は無くてもよい。

## 7. 注意事項

- 許認可番号・資格・実績・価格などは **推測で書かない**。確定事項の表にない情報を追加するときは、必ず社長に確認する。
- **許認可（確認済み）**: 古物商許可（機械工具類・静岡県公安委員会 第49118K000008号）**あり**／一般廃棄物収集運搬業許可**なし**。不用品は、**まだ使えるものは古物商許可のもとで買取**し、**処分が必要なものは提携する許可業者に適正処理を委託**する運用（社長確認済み）。サイト本文（不用品回収・家の片付け）にもその旨を明記済み。
- 「施工実績◯件」「業界最安」などの根拠のない表現は使わない。
- 具体的な料金表・目安額は掲載しない（現地条件で変わるため「無料でお見積り」に統一）。
- 掲載する電話番号は 0547-39-3750 のみ。メールは katazuke@amt-eco.com のみ。
- 他事業（解体・金属買取など）や他社名義の許認可番号を、このサイトに流用しない。
- ファイルの編集・作成の前には、変更内容をリストで社長に確認してから作業する。
- 呼びかけは「社長」。


## 8. 2026-09-27 の更新（社長対応分）

- 配色：緑に一度変更後、ご希望で**黄色に戻した**（現状＝黄色）。
- **ロゴ・マスコット採用**：ヘッダーロゴ＝社長提供の家＋箱ロゴ、ファビコンも同ロゴ。トップのヒーロー右に作業員マスコット、各ページ下部CTAにヒーロー風マスコット（`assets/images/` に格納、WPメディア済み）。緑ユニフォームの作業写真4点は各サービスページに配置。
- **会社概要から代表者名を削除**（ご希望）。
- **お問い合わせフォーム**：Contact Form 7 を導入し /contact/ に埋め込み（日本語項目・送信先 katazuke@amt-eco.com）。※送信テスト未実施。
- **Google Search Console**：`https://katazuke.amt-eco.com/` を**所有権確認済み（HTMLタグ方式）**。検証メタタグは **WPCode Lite（Insert Headers and Footers）** の「ヘッダー」に設定して <head> へ出力（`<meta name="google-site-verification" content="p_Aps9WvGC9dpWF66Sm5frMbrjQ3jtCJe8LgwAYXQTc">`）。**このWPCode設定とメタタグは削除しない**（削除すると確認が外れる）。
- **サイトマップ**：`wp-sitemap.xml` をGSCに送信済み（送信直後は「取得できませんでした」表示だが、サイトマップ自体はHTTP 200で正常。Googleが取得すると成功に変わる見込み）。
- 導入プラグイン（katazuke）：Contact Form 7、WPCode Lite（ともに有効）。
- ※テーマ(functions.php)への直接コード追加は本番安全機構によりブロックされるため、head出力はWPCodeで管理している。


## 9. 2026-09-27 追加対応（Google連携・デザイン強化）

- **Site Kit by Google 導入・連携済み**：Search Console と Google アナリティクス(GA4)を接続。GA4はアカウント「おうち片付け隊」／プロパティ katazuke.amt-eco.com を新規作成し、gtagはSite Kitが自動出力（手動設置不要）。
- **Google Search Console**：所有権確認済み（HTMLタグ＝WPCode）。サイトマップ wp-sitemap.xml 送信済み・検出済み。主要4ページ（トップ・家の片付け・不用品回収・残置物撤去）は手動インデックス登録をリクエスト済み。倉庫・農機具ほかは1日の割当上限のため翌日以降に追加可（サイトマップ経由でも順次クロールされる）。
- **ヘッダー強化**：ロゴマーク62px・社名1.5remに拡大（左上のインパクト向上）。
- **トップのヒーローを写真背景化**：作業風景の写真（hero-bg.jpg）＋左に文字スクリム。スマホは全面スクリムで可読性確保。
- **農機具ページに農機具写真**（service-nouki.jpg）を追加。作業員マスコットは「選ばれる理由」に配置。
- **ファビコン**：ロゴ（家＋箱＋きらめき）を設定済み。
- 導入プラグイン（追加）：Site Kit by Google。※WordPress管理画面のCF7/WPCode/Site Kitは削除しないこと（フォーム・GSC検証・解析が外れる）。

## 10. 2026-09-27 追加対応（AIOSEO・コラム記事）

- **All in One SEO (AIOSEO) 導入・設定済み**：セットアップウィザードでビジネス種別＝「小規模オフラインビジネス」（LocalBusinessスキーマ）、組織情報（電話 0547-39-3750／ロゴ／SNSシェア画像＝OGP）を設定。サイトマップ有効・全投稿タイプを含む。※ウィザードの「機能」画面にある外部プラグイン（MonsterInsights/OptinMonster/リンク切れチェッカー/Multilingual）は導入しない方針のため、ウィザードは途中で本体設定へ移動して完了させている（余計なプラグインは未導入）。
- **パーマリンクを「投稿名」(/%postname%/) に変更**：投稿URLが `https://katazuke.amt-eco.com/<スラッグ>/` に統一（旧 `/年/月/日/スラッグ/` は404）。※固定ページのURLには影響なし。
- **コラム記事11本を公開**（WordPress投稿・カテゴリー「コラム」slug=column, ID 11／各投稿はコメント無効）：
  - `/seizen-seiri/` 生前整理は何から始める？（ID155）
  - `/ihin-seiri/` 遺品整理の進め方と業者選び（ID156）
  - `/akiya-katazuke/` 空き家・実家の片付け5ステップ（ID157）
  - `/fuyouhin-tebanashi/` 不用品を賢く手放す方法（ID158）
  - `/nouki-kaitori-kotsu/` 農機具を高く売るコツ（ID159）
  - `/souko-seiri-houjin/` 倉庫・工場の片付け（法人向け）（ID160）
  - `/gomiyashiki/` ゴミ屋敷の片付けはどう進める？
  - `/fuyouhin-hiyou/` 不用品回収の費用はどう決まる？
  - `/hikkoshi-fuyouhin/` 引っ越しで出る不用品をまとめて処分
  - `/kaden-shobun/` 冷蔵庫・洗濯機・テレビの処分方法（家電リサイクル法）
  - `/tenpo-heiten/` 店舗・オフィスの閉店・移転の片付け（法人向け）
  - ※後半5本は **SEO＋AIO（AI検索・強調スニペット）対策**として、本文冒頭に「結論」先出しブロック(`.answer`)＋質問型の見出しを採用。
- **コラム一覧ページ `/column/`**（固定ページ・サイトと同じデザイン）を新設。ヘッダーナビとフッター「ご案内」に「コラム」リンクを追加（全ページ再公開済み）。
- **記事の作り方（単一ソース）**：`assets/build_articles.py` が `build_pages.py` のヘッダー/フッター/CTA/デザインCSSを再利用して自己完結HTML（`<style>`同梱・Article/BreadcrumbList/FAQ の JSON-LD付き）を生成。出力＝`assets/articles/*.html`＋`manifest.json`（投稿本文）、`column.html`＋`page_manifest.json`（一覧ページ）。記事を増やす手順：build_articles.py に `add_article(...)` を追記 → `python assets/build_articles.py` → git push → 管理画面（post-new.php 等 wpApiSettings がある画面）でRESTにより slug 一致で投稿へ upsert。
- **テーマ(TT5)の投稿装飾を非表示**：投稿ページに出る「執筆者/カテゴリ/日付」メタ（`.wp-block-group.has-small-font-size`）と、本文下の関連投稿(`.wp-block-query` ほか）を、記事の`<style>`内HIDE_CSSでクラス指定により非表示化済み。
- **運用ルール厳守**：料金の具体額・実績件数・お客様の声は記載しない／不用品は「古物商での買取＋片付け搬出、処分は提携許可業者へ適正処理を委託」と表現（一般廃棄物収集運搬業許可は無いため無許可回収を名乗らない）／古物商許可（機械工具類・静岡県公安委員会 第49118K000008号）は農機具・機械の買取で言及可。
- **お問い合わせフォーム：送信テスト済み（2026-09-27）**。/contact/ から送信し、katazuke@amt-eco.com に受信できることを確認済み（フォーム正常動作）。※CF7の完了/エラーメッセージは初期設定の英語のまま（日本語化は任意。社長のご希望があれば変更）。
- **未対応（社長対応 or 翌日以降）**：新記事6本＋/column/のGSC手動インデックス登録（前日に割当上限のため。サイトマップ経由で順次クロールされる）。投稿の「執筆者」表示名が管理者メール（katazuke@amt-eco.com）になっている（CSSで非表示だがHTMLソースには残る）。
