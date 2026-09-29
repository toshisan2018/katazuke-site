# robots.txt ライブ設置 手順書

対象サイト：`https://katazuke.amt-eco.com/`（Xserver 上の WordPress）
目的：現在 `https://katazuke.amt-eco.com/robots.txt` が **404** の状態を解消し、クローラーにサイトマップの場所を伝える。

---

## 0. 設置するファイルの中身

以下の内容の `robots.txt` を用意します（GitHub リポジトリ `toshisan2018/katazuke-site` の PR #1 のファイルと同一）。

```
# robots.txt for https://katazuke.amt-eco.com/
# 株式会社AMT / おうちのお片付け隊

User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php

Sitemap: https://katazuke.amt-eco.com/wp-sitemap.xml
```

- 全クローラー（Googlebot 含む）を許可し、管理画面 `/wp-admin/` だけ除外（`admin-ajax.php` は許可）。
- サイトマップ `wp-sitemap.xml`（HTTP 200 で有効確認済み）を宣言。

---

## 方法A：Xserver ファイルマネージャで設置（推奨・最も確実）

物理ファイルを置くため、WordPress の設定に関係なく確実に 200 で返せます。

1. **Xserver アカウントにログイン**
   - Xserver アカウント（[https://www.xserver.ne.jp/login_info.php](https://www.xserver.ne.jp/login_info.php)）→「サーバー管理」で **サーバーパネル** を開く。

2. **ファイルマネージャを開く**
   - サーバーパネル内の「**ファイルマネージャ**」（WebFTP）をクリック。

3. **片付けサイトのドキュメントルートを開く**
   - サブドメイン `katazuke.amt-eco.com` の公開フォルダへ移動します。
   - Xserver では通常、メインドメイン配下にサブドメイン用フォルダが作られます。目安の場所（※実際のフォルダ名は環境で異なるため要確認）：
     ```
     amt-eco.com / public_html / katazuke /
     ```
   - **見分け方**：そのフォルダの中に `wp-config.php` や `index.php`、`wp-content` フォルダがあれば、そこが片付けサイトの公開フォルダ（ドキュメントルート）です。

4. **robots.txt をアップロード**
   - 上記フォルダの直下（`wp-config.php` と同じ階層）に、用意した `robots.txt` を **アップロード**。
   - 既に `robots.txt` がある場合は、中身を上記内容で上書き。

5. **反映確認** → 「設置後の確認」へ。

---

## 方法B：FTP ソフトで設置

FileZilla などの FTP ソフトを使う場合。

1. Xserver サーバーパネル →「**FTPアカウント設定**」で FTP ホスト名・ユーザー名・パスワードを確認。
2. FTP ソフトで接続。
3. 方法A の手順3と同じ **ドキュメントルート**（`wp-config.php` がある階層）へ移動。
4. `robots.txt` をアップロード。
5. 「設置後の確認」へ。

---

## 方法C：SEOプラグインで出力（物理設置ができない場合の代替）

AIOSEO や Yoast SEO を導入している場合、管理画面から robots.txt を出力できます。

1. WordPress 管理画面にログイン。
2. プラグインの **robots.txt エディター** を開く
   - AIOSEO：`All in One SEO > ツール > robots.txt エディター`
   - Yoast：`Yoast SEO > ツール > ファイルエディター`
3. 「0. 設置するファイルの中身」の内容を貼り付けて保存。
4. 「設置後の確認」へ。

> 注意：プラグイン出力の場合、他プラグインや WordPress のデフォルト robots が競合することがあります。確認時に想定通りの内容になっているか必ずチェックしてください。

---

## 設置後の確認

1. **ブラウザで確認**
   - `https://katazuke.amt-eco.com/robots.txt` を開く。
   - 「0.」の内容がそのまま表示されれば成功（＝HTTP 200）。
   - キャッシュが残る場合は、URL 末尾に `?v=1` を付けて再読み込み、またはスーパーリロード（Ctrl/⌘+Shift+R）。

2. **Google Search Console で確認**
   - GSC →「設定」→「**robots.txt**」レポートで「取得: 成功」になるか確認（Google が取得するまで数時間〜数日かかる場合あり）。
   - 必要に応じて GSC の「URL 検査」で主要ページの再クロールを依頼。

---

## 注意点・つまずきやすい点

- **設置場所はサブドメインの公開フォルダ**（`katazuke.amt-eco.com` 用フォルダ）です。メインドメイン `amt-eco.com` 直下の `public_html` ルートに置くと `katazuke.amt-eco.com/robots.txt` には反映されません。
- **ファイル名・文字コード**：ファイル名は必ず `robots.txt`（すべて小文字）。文字コードは UTF-8、改行は問いません。
- **上書き注意**：既存の robots.txt がある場合、内容を確認してから上書きすること。
- **WordPress の仮想 robots.txt**：物理ファイルを置くと、そちらが優先されます（本手順の狙い）。
- `Sitemap:` 行の URL（`wp-sitemap.xml`）が実際に 200 で開けることを、あわせて確認しておくと安心です。

---

作成：株式会社AMT 片付けサイト運用メモ
関連：GitHub `toshisan2018/katazuke-site` PR #1（robots.txt 本体）
