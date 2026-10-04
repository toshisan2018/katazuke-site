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
    ("/nouki-kaitori/", "農機具買取"),
    ("/seiri/", "生前整理・遺品整理"),
    ("/ryoukin/", "料金・費用"),
    ("/column/", "コラム"),
    ("/faq/", "よくある質問"),
    ("/company/", "会社概要"),
    ("/flow/", "ご利用の流れ"),
    ("/area/", "対応エリア"),
    ("/contact/", "お問い合わせ"),
]

# フッターの2カラム分（サービス／ご案内）のリンク
FOOT_SERVICE = [
    ("/katazuke/", "家の片付け"),
    ("/fuyouhin/", "不用品の回収"),
    ("/zanchibutsu/", "解体前の残置物撤去"),
    ("/souko/", "倉庫の片付け"),
    ("/nouki-kaitori/", "農機具の買取り"),
    ("/seiri/", "生前整理・遺品整理"),
    ("/akiya/", "空き家・実家の片付け"),
    ("/gomiyashiki-katazuke/", "ゴミ屋敷の片付け"),
    ("/hikkoshi/", "引っ越しの片付け"),
    ("/tenpo/", "店舗・オフィスの片付け"),
    ("/hinmoku/", "対応品目一覧"),
    ("/ryoukin/", "料金・費用について"),
]
FOOT_GUIDE = [
    ("/flow/", "ご利用の流れ"),
    ("/area/", "対応エリア"),
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
        '<header class="k-header"><div class="hdr-topbar"></div>'
        '<div class="header-inner">'
        f'<a class="logo" href="/"><span class="logo-mark"><img src="{IMG["logo_v2"]}" alt="おうちのお片付け隊 ロゴ" width="64" height="64"></span>'
        f'<span class="logo-tx"><span class="logo-name"><b>{COMPANY_NAME}</b> {SITE_NAME}</span>'
        f'<small>{CATCH}</small></span></a>'
        f'<div class="header-tel"><a class="tel-btn" href="tel:{TEL}">{TEL_ICON}TEL {TEL}</a>'
        '<small>お見積り・ご相談無料</small></div></div></header>'
        '<nav class="k-nav"><input type="checkbox" id="amtnav" class="amt-navtoggle">'
        '<label class="amt-navbtn" for="amtnav"><span class="bars"><i></i></span>メニュー</label>'
        f'<ul>{lis}</ul></nav>'
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
    gui = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_GUIDE)
    return (
        '<footer class="k-footer"><div class="foot-inner">'
        '<div class="foot-col foot-about">'
        f'<div class="foot-logo"><img src="{IMG["logo_v2"]}" alt="" width="44" height="44" loading="lazy" decoding="async"><span class="fl-tx"><span>{COMPANY_NAME}</span> {SITE_NAME}</span></div>'
        '<p>静岡県島田市を拠点に、家の片付け・不用品回収・解体前の残置物撤去・'
        '倉庫の片付け・農機具の買取りまで対応します。個人のお客様も法人・事業者さまも、'
        'お見積り・ご相談は無料です。</p></div>'
        f'<div class="foot-col"><p class="foot-h">サービス</p><ul>{svc}</ul></div>'
        f'<div class="foot-col"><p class="foot-h">ご案内</p><ul>{gui}</ul></div>'
        '<div class="foot-col foot-contact"><p class="foot-h">お問い合わせ</p>'
        f'<a class="foot-tel" href="tel:{TEL}">{TEL}</a>'
        '<p class="foot-note">お見積り・ご相談は無料</p>'
        '<a class="foot-mail" href="/contact/">メールで相談する</a>'
        '<p class="foot-addr">〒428-0013<br>静岡県島田市金谷東2丁目3483-290</p>'
        '<p class="foot-corp"><a href="https://amt-eco.com/" target="_blank" rel="noopener">'
        'コーポレートサイト ↗</a></p></div></div>'
        '<div class="foot-bottom"><p><a href="/privacy-policy/">プライバシーポリシー</a>'
        '　｜　&copy; 株式会社AMT All Rights Reserved.</p></div></footer>'
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
# 5. 農機具の買取り
# ------------------------------------------------------------
add_service_page(
    "nouki-kaitori", "農機具買取",
    "農機具の買取り（トラクター等）｜静岡県島田市の株式会社AMT",
    "使わなくなったトラクター・耕運機・田植機などの農機具を買取ります。片付けと同時のご相談も歓迎。静岡県内中心・査定無料。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">使わなくなった農機具の買取に対応します。'
    '農地の整理や世代交代、農機の入れ替えなどで不要になった機械をご相談ください。'
    '片付け・回収とあわせてまとめて対応できます。</p>'
    '<h2>買取・ご相談の対象になるもの（例）</h2>'
    '<ul><li>トラクター・耕運機・管理機</li>'
    '<li>田植機・コンバイン</li>'
    '<li>草刈機・運搬車などの農業機械</li>'
    '<li>農機具にともなう金属・部品類</li></ul>'
    '<h2>片付けと同時のご相談も歓迎です</h2>'
    '<p>農機具だけでなく、倉庫や納屋の片付けとあわせてのご依頼も承ります。'
    '<a href="/souko/">倉庫の片付け</a>や'
    '<a href="/fuyouhin/">不用品の回収</a>とまとめてご相談いただけます。</p>'
    '<h2>査定・買取について</h2>'
    '<p><strong>古物商許可（静岡県公安委員会）</strong>のもと、中古の農機具の買取に対応します。'
    '買取の可否や金額は、<strong>機種・年式・状態・稼働の可否・市場の相場</strong>などによって変わります。'
    '現物を確認のうえで査定します。動かない機械や古い機械も、'
    'まずは状態をお知らせください。</p>'
    '<p class="note">※すべての農機具を買取できるとは限りません。'
    '買取が難しい場合も、回収・処分としてご相談いただけます。</p>'
    '</div></section>',
    [("古い農機具や動かない機械も買取できますか？",
      "機種・状態によって異なります。動かない機械でも金属・部品として対応できる場合がありますので、まずは状態をお知らせください。"),
     ("出張での査定は可能ですか？",
      "静岡県内を中心に、現地での確認・査定に対応します。まずはお電話またはメールでご相談ください。")],
    [("/souko/", "倉庫の片付け", "納屋・倉庫の整理"),
     ("/fuyouhin/", "不用品の回収", "まとめて回収"),
     ("/katazuke/", "家のお片付け", "住まいの片付け"),
     ("/company/", "会社概要", "株式会社AMTについて")],
    "農機具の買取り", "トラクター・耕運機・田植機などの農機具買取。片付けと同時対応。",
    "農機具の買取り（トラクター等）｜静岡県島田市の株式会社AMT",
    hero_img=IMG["nouki"],
)

# ------------------------------------------------------------
# 6. 料金・費用について
# ------------------------------------------------------------
c, _ = assemble(
    "ryoukin", "料金・費用",
    "片付け・不用品回収の料金｜静岡県島田市｜株式会社AMT",
    "片付け・不用品回収の費用の決まり方と、費用を抑える考え方をご説明します。正確な金額は現地確認のうえ無料でお見積りします。",
    '<section class="k-section"><div class="prose">'
    '<p class="lead">片付け・回収の費用は、品物の量や現場の条件によって変わるため、'
    '一律の料金表ではご案内していません。ここでは費用の決まり方と、'
    '費用を抑えるための考え方をご説明します。正確な金額は現地確認のうえ無料でお見積りします。</p>'
    '<h2>費用を左右する主な要素</h2>'
    '<table><tbody>'
    '<tr><th>品物の量</th><td>家財・不用品の量が多いほど、搬出・運搬・処分の手間が増えます。</td></tr>'
    '<tr><th>品物の種類</th><td>家電リサイクル法の対象品や、別途処理が必要なものは扱いが変わります。</td></tr>'
    '<tr><th>間取り・階数</th><td>部屋数や階数、エレベーターの有無で搬出の手間が変わります。</td></tr>'
    '<tr><th>搬出経路</th><td>前面道路の幅、駐車スペース、トラックの横付け可否などが影響します。</td></tr>'
    '<tr><th>作業人数・日数</th><td>量や条件に応じて、必要な人数・日数が変わります。</td></tr>'
    '</tbody></table>'
    '<h2>費用を抑えるための考え方</h2>'
    '<ul><li>残すもの・処分するものを事前に分けておく</li>'
    '<li>買取できる品物（金属・機械・農機具など）があれば査定に出す</li>'
    '<li>片付け・回収・撤去をまとめて依頼して搬出を効率化する</li></ul>'
    '<p>株式会社AMTは金属スクラップの買取や農機具の買取も行っています。'
    '買取できるものがあれば、<a href="/nouki-kaitori/">農機具の買取り</a>などとあわせ、'
    '<strong>費用への反映をご提案</strong>できる場合があります。</p>'
    '<p class="note">※このページには具体的な料金表は掲載していません。'
    '費用は現地条件で大きく変わるため、正確な金額は現地確認後に無料でお見積りします。</p>'
    '</div></section>',
    [("見積りは無料ですか？", "はい、お見積り・ご相談は無料です。"),
     ("料金はどうやって決まりますか？",
      "品物の量・種類・間取り・搬出経路・作業人数などをもとに算出します。現地を確認のうえ、無料でお見積りします。"),
     ("追加料金はかかりますか？",
      "お見積り時にご説明した内容から大きく変わる場合は、作業前に必ずご相談します。")],
    [("/katazuke/", "家のお片付け", "住まいの片付け"),
     ("/fuyouhin/", "不用品の回収", "家具・家電の回収"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
     ("/faq/", "よくある質問", "費用・流れ・対応品目")],
    [breadcrumb_jsonld("料金・費用", "/ryoukin/"),
     faq_jsonld([("見積りは無料ですか？", "はい、お見積り・ご相談は無料です。")])],
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
c, _ = assemble(
    "flow", "ご利用の流れ",
    "ご利用の流れ｜お問い合わせから完了まで｜株式会社AMT",
    "お問い合わせ・現地確認・お見積り・作業・完了までの流れをご案内します。お見積り無料。",
    flow_body, [],
    [("/ryoukin/", "料金・費用について", "費用の決まり方"),
     ("/faq/", "よくある質問", "対応品目・流れ"),
     ("/contact/", "お問い合わせ", "電話・メールで相談")],
    [breadcrumb_jsonld("ご利用の流れ", "/flow/")],
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
        '<p class="kz-badge">静岡県内中心に対応｜お見積り無料</p>'
        '<h1>家の片付け・不用品回収・<br>残置物撤去、<br>まずは<em>無料見積り</em>から。</h1>'
        '<p class="kz-hero-copy">ご自宅の片付けや不用品の回収から、解体前の残置物撤去、倉庫・工場の片付け、'
        '農機具の買取りまで。個人のお客様も法人のお客様も、静岡県内を中心に対応します。'
        '解体工事とあわせたご相談も可能です。</p>'
        '<div class="hero-cta">'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}<small>受付時間内にお気軽にお電話ください</small></a>'
        '<a class="btn-mail" href="/contact/">メールで相談する</a></div>'
        '<ul class="kz-points"><li>個人・法人どちらも対応</li><li>使えるものは買取で還元</li><li>解体工事まで自社で一貫</li></ul>'
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
        '<p><a class="kz-btn" href="/area/">対応エリアを詳しく見る</a></p></div>'
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

    body = ('<div class="amt-katazuke">'
            + header("/") + hero + passion + works + scenes_sec + reasons_sec + license_sec
            + flow_sec + area_sec + company_sec + cta() + footer() + '</div>')

    jsonld = {
        "@context": "https://schema.org",
        "@type": PROVIDER_TYPE,
        "name": COMPANY_NAME + "（" + SITE_NAME + "）",
        "url": DOMAIN + "/",
        "telephone": TEL_INTL,
        "email": MAIL,
        "address": {
            "@type": "PostalAddress",
            "postalCode": "428-0013",
            "addressRegion": "静岡県",
            "addressLocality": "島田市",
            "streetAddress": "金谷東2丁目3483-290",
            "addressCountry": "JP",
        },
        "areaServed": {"@type": "AdministrativeArea", "name": AREA_NAME},
        "description": "静岡県島田市の株式会社AMTによる、家の片付け・不用品回収・"
                       "解体前の残置物撤去・倉庫の片付け・農機具買取のサービス。個人・法人対応。",
    }

    doc = (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>おうちのお片付け隊｜片付け・不用品回収・残置物撤去｜静岡県島田市の株式会社AMT</title>\n'
        '<meta name="description" content="静岡県島田市の株式会社AMT「おうちのお片付け隊」。家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・農機具の買取に、個人・法人問わず対応。静岡県内中心、お見積り無料。TEL 0547-39-3750。">\n'
        '<meta property="og:title" content="おうちのお片付け隊｜株式会社AMT｜静岡県島田市">\n'
        '<meta property="og:description" content="家の片付け・不用品回収・解体前の残置物撤去・倉庫片付け・農機具買取。個人・法人どちらも対応。静岡県内中心、お見積り無料。">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:url" content="{DOMAIN}/">\n'
        f'<meta property="og:image" content="{IMG["ogp_v2"]}">\n'
        '<style>\n' + DESIGN_CSS + '\n</style>\n'
        '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False) + '</script>\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n'
    )
    with io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)

    # WordPress公開用のトップページ本文（wp:htmlブロック）も返す
    home_block = (
        "<!-- wp:html -->\n" + body + "\n<!-- /wp:html -->\n\n"
        '<!-- wp:html -->\n<script type="application/ld+json">'
        + json.dumps(jsonld, ensure_ascii=False) + "</script>\n<!-- /wp:html -->"
    )
    home_title = "おうちのお片付け隊｜片付け・不用品回収・残置物撤去｜静岡県島田市の株式会社AMT"
    return len(doc), home_title, home_block


# 各固定ページの meta description（AIOSEO に公開時に設定。docs/live-apply-sheet.md が元）
PAGE_DESC = {
    "home": "静岡県島田市の株式会社AMT「おうちのお片付け隊」。家の片付け・不用品回収・解体前の残置物撤去・倉庫の片付け・農機具買取に、個人・法人とも対応。静岡県内中心、お見積り無料。TEL 0547-39-3750。",
    "katazuke": "静岡県島田市で家の片付けなら株式会社AMT。引越し前後・空き家・実家の片付けを、仕分けから搬出まで対応。個人・法人OK、お見積り無料。TEL 0547-39-3750。",
    "fuyouhin": "静岡県島田市の不用品回収は株式会社AMT。家具・家電・雑貨などをまとめて回収。買取できる品は買取、処分品は提携の許可業者へ適正委託。見積り無料。TEL 0547-39-3750。",
    "zanchibutsu": "静岡県島田市で解体前の残置物撤去なら株式会社AMT。家財・設備・不用品を撤去。自社の解体工事とあわせた相談も可能。個人・法人対応、見積り無料。TEL 0547-39-3750。",
    "souko": "静岡県島田市で倉庫・工場・店舗の片付けは株式会社AMT。資材・在庫・什器の整理・搬出に法人対応。お見積り無料。TEL 0547-39-3750。",
    "nouki-kaitori": "静岡県島田市で農機具の買取りは株式会社AMT。トラクター・耕運機・田植機などを買取。片付けと同時の相談も歓迎。見積り無料。TEL 0547-39-3750。",
    "hinmoku": "静岡県島田市のおうちのお片付け隊（AMT）が、回収・買取できる品目を一覧でご案内。買取品は古物商許可のもと買取。見積り無料。TEL 0547-39-3750。",
    "tenpo": "静岡県島田市で店舗・オフィスの片付けは株式会社AMT。閉店・移転・原状回復までワンストップ。法人対応、見積り無料。TEL 0547-39-3750。",
    "ryoukin": "静岡県島田市の片付け・不用品回収の料金は株式会社AMT。現地確認のうえ明確なお見積りをご提示（無料）。TEL 0547-39-3750。",
    "seiri": "静岡県島田市で生前整理・遺品整理なら株式会社AMT。元気なうちの整理から遺品整理まで、ていねいに対応。個人・法人OK、見積り無料。TEL 0547-39-3750。",
    "akiya": "静岡県島田市で空き家・実家の片付けは株式会社AMT。遠方・解体前でもまとめて対応。片付けから解体の相談まで。見積り無料。TEL 0547-39-3750。",
    "gomiyashiki-katazuke": "静岡県島田市でゴミ屋敷・汚部屋の片付けは株式会社AMT。足の踏み場がなくても、まずご相談を。見積り無料。TEL 0547-39-3750。",
    "hikkoshi": "静岡県島田市で引っ越しの片付け・不用品回収は株式会社AMT。期日までにまとめて搬出・処分・買取。見積り無料。TEL 0547-39-3750。",
    "area": "株式会社AMT（おうちのお片付け隊）の対応エリア。静岡県島田市を中心に、藤枝・焼津・掛川・菊川・牧之原ほか静岡県内に対応。見積り無料。",
    "flow": "おうちのお片付け隊（静岡県島田市・株式会社AMT）のご利用の流れ。お問い合わせ→現地確認→お見積り→作業→完了まで分かりやすくご案内。",
    "faq": "静岡県島田市の片付け・不用品回収「おうちのお片付け隊」（AMT）へのよくある質問。料金・日数・近隣配慮などにお答えします。",
    "company": "株式会社AMT（静岡県島田市）の会社概要。片付け・不用品回収・残置物撤去・農機具買取、解体、金属スクラップ買取、通販・卸売を手がけます。",
    "contact": "静岡県島田市の片付け・不用品回収のご相談・お見積りは株式会社AMTへ。電話・メールで受付。見積り無料。TEL 0547-39-3750。",
    "privacy-policy": "株式会社AMT（おうちのお片付け隊）のプライバシーポリシー。お問い合わせ等でお預かりする個人情報の取り扱いについて定めています。",
}


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
                         "b64": base64.b64encode(content.encode("utf-8")).decode("ascii")})
    with io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)

    print("index.html:", idx_len, "bytes")
    print("extra.css :", len(DESIGN_CSS), "bytes")
    print("pages:", len(PAGES))
    for slug, title, content in PAGES:
        print(f"  {slug}: {len(content)} bytes")


if __name__ == "__main__":
    build_all()
