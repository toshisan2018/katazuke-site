# -*- coding: utf-8 -*-
"""事業サブドメインサイト 下層ページ生成スクリプト（テンプレート）。

kaitai.amt-eco.com（解体工事サイト）の assets/build_pages.py を汎用化したものです。
下の CONFIG ブロックと PAGES のサンプル1件を、事業の内容に合わせて書き換えてから使ってください。

料金の具体額・施工実績・お客様の声など、実データが必要な内容は
確認が取れるまで入れないこと（推測で書かない）。
"""
import json, os, base64, io

OUT = os.path.join(os.path.dirname(__file__), "pages")
os.makedirs(OUT, exist_ok=True)

# ============================================================
# ▼▼▼ CONFIG：事業ごとに書き換える設定 ▼▼▼
# ============================================================
SITE_NAME = "【事業名】"                       # 例: 片付け／システム開発／通販
COMPANY_NAME = "株式会社AMT"
DOMAIN = "https://【サブドメイン】.amt-eco.com"  # 末尾スラッシュなし
TEL = "【電話番号（ハイフンあり）】"             # 例: 0547-39-3750
TEL_INTL = "+81-【市外局番以下（先頭0を除く）】"  # JSON-LD用（例: +81-547-39-3750）
MAIL = "【メールアドレス】"
AREA_NAME = "静岡県"                            # areaServed に使う都道府県名等

# schema.org の provider type。事業内容に合わせて選ぶ（例）
#   工事・施工系      → "GeneralContractor"
#   店舗・小売系       → "LocalBusiness" / "Store"
#   ネット通販         → "OnlineStore"
#   ソフトウェア開発    → "Organization"（Serviceのprovider程度なら十分）
PROVIDER_TYPE = "LocalBusiness"

# ナビゲーション項目：(パス, 表示名)。事業のページ構成に合わせて書き換える
NAV_ITEMS = [
    ("/", "ホーム"),
    ("/faq/", "よくある質問"),
    ("/company/", "会社概要"),
    ("/flow/", "ご利用の流れ"),
    ("/contact/", "お問い合わせ"),
]
# ============================================================
# ▲▲▲ CONFIG ここまで ▲▲▲
# ============================================================


def header(current=""):
    lis = "".join(
        f'<li><a href="{u}"{" aria-current=\"page\"" if u==current else ""}>{t}</a></li>'
        for u, t in NAV_ITEMS
    )
    return (
        f'<header class="site-header"><div class="header-inner">'
        f'<div class="logo"><span>{COMPANY_NAME}</span> {SITE_NAME}</div>'
        f'<div class="header-tel"><a href="tel:{TEL}">TEL {TEL}</a>'
        '<small>お見積り・ご相談無料</small></div></div></header>'
        f'<nav class="site-nav"><ul>{lis}</ul></nav>'
    )


def breadcrumb(label):
    return ('<div class="breadcrumb"><a href="/">ホーム</a>'
            f'<span>›</span>{label}</div>')


def page_hero(h1, lead):
    return (f'<div class="page-hero"><div class="inner"><h1>{h1}</h1>'
            f'<p>{lead}</p></div></div>')


def cta():
    return (
        '<section class="cta-band"><h2>【問い合わせを後押しする一言】</h2>'
        '<p>【補足説明】</p>'
        f'<a class="btn-tel" href="tel:{TEL}">{TEL}</a>'
        '<div class="btn-line"><a class="btn-mail" href="/contact/">'
        'メールで相談する</a></div></section>'
    )


def footer():
    return (f'<footer class="site-footer"><p>&copy; {COMPANY_NAME}｜'
            '<a href="https://amt-eco.com/" target="_blank" rel="noopener">'
            'コーポレートサイト</a></p></footer>')


def faq_block(items):
    if not items:
        return ""
    inner = "".join(
        f'<div class="faq-item"><div class="faq-q">{q}</div>'
        f'<div class="faq-a">{a}</div></div>' for q, a in items
    )
    return ('<section class="site-section"><div class="inner">'
            '<h2 class="sec-title">よくある質問</h2>'
            f'<div class="faq">{inner}</div></div></section>')


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
            {"@type": "ListItem", "position": 1, "name": "ホーム",
             "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": label,
             "item": DOMAIN + url},
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


def assemble(slug, current, breadcrumb_label, hero_h1, hero_lead, body_html,
             faq_items, jsonlds):
    url = "/" + slug + "/"
    parts = ['<div class="site-wrap">']
    parts.append(header(current))
    parts.append(breadcrumb(breadcrumb_label))
    parts.append(page_hero(hero_h1, hero_lead))
    parts.append(body_html)
    parts.append(faq_block(faq_items))
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
    content = "\n\n".join([html_block] + scripts)
    return content, url


PAGES = []

# ------------------------------------------------------------
# サンプル：ページ1件分のひな形。
# これをコピーして、事業に必要なページ数だけ増やしてください。
# 料金・実績・保有資格など事実が必要な項目は、確認が取れるまで書かない。
# ------------------------------------------------------------
faq = [
    ("【よくある質問1】", "【回答1】"),
    ("【よくある質問2】", "【回答2】"),
]
body = (
    '<section class="site-section"><div class="prose">'
    '<p class="lead">【このページで扱うサービスの概要を2〜3文で】</p>'
    '<h2>【見出し1】</h2>'
    '<p>【本文1】</p>'
    '<h2>【見出し2】</h2>'
    '<p>【本文2】</p>'
    '<h2>費用について</h2>'
    '<p>費用は条件によって変わるため、<strong>無料でお見積り</strong>します。'
    '確定していない金額・件数は掲載しないこと。</p>'
    '<p class="note">※費用の目安は現地条件・案件内容によって大きく変わるため、'
    'まずはお気軽にお問い合わせください。</p>'
    '</div></section>'
)
c, u = assemble(
    "sample-page", "/sample-page/", "【パンくず表示名】",
    f"【ページタイトルH1】｜{SITE_NAME}の{COMPANY_NAME}",
    "【メタディスクリプション相当の要約文】",
    body, faq,
    [service_jsonld("【サービス名】", "【サービス説明】", "/sample-page/"),
     breadcrumb_jsonld("【パンくず表示名】", "/sample-page/"), faq_jsonld(faq)],
)
PAGES.append(("sample-page", f"【ページタイトルH1】｜{SITE_NAME}の{COMPANY_NAME}", c))


# 保存
manifest = []
for slug, title, content in PAGES:
    fn = os.path.join(OUT, slug + ".html")
    with io.open(fn, "w", encoding="utf-8") as f:
        f.write(content)
    manifest.append({"slug": slug, "title": title,
                     "b64": base64.b64encode(content.encode("utf-8")).decode("ascii")})

with io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False)

print("pages:", len(PAGES))
for slug, title, content in PAGES:
    print(f"  {slug}: {len(content)} bytes")
