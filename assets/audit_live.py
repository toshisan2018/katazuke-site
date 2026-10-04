"""
公開中の katazuke.amt-eco.com を外から点検する（bundle.json の全ページ）。
  python assets/audit_live.py  → 問題点のみ表示（UTF-8）
点検: HTTP 200 / title / meta description（重複・CSS混入）/ og:image / JSON-LD パース / 旧ロゴ / Googleフォント / 電話番号
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


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 amt-audit"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main():
    items = json.load(io.open(os.path.join(HERE, "publish", "bundle.json"), encoding="utf-8"))
    issues, descs = [], {}
    for it in items:
        url = BASE if it["slug"] == "home" else BASE + it["slug"] + "/"
        try:
            st, t = get(url + "?audit=1")
        except Exception as e:  # noqa: BLE001
            issues.append(f"{url} 取得失敗 {e}")
            continue
        m = lambda p: (re.search(p, t, re.S) or [None, ""])[1]  # noqa: E731
        title = m(r"<title>(.*?)</title>")
        desc = m(r'<meta name="description" content="([^"]*)"')
        og = m(r'property="og:image" content="([^"]*)"')
        if st != 200:
            issues.append(f"{url} status {st}")
        if not desc or "{" in desc or "/*" in desc or "header.wp-block" in desc:
            issues.append(f"{url} description 不正: {desc[:40]}")
        descs.setdefault(desc, []).append(it["slug"])
        if OGP not in og:
            issues.append(f"{url} og:image が旧: {og}")
        for i, ld in enumerate(re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S)):
            try:
                json.loads(ld)
            except Exception as e:  # noqa: BLE001
                issues.append(f"{url} JSON-LD[{i}] 不正 {e}")
        if "2026/09/logo.png" in t:
            issues.append(f"{url} 旧ロゴが残っている")
        if "fonts.googleapis.com" in t:
            issues.append(f"{url} Googleフォントを読み込んでいる")
        tels = set(re.findall(r"0\d{1,4}-\d{1,4}-\d{3,4}", t)) - {"0547-39-3750"}
        if tels:
            issues.append(f"{url} 想定外の電話番号 {tels}")
        print(f"ok {it['slug']:22} {len(t):7}  {title[:48]}")
    for d, slugs in descs.items():
        if len(slugs) > 1:
            issues.append(f"description 重複: {slugs}")
    print("\n問題:", len(issues))
    for x in issues:
        print(" -", x)


if __name__ == "__main__":
    main()
