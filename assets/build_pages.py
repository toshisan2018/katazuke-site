# -*- coding: utf-8 -*-
"""katazuke.amt-eco.com（おうちのお片付け隊）サイト生成スクリプト。

株式会社AMTのサブドメイン事業サイト用。解体サイト（kaitai.amt-eco.com）で確立した
AMT共通デザインシステムを黄色系統に置き換えて使用する。

このスクリプト1本が「単一ソース」になっており、実行すると次を生成する:
  - ../index.html          … トップページ（単一HTMLファイル・CSS埋め込み・そのまま開ける）
  - assets/extra.css       … デザインシステム本体（WordPressの「追加CSS」に貼るためのCSS）
  - assets/pages/*.html    … 下層ページ本体（WordPress投稿へ貼る wp:html ブロック）
  - assets/pages/manifest.json … 上記ページの一覧（base64同梱）

デザインシステムのCSSは DESIGN_CSS（.amt-katazuke スコープ）に集約。トップも下層も
同じ .amt-katazuke を使うので、見た目が完全に統一される。

【運用ルール】
  - 料金の具体額・実績件数・お客様の声など、根拠が必要な内容は入れない（推測で書かない）。
  - 掲載する電話番号は CONFIG の TEL 1件のみ。
  - 許認可・資格は保有していないため記載しない（会社概要にも資格欄を置かない）。
"""
import json, os, base64, io, re

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "pages")
ROOT = os.path.abspath(os.path.join(HERE, ".."))
os.makedirs(OUT, exist_ok=True)

# ============================================================
# ▼▼▼ CONFIG：事業ごとの設定 ▼▼▼
# ============================================================
SITE_NAME = "おうちのお片付け隊"
COMPANY_NAME = "株式会社AMT"
DOMAIN = "https://katazuke.amt-eco.com"      # 末尾スラッシュなし
TEL = "0547-39-3750"                          # 掲載する電話番号はこれのみ
TEL_INTL = "+81-547-39-3750"                  # JSON-LD用
MAIL = "katazuke@amt-eco.com"
AREA_NAME = "静岡県"
PROVIDER_TYPE = "LocalBusiness"
CATCH = "静岡県島田市｜片付け・不用品回収・残置物撤去・農機具買取"

# 許認可（この事業で実際に保有しているもののみ）
#   一般廃棄物収集運搬業許可：なし（→ 収集運搬業としての「回収」を名乗らない書き方にする）
#   古物商許可：あり
KOBUTSU_AUTH = "静岡県公安委員会"     # 古物商許可の公安委員会
KOBUTSU_NO = "49118K000008"          # 古物商許可番号
KOBUTSU_CATEGORY = "機械工具類"       # 取扱品目
_kb_no = (" 第" + KOBUTSU_NO + "号") if KOBUTSU_NO else ""
# 会社概要テーブル用（例: 古物商許可（機械工具類）　静岡県公安委員会 第49118K000008号）
KOBUTSU_TD = "古物商許可（" + KOBUTSU_CATEGORY + "）　" + KOBUTSU_AUTH + _kb_no
KOBUTSU_LABEL = "古物商許可（" + KOBUTSU_AUTH + "）" + _kb_no  # 本文用

# ------------------------------------------------------------
# 料金（2026-10-10 社長指示：1㎥あたり20,000円から を公開する）
#   ※税込/税別の表記は未確定のため本文では断定しない。確定後 PRICE_TAX を "（税込）" 等にする。
# ------------------------------------------------------------
PRICE_PER_M3 = 20000
PRICE_TAX = ""                                  # 例: "（税込）" / "（税別）"
PRICE_LABEL = "1㎥あたり{:,}円".format(PRICE_PER_M3) + PRICE_TAX + "から"
PRICE_CURRENCY = "JPY"

# 対応エリア（JSON-LD areaServed・llms.txt で使う市町。確定情報）
AREA_CITIES = ["島田市", "藤枝市", "焼津市", "掛川市", "菊川市", "牧之原市",
               "静岡市", "吉田町", "川根本町", "磐田市", "袋井市", "御前崎市"]

# 本社の緯度経度（静岡県島田市金谷東2丁目3483-290）
GEO_LAT = 34.8213
GEO_LNG = 138.1312

# 関連サイト（JSON-LD sameAs）
SAME_AS = ["https://amt-eco.com/", "https://kaitai.amt-eco.com/"]

# サイト画像（WordPressメディアにアップ済みのURL）
UPLOADS = "https://katazuke.amt-eco.com/wp-content/uploads/2026/09/"
UPLOADS_OCT = "https://katazuke.amt-eco.com/wp-content/uploads/2026/10/"   # 2026-10 以降にアップした画像
IMG = {
    "hero": UPLOADS + "hero-main.jpg",
    "katazuke": UPLOADS + "service-katazuke.jpg",
    "fuyouhin": UPLOADS + "service-fuyouhin.jpg",
    "zanchibutsu": UPLOADS + "service-zanchibutsu.jpg",
    "souko": UPLOADS + "service-souko.jpg",
    "nouki": UPLOADS + "service-nouki.jpg",
    "hero_bg": UPLOADS + "hero-bg.jpg",
    "ogp": UPLOADS + "ogp-katazuke.jpg",
    "logo": UPLOADS + "logo.png",
    "logoicon": UPLOADS + "logo-icon.png",
    "mascot_worker": UPLOADS + "mascot-worker.png",
    "mascot_hero": UPLOADS + "mascot-hero.png",
    # 対応業務セクション用イラスト（透過PNG）
    "illust_katazuke": UPLOADS + "illust-katazuke.png",
    "illust_fuyouhin": UPLOADS + "illust-fuyouhin.png",
    "illust_zanchibutsu": UPLOADS + "illust-zanchibutsu.png",
    "illust_souko": UPLOADS + "illust-souko.png",
    "illust_nouki": UPLOADS + "illust-nouki.png",
    # 対応エリアの地図イラスト
    "area_map": UPLOADS + "area-map.jpg",
    # お困りごと6テーマのイラスト（透過PNG）
    "illust_seiri": UPLOADS_OCT + "illust-seiri-v2.png",
    "illust_akiya": UPLOADS_OCT + "illust-akiya-v2.png",
    "illust_gomiyashiki": UPLOADS_OCT + "illust-gomiyashiki-v2.png",
    "illust_hikkoshi": UPLOADS_OCT + "illust-hikkoshi-v2.png",
    "illust_tenpo": UPLOADS_OCT + "illust-tenpo-v2.png",
    "illust_hinmoku": UPLOADS_OCT + "illust-hinmoku-v2.png",
    # 2026-10-05 リニューアル（新ロゴ・軽量WebP）
    "logo_v2": UPLOADS_OCT + "logo-v2-mark.webp",
    "hero_v2": UPLOADS_OCT + "hero-bg-1600.webp",
    "hero_v2_sp": UPLOADS_OCT + "hero-bg-900.webp",
    "svc_katazuke": UPLOADS_OCT + "service-katazuke-720.webp",
    "svc_fuyouhin": UPLOADS_OCT + "service-fuyouhin-720.webp",
    "svc_zanchibutsu": UPLOADS_OCT + "service-zanchibutsu-720.webp",
    "svc_souko": UPLOADS_OCT + "service-souko-720.webp",
    "svc_nouki": UPLOADS_OCT + "service-nouki-720.webp",
    "mascot_hero_v2": UPLOADS_OCT + "mascot-hero-420.webp",
    "mascot_worker_v2": UPLOADS_OCT + "mascot-worker-420.webp",
    "ogp_v2": UPLOADS_OCT + "ogp-katazuke-v2.jpg",
    "logo_v2_png": UPLOADS_OCT + "favicon-v2-512.png",
}

NAV_ITEMS = [
    ("/", "ホーム"),
    ("/katazuke/", "家の片付け"),
    ("/fuyouhin/", "不用品回収"),
    ("/zanchibutsu/", "残置物撤去"),
    ("/souko/", "倉庫の片付け"),
    ("/seiri/", "生前整理・遺品整理"),
    ("/nouki-kaitori/", "農機具買取"),
    ("/ryoukin/", "料金・費用"),
    ("/faq/", "よくある質問"),
    ("/column/", "コラム"),
    ("/contact/", "お問い合わせ"),
]

# フッターの2カラム分（サービス／ご案内）のリンク
FOOT_SERVICE = [
    ("/katazuke/", "家の片付け"),
    ("/fuyouhin/", "不用品の回収"),
    ("/zanchibutsu/", "解体前の残置物撤去"),
    ("/souko/", "倉庫の片付け"),
    ("/seiri/", "生前整理・遺品整理"),
    ("/akiya/", "空き家・実家の片付け"),
    ("/gomiyashiki-katazuke/", "ゴミ屋敷の片付け"),
    ("/hikkoshi/", "引っ越しの片付け"),
    ("/tenpo/", "店舗・オフィスの片付け"),
    ("/hinmoku/", "対応品目一覧"),
]
# フッターの農機具買取カラム（2026-10-10 新設：機種別ページへの導線）
FOOT_NOUKI = [
    ("/nouki-kaitori/", "農機具の買取り"),
    ("/nouki-tractor/", "トラクター"),
    ("/nouki-combine/", "コンバイン"),
    ("/nouki-taue/", "田植機"),
    ("/nouki-kouunki/", "耕運機・管理機"),
    ("/nouki-kusakari/", "草刈機・運搬車"),
    ("/nouki-kaitori-shizuoka/", "静岡県の農機具買取"),
]
FOOT_GUIDE = [
    ("/ryoukin/", "料金・費用について"),
    ("/flow/", "ご利用の流れ"),
    ("/area/", "対応エリア"),
    ("/katazuke-shimada/", "島田市の片付け・不用品回収"),
    ("/company/", "会社概要"),
    ("/faq/", "よくある質問"),
    ("/column/", "コラム"),
    ("/contact/", "お問い合わせ"),
]
# ============================================================
# ▲▲▲ CONFIG ここまで ▲▲▲
# ============================================================


# ============================================================
# デザインシステム本体（.amt-katazuke スコープ・黄色系統）
# WordPressでは「外観 > カスタマイズ > 追加CSS」にこの内容を貼る（= assets/extra.css）。
# 黄色=ブランド主役 / スレート濃色=構造色（白文字を載せる）。
# ============================================================
DESIGN_CSS = """/* ===== 株式会社AMT おうちのお片付け隊 デザインシステム =====
   スコープ: .amt-katazuke（解体サイトの .amt-kaitai を黄色系統に置換）
   使い方: この内容を WordPress「追加CSS」に貼る。各ページ本文は .amt-katazuke で囲む。 */

.amt-katazuke{
  --primary:#f7b500;        /* ブランド黄（アクセント・ボタン・見出し飾り・現在地ナビ） */
  --primary-dark:#e0a000;   /* 濃い黄（グラデ・ホバー） */
  --primary-bright:#ffd23f; /* 明るい黄 */
  --primary-light:#fff5d6;  /* 淡い黄（背景面） */
  --ink:#2a2724;            /* 本文の黒 */
  --dark:#2f3a41;           /* 構造色スレート（白文字を載せる：ナビ・CTA・見出しマーク等） */
  --dark-2:#212a30;         /* さらに濃い */
  --gray:#f6f5f2;
  --white:#ffffff;
  --link:#9a6a00;           /* 白背景で読めるリンク色（黄系） */
  font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium",YuGothic,"Yu Gothic",Meiryo,sans-serif;  /* 端末標準フォント（速度対策 2026-10-05） */
  color:var(--ink);
  background:var(--white);
  line-height:1.8;
}
.amt-katazuke *{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow-x:hidden;}
.amt-katazuke{width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);overflow-x:clip;}
.amt-katazuke img{max-width:100%;}
.amt-katazuke a{color:var(--link);}

/* ===== ヘッダー ===== */
.amt-katazuke .k-header{background:var(--white);border-bottom:none;box-shadow:0 2px 12px rgba(0,0,0,.09);}
.amt-katazuke .hdr-topbar{height:5px;background:linear-gradient(90deg,var(--dark),var(--primary-dark) 40%,var(--primary) 70%,var(--primary-bright));}
.amt-katazuke .header-inner{max-width:1080px;margin:0 auto;padding:13px 16px;display:flex;align-items:center;justify-content:space-between;gap:14px;}
.amt-katazuke .k-header .logo{display:flex;align-items:center;gap:12px;text-decoration:none;}
.amt-katazuke .logo-mark{width:62px;height:62px;flex-shrink:0;line-height:0;}
.amt-katazuke .logo-mark img{width:100%;height:100%;object-fit:contain;display:block;}
.amt-katazuke .logo-tx{display:flex;flex-direction:column;line-height:1.22;}
.amt-katazuke .logo-name{font-weight:900;font-size:1.5rem;color:var(--ink);letter-spacing:.5px;}
.amt-katazuke .logo-name b{color:var(--dark);}
.amt-katazuke .logo-tx small{font-size:.82rem;color:#555;font-weight:700;margin-top:4px;}
@media(max-width:640px){.amt-katazuke .logo-mark{width:52px;height:52px;}.amt-katazuke .logo-name{font-size:1.2rem;}.amt-katazuke .logo-tx small{font-size:.72rem;}}
.amt-katazuke .k-header .header-tel{text-align:center;flex-shrink:0;}
.amt-katazuke .tel-btn{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,var(--primary-dark),var(--primary));color:var(--ink) !important;font-weight:900;font-size:1.28rem;padding:10px 24px;border-radius:30px;text-decoration:none;box-shadow:0 4px 12px rgba(224,160,0,.4);white-space:nowrap;}
.amt-katazuke .tel-btn:hover{filter:brightness(1.05);}
.amt-katazuke .k-header .header-tel small{display:block;font-size:.72rem;color:var(--ink);font-weight:700;margin-top:6px;}
@media(max-width:640px){
  .amt-katazuke .header-inner{flex-wrap:wrap;justify-content:center;text-align:center;gap:10px;padding:12px 14px;}
  .amt-katazuke .k-header .logo{justify-content:center;flex-wrap:wrap;}
  .amt-katazuke .logo-name{font-size:1.02rem;}
  .amt-katazuke .logo-tx{align-items:center;}
  .amt-katazuke .logo-tx small{font-size:.68rem;line-height:1.5;}
  .amt-katazuke .k-header .header-tel{width:100%;}
  .amt-katazuke .tel-btn{font-size:1.15rem;padding:10px 20px;}
}

/* ===== グローバルナビ ===== */
.amt-katazuke .k-nav{background:var(--dark);position:relative;}
.amt-katazuke .k-nav ul{max-width:1080px;margin:0 auto;padding:0 16px;list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:2px 0;}
.amt-katazuke .k-nav a{display:block;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;padding:12px 14px;white-space:nowrap;position:relative;}
.amt-katazuke .k-nav a::after{content:"";position:absolute;left:14px;right:14px;bottom:5px;height:2px;background:var(--primary);transform:scaleX(0);transform-origin:center;transition:transform .2s;}
.amt-katazuke .k-nav a:hover::after{transform:scaleX(1);}
.amt-katazuke .k-nav a:hover{background:rgba(255,255,255,.10);}
.amt-katazuke .k-nav a[aria-current="page"]{background:var(--primary);color:var(--ink);}
.amt-katazuke .k-nav a[aria-current="page"]::after{display:none;}

/* ハンバーガー（スマホ） */
.amt-katazuke .amt-navtoggle{display:none;}
.amt-katazuke .amt-navbtn{display:none;}
@media(max-width:860px){
  .amt-katazuke .amt-navbtn{display:flex;align-items:center;gap:10px;color:#fff;font-weight:700;padding:14px 16px;cursor:pointer;font-size:.98rem;user-select:none;}
  .amt-katazuke .amt-navbtn .bars{position:relative;display:inline-block;width:22px;height:16px;}
  .amt-katazuke .amt-navbtn .bars::before,.amt-katazuke .amt-navbtn .bars::after,.amt-katazuke .amt-navbtn .bars i{content:"";position:absolute;left:0;width:100%;height:2px;background:#fff;transition:.3s;}
  .amt-katazuke .amt-navbtn .bars::before{top:0;}
  .amt-katazuke .amt-navbtn .bars i{top:7px;}
  .amt-katazuke .amt-navbtn .bars::after{top:14px;}
  .amt-katazuke .k-nav ul{display:none;flex-direction:column;flex-wrap:nowrap;padding:0;}
  .amt-katazuke .amt-navtoggle:checked ~ ul{display:flex;}
  .amt-katazuke .k-nav li{width:100%;border-top:1px solid rgba(255,255,255,.15);}
  .amt-katazuke .k-nav a{padding:14px 16px;}
  .amt-katazuke .k-nav a::after{display:none;}
  .amt-katazuke .amt-navtoggle:checked ~ .amt-navbtn .bars::before{top:7px;transform:rotate(45deg);}
  .amt-katazuke .amt-navtoggle:checked ~ .amt-navbtn .bars i{opacity:0;}
  .amt-katazuke .amt-navtoggle:checked ~ .amt-navbtn .bars::after{top:7px;transform:rotate(-45deg);}
}

/* ===== パンくず ===== */
.amt-katazuke .breadcrumb{max-width:1080px;margin:0 auto;padding:14px 16px;font-size:.82rem;color:#666;}
.amt-katazuke .breadcrumb a{color:var(--link);text-decoration:none;}
.amt-katazuke .breadcrumb span{color:#999;margin:0 6px;}

/* ===== トップの大ヒーロー（黄色地・黒文字） ===== */
.amt-katazuke .hero{background:linear-gradient(135deg,var(--primary-dark) 0%,var(--primary) 55%,var(--primary-bright) 100%);color:var(--ink);padding:72px 16px 88px;position:relative;overflow:hidden;}
.amt-katazuke .hero::after{content:"";position:absolute;left:0;right:0;bottom:0;height:14px;background:repeating-linear-gradient(45deg,var(--dark) 0 24px,var(--primary-dark) 24px 48px);}
.amt-katazuke .hero-inner{max-width:1080px;margin:0 auto;position:relative;z-index:1;}
.amt-katazuke .hero .badge{display:inline-block;background:var(--dark);color:#fff;font-weight:700;font-size:.85rem;padding:5px 16px;border-radius:999px;margin-bottom:20px;}
.amt-katazuke .hero h1{font-size:clamp(1.7rem,4.5vw,3rem);font-weight:900;line-height:1.4;margin-bottom:18px;color:var(--ink);}
.amt-katazuke .hero h1 em{font-style:normal;color:var(--dark);background:rgba(255,255,255,.55);padding:0 .2em;border-radius:4px;}
.amt-katazuke .hero p{font-size:clamp(.95rem,2vw,1.15rem);max-width:660px;margin-bottom:32px;color:#3a352d;}
/* トップの写真ヒーロー（左に文字スクリム） */
.amt-katazuke .hero--home{background:linear-gradient(100deg, rgba(255,251,240,.96) 0%, rgba(255,251,240,.84) 30%, rgba(255,251,240,.38) 58%, rgba(255,251,240,0) 82%), url("__HERO_BG__"); background-size:cover; background-position:center right; padding:66px 16px 80px;}
.amt-katazuke .hero--home .hero-text{max-width:620px;}
@media(max-width:760px){.amt-katazuke .hero--home{background:linear-gradient(180deg,rgba(255,251,240,.95) 0%,rgba(255,251,240,.9) 40%,rgba(255,251,240,.5) 72%,rgba(255,251,240,.15) 100%), url("__HERO_BG__"); background-size:cover; background-position:center;}}
.amt-katazuke .hero-inner--mascot{display:flex;align-items:center;gap:28px;}
.amt-katazuke .hero-text{flex:1 1 auto;min-width:0;}
.amt-katazuke .hero-mascot{flex:0 0 auto;}
.amt-katazuke .hero-mascot img{width:clamp(190px,26vw,330px);height:auto;display:block;filter:drop-shadow(0 10px 18px rgba(0,0,0,.22));}
@media(max-width:760px){.amt-katazuke .hero-inner--mascot{flex-direction:column;gap:8px;}.amt-katazuke .hero-mascot img{width:200px;margin:6px auto 0;}}
.amt-katazuke .hero-cta{display:flex;gap:16px;flex-wrap:wrap;align-items:center;}
.amt-katazuke .btn-tel{display:inline-block;background:var(--dark);color:#fff;font-weight:900;font-size:clamp(1.2rem,3vw,1.6rem);padding:14px 32px;border-radius:8px;text-decoration:none;box-shadow:0 4px 0 rgba(0,0,0,.28);}
.amt-katazuke .btn-tel small{display:block;font-size:.75rem;font-weight:700;}
.amt-katazuke .btn-mail{display:inline-block;background:transparent;color:var(--ink);border:2px solid var(--dark);font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;}
.amt-katazuke .btn-mail:hover{background:var(--dark);color:#fff;}
.amt-katazuke .btn-tel:hover{filter:brightness(1.1);}

/* トップのヒーローバナー画像＋CTA帯 */
.amt-katazuke .hero-banner{line-height:0;}
.amt-katazuke .hero-banner img{width:100%;height:auto;display:block;}
.amt-katazuke .hero-cta-strip{background:linear-gradient(135deg,var(--dark-2),var(--dark));color:#fff;text-align:center;padding:28px 16px;}
.amt-katazuke .hero-cta-strip .hcs-lead{font-weight:700;margin-bottom:16px;font-size:clamp(.95rem,2.2vw,1.1rem);}
.amt-katazuke .hero-cta-strip .hero-cta{justify-content:center;}

/* サービスページ上部の写真 */
.amt-katazuke .svc-hero{max-width:1080px;margin:0 auto;padding:0 16px;}
.amt-katazuke .svc-hero img{width:100%;height:auto;display:block;border-radius:10px;margin:22px auto 0;box-shadow:0 2px 14px rgba(0,0,0,.12);}
/* 透過イラストの見出し画像：伸ばさず中央に、影・角丸なし */
.amt-katazuke .svc-hero--illust{text-align:center;}
.amt-katazuke .svc-hero--illust img{width:auto;max-width:100%;height:auto;max-height:300px;display:inline-block;border-radius:0;box-shadow:none;margin:18px auto 0;}

/* 下層ページ用のコンパクトなヒーロー */
.amt-katazuke .page-hero{padding:46px 16px 54px;}
.amt-katazuke .page-hero h1{font-size:clamp(1.5rem,3.6vw,2.3rem);margin-bottom:0;}
.amt-katazuke .page-hero p{margin-top:12px;margin-bottom:0;font-size:clamp(.95rem,2vw,1.1rem);max-width:760px;}

/* ===== 共通セクション ===== */
.amt-katazuke .k-section{padding:64px 16px;}
.amt-katazuke .inner{max-width:1080px;margin:0 auto;}
.amt-katazuke .sec-title{font-size:clamp(1.4rem,3vw,2rem);font-weight:900;text-align:center;margin-bottom:8px;}
.amt-katazuke .sec-title::after{content:"";display:block;width:64px;height:5px;margin:14px auto 0;background:linear-gradient(90deg,var(--primary) 50%,var(--dark) 50%);}
.amt-katazuke .sec-lead{text-align:center;color:#555;margin-bottom:40px;}

/* サービスカード */
.amt-katazuke .works{background:var(--gray);}
.amt-katazuke .card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;}
.amt-katazuke .card{background:var(--white);border-radius:10px;padding:26px 22px;border-top:6px solid var(--primary);box-shadow:0 2px 10px rgba(0,0,0,.06);}
.amt-katazuke .card h3{font-size:1.1rem;font-weight:700;margin-bottom:10px;}
.amt-katazuke .card h3 .mk{color:var(--primary-dark);margin-right:6px;}
.amt-katazuke .card p{font-size:.92rem;color:#444;}
/* カード中央寄せグリッド（3列・端数の行も中央に） */
.amt-katazuke .card-grid--c{display:flex;flex-wrap:wrap;justify-content:center;gap:20px;}
.amt-katazuke .card-grid--c>.card{flex:0 1 calc((100% - 40px)/3);box-sizing:border-box;}
@media(max-width:900px){.amt-katazuke .card-grid--c>.card{flex-basis:calc((100% - 20px)/2);}}
@media(max-width:560px){.amt-katazuke .card-grid--c>.card{flex-basis:100%;}}
/* サービスカードのイラスト */
.amt-katazuke .card--svc{padding-top:16px;transition:box-shadow .2s,transform .2s;}
.amt-katazuke .card--svc:hover{box-shadow:0 8px 22px rgba(0,0,0,.12);transform:translateY(-3px);}
.amt-katazuke .card-illust{text-align:center;margin:0 0 10px;}
.amt-katazuke .card-illust img{height:132px;width:auto;display:inline-block;}

/* 対応エリアの地図 */
.amt-katazuke .area-map{margin:0 0 26px;}
.amt-katazuke .area-map img{width:100%;max-width:860px;height:auto;display:block;margin:0 auto;border-radius:12px;box-shadow:0 3px 16px rgba(0,0,0,.10);}

/* 選ばれる理由 */
.amt-katazuke .reasons .card{border-top-color:var(--dark);}
.amt-katazuke .reasons .card h3 .mk{color:var(--dark);}

/* 流れ */
.amt-katazuke .flow{background:var(--gray);}
.amt-katazuke .flow-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;counter-reset:step;}
.amt-katazuke .flow-step{background:var(--white);border-radius:10px;padding:22px 16px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.06);position:relative;}
.amt-katazuke .flow-step::before{counter-increment:step;content:"0" counter(step);display:block;font-weight:900;font-size:1.6rem;color:var(--dark);border-bottom:3px solid var(--primary);width:56px;margin:0 auto 12px;padding-bottom:4px;}
.amt-katazuke .flow-step h3{font-size:1rem;font-weight:700;margin-bottom:8px;}
.amt-katazuke .flow-step p{font-size:.85rem;color:#555;}

/* エリア */
.amt-katazuke .area p{max-width:760px;margin:0 auto;text-align:center;}
.amt-katazuke .area strong{color:var(--primary-dark);}

/* 会社概要 */
.amt-katazuke .company{background:var(--gray);}
.amt-katazuke .company table{width:100%;max-width:760px;margin:0 auto;border-collapse:collapse;background:var(--white);box-shadow:0 2px 10px rgba(0,0,0,.06);border-radius:10px;overflow:hidden;}
.amt-katazuke .company th,.amt-katazuke .company td{padding:16px 20px;text-align:left;border-bottom:1px solid #eee;font-size:.95rem;vertical-align:top;}
.amt-katazuke .company th{width:32%;background:var(--dark);color:var(--white);font-weight:700;white-space:nowrap;}
@media(max-width:560px){.amt-katazuke .company th{width:38%;}}

/* 本文（prose） */
.amt-katazuke .prose{max-width:820px;margin:0 auto;}
.amt-katazuke .prose h2{font-size:clamp(1.3rem,2.6vw,1.7rem);font-weight:900;margin:40px 0 14px;padding-left:14px;border-left:6px solid var(--primary);line-height:1.5;}
.amt-katazuke .prose h3{font-size:1.15rem;font-weight:700;margin:28px 0 10px;color:var(--dark);}
.amt-katazuke .prose p{margin:0 0 16px;font-size:1rem;color:#333;}
.amt-katazuke .prose ul,.amt-katazuke .prose ol{margin:0 0 18px 1.4em;}
.amt-katazuke .prose li{margin-bottom:8px;}
.amt-katazuke .prose strong{color:var(--dark);}
.amt-katazuke .prose .lead{font-size:1.08rem;color:#444;background:var(--primary-light);border-left:6px solid var(--primary);padding:18px 20px;border-radius:6px;margin-bottom:28px;}
.amt-katazuke .prose table{width:100%;border-collapse:collapse;margin:0 0 24px;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.06);border-radius:8px;overflow:hidden;font-size:.95rem;}
.amt-katazuke .prose th,.amt-katazuke .prose td{padding:12px 14px;border-bottom:1px solid #eee;text-align:left;vertical-align:top;}
.amt-katazuke .prose thead th{background:var(--dark);color:#fff;}
.amt-katazuke .prose tbody th{background:var(--primary-light);white-space:nowrap;width:34%;}
.amt-katazuke .note{font-size:.88rem;color:#666;background:#f7f7f5;border-radius:6px;padding:14px 16px;margin:0 0 24px;}
/* 要点（結論先出し）ブロック：SEO/AIO対策 */
.amt-katazuke .answer{background:var(--dark);color:#fff;border-radius:10px;padding:18px 22px;margin:0 0 8px;box-shadow:0 4px 14px rgba(0,0,0,.12);}
.amt-katazuke .answer .answer-h{display:inline-block;background:var(--primary);color:var(--ink);font-weight:900;font-size:.78rem;padding:3px 14px;border-radius:999px;margin-bottom:10px;}
.amt-katazuke .answer p{color:#fff;margin:0;font-size:1.02rem;line-height:1.85;}
.amt-katazuke .answer strong{color:var(--primary-bright);}

/* FAQ */
.amt-katazuke .faq{max-width:820px;margin:0 auto;}
.amt-katazuke .faq-item{background:#fff;border:1px solid #eee;border-radius:8px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.04);overflow:hidden;}
.amt-katazuke .faq-q{display:flex;gap:12px;align-items:flex-start;padding:18px 20px;font-weight:700;font-size:1.02rem;background:var(--primary-light);}
.amt-katazuke .faq-q::before{content:"Q";flex-shrink:0;width:26px;height:26px;border-radius:50%;background:var(--dark);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.9rem;}
.amt-katazuke .faq-a{display:flex;gap:12px;align-items:flex-start;padding:18px 20px;color:#444;font-size:.95rem;}
.amt-katazuke .faq-a::before{content:"A";flex-shrink:0;width:26px;height:26px;border-radius:50%;background:var(--primary);color:var(--ink);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.9rem;}

/* お問い合わせフォーム（自作フォーム＋Contact Form 7 共通） */
.amt-katazuke .amt-form{max-width:640px;margin:8px auto 0;}
.amt-katazuke .amt-form label{display:block;font-weight:700;margin:16px 0 6px;color:var(--dark);font-size:.95rem;}
.amt-katazuke .amt-form label .req{color:#c0392b;font-size:.8rem;margin-left:6px;}
.amt-katazuke .amt-form input,.amt-katazuke .amt-form textarea,.amt-katazuke .amt-form select{width:100%;padding:12px 14px;border:1px solid #ccc;border-radius:8px;font-size:1rem;font-family:inherit;background:#fff;color:var(--ink);}
.amt-katazuke .amt-form input:focus,.amt-katazuke .amt-form textarea:focus,.amt-katazuke .amt-form select:focus{outline:2px solid var(--primary);border-color:var(--primary);}
.amt-katazuke .amt-form .form-submit{margin-top:22px;text-align:center;}
.amt-katazuke .amt-form button,.amt-katazuke .amt-form input[type="submit"],.amt-katazuke .amt-form .wpcf7-submit{width:auto;background:var(--dark);color:#fff;font-weight:900;font-size:1.1rem;padding:14px 44px;border:none;border-radius:8px;cursor:pointer;box-shadow:0 4px 0 rgba(0,0,0,.25);}
.amt-katazuke .amt-form button:hover,.amt-katazuke .amt-form input[type="submit"]:hover,.amt-katazuke .amt-form .wpcf7-submit:hover{filter:brightness(1.15);}
.amt-katazuke .amt-form .form-note{font-size:.82rem;color:#666;margin-top:12px;text-align:center;}
/* Contact Form 7 個別調整 */
.amt-katazuke .amt-cf7 p{margin:0 0 4px;}
.amt-katazuke .amt-cf7 .wpcf7-form-control-wrap{display:block;margin-bottom:6px;}
.amt-katazuke .amt-cf7 br{display:none;}
.amt-katazuke .amt-cf7 .wpcf7-list-item{display:inline-block;margin:0 1em 0 0;}
.amt-katazuke .amt-cf7 .wpcf7-submit{display:block;margin:22px auto 0;}
.amt-katazuke .amt-cf7 .wpcf7-not-valid-tip{color:#c0392b;font-size:.85rem;}
.amt-katazuke .amt-cf7 .wpcf7-response-output{margin:16px 0 0!important;border-radius:8px;font-size:.9rem;}

/* 下部CTA帯（濃色地・白文字＋黄ボタン） */
.amt-katazuke .cta-band{background:linear-gradient(135deg,var(--dark-2),var(--dark));color:#fff;text-align:center;padding:48px 16px;}
.amt-katazuke .cta-band h2{font-size:clamp(1.3rem,3vw,1.9rem);font-weight:900;margin-bottom:10px;color:#fff;}
.amt-katazuke .cta-band p{margin-bottom:24px;color:#e7e7e7;}
.amt-katazuke .cta-band .btn-tel{display:inline-block;background:var(--primary);color:var(--ink);font-weight:900;font-size:clamp(1.3rem,3.5vw,1.8rem);padding:16px 40px;border-radius:8px;text-decoration:none;box-shadow:0 4px 0 rgba(0,0,0,.3);}
.amt-katazuke .cta-band .btn-line{display:block;margin-top:16px;}
.amt-katazuke .cta-band .btn-mail{display:inline-block;background:transparent;color:#fff;border:2px solid #fff;font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;margin-top:8px;}
.amt-katazuke .cta-band .btn-mail:hover{background:#fff;color:var(--dark);}
.amt-katazuke .cta-band .cta-inner{max-width:1000px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:32px;}
.amt-katazuke .cta-band .cta-mascot{flex:0 0 auto;}
.amt-katazuke .cta-band .cta-mascot img{width:clamp(140px,17vw,210px);height:auto;display:block;filter:drop-shadow(0 8px 16px rgba(0,0,0,.3));}
.amt-katazuke .cta-band .cta-content{flex:0 1 auto;}
@media(max-width:700px){.amt-katazuke .cta-band .cta-mascot{display:none;}}

/* 関連ページ */
.amt-katazuke .rel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;max-width:1080px;margin:0 auto;}
.amt-katazuke .rel-card{display:block;background:#fff;border-top:5px solid var(--primary);border-radius:10px;padding:20px;text-decoration:none;color:var(--ink);box-shadow:0 2px 10px rgba(0,0,0,.06);}
.amt-katazuke .rel-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.12);}
.amt-katazuke .rel-card b{display:block;font-size:1.05rem;margin-bottom:6px;color:var(--dark);}
.amt-katazuke .rel-card span{font-size:.88rem;color:#555;}

/* ===== フッター ===== */
.amt-katazuke .k-footer{background:#1f2529;color:#ddd;border-top:6px solid var(--primary);}
.amt-katazuke .foot-inner{max-width:1080px;margin:0 auto;padding:44px 20px 26px;display:grid;grid-template-columns:1.6fr 1fr 1fr 1.2fr;gap:30px;}
.amt-katazuke .foot-logo{font-weight:900;font-size:1.15rem;color:#fff;margin-bottom:12px;}
.amt-katazuke .foot-logo span{color:var(--primary);}
.amt-katazuke .foot-about p{font-size:.85rem;line-height:1.75;color:#b8b8b8;margin:0 0 10px;}
.amt-katazuke .foot-col h4{color:#fff;font-size:.95rem;font-weight:700;margin:0 0 14px;padding-bottom:8px;border-bottom:2px solid var(--primary);}
.amt-katazuke .foot-col ul{list-style:none;margin:0;padding:0;}
.amt-katazuke .foot-col li{margin-bottom:9px;}
.amt-katazuke .foot-col a{color:#cfcfcf;text-decoration:none;font-size:.88rem;}
.amt-katazuke .foot-col a:hover{color:var(--primary-bright);}
.amt-katazuke .foot-tel{display:block;color:#fff;font-weight:900;font-size:1.55rem;text-decoration:none;letter-spacing:.5px;}
.amt-katazuke .foot-note{font-size:.8rem;color:var(--primary);margin:4px 0 12px;}
.amt-katazuke .foot-mail{display:inline-block;background:var(--primary);color:var(--ink);font-weight:700;padding:10px 22px;border-radius:6px;text-decoration:none;font-size:.85rem;}
.amt-katazuke .foot-mail:hover{background:var(--primary-bright);}
.amt-katazuke .foot-addr{font-size:.82rem;color:#b8b8b8;line-height:1.65;margin:16px 0 6px;}
.amt-katazuke .foot-corp{font-size:.85rem;}
.amt-katazuke .foot-corp a{color:#cfcfcf;text-decoration:none;}
.amt-katazuke .foot-corp a:hover{color:var(--primary-bright);}
.amt-katazuke .foot-bottom{border-top:1px solid #333;text-align:center;padding:16px;font-size:.8rem;color:#888;}
.amt-katazuke .foot-bottom a{color:#bbb;text-decoration:none;}
.amt-katazuke .foot-bottom a:hover{color:var(--primary-bright);}
@media(max-width:760px){.amt-katazuke .foot-inner{grid-template-columns:1fr 1fr;gap:24px;}}
@media(max-width:480px){.amt-katazuke .foot-inner{grid-template-columns:1fr;}}
"""

# ヒーロー背景画像のURLを差し込む
DESIGN_CSS = DESIGN_CSS.replace('__HERO_BG__', IMG['hero_bg'])

# ============================================================
# リニューアル v2（2026-10-05）：解体サイトと同じ作り込み。黄色×スレートのまま、
# 下層ページの見出し帯・本文・FAQ・カード・CTA を共通で格上げし、トップの新セクション(.kz-*)を定義。
# ============================================================
V2_CSS = """
/* ===== v2 共通 ===== */
body,.wp-site-blocks{font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium",YuGothic,"Yu Gothic",Meiryo,sans-serif;}
.amt-katazuke{--deep:#1c2328;}
.amt-katazuke .logo-mark{width:64px;height:64px;}
@media(max-width:640px){.amt-katazuke .logo-mark{width:52px;height:52px;}}

/* 下層ページの見出し帯（濃いスレート＋黄の光＋ロゴの透かし） */
.amt-katazuke .page-hero{background:radial-gradient(ellipse 60% 75% at 100% 100%,rgba(247,181,0,.30),transparent 70%),radial-gradient(ellipse 45% 55% at 0% 0%,rgba(255,210,63,.10),transparent 70%),var(--deep);color:#fff;padding:60px 16px 70px;isolation:isolate;}
.amt-katazuke .page-hero::before{content:"";position:absolute;right:-50px;top:50%;width:min(44vw,400px);aspect-ratio:1/1;transform:translateY(-50%);background:url("__LOGO_V2__") no-repeat center/contain;opacity:.12;z-index:-1;pointer-events:none;}
.amt-katazuke .page-hero::after{height:8px;background:repeating-linear-gradient(45deg,var(--primary) 0 18px,var(--deep) 18px 36px);}
.amt-katazuke .page-hero .hero-inner::before{content:"OUCHI NO OKATAZUKE-TAI";display:block;margin:0 0 12px;font-size:.72rem;font-weight:700;letter-spacing:.3em;color:var(--primary);}
.amt-katazuke .page-hero h1{color:#fff;text-shadow:0 2px 18px rgba(0,0,0,.3);}
.amt-katazuke .page-hero h1 em{background:none;color:var(--primary-bright);padding:0;}
.amt-katazuke .page-hero p{color:#d6dbde;line-height:1.9;}
@media(max-width:700px){.amt-katazuke .page-hero{padding:46px 16px 56px;}.amt-katazuke .page-hero::before{width:62vw;right:-18vw;opacity:.09;}}

/* 本文 */
.amt-katazuke .prose h2{border-left:none;padding:0 0 12px 18px;position:relative;border-bottom:1px solid #ece7da;}
.amt-katazuke .prose h2::before{content:"";position:absolute;left:0;top:.2em;bottom:14px;width:6px;border-radius:3px;background:linear-gradient(180deg,var(--primary-bright),var(--primary-dark));}
.amt-katazuke .prose h3{padding-left:1.1em;position:relative;}
.amt-katazuke .prose h3::before{content:"";position:absolute;left:0;top:.5em;width:.55em;height:.55em;border-radius:2px;background:var(--primary);}
.amt-katazuke .prose strong{background:linear-gradient(transparent 62%,rgba(247,181,0,.32) 62%);}
.amt-katazuke .prose a{color:var(--link);text-underline-offset:3px;}
.amt-katazuke .prose .lead{border-left:none;border-radius:14px;padding:20px 22px 20px 28px;position:relative;}
.amt-katazuke .prose .lead::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:6px;border-radius:3px;background:var(--primary);}
.amt-katazuke .prose table{border-radius:14px;box-shadow:0 8px 24px rgba(30,36,40,.08);}
.amt-katazuke .note{border-left:4px solid var(--primary);border-radius:10px;}
.amt-katazuke .answer{border-radius:16px;position:relative;overflow:hidden;}
.amt-katazuke .answer::before{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,var(--primary-dark),var(--primary-bright));}
.amt-katazuke .svc-hero img{border-radius:16px;box-shadow:0 14px 34px rgba(30,36,40,.16);}

/* 章タイトル */
.amt-katazuke .sec-eye{display:block;text-align:center;font-size:.74rem;font-weight:700;letter-spacing:.32em;color:#8a6200;margin:0 0 8px;}
.amt-katazuke .sec-title::after{width:72px;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--primary) 0 60%,var(--dark) 60%);}

/* FAQ */
.amt-katazuke .faq-item{border:1px solid #ece7da;border-radius:14px;box-shadow:0 6px 18px rgba(30,36,40,.06);transition:box-shadow .25s,transform .25s;}
.amt-katazuke .faq-item:hover{box-shadow:0 14px 30px rgba(30,36,40,.12);transform:translateY(-2px);}
.amt-katazuke .faq-q::before{box-shadow:0 0 0 4px rgba(247,181,0,.28);}

/* 関連ページ・カード */
.amt-katazuke .rel-grid{gap:14px;}
.amt-katazuke .rel-card{position:relative;border-top:none;border:1px solid #ece7da;border-left:5px solid var(--primary);border-radius:12px;padding:18px 44px 18px 20px;transition:transform .25s,box-shadow .25s;}
.amt-katazuke .rel-card::after{content:"→";position:absolute;right:18px;top:50%;transform:translateY(-50%);color:var(--dark);font-weight:900;transition:right .25s;}
.amt-katazuke .rel-card:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(30,36,40,.12);}
.amt-katazuke .rel-card:hover::after{right:12px;}

/* 下部CTA帯 */
.amt-katazuke .cta-band{position:relative;overflow:hidden;isolation:isolate;background:radial-gradient(ellipse 55% 70% at 100% 100%,rgba(247,181,0,.25),transparent 70%),linear-gradient(135deg,#161c20,var(--dark));padding:70px 16px 64px;}
.amt-katazuke .cta-band::before{content:"";position:absolute;left:0;right:0;top:0;height:6px;background:repeating-linear-gradient(45deg,var(--primary) 0 18px,var(--deep) 18px 36px);}
.amt-katazuke .cta-band .btn-tel{border-radius:18px;padding:16px 44px;box-shadow:0 12px 30px rgba(0,0,0,.3);transition:transform .2s;}
.amt-katazuke .cta-band .btn-tel:hover{transform:translateY(-3px);}
.amt-katazuke .cta-band .btn-mail{border-radius:999px;padding:12px 30px;}

/* フッター（見出しは p.foot-h：見出し順序の是正） */
.amt-katazuke .foot-h{color:#fff;font-size:.95rem;font-weight:700;margin:0 0 14px;padding-bottom:8px;border-bottom:2px solid var(--primary);}
.amt-katazuke .foot-logo{display:flex;align-items:center;gap:10px;}
.amt-katazuke .foot-logo .fl-tx span{color:var(--primary);}
.amt-katazuke .foot-logo img{width:44px;height:44px;background:#fff;border-radius:10px;padding:4px;}

/* ===== トップ v2 ===== */
/* ヒーロー（写真は<img>でLCPを早く） */
.amt-katazuke .kz-hero{position:relative;overflow:hidden;isolation:isolate;background:#fffbf0;padding:70px 16px 84px;}
.amt-katazuke .kz-hero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center right;z-index:-2;}
.amt-katazuke .kz-hero::before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(100deg,rgba(255,251,240,.97) 0%,rgba(255,251,240,.88) 32%,rgba(255,251,240,.35) 60%,rgba(255,251,240,0) 82%);}
.amt-katazuke .kz-hero::after{content:"";position:absolute;left:0;right:0;bottom:0;height:12px;background:repeating-linear-gradient(45deg,var(--dark) 0 22px,var(--primary) 22px 44px);}
.amt-katazuke .kz-hero-in{max-width:1080px;margin:0 auto;}
.amt-katazuke .kz-hero-tx{max-width:640px;}
.amt-katazuke .kz-badge{display:inline-flex;align-items:center;gap:8px;background:var(--dark);color:#fff;font-weight:700;font-size:.85rem;padding:6px 16px;border-radius:999px;margin:0 0 20px;}
.amt-katazuke .kz-badge::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--primary);box-shadow:0 0 0 3px rgba(247,181,0,.35);}
.amt-katazuke .kz-hero h1{font-size:clamp(1.75rem,4.6vw,3.1rem);font-weight:900;line-height:1.38;margin:0 0 18px;color:var(--ink);letter-spacing:.01em;}
.amt-katazuke .kz-hero h1 em{font-style:normal;background:linear-gradient(transparent 58%,rgba(247,181,0,.75) 58%);padding:0 .1em;}
.amt-katazuke .kz-hero-copy{font-size:clamp(.95rem,2vw,1.1rem);margin:0 0 28px;color:#3a352d;line-height:1.95;}
.amt-katazuke .kz-hero .hero-cta{margin:0 0 26px;}
.amt-katazuke .kz-hero .btn-tel{border-radius:14px;box-shadow:0 10px 24px rgba(30,36,40,.28);}
.amt-katazuke .kz-hero .btn-mail{border-radius:999px;background:rgba(255,255,255,.85);}
.amt-katazuke .kz-points{list-style:none;display:flex;flex-wrap:wrap;gap:10px;margin:0;padding:0;}
.amt-katazuke .kz-points li{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid #efe3bf;border-radius:999px;padding:7px 16px 7px 10px;font-weight:700;font-size:.88rem;box-shadow:0 4px 12px rgba(30,36,40,.08);}
.amt-katazuke .kz-points li::before{content:"✓";display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--primary);color:var(--ink);font-size:.8rem;font-weight:900;}
@media(max-width:760px){.amt-katazuke .kz-hero{padding:44px 16px 230px;}.amt-katazuke .kz-hero-bg{object-position:70% 100%;}.amt-katazuke .kz-hero::before{background:linear-gradient(180deg,rgba(255,251,240,.97) 0%,rgba(255,251,240,.93) 55%,rgba(255,251,240,.35) 78%,rgba(255,251,240,0) 100%);}}

/* 想い（濃色） */
.amt-katazuke .kz-pas{position:relative;overflow:hidden;isolation:isolate;background:radial-gradient(ellipse 70% 60% at 100% 100%,rgba(247,181,0,.22),transparent 70%),radial-gradient(ellipse 50% 45% at 0% 0%,rgba(255,210,63,.08),transparent 70%),var(--deep);color:#fff;padding:88px 16px 80px;}
.amt-katazuke .kz-pas::after{content:"";position:absolute;left:0;right:0;top:0;height:6px;background:repeating-linear-gradient(45deg,var(--primary) 0 18px,var(--deep) 18px 36px);}
.amt-katazuke .kz-pas-mark{position:absolute;right:-4%;bottom:-10%;width:min(56vw,620px);opacity:.10;z-index:-1;pointer-events:none;}
.amt-katazuke .kz-pas-in{max-width:1080px;margin:0 auto;}
.amt-katazuke .kz-eye{display:flex;align-items:center;gap:12px;margin:0 0 16px;font-size:.76rem;font-weight:700;letter-spacing:.32em;color:var(--primary);}
.amt-katazuke .kz-eye::before{content:"";width:40px;height:2px;background:var(--primary);}
.amt-katazuke .kz-pas h2{margin:0 0 34px;font-size:clamp(1rem,1.6vw,1.15rem);font-weight:700;letter-spacing:.12em;color:#cfd5d8;}
.amt-katazuke .kz-pas-grid{display:grid;grid-template-columns:1.25fr 1fr;gap:48px;align-items:end;margin:0 0 54px;}
.amt-katazuke .kz-state{margin:0;font-size:clamp(1.9rem,4.2vw,3.25rem);font-weight:900;line-height:1.3;color:#fff;}
.amt-katazuke .kz-state em{font-style:normal;color:var(--primary-bright);text-shadow:0 0 28px rgba(247,181,0,.35);}
.amt-katazuke .kz-pas-body p{margin:0 0 16px;font-size:clamp(.98rem,1.6vw,1.05rem);line-height:2.05;color:#d9dee1;}
.amt-katazuke .kz-pas-body strong{color:#fff;}
.amt-katazuke .kz-pcards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
.amt-katazuke .kz-pcard{position:relative;padding:30px 24px 26px;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.025));border:1px solid rgba(255,255,255,.10);transition:transform .25s,border-color .25s,box-shadow .25s;}
.amt-katazuke .kz-pcard::before{content:"";position:absolute;left:24px;right:24px;top:-1px;height:3px;border-radius:3px;background:linear-gradient(90deg,var(--primary-bright),var(--primary-dark));box-shadow:0 0 18px rgba(247,181,0,.5);}
.amt-katazuke .kz-pcard:hover{transform:translateY(-6px);border-color:rgba(247,181,0,.45);box-shadow:0 18px 40px rgba(0,0,0,.45);}
.amt-katazuke .kz-num{display:block;margin:0 0 10px;font-size:3.3rem;font-weight:900;line-height:1;color:transparent;-webkit-text-stroke:1.5px var(--primary);}
.amt-katazuke .kz-pcard h3{margin:0 0 12px;font-size:1.22rem;font-weight:900;color:#fff;}
.amt-katazuke .kz-pcard p{margin:0;font-size:.95rem;line-height:1.9;color:#cdd3d6;}
.amt-katazuke .kz-pcard a{color:var(--primary-bright);}
.amt-katazuke .kz-sign{display:flex;align-items:center;justify-content:flex-end;gap:14px;margin:42px 0 0;font-size:.95rem;font-weight:700;letter-spacing:.14em;color:#b9c1c5;}
.amt-katazuke .kz-sign::before{content:"";width:64px;height:1px;background:var(--primary);}
@media(max-width:860px){.amt-katazuke .kz-pas-grid{grid-template-columns:1fr;gap:24px;}.amt-katazuke .kz-pcards{grid-template-columns:1fr;}.amt-katazuke .kz-pas-mark{width:110vw;right:-30%;bottom:auto;top:6%;}}
@media(max-width:600px){.amt-katazuke .kz-pas{padding:64px 16px 56px;}.amt-katazuke .kz-pas-body p br{display:none;}.amt-katazuke .kz-sign{font-size:.8rem;letter-spacing:.06em;}.amt-katazuke .kz-sign::before{width:32px;}}

/* 対応業務（写真カード） */
.amt-katazuke .kz-svc{background:var(--gray);}
.amt-katazuke .kz-sgrid{display:flex;flex-wrap:wrap;justify-content:center;gap:22px;}
.amt-katazuke .kz-scard{flex:0 1 calc((100% - 44px)/3);display:flex;flex-direction:column;background:#fff;border-radius:18px;overflow:hidden;text-decoration:none;color:var(--ink);box-shadow:0 10px 28px rgba(30,36,40,.09);transition:transform .25s,box-shadow .25s;}
.amt-katazuke .kz-scard:hover{transform:translateY(-6px);box-shadow:0 20px 40px rgba(30,36,40,.16);}
.amt-katazuke .kz-sph{position:relative;aspect-ratio:3/2;overflow:hidden;background:#ddd;}
.amt-katazuke .kz-sph img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s;}
.amt-katazuke .kz-scard:hover .kz-sph img{transform:scale(1.06);}
.amt-katazuke .kz-sno{position:absolute;left:14px;top:14px;background:var(--primary);color:var(--ink);font-weight:900;font-size:.82rem;letter-spacing:.08em;padding:4px 12px;border-radius:999px;box-shadow:0 4px 10px rgba(0,0,0,.2);}
.amt-katazuke .kz-sbody{padding:20px 22px 22px;display:flex;flex-direction:column;flex:1;}
.amt-katazuke .kz-sbody h3{font-size:1.2rem;font-weight:900;margin:0 0 8px;}
.amt-katazuke .kz-sbody p{font-size:.93rem;color:#4a4740;margin:0 0 14px;flex:1;}
.amt-katazuke .kz-more{font-weight:900;font-size:.9rem;color:var(--dark);}
.amt-katazuke .kz-more::after{content:" →";color:var(--primary-dark);}
@media(max-width:900px){.amt-katazuke .kz-scard{flex-basis:calc((100% - 22px)/2);}}
@media(max-width:560px){.amt-katazuke .kz-scard{flex-basis:100%;}}

/* お困りごと（イラストカード） */
.amt-katazuke .kz-scn .card{border-top:none;border-radius:18px;border:1px solid #efe8d4;box-shadow:0 8px 22px rgba(30,36,40,.07);}
.amt-katazuke .kz-scn .card h3 .mk{display:none;}
.amt-katazuke .kz-scn .card h3{text-align:center;}
.amt-katazuke .kz-scn .card p{text-align:center;}
.amt-katazuke .kz-scn .card-illust{background:radial-gradient(circle at 50% 60%,var(--primary-light),transparent 70%);border-radius:14px;padding:6px 0;}

/* 選ばれる理由 */
.amt-katazuke .kz-rsn{background:#fff;}
.amt-katazuke .kz-rgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
.amt-katazuke .kz-rcard{position:relative;background:#fff;border:1px solid #efe8d4;border-radius:18px;padding:30px 22px 24px;box-shadow:0 10px 26px rgba(30,36,40,.07);overflow:hidden;transition:transform .25s,box-shadow .25s;}
.amt-katazuke .kz-rcard:hover{transform:translateY(-5px);box-shadow:0 18px 36px rgba(30,36,40,.13);}
.amt-katazuke .kz-rcard::after{content:attr(data-n);position:absolute;right:12px;top:2px;font-size:4.2rem;font-weight:900;line-height:1;color:rgba(247,181,0,.16);}
.amt-katazuke .kz-ric{display:flex;align-items:center;justify-content:center;width:58px;height:58px;border-radius:16px;background:var(--dark);margin:0 0 16px;box-shadow:0 8px 18px rgba(30,36,40,.25);}
.amt-katazuke .kz-ric svg{width:30px;height:30px;}
.amt-katazuke .kz-rcard h3{font-size:1.08rem;font-weight:900;margin:0 0 10px;line-height:1.5;}
.amt-katazuke .kz-rcard p{font-size:.9rem;color:#4a4740;margin:0;line-height:1.85;}
@media(max-width:960px){.amt-katazuke .kz-rgrid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:560px){.amt-katazuke .kz-rgrid{grid-template-columns:1fr;}}

/* 許可（証書風） */
.amt-katazuke .kz-lic{background:var(--gray);}
.amt-katazuke .kz-cert{max-width:760px;margin:0 auto;position:relative;background:#fffdf6;border-radius:6px;padding:44px 40px 36px;box-shadow:0 16px 40px rgba(30,36,40,.12);border:1px solid #e8dcb6;}
.amt-katazuke .kz-cert::before{content:"";position:absolute;inset:10px;border:2px solid var(--primary);border-radius:4px;pointer-events:none;}
.amt-katazuke .kz-cert::after{content:"";position:absolute;inset:16px;border:1px solid rgba(224,160,0,.45);border-radius:2px;pointer-events:none;}
.amt-katazuke .kz-cert-t{text-align:center;font-size:clamp(1.35rem,3vw,1.8rem);font-weight:900;letter-spacing:.3em;margin:0 0 6px;color:var(--ink);}
.amt-katazuke .kz-cert-s{text-align:center;font-size:.8rem;letter-spacing:.2em;color:#8a6200;margin:0 0 24px;}
.amt-katazuke .kz-cert dl{display:grid;grid-template-columns:9em 1fr;gap:0;margin:0 auto;max-width:520px;}
.amt-katazuke .kz-cert dt,.amt-katazuke .kz-cert dd{padding:12px 6px;border-bottom:1px dashed #e2d3a6;margin:0;}
.amt-katazuke .kz-cert dt{font-weight:700;color:#6b5a2a;}
.amt-katazuke .kz-cert dd{font-weight:900;}
.amt-katazuke .kz-seal{position:absolute;right:34px;bottom:26px;width:86px;height:86px;border-radius:50%;border:3px solid rgba(224,160,0,.75);display:flex;align-items:center;justify-content:center;text-align:center;font-size:.72rem;font-weight:900;line-height:1.3;color:rgba(160,110,0,.9);transform:rotate(-12deg);background:rgba(255,245,214,.6);}
.amt-katazuke .kz-cert-note{max-width:760px;margin:22px auto 0;font-size:.88rem;color:#555;text-align:center;line-height:1.85;}
@media(max-width:600px){.amt-katazuke .kz-cert{padding:36px 22px 110px;}.amt-katazuke .kz-cert dl{grid-template-columns:1fr;}.amt-katazuke .kz-cert dt{border-bottom:none;padding-bottom:0;}.amt-katazuke .kz-seal{right:50%;transform:translateX(50%) rotate(-12deg);bottom:16px;}}

/* ご利用の流れ（タイムライン） */
.amt-katazuke .kz-flow{background:#fff;}
.amt-katazuke .kz-fwrap{display:grid;grid-template-columns:1fr 220px;gap:28px;align-items:center;}
.amt-katazuke .kz-steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:14px;position:relative;}
.amt-katazuke .kz-steps::before{content:"";position:absolute;left:8%;right:8%;top:30px;height:4px;border-radius:2px;background:repeating-linear-gradient(90deg,var(--primary) 0 14px,transparent 14px 22px);}
.amt-katazuke .kz-steps li{position:relative;text-align:center;}
.amt-katazuke .kz-sn{position:relative;display:flex;align-items:center;justify-content:center;width:62px;height:62px;margin:0 auto 14px;border-radius:50%;background:var(--dark);color:var(--primary);font-weight:900;font-size:1.25rem;border:4px solid #fff;box-shadow:0 0 0 3px var(--primary),0 10px 20px rgba(30,36,40,.2);}
.amt-katazuke .kz-steps h3{font-size:1rem;font-weight:900;margin:0 0 6px;}
.amt-katazuke .kz-steps p{font-size:.85rem;color:#555;margin:0;line-height:1.75;}
.amt-katazuke .kz-fmascot img{width:100%;max-width:220px;height:auto;display:block;margin:0 auto;filter:drop-shadow(0 12px 18px rgba(0,0,0,.18));}
.amt-katazuke .kz-flow-more{text-align:center;margin:30px 0 0;}
.amt-katazuke .kz-btn{display:inline-block;background:var(--dark);color:#fff!important;font-weight:900;text-decoration:none;padding:13px 34px;border-radius:999px;box-shadow:0 8px 20px rgba(30,36,40,.22);transition:transform .2s;}
.amt-katazuke .kz-btn:hover{transform:translateY(-2px);}
.amt-katazuke .kz-btn::after{content:" →";color:var(--primary);}
@media(max-width:960px){.amt-katazuke .kz-fwrap{grid-template-columns:1fr;}.amt-katazuke .kz-fmascot{display:none;}}
@media(max-width:760px){.amt-katazuke .kz-steps{grid-template-columns:1fr;gap:0;}.amt-katazuke .kz-steps::before{left:30px;right:auto;top:20px;bottom:20px;width:4px;height:auto;background:repeating-linear-gradient(180deg,var(--primary) 0 14px,transparent 14px 22px);}.amt-katazuke .kz-steps li{display:grid;grid-template-columns:62px 1fr;column-gap:16px;text-align:left;padding:0 0 18px;}.amt-katazuke .kz-sn{grid-row:span 2;margin:0;}.amt-katazuke .kz-steps h3{align-self:end;}}

/* 対応エリア */
.amt-katazuke .kz-area{background:var(--gray);}
.amt-katazuke .kz-agrid{display:grid;grid-template-columns:1.3fr 1fr;gap:34px;align-items:center;}
.amt-katazuke .kz-agrid .area-map{margin:0;}
.amt-katazuke .kz-agrid .area-map img{border-radius:18px;box-shadow:0 14px 34px rgba(30,36,40,.14);}
.amt-katazuke .kz-chips{list-style:none;display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px;padding:0;}
.amt-katazuke .kz-chips li{background:#fff;border:1px solid #e8dcb6;border-radius:999px;padding:6px 14px;font-weight:700;font-size:.9rem;}
.amt-katazuke .kz-chips li.is-base{background:var(--dark);border-color:var(--dark);color:#fff;}
.amt-katazuke .kz-chips li.is-base::before{content:"● ";color:var(--primary);}
.amt-katazuke .kz-atx p{margin:0 0 12px;line-height:1.9;}
@media(max-width:860px){.amt-katazuke .kz-agrid{grid-template-columns:1fr;}}

/* 会社概要（タイル） */
.amt-katazuke .kz-co{background:#fff;}
.amt-katazuke .kz-cogrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.amt-katazuke .kz-tile{background:var(--gray);border-radius:16px;padding:20px 22px;border:1px solid #efe8d4;}
.amt-katazuke .kz-tile .t{display:block;font-size:.76rem;font-weight:700;letter-spacing:.14em;color:#8a6200;margin:0 0 6px;}
.amt-katazuke .kz-tile .v{font-weight:900;font-size:1.02rem;line-height:1.65;word-break:break-word;}
.amt-katazuke .kz-tile .v a{color:var(--ink);}
.amt-katazuke .kz-tile--wide{grid-column:span 3;background:var(--deep);border-color:var(--deep);color:#fff;}
.amt-katazuke .kz-tile--wide .t{color:var(--primary);}
.amt-katazuke .kz-biz{list-style:none;display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 0;padding:0;}
.amt-katazuke .kz-biz li{border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:6px 14px;font-weight:700;font-size:.88rem;}
.amt-katazuke .kz-biz li.is-here{background:var(--primary);border-color:var(--primary);color:var(--ink);}
@media(max-width:860px){.amt-katazuke .kz-cogrid{grid-template-columns:1fr 1fr;}.amt-katazuke .kz-tile--wide{grid-column:span 2;}}
@media(max-width:520px){.amt-katazuke .kz-cogrid{grid-template-columns:1fr;}.amt-katazuke .kz-tile--wide{grid-column:auto;}}

/* コントラスト・表示比率の是正（PSI 2026-10-05） */
.amt-katazuke .kz-pas-mark{height:auto;}
.amt-katazuke .kz-seal{color:#7a5200;border-color:#b07a00;}
.amt-katazuke .kz-cert-note a,.amt-katazuke .kz-lic a{color:#7a5200;}
.amt-katazuke .foot-col a.foot-mail{color:var(--ink);}
.amt-katazuke .foot-bottom{color:#a9afb3;}
"""
V2_CSS = V2_CSS.replace('__LOGO_V2__', IMG['logo_v2'])
DESIGN_CSS = DESIGN_CSS + V2_CSS


V3_CSS = """
/* ============================================================
   2026-10-10 v3：ヘッダー/フッターの格上げ・料金ボックス・スマホ固定CTA
   ============================================================ */

/* ---- ヘッダー：スティッキー＋信頼バー ---- */
.amt-katazuke .k-header{position:sticky;top:0;z-index:60;background:var(--white);
  box-shadow:0 2px 18px rgba(20,26,30,.12);}
.amt-katazuke .hdr-topbar{height:4px;
  background:linear-gradient(90deg,var(--dark),var(--primary-dark) 38%,var(--primary) 66%,var(--primary-bright));}
.amt-katazuke .hdr-trust{background:var(--dark-2);color:#e8ebed;}
.amt-katazuke .hdr-trust-in{max-width:1080px;margin:0 auto;padding:6px 16px;display:flex;flex-wrap:wrap;
  gap:4px 20px;font-size:.74rem;font-weight:700;letter-spacing:.2px;}
.amt-katazuke .hdr-trust-in span{position:relative;padding-left:14px;white-space:nowrap;}
.amt-katazuke .hdr-trust-in span::before{content:"";position:absolute;left:0;top:50%;width:6px;height:6px;
  margin-top:-3px;border-radius:50%;background:var(--primary);}
.amt-katazuke .header-inner{max-width:1080px;margin:0 auto;padding:11px 16px;display:flex;align-items:center;
  justify-content:space-between;gap:16px;}
.amt-katazuke .hdr-act{display:flex;align-items:stretch;gap:10px;flex-shrink:0;}

/* 電話ボタン：ラベル＋番号の2段組 */
.amt-katazuke .k-header .header-tel{text-align:left;}
.amt-katazuke .tel-btn{display:inline-flex;align-items:center;gap:10px;
  background:linear-gradient(135deg,var(--primary-dark),var(--primary-bright));
  color:var(--ink) !important;text-decoration:none;padding:9px 20px;border-radius:12px;
  box-shadow:0 5px 14px rgba(224,160,0,.35);border:1px solid rgba(0,0,0,.06);
  transition:transform .15s,box-shadow .15s;}
.amt-katazuke .tel-btn:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(224,160,0,.45);}
.amt-katazuke .tel-btn svg{flex-shrink:0;}
.amt-katazuke .tel-btn .tb-tx{display:flex;flex-direction:column;line-height:1.15;}
.amt-katazuke .tel-btn .tb-tx small{font-size:.68rem;font-weight:700;opacity:.8;}
.amt-katazuke .tel-btn .tb-tx b{font-size:1.3rem;font-weight:900;letter-spacing:.4px;}

/* 無料見積りボタン：濃色で対比 */
.amt-katazuke .hdr-quote{display:flex;flex-direction:column;justify-content:center;align-items:center;
  background:var(--dark);color:#fff !important;text-decoration:none;padding:9px 20px;border-radius:12px;
  line-height:1.2;box-shadow:0 5px 14px rgba(47,58,65,.3);transition:transform .15s,background .15s;}
.amt-katazuke .hdr-quote:hover{background:var(--dark-2);transform:translateY(-1px);}
.amt-katazuke .hdr-quote b{font-size:1rem;font-weight:900;}
.amt-katazuke .hdr-quote small{font-size:.66rem;color:var(--primary-bright);font-weight:700;margin-top:2px;}

@media(max-width:900px){
  .amt-katazuke .hdr-quote{display:none;}
  .amt-katazuke .hdr-trust-in span:nth-child(n+3){display:none;}
}
@media(max-width:760px){
  .amt-katazuke .k-header{position:static;}
  .amt-katazuke .header-inner{flex-wrap:wrap;justify-content:center;text-align:center;gap:8px;padding:10px 14px;}
  .amt-katazuke .k-header .logo{justify-content:center;}
  .amt-katazuke .hdr-act{display:none;}
  .amt-katazuke .hdr-trust-in{justify-content:center;font-size:.68rem;gap:2px 14px;}
}

/* ---- グローバルナビ：下線アニメを少し上質に ---- */
.amt-katazuke .k-nav{background:var(--dark);position:relative;box-shadow:inset 0 -1px 0 rgba(255,255,255,.07);}
.amt-katazuke .k-nav a{font-size:.86rem;letter-spacing:.2px;}
.amt-katazuke .k-nav a::after{height:3px;bottom:4px;border-radius:2px;
  background:linear-gradient(90deg,var(--primary),var(--primary-bright));}
.amt-katazuke .k-nav a[aria-current="page"]{background:linear-gradient(180deg,var(--primary-bright),var(--primary));}

/* ---- 料金ボックス（/ryoukin/・トップ） ---- */
.amt-katazuke .kz-price{margin:22px 0 12px;padding:24px 26px;border-radius:18px;
  background:linear-gradient(135deg,var(--dark),var(--dark-2));color:#fff;position:relative;overflow:hidden;
  box-shadow:0 14px 34px rgba(31,37,41,.26);}
.amt-katazuke .kz-price::after{content:"";position:absolute;right:-50px;top:-50px;width:190px;height:190px;
  border-radius:50%;background:radial-gradient(circle,rgba(247,181,0,.45),transparent 68%);}
.amt-katazuke .kz-price-lbl{margin:0 0 4px;font-size:.88rem;font-weight:700;color:var(--primary-bright);
  letter-spacing:.4px;position:relative;}
.amt-katazuke .kz-price-val{margin:0;display:flex;align-items:baseline;flex-wrap:wrap;gap:0 6px;position:relative;}
.amt-katazuke .kz-price-num{font-size:3.4rem;font-weight:900;line-height:1;letter-spacing:-1px;
  color:var(--primary-bright);}
.amt-katazuke .kz-price-yen{font-size:1.5rem;font-weight:900;color:var(--primary-bright);}
.amt-katazuke .kz-price-unit{font-size:1.05rem;font-weight:700;color:#fff;}
.amt-katazuke .kz-price-unit b{font-size:1.3rem;font-weight:900;color:var(--primary-bright);}
.amt-katazuke .kz-price-note{margin:10px 0 0;font-size:.84rem;color:#cfd5d9;position:relative;line-height:1.7;}
@media(max-width:560px){
  .amt-katazuke .kz-price{padding:20px 18px;}
  .amt-katazuke .kz-price-num{font-size:2.6rem;}
}

/* ---- フッター：5カラム・料金・許認可・エリア帯 ---- */
.amt-katazuke .k-footer{background:linear-gradient(180deg,#232a2e,#1b2125);color:#d7dcdf;
  border-top:5px solid var(--primary);}
.amt-katazuke .foot-inner{max-width:1180px;margin:0 auto;padding:46px 20px 26px;display:grid;
  grid-template-columns:1.55fr .9fr .9fr .9fr 1.05fr;gap:30px;}
.amt-katazuke .foot-h{color:#fff;font-size:.93rem;font-weight:800;margin:0 0 14px;padding-bottom:8px;
  border-bottom:2px solid var(--primary);letter-spacing:.3px;}
.amt-katazuke .foot-price{display:flex;flex-direction:column;gap:2px;margin:14px 0 10px;padding:12px 14px;
  border-radius:12px;background:rgba(247,181,0,.1);border:1px solid rgba(247,181,0,.3);}
.amt-katazuke .foot-price span{font-size:.74rem;font-weight:700;color:#c8cdd1;}
.amt-katazuke .foot-price b{font-size:1.08rem;font-weight:900;color:var(--primary-bright);}
.amt-katazuke .foot-lic{margin:0;font-size:.74rem;color:#9aa1a6;line-height:1.6;}
.amt-katazuke .foot-area{max-width:1180px;margin:0 auto;padding:0 20px 20px;}
.amt-katazuke .foot-area p{margin:0;padding:14px 16px;border-radius:12px;background:rgba(255,255,255,.045);
  font-size:.8rem;color:#b6bcc0;line-height:1.8;}
.amt-katazuke .foot-area b{color:var(--primary-bright);margin-right:4px;}
.amt-katazuke .foot-area a{color:#d7dcdf;}
.amt-katazuke .foot-col a{transition:color .15s;}
@media(max-width:1000px){
  .amt-katazuke .foot-inner{grid-template-columns:1fr 1fr 1fr;}
  .amt-katazuke .foot-about{grid-column:1 / -1;}
}
@media(max-width:620px){
  .amt-katazuke .foot-inner{grid-template-columns:1fr 1fr;gap:22px;}
}
@media(max-width:420px){
  .amt-katazuke .foot-inner{grid-template-columns:1fr;}
}

/* ---- スマホ下部の固定CTA（PCでは非表示） ---- */
.amt-katazuke .kz-sticky{display:none;}
@media(max-width:760px){
  .amt-katazuke .kz-sticky{display:grid;grid-template-columns:1fr 1fr;gap:8px;position:fixed;left:0;right:0;
    bottom:0;z-index:80;padding:8px 10px calc(8px + env(safe-area-inset-bottom));
    background:rgba(33,42,48,.96);backdrop-filter:blur(6px);box-shadow:0 -4px 18px rgba(0,0,0,.3);}
  .amt-katazuke .kz-sticky a{display:flex;flex-direction:column;align-items:center;justify-content:center;
    text-decoration:none;border-radius:12px;padding:9px 6px;line-height:1.2;}
  .amt-katazuke .kz-sticky a span{font-size:.64rem;font-weight:700;opacity:.85;}
  .amt-katazuke .kz-sticky a b{font-size:1.02rem;font-weight:900;letter-spacing:.3px;}
  .amt-katazuke .kz-sticky .ks-tel{background:linear-gradient(135deg,var(--primary-dark),var(--primary-bright));
    color:var(--ink);}
  .amt-katazuke .kz-sticky .ks-mail{background:#fff;color:var(--dark);}
  /* 固定バーの高さぶん、本文末尾に余白を足す */
  .amt-katazuke .k-footer .foot-bottom{padding-bottom:76px;}
}
"""
V3_CSS = V3_CSS + """
/* ---- 対応事例（/jirei/） ---- */
.amt-katazuke .jr-list{display:grid;gap:26px;}
.amt-katazuke .jr-card{background:var(--white);border:1px solid #ece7da;border-radius:18px;
  padding:26px 26px 22px;box-shadow:0 10px 28px rgba(31,37,41,.07);}
.amt-katazuke .jr-card h2{margin:4px 0 16px;font-size:1.3rem;line-height:1.5;}
.amt-katazuke .jr-card h3{margin:20px 0 6px;font-size:1.02rem;}
.amt-katazuke .jr-tag{display:inline-block;margin:0;padding:4px 12px;border-radius:30px;
  background:var(--primary-light);color:#7a5400;font-size:.76rem;font-weight:800;}
.amt-katazuke .jr-img{margin:0 0 16px;border-radius:14px;overflow:hidden;}
.amt-katazuke .jr-img img{width:100%;height:auto;display:block;}
.amt-katazuke .jr-card table{margin:0 0 4px;}
.amt-katazuke .jr-card table th{width:34%;white-space:nowrap;}
.amt-katazuke .jr-voice{margin:18px 0 0;padding:14px 18px;border-left:4px solid var(--primary);
  background:var(--gray);border-radius:0 10px 10px 0;}
.amt-katazuke .jr-voice p{margin:0;font-size:.94rem;line-height:1.8;color:#4a453e;}
.amt-katazuke .jr-link{margin:16px 0 0;font-weight:700;}
@media(max-width:560px){
  .amt-katazuke .jr-card{padding:20px 16px 18px;}
  .amt-katazuke .jr-card h2{font-size:1.12rem;}
  .amt-katazuke .jr-card table th{width:40%;font-size:.84rem;}
}
"""
V3_CSS = V3_CSS + """
/* ---- ヒーローの料金バッジ ---- */
.amt-katazuke .kz-hprice{display:inline-flex;flex-direction:column;gap:1px;margin:0 0 18px;
  padding:12px 20px;border-radius:14px;background:rgba(33,42,48,.92);color:#fff;
  box-shadow:0 10px 26px rgba(20,26,30,.3);border:1px solid rgba(247,181,0,.4);}
.amt-katazuke .kz-hprice span{font-size:.76rem;font-weight:700;color:#cfd5d9;letter-spacing:.3px;}
.amt-katazuke .kz-hprice b{font-size:1.5rem;font-weight:900;color:var(--primary-bright);line-height:1.2;}
.amt-katazuke .kz-hprice small{font-size:.68rem;color:#aeb5ba;line-height:1.5;}
@media(max-width:560px){.amt-katazuke .kz-hprice{padding:10px 16px;}
  .amt-katazuke .kz-hprice b{font-size:1.25rem;}}

/* ---- 料金セクション ---- */
.amt-katazuke .kz-prc{background:var(--gray);}
.amt-katazuke .kz-prc-grid{display:grid;grid-template-columns:1fr 1.15fr;gap:26px;align-items:start;}
.amt-katazuke .kz-prc .kz-price{margin:0;}
.amt-katazuke .kz-inc{list-style:none;margin:0;padding:0;display:grid;gap:10px;}
.amt-katazuke .kz-inc li{background:#fff;border:1px solid #ece7da;border-radius:12px;padding:13px 16px;
  font-size:.9rem;line-height:1.75;color:#4a453e;}
.amt-katazuke .kz-inc li b{display:block;font-size:.78rem;font-weight:800;color:#8a6200;
  letter-spacing:.4px;margin-bottom:2px;}
@media(max-width:860px){.amt-katazuke .kz-prc-grid{grid-template-columns:1fr;}}

/* ---- 農機具買取セクション ---- */
.amt-katazuke .kz-nouki{background:linear-gradient(170deg,var(--dark),var(--dark-2));color:#eef1f3;
  position:relative;overflow:hidden;}
.amt-katazuke .kz-nouki::before{content:"";position:absolute;left:-80px;bottom:-80px;width:320px;height:320px;
  border-radius:50%;background:radial-gradient(circle,rgba(247,181,0,.2),transparent 70%);}
.amt-katazuke .kz-nouki .sec-eye{color:var(--primary-bright);}
.amt-katazuke .kz-nouki .sec-title{color:#fff;}
.amt-katazuke .kz-nouki .sec-title::after{background:var(--primary-bright);}
.amt-katazuke .kz-nouki .sec-lead{color:#c6ccd0;}
.amt-katazuke .kz-nouki .sec-lead strong{color:var(--primary-bright);}
.amt-katazuke .kz-npoints{list-style:none;margin:0 0 26px;padding:0;display:grid;
  grid-template-columns:repeat(4,1fr);gap:12px;}
.amt-katazuke .kz-npoints li{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13);
  border-radius:12px;padding:13px 15px;font-size:.8rem;line-height:1.6;color:#c6ccd0;}
.amt-katazuke .kz-npoints li b{display:block;font-size:.95rem;font-weight:900;color:var(--primary-bright);
  margin-bottom:3px;}
.amt-katazuke .kz-ngrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.amt-katazuke .kz-ncard{display:block;background:#fff;border-radius:14px;padding:20px 20px 16px;
  text-decoration:none;color:var(--ink);box-shadow:0 10px 26px rgba(0,0,0,.2);
  border-top:4px solid var(--primary);transition:transform .16s,box-shadow .16s;}
.amt-katazuke .kz-ncard:hover{transform:translateY(-3px);box-shadow:0 16px 34px rgba(0,0,0,.28);}
.amt-katazuke .kz-ncard h3{margin:0 0 6px;font-size:1.08rem;font-weight:900;color:var(--dark);}
.amt-katazuke .kz-ncard p{margin:0 0 10px;font-size:.84rem;color:#6b655c;line-height:1.65;}
.amt-katazuke .kz-narr{font-size:.8rem;font-weight:800;color:#8a6200;}
.amt-katazuke .kz-narr::after{content:" →";}
.amt-katazuke .kz-nlic{margin:20px 0 0;font-size:.78rem;color:#aeb5ba;line-height:1.75;}
.amt-katazuke .kz-nlic strong{color:#e8ebed;}
.amt-katazuke .kz-nouki .kz-btn{border-color:rgba(255,255,255,.3);color:#fff;}
.amt-katazuke .kz-nouki .kz-btn:hover{background:rgba(255,255,255,.1);}
@media(max-width:900px){
  .amt-katazuke .kz-npoints{grid-template-columns:1fr 1fr;}
  .amt-katazuke .kz-ngrid{grid-template-columns:1fr 1fr;}
}
@media(max-width:560px){
  .amt-katazuke .kz-npoints{grid-template-columns:1fr;}
  .amt-katazuke .kz-ngrid{grid-template-columns:1fr;}
}

/* ---- ボタン（塗り）・ボタン並び ---- */
.amt-katazuke .kz-btn--fill{background:linear-gradient(135deg,var(--primary-dark),var(--primary-bright));
  color:var(--ink) !important;border-color:transparent;box-shadow:0 6px 16px rgba(224,160,0,.35);}
.amt-katazuke .kz-btn--fill:hover{filter:brightness(1.05);background:linear-gradient(135deg,var(--primary-dark),var(--primary-bright));}
.amt-katazuke .kz-flow-more{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;}
.amt-katazuke .kz-abtns{display:flex;flex-wrap:wrap;gap:10px;}

/* ---- コラム導線 ---- */
.amt-katazuke .kz-collist{list-style:none;margin:0 0 24px;padding:0;display:grid;
  grid-template-columns:repeat(3,1fr);gap:12px;}
.amt-katazuke .kz-collist a{display:block;background:#fff;border:1px solid #ece7da;border-radius:12px;
  padding:16px 18px;text-decoration:none;color:var(--ink);font-weight:700;font-size:.92rem;line-height:1.6;
  transition:border-color .15s,box-shadow .15s,transform .15s;}
.amt-katazuke .kz-collist a::before{content:"COLUMN";display:block;font-size:.64rem;font-weight:800;
  color:#b08a1e;letter-spacing:1px;margin-bottom:5px;}
.amt-katazuke .kz-collist a:hover{border-color:var(--primary);transform:translateY(-2px);
  box-shadow:0 10px 22px rgba(31,37,41,.09);}
@media(max-width:860px){.amt-katazuke .kz-collist{grid-template-columns:1fr 1fr;}}
@media(max-width:520px){.amt-katazuke .kz-collist{grid-template-columns:1fr;}}
"""
V3_CSS = V3_CSS + """
/* ---- 仕上げの微調整 ---- */
/* ナビを1段に収める（11項目） */
@media(min-width:761px){
  .amt-katazuke .k-nav a{padding:12px 11px;font-size:.84rem;}
}
@media(min-width:761px) and (max-width:1040px){
  .amt-katazuke .k-nav a{padding:11px 8px;font-size:.79rem;}
}
/* ヒーローの料金バッジ：注記が枠からはみ出さないように */
.amt-katazuke .kz-hprice{display:flex;max-width:min(100%,420px);}
.amt-katazuke .kz-hprice small{white-space:normal;word-break:break-word;}
/* 「想い」の署名がスマホで切れないように */
@media(max-width:600px){
  .amt-katazuke .kz-sign{font-size:.74rem;letter-spacing:0;white-space:normal;text-align:right;}
}
/* 長い見出し・語がスマホで溢れないための保険 */
.amt-katazuke h1,.amt-katazuke h2,.amt-katazuke h3{overflow-wrap:anywhere;}
.amt-katazuke .foot-logo .fl-tx{overflow-wrap:anywhere;}
"""
DESIGN_CSS = DESIGN_CSS + V3_CSS

# ロゴマーク（片付け＝きれいに整った家＋きらめき）。文字は入れない。
LOGO_SVG = (
    '<svg viewBox="0 0 48 48" width="46" height="46" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<rect width="48" height="48" rx="11" fill="#f7b500"/>'
    '<path d="M11 24l13-10 13 10" fill="none" stroke="#2f3a41" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M14 22.5V35h20V22.5" fill="none" stroke="#2f3a41" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M20.5 35v-6h7v6" fill="none" stroke="#2f3a41" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M37 13l1.1 2.4L40.5 16.5l-2.4 1.1L37 20l-1.1-2.4L33.5 16.5l2.4-1.1z" fill="#ffffff"/>'
    '</svg>'
)

TEL_ICON = (
    '<svg viewBox="0 0 24 24" width="19" height="19" fill="#2a2724" style="flex-shrink:0">'
    '<path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.4 21 3 13.6 3 4.5 3 3.9 3.4 3.5 4 3.5H7.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.4 0 .8-.3 1l-2.2 1.7z"/></svg>'
)


def header(current=""):
    lis = "".join(
        f'<li><a href="{u}"{" aria-current=\"page\"" if u == current else ""}>{t}</a></li>'
        for u, t in NAV_ITEMS
    )
    return (
        '<header class="k-header">'
        '<div class="hdr-topbar"></div>'
        # 上段：許認可・対応範囲の信頼バー
        '<div class="hdr-trust"><div class="hdr-trust-in">'
        '<span>静岡県島田市・金谷の片付け屋</span>'
        f'<span>{KOBUTSU_LABEL}</span>'
        '<span>個人・法人対応</span>'
        '<span>出張見積り無料</span>'
        '</div></div>'
        '<div class="header-inner">'
        f'<a class="logo" href="/"><span class="logo-mark"><img src="{IMG["logo_v2"]}" alt="おうちのお片付け隊 ロゴ" width="64" height="64"></span>'
        f'<span class="logo-tx"><span class="logo-name"><b>{COMPANY_NAME}</b> {SITE_NAME}</span>'
        f'<small>{CATCH}</small></span></a>'
        '<div class="hdr-act">'
        f'<div class="header-tel"><a class="tel-btn" href="tel:{TEL}">{TEL_ICON}<span class="tb-tx">'
        f'<small>お電話でのご相談</small><b>{TEL}</b></span></a></div>'
        '<a class="hdr-quote" href="/contact/"><b>無料見積り</b><small>24時間受付</small></a>'
        '</div></div></header>'
        '<nav class="k-nav"><input type="checkbox" id="amtnav" class="amt-navtoggle">'
        '<label class="amt-navbtn" for="amtnav"><span class="bars"><i></i></span>メニュー</label>'
        f'<ul>{lis}</ul></nav>'
    )


def sticky_cta():
    """スマホ画面の下部に固定表示するCTAバー（電話／無料見積り）。"""
    return (
        '<div class="kz-sticky" role="complementary" aria-label="お問い合わせ">'
        f'<a class="ks-tel" href="tel:{TEL}"><span>お電話</span><b>{TEL}</b></a>'
        '<a class="ks-mail" href="/contact/"><span>かんたん</span><b>無料見積り</b></a>'
        '</div>'
    )


def breadcrumb(label):
    return ('<div class="breadcrumb"><a href="/">ホーム</a>'
            f'<span>›</span>{label}</div>')


def page_hero(h1, lead):
    return (f'<div class="page-hero hero"><div class="hero-inner"><h1>{h1}</h1>'
            f'<p>{lead}</p></div></div>')


def cta():
    return (
        '<section class="cta-band"><div class="cta-inner">'
        f'<div class="cta-mascot"><img src="{IMG["mascot_hero_v2"]}" alt="おうちのお片付け隊 マスコット" width="210" height="213" loading="lazy" decoding="async"></div>'
        '<div class="cta-content"><h2>お片付けのご相談・お見積りは無料です</h2>'
        '<p>「いくらかかる？」「これは回収できる？」だけでもお気軽にどうぞ。'
        '個人のお客様も法人のお客様も、静岡県内を中心に対応します。</p>'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}</a>'
        '<div class="btn-line"><a class="btn-mail" href="/contact/">'
        'メールで相談する</a></div></div></div></section>'
    )


def footer():
    svc = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_SERVICE)
    nouki = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_NOUKI)
    gui = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_GUIDE)
    areas = "・".join(AREA_CITIES)
    return (
        '<footer class="k-footer">'
        '<div class="foot-inner">'
        '<div class="foot-col foot-about">'
        f'<div class="foot-logo"><img src="{IMG["logo_v2"]}" alt="" width="44" height="44" loading="lazy" decoding="async"><span class="fl-tx"><span>{COMPANY_NAME}</span> {SITE_NAME}</span></div>'
        '<p>静岡県島田市金谷を拠点に、家の片付け・不用品回収・解体前の残置物撤去・'
        '倉庫の片付け・農機具の買取りまで対応します。個人のお客様も法人・事業者さまも、'
        'お見積り・ご相談は無料です。</p>'
        f'<p class="foot-price"><span>片付け・不用品回収</span><b>{PRICE_LABEL}</b></p>'
        f'<p class="foot-lic">{KOBUTSU_TD}</p>'
        '</div>'
        f'<div class="foot-col"><p class="foot-h">サービス</p><ul>{svc}</ul></div>'
        f'<div class="foot-col"><p class="foot-h">農機具の買取り</p><ul>{nouki}</ul></div>'
        f'<div class="foot-col"><p class="foot-h">ご案内</p><ul>{gui}</ul></div>'
        '<div class="foot-col foot-contact"><p class="foot-h">お問い合わせ</p>'
        f'<a class="foot-tel" href="tel:{TEL}">{TEL}</a>'
        '<p class="foot-note">お見積り・ご相談は無料</p>'
        '<a class="foot-mail" href="/contact/">メールで相談する</a>'
        '<p class="foot-addr">〒428-0013<br>静岡県島田市金谷東2丁目3483-290</p>'
        '<p class="foot-corp"><a href="https://amt-eco.com/" target="_blank" rel="noopener">'
        'コーポレートサイト ↗</a><br>'
        '<a href="https://kaitai.amt-eco.com/" target="_blank" rel="noopener">'
        '解体工事サイト ↗</a></p></div></div>'
        f'<div class="foot-area"><p><b>対応エリア</b>　{areas}　ほか静岡県内'
        '（<a href="/area/">対応エリアの詳細</a>）</p></div>'
        '<div class="foot-bottom"><p><a href="/privacy-policy/">プライバシーポリシー</a>'
        '　｜　&copy; 株式会社AMT All Rights Reserved.</p></div></footer>'
        + sticky_cta()
    )


def faq_block(items):
    if not items:
        return ""
    inner = "".join(
        f'<div class="faq-item"><div class="faq-q">{q}</div>'
        f'<div class="faq-a">{a}</div></div>' for q, a in items
    )
    return ('<section class="k-section"><div class="inner">'
            '<h2 class="sec-title">よくある質問</h2>'
            f'<div class="faq">{inner}</div></div></section>')


def rel_block(cards):
    if not cards:
        return ""
    inner = "".join(
        f'<a class="rel-card" href="{u}"><b>{t}</b><span>{d}</span></a>'
        for u, t, d in cards
    )
    return ('<section class="k-section"><div class="inner">'
            '<h2 class="sec-title">関連ページ</h2>'
            f'<div class="rel-grid">{inner}</div></div></section>')


def faq_jsonld(items):
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in items
        ],
    }


def breadcrumb_jsonld(label, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": label, "item": DOMAIN + url},
        ],
    }


def service_jsonld(name, desc, url):
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": name,
        "name": name,
        "description": desc,
        "areaServed": {"@type": "AdministrativeArea", "name": AREA_NAME},
        "provider": {
            "@type": PROVIDER_TYPE,
            "name": COMPANY_NAME,
            "url": DOMAIN + "/",
            "telephone": TEL_INTL,
        },
        "url": DOMAIN + url,
    }


def local_business_jsonld():
    """サイト共通の LocalBusiness（トップ・料金・農機具ハブで使う完全版）。"""
    return {
        "@context": "https://schema.org",
        "@type": PROVIDER_TYPE,
        "@id": DOMAIN + "/#localbusiness",
        "name": COMPANY_NAME + "（" + SITE_NAME + "）",
        "alternateName": SITE_NAME,
        "url": DOMAIN + "/",
        "telephone": TEL_INTL,
        "email": MAIL,
        "image": IMG["ogp_v2"],
        "logo": IMG["logo_v2_png"],
        "priceRange": "¥¥",
        "currenciesAccepted": PRICE_CURRENCY,
        "paymentAccepted": "現金, 銀行振込",
        "sameAs": SAME_AS,
        "address": {
            "@type": "PostalAddress",
            "postalCode": "428-0013",
            "addressRegion": "静岡県",
            "addressLocality": "島田市",
            "streetAddress": "金谷東2丁目3483-290",
            "addressCountry": "JP",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": GEO_LAT, "longitude": GEO_LNG},
        "areaServed": [{"@type": "City", "name": c} for c in AREA_CITIES],
        "knowsAbout": ["家の片付け", "不用品回収", "残置物撤去", "倉庫・工場の片付け",
                       "農機具買取", "生前整理", "遺品整理", "空き家の片付け"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "片付け・不用品回収・農機具買取のサービス",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": n, "url": DOMAIN + u}}
                for n, u in [
                    ("家のお片付け", "/katazuke/"),
                    ("不用品の回収", "/fuyouhin/"),
                    ("解体前の残置物撤去", "/zanchibutsu/"),
                    ("倉庫・工場の片付け", "/souko/"),
                    ("農機具の買取り", "/nouki-kaitori/"),
                    ("生前整理・遺品整理", "/seiri/"),
                ]
            ],
        },
        "description": "静岡県島田市の株式会社AMTによる、家の片付け・不用品回収・"
                       "解体前の残置物撤去・倉庫の片付け・農機具買取のサービス。個人・法人対応。",
    }


def price_offer_jsonld(url, name, desc):
    """料金の構造化データ（1㎥あたりの単価）。AI検索・リッチリザルトで価格を拾わせる。"""
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": desc,
        "serviceType": "不用品回収・片付け",
        "url": DOMAIN + url,
        "provider": {"@id": DOMAIN + "/#localbusiness"},
        "areaServed": [{"@type": "City", "name": c} for c in AREA_CITIES],
        "offers": {
            "@type": "Offer",
            "url": DOMAIN + url,
            "priceCurrency": PRICE_CURRENCY,
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": PRICE_PER_M3,
                "priceCurrency": PRICE_CURRENCY,
                "minPrice": PRICE_PER_M3,
                "unitText": "立方メートル",
                "unitCode": "MTQ",
                "referenceQuantity": {
                    "@type": "QuantitativeValue", "value": 1,
                    "unitText": "立方メートル", "unitCode": "MTQ",
                },
            },
            "availability": "https://schema.org/InStock",
            "areaServed": [{"@type": "City", "name": c} for c in AREA_CITIES],
        },
    }


def howto_jsonld(name, desc, url, steps):
    """ご利用の流れ → HowTo。steps = [(見出し, 本文), ...]"""
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "description": desc,
        "url": DOMAIN + url,
        "totalTime": "P1D",
        "estimatedCost": {"@type": "MonetaryAmount", "currency": PRICE_CURRENCY,
                          "value": PRICE_PER_M3, "description": PRICE_LABEL},
        "step": [
            {"@type": "HowToStep", "position": i + 1, "name": t,
             "text": d, "url": DOMAIN + url + "#step" + str(i + 1)}
            for i, (t, d) in enumerate(steps)
        ],
    }


def itemlist_jsonld(name, desc, url, items):
    """一覧ページ（事例・機種別など）→ ItemList。items = [(名前, URL or None, 説明), ...]"""
    el = []
    for i, (t, u, d) in enumerate(items):
        item = {"@type": "ListItem", "position": i + 1, "name": t}
        if u:
            item["url"] = DOMAIN + u
        if d:
            item["description"] = d
        el.append(item)
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "description": desc,
        "url": DOMAIN + url,
        "numberOfItems": len(items),
        "itemListElement": el,
    }


def assemble(slug, breadcrumb_label, hero_h1, hero_lead, body_html,
             faq_items, rel_cards, jsonlds, hero_img=None, hero_illust=None):
    """下層ページ本体を wp:html ブロックとして組み立てる。"""
    url = "/" + slug + "/"
    parts = ['<div class="amt-katazuke">']
    parts.append(header(url))
    parts.append(breadcrumb(breadcrumb_label))
    parts.append(page_hero(hero_h1, hero_lead))
    if hero_illust:
        # 透過イラストを見出し画像として中央に（写真ヒーローの代わり）
        parts.append(f'<div class="svc-hero svc-hero--illust"><img src="{hero_illust}" alt="{breadcrumb_label}のイラスト" width="560" height="520" loading="lazy"></div>')
    elif hero_img:
        parts.append(f'<div class="svc-hero"><img src="{hero_img}" alt="{breadcrumb_label}" width="1200" height="800" loading="lazy"></div>')
    parts.append(body_html)
    parts.append(faq_block(faq_items))
    parts.append(rel_block(rel_cards))
    parts.append(cta())
    parts.append(footer())
    parts.append('</div>')
    html_block = "<!-- wp:html -->\n" + "".join(parts) + "\n<!-- /wp:html -->"
    scripts = []
    for j in jsonlds:
        if j:
            scripts.append(
                '<!-- wp:html -->\n<script type="application/ld+json">'
                + json.dumps(j, ensure_ascii=False)
                + "</script>\n<!-- /wp:html -->"
            )
    return "\n\n".join([html_block] + scripts), url


PAGES = []

# 各サービスページ冒頭に置く「要点（結論先出し）」ブロック（SEO/AIO：AI検索・強調スニペット対策）。
# slug をキーに add_service_page が自動で挿入する。
ANSWERS = {
    "katazuke": "家のお片付けは<strong>仕分けから搬出まで</strong>一括対応。引越し・空き家・生前整理など量を問わず、まだ使えるものは<strong>買取</strong>で費用に反映できます。現地確認のうえ<strong>無料でお見積り</strong>します。",
    "fuyouhin": "不用品は<strong>まだ使えるものは古物商で買取</strong>し、処分が必要なものは提携する許可業者へ適正処理を委託します。1点から家一軒分まで、個人・法人対応。<strong>お見積り無料</strong>です。",
    "zanchibutsu": "解体前の残置物撤去は、家財・設備・不用品を建物からすべて搬出します。<strong>解体工事も自社対応</strong>のため撤去から解体まで一貫。買取できるものは費用に反映します。",
    "souko": "倉庫・工場の片付けは、<strong>業務を止めない段取り</strong>で在庫・什器・機械を仕分け。使えるものは買取、処分は許可業者へ委託します。<strong>請求書払い可</strong>。",
    "nouki-kaitori": "使わない農機具は<strong>古物商許可（機械工具類）</strong>のもとで買取します。トラクター・耕運機・田植機など、動かない機械もまずご相談を。片付け・搬出と同時対応も可能です。",
    "seiri": "生前整理・遺品整理は、仕分け・搬出・<strong>買取</strong>・適正処理までまとめて対応。遠方・立ち会い困難のご事情も相談可。解体が必要なら残置物撤去まで一貫します。<strong>お見積り無料</strong>。",
    "hinmoku": "家具・家電・生活用品・事務什器・農機具・金属まで幅広く対応。<strong>使えるものは買取</strong>、処分は提携する許可業者へ適正処理を委託します。掲載外の品もご相談ください。",
    "akiya": "空き家・実家の片付けは<strong>遠方でも対応</strong>。現地確認と見積りをまとめ、搬出・買取・処分・清掃まで。解体予定なら<strong>残置物撤去から解体まで一貫</strong>します。",
    "gomiyashiki-katazuke": "ゴミ屋敷は<strong>安全確保→貴重品の確保→仕分け→清掃</strong>の順で対応します。プライバシーに配慮し、分別・搬出・買取・清掃までまとめて。<strong>お見積り無料</strong>。",
    "hikkoshi": "引っ越しの不用品は<strong>期日までにまとめて</strong>搬出・買取・処分します。大型家具・家電も対応（家電リサイクル法対象品は法令どおり）。引っ越し前後どちらも相談可。",
    "tenpo": "店舗・オフィスの閉店・移転は、什器・機械の<strong>買取</strong>＋撤去＋<strong>産業廃棄物の適正処理委託</strong>＋原状回復・解体まで一貫対応。<strong>請求書払い可</strong>です。",
}


# 片付け → 解体サイトへの相互リンクバナー（assets/cross-link-snippets のスニペットを単一ソースとして読み込む）
KAITAI_BANNER_SLUGS = {"zanchibutsu", "akiya", "tenpo"}


def kaitai_banner():
    path = os.path.join(HERE, "cross-link-snippets", "for-katazuke-site-to-kaitai.html")
    try:
        with io.open(path, encoding="utf-8") as f:
            snip = f.read()
    except IOError:
        return ""
    snip = re.sub(r"<!--.*?-->", "", snip, flags=re.S).strip()
    snip = "".join(line.strip() for line in snip.splitlines())
    return ('<section class="k-section" style="padding-top:0;"><div class="inner">'
            + snip + '</div></section>')


# 下層ページの見出し画像に透過イラストを使うページ（slug → IMG キー）。写真ヒーローの代わりに中央表示。
HERO_ILLUSTS = {
    "seiri": "illust_seiri",
    "akiya": "illust_akiya",
    "gomiyashiki-katazuke": "illust_gomiyashiki",
    "hikkoshi": "illust_hikkoshi",
    "tenpo": "illust_tenpo",
    "hinmoku": "illust_hinmoku",
}


def add_service_page(slug, nav_label, h1, lead, body, faq, rel, jsonld_name, jsonld_desc, title, hero_img=None):
    ans = ANSWERS.get(slug)
    if ans:
        body = ('<section class="k-section" style="padding-bottom:0;">'
                '<div class="prose"><div class="answer"><span class="answer-h">要点</span>'
                '<p>' + ans + '</p></div></div></section>') + body
    if slug in KAITAI_BANNER_SLUGS:
        body = body + kaitai_banner()
    hi = HERO_ILLUSTS.get(slug)
    hero_illust = IMG[hi] if hi else None
    c, _ = assemble(
        slug, nav_label, h1, lead, body, faq, rel,
        [service_jsonld(jsonld_name, jsonld_desc, "/" + slug + "/"),
         breadcrumb_jsonld(nav_label, "/" + slug + "/"), faq_jsonld(faq)],
        hero_img=(None if hero_illust else hero_img), hero_illust=hero_illust,
    )
    PAGES.append((slug, title, c))


# ------------------------------------------------------------
# 1. 家のお片付け
# ------------------------------------------------------------
add_service_page(
    "katazuke", "家の片付け",
    "家のお片付け｜静岡県島田市の株式会社AMT",
    "お引越し前後・空き家・実家の片付けまで。仕分けから搬出まで、ご希望に合わせて静岡県内を中心に対応します。お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">ご自宅の片付けを、仕分けから搬出まで一括でお手伝いします。'
    'お引越しや模様替え、空き家・ご実家の整理など、量の多少を問わずご相談ください。'
    '個人のお客様はもちろん、事業者さまのご依頼にも対応します。</p>'
    '<h2>こんなときにご利用いただけます</h2>'
    '<ul><li>引越し前後で不要になった家具・家電をまとめて処分したい</li>'
    '<li>空き家・ご実家を片付けたいが、量が多くて手が回らない</li>'
    '<li>遠方に住んでいて、現地の片付けを任せたい</li>'
    '<li>生前整理・老前整理として少しずつ進めたい</li></ul>'
    '<h2>片付けの進め方</h2>'
    '<p>まず現地でお品物の量や搬出経路を確認し、ご要望をうかがいます。'
    '当日は、残すもの・処分するものを一緒に仕分けしながら搬出・運び出しを行います。'
    '処分が必要なものは提携する許可業者に適正処理を委託し、'
    'ご希望に応じて簡単な清掃までまとめて承ります。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、<strong>お品物の量・間取り・搬出経路・作業人数</strong>などによって変わります。'
    '正確な金額は現地を確認したうえで、<strong>無料でお見積り</strong>します。'
    '不用品の中に買取できるものがあれば、費用へ反映できる場合があります。</p>'
    '<p class="note">※料金は現地条件によって変わるため、このページには目安額を掲載していません。'
    'まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("少量でも片付けを依頼できますか？",
      "はい、一部屋・一部の家財だけでも承ります。量が多い場合ももちろん対応しますので、まずはご相談ください。"),
     ("立ち会いは必要ですか？",
      "当日の立ち会いをお願いすることが多いですが、遠方の場合など、ご事情に応じた進め方もご相談いただけます。")],
    [("/fuyouhin/", "不用品の回収", "家具・家電などをまとめて回収"),
     ("/zanchibutsu/", "解体前の残置物撤去", "解体予定の建物の家財撤去"),
     ("/ryoukin/", "料金・費用について", "費用の決まり方・抑え方"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで")],
    "家のお片付け", "引越し・空き家・実家の片付け。仕分けから搬出まで対応。静岡県内中心。",
    "家のお片付け｜静岡県島田市の株式会社AMT",
    hero_img=IMG["katazuke"],
)

# ------------------------------------------------------------
# 2. 不用品の回収
# ------------------------------------------------------------
add_service_page(
    "fuyouhin", "不用品回収",
    "不用品の回収（家具・家電）｜静岡県島田市の株式会社AMT",
    "ご家庭や事業所で不要になった家具・家電・雑貨などをまとめて回収します。量が多い場合もご相談ください。静岡県内中心・お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">お片付けや整理にともなって不要になった家具・家電・生活用品などを、'
    '搬出とあわせてお引き取りします。まだ使えるものは'
    '<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、'
    'その分を費用に反映できる場合があります。「一つだけ」から「家一軒分」まで、'
    '量を問わずご相談ください。個人のお客様も法人・事業者さまも対応します。</p>'
    '<h2>お引き取り・買取の対象になるもの（例）</h2>'
    '<ul><li>家具（タンス・ソファ・机・棚など）</li>'
    '<li>家電（冷蔵庫・洗濯機・テレビなど）</li>'
    '<li>生活用品・雑貨・寝具など</li>'
    '<li>オフィス什器・事業所の備品</li></ul>'
    '<p>家電リサイクル法の対象品目（テレビ・冷蔵庫・洗濯機・エアコンなど）は、'
    '法令に沿った取り扱いが必要です。回収の可否・方法は現地確認時にご案内します。</p>'
    '<h2>買取と適正処理の流れ</h2>'
    '<p>まだ使えるものは<strong>古物商許可のもとで買取</strong>し、'
    '処分が必要なものは<strong>提携する許可業者に適正処理を委託</strong>します。'
    '分別・搬出から適正な処理まで、まとめてお任せいただけます。</p>'
    '<h2>まとめてのご依頼がおすすめです</h2>'
    '<p>複数の品物を一度にまとめてお引き取りすると、搬出や運搬を効率化できます。'
    '片付けと合わせてのご依頼も承ります。'
    '<a href="/katazuke/">家のお片付け</a>とあわせてご相談ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、<strong>品物の種類・量・大きさ・搬出条件</strong>などによって変わります。'
    '現地確認のうえ<strong>無料でお見積り</strong>します。'
    '買取できる品物があれば、費用へ反映できる場合があります。</p>'
    '<p class="note">※取り扱いできない品目（危険物・法令で別途処理が必要なものなど）もあります。'
    '詳しくはお問い合わせください。</p>'
    '</div></section>',
    [("回収できないものはありますか？",
      "危険物や、法令で別途処理が定められているものなど、お引き取りできない品目があります。品目を確認のうえご案内しますので、まずはご相談ください。"),
     ("見積り後に品物が増えても大丈夫ですか？",
      "当日に品物が増えた場合は、その場で内容を確認して対応します。大きく変わる場合は改めてご説明します。")],
    [("/katazuke/", "家のお片付け", "仕分けから搬出まで"),
     ("/souko/", "倉庫の片付け", "資材・在庫・什器の整理"),
     ("/nouki-kaitori/", "農機具の買取り", "使わない農機具を買取"),
     ("/ryoukin/", "料金・費用について", "費用の決まり方")],
    "不用品の回収", "家具・家電・雑貨などの不用品回収。個人・法人対応。静岡県内中心。",
    "不用品の回収（家具・家電）｜静岡県島田市の株式会社AMT",
    hero_img=IMG["fuyouhin"],
)

# ------------------------------------------------------------
# 3. 解体前の残置物撤去
# ------------------------------------------------------------
add_service_page(
    "zanchibutsu", "残置物撤去",
    "解体前の残置物撤去｜静岡県島田市の株式会社AMT",
    "解体予定の建物に残った家財・設備・不用品を撤去します。当社の解体工事とあわせてのご依頼も可能。静岡県内中心・お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">解体やリフォームの前に必要な、建物内の残置物撤去に対応します。'
    '家財・設備・不用品をまとめて撤去し、次の工事へスムーズに進められるようにします。</p>'
    '<h2>残置物撤去とは</h2>'
    '<p>建物を解体する前には、室内に残った家具・家電・生活用品などの'
    '「残置物」を撤去しておく必要があります。'
    '残置物が多いと解体費用が上がることもあるため、事前の撤去が有効です。</p>'
    '<h2>解体とあわせて一社で対応できます</h2>'
    '<p>株式会社AMTは解体工事も行っています。'
    '残置物の撤去から建物の解体まで<strong>一貫してご相談いただける</strong>ため、'
    '窓口を分けずに進められます。解体については'
    '<a href="https://kaitai.amt-eco.com/" target="_blank" rel="noopener">解体工事のサイト</a>も'
    'あわせてご覧ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、<strong>残置物の量・種類・建物の状況・搬出条件</strong>などによって変わります。'
    '現地確認のうえ<strong>無料でお見積り</strong>します。'
    '買取・再資源化できるものがあれば、費用へ反映できる場合があります。</p>'
    '<p class="note">※費用は現地条件で大きく変わります。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("解体工事と一緒に頼めますか？",
      "はい、残置物の撤去から解体まで一貫して承れます。窓口が一つになるため、やり取りがスムーズです。"),
     ("家財が多くても撤去できますか？",
      "量が多い場合も対応します。現地で量と搬出経路を確認し、無料でお見積りします。")],
    [("/katazuke/", "家のお片付け", "室内の仕分け・搬出"),
     ("/fuyouhin/", "不用品の回収", "家具・家電の回収"),
     ("/souko/", "倉庫の片付け", "倉庫・工場の整理"),
     ("/ryoukin/", "料金・費用について", "費用の決まり方")],
    "解体前の残置物撤去", "解体予定の建物の家財・設備・不用品を撤去。解体工事と一貫対応。",
    "解体前の残置物撤去｜静岡県島田市の株式会社AMT",
    hero_img=IMG["zanchibutsu"],
)

# ------------------------------------------------------------
# 4. 倉庫の片付け
# ------------------------------------------------------------
add_service_page(
    "souko", "倉庫の片付け",
    "倉庫・工場の片付け｜静岡県島田市の株式会社AMT",
    "倉庫・工場・店舗に溜まった資材・在庫・什器の片付けに対応します。法人・事業者さまの整理もお任せください。静岡県内中心・お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">倉庫・工場・店舗などに溜まった資材・在庫・什器の片付けを承ります。'
    '事業者さまの整理・移転・閉鎖にともなう片付けにも対応します。</p>'
    '<h2>こんな片付けに対応します</h2>'
    '<ul><li>倉庫に溜まった古い資材・在庫の整理</li>'
    '<li>工場の設備・什器・パレットなどの撤去</li>'
    '<li>店舗・事務所の移転・閉店にともなう片付け</li>'
    '<li>金属・機械が混ざった品物の整理</li></ul>'
    '<h2>金属・機械の買取もあわせて</h2>'
    '<p>株式会社AMTは金属スクラップの買取も本業としています。'
    '倉庫に眠る金属や機械類の中に買取できるものがあれば、'
    '<strong>片付け費用へ反映できる場合があります</strong>。'
    '農機具については<a href="/nouki-kaitori/">農機具の買取り</a>もご覧ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、<strong>片付ける量・品物の種類・搬出条件・作業日数</strong>などによって変わります。'
    '現地確認のうえ<strong>無料でお見積り</strong>します。</p>'
    '<p class="note">※法人さまは、御見積書・請求書の発行にも対応します。お気軽にご相談ください。</p>'
    '</div></section>',
    [("法人でも依頼できますか？",
      "はい、法人・事業者さまのご依頼に対応します。御見積書・請求書の発行も承ります。"),
     ("金属や機械が混ざっていても大丈夫ですか？",
      "対応します。買取できる金属・機械があれば、査定のうえ片付け費用への反映をご提案できる場合があります。")],
    [("/fuyouhin/", "不用品の回収", "什器・備品の回収"),
     ("/nouki-kaitori/", "農機具の買取り", "農機具を買取"),
     ("/zanchibutsu/", "解体前の残置物撤去", "解体前の一括撤去"),
     ("/ryoukin/", "料金・費用について", "費用の決まり方")],
    "倉庫の片付け", "倉庫・工場・店舗の資材・在庫・什器の片付け。法人対応。金属買取も。",
    "倉庫・工場の片付け｜静岡県島田市の株式会社AMT",
    hero_img=IMG["souko"],
)

# ------------------------------------------------------------
# 5. 農機具の買取り（2026-10-10 強化：ハブ＋機種別ページ）
# ------------------------------------------------------------
# 対応メーカー（メーカーを問わず査定する、という当社サービスの範囲の説明。
# 提携・代理店等を示すものではないため、本文でもその旨がわかる書き方にする）
NOUKI_MAKERS = ["クボタ", "ヤンマー", "井関農機（ISEKI）", "三菱マヒンドラ農機",
                "ホンダ", "スター農機", "ニプロ（松山）", "サタケ", "オーレック", "共立・新ダイワ"]

# 査定で見るポイント（機種別ページでも共通で使う）
NOUKI_SATEI = [
    ("メーカー・型式", "需要の高いメーカー・型式ほど評価が上がります。型式は本体の銘板（プレート）に記載があります。"),
    ("年式", "新しいほど有利ですが、古くても部品需要のある機種は値がつくことがあります。"),
    ("稼働時間（アワーメーター）", "トラクター・コンバインなどは稼働時間が重要な判断材料になります。"),
    ("エンジンの状態", "始動するか、異音・白煙・オイル漏れがないか。自走できるかどうかも確認します。"),
    ("外装・サビ・破損", "外装のへこみやサビ、ガラス・ランプの割れ、タイヤの残り溝などを見ます。"),
    ("付属品・作業機の有無", "ロータリー・プラウ・ブーム等の作業機、取扱説明書、鍵、予備部品がそろうと評価が上がります。"),
    ("整備の記録", "点検・整備の記録や、交換した部品の履歴が残っていると状態を判断しやすくなります。"),
]
_satei_rows = "".join(
    "<tr><th>" + t + "</th><td>" + d + "</td></tr>" for t, d in NOUKI_SATEI
)
NOUKI_SATEI_TABLE = "<table><tbody>" + _satei_rows + "</tbody></table>"

# 機種別ページ（slug, ナビ用短縮名, 一覧での表示名, リード、本文の機種固有パート）
NOUKI_TYPES = [
    ("nouki-tractor", "トラクター", "トラクターの買取り",
     "クボタ・ヤンマー・井関などのトラクターを、メーカー・型式を問わず査定します。自走できない機械もご相談ください。"),
    ("nouki-combine", "コンバイン", "コンバイン・ハーベスタの買取り",
     "自脱型・普通型のコンバイン、バインダー、ハーベスタを査定します。稲刈り後の入れ替え時期のご相談も歓迎です。"),
    ("nouki-taue", "田植機", "田植機の買取り",
     "乗用・歩行型の田植機を査定します。シーズン前の入れ替えや、作付けをやめるタイミングでのご相談も承ります。"),
    ("nouki-kouunki", "耕運機・管理機", "耕運機・管理機の買取り",
     "歩行型の耕運機・管理機・ティラーを査定します。家庭菜園規模の小型機もまとめてご相談ください。"),
    ("nouki-kusakari", "草刈機・運搬車", "草刈機・刈払機・運搬車の買取り",
     "乗用草刈機・ハンマーナイフモア・刈払機・運搬車（クローラ運搬車）などを査定します。"),
]
_type_links = "".join(
    '<li><a href="/' + s + '/"><strong>' + n + '</strong></a>：' + lead + "</li>"
    for s, short, n, lead in NOUKI_TYPES
)

# ------------------------------------------------------------
# 5-0. 農機具買取ハブ
# ------------------------------------------------------------
NOUKI_FAQ = [
    ("動かない農機具・故障している農機具も買取できますか？",
     "ご相談ください。エンジンがかからない機械や自走できない機械でも、部品としての需要や、"
     "鉄・アルミなどの金属としての価値で評価できる場合があります。"
     "当社は古物商許可（" + KOBUTSU_AUTH + "・" + KOBUTSU_CATEGORY + "）のもとで中古機械の買取を行っており、"
     "金属スクラップの買取も本業として手がけています。"),
    ("出張での査定はできますか？費用はかかりますか？",
     "静岡県内を中心に、現地にうかがって査定します。査定・出張費は無料です。"
     "農地や倉庫に置いたままの状態でも拝見できます。"),
    ("査定はどこを見て決まりますか？",
     "メーカー・型式・年式・稼働時間・エンジンの状態・外装のサビや破損・作業機や付属品の有無、"
     "そして中古市場の相場をあわせて判断します。現物を確認したうえで金額をご提示します。"),
    ("自走できない農機具はどう運び出すのですか？",
     "自走できない機械も、当社が搬出の方法から手配します。"
     "ユニック車やトラックへの積み込み、倉庫からの引き出しもお任せください。"
     "搬出の都合でご相談が必要な場合は、査定のときにご説明します。"),
    ("農機具の買取に必要なものはありますか？",
     "身分を確認できるもの（運転免許証など）をご用意ください。"
     "古物営業法により、買取のときに本人確認が必要です。"
     "取扱説明書・鍵・保証書・整備の記録が残っていれば、査定の参考になります。"),
    ("倉庫や納屋の片付けとまとめて頼めますか？",
     "はい。農機具の買取と、倉庫・納屋の片付け、不用品の回収をまとめて承れます。"
     "買取できた金額は片付け費用から差し引いてご提示しますので、"
     "片付け費用の負担を軽くできる場合があります。"),
    ("どんなメーカーに対応していますか？",
     "メーカーを問わず査定します。クボタ・ヤンマー・井関農機・三菱マヒンドラ農機・ホンダ・"
     "スター農機・ニプロなど、国内メーカーの機械を幅広く拝見しています。"),
    ("まとめて何台もありますが対応できますか？",
     "対応できます。離農・世代交代・農地の整理などで複数台をまとめて手放されるご相談も承ります。"
     "台数が多い場合は、搬出の日程を分けてご提案することもあります。"),
]

add_service_page(
    "nouki-kaitori", "農機具買取",
    "農機具の買取り｜静岡県島田市の株式会社AMT",
    "トラクター・コンバイン・田植機・耕運機などの農機具を、メーカーを問わず査定します。"
    "動かない機械・自走できない機械もご相談ください。静岡県内中心・出張査定無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">使わなくなった農機具の買取に対応します。'
    '離農や世代交代、農地の整理、機械の入れ替えなどで不要になった機械をご相談ください。'
    '当社は<strong>' + KOBUTSU_LABEL + '</strong>のもとで中古機械の買取を行い、'
    '<strong>金属スクラップの買取</strong>も本業として手がけています。'
    'そのため、<strong>値のつく機械は買取、値がつきにくい機械も金属として評価</strong>という形で、'
    '「どこも引き取ってくれなかった機械」もまとめてご相談いただけます。</p>'

    '<h2>買取・ご相談の対象になる農機具</h2>'
    '<ul>' + _type_links + '</ul>'
    '<p>上の機種以外でも、<strong>農業に使う機械であればまずご相談ください</strong>。'
    '乾燥機・籾摺機・精米機・選別機、噴霧器・動力噴霧機、ハウスの暖房機、'
    'ロータリーやプラウなどの作業機（アタッチメント）単体、'
    '農機具にともなう金属・部品類も対象です。</p>'

    '<h2>対応メーカー</h2>'
    '<p><strong>メーカーを問わず査定します。</strong>'
    '国内メーカーの機械を幅広く拝見しています（例：'
    + "・".join(NOUKI_MAKERS) + ' ほか）。</p>'
    '<p class="note">※上記は査定の対象となるメーカーの例です。'
    '各メーカーとの提携・代理店関係を示すものではありません。</p>'

    '<h2>査定で見るポイント</h2>'
    '<p>買取の可否と金額は、次の点と中古市場の相場をあわせて判断します。'
    '現物を確認したうえでご提示します。</p>'
    + NOUKI_SATEI_TABLE +
    '<p>型式がわからないときは、<strong>本体の銘板（プレート）の写真</strong>を'
    '<a href="/contact/">お問い合わせフォーム</a>からお送りいただくと、'
    'おおよその見通しをお伝えしやすくなります。'
    '高く売るための準備は<a href="/nouki-kaitori-kotsu/">使わない農機具を高く売るコツ</a>にまとめています。</p>'

    '<h2>動かない農機具・自走できない農機具も相談できます</h2>'
    '<p>エンジンがかからない、自走できない、長年倉庫に眠っている——'
    'そうした機械も、<strong>部品としての需要</strong>や'
    '<strong>鉄・アルミなどの金属としての価値</strong>で評価できる場合があります。</p>'
    '<p>搬出も当社が手配します。倉庫や納屋から引き出せない機械、'
    'ぬかるんだ農地に置いたままの機械も、積み込みの方法からご相談ください。</p>'

    '<h2>買取のときに必要なもの</h2>'
    '<ul>'
    '<li><strong>身分を確認できるもの</strong>（運転免許証など）'
    '※古物営業法により、買取のときに本人確認が必要です</li>'
    '<li>取扱説明書・鍵・保証書（あれば。査定の参考になります）</li>'
    '<li>点検・整備の記録（あれば）</li>'
    '</ul>'
    '<p class="note">※すべての農機具を買取できるとは限りません。'
    '買取が難しい場合も、回収・処分としてご相談いただけます。</p>'

    '<h2>倉庫・納屋の片付けとまとめてご相談いただけます</h2>'
    '<p>農機具だけでなく、倉庫や納屋ごとの片付けもあわせて承ります。'
    '<strong>買取できた金額は片付け費用から差し引いてご提示</strong>しますので、'
    '片付けの負担を軽くできる場合があります。</p>'
    '<p><a href="/souko/">倉庫の片付け</a>・'
    '<a href="/fuyouhin/">不用品の回収</a>・'
    '<a href="/akiya/">空き家・実家の片付け</a>とまとめてご相談ください。'
    '料金の考え方は<a href="/ryoukin/">料金・費用について</a>をご覧ください'
    '（片付け・不用品回収は' + PRICE_LABEL + '）。</p>'

    '<h2>対応エリア</h2>'
    '<p>静岡県内を中心に対応します。'
    '<a href="/nouki-kaitori-shizuoka/">静岡県の農機具買取（市町別の対応）</a>もご覧ください。</p>'
    '</div></section>',
    NOUKI_FAQ,
    [("/nouki-kaitori-shizuoka/", "静岡県の農機具買取", "市町別の対応"),
     ("/nouki-kaitori-kotsu/", "農機具を高く売るコツ", "準備で査定が変わります"),
     ("/souko/", "倉庫の片付け", "納屋・倉庫の整理"),
     ("/ryoukin/", "料金・費用について", PRICE_LABEL)],
    "農機具の買取り", "トラクター・コンバイン・田植機・耕運機などの農機具買取。メーカー不問、動かない機械も相談可。静岡県内中心・出張査定無料。",
    "農機具の買取り｜静岡県島田市の株式会社AMT",
    hero_img=IMG["nouki"],
)

# ------------------------------------------------------------
# 5-1〜5-5. 機種別ページ
# ------------------------------------------------------------
NOUKI_DETAIL = {
    "nouki-tractor": {
        "h1": "トラクターの買取り｜静岡県島田市の株式会社AMT",
        "answer": "トラクターは<strong>メーカー・型式・年式・稼働時間（アワーメーター）・エンジンの状態</strong>で"
                  "評価が決まります。<strong>メーカーは問いません</strong>。"
                  "エンジンがかからない機械・自走できない機械も、部品や金属としての価値で評価できる場合があります。"
                  "出張査定は無料です。",
        "sections": [
            ("買取の対象になるトラクター",
             '<ul>'
             '<li>乗用トラクター（装輪式・クローラ式）</li>'
             '<li>小型・中型・大型を問わず対応（家庭菜園規模の小型機から、ほ場用の大型機まで）</li>'
             '<li>キャビン付き・ロプス（安全フレーム）付きのいずれも対応</li>'
             '<li>ロータリー・プラウ・ハロー・畦塗機などの<strong>作業機（アタッチメント）単体</strong></li>'
             '<li>フロントローダー付きの機械、作業機をまとめてのご相談</li>'
             '</ul>'
             '<p>メーカーはクボタ・ヤンマー・井関農機・三菱マヒンドラ農機ほか、問いません。</p>'),
            ("トラクターの査定で特に見るところ",
             '<p>トラクターは、次の点がとくに金額に影響します。</p>'
             '<ul>'
             '<li><strong>アワーメーター（稼働時間）</strong>：走行時間が短いほど有利です。'
             'メーターが動かなくなっている場合も、その旨をお伝えください。</li>'
             '<li><strong>エンジンの始動性と異音・白煙</strong>：かかるか、かかってからの音や煙の出方を確認します。</li>'
             '<li><strong>油圧の動作</strong>：三点リンクの上下、作業機の昇降がスムーズかどうか。</li>'
             '<li><strong>タイヤの残り溝</strong>：前後輪の摩耗、ひび割れ。</li>'
             '<li><strong>作業機がそろっているか</strong>：ロータリー等が付属すると評価が上がりやすくなります。</li>'
             '</ul>'),
        ],
        "faq": [
            ("古いトラクターでも買取できますか？",
             "年式が古くても、部品需要のある型式や、整備して使える状態の機械は値がつくことがあります。"
             "値がつきにくい場合も、鉄・アルミなどの金属として評価できる場合がありますのでご相談ください。"),
            ("エンジンがかからないトラクターはどうなりますか？",
             "ご相談ください。部品としての需要や金属としての価値で評価します。"
             "自走できない機械の搬出・積み込みも当社で手配します。"),
            ("ロータリーなどの作業機だけでも買取できますか？",
             "はい、作業機（アタッチメント）単体でもご相談いただけます。"
             "ロータリー・プラウ・ハロー・畦塗機などをお知らせください。"),
        ],
    },
    "nouki-combine": {
        "h1": "コンバイン・ハーベスタの買取り｜静岡県島田市の株式会社AMT",
        "answer": "コンバインは<strong>条数・稼働時間・刈刃や脱穀部の状態</strong>が評価の中心です。"
                  "自脱型・普通型のいずれも、<strong>メーカーを問わず</strong>査定します。"
                  "稲刈り後の入れ替え時期のご相談も歓迎です。出張査定は無料です。",
        "sections": [
            ("買取の対象になる機械",
             '<ul>'
             '<li>自脱型コンバイン（2条・3条・4条・5条以上）</li>'
             '<li>普通型コンバイン（汎用コンバイン）</li>'
             '<li>バインダー（刈取結束機）</li>'
             '<li>ハーベスタ、自走式の脱穀機</li>'
             '<li>乾燥機・籾摺機・選別機・精米機など、収穫後の調製機械</li>'
             '</ul>'),
            ("コンバインの査定で特に見るところ",
             '<ul>'
             '<li><strong>条数</strong>：需要の多い条数ほど評価が安定します。</li>'
             '<li><strong>稼働時間</strong>：使用時間が短いほど有利です。</li>'
             '<li><strong>刈刃・こぎ胴・脱穀部の摩耗</strong>：消耗部品の状態を確認します。</li>'
             '<li><strong>クローラ（ゴムキャタ）の残り</strong>：ひび割れ・摩耗の程度。</li>'
             '<li><strong>詰まり・修理の履歴</strong>：整備の記録があれば査定の参考になります。</li>'
             '</ul>'
             '<p class="note">※収穫期の直前・直後は中古の需要が動きます。'
             '入れ替えをお考えの場合は、時期も含めてご相談ください。</p>'),
        ],
        "faq": [
            ("稲刈りが終わったあとに引き取ってもらえますか？",
             "はい。収穫が終わってからのご相談も承ります。"
             "次のシーズンまで置いたままにするより、状態が落ちる前に査定を受けられることをおすすめします。"),
            ("乾燥機や籾摺機も買取できますか？",
             "ご相談ください。収穫後の調製機械も査定の対象です。設置されたままの機械も、取り外しから手配します。"),
            ("動かないコンバインはどうなりますか？",
             "部品としての需要や、金属としての価値で評価できる場合があります。"
             "自走できない機械の搬出も当社で手配しますのでご相談ください。"),
        ],
    },
    "nouki-taue": {
        "h1": "田植機の買取り｜静岡県島田市の株式会社AMT",
        "answer": "田植機は<strong>条数・乗用か歩行型か・稼働時間・植付部の状態</strong>で評価が決まります。"
                  "<strong>メーカーは問いません</strong>。シーズン前の入れ替えや、作付けをやめるタイミングでの"
                  "ご相談も承ります。出張査定は無料です。",
        "sections": [
            ("買取の対象になる田植機",
             '<ul>'
             '<li>乗用田植機（4条・5条・6条・8条など）</li>'
             '<li>歩行型田植機（2条・4条など）</li>'
             '<li>施肥機・除草剤散布装置つきの機械</li>'
             '<li>育苗箱・苗運搬車などの関連機材</li>'
             '</ul>'),
            ("田植機の査定で特に見るところ",
             '<ul>'
             '<li><strong>条数</strong>：ほ場の規模に合う条数ほど需要があります。</li>'
             '<li><strong>植付部（爪・ロータリーケース）の状態</strong>：摩耗や曲がりを確認します。</li>'
             '<li><strong>油圧・水平制御の動作</strong>：センサー類が正常に働くかどうか。</li>'
             '<li><strong>保管状態</strong>：屋内保管で泥を落としてある機械は評価が上がりやすくなります。</li>'
             '</ul>'
             '<p>植付が終わったあとに<strong>泥を洗い落として乾かしてから保管</strong>しておくと、'
             'サビの進行を抑えられ、査定にも有利です。</p>'),
        ],
        "faq": [
            ("田植機を売るのに良い時期はありますか？",
             "一般に、春の作付け前に中古の需要が高まります。ただし保管中に状態が落ちることもあるため、"
             "手放すことが決まっているなら早めに査定を受けられることをおすすめします。"),
            ("歩行型の小さな田植機でも対応できますか？",
             "はい、歩行型の田植機もご相談いただけます。"),
            ("育苗箱や苗運搬車もまとめて引き取れますか？",
             "はい。関連する機材や、倉庫に残った資材もまとめてご相談ください。"),
        ],
    },
    "nouki-kouunki": {
        "h1": "耕運機・管理機の買取り｜静岡県島田市の株式会社AMT",
        "answer": "耕運機・管理機は<strong>馬力・エンジンの始動性・爪の摩耗・付属のアタッチメント</strong>で"
                  "評価が決まります。<strong>家庭菜園規模の小型機から対応</strong>し、メーカーは問いません。"
                  "複数台まとめてのご相談も歓迎です。出張査定は無料です。",
        "sections": [
            ("買取の対象になる機械",
             '<ul>'
             '<li>歩行型耕運機（ロータリー式・車軸式）</li>'
             '<li>管理機（うね立て・培土・中耕用）</li>'
             '<li>ティラー・ミニ耕運機（家庭菜園向けの小型機も対応）</li>'
             '<li>うね立て器・培土器・ハロー等のアタッチメント</li>'
             '<li>発動機・エンジンポンプ・動力噴霧器などの小型農業機械</li>'
             '</ul>'),
            ("耕運機・管理機の査定で特に見るところ",
             '<ul>'
             '<li><strong>エンジンがかかるか</strong>：始動性がもっとも大きな要素です。'
             '燃料を抜かずに長期保管していた機械は、キャブレターが詰まっていることがあります。</li>'
             '<li><strong>馬力・排気量</strong>：用途に合う出力ほど需要があります。</li>'
             '<li><strong>爪の摩耗</strong>：ロータリーの爪の減り具合を確認します。</li>'
             '<li><strong>アタッチメントの有無</strong>：付属品がそろうと評価が上がります。</li>'
             '</ul>'
             '<p class="note">※小型機は1台だけだと搬出の手間に対して金額が小さくなりがちです。'
             '倉庫や納屋の片付け・<a href="/fuyouhin/">不用品の回収</a>とまとめてご相談いただくと、'
             '一度の作業で済ませられます。</p>'),
        ],
        "faq": [
            ("何年も動かしていない耕運機でも見てもらえますか？",
             "ご相談ください。長期保管でエンジンがかからなくなっている機械も、"
             "部品や金属としての価値で評価できる場合があります。"),
            ("小型の耕運機1台だけでも来てもらえますか？",
             "ご相談ください。1台のみの場合は、ほかの不用品の片付けとあわせてのご依頼だと"
             "お引き受けしやすくなります。"),
            ("家庭菜園用のミニ耕運機も対象ですか？",
             "はい、小型機も査定の対象です。"),
        ],
    },
    "nouki-kusakari": {
        "h1": "草刈機・刈払機・運搬車の買取り｜静岡県島田市の株式会社AMT",
        "answer": "乗用草刈機・ハンマーナイフモア・刈払機・クローラ運搬車などを査定します。"
                  "<strong>メーカーは問いません</strong>。小型機は<strong>まとめてのご相談</strong>だと"
                  "お引き受けしやすくなります。出張査定は無料です。",
        "sections": [
            ("買取の対象になる機械",
             '<ul>'
             '<li>乗用草刈機（モアー）、自走式草刈機</li>'
             '<li>ハンマーナイフモア、畦畔（けいはん）草刈機</li>'
             '<li>刈払機・ブロワ・ヘッジトリマなどの小型エンジン機械</li>'
             '<li>クローラ運搬車・一輪車型の動力運搬車・手押し式の動力運搬機</li>'
             '<li>チェーンソー、高圧洗浄機、発電機、溶接機などの機械工具類</li>'
             '</ul>'),
            ("査定で特に見るところ",
             '<ul>'
             '<li><strong>エンジンがかかるか</strong>：2サイクル機は燃料の劣化で始動しなくなることがあります。</li>'
             '<li><strong>刃・ブレードの状態</strong>：摩耗・欠け・曲がりを確認します。</li>'
             '<li><strong>クローラ（ゴムキャタ）の残り</strong>：運搬車は足回りの状態が重要です。</li>'
             '<li><strong>台数</strong>：小型機は複数台まとめてのほうが評価しやすくなります。</li>'
             '</ul>'
             '<p>工具・機械工具類は<a href="/hinmoku/">回収・買取できる品目一覧</a>にもまとめています。</p>'),
        ],
        "faq": [
            ("刈払機が何台かありますが、まとめて見てもらえますか？",
             "はい。小型機は台数がまとまっているほうが評価しやすくなります。まとめてご相談ください。"),
            ("エンジンがかからない刈払機も対象ですか？",
             "ご相談ください。部品や金属としての価値で評価できる場合があります。"),
            ("農機具以外の工具や発電機も見てもらえますか？",
             "はい。当社の古物商許可は機械工具類を取扱品目としており、"
             "工具・発電機・溶接機などもご相談いただけます。"),
        ],
    },
}

for _slug, _short, _name, _lead in NOUKI_TYPES:
    _d = NOUKI_DETAIL[_slug]
    _body = (
        '<section class="k-section" style="padding-bottom:0;"><div class="prose">'
        '<div class="answer"><span class="answer-h">要点</span><p>' + _d["answer"] + '</p></div>'
        '</div></section>'
        '<section class="k-section"><div class="prose">'
        '<p class="lead">' + _lead + '</p>'
    )
    for _h, _html in _d["sections"]:
        _body += "<h2>" + _h + "</h2>" + _html
    _body += (
        '<h2>査定から買取までの流れ</h2>'
        '<ol>'
        '<li><strong>ご相談</strong>（<a href="tel:' + TEL + '">' + TEL + '</a> ／ '
        '<a href="/contact/">お問い合わせフォーム</a>）。'
        '本体の銘板（プレート）の写真をお送りいただくと見通しをお伝えしやすくなります。</li>'
        '<li><strong>出張査定</strong>（無料）。現物を拝見して状態を確認します。</li>'
        '<li><strong>金額のご提示</strong>。見ていただいた根拠もあわせてご説明します。</li>'
        '<li><strong>ご契約・搬出</strong>。本人確認のうえ、搬出・積み込みまで当社で対応します。</li>'
        '</ol>'
        '<p class="note">※古物営業法により、買取のときは身分を確認できるもの'
        '（運転免許証など）のご提示が必要です。</p>'
        '<h2>片付けとまとめてご相談いただけます</h2>'
        '<p>' + _short + 'の買取だけでなく、倉庫・納屋の片付けや不用品の回収も'
        'あわせて承ります。買取できた金額は片付け費用から差し引いてご提示します'
        '（片付け・不用品回収は' + PRICE_LABEL + '）。</p>'
        '<p><a href="/nouki-kaitori/">農機具の買取り（トップ）</a>に、'
        '対応メーカー・査定のポイント・必要なものをまとめています。</p>'
        '</div></section>'
    )
    _rel = [("/nouki-kaitori/", "農機具の買取り", "対応機種・査定のポイント"),
            ("/nouki-kaitori-shizuoka/", "静岡県の農機具買取", "市町別の対応"),
            ("/nouki-kaitori-kotsu/", "農機具を高く売るコツ", "準備で査定が変わります"),
            ("/souko/", "倉庫の片付け", "納屋・倉庫の整理")]
    add_service_page(
        _slug, _short, _d["h1"], _lead, _body, _d["faq"], _rel,
        _name, _lead,
        _d["h1"],
        hero_img=IMG["nouki"],
    )

# ------------------------------------------------------------
# 5-6. 静岡県の農機具買取（エリア）
# ------------------------------------------------------------
_nouki_city_rows = "".join(
    '<li>' + c + '</li>' for c in AREA_CITIES
)
NOUKI_AREA_FAQ = [
    ("静岡県内ならどこでも出張査定に来てもらえますか？",
     "島田市（金谷）の拠点から、静岡県内を中心に出張査定にうかがいます。"
     "査定・出張費は無料です。県境に近い地域など、距離がある場合は日程をご相談させてください。"),
    ("農地や山あいの倉庫に置いたままでも見てもらえますか？",
     "はい。農地・倉庫・納屋に置いたままの状態で拝見します。"
     "自走できない機械の搬出・積み込みも当社で手配します。"),
    ("島田市以外でも片付けとまとめて頼めますか？",
     "はい。静岡県内中心に、農機具の買取と倉庫・納屋の片付けをまとめて承ります。"
     "買取できた金額は片付け費用から差し引いてご提示します。"),
]
add_service_page(
    "nouki-kaitori-shizuoka", "静岡県の農機具買取",
    "静岡県の農機具買取｜出張査定無料｜株式会社AMT（島田市）",
    "静岡県島田市（金谷）を拠点に、県内各市町へ出張査定にうかがいます。"
    "トラクター・コンバイン・田植機・耕運機など、メーカーを問わず査定。出張査定無料。",
    '<section class="k-section" style="padding-bottom:0;"><div class="prose">'
    '<div class="answer"><span class="answer-h">要点</span>'
    '<p>静岡県<strong>島田市金谷</strong>の拠点から、県内各市町へ<strong>出張査定</strong>にうかがいます。'
    '査定・出張費は<strong>無料</strong>です。農地や倉庫に置いたままの機械、'
    '自走できない機械も、<strong>搬出から当社で手配</strong>します。</p></div>'
    '</div></section>'
    '<section class="k-section"><div class="prose">'
    '<h2>対応エリア（静岡県内）</h2>'
    '<p>当社は静岡県島田市金谷東に拠点があります。'
    '国道473号・東名高速（相良牧之原IC）・新東名（島田金谷IC）に近く、'
    '県中部の農業地域へうかがいやすい場所です。'
    '次の市町を中心に、静岡県内へ出張査定にうかがいます。</p>'
    '<ul class="area-list">' + _nouki_city_rows + '</ul>'
    '<p class="note">※上記以外の静岡県内の市町もご相談ください。'
    '距離がある場合は日程をあわせてご相談させていただきます。</p>'
    '<h2>静岡県の農機具・当社が拝見する機械</h2>'
    '<p>静岡県の中部は茶園と水田が混在し、'
    '牧之原・島田・菊川・掛川のあたりでは<strong>茶園向けの乗用型機械・管理機・運搬車</strong>、'
    '大井川沿いの水田地帯では<strong>トラクター・田植機・コンバイン</strong>のご相談が多くなります。</p>'
    '<ul>' + _type_links + '</ul>'
    '<p>乾燥機・籾摺機などの調製機械、作業機（アタッチメント）単体、'
    '農機具にともなう金属・部品類も対象です。'
    '対応メーカー・査定のポイントは'
    '<a href="/nouki-kaitori/">農機具の買取り</a>にまとめています。</p>'
    '<h2>島田市にお住まいの方へ</h2>'
    '<p>拠点のある島田市では、農機具の買取と'
    '<a href="/katazuke-shimada/">島田市の片付け・不用品回収</a>をまとめて承れます。'
    '市の粗大ごみ制度との使い分けもあわせてご案内します。</p>'
    '<h2>片付けとあわせてのご相談</h2>'
    '<p>離農・世代交代で<strong>倉庫や納屋ごと片付けたい</strong>というご相談も承ります。'
    '買取できた金額は片付け費用から差し引いてご提示します'
    '（片付け・不用品回収は' + PRICE_LABEL + '）。'
    '<a href="/souko/">倉庫の片付け</a>・'
    '<a href="/akiya/">空き家・実家の片付け</a>もご覧ください。</p>'
    '</div></section>',
    NOUKI_AREA_FAQ,
    [("/nouki-kaitori/", "農機具の買取り", "対応機種・査定のポイント"),
     ("/katazuke-shimada/", "島田市の片付け・不用品回収", "拠点のある島田市"),
     ("/area/", "対応エリア", "片付け・回収の対応エリア"),
     ("/souko/", "倉庫の片付け", "納屋・倉庫の整理")],
    "静岡県の農機具買取", "静岡県内の出張農機具買取。島田市金谷の拠点から県内各市町へ。出張査定無料。",
    "静岡県の農機具買取｜出張査定無料｜株式会社AMT（島田市）",
    hero_img=IMG["nouki"],
)


# ------------------------------------------------------------
# 6. 料金・費用について（2026-10-10 1㎥あたりの単価を公開）
# ------------------------------------------------------------
RYOUKIN_FAQ = [
    ("片付け・不用品回収の料金はいくらですか？",
     "荷物の体積（㎥）を基準に、" + PRICE_LABEL + "でご案内しています。"
     "正確な金額は、間取り・階数・搬出経路・品目などを現地で確認したうえで無料でお見積りします。"),
    ("1㎥はどのくらいの量ですか？",
     "1㎥は、たて・よこ・高さがそれぞれ1mの立方体ぶんの体積です。"
     "押入れの下段がおよそ1㎥、一般的な2ドア冷蔵庫1台でおよそ0.3〜0.5㎥が目安です。"),
    ("見積りは無料ですか？", "はい、ご相談・現地確認・お見積りはすべて無料です。出張費もいただきません。"),
    ("買取できるものがあると安くなりますか？",
     "はい。古物商許可（" + KOBUTSU_AUTH + "）のもとで買取できる品物があれば、"
     "その査定額を片付け費用から差し引いてご提示します。農機具・機械・金属などは買取の対象になりやすい品物です。"),
    ("見積りより高くなることはありませんか？",
     "お見積りでご説明した内容から作業範囲が変わる場合は、作業を進める前に必ずご相談し、"
     "ご了解をいただいてから対応します。無断での追加請求はいたしません。"),
    ("追加でかかる費用はありますか？",
     "家電リサイクル法の対象品（エアコン・テレビ・冷蔵庫・洗濯機など）は、法律で定められたリサイクル料金が別途必要です。"
     "そのほか、クレーン等の特殊な機材が必要な重量物などの個別条件は、お見積りの時点でご説明します。"),
    ("キャンセル料はかかりますか？",
     "お見積り後のキャンセルは無料です。作業日の直前のご連絡は、手配の都合をご相談させてください。"),
    ("支払い方法は何がありますか？", "現金または銀行振込でお受けしています。法人のお客様は請求書払いも可能です。"),
]

c, _ = assemble(
    "ryoukin", "料金・費用",
    "片付け・不用品回収の料金｜静岡県島田市｜株式会社AMT",
    "料金は荷物の体積（㎥）が基準。" + PRICE_LABEL + "でご案内しています。正確な金額は現地確認のうえ無料でお見積りします。",
    '<section class="k-section" style="padding-bottom:0;"><div class="prose">'
    '<div class="answer"><span class="answer-h">料金の結論</span>'
    '<p>片付け・不用品回収の料金は、<strong>荷物の体積（㎥）を基準に算出</strong>します。'
    '目安は<strong>' + PRICE_LABEL + '</strong>です。'
    'この金額に<strong>搬出・運搬・適正処理の委託費用まで含みます</strong>。'
    '買取できる品物があれば、その査定額を差し引いてご提示します。'
    '出張費・お見積りは<strong>無料</strong>です。</p></div>'
    '</div></section>'

    # ---- 料金の基準（㎥単価） ----
    '<section class="k-section"><div class="prose">'
    '<h2>料金の基準は「体積（㎥）」です</h2>'
    '<p>片付け・不用品回収は、トラックに積み込む荷物の量＝体積で手間が決まります。'
    'そのため当社では、<strong>荷物の体積（立方メートル／㎥）を基準</strong>にお見積りします。</p>'
    '<div class="kz-price"><p class="kz-price-lbl">片付け・不用品回収</p>'
    '<p class="kz-price-val"><span class="kz-price-num">' + "{:,}".format(PRICE_PER_M3) + '</span>'
    '<span class="kz-price-yen">円</span>'
    '<span class="kz-price-unit">／1㎥' + PRICE_TAX + ' <b>から</b></span></p>'
    '<p class="kz-price-note">搬出・運搬・適正処理の委託費用を含みます／出張費・お見積り無料</p></div>'
    '<h3>1㎥はどのくらいの量？</h3>'
    '<p>1㎥は、<strong>たて1m×よこ1m×高さ1m</strong>の立方体ぶんの体積です。'
    'イメージしづらい単位なので、身近なものに置き換えると次のくらいです。</p>'
    '<table><tbody>'
    '<tr><th>押入れの下段（1間ぶん）</th><td>およそ1㎥</td></tr>'
    '<tr><th>2ドア冷蔵庫　1台</th><td>およそ0.3〜0.5㎥</td></tr>'
    '<tr><th>洗濯機　1台</th><td>およそ0.3㎥</td></tr>'
    '<tr><th>3人掛けソファ　1台</th><td>およそ1〜1.5㎥</td></tr>'
    '<tr><th>シングルベッド（フレーム＋マットレス）</th><td>およそ1〜1.5㎥</td></tr>'
    '<tr><th>段ボール（みかん箱サイズ）　約8箱</th><td>およそ1㎥</td></tr>'
    '</tbody></table>'
    '<p class="note">※上記は体積のイメージをつかんでいただくための一般的な目安で、'
    '品物の形状や積み方によって変わります。実際の㎥数は現地で確認して算出します。</p>'
    '</div></section>'

    # ---- 料金に含まれるもの／別途になるもの ----
    '<section class="k-section"><div class="prose">'
    '<h2>料金に含まれるもの・別途になるもの</h2>'
    '<table><tbody>'
    '<tr><th>含まれるもの</th><td>室内からの搬出作業／人件費／トラックでの運搬／'
    '処分が必要な品物の<strong>提携許可業者への適正処理委託費用</strong>／簡単な掃き掃除</td></tr>'
    '<tr><th>無料のもの</th><td>ご相談・現地確認・お見積り・出張費</td></tr>'
    '<tr><th>別途になるもの</th><td><strong>家電リサイクル法の対象品</strong>'
    '（エアコン・テレビ・冷蔵庫・冷凍庫・洗濯機・衣類乾燥機）の法定リサイクル料金／'
    'クレーン等の特殊機材が必要な重量物／ハウスクリーニング等の専門清掃</td></tr>'
    '<tr><th>お引きするもの</th><td><strong>買取できる品物の査定額</strong>'
    '（農機具・機械・金属・まだ使える家具家電など）</td></tr>'
    '</tbody></table>'
    '<p>家電リサイクル法については'
    '<a href="/kaden-shobun/">冷蔵庫・洗濯機・テレビの正しい処分方法</a>でくわしく解説しています。</p>'
    '</div></section>'

    # ---- 買取で費用を下げる ----
    '<section class="k-section"><div class="prose">'
    '<h2>買取で費用が下がることがあります</h2>'
    '<p>当社は<strong>' + KOBUTSU_LABEL + '</strong>を持ち、金属スクラップの買取や'
    '<a href="/nouki-kaitori/">農機具の買取り</a>も本業として手がけています。'
    'そのため、片付けのなかに<strong>買取できる品物</strong>があれば、'
    'その査定額を片付け費用から<strong>差し引いてご提示</strong>できます。</p>'
    '<h3>買取の対象になりやすい品物</h3>'
    '<ul>'
    '<li><a href="/nouki-kaitori/">農機具</a>（トラクター・耕運機・田植機・コンバイン・管理機など。動かない機械もご相談ください）</li>'
    '<li>鉄・アルミ・銅・ステンレスなどの金属、電線、モーター類</li>'
    '<li>工具・建設機械・発電機・溶接機などの機械工具類</li>'
    '<li>年式の新しい家電、状態のよい家具、業務用の厨房機器・什器</li>'
    '</ul>'
    '<p>買取・回収できる品物は<a href="/hinmoku/">回収・買取できる品目一覧</a>にまとめています。</p>'
    '</div></section>'

    # ---- 料金を左右する条件 ----
    '<section class="k-section"><div class="prose">'
    '<h2>' + PRICE_LABEL + 'の「から」が動く条件</h2>'
    '<p>同じ㎥数でも、現場の条件によって作業の手間が変わります。'
    'お見積りでは次の点を確認したうえで金額を確定します。</p>'
    '<table><tbody>'
    '<tr><th>荷物の量（㎥）</th><td>もっとも大きな要素です。量が多いほど人数・台数・日数が増えます。</td></tr>'
    '<tr><th>品物の種類</th><td>家電リサイクル法の対象品や、別途処理が必要なものは扱いが変わります。</td></tr>'
    '<tr><th>間取り・階数</th><td>部屋数、2階以上からの搬出、エレベーターの有無で手間が変わります。</td></tr>'
    '<tr><th>搬出経路</th><td>前面道路の幅、駐車スペース、トラックの横付けができるかどうかが影響します。</td></tr>'
    '<tr><th>仕分けの有無</th><td>残すもの・処分するものの仕分けからお任せの場合は作業時間が増えます。</td></tr>'
    '<tr><th>作業日・期限</th><td>お急ぎの日程指定や、休日・夜間のご希望は手配の都合をご相談させてください。</td></tr>'
    '</tbody></table>'
    '</div></section>'

    # ---- 費用を抑えるコツ ----
    '<section class="k-section"><div class="prose">'
    '<h2>費用を抑える5つのコツ</h2>'
    '<ol>'
    '<li><strong>残すもの・処分するものを先に分けておく</strong>。仕分けの時間が減り、㎥数も正確に出せます。</li>'
    '<li><strong>買取できそうな品物をまとめておく</strong>。農機具・機械・金属があれば査定で費用に反映できます。</li>'
    '<li><strong>片付け・回収・撤去をまとめて依頼する</strong>。搬出が1回で済み、運搬の回数を減らせます。</li>'
    '<li><strong>自治体の粗大ごみも併用する</strong>。品数が少なく日程に余裕があるなら、'
    '<a href="/katazuke-shimada/">島田市の粗大ごみ</a>のほうが安く済む場合があります。</li>'
    '<li><strong>繁忙期を避ける</strong>。年度末・お盆・年末は依頼が集中します。日程に余裕があるとご相談しやすくなります。</li>'
    '</ol>'
    '<p>自治体の制度との使い分けは'
    '<a href="/fuyouhin-tebanashi/">不用品を賢く手放す方法</a>と'
    '<a href="/fuyouhin-hiyou/">不用品回収の費用はどう決まる？</a>でもくわしく解説しています。</p>'
    '</div></section>'

    # ---- 見積りの流れ ----
    '<section class="k-section"><div class="prose">'
    '<h2>お見積りまでの流れ</h2>'
    '<ol>'
    '<li><strong>お電話またはフォームでご相談</strong>（<a href="tel:' + TEL + '">' + TEL + '</a> ／ '
    '<a href="/contact/">お問い合わせフォーム</a>）</li>'
    '<li><strong>現地確認</strong>（無料・出張費なし）。量と現場の条件を拝見します。</li>'
    '<li><strong>お見積りのご提示</strong>（無料）。㎥数の内訳と、買取で差し引ける金額をご説明します。</li>'
    '<li><strong>ご検討</strong>。その場で決めていただく必要はありません。</li>'
    '</ol>'
    '<p>くわしくは<a href="/flow/">ご利用の流れ</a>をご覧ください。</p>'
    '<p class="note">※' + PRICE_LABEL + 'は目安です。消費税の取り扱いを含む正確な金額は、'
    '現地確認のうえ無料のお見積りでご提示します。</p>'
    '</div></section>',
    RYOUKIN_FAQ,
    [("/hinmoku/", "回収・買取できる品目一覧", "対応品目をまとめて確認"),
     ("/nouki-kaitori/", "農機具の買取り", "査定額を費用に反映"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
     ("/katazuke-shimada/", "島田市の片付け・不用品回収", "市の制度との使い分け")],
    [price_offer_jsonld("/ryoukin/", "片付け・不用品回収（静岡県島田市）",
                        "荷物の体積（㎥）を基準にお見積り。" + PRICE_LABEL
                        + "。搬出・運搬・適正処理の委託費用を含む。出張費・見積り無料。"),
     local_business_jsonld(),
     breadcrumb_jsonld("料金・費用", "/ryoukin/"),
     faq_jsonld(RYOUKIN_FAQ)],
)

PAGES.append(("ryoukin", "片付け・不用品回収の料金｜静岡県島田市｜株式会社AMT", c))

# ------------------------------------------------------------
# 7. ご利用の流れ
# ------------------------------------------------------------
flow_body = (
    '<section class="k-section flow"><div class="inner">'
    '<h2 class="sec-title">ご利用の流れ</h2>'
    '<p class="sec-lead">お問い合わせから作業完了までの流れです。</p>'
    '<div class="flow-steps">'
    '<div class="flow-step"><h3>お問い合わせ</h3><p>電話またはメールで、片付けたい内容・場所・ご希望時期をお知らせください。</p></div>'
    '<div class="flow-step"><h3>現地確認・ヒアリング</h3><p>お品物の量や搬出経路を確認し、ご要望をうかがいます。</p></div>'
    '<div class="flow-step"><h3>お見積り</h3><p>内容をもとに、明確なお見積りをご提示します（無料）。</p></div>'
    '<div class="flow-step"><h3>日程調整・作業</h3><p>ご都合に合わせて日程を決め、仕分け・搬出・回収を行います。</p></div>'
    '<div class="flow-step"><h3>完了・お支払い</h3><p>作業後の状態をご確認いただき完了です。法人さまは請求書払いにも対応します。</p></div>'
    '</div></div></section>'
    '<section class="k-section"><div class="prose">'
    '<h2>買取できるものがあれば費用に反映します</h2>'
    '<p>片付けや回収で出たものの中に、金属・機械・農機具など'
    '<strong>買取できるものがあれば査定</strong>し、'
    '条件に応じて費用への反映をご提案します。</p>'
    '<p class="note">※買取額や費用への反映は、品物の種類・状態・相場によって変わります。</p>'
    '</div></section>'
)
FLOW_STEPS = [
    ("お問い合わせ",
     "お電話（" + TEL + "）またはお問い合わせフォームからご相談ください。"
     "品物の量や作業のご希望、ご希望の時期をお聞かせください。"),
    ("現地確認（無料）",
     "担当者が現地にうかがい、荷物の量（㎥）・間取り・階数・搬出経路を確認します。"
     "出張費はいただきません。立ち会いが難しい場合もご相談ください。"),
    ("お見積りのご提示（無料）",
     "確認した内容をもとに、㎥数の内訳と、買取で差し引ける金額をあわせてご提示します。"
     "片付け・不用品回収は" + PRICE_LABEL + "が目安です。"),
    ("ご検討・日程の調整",
     "内容にご納得いただけたら作業日を調整します。"
     "その場でお決めいただく必要はありません。お見積り後のキャンセルは無料です。"),
    ("作業・搬出",
     "仕分け・搬出・運搬を行います。買取品は査定のうえ買取し、"
     "処分が必要なものは提携する許可業者へ適正処理を委託します。近隣への配慮も徹底します。"),
    ("完了のご確認",
     "簡単な掃き掃除をして、お客様に仕上がりをご確認いただいて完了です。"
     "お支払いは現金または銀行振込（法人は請求書払い可）です。"),
]

FLOW_FAQ = [
    ("お問い合わせから作業までどのくらいかかりますか？",
     "ご相談の内容と混み具合によりますが、現地確認は日程を調整のうえ早めにうかがいます。"
     "お急ぎのご事情がある場合はお伝えください。可能な範囲で優先して調整します。"),
    ("現地確認やお見積りに費用はかかりますか？",
     "かかりません。ご相談・現地確認・お見積り・出張費はすべて無料です。"),
    ("立ち会えないのですが依頼できますか？",
     "ご相談ください。遠方にお住まいの場合や立ち会いが難しい場合も、"
     "写真や鍵のお預かりなど、方法をあわせてご検討します。"),
    ("見積りのあとに断ってもいいですか？",
     "はい。お見積り後のキャンセルは無料です。ほかと比べていただいてかまいません。"),
    ("作業当日は何を用意すればよいですか？",
     "とくにご用意いただくものはありません。"
     "買取をご希望の場合は、古物営業法により身分を確認できるもの（運転免許証など）が必要です。"),
    ("支払いはいつ、どのようにしますか？",
     "作業完了後に、現金または銀行振込でお願いしています。法人のお客様は請求書払いも可能です。"),
]

c, _ = assemble(
    "flow", "ご利用の流れ",
    "ご利用の流れ｜お問い合わせから完了まで｜株式会社AMT",
    "お問い合わせ・現地確認・お見積り・作業・完了までの流れをご案内します。お見積り無料。",
    flow_body, FLOW_FAQ,
    [("/ryoukin/", "料金・費用について", PRICE_LABEL),
     ("/faq/", "よくある質問", "対応品目・流れ"),
     ("/jirei/", "対応事例", "実際の作業の例"),
     ("/contact/", "お問い合わせ", "電話・メールで相談")],
    [howto_jsonld(
        "片付け・不用品回収のご依頼の流れ",
        "お問い合わせから現地確認・お見積り・作業・完了までの流れ。現地確認とお見積りは無料です。",
        "/flow/", FLOW_STEPS),
     local_business_jsonld(),
     breadcrumb_jsonld("ご利用の流れ", "/flow/"),
     faq_jsonld(FLOW_FAQ)],
)
PAGES.append(("flow", "ご利用の流れ｜お問い合わせから完了まで｜株式会社AMT", c))

# ------------------------------------------------------------
# 8. 会社概要（資格・許認可の欄は置かない：保有していないため）
# ------------------------------------------------------------
company_body = (
    '<section class="k-section company"><div class="inner">'
    '<h2 class="sec-title">会社概要</h2>'
    '<table>'
    '<tr><th>会社名</th><td>株式会社AMT</td></tr>'
    ''
    '<tr><th>所在地</th><td>〒428-0013　静岡県島田市金谷東2丁目3483-290</td></tr>'
    f'<tr><th>電話番号</th><td><a href="tel:{TEL}">{TEL}</a></td></tr>'
    f'<tr><th>メール</th><td><a href="mailto:{MAIL}">{MAIL}</a></td></tr>'
    f'<tr><th>許認可</th><td>{KOBUTSU_TD}</td></tr>'
    '<tr><th>事業内容</th><td>お片付け・不用品回収・残置物撤去・農機具買取（おうちのお片付け隊）、'
    '解体工事、非鉄金属・工業雑品スクラップ買取、中古太陽光パネル買取・輸出、通販・卸売</td></tr>'
    '<tr><th>対応エリア</th><td>静岡県内を中心（島田市・金谷・藤枝市・焼津市・静岡市・掛川市・菊川市・牧之原市・浜松市ほか）</td></tr>'
    '<tr><th>コーポレートサイト</th><td><a href="https://amt-eco.com/" target="_blank" rel="noopener">https://amt-eco.com/</a></td></tr>'
    '</table></div></section>'
)
c, _ = assemble(
    "company", "会社概要",
    "会社概要｜株式会社AMT（静岡県島田市）",
    "株式会社AMTの会社概要。片付け・不用品回収・残置物撤去・農機具買取のほか、解体工事・金属買取なども手がけています。",
    company_body, [],
    [("/katazuke/", "家のお片付け", "対応サービス"),
     ("/area/", "対応エリア", "静岡県内中心"),
     ("/contact/", "お問い合わせ", "電話・メールで相談")],
    [breadcrumb_jsonld("会社概要", "/company/")],
)
PAGES.append(("company", "会社概要｜株式会社AMT（静岡県島田市）", c))

# ------------------------------------------------------------
# 9. 対応エリア
# ------------------------------------------------------------
area_body = (
    '<section class="k-section"><div class="prose">'
    '<p class="lead">静岡県内を中心に、片付け・不用品回収・残置物撤去・倉庫の片付け・'
    '農機具の買取りを承っています。下記エリアはもちろん、近隣地域もまずはご相談ください。</p>'
    f'<div class="area-map"><img src="{IMG["area_map"]}" alt="対応エリアマップ：静岡県島田市を中心に藤枝市・焼津市・静岡市・掛川市・菊川市・牧之原市など" width="1200" height="761" loading="lazy"></div>'
    '<h2>主な対応エリア</h2>'
    '<ul>'
    '<li>島田市（金谷を含む）</li><li>藤枝市</li><li>焼津市</li><li>静岡市</li>'
    '<li>掛川市</li><li>菊川市</li><li>牧之原市</li><li>浜松市</li></ul>'
    '<p>上記以外の静岡県内の地域や、県外の物件についてもご相談を承ります。'
    '空き家や遠方の物件の片付けもお気軽にお問い合わせください。</p>'
    '<h2>現地確認でエリアの条件を確認します</h2>'
    '<p>片付け・回収は、前面道路の幅・トラックの横付け可否・搬出経路など、'
    '立地条件によって進め方が変わります。現地を確認したうえで、'
    'その現場に合った方法とお見積りをご提案します。</p>'
    '</div></section>'
)
c, _ = assemble(
    "area", "対応エリア",
    "対応エリア｜静岡県内中心｜おうちのお片付け隊（株式会社AMT）",
    "島田市・藤枝市・焼津市・静岡市・掛川市・菊川市・牧之原市・浜松市ほか、静岡県内を中心に片付け・不用品回収に対応します。",
    area_body, [],
    [("/katazuke/", "家のお片付け", "住まいの片付け"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
     ("/contact/", "お問い合わせ", "電話・メールで相談")],
    [breadcrumb_jsonld("対応エリア", "/area/")],
)
PAGES.append(("area", "対応エリア｜静岡県内中心｜おうちのお片付け隊（株式会社AMT）", c))

# ------------------------------------------------------------
# 10. よくある質問（総合）
# ------------------------------------------------------------
faq_all = [
    ("料金はいくらくらいですか？",
     "お品物の量・種類・間取り・搬出経路・作業人数などによって変わります。現地確認のうえ無料でお見積りします。"),
    ("見積りは無料ですか？", "はい、お見積り・ご相談は無料です。"),
    ("少量でも依頼できますか？",
     "一部屋・一部の家財だけでも承ります。量が多い場合ももちろん対応します。"),
    ("個人でも法人でも依頼できますか？",
     "どちらも対応します。法人・事業者さまには御見積書・請求書の発行も承ります。"),
    ("回収できないものはありますか？",
     "危険物や、法令で別途処理が必要なものなど、お引き取りできない品目があります。品目を確認のうえご案内します。"),
    ("家電は処分してもらえますか？",
     "テレビ・冷蔵庫・洗濯機・エアコンなどは家電リサイクル法の対象です。取り扱いの可否・方法は現地確認時にご案内します。"),
    ("解体前の残置物もお願いできますか？",
     "対応します。当社は解体工事も行っているため、残置物の撤去から解体まで一貫してご相談いただけます。"),
    ("農機具や金属も買い取ってもらえますか？",
     "買取できる場合があります。機種・状態・相場によって異なりますので、現物を確認のうえ査定します。"),
    ("即日対応はできますか？",
     "内容や日程によります。お急ぎの場合はその旨をお伝えください。できる限り調整します。"),
    ("遠方や空き家でも依頼できますか？",
     "静岡県内を中心に、空き家や遠方の物件のご相談も承ります。まずはお電話またはメールでご連絡ください。"),
]
c, _ = assemble(
    "faq", "よくある質問",
    "よくある質問｜おうちのお片付け隊（株式会社AMT）",
    "料金・見積り・対応品目・家電の処分・残置物・農機具買取など、片付け・不用品回収のよくある質問にお答えします。",
    '<section class="k-section"><div class="prose"><p class="lead">'
    '片付け・不用品回収についてよくいただくご質問をまとめました。'
    'ここにない内容もお気軽にお問い合わせください。</p></div></section>',
    faq_all,
    [("/ryoukin/", "料金・費用について", "費用の決まり方"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
     ("/contact/", "お問い合わせ", "電話・メールで相談")],
    [breadcrumb_jsonld("よくある質問", "/faq/"), faq_jsonld(faq_all)],
)
PAGES.append(("faq", "よくある質問｜おうちのお片付け隊（株式会社AMT）", c))

# ------------------------------------------------------------
# 島田市の片付け・不用品回収（地域ページ／2026-10-05 追加）
# 市の制度・窓口は島田市公式サイトで確認した内容のみ。電話番号は当社の番号以外は載せず、市のページへリンクする。
# ------------------------------------------------------------
SHIMADA_CITY = {
    "sodai": "https://www.city.shimada.shizuoka.jp/kurashi-docs/kobetu2.html",
    "jiko": "https://www.city.shimada.shizuoka.jp/kurashi-docs/jikohannyu_1.html",
    "wakekata": "https://www.city.shimada.shizuoka.jp/kurashi/life-event/scene09/01/",
    "akiya": "https://www.city.shimada.shizuoka.jp/gyosei/zigyo-keikaku/kenchiku/akiya_taisaku/",
    "bank": "https://www.city.shimada.shizuoka.jp/gyosei-docs/akiyabanku.html",
}
ANSWERS["katazuke-shimada"] = (
    "島田市の片付け・不用品回収は、<strong>島田市金谷に拠点を置く</strong>おうちのお片付け隊（株式会社AMT）へ。"
    "まだ使えるものは<strong>古物商許可のもとで買取</strong>し、処分が必要なものは提携する許可業者へ適正処理を委託します。"
    "量が少なければ市の粗大ごみ・自己搬入も選べるので、<strong>無料見積り</strong>で比べてから決められます。"
)
add_service_page(
    "katazuke-shimada", "島田市の片付け・不用品回収",
    "島田市の片付け・不用品回収｜市内金谷のおうちのお片付け隊",
    "島田市の家の片付け・不用品回収・残置物撤去・農機具の買取は、市内金谷に拠点を置く株式会社AMTへ。"
    "市の粗大ごみの出し方や、空き家の相談窓口もまとめました。お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">おうちのお片付け隊（株式会社AMT）は、島田市金谷東に拠点を置いています。'
    '地元の島田市なら、現地確認やお見積りにもすぐうかがえます。'
    '自分で出せるもの、市に出せるもの、業者に頼んだほうが早いもの。島田市の制度もふまえて、いちばん負担の少ない方法をご提案します。</p>'

    '<h2>島田市で、こんな片付けをお手伝いしています</h2>'
    '<ul>'
    '<li><a href="/katazuke/">家のお片付け</a>（引越し前後・模様替え・物置の整理）</li>'
    '<li><a href="/akiya/">空き家・実家の片付け</a>（遠方にお住まいの方のご依頼も）</li>'
    '<li><a href="/seiri/">生前整理・遺品整理</a></li>'
    '<li><a href="/zanchibutsu/">解体前の残置物撤去</a>（当社の解体工事とあわせて）</li>'
    '<li><a href="/souko/">倉庫・工場・店舗の片付け</a>（法人・事業者さま）</li>'
    '<li><a href="/nouki-kaitori/">農機具の買取り</a>（トラクター・耕運機・田植機など）</li>'
    '</ul>'

    '<h2>自分で出す？業者に頼む？島田市での選び方</h2>'
    '<p>量が少なければ、市の粗大ごみや自己搬入で出すのがいちばん安く済みます。'
    '一方で、<strong>家一軒分・倉庫一棟分</strong>のように量が多いときや、運び出す人手・車がないとき、期日が決まっているときは、まとめて任せたほうが早く確実です。</p>'
    '<table><thead><tr><th>方法</th><th>向いているケース</th></tr></thead><tbody>'
    '<tr><th>市の粗大ごみ（戸別収集）</th><td>大きな家具などが数点だけのとき</td></tr>'
    '<tr><th>市の施設へ自己搬入</th><td>車と人手があり、自分で運べるとき</td></tr>'
    '<tr><th>おうちのお片付け隊</th><td>量が多い・運び出せない・期日がある・買取できる品があるとき</td></tr>'
    '</tbody></table>'

    '<h2>島田市の粗大ごみの出し方（要点）</h2>'
    '<p>島田市の粗大ごみは、<strong>電話での申し込み制の戸別収集</strong>です。'
    '申し込みの際は、品物の材質と寸法（高さ・横幅・奥行）を測っておく必要があります。'
    '<strong>1世帯1回につき2点まで</strong>で、原則として自宅の敷地内に出します。</p>'
    '<p>テレビ・エアコン・洗濯機・衣類乾燥機・冷蔵庫・冷凍庫（家電リサイクル法の対象品）、事業所から出たごみ、50kg以上の物は、粗大ごみとしては出せません。'
    '申込先や収集日などの詳細は、<a href="' + SHIMADA_CITY["sodai"] + '" target="_blank" rel="noopener">島田市公式サイト：粗大ごみの出し方</a>でご確認ください。'
    '家電4品目の処分方法は<a href="/kaden-shobun/">家電の処分方法（家電リサイクル法）</a>で解説しています。</p>'

    '<h2>島田市の施設への自己搬入</h2>'
    '<p>家庭ごみは、市の施設（田代環境プラザ）へ自分で持ち込むこともできます。'
    '受付日時・料金・持ち込めないものはごみの種類ごとに決まっているため、'
    '<a href="' + SHIMADA_CITY["jiko"] + '" target="_blank" rel="noopener">島田市公式サイト：家庭ごみの自己搬入</a>で確認してから持ち込みましょう。'
    '分別のしかたは<a href="' + SHIMADA_CITY["wakekata"] + '" target="_blank" rel="noopener">ごみの分け方・出し方</a>にまとまっています。</p>'

    '<h2>当社の回収のしくみ（許可について）</h2>'
    '<p>当社は<strong>' + KOBUTSU_LABEL + '</strong>を受けています。'
    'まだ使えるもの・価値のあるものは買取の対象とし、買取できたぶんは費用に反映します。'
    '処分が必要なものは、<strong>提携する許可業者へ適正処理を委託</strong>します。'
    '何を買取・回収できるかは<a href="/hinmoku/">回収・買取できるもの</a>をご覧ください。</p>'

    '<h2>島田市の空き家の片付け・解体の相談先</h2>'
    '<p>空き家に関する市の取り組みは<a href="' + SHIMADA_CITY["akiya"] + '" target="_blank" rel="noopener">島田市公式サイト：空き家等対策</a>に、'
    '空き家バンクの案内は<a href="' + SHIMADA_CITY["bank"] + '" target="_blank" rel="noopener">島田市公式サイト：空き家バンク</a>にまとめられています。</p>'
    '<p>片付けのあと建物の解体まで考えている場合は、当社の解体工事とまとめてご相談いただけます。'
    '島田市の空き家解体の補助金（市内の解体事業者への発注が条件）については、'
    '<a href="https://kaitai.amt-eco.com/kaitai-shimada/">島田市の解体工事・解体業者｜AMT 解体工事</a>で詳しくまとめています。</p>'

    '<p class="note">※掲載している市の制度・窓口は、2026年10月5日時点で島田市の公式サイトで確認した内容です。'
    '内容は変わることがあるため、最新の情報は島田市の担当窓口でご確認ください。</p>'
    '</div></section>',
    [
        ("島田市内ならどの地区でも来てもらえますか？",
         "はい。当社は島田市金谷に拠点があり、島田市内は対応エリアです。まずは場所と品物の量をお知らせください。"),
        ("市の粗大ごみと、どちらが安いですか？",
         "数点だけなら市の粗大ごみや自己搬入のほうが安く済むことが多いです。量が多いときや運び出せないときは、まとめてお任せいただくほうが早く確実です。お見積りは無料なので、比べてから決めていただけます。"),
        ("冷蔵庫や洗濯機も引き取ってもらえますか？",
         "家電リサイクル法の対象品（テレビ・エアコン・冷蔵庫・冷凍庫・洗濯機・衣類乾燥機）は、法令に沿った方法で取り扱います。状態によっては買取の対象になることもあります。現地確認のときにご案内します。"),
    ],
    [
        ("/akiya/", "空き家・実家の片付け", "遠方・解体前もまとめて"),
        ("/fuyouhin/", "不用品の回収", "家具・家電をまとめて"),
        ("/hinmoku/", "回収・買取できるもの", "対応品目の一覧"),
        ("/area/", "対応エリア", "静岡県内の対応地域"),
    ],
    "島田市の片付け・不用品回収",
    "静岡県島田市での家の片付け・不用品回収・残置物撤去・倉庫の片付け・農機具の買取。市内金谷の株式会社AMTが対応。",
    "島田市の片付け・不用品回収｜市内金谷のおうちのお片付け隊（株式会社AMT）",
)

# ------------------------------------------------------------
# 11. お問い合わせ
# ------------------------------------------------------------
# Contact Form 7 のショートコード（既定フォーム「Contact form 1」／送信先＝サイト管理者メール）
CF7_SHORTCODE = '[contact-form-7 id="2ca5633" title="Contact form 1"]'

contact_h1 = "お問い合わせ｜おうちのお片付け隊（株式会社AMT）"
contact_lead = ("片付け・不用品回収のご相談・お見積りは無料。"
                "電話・フォーム・メールのいずれでもお気軽にお問い合わせください。")
contact_intro = (
    '<section class="k-section"><div class="prose">'
    '<p class="lead">お片付け・不用品回収・残置物撤去・倉庫の片付け・農機具の買取りに関するご相談・'
    'お見積りは無料です。お電話・フォーム・メールのいずれでもお気軽にどうぞ。</p>'
    '<h2>お電話でのお問い合わせ</h2>'
    f'<p style="font-size:1.6rem;font-weight:900;"><a href="tel:{TEL}">{TEL}</a></p>'
    '<p>受付時間内にお気軽にお電話ください。「費用だけ知りたい」というご相談だけでも大丈夫です。</p>'
    f'<p>メールでも承ります：<a href="mailto:{MAIL}">{MAIL}</a></p>'
    '</div></section>'
)
contact_form_open = (
    '<section class="k-section"><div class="inner">'
    '<h2 class="sec-title">フォームでのお問い合わせ</h2>'
    '<p class="sec-lead">下記フォームにご記入のうえ送信してください。'
    '折り返し担当者よりご連絡します。</p>'
    '<div class="amt-form amt-cf7">'
)
contact_form_close = '</div></div></section>'
contact_rel = rel_block([
    ("/ryoukin/", "料金・費用について", "費用の決まり方"),
    ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
    ("/faq/", "よくある質問", "対応品目・流れ"),
])
# 解体サイトと同じ「カスタムHTML＋ショートコードブロック」方式でCF7を本文内に埋め込む
_c_b1 = ('<!-- wp:html -->\n<div class="amt-katazuke">'
         + header("/contact/") + breadcrumb("お問い合わせ")
         + page_hero(contact_h1, contact_lead) + contact_intro + contact_form_open
         + '\n<!-- /wp:html -->')
_c_b2 = '<!-- wp:shortcode -->' + CF7_SHORTCODE + '<!-- /wp:shortcode -->'
_c_b3 = ('<!-- wp:html -->\n' + contact_form_close + contact_rel + cta() + footer()
         + '</div>\n<!-- /wp:html -->')
_c_ld = ('<!-- wp:html -->\n<script type="application/ld+json">'
         + json.dumps(breadcrumb_jsonld("お問い合わせ", "/contact/"), ensure_ascii=False)
         + '</script>\n<!-- /wp:html -->')
# WebMCP（Declarative API）：CF7のformをAIエージェント用ツールとして宣言（2026-10-05）。
# CF7はformに任意属性を付けられないため、フォームの後ろでスクリプトが属性を付与する。
# toolautosubmit は付けない（送信はお客様自身がボタンを押す）。
WEBMCP_PARAMS = {
    "your-name": "お問い合わせする方のお名前（必須）",
    "your-email": "返信先のメールアドレス（必須）",
    "your-tel": "連絡のつく電話番号（任意）",
    "your-subject": "件名。例：家の片付け、不用品回収、残置物撤去、倉庫の片付け、農機具の買取（任意）",
    "your-message": "ご相談内容。片付けたい場所・品物の量・所在地（市町）・希望時期など（必須）",
}
_c_webmcp = (
    '<!-- wp:html -->\n<script id="amt-webmcp-form">(function(){'
    "var f=document.querySelector('form.wpcf7-form');if(!f)return;"
    "f.setAttribute('toolname','request_katazuke_estimate');"
    "f.setAttribute('tooldescription','株式会社AMT「おうちのお片付け隊」（静岡県島田市）に、家の片付け・不用品回収・"
    "解体前の残置物撤去・倉庫の片付け・農機具の買取の無料見積り・相談を依頼するお問い合わせフォーム。"
    "お名前・メールアドレス・お問い合わせ内容は必須。送信はユーザーが確認して行う。');"
    "var d=" + json.dumps(WEBMCP_PARAMS, ensure_ascii=False) + ";"
    "for(var k in d){var e=f.querySelector('[name=\"'+k+'\"]');if(e)e.setAttribute('toolparamdescription',d[k]);}"
    "})();</script>\n<!-- /wp:html -->"
)
c = "\n\n".join([_c_b1, _c_b2, _c_b3, _c_webmcp, _c_ld])
PAGES.append(("contact", "お問い合わせ｜おうちのお片付け隊（株式会社AMT）", c))

# ------------------------------------------------------------
# 12. プライバシーポリシー
# ------------------------------------------------------------
privacy_body = (
    '<section class="k-section"><div class="prose">'
    '<p class="lead">株式会社AMT（以下「当社」）は、「おうちのお片付け隊」'
    '（katazuke.amt-eco.com）の運営にあたり、お客様の個人情報を適切に取り扱い、'
    'その保護に努めます。</p>'
    '<h2>1. 取得する個人情報</h2>'
    '<p>お問い合わせ・お見積り・作業のご依頼にあたり、お名前、ご住所、電話番号、'
    'メールアドレス、お問い合わせ内容などをお預かりすることがあります。</p>'
    '<h2>2. 利用目的</h2>'
    '<ul><li>お見積り・ご相談への回答、ご連絡のため</li>'
    '<li>片付け・回収・撤去・買取などのサービスの提供・実施のため</li>'
    '<li>アフターフォロー、ご案内のため</li>'
    '<li>法令に基づく対応のため</li></ul>'
    '<h2>3. 第三者提供</h2>'
    '<p>当社は、法令に基づく場合を除き、あらかじめご本人の同意を得ることなく、'
    '個人情報を第三者に提供しません。</p>'
    '<h2>4. 業務委託</h2>'
    '<p>サービスの提供に必要な範囲で、不用品の適正処理を提携する許可業者に委託するなど、'
    '業務の一部を外部に委託する場合があります。委託先に対しては、個人情報を適切に'
    '取り扱うよう必要な監督を行います。</p>'
    '<h2>5. 個人情報の管理</h2>'
    '<p>お預かりした個人情報について、漏えい・滅失・毀損の防止に努め、適切に管理します。</p>'
    '<h2>6. 開示・訂正・削除のご請求</h2>'
    '<p>ご本人から個人情報の開示・訂正・削除などのお求めがあった場合は、'
    'ご本人であることを確認のうえ、適切に対応します。</p>'
    '<h2>7. お問い合わせ窓口</h2>'
    '<p>株式会社AMT（おうちのお片付け隊）<br>'
    '〒428-0013　静岡県島田市金谷東2丁目3483-290<br>'
    f'TEL：<a href="tel:{TEL}">{TEL}</a>　メール：<a href="mailto:{MAIL}">{MAIL}</a></p>'
    '<h2>8. 本ポリシーの改定</h2>'
    '<p>本プライバシーポリシーは、必要に応じて改定することがあります。'
    '改定後の内容は、本ページに掲載した時点から適用されます。</p>'
    '</div></section>'
)
c, _ = assemble(
    "privacy-policy", "プライバシーポリシー",
    "プライバシーポリシー｜おうちのお片付け隊（株式会社AMT）",
    "株式会社AMT「おうちのお片付け隊」の個人情報の取り扱いについてご案内します。",
    privacy_body, [],
    [("/contact/", "お問い合わせ", "電話・メールで相談"),
     ("/company/", "会社概要", "株式会社AMTについて")],
    [breadcrumb_jsonld("プライバシーポリシー", "/privacy-policy/")],
)
PAGES.append(("privacy-policy", "プライバシーポリシー｜おうちのお片付け隊（株式会社AMT）", c))


# ------------------------------------------------------------
# 12. 生前整理・遺品整理（専用サービスページ）
# ------------------------------------------------------------
add_service_page(
    "seiri", "生前整理・遺品整理",
    "生前整理・遺品整理｜静岡県島田市の株式会社AMT",
    "生前整理はこれからの暮らしのために、遺品整理は大切な方を亡くされた後に。仕分けから搬出・買取・適正処理まで、静岡県内を中心にまとめてお手伝いします。お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">生前整理は「元気なうちに、これからの暮らしと家族のために」、'
    '遺品整理は「大切な方を亡くされた後に」。どちらも、仕分けから搬出・買取・適正処理まで、'
    '静岡県内を中心にまとめてお手伝いします。個人のお客様はもちろん、遠方にお住まいの方のご依頼にも対応します。</p>'
    '<h2>生前整理のお手伝い</h2>'
    '<p>生前整理は、ご自身の意思で持ち物を整理し、これからの暮らしを整え、ご家族の負担を軽くする取り組みです。'
    '貴重品・重要書類の確認から、「残す・譲る・売る・処分」の仕分け、搬出までお手伝いします。'
    'まだ使えるものは<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、費用に反映できる場合があります。</p>'
    '<p>進め方のコツは<a href="/seizen-seiri/">生前整理の進め方（コラム）</a>で詳しく解説しています。</p>'
    '<h2>遺品整理のお手伝い</h2>'
    '<p>遺品整理は、ご家族の気持ちに寄り添いながら進めます。通帳・印鑑などの貴重品や重要書類の捜索、'
    '形見分けの取り分け、ご希望に応じた供養のご相談にも配慮します。'
    '賃貸住宅で退去期限がある場合も、日程を含めてご相談ください。</p>'
    '<p class="note">※相続放棄をご検討の場合、遺品の処分が相続の承認とみなされることがあります。'
    '判断に迷うときは、片付けを始める前に専門家（弁護士・司法書士など）へご相談ください。</p>'
    '<p>詳しくは<a href="/ihin-seiri/">遺品整理の進め方と業者選び（コラム）</a>もご覧ください。</p>'
    '<h2>当社にまとめて任せるメリット</h2>'
    '<ul>'
    '<li>まだ使えるものは<strong>古物商のもとで買取</strong>し、費用に反映できる場合があります</li>'
    '<li>処分が必要なものは<strong>提携する許可業者に適正処理を委託</strong>します</li>'
    '<li>解体が必要な場合は、<a href="/zanchibutsu/">残置物撤去</a>から解体まで一貫してご相談いただけます</li>'
    '</ul>'
    '<h2>費用について</h2>'
    '<p>費用は、お品物の量・間取り・搬出経路・作業人数などによって変わります。'
    '現地を確認したうえで<strong>無料でお見積り</strong>します。買取できるものがあれば費用へ反映できる場合があります。</p>'
    '<p class="note">※料金は現地条件によって変わるため、目安額は掲載していません。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("一部屋だけ・少量でも依頼できますか？",
      "はい、一部屋・一部の家財だけでも承ります。量が多い場合ももちろん対応します。"),
     ("遠方に住んでいても依頼できますか？",
      "はい。遠方の方のご依頼も承ります。立ち会いが難しい場合の進め方もご相談ください。"),
     ("買取と片付けは同時にお願いできますか？",
      "できます。使えるものは買取し、費用に反映できる場合があります。")],
    [("/katazuke/", "家のお片付け", "住まいの片付け全般"),
     ("/fuyouhin/", "不用品の回収", "買取＋搬出＋適正処理"),
     ("/seizen-seiri/", "生前整理の進め方", "始め方・チェックリスト（コラム）"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "生前整理・遺品整理", "生前整理・遺品整理の仕分け・搬出・買取・適正処理。静岡県内中心、個人・遠方対応。お見積り無料。",
    "生前整理・遺品整理｜静岡県島田市の株式会社AMT",
    hero_img=IMG["katazuke"],
)

# ------------------------------------------------------------
# 13. 回収・買取できるもの（対応品目一覧）
# ------------------------------------------------------------
add_service_page(
    "hinmoku", "対応品目一覧",
    "回収・買取できる品目一覧｜静岡県島田市の株式会社AMT",
    "家具・家電・生活用品・事務什器・農機具・機械・金属くずまで幅広く対応。まだ使えるものは古物商のもとで買取、処分が必要なものは提携する許可業者へ適正処理を委託します。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">ご家庭から出るものも、事業所のものも、幅広く対応します。'
    'まだ使えるものは<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、'
    '処分が必要なものは<strong>提携する許可業者に適正処理を委託</strong>します。'
    '下記は代表的な品目の例です。掲載のないものも、まずはご相談ください。</p>'
    '<h2>対応品目の例</h2>'
    '<table><thead><tr><th>区分</th><th>品目の例</th></tr></thead><tbody>'
    '<tr><th>家具</th><td>タンス・ソファ・机・椅子・棚・ベッド など</td></tr>'
    '<tr><th>家電</th><td>冷蔵庫・洗濯機・テレビ・電子レンジ・エアコン など（家電リサイクル法対象品は法令に沿って取り扱います）</td></tr>'
    '<tr><th>生活用品</th><td>食器・調理器具・寝具・衣類・日用雑貨 など</td></tr>'
    '<tr><th>事務用品・什器</th><td>デスク・キャビネット・棚・厨房機器・店舗什器 など</td></tr>'
    '<tr><th>農機具・機械</th><td>トラクター・耕運機・田植機・刈払機・動力機械 など</td></tr>'
    '<tr><th>金属・スクラップ</th><td>非鉄金属・工業雑品・金属くず・使わなくなった機械 など</td></tr>'
    '</tbody></table>'
    '<h2>買取できるもの</h2>'
    '<p>状態のよい家具・家電、工具、農機具・機械、金属類などは、'
    '<strong>古物商許可（機械工具類・静岡県公安委員会）</strong>や非鉄金属・工業雑品スクラップの買取として、'
    '費用に反映できる場合があります。使わなくなった農機具は<a href="/nouki-kaitori/">農機具の買取り</a>もご覧ください。</p>'
    '<h2>取り扱いに注意が必要なもの</h2>'
    '<p>テレビ・冷蔵庫・洗濯機・エアコンなどの<strong>家電リサイクル法</strong>対象品は、'
    '法令に沿った方法で手放す必要があります。詳しくは'
    '<a href="/kaden-shobun/">家電の正しい処分方法（コラム）</a>をご覧ください。'
    '危険物・液体・特殊なものなど、お預かりできないものもあります。判断に迷う場合は現地確認時にご案内します。</p>'
    '<h2>まずはご相談ください</h2>'
    '<p>「これは回収できる？」「買取できる？」だけでも大丈夫です。'
    '量の多少や品目を問わず、静岡県内を中心に対応します。'
    '<a href="/fuyouhin/">不用品の回収</a>とあわせてご相談ください。</p>'
    '</div></section>',
    [("一覧にないものも対応できますか？",
      "掲載のない品目もご相談ください。現地確認で対応の可否と方法をご案内します。"),
     ("買取できるか分からないものも見てもらえますか？",
      "はい、買取の可否を含めて現地で確認します。まとめてご相談ください。"),
     ("家電リサイクル法の対象品も相談できますか？",
      "回収の可否・方法をご案内します。法令に沿って取り扱います。")],
    [("/fuyouhin/", "不用品の回収", "家具・家電をまとめて"),
     ("/nouki-kaitori/", "農機具の買取り", "農機具・機械の買取"),
     ("/souko/", "倉庫の片付け", "法人・事業者さま向け"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "回収・買取できるもの（対応品目）", "家具・家電・生活用品・事務什器・農機具・機械・金属など幅広く対応。買取と適正処理の手配。",
    "回収・買取できる品目一覧｜静岡県島田市の株式会社AMT",
    hero_img=IMG["fuyouhin"],
)


# ------------------------------------------------------------
# 14. 空き家・実家の片付け
# ------------------------------------------------------------
add_service_page(
    "akiya", "空き家・実家の片付け",
    "空き家・実家の片付け｜静岡県島田市の株式会社AMT",
    "遠方の実家や誰も住まなくなった空き家の片付けを、仕分けから搬出・買取・適正処理までまとめて。解体予定なら残置物撤去まで一貫対応します。お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">遠方のご実家や、誰も住まなくなった空き家の片付けは、量も多く、'
    'なかなか手をつけられないものです。仕分けから搬出・買取・処分・簡単な清掃まで、'
    '静岡県内を中心にまとめてお手伝いします。売却・賃貸・解体をお考えの場合もご相談ください。</p>'
    '<h2>こんなお悩みに対応します</h2>'
    '<ul>'
    '<li>遠方に住んでいて、現地の片付けに何度も通えない</li>'
    '<li>家財の量が多く、自分たちでは手が回らない</li>'
    '<li>何を残すべきか分からない／貴重品や書類を確認したい</li>'
    '<li>売却・賃貸・解体の前に、まず片付けたい</li>'
    '</ul>'
    '<h2>遠方でも進められます</h2>'
    '<p>現地確認とお見積りをまとめて行い、通う回数を抑えます。'
    '残すもの・処分するものの方針を事前に共有しておけば、立ち会いが難しい場合の進め方もご相談いただけます。'
    'まだ使えるものは<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、費用に反映できる場合があります。</p>'
    '<h2>解体を予定しているなら残置物撤去とセットで</h2>'
    '<p>建物を解体する場合は、家財を残したままでは工事を始められません。当社は'
    '<strong>解体工事も自社で対応</strong>しているため、<a href="/zanchibutsu/">残置物撤去</a>から解体まで'
    '一貫してご相談いただけます。進め方のコツは<a href="/akiya-katazuke/">空き家・実家の片付け（コラム）</a>もご覧ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、物量・間取り・搬出経路・作業人数などによって変わります。'
    '現地を確認したうえで<strong>無料でお見積り</strong>します。買取できるものがあれば費用へ反映できる場合があります。</p>'
    '<p class="note">※料金は現地条件によって変わるため、目安額は掲載していません。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("遠方に住んでいても依頼できますか？",
      "はい。現地確認・お見積りをまとめて行い、立ち会いが難しい場合の進め方もご相談いただけます。"),
     ("空き家の片付けと解体を両方頼めますか？",
      "できます。当社は解体工事も手がけているため、家財の撤去から解体まで一貫してご相談いただけます。"),
     ("庭木や物置も片付けられますか？",
      "現地の状況を確認のうえ対応可否をご案内します。まとめてのご相談も歓迎です。")],
    [("/katazuke/", "家のお片付け", "住まいの片付け全般"),
     ("/zanchibutsu/", "解体前の残置物撤去", "解体とあわせて一貫対応"),
     ("/akiya-katazuke/", "空き家・実家の片付け方", "進め方のコラム"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "空き家・実家の片付け", "空き家・実家の片付けを仕分け・搬出・買取・適正処理までまとめて。遠方対応・解体まで一貫。静岡県内中心。",
    "空き家・実家の片付け｜静岡県島田市の株式会社AMT",
    hero_img=IMG["katazuke"],
)

# ------------------------------------------------------------
# 15. ゴミ屋敷の片付け
# ------------------------------------------------------------
add_service_page(
    "gomiyashiki-katazuke", "ゴミ屋敷の片付け",
    "ゴミ屋敷の片付け｜静岡県島田市の株式会社AMT",
    "足の踏み場がない状態でも大丈夫。プライバシーに配慮し、分別・搬出・買取・簡単な清掃までまとめて対応します。静岡県内中心・お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">物があふれて足の踏み場がない状態でも、正しい手順で進めれば片付けられます。'
    'ひとりで抱え込まず、まずはご相談ください。プライバシーに配慮しながら、'
    '分別・搬出・買取・簡単な清掃まで、静岡県内を中心にまとめて対応します。</p>'
    '<h2>こんな状態でもご相談ください</h2>'
    '<ul>'
    '<li>床が見えないほど物が積もっている</li>'
    '<li>大型の家具・家電が多く、自分では運び出せない</li>'
    '<li>どこから手をつければよいか分からない</li>'
    '<li>短期間でまとめて片付けたい</li>'
    '</ul>'
    '<h2>片付けの進め方</h2>'
    '<p>まず入口・通路から安全と動線を確保し、通帳・印鑑・重要書類などの貴重品を先に探して分けます。'
    'その後「残す・売る・処分」で仕分け、搬出。作業後は簡単な清掃まで承ります。'
    'まだ使えるものは<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、'
    '処分が必要なものは<strong>提携する許可業者に適正処理を委託</strong>します。</p>'
    '<h2>プライバシーに配慮します</h2>'
    '<p>近隣に配慮し、できる限り目立たないよう作業します。日程や進め方についてもご相談いただけます。'
    '詳しい進め方は<a href="/gomiyashiki/">ゴミ屋敷の片付け方（コラム）</a>もご覧ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、物量・間取り・搬出経路・作業人数・清掃の有無などによって変わります。'
    '現地を確認したうえで<strong>無料でお見積り</strong>します。買取できるものがあれば費用へ反映できる場合があります。</p>'
    '<p class="note">※料金は現地条件によって変わるため、目安額は掲載していません。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("近所に知られずに片付けできますか？",
      "できる限り目立たないよう配慮して作業します。日程や進め方もご相談いただけます。"),
     ("量が多くても一度に片付けられますか？",
      "作業人数と日程を調整し、まとめて片付けます。まずは現地を確認してお見積りします。"),
     ("貴重品が見つかったらどうなりますか？",
      "作業中に見つかった通帳・貴重品などはお渡しします。事前に探してほしいものがあればお知らせください。")],
    [("/katazuke/", "家のお片付け", "住まいの片付け全般"),
     ("/fuyouhin/", "不用品の回収", "買取＋搬出＋適正処理"),
     ("/gomiyashiki/", "ゴミ屋敷の片付け方", "進め方のコラム"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "ゴミ屋敷の片付け", "ゴミ屋敷の片付けを、安全確保・貴重品確保・仕分け・搬出・清掃までまとめて。プライバシー配慮・買取対応。静岡県内中心。",
    "ゴミ屋敷の片付け｜静岡県島田市の株式会社AMT",
    hero_img=IMG["katazuke"],
)

# ------------------------------------------------------------
# 16. 引っ越しの片付け・不用品回収
# ------------------------------------------------------------
add_service_page(
    "hikkoshi", "引っ越しの片付け",
    "引っ越しの片付け・不用品回収｜静岡県島田市の株式会社AMT",
    "引っ越しで一度に出る不用品を、期日までにまとめて。大型家具・家電の搬出、買取、処分まで一括対応します。静岡県内中心・お見積り無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">引っ越しは不用品が一気に出るうえ、期日も決まっています。'
    '大型家具・家電の搬出から、買取、処分まで一括でお手伝いし、期日に間に合うよう段取りします。'
    'お引っ越し前後の片付けを、静岡県内を中心に承ります。</p>'
    '<h2>引っ越しにともなう不用品をまとめて</h2>'
    '<p>新居で使わない家具・家電、こまごまとした生活用品まで、まとめてお引き取りします。'
    'まだ使えるものは<strong>古物商許可（静岡県公安委員会）</strong>のもとで買取し、費用に反映できる場合があります。</p>'
    '<h2>期日までに間に合わせます</h2>'
    '<p>粗大ごみは自治体で収集日まで日数がかかる場合があります。'
    '搬出・買取・処分をまとめて依頼すれば、一度で片付き、退去・入居のスケジュールにも合わせやすくなります。'
    '段取りのコツは<a href="/hikkoshi-fuyouhin/">引っ越しの不用品処分（コラム）</a>もご覧ください。</p>'
    '<h2>大型家具・家電もお任せください</h2>'
    '<p>ベッド・タンス・冷蔵庫・洗濯機などの大型品も搬出します。'
    'テレビ・冷蔵庫・洗濯機・エアコンなどの家電リサイクル法対象品は、法令に沿って取り扱います。'
    '対応品目は<a href="/hinmoku/">回収・買取できるもの</a>をご覧ください。</p>'
    '<h2>費用について</h2>'
    '<p>費用は、品物の種類・量・大きさ・搬出条件などによって変わります。'
    '現地確認のうえ<strong>無料でお見積り</strong>します。買取できる品物があれば費用へ反映できる場合があります。</p>'
    '<p class="note">※料金は現地条件によって変わるため、目安額は掲載していません。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("引っ越し直前でも対応できますか？",
      "日程を確認のうえ、できる限り対応します。早めのご相談ほど段取りしやすくなります。"),
     ("家具と家電をまとめて引き取れますか？",
      "まとめて搬出・お引き取りします。使えるものは買取で費用に反映できる場合があります。"),
     ("新居の片付けも頼めますか？",
      "引っ越し前後どちらもご相談いただけます。搬出・設置まわりの片付けにも対応します。")],
    [("/fuyouhin/", "不用品の回収", "家具・家電をまとめて"),
     ("/hinmoku/", "回収・買取できるもの", "対応品目一覧"),
     ("/hikkoshi-fuyouhin/", "引っ越しの不用品処分", "段取りのコラム"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "引っ越しの片付け・不用品回収", "引っ越しで出る不用品を期日までにまとめて搬出・買取・処分。大型家具家電も対応。静岡県内中心。",
    "引っ越しの片付け・不用品回収｜静岡県島田市の株式会社AMT",
    hero_img=IMG["fuyouhin"],
)

# ------------------------------------------------------------
# 17. 店舗・オフィスの片付け（閉店・移転・原状回復）
# ------------------------------------------------------------
add_service_page(
    "tenpo", "店舗・オフィスの片付け",
    "店舗・オフィスの片付け｜静岡県島田市の株式会社AMT",
    "閉店・移転にともなう什器・在庫・機械の撤去から原状回復まで。買取と適正処理を組み合わせ、解体まで一貫対応。請求書払い可。静岡県内中心。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">店舗やオフィスの閉店・移転では、什器・在庫・機械の撤去から原状回復まで、'
    '期日内に終える段取りが欠かせません。買取と適正処理を組み合わせ、無駄なく撤去します。'
    '法人・事業者さまのご依頼を、静岡県内を中心に承ります。</p>'
    '<h2>閉店・移転で必要な片付け</h2>'
    '<p>賃貸の店舗・オフィスは、契約終了までに残置物をすべて撤去し、原状回復する必要があります。'
    '什器・在庫・機械・書類など、量が多く判断も必要なため、早めの段取りが重要です。</p>'
    '<h2>什器・機械は買取で費用を抑える</h2>'
    '<p>使える什器・機械・厨房機器などは<strong>買取</strong>で費用を抑えられる場合があります。'
    '当社は<strong>古物商許可（機械工具類・静岡県公安委員会）</strong>に加え、'
    '<strong>非鉄金属・工業雑品スクラップの買取</strong>も手がけています。'
    '対応品目は<a href="/hinmoku/">回収・買取できるもの</a>をご覧ください。</p>'
    '<h2>産業廃棄物は許可業者へ適正処理を委託</h2>'
    '<p>事業活動から出る廃棄物は産業廃棄物にあたり、法令に沿った処理が必要です。'
    '当社では、処分が必要なものは<strong>提携する許可業者に適正処理を委託</strong>します。</p>'
    '<h2>解体・原状回復まで一貫対応</h2>'
    '<p>建物の解体を予定している場合は、<a href="/zanchibutsu/">残置物撤去</a>から解体まで一貫してご相談いただけます。'
    '倉庫・工場の整理は<a href="/souko/">倉庫の片付け</a>もご覧ください。'
    '進め方は<a href="/tenpo-heiten/">店舗・オフィスの閉店の片付け（コラム）</a>で解説しています。</p>'
    '<h2>費用について（法人対応）</h2>'
    '<p>現地を確認したうえで、作業内容と費用を明確に<strong>無料でお見積り</strong>します。'
    '業務に影響しない日程のご提案や、<strong>請求書払い</strong>にも対応します。</p>'
    '<p class="note">※料金は現地条件によって変わるため、目安額は掲載していません。まずはお気軽にお問い合わせください。</p>'
    '</div></section>',
    [("閉店の期日が迫っていても対応できますか？",
      "日程を確認のうえ、できる限り対応します。早めにご相談いただくと段取りしやすくなります。"),
     ("什器や厨房機器は買取できますか？",
      "使えるものは古物商許可のもとで買取できる場合があります。金属くず・機械のスクラップ買取も可能です。"),
     ("請求書払いはできますか？",
      "はい、法人・事業者さまの請求書払いに対応しています。")],
    [("/souko/", "倉庫の片付け", "法人・事業者さま向け"),
     ("/zanchibutsu/", "解体前の残置物撤去", "撤去から解体まで一貫"),
     ("/tenpo-heiten/", "店舗・オフィス閉店の片付け", "進め方のコラム"),
     ("/contact/", "お問い合わせ", "ご相談・お見積りは無料")],
    "店舗・オフィスの片付け（閉店・移転・原状回復）", "店舗・オフィスの閉店・移転の片付けを、什器買取・撤去・適正処理・原状回復・解体まで一貫。請求書払い可。",
    "店舗・オフィスの片付け｜静岡県島田市の株式会社AMT",
    hero_img=IMG["souko"],
)


# ============================================================
# トップページ（単一HTMLファイル index.html）を生成
# ============================================================
# ------------------------------------------------------------
# 18. 対応事例（/jirei/）
#   assets/jirei-data.json の confirmed=true の事例だけを掲載する。
#   → 実在しない事例を「実績」として公開しないための仕組み。
#   記入シート: docs/jirei-kinyu-sheet.md
# ------------------------------------------------------------
def _load_jirei():
    path = os.path.join(HERE, "jirei-data.json")
    try:
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, ValueError):
        return []
    return [it for it in data.get("items", [])
            if it.get("confirmed") and it.get("title")]


JIREI_ITEMS = _load_jirei()

if JIREI_ITEMS:
    def _jirei_card(it):
        rows = []
        for lbl, key in [("ご依頼", "service"), ("エリア", "city"), ("建物", "building"),
                         ("ご依頼主", "who"), ("搬出量", "volume_m3"),
                         ("作業人数", "workers"), ("作業日数", "days"),
                         ("お見積り額", "price_note"), ("買取できたもの", "kaitori")]:
            v = (it.get(key) or "").strip()
            if v:
                rows.append("<tr><th>" + lbl + "</th><td>" + v + "</td></tr>")
        spec = "<table><tbody>" + "".join(rows) + "</tbody></table>" if rows else ""
        img = ""
        if (it.get("image") or "").strip():
            src = it["image"] if it["image"].startswith("http") else UPLOADS_OCT + it["image"]
            img = ('<div class="jr-img"><img src="' + src + '" alt="'
                   + (it.get("image_alt") or it["title"]) + '" width="1000" height="667" '
                   'loading="lazy" decoding="async"></div>')
        voice = ""
        if (it.get("voice") or "").strip():
            voice = '<blockquote class="jr-voice"><p>' + it["voice"] + "</p></blockquote>"
        reason = ""
        if (it.get("reason") or "").strip():
            reason = "<h3>ご依頼のきっかけ</h3><p>" + it["reason"] + "</p>"
        work = ""
        if (it.get("work") or "").strip():
            work = "<h3>実際の作業</h3><p>" + it["work"] + "</p>"
        link = ""
        if (it.get("service_url") or "").strip():
            link = ('<p class="jr-link"><a href="' + it["service_url"] + '">'
                    + (it.get("service") or "サービス") + "のページを見る</a></p>")
        return ('<article class="jr-card" id="jirei' + str(it.get("id", "")) + '">'
                '<p class="jr-tag">' + (it.get("service") or "") + "</p>"
                "<h2>" + it["title"] + "</h2>"
                + img + spec + reason + work + voice + link + "</article>")

    _cards = "".join(_jirei_card(it) for it in JIREI_ITEMS)
    _jirei_body = (
        '<section class="k-section" style="padding-bottom:0;"><div class="prose">'
        '<div class="answer"><span class="answer-h">要点</span>'
        '<p>実際にお引き受けした片付け・不用品回収・農機具買取の事例です。'
        '搬出量（㎥）・作業人数・日数・お見積り額の実例を掲載しています。'
        '料金の考え方は<a href="/ryoukin/">料金・費用について</a>'
        '（' + PRICE_LABEL + '）をご覧ください。</p></div>'
        '<p class="note">※お客様のプライバシーに配慮し、お名前・詳しい所在地は掲載していません。'
        '写真は掲載の許可をいただいたものを使用しています。</p>'
        '</div></section>'
        '<section class="k-section"><div class="prose jr-list">' + _cards + '</div></section>'
    )
    _jirei_faq = [
        ("同じような片付けだといくらぐらいかかりますか？",
         "片付け・不用品回収は" + PRICE_LABEL + "を目安に、荷物の体積（㎥）を基準に算出します。"
         "同じ㎥数でも間取り・階数・搬出経路で手間が変わるため、"
         "現地を確認したうえで無料でお見積りします。"),
        ("掲載されている事例と同じ作業を頼めますか？",
         "はい。事例と同様のご依頼を承ります。まずはお電話または"
         "お問い合わせフォームからご相談ください。"),
        ("作業前後の写真は必ず撮るのですか？",
         "掲載用の写真は、お客様の許可をいただいた場合のみ撮影・使用します。"
         "掲載をご希望されない場合は撮影しません。"),
    ]
    c, _ = assemble(
        "jirei", "対応事例",
        "片付け・不用品回収の対応事例｜静岡県島田市の株式会社AMT",
        "実際にお引き受けした片付け・不用品回収・農機具買取の事例を、"
        "搬出量・作業人数・日数・お見積り額つきでご紹介します。",
        _jirei_body, _jirei_faq,
        [("/ryoukin/", "料金・費用について", PRICE_LABEL),
         ("/katazuke/", "家のお片付け", "住まいの片付け"),
         ("/nouki-kaitori/", "農機具の買取り", "査定額を費用に反映"),
         ("/contact/", "お問い合わせ", "無料でお見積り")],
        [itemlist_jsonld("片付け・不用品回収の対応事例",
                         "株式会社AMT（おうちのお片付け隊）が静岡県内でお引き受けした事例。",
                         "/jirei/",
                         [(it["title"], "/jirei/#jirei" + str(it.get("id", "")),
                           (it.get("work") or "")[:160]) for it in JIREI_ITEMS]),
         local_business_jsonld(),
         breadcrumb_jsonld("対応事例", "/jirei/"),
         faq_jsonld(_jirei_faq)],
    )
    PAGES.append(("jirei", "片付け・不用品回収の対応事例｜静岡県島田市｜株式会社AMT", c))


def build_index():
    # ---- 2026-10-05 リニューアル v2：解体サイトと同じ作り込み（黄色×スレート） ----
    ICON = {
        "people": '<svg viewBox="0 0 24 24" fill="none" stroke="#f7b500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.6"/><path d="M15.5 14.2c3 .2 5.5 2.6 5.5 5.8"/></svg>',
        "coin": '<svg viewBox="0 0 24 24" fill="none" stroke="#f7b500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 13.7-5.6M20 12a8 8 0 0 1-13.7 5.6"/><path d="M17.5 2.5v4h-4M6.5 21.5v-4h4"/><path d="M12 8.5v7M9.8 10.2c0-1 1-1.7 2.2-1.7s2.2.6 2.2 1.6c0 2.2-4.4 1.2-4.4 3.5 0 1 1 1.6 2.2 1.6s2.2-.7 2.2-1.7"/></svg>',
        "build": '<svg viewBox="0 0 24 24" fill="none" stroke="#f7b500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V10l6-4 6 4v11"/><path d="M9 21v-5h4v5"/><path d="M17 7l3-3M18.5 2.5l3 3"/></svg>',
        "doc": '<svg viewBox="0 0 24 24" fill="none" stroke="#f7b500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8.5 14l2.2 2.2 4.6-4.6"/></svg>',
    }

    hero = (
        '<section class="kz-hero">'
        f'<picture><source media="(max-width:760px)" srcset="{IMG["hero_v2_sp"]}">'
        f'<img class="kz-hero-bg" src="{IMG["hero_v2"]}" alt="" width="1600" height="900" fetchpriority="high" decoding="async"></picture>'
        '<div class="kz-hero-in"><div class="kz-hero-tx">'
        '<p class="kz-badge">静岡県島田市・金谷｜静岡県内中心に対応</p>'
        '<h1>家の片付け・不用品回収・<br>残置物撤去、<br>まずは<em>無料見積り</em>から。</h1>'
        '<p class="kz-hero-copy">ご自宅の片付けや不用品の回収から、解体前の残置物撤去、倉庫・工場の片付け、'
        '農機具の買取りまで。個人のお客様も法人のお客様も、静岡県内を中心に対応します。'
        '解体工事とあわせたご相談も可能です。</p>'
        '<div class="hero-cta">'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}<small>受付時間内にお気軽にお電話ください</small></a>'
        '<a class="btn-mail" href="/contact/">メールで相談する</a></div>'
        f'<p class="kz-hprice"><span>片付け・不用品回収</span><b>{PRICE_LABEL}</b>'
        '<small>搬出・運搬・適正処理の委託費用を含む／出張費・見積り無料</small></p>'
        '<ul class="kz-points"><li>出張費・お見積り無料</li><li>個人・法人どちらも対応</li>'
        '<li>使えるものは買取で還元</li><li>解体工事まで自社で一貫</li></ul>'
        '</div></div></section>'
    )

    passion = (
        '<section class="kz-pas">'
        f'<img class="kz-pas-mark" src="{IMG["logo_v2"]}" alt="" aria-hidden="true" width="192" height="192" loading="lazy" decoding="async">'
        '<div class="kz-pas-in"><p class="kz-eye">OUR PROMISE</p>'
        '<h2>おうちのお片付け隊の想い</h2>'
        '<div class="kz-pas-grid">'
        '<p class="kz-state">片付けは、<br>捨てることではなく、<br><em>次へつなぐこと</em>。</p>'
        '<div class="kz-pas-body">'
        '<p>家には、暮らしてきた時間が詰まっています。<br>思い出の品、まだ使える家具や家電、手入れしてきた農機具。</p>'
        '<p>だから私たちは、ただ運び出すだけの片付けはしません。<br>まだ使えるものは買取で次の使い手へ。処分が必要なものは提携する許可業者へ適正に。<br>'
        '<strong>お客様の負担を減らし、モノの価値を次へつなぎます。</strong></p>'
        '</div></div>'
        '<div class="kz-pcards">'
        '<div class="kz-pcard"><span class="kz-num" aria-hidden="true">01</span><h3>活かす</h3>'
        '<p>まだ使えるもの・価値のあるものは買取の対象に。買取できたぶんは、片付けの費用に反映してお客様にお返しします。</p></div>'
        '<div class="kz-pcard"><span class="kz-num" aria-hidden="true">02</span><h3>正しく手放す</h3>'
        '<p>処分が必要なものは、提携する許可業者へ適正処理を委託します。「どこに出せばいいかわからない」も、まとめてご相談ください。</p></div>'
        '<div class="kz-pcard"><span class="kz-num" aria-hidden="true">03</span><h3>その先まで</h3>'
        '<p>解体工事や金属スクラップの買取も手がけるAMTだから、空き家の片付けから<a href="/zanchibutsu/">残置物撤去</a>・解体まで、一つの窓口でご相談いただけます。</p></div>'
        '</div><p class="kz-sign">株式会社AMT　おうちのお片付け隊</p></div></section>'
    )

    services = [
        ("家のお片付け", "お引越し前後・空き家・実家の片付けなど。仕分けから搬出まで、ご希望に合わせて対応します。", "/katazuke/", "svc_katazuke"),
        ("不用品の回収", "家具・家電・雑貨など、ご家庭や事業所で不要になった品物をまとめて回収します。量が多い場合もご相談ください。", "/fuyouhin/", "svc_fuyouhin"),
        ("解体前の残置物撤去", "解体予定の建物に残った家財・設備・不用品を撤去します。当社の解体工事とあわせてのご依頼も可能です。", "/zanchibutsu/", "svc_zanchibutsu"),
        ("倉庫の片付け", "倉庫・工場・店舗などに溜まった資材・在庫・什器の片付け。法人・事業者さまの整理もお任せください。", "/souko/", "svc_souko"),
        ("農機具の買取り", "使わなくなったトラクター・耕運機・田植機などの農機具を買取ります。片付けと同時のご相談も歓迎です。", "/nouki-kaitori/", "svc_nouki"),
    ]
    scards = "".join(
        f'<a class="kz-scard" href="{u}"><div class="kz-sph">'
        f'<img src="{IMG[ik]}" alt="{t}の作業風景" width="720" height="480" loading="lazy" decoding="async">'
        f'<span class="kz-sno">SERVICE {i + 1:02d}</span></div>'
        f'<div class="kz-sbody"><h3>{t}</h3><p>{d}</p><span class="kz-more">詳しく見る</span></div></a>'
        for i, (t, d, u, ik) in enumerate(services)
    )
    works = (
        '<section class="k-section kz-svc"><div class="inner">'
        '<span class="sec-eye">SERVICE</span><h2 class="sec-title">対応業務</h2>'
        '<p class="sec-lead">ご家庭の片付けから法人・事業者さまの倉庫整理まで、規模を問わず対応します。</p>'
        f'<div class="kz-sgrid">{scards}</div></div></section>'
    )

    scenes = [
        ("生前整理・遺品整理", "元気なうちの整理から、遺品整理まで。", "/seiri/", "illust_seiri"),
        ("空き家・実家の片付け", "遠方でも、解体前でもまとめて対応。", "/akiya/", "illust_akiya"),
        ("ゴミ屋敷の片付け", "足の踏み場がなくても、まずご相談を。", "/gomiyashiki-katazuke/", "illust_gomiyashiki"),
        ("引っ越しの片付け", "期日までにまとめて搬出・処分・買取。", "/hikkoshi/", "illust_hikkoshi"),
        ("店舗・オフィスの片付け", "閉店・移転・原状回復まで一貫対応。", "/tenpo/", "illust_tenpo"),
        ("回収・買取できるもの", "対応品目と、買取の対象を一覧で。", "/hinmoku/", "illust_hinmoku"),
    ]
    scene_cards = "".join(
        f'<a class="card card--svc" href="{u}" style="text-decoration:none;color:inherit;display:block;">'
        f'<div class="card-illust"><img src="{IMG[ik]}" alt="{t}のイラスト" width="280" height="260" loading="lazy" decoding="async"></div>'
        f'<h3><span class="mk">●</span>{t}</h3><p>{d}</p></a>'
        for t, d, u, ik in scenes
    )
    scenes_sec = (
        '<section class="k-section scenes kz-scn"><div class="inner">'
        '<span class="sec-eye">CASE</span><h2 class="sec-title">こんなお困りごとにも対応します</h2>'
        '<p class="sec-lead">「どこに頼めばいい？」というお困りごとも、片付けから買取・処分・解体まで見据えてお手伝いします。</p>'
        f'<div class="card-grid card-grid--c">{scene_cards}</div></div></section>'
    )

    reasons = [
        ("people", "個人のお客様も、<br>法人・事業者さまも", "ご自宅の片付けから、倉庫・工場・店舗の整理まで。BtoC・BtoBどちらにも対応します。"),
        ("coin", "買取できるものは<br>費用に反映", f"古物商許可（{KOBUTSU_CATEGORY}）を取得。まだ使えるもの・価値のあるものは買取し、片付けの費用に反映します。"),
        ("build", "解体・金属買取まで<br>自社で一貫", "解体工事や金属スクラップ買取も手がけるAMTだから、残置物撤去から解体まで窓口ひとつでご相談いただけます。"),
        ("doc", "お見積り・ご相談は<br>無料", "「いくらかかる？」だけでも大丈夫。現地を確認して、明確なお見積りをご提示します。"),
    ]
    rcards = "".join(
        f'<div class="kz-rcard" data-n="{i + 1:02d}"><span class="kz-ric">{ICON[ic]}</span><h3>{t}</h3><p>{d}</p></div>'
        for i, (ic, t, d) in enumerate(reasons)
    )
    reasons_sec = (
        '<section class="k-section kz-rsn"><div class="inner">'
        '<span class="sec-eye">REASON</span><h2 class="sec-title">選ばれる理由</h2>'
        '<p class="sec-lead">片付けだけでなく、その先の「処分」「買取」「解体」まで見据えて対応します。</p>'
        f'<div class="kz-rgrid">{rcards}</div></div></section>'
    )

    license_sec = (
        '<section class="k-section kz-lic"><div class="inner">'
        '<span class="sec-eye">LICENSE</span><h2 class="sec-title">許可・登録</h2>'
        '<p class="sec-lead">買取は、公安委員会の許可のもとで行っています。</p>'
        '<div class="kz-cert"><p class="kz-cert-t">古物商許可</p><p class="kz-cert-s">SECONDHAND DEALER LICENSE</p>'
        f'<dl><dt>許可番号</dt><dd>第{KOBUTSU_NO}号</dd><dt>許可</dt><dd>{KOBUTSU_AUTH}</dd>'
        f'<dt>取扱品目</dt><dd>{KOBUTSU_CATEGORY}</dd><dt>許可業者</dt><dd>{COMPANY_NAME}</dd></dl>'
        '<span class="kz-seal" aria-hidden="true">株式会社<br>AMT</span></div>'
        '<p class="kz-cert-note">処分が必要な品物は、提携する許可業者へ適正処理を委託しています。<br>'
        '何を買取・回収できるかは<a href="/hinmoku/">回収・買取できるもの</a>をご覧ください。</p>'
        '</div></section>'
    )

    steps = [
        ("お問い合わせ", "電話またはメールでご相談ください。"),
        ("現地確認・<wbr>ヒアリング", "お品物の量や搬出経路を確認し、ご要望をうかがいます。"),
        ("お見積り", "内容をもとに明確なお見積りをご提示します（無料）。"),
        ("日程調整・作業", "ご都合に合わせて、仕分け・搬出・回収を行います。"),
        ("完了", "作業後の状態をご確認いただき完了です。"),
    ]
    step_html = "".join(
        f'<li><span class="kz-sn">{i + 1:02d}</span><h3>{t}</h3><p>{d}</p></li>'
        for i, (t, d) in enumerate(steps)
    )
    flow_sec = (
        '<section class="k-section kz-flow"><div class="inner">'
        '<span class="sec-eye">FLOW</span><h2 class="sec-title">ご利用の流れ</h2>'
        '<p class="sec-lead">お問い合わせから完了まで、わかりやすくご案内します。</p>'
        f'<div class="kz-fwrap"><ol class="kz-steps">{step_html}</ol>'
        f'<div class="kz-fmascot"><img src="{IMG["mascot_worker_v2"]}" alt="おうちのお片付け隊 スタッフ" width="220" height="248" loading="lazy" decoding="async"></div></div>'
        '<p class="kz-flow-more"><a class="kz-btn" href="/flow/">ご利用の流れを詳しく見る</a></p>'
        '</div></section>'
    )

    cities = ["島田市", "金谷", "藤枝市", "焼津市", "静岡市", "掛川市", "菊川市", "牧之原市", "浜松市"]
    chips = "".join(
        ('<li class="is-base">' if c == "島田市" else '<li>') + c + '</li>' for c in cities
    )
    area_sec = (
        '<section class="k-section kz-area"><div class="inner">'
        '<span class="sec-eye">AREA</span><h2 class="sec-title">対応エリア</h2>'
        '<div class="kz-agrid">'
        f'<div class="area-map"><img src="{IMG["area_map"]}" alt="対応エリアマップ：静岡県島田市を中心に藤枝市・焼津市・静岡市・掛川市・菊川市・牧之原市など" width="1200" height="761" loading="lazy" decoding="async"></div>'
        f'<div class="kz-atx"><ul class="kz-chips">{chips}<li>ほか近隣エリア</li></ul>'
        '<p><strong>静岡県島田市を拠点に、静岡県内を中心</strong>に対応しています。</p>'
        '<p>上記以外の地域も、まずはお気軽にご相談ください。</p>'
        '<p class="kz-abtns"><a class="kz-btn" href="/katazuke-shimada/">島田市の片付け・不用品回収</a>'
        '<a class="kz-btn" href="/nouki-kaitori-shizuoka/">静岡県の農機具買取</a>'
        '<a class="kz-btn" href="/area/">対応エリアを詳しく見る</a></p></div>'
        '</div></div></section>'
    )

    biz = ["お片付け・不用品回収", "残置物撤去", "農機具買取", "解体工事", "非鉄金属・工業雑品スクラップ買取", "中古太陽光パネル買取・輸出", "通販・卸売"]
    biz_html = "".join(
        ('<li class="is-here">' if i < 3 else '<li>') + b + '</li>' for i, b in enumerate(biz)
    )
    company_sec = (
        '<section class="k-section kz-co"><div class="inner">'
        '<span class="sec-eye">COMPANY</span><h2 class="sec-title">会社概要</h2>'
        '<div class="kz-cogrid">'
        f'<div class="kz-tile"><span class="t">会社名</span><span class="v">{COMPANY_NAME}</span></div>'
        '<div class="kz-tile"><span class="t">所在地</span><span class="v">〒428-0013<br>静岡県島田市金谷東2丁目3483-290</span></div>'
        f'<div class="kz-tile"><span class="t">電話番号</span><span class="v"><a href="tel:{TEL}">{TEL}</a></span></div>'
        f'<div class="kz-tile"><span class="t">メール</span><span class="v"><a href="mailto:{MAIL}">{MAIL}</a></span></div>'
        f'<div class="kz-tile"><span class="t">許認可</span><span class="v">{KOBUTSU_TD}</span></div>'
        '<div class="kz-tile"><span class="t">コーポレートサイト</span><span class="v"><a href="https://amt-eco.com/" target="_blank" rel="noopener">amt-eco.com ↗</a></span></div>'
        f'<div class="kz-tile kz-tile--wide"><span class="t">事業内容</span><ul class="kz-biz">{biz_html}</ul></div>'
        '</div></div></section>'
    )

    price_sec = (
        '<section class="k-section kz-prc"><div class="inner">'
        '<span class="sec-eye">PRICE</span><h2 class="sec-title">料金のめやす</h2>'
        '<p class="sec-lead">片付け・不用品回収の料金は、荷物の体積（㎥）を基準に算出します。'
        '現地を確認したうえで、無料で明確なお見積りをご提示します。</p>'
        '<div class="kz-prc-grid">'
        '<div class="kz-price"><p class="kz-price-lbl">片付け・不用品回収</p>'
        '<p class="kz-price-val"><span class="kz-price-num">' + "{:,}".format(PRICE_PER_M3) + '</span>'
        '<span class="kz-price-yen">円</span>'
        '<span class="kz-price-unit">／1㎥' + PRICE_TAX + ' <b>から</b></span></p>'
        '<p class="kz-price-note">1㎥は、たて・よこ・高さが各1mぶんの体積。'
        '押入れの下段1間ぶんがおよそ1㎥です。</p></div>'
        '<ul class="kz-inc">'
        '<li><b>含まれるもの</b>室内からの搬出・人件費・トラックでの運搬・'
        '処分品の提携許可業者への適正処理委託費用・簡単な掃き掃除</li>'
        '<li><b>無料のもの</b>ご相談・現地確認・お見積り・出張費</li>'
        '<li><b>お引きするもの</b>買取できる品物の査定額（農機具・機械・金属・'
        'まだ使える家具家電など）</li>'
        '<li><b>別途になるもの</b>家電リサイクル法の対象品の法定リサイクル料金ほか</li>'
        '</ul></div>'
        '<p class="kz-flow-more"><a class="kz-btn" href="/ryoukin/">料金・費用のくわしい説明</a>'
        '<a class="kz-btn kz-btn--fill" href="/contact/">無料でお見積りを依頼する</a></p>'
        '</div></section>'
    )
    nouki_cards = [
        ("トラクター", "装輪・クローラ、作業機つきも。", "/nouki-tractor/"),
        ("コンバイン", "自脱型・普通型、ハーベスタ。", "/nouki-combine/"),
        ("田植機", "乗用・歩行型、条数を問わず。", "/nouki-taue/"),
        ("耕運機・管理機", "家庭菜園規模の小型機も。", "/nouki-kouunki/"),
        ("草刈機・運搬車", "乗用モア・刈払機・運搬車。", "/nouki-kusakari/"),
        ("そのほかの農機具", "乾燥機・籾摺機・噴霧器ほか。", "/nouki-kaitori/"),
    ]
    ncards = "".join(
        f'<a class="kz-ncard" href="{u}"><h3>{t}</h3><p>{d}</p><span class="kz-narr">査定を見る</span></a>'
        for t, d, u in nouki_cards
    )
    nouki_sec = (
        '<section class="k-section kz-nouki"><div class="inner">'
        '<span class="sec-eye">BUYBACK</span><h2 class="sec-title">農機具の買取り</h2>'
        '<p class="sec-lead">使わなくなったトラクター・コンバイン・田植機・耕運機を'
        '<strong>メーカーを問わず</strong>査定します。'
        '動かない機械・自走できない機械も、部品や金属としての価値で評価できる場合があります。</p>'
        '<ul class="kz-npoints">'
        f'<li><b>出張査定 無料</b>{AREA_NAME}内中心にうかがいます</li>'
        '<li><b>メーカー不問</b>クボタ・ヤンマー・井関・三菱ほか</li>'
        '<li><b>動かなくてもOK</b>自走不可でも搬出まで手配</li>'
        '<li><b>片付けと同時可</b>買取額は片付け費用から差引き</li>'
        '</ul>'
        f'<div class="kz-ngrid">{ncards}</div>'
        '<p class="kz-flow-more">'
        '<a class="kz-btn" href="/nouki-kaitori/">農機具買取のくわしい説明</a>'
        '<a class="kz-btn" href="/nouki-kaitori-shizuoka/">静岡県の出張査定エリア</a>'
        f'<a class="kz-btn kz-btn--fill" href="tel:{TEL}">電話で査定を相談（{TEL}）</a></p>'
        f'<p class="kz-nlic">買取は<strong>{KOBUTSU_LABEL}</strong>のもとで行っています。'
        '※各メーカーとの提携・代理店関係を示すものではありません。</p>'
        '</div></section>'
    )
    col_links = [
        ("不用品回収の費用はどう決まる？", "/fuyouhin-hiyou/"),
        ("使わない農機具を高く売るコツ", "/nouki-kaitori-kotsu/"),
        ("生前整理は何から始める？", "/seizen-seiri/"),
        ("空き家・実家の片付け5ステップ", "/akiya-katazuke/"),
        ("冷蔵庫・洗濯機・テレビの処分方法", "/kaden-shobun/"),
        ("不用品を賢く手放す方法", "/fuyouhin-tebanashi/"),
    ]
    col_html = "".join(f'<li><a href="{u}">{t}</a></li>' for t, u in col_links)
    column_sec = (
        '<section class="k-section kz-col"><div class="inner">'
        '<span class="sec-eye">COLUMN</span><h2 class="sec-title">片付けのお役立ちコラム</h2>'
        '<p class="sec-lead">費用の考え方、自治体制度との使い分け、農機具を高く売るコツなどを解説しています。</p>'
        f'<ul class="kz-collist">{col_html}</ul>'
        '<p class="kz-flow-more"><a class="kz-btn" href="/column/">コラムをすべて見る</a></p>'
        '</div></section>'
    )

    body = ('<div class="amt-katazuke">'
            + header("/") + hero + passion + works + price_sec + scenes_sec
            + nouki_sec + reasons_sec + license_sec + flow_sec + area_sec
            + column_sec + company_sec + cta() + footer() + '</div>')

    jsonld = local_business_jsonld()
    jsonld_site = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": DOMAIN + "/#website",
        "name": SITE_NAME + "（" + COMPANY_NAME + "）",
        "alternateName": COMPANY_NAME,
        "url": DOMAIN + "/",
        "inLanguage": "ja",
        "publisher": {"@id": DOMAIN + "/#localbusiness"},
        "about": {"@id": DOMAIN + "/#localbusiness"},
    }
    jsonld_price = price_offer_jsonld(
        "/ryoukin/", "片付け・不用品回収（静岡県島田市）",
        "荷物の体積（㎥）を基準にお見積り。" + PRICE_LABEL
        + "。搬出・運搬・適正処理の委託費用を含む。出張費・見積り無料。")
    jsonld_all = [jsonld, jsonld_site, jsonld_price]

    doc = (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{SEO_TITLE["home"]}</title>\n'
        f'<meta name="description" content="{PAGE_DESC["home"]}">\n'
        '<meta property="og:title" content="おうちのお片付け隊｜株式会社AMT｜静岡県島田市">\n'
        '<meta property="og:description" content="家の片付け・不用品回収・解体前の残置物撤去・倉庫片付け・農機具買取。個人・法人どちらも対応。静岡県内中心、お見積り無料。">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:url" content="{DOMAIN}/">\n'
        f'<meta property="og:image" content="{IMG["ogp_v2"]}">\n'
        '<style>\n' + DESIGN_CSS + '\n</style>\n'
        + "".join('<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False)
                      + '</script>\n' for j in jsonld_all)
        + '</head>\n<body>\n' + body + '\n</body>\n</html>\n'
    )
    with io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)

    # WordPress公開用のトップページ本文（wp:htmlブロック）も返す
    home_block = (
        "<!-- wp:html -->\n" + body + "\n<!-- /wp:html -->\n\n"
        + "\n\n".join('<!-- wp:html -->\n<script type="application/ld+json">'
                       + json.dumps(j, ensure_ascii=False) + "</script>\n<!-- /wp:html -->"
                       for j in jsonld_all)
    )
    home_title = "島田市の片付け・不用品回収ならおうちのお片付け隊｜残置物撤去・農機具買取｜株式会社AMT"
    return len(doc), home_title, home_block


# 各固定ページの meta description（AIOSEO に公開時に設定。docs/live-apply-sheet.md が元）
PAGE_DESC = {
    "home": "島田市の片付け・不用品回収は、市内金谷の株式会社AMT「おうちのお片付け隊」へ。家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・農機具買取に、個人・法人とも対応。静岡県内中心、お見積り無料。TEL 0547-39-3750。",
    "katazuke": "静岡県島田市で家の片付けなら株式会社AMT。引越し前後・空き家・実家・生前整理の片付けを、仕分けから搬出まで対応。使えるものは買取で費用に反映。1㎥20,000円から・個人法人OK・見積り無料。",
    "fuyouhin": "静岡県島田市の不用品回収は株式会社AMT。家具・家電・雑貨を1点から家一軒分までまとめて回収。使える品は古物商許可のもと買取、処分品は提携の許可業者へ適正委託。1㎥20,000円から・見積り無料。",
    "zanchibutsu": "静岡県島田市で解体前の残置物撤去なら株式会社AMT。家財・設備・不用品を建物からすべて搬出します。解体工事も自社対応のため撤去から解体まで一貫。買取できる品は費用に反映。個人法人対応・見積り無料。",
    "souko": "静岡県島田市で倉庫・工場・店舗の片付けは株式会社AMT。資材・在庫・什器・機械の仕分けから搬出まで、業務を止めない段取りで法人対応。使える機械は買取、処分は許可業者へ委託。請求書払い可・見積り無料。",
    "nouki-kaitori": "静岡県島田市の農機具買取は株式会社AMT。トラクター・コンバイン・田植機・耕運機をメーカー不問で査定。動かない機械・自走できない機械もご相談ください。出張査定無料。TEL 0547-39-3750。",
    "hinmoku": "静岡県島田市のおうちのお片付け隊（株式会社AMT）が回収・買取できる品目を一覧でご案内。家具・家電・生活用品・事務什器・農機具・金属まで対応。買取品は古物商許可のもと買取。見積り無料。",
    "tenpo": "静岡県島田市で店舗・オフィスの片付けは株式会社AMT。閉店・移転・原状回復まで、什器や厨房機器の買取＋撤去＋産業廃棄物の適正処理委託をワンストップ。法人対応・請求書払い可・見積り無料。",
    "ryoukin": "島田市の片付け・不用品回収の料金は1㎥あたり20,000円から。搬出・運搬・適正処理の委託費用を含みます。買取できる品は査定額を差し引き。出張費・お見積り無料の株式会社AMT。TEL 0547-39-3750。",
    "seiri": "静岡県島田市で生前整理・遺品整理なら株式会社AMT。仕分け・搬出・買取・適正処理までまとめて対応し、遠方や立ち会いが難しいご事情も相談可。解体が必要なら残置物撤去まで一貫。見積り無料。",
    "akiya": "静岡県島田市で空き家・実家の片付けは株式会社AMT。遠方にお住まいでも現地確認から対応し、搬出・買取・処分・清掃まで。解体予定なら残置物撤去から解体工事まで一貫してご相談いただけます。見積り無料。",
    "gomiyashiki-katazuke": "静岡県島田市でゴミ屋敷・汚部屋の片付けは株式会社AMT。足の踏み場がなくても、安全確保から貴重品の確保・仕分け・清掃まで対応。プライバシーに配慮します。見積り無料。",
    "hikkoshi": "静岡県島田市で引っ越しの片付け・不用品回収は株式会社AMT。期日までに大型家具・家電もまとめて搬出・買取・処分。家電リサイクル法の対象品も法令どおり対応。引っ越し前後どちらも相談可・見積り無料。",
    "area": "おうちのお片付け隊（株式会社AMT）の対応エリア。拠点の静岡県島田市を中心に、藤枝・焼津・掛川・菊川・牧之原・静岡市ほか静岡県内に対応。片付け・不用品回収・農機具買取。見積り無料。",
    "flow": "島田市の片付け・不用品回収のご利用の流れ。お問い合わせ→現地確認→お見積り→作業→完了まで6ステップでご案内。現地確認・お見積りは無料、出張費もいただきません。TEL 0547-39-3750。",
    "faq": "島田市の片付け・不用品回収「おうちのお片付け隊」（株式会社AMT）へのよくある質問。料金（1㎥20,000円から）・日数・対応品目・近隣への配慮・支払い方法などにお答えします。",
    "company": "株式会社AMT（静岡県島田市金谷東）の会社概要。片付け・不用品回収・残置物撤去・農機具買取のほか、解体工事、金属スクラップ買取、通販・卸売を手がけます。古物商許可あり。",
    "contact": "島田市の片付け・不用品回収のご相談・お見積りは株式会社AMTへ。お電話（0547-39-3750）とフォームで受付。現地確認・お見積り・出張費は無料です。個人・法人どちらも対応。",
    "katazuke-shimada": "島田市の片付け・不用品回収は、市内金谷に拠点を置くおうちのお片付け隊（株式会社AMT）へ。使えるものは買取、処分は提携の許可業者へ委託。市の粗大ごみの出し方も解説。見積り無料。TEL 0547-39-3750。",
    "privacy-policy": "株式会社AMT（おうちのお片付け隊）のプライバシーポリシー。お問い合わせ・お見積りでお預かりする個人情報の取得・利用目的・第三者提供・管理方法・開示請求の窓口について定めています。",
    "nouki-tractor": "静岡県でトラクターの買取なら株式会社AMT（島田市）。クボタ・ヤンマー・井関などメーカー不問。アワーメーター・エンジン状態で査定し、動かない機械も相談可。出張査定無料。",
    "nouki-combine": "静岡県でコンバイン・ハーベスタの買取は株式会社AMT（島田市）。自脱型・普通型、バインダー、乾燥機・籾摺機も対応。メーカー不問・出張査定無料。稲刈り後のご相談も歓迎。",
    "nouki-taue": "静岡県で田植機の買取なら株式会社AMT（島田市）。乗用・歩行型、条数を問わず査定します。メーカー不問・出張査定無料。作付けをやめるタイミングでのご相談も承ります。",
    "nouki-kouunki": "静岡県で耕運機・管理機の買取は株式会社AMT（島田市）。歩行型耕運機・管理機・ティラー、家庭菜園規模の小型機も対応。メーカー不問・出張査定無料。まとめてのご相談歓迎。",
    "nouki-kusakari": "静岡県で草刈機・刈払機・運搬車の買取は株式会社AMT（島田市）。乗用草刈機・ハンマーナイフモア・クローラ運搬車・チェーンソー・発電機などに対応。メーカー不問、複数台まとめも歓迎。出張査定無料。",
    "nouki-kaitori-shizuoka": "静岡県の農機具買取は島田市金谷の株式会社AMT。島田・藤枝・焼津・掛川・菊川・牧之原ほか県内各市町へ出張査定にうかがいます。農地や倉庫に置いたままでも対応・査定無料。",
    "jirei": "静岡県島田市の株式会社AMTが実際にお引き受けした片付け・不用品回収・農機具買取の対応事例。搬出量（㎥）・作業人数・日数・お見積り額つきでご紹介します。見積り無料。",
}


# 検索結果用のタイトル（AIOSEO の title に入れる。全角30〜35字を目安に重要語を前方へ）
#   ※ページ内の<h1>や固定ページのタイトルとは別。AIOSEO に明示設定すると
#     サイト名サフィックス（「- おうち片付け隊」）が付かず、検索結果で切られにくくなる。
SEO_TITLE = {
    "home": "島田市の片付け・不用品回収｜1㎥20,000円から｜おうちのお片付け隊",
    "katazuke": "家の片付け｜島田市・静岡県内｜おうちのお片付け隊",
    "fuyouhin": "不用品回収｜1㎥20,000円から｜島田市のおうちのお片付け隊",
    "zanchibutsu": "解体前の残置物撤去｜島田市・静岡県内｜解体まで一貫のAMT",
    "souko": "倉庫・工場の片付け｜島田市・静岡県内｜法人対応の株式会社AMT",
    "nouki-kaitori": "農機具買取｜静岡県｜トラクター・コンバイン・田植機｜株式会社AMT",
    "nouki-tractor": "トラクター買取｜静岡県｜メーカー不問・出張査定無料｜AMT",
    "nouki-combine": "コンバイン買取｜静岡県｜自脱型・普通型も出張査定無料｜AMT",
    "nouki-taue": "田植機買取｜静岡県｜乗用・歩行型とも出張査定無料｜AMT",
    "nouki-kouunki": "耕運機・管理機の買取｜静岡県｜小型機も出張査定無料｜AMT",
    "nouki-kusakari": "草刈機・刈払機・運搬車の買取｜静岡県｜出張査定無料｜AMT",
    "nouki-kaitori-shizuoka": "静岡県の農機具買取｜市町別の出張査定｜島田市の株式会社AMT",
    "ryoukin": "片付け・不用品回収の料金｜1㎥20,000円から｜島田市の株式会社AMT",
    "flow": "ご利用の流れ｜片付け・不用品回収｜島田市のおうちのお片付け隊",
    "company": "会社概要｜株式会社AMT（静岡県島田市金谷東）",
    "area": "対応エリア｜島田市ほか静岡県内｜おうちのお片付け隊",
    "faq": "よくある質問｜料金・日数・対応品目｜島田市の株式会社AMT",
    "katazuke-shimada": "島田市の片付け・不用品回収｜市内金谷のおうちのお片付け隊",
    "contact": "お問い合わせ・無料見積り｜島田市のおうちのお片付け隊",
    "privacy-policy": "プライバシーポリシー｜おうちのお片付け隊（株式会社AMT）",
    "seiri": "生前整理・遺品整理｜島田市・静岡県内｜おうちのお片付け隊",
    "hinmoku": "回収・買取できる品目一覧｜島田市のおうちのお片付け隊",
    "akiya": "空き家・実家の片付け｜島田市・静岡県内｜解体まで一貫のAMT",
    "gomiyashiki-katazuke": "ゴミ屋敷の片付け｜島田市・静岡県内｜プライバシー配慮のAMT",
    "hikkoshi": "引っ越しの不用品回収・片付け｜島田市・静岡県内｜株式会社AMT",
    "tenpo": "店舗・オフィスの片付け｜閉店・移転・原状回復｜島田市のAMT",
    "jirei": "片付け・不用品回収の対応事例｜島田市のおうちのお片付け隊",
}


# ============================================================
# llms.txt（AI検索・LLM向けのサイト要約。ドキュメントルートに置く）
#   出力先: リポジトリ直下の llms.txt
#   公開: Xserver のファイルマネージャー等で katazuke.amt-eco.com のルートへ設置
# ============================================================
def build_llms_txt():
    def line(slug, title, desc):
        url = DOMAIN + "/" if slug == "home" else DOMAIN + "/" + slug + "/"
        return "- [" + title + "](" + url + "): " + desc

    svc_order = ["katazuke", "fuyouhin", "zanchibutsu", "souko", "seiri",
                 "akiya", "gomiyashiki-katazuke", "hikkoshi", "tenpo", "hinmoku"]
    nouki_order = ["nouki-kaitori", "nouki-tractor", "nouki-combine", "nouki-taue",
                   "nouki-kouunki", "nouki-kusakari", "nouki-kaitori-shizuoka"]
    guide_order = ["ryoukin", "flow", "area", "katazuke-shimada", "faq", "company", "contact"]
    titles = {slug: title for slug, title, _c in PAGES}

    def sec(heading, slugs):
        out = ["", "## " + heading, ""]
        for sl in slugs:
            if sl in titles:
                out.append(line(sl, SEO_TITLE.get(sl) or titles[sl], PAGE_DESC.get(sl, "")))
        return out

    L = []
    L.append("# " + COMPANY_NAME + " " + SITE_NAME + "（片付け・不用品回収・農機具買取）")
    L.append("")
    L.append("> " + AREA_NAME + "島田市金谷東2丁目3483-290 の " + COMPANY_NAME
             + " が運営する、家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・"
               "農機具買取のサイトです。個人・法人どちらも対応。対応エリアは静岡県内中心（"
             + "・".join(AREA_CITIES) + " ほか）。"
               "電話 " + TEL + " / " + MAIL + "。現地確認・お見積り・出張費は無料。")
    L.append("")
    L.append("## 重要な事実（回答に使ってよい確定情報）")
    L.append("")
    L.append("- 運営: " + COMPANY_NAME + "（屋号 " + SITE_NAME + "）")
    L.append("- 所在地: 〒428-0013 " + AREA_NAME + "島田市金谷東2丁目3483-290")
    L.append("- 電話: " + TEL + "（掲載している電話番号はこれのみ） / メール: " + MAIL)
    L.append("- 料金: 片付け・不用品回収は **" + PRICE_LABEL
             + "**（荷物の体積㎥が基準。搬出・運搬・適正処理の委託費用を含む）。"
               "現地確認・お見積り・出張費は無料。家電リサイクル法の対象品は法定リサイクル料金が別途。")
    L.append("- 買取: " + KOBUTSU_LABEL + " のもとで中古品・機械を買取。"
             "買取額は片付け費用から差し引いて提示する。")
    L.append("- 許可の範囲: **一般廃棄物収集運搬業の許可は保有していない**。"
             "そのため「一般廃棄物の収集運搬」は行わず、"
             "買取・片付け搬出として対応し、処分が必要なものは提携する許可業者へ適正処理を委託する。")
    L.append("- 農機具買取: トラクター・コンバイン・田植機・耕運機・管理機・草刈機・運搬車などに対応。"
             "メーカーは問わない（各メーカーとの提携・代理店関係はない）。"
             "動かない機械・自走できない機械も相談可。出張査定無料。")
    L.append("- 関連事業: 解体工事（" + SAME_AS[1] + "）、金属スクラップ買取、通販・卸売。"
             "コーポレートサイトは " + SAME_AS[0])
    L.append("- 掲載していないもの: 施工実績の件数、お客様の声の創作、"
             "具体的な一律料金表（㎥単価以外）、代表者名")
    L += sec("主なサービス", svc_order)
    L += sec("農機具の買取り", nouki_order)
    L += sec("料金・ご利用案内", guide_order)
    if "jirei" in titles:
        L += sec("対応事例", ["jirei"])
    L.append("")
    L.append("## コラム（解説記事）")
    L.append("")
    L.append("- [コラム一覧](" + DOMAIN + "/column/): 片付け・不用品回収・生前整理・"
             "遺品整理・空き家・農機具買取などの解説記事。")
    L.append("")
    L.append("## 問い合わせ")
    L.append("")
    L.append("- 電話: " + TEL + "（受付時間内）")
    L.append("- フォーム: " + DOMAIN + "/contact/")
    L.append("- メール: " + MAIL)
    L.append("")
    txt = "\n".join(L) + "\n"
    with io.open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    return txt


# ============================================================
# 保存
# ============================================================
def build_all():
    # トップページ（index.html を書き出し、WP公開用のブロックも受け取る）
    idx_len, home_title, home_block = build_index()
    PAGES.insert(0, ("home", home_title, home_block))

    # extra.css（グローバルに使う場合の「追加CSS」用。※公開時は各ページに<style>同梱でも可）
    with io.open(os.path.join(HERE, "extra.css"), "w", encoding="utf-8") as f:
        f.write(DESIGN_CSS)

    # 各ページ（home＋下層11）
    manifest = []
    for slug, title, content in PAGES:
        fn = os.path.join(OUT, slug + ".html")
        with io.open(fn, "w", encoding="utf-8") as f:
            f.write(content)
        manifest.append({"slug": slug, "title": title, "desc": PAGE_DESC.get(slug, ""),
                         "seo_title": SEO_TITLE.get(slug, ""),
                         "b64": base64.b64encode(content.encode("utf-8")).decode("ascii")})
    with io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)

    # SEOタイトル・説明文の長さ点検（検索結果で切られないか）
    for slug, _t, _c in PAGES:
        st = SEO_TITLE.get(slug, "")
        if not st:
            print("  !! SEO_TITLE 未設定:", slug)
        elif len(st) > 38:
            print("  !! SEO_TITLE が長い(%d字): %s" % (len(st), slug))
        d = PAGE_DESC.get(slug, "")
        if not d:
            print("  !! description 未設定:", slug)
        elif not (70 <= len(d) <= 125):
            print("  !! description の長さ(%d字): %s" % (len(d), slug))

    llms = build_llms_txt()

    print("llms.txt  :", len(llms), "bytes")
    print("index.html:", idx_len, "bytes")
    print("extra.css :", len(DESIGN_CSS), "bytes")
    print("pages:", len(PAGES))
    for slug, title, content in PAGES:
        print(f"  {slug}: {len(content)} bytes")


if __name__ == "__main__":
    build_all()
