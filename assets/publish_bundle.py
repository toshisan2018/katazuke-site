"""
WordPress 公開用バンドルを作る（固定ページ＋コラム一覧＋コラム記事）。

  python assets/build_pages.py && python assets/publish_bundle.py   （build_articles は import 時に再生成される）
  → assets/publish/bundle.json  [{type, slug, title, desc, content}]

管理画面（ログイン済み）でこの JSON を読み込み、REST(/wp-json/wp/v2/pages, /posts) へ slug 一致で上書きする。
  body: {title, content, aioseo_meta_data: {title: seo_title, description: desc}}
固定ページは本文の前に、デザインCSS（テーマ枠を隠すCSS込み・コメント除去済み）を <style id="amt-katazuke-css"> で同梱する
（記事・コラム一覧は build_articles.py の出力に既に同梱済み）。
"""
import base64
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_articles as ba  # noqa: E402  (build_pages も読み込まれる)

PAGE_CSS = ba.CSS


def _content(p):
    return base64.b64decode(p["b64"]).decode("utf-8")


def main():
    items = []
    style = '<!-- wp:html -->\n<style id="amt-katazuke-css">' + PAGE_CSS + '</style>\n<!-- /wp:html -->\n\n'
    for p in json.load(io.open(os.path.join(HERE, "pages", "manifest.json"), encoding="utf-8")):
        items.append({"type": "pages", "slug": p["slug"], "title": p["title"], "desc": p.get("desc", ""),
                      "seo_title": p.get("seo_title", ""),
                      "content": style + _content(p)})
    for p in json.load(io.open(os.path.join(HERE, "articles", "page_manifest.json"), encoding="utf-8")):
        items.append({"type": "pages", "slug": p["slug"], "title": p["title"], "desc": p.get("desc", ""),
                      "seo_title": p.get("seo_title") or p["title"],
                      "content": _content(p)})
    for p in json.load(io.open(os.path.join(HERE, "articles", "manifest.json"), encoding="utf-8")):
        items.append({"type": "posts", "slug": p["slug"], "title": p["title"], "desc": p.get("desc", ""),
                      "seo_title": p.get("seo_title") or p["title"],
                      "content": _content(p)})
    # ブラウザ側で bundle を組み立て直せるように、公開用CSS（コメント除去済み）も
    # Git管理下に書き出す（raw.githubusercontent.com から取得して使う）。
    with io.open(os.path.join(HERE, "page-css.css"), "w", encoding="utf-8") as f:
        f.write(PAGE_CSS)

    out = os.path.join(HERE, "publish")
    os.makedirs(out, exist_ok=True)
    with io.open(os.path.join(out, "bundle.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    print("bundle:", len(items), "items, no desc:", [i["slug"] for i in items if not i["desc"]])


if __name__ == "__main__":
    main()
