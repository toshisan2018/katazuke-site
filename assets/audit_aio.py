# -*- coding: utf-8 -*-
"""katazuke.amt-eco.com の AIO/GEO 対応状況を公開ページから実測する。

audit_live.py が title/description/canonical などの「SEOの基本」を見るのに対し、
こちらは生成AI検索（AI Overviews / ChatGPT Search / Perplexity など）に
引用されるための構造を見る。解体サイトの assets/audit_aio.py と同じ枠組み。

判定する項目:
  1. アンサーカプセル … 本文H2の直後が30文字以上の段落になっているか
  2. 構造化データ     … JSON-LD が単一の @graph になっていて
                        Organization / WebPage が @id で結ばれているか
  3. モジュール化     … 比較表・FAQ の有無
  4. 出典             … go.jp / lg.jp など公的機関へのリンク本数
  5. 更新日           … 可視の更新日表示と schema の dateModified

使い方:
    py -3 assets/audit_aio.py            # サマリーのみ
    py -3 assets/audit_aio.py --detail   # ページ別の内訳も表示
"""

import io
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://katazuke.amt-eco.com/"
ORG_ID = "https://katazuke.amt-eco.com/#organization"

# FAQ・関連ページ・CTA の見出しは本文H2として数えない
SKIP_H2 = ("よくある質問", "関連ページ", "関連コラム", "お問い合わせ",
           "無料です", "ご相談", "お気軽", "この記事の要点")
# リンクグリッドなど、要約文を置く意味がないセクション
NAV_H2 = ("ほかの市町", "あわせて読みたい", "主な対応エリア", "対応エリア",
          "関連する", "コラム", "市町別", "サービス一覧", "メニュー",
          "近隣の市町", "投稿をさらに読み込む", "さらに読み込む")
# ページ全体がリンク集のため、本文H2として数えないページ
NAV_SLUGS = {"column"}

CAPSULE_MIN = 30
# 公的機関のリンク。自治体は lg.jp 以外に city.*.<県>.jp / town.*.jp も多い
GOV = re.compile(r'href="https?://(?:[^"/]*\.)?(?:[^"/]*\.)?(?:go\.jp|lg\.jp)|href="https?://(?:www\.)?(?:city|town|pref)\.[^"/]*\.jp')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 amt-aio-audit"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def main_html(html):
    """ヘッダー・フッターを除いた本文だけを返す（取れなければ全文）。"""
    m = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    if m:
        return m.group(1)
    m = re.search(r'<div class="k-wrap">(.*?)<footer', html, re.S)
    return m.group(1) if m else html


def audit_page(html, slug=""):
    body_html = main_html(html)
    res = {"h2": 0, "capsule": 0, "nav": 0, "gaps": [],
           "table": body_html.count("<table"),
           "faq": 1 if ("faq" in body_html and "よくある質問" in body_html) else 0,
           "dates": 1 if ("更新日" in body_html or "最終更新" in body_html) else 0,
           "gov": len(GOV.findall(body_html)),
           "sources_box": 1 if "k-sources" in body_html else 0,
           "ld": 0, "graph": 0, "org": 0, "webpage": 0,
           "date_modified": None, "ld_broken": False}

    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)", body_html, re.S):
        title = strip_tags(m.group(1))
        if not title:
            continue
        if any(k in title for k in SKIP_H2):
            continue
        if slug in NAV_SLUGS or any(k in title for k in NAV_H2):
            res["nav"] += 1
            continue
        res["h2"] += 1
        after = m.group(2).lstrip()
        mm = re.match(r"<p[^>]*>(.*?)</p>", after, re.S)
        if mm and len(strip_tags(mm.group(1))) >= CAPSULE_MIN:
            res["capsule"] += 1
        else:
            res["gaps"].append(title)

    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    res["ld"] = len(blocks)
    for b in blocks:
        try:
            data = json.loads(b)
        except ValueError:
            res["ld_broken"] = True
            continue
        nodes = data.get("@graph") if isinstance(data, dict) and "@graph" in data else None
        if nodes:
            res["graph"] += 1
            for n in nodes:
                nid = n.get("@id", "")
                if nid == ORG_ID:
                    res["org"] = 1
                if str(n.get("@type", "")).find("WebPage") >= 0 or (
                        isinstance(n.get("@type"), list) and "WebPage" in n["@type"]):
                    res["webpage"] = 1
                if n.get("dateModified"):
                    res["date_modified"] = n["dateModified"]
    return res


SNAP = os.path.join(os.path.dirname(HERE), "snapshot-live")


def fetch_all(items):
    """公開ページを snapshot-live/ に取り込む。"""
    if not os.path.isdir(SNAP):
        os.makedirs(SNAP)
    for it in items:
        slug = it["slug"]
        url = BASE if slug == "home" else BASE + slug + "/"
        try:
            st, html = get(url + "?aio=1")
        except Exception as e:  # noqa: BLE001
            print("取得失敗", url, e)
            continue
        if st != 200:
            print("status", st, url)
            continue
        io.open(os.path.join(SNAP, slug + ".html"), "w", encoding="utf-8").write(html)
    print("snapshot-live を更新しました（%d ページ）" % len(items))


def main():
    detail = "--detail" in sys.argv
    items = json.load(io.open(os.path.join(HERE, "publish", "bundle.json"), encoding="utf-8"))
    if "--refresh" in sys.argv:
        fetch_all(items)
    tot = {"pages": 0, "h2": 0, "capsule": 0, "nav": 0, "table": 0, "faq": 0,
           "gov": 0, "gov_pages": 0, "dates": 0, "graph": 0, "org": 0,
           "webpage": 0, "dm": 0, "multi_ld": 0}
    rows = []
    for it in items:
        slug = it["slug"]
        f = os.path.join(SNAP, slug + ".html")
        if not os.path.isfile(f):
            print("snapshot なし（--refresh で取得）:", slug)
            continue
        html = io.open(f, encoding="utf-8").read()
        r = audit_page(html, slug)
        rows.append((slug, r))
        tot["pages"] += 1
        tot["h2"] += r["h2"]
        tot["capsule"] += r["capsule"]
        tot["nav"] += r["nav"]
        tot["table"] += 1 if r["table"] else 0
        tot["faq"] += r["faq"]
        tot["gov"] += r["gov"]
        tot["gov_pages"] += 1 if r["gov"] else 0
        tot["dates"] += r["dates"]
        tot["graph"] += 1 if r["graph"] else 0
        tot["org"] += r["org"]
        tot["webpage"] += r["webpage"]
        tot["dm"] += 1 if r["date_modified"] else 0
        tot["multi_ld"] += 1 if r["ld"] > 1 else 0

    p = tot["pages"]
    print("=" * 58)
    print("AIO/GEO 実測  katazuke.amt-eco.com   対象 %d ページ" % p)
    print("=" * 58)
    print("1. アンサーカプセル   %d/%d 本 (%.0f%%)  ※ナビ見出し %d 本は対象外"
          % (tot["capsule"], tot["h2"], 100.0 * tot["capsule"] / max(tot["h2"], 1), tot["nav"]))
    print("2. JSON-LD @graph     %d/%d ページ" % (tot["graph"], p))
    print("   Organization @id   %d/%d ページ" % (tot["org"], p))
    print("   WebPage ノード     %d/%d ページ" % (tot["webpage"], p))
    print("   script が2本以上   %d ページ（@graph化できていない）" % tot["multi_ld"])
    print("3. 比較表あり         %d ページ / FAQあり %d ページ" % (tot["table"], tot["faq"]))
    print("4. 公的機関リンク     %d 本 / %d ページ" % (tot["gov"], tot["gov_pages"]))
    print("5. 可視の更新日       %d/%d ページ" % (tot["dates"], p))
    print("   dateModified       %d/%d ページ" % (tot["dm"], p))
    if detail:
        print("\n--- カプセル未達の見出し ---")
        for slug, r in rows:
            if r["gaps"]:
                print(" /%s/" % slug)
                for g in r["gaps"]:
                    print("    -", g)
        print("\n--- 公的出典のないページ ---")
        print("   " + ", ".join("/%s/" % s for s, r in rows if not r["gov"]))
        print("\n--- 更新日表示のないページ ---")
        print("   " + ", ".join("/%s/" % s for s, r in rows if not r["dates"]))


main()
