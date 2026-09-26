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
import json, os, base64, io

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

NAV_ITEMS = [
    ("/", "ホーム"),
    ("/katazuke/", "家の片付け"),
    ("/fuyouhin/", "不用品回収"),
    ("/zanchibutsu/", "残置物撤去"),
    ("/souko/", "倉庫の片付け"),
    ("/nouki-kaitori/", "農機具買取"),
    ("/ryoukin/", "料金・費用"),
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
    ("/ryoukin/", "料金・費用について"),
]
FOOT_GUIDE = [
    ("/flow/", "ご利用の流れ"),
    ("/area/", "対応エリア"),
    ("/company/", "会社概要"),
    ("/faq/", "よくある質問"),
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
  font-family:'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif;
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
.amt-katazuke .logo-mark{width:46px;height:46px;flex-shrink:0;line-height:0;}
.amt-katazuke .logo-tx{display:flex;flex-direction:column;line-height:1.25;}
.amt-katazuke .logo-name{font-weight:900;font-size:1.12rem;color:var(--ink);letter-spacing:.3px;}
.amt-katazuke .logo-name b{color:var(--dark);}
.amt-katazuke .logo-tx small{font-size:.72rem;color:#666;font-weight:600;margin-top:3px;}
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
.amt-katazuke .k-nav ul{max-width:1080px;margin:0 auto;padding:0 16px;list-style:none;display:flex;flex-wrap:wrap;gap:2px 0;}
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
.amt-katazuke .hero-cta{display:flex;gap:16px;flex-wrap:wrap;align-items:center;}
.amt-katazuke .btn-tel{display:inline-block;background:var(--dark);color:#fff;font-weight:900;font-size:clamp(1.2rem,3vw,1.6rem);padding:14px 32px;border-radius:8px;text-decoration:none;box-shadow:0 4px 0 rgba(0,0,0,.28);}
.amt-katazuke .btn-tel small{display:block;font-size:.75rem;font-weight:700;}
.amt-katazuke .btn-mail{display:inline-block;background:transparent;color:var(--ink);border:2px solid var(--dark);font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;}
.amt-katazuke .btn-mail:hover{background:var(--dark);color:#fff;}
.amt-katazuke .btn-tel:hover{filter:brightness(1.1);}

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

/* FAQ */
.amt-katazuke .faq{max-width:820px;margin:0 auto;}
.amt-katazuke .faq-item{background:#fff;border:1px solid #eee;border-radius:8px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.04);overflow:hidden;}
.amt-katazuke .faq-q{display:flex;gap:12px;align-items:flex-start;padding:18px 20px;font-weight:700;font-size:1.02rem;background:var(--primary-light);}
.amt-katazuke .faq-q::before{content:"Q";flex-shrink:0;width:26px;height:26px;border-radius:50%;background:var(--dark);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.9rem;}
.amt-katazuke .faq-a{display:flex;gap:12px;align-items:flex-start;padding:18px 20px;color:#444;font-size:.95rem;}
.amt-katazuke .faq-a::before{content:"A";flex-shrink:0;width:26px;height:26px;border-radius:50%;background:var(--primary);color:var(--ink);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.9rem;}

/* 下部CTA帯（濃色地・白文字＋黄ボタン） */
.amt-katazuke .cta-band{background:linear-gradient(135deg,var(--dark-2),var(--dark));color:#fff;text-align:center;padding:48px 16px;}
.amt-katazuke .cta-band h2{font-size:clamp(1.3rem,3vw,1.9rem);font-weight:900;margin-bottom:10px;color:#fff;}
.amt-katazuke .cta-band p{margin-bottom:24px;color:#e7e7e7;}
.amt-katazuke .cta-band .btn-tel{display:inline-block;background:var(--primary);color:var(--ink);font-weight:900;font-size:clamp(1.3rem,3.5vw,1.8rem);padding:16px 40px;border-radius:8px;text-decoration:none;box-shadow:0 4px 0 rgba(0,0,0,.3);}
.amt-katazuke .cta-band .btn-line{display:block;margin-top:16px;}
.amt-katazuke .cta-band .btn-mail{display:inline-block;background:transparent;color:#fff;border:2px solid #fff;font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;margin-top:8px;}
.amt-katazuke .cta-band .btn-mail:hover{background:#fff;color:var(--dark);}

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
        f'<a class="logo" href="/"><span class="logo-mark">{LOGO_SVG}</span>'
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
        '<section class="cta-band"><h2>お片付けのご相談・お見積りは無料です</h2>'
        '<p>「いくらかかる？」「これは回収できる？」だけでもお気軽にどうぞ。'
        '個人のお客様も法人のお客様も、静岡県内を中心に対応します。</p>'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}</a>'
        f'<div class="btn-line"><a class="btn-mail" href="mailto:{MAIL}">'
        'メールで相談する</a></div></section>'
    )


def footer():
    svc = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_SERVICE)
    gui = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in FOOT_GUIDE)
    return (
        '<footer class="k-footer"><div class="foot-inner">'
        '<div class="foot-col foot-about">'
        f'<div class="foot-logo"><span>{COMPANY_NAME}</span> {SITE_NAME}</div>'
        '<p>静岡県島田市を拠点に、家の片付け・不用品回収・解体前の残置物撤去・'
        '倉庫の片付け・農機具の買取りまで対応します。個人のお客様も法人・事業者さまも、'
        'お見積り・ご相談は無料です。</p></div>'
        f'<div class="foot-col"><h4>サービス</h4><ul>{svc}</ul></div>'
        f'<div class="foot-col"><h4>ご案内</h4><ul>{gui}</ul></div>'
        '<div class="foot-col foot-contact"><h4>お問い合わせ</h4>'
        f'<a class="foot-tel" href="tel:{TEL}">{TEL}</a>'
        '<p class="foot-note">お見積り・ご相談は無料</p>'
        f'<a class="foot-mail" href="mailto:{MAIL}">メールで相談する</a>'
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
             faq_items, rel_cards, jsonlds):
    """下層ページ本体を wp:html ブロックとして組み立てる。"""
    url = "/" + slug + "/"
    parts = ['<div class="amt-katazuke">']
    parts.append(header(url))
    parts.append(breadcrumb(breadcrumb_label))
    parts.append(page_hero(hero_h1, hero_lead))
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


def add_service_page(slug, nav_label, h1, lead, body, faq, rel, jsonld_name, jsonld_desc, title):
    c, _ = assemble(
        slug, nav_label, h1, lead, body, faq, rel,
        [service_jsonld(jsonld_name, jsonld_desc, "/" + slug + "/"),
         breadcrumb_jsonld(nav_label, "/" + slug + "/"), faq_jsonld(faq)],
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
)

# ------------------------------------------------------------
# 2. 不用品の回収
# ------------------------------------------------------------
add_service_page(
    "fuyouhin", "不用品回収",
    "不用品の回収｜家具・家電をまとめて｜株式会社AMT",
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
    "不用品の回収｜家具・家電をまとめて｜株式会社AMT",
)

# ------------------------------------------------------------
# 3. 解体前の残置物撤去
# ------------------------------------------------------------
add_service_page(
    "zanchibutsu", "残置物撤去",
    "解体前の残置物撤去｜家財・設備の撤去｜株式会社AMT",
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
    "解体前の残置物撤去｜家財・設備の撤去｜株式会社AMT",
)

# ------------------------------------------------------------
# 4. 倉庫の片付け
# ------------------------------------------------------------
add_service_page(
    "souko", "倉庫の片付け",
    "倉庫の片付け｜工場・店舗の整理｜株式会社AMT",
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
    "倉庫の片付け｜工場・店舗の整理｜株式会社AMT",
)

# ------------------------------------------------------------
# 5. 農機具の買取り
# ------------------------------------------------------------
add_service_page(
    "nouki-kaitori", "農機具買取",
    "農機具の買取り｜トラクター・耕運機ほか｜株式会社AMT",
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
    "農機具の買取り｜トラクター・耕運機ほか｜株式会社AMT",
)

# ------------------------------------------------------------
# 6. 料金・費用について
# ------------------------------------------------------------
c, _ = assemble(
    "ryoukin", "料金・費用",
    "料金・費用について｜見積り無料｜株式会社AMT",
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
PAGES.append(("ryoukin", "料金・費用について｜見積り無料｜株式会社AMT", c))

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
    '<tr><th>代表者</th><td>代表取締役　鈴木 敏也</td></tr>'
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
contact_body = (
    '<section class="k-section"><div class="prose">'
    '<p class="lead">お片付け・不用品回収・残置物撤去・倉庫の片付け・農機具の買取りに関するご相談・'
    'お見積りは無料です。お電話またはメールでお気軽にお問い合わせください。</p>'
    '<h2>お電話でのお問い合わせ</h2>'
    f'<p style="font-size:1.6rem;font-weight:900;"><a href="tel:{TEL}">{TEL}</a></p>'
    '<p>受付時間内にお気軽にお電話ください。「費用だけ知りたい」というご相談だけでも大丈夫です。</p>'
    '<h2>メールでのお問い合わせ</h2>'
    f'<p><a href="mailto:{MAIL}">{MAIL}</a></p>'
    '<p>次の内容をお知らせいただくと、ご案内がスムーズです。</p>'
    '<ul><li>片付けたい場所（住所・エリア）</li>'
    '<li>おおよその内容（例：一軒分／一部屋／不用品◯点／倉庫／農機具など）</li>'
    '<li>ご希望の時期</li><li>お名前・ご連絡先</li></ul>'
    '<p class="note">※お問い合わせフォームを設置する場合は、この位置にWordPressの'
    'お問い合わせフォーム（Contact Form 7 等）を差し込めます。</p>'
    '</div></section>'
)
c, _ = assemble(
    "contact", "お問い合わせ",
    "お問い合わせ｜おうちのお片付け隊（株式会社AMT）",
    "片付け・不用品回収のご相談・お見積りは無料。電話 0547-39-3750、またはメールでお問い合わせください。",
    contact_body, [],
    [("/ryoukin/", "料金・費用について", "費用の決まり方"),
     ("/flow/", "ご利用の流れ", "お問い合わせから完了まで"),
     ("/faq/", "よくある質問", "対応品目・流れ")],
    [breadcrumb_jsonld("お問い合わせ", "/contact/")],
)
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


# ============================================================
# トップページ（単一HTMLファイル index.html）を生成
# ============================================================
def build_index():
    services = [
        ("家のお片付け", "お引越し前後・空き家・実家の片付けなど。仕分けから搬出まで、ご希望に合わせて対応します。", "/katazuke/"),
        ("不用品の回収", "家具・家電・雑貨など、ご家庭や事業所で不要になった品物をまとめて回収します。量が多い場合もご相談ください。", "/fuyouhin/"),
        ("解体前の残置物撤去", "解体予定の建物に残った家財・設備・不用品を撤去します。当社の解体工事とあわせてのご依頼も可能です。", "/zanchibutsu/"),
        ("倉庫の片付け", "倉庫・工場・店舗などに溜まった資材・在庫・什器の片付け。法人・事業者さまの整理もお任せください。", "/souko/"),
        ("農機具の買取り", "使わなくなったトラクター・耕運機・田植機などの農機具を買取ります。片付けと同時のご相談も歓迎です。", "/nouki-kaitori/"),
    ]
    cards = "".join(
        f'<a class="card" href="{u}" style="text-decoration:none;color:inherit;display:block;">'
        f'<h3><span class="mk">■</span>{t}</h3><p>{d}</p></a>'
        for t, d, u in services
    )
    reasons = [
        ("BtoB・BtoC どちらも対応", "個人のお客様から法人・事業者さままで、片付け・回収・撤去に幅広く対応します。"),
        ("解体・金属買取も自社対応", "解体工事や金属スクラップ買取も手がけるAMTだから、残置物撤去や買取の反映まで一貫してご相談いただけます。"),
        ("お見積り・ご相談は無料", "「いくらかかる？」だけでも大丈夫。現地を確認して、明確なお見積りをご提示します。"),
    ]
    reason_cards = "".join(
        f'<div class="card"><h3><span class="mk">◆</span>{t}</h3><p>{d}</p></div>'
        for t, d in reasons
    )
    steps = [
        ("お問い合わせ", "電話またはメールでご相談ください。"),
        ("現地確認・ヒアリング", "お品物の量や搬出経路を確認し、ご要望をうかがいます。"),
        ("お見積り", "内容をもとに明確なお見積りをご提示します（無料）。"),
        ("日程調整・作業", "ご都合に合わせて、仕分け・搬出・回収を行います。"),
        ("完了", "作業後の状態をご確認いただき完了です。"),
    ]
    step_html = "".join(
        f'<div class="flow-step"><h3>{t}</h3><p>{d}</p></div>' for t, d in steps
    )

    hero = (
        '<div class="hero"><div class="hero-inner">'
        '<span class="badge">静岡県内中心に対応｜お見積り無料</span>'
        '<h1>家の片付け・不用品回収・残置物撤去、<br>まずは<em>無料見積り</em>から。</h1>'
        '<p>ご自宅の片付けや不用品の回収から、解体前の残置物撤去、倉庫・工場の片付け、'
        '農機具の買取りまで。個人のお客様も法人のお客様も、静岡県内を中心に対応します。'
        '解体工事とあわせたご相談も可能です。</p>'
        '<div class="hero-cta">'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}<small>受付時間内にお気軽にお電話ください</small></a>'
        f'<a class="btn-mail" href="mailto:{MAIL}">メールで相談する</a>'
        '</div></div></div>'
    )
    works = (
        '<section class="k-section works"><div class="inner">'
        '<h2 class="sec-title">対応業務</h2>'
        '<p class="sec-lead">ご家庭の片付けから法人・事業者さまの倉庫整理まで、規模を問わず対応します。</p>'
        f'<div class="card-grid">{cards}</div></div></section>'
    )
    reasons_sec = (
        '<section class="k-section reasons"><div class="inner">'
        '<h2 class="sec-title">選ばれる理由</h2>'
        '<p class="sec-lead">片付けだけでなく、その先の「処分」「買取」「解体」まで見据えて対応します。</p>'
        f'<div class="card-grid">{reason_cards}</div></div></section>'
    )
    flow_sec = (
        '<section class="k-section flow"><div class="inner">'
        '<h2 class="sec-title">ご利用の流れ</h2>'
        '<p class="sec-lead">お問い合わせから完了まで、わかりやすくご案内します。</p>'
        f'<div class="flow-steps">{step_html}</div></div></section>'
    )
    area_sec = (
        '<section class="k-section area"><div class="inner">'
        '<h2 class="sec-title">対応エリア</h2>'
        '<p><strong>静岡県内を中心</strong>に対応しています。'
        '島田市・金谷・藤枝市・焼津市・静岡市・掛川市・菊川市・牧之原市・浜松市ほか、'
        '近隣エリアもまずはご相談ください。</p></div></section>'
    )
    company_sec = (
        '<section class="k-section company"><div class="inner">'
        '<h2 class="sec-title">会社概要</h2>'
        '<table>'
        '<tr><th>会社名</th><td>株式会社AMT</td></tr>'
        '<tr><th>代表者</th><td>代表取締役　鈴木 敏也</td></tr>'
        '<tr><th>所在地</th><td>〒428-0013　静岡県島田市金谷東2丁目3483-290</td></tr>'
        f'<tr><th>電話番号</th><td><a href="tel:{TEL}">{TEL}</a></td></tr>'
        f'<tr><th>メール</th><td><a href="mailto:{MAIL}">{MAIL}</a></td></tr>'
        f'<tr><th>許認可</th><td>{KOBUTSU_TD}</td></tr>'
        '<tr><th>事業内容</th><td>お片付け・不用品回収・残置物撤去・農機具買取（おうちのお片付け隊）、'
        '解体工事、非鉄金属・工業雑品スクラップ買取、中古太陽光パネル買取・輸出、通販・卸売</td></tr>'
        '<tr><th>コーポレートサイト</th><td><a href="https://amt-eco.com/" target="_blank" rel="noopener">https://amt-eco.com/</a></td></tr>'
        '</table></div></section>'
    )

    body = ('<div class="amt-katazuke">'
            + header("/") + hero + works + reasons_sec + flow_sec
            + area_sec + company_sec + cta() + footer() + '</div>')

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
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet">\n'
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


# ============================================================
# 保存
# ============================================================
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
    manifest.append({"slug": slug, "title": title,
                     "b64": base64.b64encode(content.encode("utf-8")).decode("ascii")})
with io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False)

print("index.html:", idx_len, "bytes")
print("extra.css :", len(DESIGN_CSS), "bytes")
print("pages:", len(PAGES))
for slug, title, content in PAGES:
    print(f"  {slug}: {len(content)} bytes")
