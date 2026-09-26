# 画像制作指示書｜katazuke.amt-eco.com（株式会社AMT おうちのお片付け隊）

他のAIツール（Midjourney / DALL·E / Adobe Firefly / Stable Diffusion / Canva など）やデザイナーに
画像を依頼するための指示書です。事業＝家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・
農機具の買取り（個人・法人どちらも対応）。配色は**黄色系統**。

---

## 0. まず最初に（超重要ルール）

1. **画像の中に文字を入れない**（AIに日本語を書かせると必ず崩れます）。社名やキャッチは、あとから
   合成します。英語プロンプトにも必ず `no text, no logos, no watermarks` を入れてください。
2. **「自社の実際の実績・現場」だと誤解される写り方は避ける**。あくまでイメージ画像です。特定の看板・
   会社名・ナンバープレート・個人が特定できる顔は入れないでください。
3. **人物の顔ははっきり写さない**（後ろ姿・遠景・手元・マスクやヘルメットで顔が隠れる程度ならOK）。
4. **日本の実情に合う画像**にする（海外のスケール感ではなく、日本の住宅・倉庫・軽トラ／2tトラックの
   スケール感）。片付け・不用品回収の「きれいに片付いた」清潔感を大切に。
5. 生成後のファイルは、決めた**ファイル名**で保存して渡してください（そのまま差し替えられます）。

---

## 1. ブランド・トーン

| 項目 | 内容 |
|---|---|
| 会社 | 株式会社AMT（おうちのお片付け隊）／静岡県島田市金谷東2丁目3483-290 |
| 事業 | 家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・農機具の買取り（BtoB・BtoC） |
| 印象 | 明るい・清潔・親しみやすい・頼れる・スピーディー・誠実（地域密着） |
| ブランドカラー | メイン黄 `#f7b500` / 濃い黄 `#e0a000` / 明るい黄 `#ffd23f` / 淡い黄 `#fff5d6` / 構造色スレート `#2f3a41` |
| 写真の色調 | 明るく清潔感のある自然光（順光の日中）。彩度は上げすぎず、白・木目・黄色の差し色が映えるトーン |
| イラストの作風 | フラットデザイン。太めのアウトライン。黄色＋濃いスレートの2色を主体に、親しみやすいアイコン調 |

英語プロンプトに使えるブランド指定：
`warm and clean color palette, accents in bright yellow #f7b500 and dark slate #2f3a41, bright natural daylight`

---

## 2. 画像一覧（優先順）

| # | 用途 | 形式 | 推奨サイズ(px) | ファイル名 |
|---|---|---|---|---|
| A | トップ ヒーロー背景（任意：黄色グラデ上に重ねる淡い写真） | 写真 | 1920×1080 (16:9) | `hero-main.jpg` |
| B1〜5 | ご利用の流れ（各ステップ） | イラスト | 各 800×800 (1:1) | `flow-1.png`〜`flow-5.png` |
| C1〜5 | 対応業務（サービス別イメージ） | 写真 | 各 1200×800 (3:2) | `service-katazuke.jpg` ほか |
| D1〜3 | 「選ばれる理由」アイコン | イラスト（アイコン） | 各 400×400 透過PNG | `reason-1.png`〜 |
| E | SNS共有用OGP | デザイン | 1200×630 | `ogp-katazuke.png` |

> 写真は `.jpg`（軽さ優先）、イラスト・アイコンは `.png`（透過）。1枚あたり **300〜500KB以下**を目安に書き出す。
> ※トップのヒーローは黄色グラデーション＋黒文字のデザインで既に成立しているため、Aは任意。
> 　入れる場合は「うっすら」敷く前提で、明るく余白の多い写真にする。

---

## A. ヒーロー（任意・トップ最上部の背景）

- **用途/配置**：トップ最上部。既存の黄色グラデの上に、うっすら重ねる背景。
- **サイズ**：1920×1080（16:9）。**上側と左側に広めの余白**（文字を重ねる）。
- **ファイル名**：`hero-main.jpg`
- **狙い**：片付いて明るいリビング、または軽トラ／2tトラックへ丁寧に積み込む作業の引き（顔なし）。
- **英語プロンプト例**：
  `Bright tidy Japanese living room after decluttering, sunlight through window, minimal clean space, wide empty area on upper-left for text overlay, cheerful and clean atmosphere. No people, no text, no logos, no watermarks.`
- **ネガティブ**：`text, letters, japanese characters, logo, watermark, signboard, license plate, close-up human face, messy clutter, dark, low quality`

---

## B. ご利用の流れ（各ステップ・アイコン調イラスト）

**共通指定**：5枚を**同じ作風・同じ色調でシリーズ**に。正方形1:1・800×800。**画像内に文字・数字を入れない**。

**シリーズ共通スタイル（各プロンプト末尾に付ける）**
```
flat vector illustration, bold outlines, palette of bright yellow #f7b500 and dark slate #2f3a41 on white, simple and friendly, consistent icon-style series, centered composition. No text, no numbers, no letters, no logos, no watermark.
```

| # | ステップ | 描くもの | 英語プロンプト（本体） |
|---|---|---|---|
| B1 | お問い合わせ | スマホ／電話で相談 | `a smartphone with a phone call and a friendly chat bubble` |
| B2 | 現地確認・ヒアリング | 室内で荷物の量を確認する係員（後ろ姿・顔なし）とクリップボード | `a worker with a clipboard checking boxes and furniture inside a room, back view` |
| B3 | お見積り | 見積書の書類と電卓、チェックマーク | `an estimate document with a calculator and a checkmark` |
| B4 | 日程調整・作業 | 段ボールを運ぶ手元と軽トラック | `hands carrying cardboard boxes toward a small truck` |
| B5 | 完了 | すっきり片付いた部屋とキラッと光る清潔感 | `a clean empty tidy room with a sparkle, sense of completion` |

---

## C. 対応業務（サービス別・写真）

- **用途/配置**：トップ「対応業務」や各サービスページのサムネイル。
- **サイズ**：1200×800（3:2）。**共通ネガティブ**：`text, logo, watermark, signboard, close-up human face, license plate, low quality`

| # | サービス | ファイル名 | 英語プロンプト |
|---|---|---|---|
| C1 | 家のお片付け | `service-katazuke.jpg` | `Sorting household items into keep and dispose piles in a Japanese home, hands only, boxes and furniture, bright daylight` |
| C2 | 不用品の回収 | `service-fuyouhin.jpg` | `Furniture and home appliances loaded neatly onto a small Japanese truck in a residential street, back view of worker` |
| C3 | 解体前の残置物撤去 | `service-zanchibutsu.jpg` | `Emptying furniture and belongings out of an old vacant Japanese house before demolition, hands carrying items, daylight` |
| C4 | 倉庫の片付け | `service-souko.jpg` | `Organizing pallets, shelves and materials inside a warehouse, worker back view, bright industrial interior` |
| C5 | 農機具の買取り | `service-nouki.jpg` | `A used compact tractor and farm machinery in a rural Japanese barn yard, clean daylight, no people` |

---

## D. 「選ばれる理由」アイコン（任意）

- **サイズ**：400×400・**透過PNG**。フラットアイコン。**文字なし**。黄色＋スレートの2色。

| # | テーマ | ファイル名 | 英語プロンプト |
|---|---|---|---|
| D1 | 個人も法人も対応 | `reason-1.png` | `flat icon of a house and an office building side by side` |
| D2 | 解体・買取まで一貫 | `reason-2.png` | `flat icon of a recycling arrow with a coin, representing buyback and reuse` |
| D3 | 見積り無料 | `reason-3.png` | `flat icon of a document with a checkmark and a zero-yen tag` |

共通末尾：`flat vector icon, bold outlines, bright yellow #f7b500 and dark slate #2f3a41, transparent background. No text, no letters, no logos, no watermark.`

---

## E. OGP（SNS共有画像）

- サイズ 1200×630。文字（社名・キャッチ）はデザインで入れてOK（後から合成）。
- 背景：黄色ベース＋片付いた部屋 or 軽トラのワンポイント。キャッチ例「静岡県内 片付け・不用品回収・農機具買取」。

---

## 3. 生成後の流れ

1. 決めたファイル名で書き出す（jpgは~300〜500KB以下目安）。
2. 画像を渡してもらったら：ヒーロー等に日本語文字を合成／サイトへの設置（alt属性・表示サイズ最適化込み）
   ／公開前に完成イメージを確認、という流れで対応する。
3. どのAIで作ったかを共有してもらうと、追加調整の相談がしやすい。

## 4. 困ったときのコツ

- 思った画像が出ないときは、英語プロンプトの**最初に用途**（例：`website hero banner,`）を足すと安定する。
- 作風がバラつくときは、**1枚気に入ったものを「参照画像」**にして残りを生成すると統一できる。
- 片付け系は「散らかった before」より、**片付いた after の清潔感**を主役にすると好印象。
