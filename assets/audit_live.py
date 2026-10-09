"""
公開中の katazuke.amt-eco.com を外から点検する（bundle.json の全ページ）。
  python assets/audit_live.py  → 問題点のみ表示（UTF-8）

点検内容:
  HTTP 200 / title（長さ・サイト名サフィックスの有無・重複）/ meta description（長さ・重複・CSS混入）
  / canonical / og:image / JSON-LD（パース・種別）/ h1 / 画像のalt / 旧ロゴ / Googleフォント / 電話番号
  / 新ページ（料金・農機具・事例）の必須要素
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
OGP = "uploads/2026/10/ogp-katazuke-v2.jpg"
SITE_SUFFIX_RE = re.compile(r"\s[-–|｜]\s*おうち(の)?片付け隊\s*$")
TITLE_MAX = 40          # 全角。これを超えると検索結果で切られやすい
DESC_MIN, DESC_MAX = 70, 125
PRICE_TEXT = "20,000円"  # 料金ページ・トップに出ているはずの㎥単価


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 amt-audit"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def jsonld_types(obj, out):
    if isinstance(obj, dict):
        for g in obj.get("@graph", []):
            jsonld_types(g, out)
        t = obj.get("@type")
        if isinstance(t, list):
            out.update(t)
        elif t:
            out.add(t)
    elif isinstance(obj, list):
        for i in obj:
            jsonld_types(i, out)
    return out


def main():
    items = json.load(io.open(os.path.join(HERE, "publish", "bundle.json"), encoding="utf-8"))
    issues, descs, titles = [], {}, {}
    seen_types = {}
    for it in items:
        slug = it["slug"]
        url = BASE if slug == "home" else BASE + slug + "/"
        try:
            st, t = get(url + "?audit=1")
        except Exception as e:  # noqa: BLE001
            issues.append(f"{url} 取得失敗 {e}")
            continue
        m = lambda p: (re.search(p, t, re.S) or [None, ""])[1]  # noqa: E731
        title = m(r"<title>(.*?)</title>")
        desc = m(r'<meta name="description" content="([^"]*)"')
        og = m(r'property="og:image" content="([^"]*)"')
        canon = m(r'<link rel="canonical" href="([^"]*)"')

        if st != 200:
            issues.append(f"{url} status {st}")

        # --- title ---
        if not title:
            issues.append(f"{url} title が空")
        else:
            if SITE_SUFFIX_RE.search(title):
                issues.append(f"{url} title にサイト名サフィックスが残っている: …{title[-14:]}")
            if len(title) > TITLE_MAX:
                issues.append(f"{url} title が長い({len(title)}字): {title[:30]}…")
            titles.setdefault(title, []).append(slug)

        # --- description ---
        if not desc or "{" in desc or "/*" in desc or "header.wp-block" in desc:
            issues.append(f"{url} description 不正: {desc[:40]}")
        elif not (DESC_MIN <= len(desc) <= DESC_MAX):
            issues.append(f"{url} description の長さ({len(desc)}字)")
        descs.setdefault(desc, []).append(slug)

        # --- canonical / og ---
        if canon.rstrip("/") != url.rstrip("/").split("?")[0]:
            issues.append(f"{url} canonical が不一致: {canon}")
        if OGP not in og:
            issues.append(f"{url} og:image が旧: {og}")

        # --- JSON-LD ---
        types = set()
        for i, ld in enumerate(re.findall(
                r'<script type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S)):
            try:
                jsonld_types(json.loads(ld), types)
            except Exception as e:  # noqa: BLE001
                issues.append(f"{url} JSON-LD[{i}] 不正 {e}")
        seen_types[slug] = types
        if "BreadcrumbList" not in types:
            issues.append(f"{url} BreadcrumbList が無い")

        # --- h1 ---
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        if not h1s:
            issues.append(f"{url} h1 が無い")

        # --- 画像の alt ---
        no_alt = len(re.findall(r"<img(?![^>]*\balt=)[^>]*>", t))
        if no_alt:
            issues.append(f"{url} alt の無い img が {no_alt} 件")

        # --- 既存チェック ---
        if "2026/09/logo.png" in t:
            issues.append(f"{url} 旧ロゴが残っている")
        if "fonts.googleapis.com" in t:
            issues.append(f"{url} Googleフォントを読み込んでいる")
        tels = set(re.findall(r"0\d{1,4}-\d{1,4}-\d{3,4}", t)) - {"0547-39-3750"}
        if tels:
            issues.append(f"{url} 想定外の電話番号 {tels}")

        # --- ページ固有 ---
        if slug in ("home", "ryoukin") and PRICE_TEXT not in t:
            issues.append(f"{url} ㎥単価（{PRICE_TEXT}）が出ていない")
        if slug == "ryoukin" and "UnitPriceSpecification" not in t:
            issues.append(f"{url} 料金の構造化データ(UnitPriceSpecification)が無い")
        if slug == "flow" and "HowTo" not in types:
            issues.append(f"{url} HowTo の構造化データが無い")
        if slug == "home" and "LocalBusiness" not in types:
            issues.append(f"{url} LocalBusiness の構造化データが無い")

        print(f"ok {slug:24} {len(t):7} {len(title):3}字  {title[:46]}")

    for d, slugs in descs.items():
        if len(slugs) > 1:
            issues.append(f"description が重複: {slugs}")
    for ti, slugs in titles.items():
        if len(slugs) > 1:
            issues.append(f"title が重複: {slugs}")

    # llms.txt
    try:
        st, body = get(BASE + "llms.txt")
        if st != 200 or "株式会社AMT" not in body:
            issues.append("llms.txt が正しく配信されていない")
    except Exception:  # noqa: BLE001
        issues.append("llms.txt が 404（ドキュメントルートへの設置が必要）")

    print()
    for i in issues:
        print("  -", i)
    print("問題:", len(issues))


if __name__ == "__main__":
    main()
