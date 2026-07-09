#!/usr/bin/env python3
"""
Static blog generator.

Turns Markdown files in ./posts into a fully static website in ./public that
you can host for free on Cloudflare Pages, GitHub Pages, Netlify, or any static
host. No server, no database, no login.

Workflow
--------
1. Write a post as a Markdown file in ./posts, e.g. posts/hello-world.md
   Start the file with a small metadata header:

       Title: Hello World
       Subtitle: An optional one-line summary
       Date: 2026-07-07
       Tags: recon, notes
       Draft: false

       # Your first heading
       Write the article in **Markdown** below...

   The file name (without ".md") becomes the URL, e.g. /hello-world.html

2. Pictures: drop image files into ./images and reference them in a post as
       ![A caption](images/screenshot.png)
   They are copied into the built site and displayed inline.

3. Build the site:
       python build.py            # build published posts into ./public
       python build.py --drafts   # also include posts marked Draft: true
       python build.py --serve    # build, then preview at http://127.0.0.1:8000

4. Deploy the ./public folder (see README.md).

Config (optional environment variables)
       BLOG_TITLE     site title / brand      (default: "root_notes")
       BLOG_AUTHOR    byline name             (default: "researcher")
       BLOG_TAGLINE   home-page tagline       (default: security-flavored)
"""

import os
import re
import sys
import json
import math
import shutil
import hashlib
from html import unescape
from datetime import datetime, date

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from jinja2 import Environment, FileSystemLoader, select_autoescape

# --------------------------------------------------------------------------- #
# Paths & config
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
FILES_DIR = os.path.join(BASE_DIR, "files")
OUTPUT_DIR = os.path.join(BASE_DIR, "public")

SITE = {
    "title": os.environ.get("BLOG_TITLE", "Shadow Monarch"),
    "author": os.environ.get("BLOG_AUTHOR", "Danish Ahmed"),
    "tagline": os.environ.get("BLOG_TAGLINE", "Bug bounty writeups, CTF notes, and security research."),
    "year": datetime.now().year,
    # Comments via giscus (GitHub Discussions). Fill these in to turn comments on.
    # Get the values from https://giscus.app after enabling Discussions on your repo.
    "giscus_repo": os.environ.get("BLOG_GISCUS_REPO", ""),            # e.g. "danish/blog"
    "giscus_repo_id": os.environ.get("BLOG_GISCUS_REPO_ID", ""),
    "giscus_category": os.environ.get("BLOG_GISCUS_CATEGORY", "General"),
    "giscus_category_id": os.environ.get("BLOG_GISCUS_CATEGORY_ID", ""),
}

# Custom domain for GitHub Pages. Writing a CNAME file into the build output
# keeps the domain configured across every deploy. Leave empty to skip.
CUSTOM_DOMAIN = os.environ.get("BLOG_DOMAIN", "shadowmonarch.com")

# HackTheBox profile, used for the live rank badge on the home page.
HTB_USER_ID = os.environ.get("BLOG_HTB_USER_ID", "1443864")
SITE["htb_badge_url"] = f"https://www.hackthebox.com/badge/image/{HTB_USER_ID}"
SITE["htb_profile_url"] = f"https://app.hackthebox.com/users/{HTB_USER_ID}"

# Kept in sync with the certifications listed on templates/portfolio.html.
CERT_COUNT = 7

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "PKR": "Rs "}

# Vulnerability filter chips shown under the search bar. Each entry is
# (display label, [terms matched against a post's title/tags/body]). Add or
# remove rows here to change the filter set.
VULN_FILTERS = [
    ("XSS", ["xss", "cross-site scripting", "cross site scripting"]),
    ("SQL Injection", ["sqli", "sql injection"]),
    ("SSTI", ["ssti", "template injection"]),
    ("RCE", ["rce", "remote code execution", "command execution"]),
    ("IDOR", ["idor", "insecure direct object", "bola"]),
    ("SSRF", ["ssrf", "server-side request forgery", "server side request forgery"]),
    ("CSRF", ["csrf", "cross-site request forgery"]),
    ("Race Condition", ["race condition", "race-condition"]),
    ("Open Redirect", ["open redirect", "open-redirect"]),
    ("XXE", ["xxe", "xml external entity"]),
    ("LFI / Path Traversal", ["lfi", "path traversal", "directory traversal", "/etc/passwd"]),
    ("Auth Bypass / ATO", ["auth bypass", "authentication bypass", "account takeover", "ato"]),
    ("Business Logic", ["business logic", "logic flaw"]),
    ("CORS", ["cors"]),
    ("Command Injection", ["command injection", "os command"]),
    ("Privilege Escalation", ["privilege escalation", "privesc"]),
    ("Info Disclosure", ["information disclosure", "info leak", "sensitive data"]),
    ("Subdomain Takeover", ["subdomain takeover"]),
    ("JWT", ["jwt", "json web token"]),
    ("Prototype Pollution", ["prototype pollution"]),
    ("GraphQL", ["graphql"]),
    ("File Upload", ["file upload", "unrestricted upload"]),
    ("Clickjacking", ["clickjacking"]),
    ("CTF", ["ctf", "capture the flag"]),
    ("Certificate", ["cpts", "oscp", "ceh", "crta", "crtom", "certification", "certified", "exam"]),
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def new_md():
    """A fresh Markdown instance (reset between files so metadata does not leak)."""
    return markdown.Markdown(
        extensions=[
            "meta",             # reads the Title:/Date:/... header block
            "extra",            # tables, fenced code, footnotes, etc.
            "sane_lists",
            "smarty",
            "admonition",
            "toc",
            CodeHiliteExtension(guess_lang=False, css_class="codehilite"),
        ],
        output_format="html5",
    )


def slugify(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "post"


def reading_time(html):
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html)))
    return max(1, math.ceil(words / 200))


def parse_date(value, fallback):
    if not value:
        return fallback
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return fallback


def meta_first(meta, key, default=""):
    val = meta.get(key)
    if not val:
        return default
    return val[0] if isinstance(val, list) else val


def fmt_date(d):
    return d.strftime("%b %d, %Y").replace(" 0", " ") if d else ""


def asset_version():
    """Short content hash of the assets, used to cache-bust CSS/JS URLs so the
    browser always loads the current version after a rebuild."""
    h = hashlib.md5()
    if os.path.isdir(ASSETS_DIR):
        for name in sorted(os.listdir(ASSETS_DIR)):
            p = os.path.join(ASSETS_DIR, name)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    h.update(fh.read())
    return h.hexdigest()[:8]


def plain_text(html):
    """Strip HTML down to searchable plain text."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def build_search_json(posts):
    """A JSON search index, safely embeddable inside a <script> tag."""
    records = [{
        "title": p["title"],
        "subtitle": p["subtitle"],
        "tags": p["tags"],
        "url": p["url"],
        "date": fmt_date(p["date"]),
        "reading_time": p["reading_time"],
        "text": plain_text(p["html"])[:6000],
    } for p in posts]
    # escape "<" so a literal "</script>" in any post cannot break out of the tag
    return json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")


def term_match(hay, term):
    """Whole-token match so short acronyms (rce, ato, cors) do not match inside
    unrelated words like 'e-commerce' or 'gladiator'."""
    return re.search(r"(?:^|[^a-z0-9])" + re.escape(term) + r"(?:[^a-z0-9]|$)", hay) is not None


def build_vuln_filters(posts):
    """Count how many posts match each vulnerability category."""
    haystacks = [
        " ".join([p["title"], p["subtitle"], " ".join(p["tags"]), plain_text(p["html"])]).lower()
        for p in posts
    ]
    out = []
    for label, terms in VULN_FILTERS:
        count = sum(1 for hay in haystacks if any(term_match(hay, t) for t in terms))
        out.append({"label": label, "terms": "|".join(terms), "count": count})
    # available categories first (most posts first), then the rest alphabetically
    out.sort(key=lambda f: (f["count"] == 0, -f["count"], f["label"]))
    return out


def build_home_stats(posts, vuln_filters):
    """Auto-computed stats strip: no numbers are hand-maintained, they all
    come from post metadata so a new post updates the strip on its own."""
    live_posts = [p for p in posts if not p["draft"]]

    rewards = {}
    for p in live_posts:
        if p["reward_amount"] is not None:
            rewards[p["reward_currency"]] = rewards.get(p["reward_currency"], 0) + p["reward_amount"]
    reward_lines = []
    for cur, total in sorted(rewards.items(), key=lambda kv: -kv[1]):
        symbol = CURRENCY_SYMBOLS.get(cur, cur + " ")
        amount = f"{total:,.0f}" if total == int(total) else f"{total:,.2f}"
        reward_lines.append(f"{symbol}{amount}")

    categories_covered = sum(1 for f in vuln_filters if f["count"] > 0)

    return {
        "post_count": len(live_posts),
        "reward_text": " + ".join(reward_lines) if reward_lines else None,
        "category_count": categories_covered,
        "cert_count": CERT_COUNT,
    }


# --------------------------------------------------------------------------- #
# Load posts
# --------------------------------------------------------------------------- #
def load_posts(include_drafts=False):
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts

    for name in os.listdir(POSTS_DIR):
        if not name.endswith(".md") or name.startswith("."):
            continue
        path = os.path.join(POSTS_DIR, name)
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()

        md = new_md()
        html = md.convert(raw)
        meta = getattr(md, "Meta", {})

        is_draft = meta_first(meta, "draft", "false").lower() in ("true", "1", "yes")
        if is_draft and not include_drafts:
            continue

        stem = name[:-3]
        file_mtime = date.fromtimestamp(os.path.getmtime(path))
        title = meta_first(meta, "title", stem.replace("-", " ").title())
        tags_raw = meta_first(meta, "tags", "")
        tags = [t.strip() for t in re.split(r"[,;]", tags_raw) if t.strip()]
        banner_raw = meta_first(meta, "banner", "").strip()
        show_banner = banner_raw.lower() != "none"   # "Banner: none" hides it entirely

        reward_raw = meta_first(meta, "reward", "").strip()
        reward_amount, reward_currency = None, None
        if reward_raw:
            m = re.match(r"([\d,.]+)\s*([A-Za-z]{3})?", reward_raw)
            if m:
                reward_amount = float(m.group(1).replace(",", ""))
                reward_currency = (m.group(2) or "USD").upper()

        posts.append({
            "slug": slugify(meta_first(meta, "slug", stem)),
            "title": title,
            "subtitle": meta_first(meta, "subtitle", ""),
            "banner": banner_raw if show_banner else "",
            "show_banner": show_banner,
            "date": parse_date(meta_first(meta, "date", ""), file_mtime),
            "tags": tags,
            "draft": is_draft,
            "html": html,
            "reading_time": reading_time(html),
            "url": slugify(meta_first(meta, "slug", stem)) + ".html",
            "reward_amount": reward_amount,
            "reward_currency": reward_currency,
        })

    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    return posts


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def build(include_drafts=False):
    posts = load_posts(include_drafts=include_drafts)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["fmt_date"] = fmt_date
    env.globals["asset_version"] = asset_version()

    # fresh output dir
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # copy theme assets -> public/static
    static_out = os.path.join(OUTPUT_DIR, "static")
    shutil.copytree(ASSETS_DIR, static_out)

    # also drop favicon.ico at the site root; some browsers/crawlers request
    # /favicon.ico directly regardless of the <link> tag in <head>
    favicon_src = os.path.join(ASSETS_DIR, "favicon.ico")
    if os.path.isfile(favicon_src):
        shutil.copy2(favicon_src, os.path.join(OUTPUT_DIR, "favicon.ico"))

    # copy your pictures -> public/images  (reference them as images/<file> in Markdown)
    if os.path.isdir(IMAGES_DIR):
        shutil.copytree(IMAGES_DIR, os.path.join(OUTPUT_DIR, "images"))

    # copy downloadable files (CV, etc.) -> public/files
    if os.path.isdir(FILES_DIR):
        shutil.copytree(FILES_DIR, os.path.join(OUTPUT_DIR, "files"))

    # home / feed
    # `posts` already respects include_drafts (set by load_posts); the featured
    # slot and the rest of the feed are just a split of that same list, so a
    # draft previewed via --drafts still appears (with its draft badge).
    vuln_filters = build_vuln_filters(posts)
    featured, rest = (posts[0], posts[1:]) if posts else (None, [])
    index_html = env.get_template("index.html").render(
        site=SITE, posts=rest, featured=featured,
        search_json=build_search_json(posts),
        vuln_filters=vuln_filters,
        stats=build_home_stats(posts, vuln_filters),
    )
    _write("index.html", index_html)

    # each post
    post_tpl = env.get_template("post.html")
    for p in posts:
        _write(p["url"], post_tpl.render(site=SITE, post=p))

    # portfolio / CV page
    _write("portfolio.html", env.get_template("portfolio.html").render(site=SITE))

    # 404
    _write("404.html", env.get_template("404.html").render(site=SITE, posts=posts))

    # custom domain (GitHub Pages reads this file to route the domain)
    if CUSTOM_DOMAIN:
        _write("CNAME", CUSTOM_DOMAIN + "\n")

    drafts = sum(1 for p in posts if p["draft"])
    print(f"Built {len(posts)} post(s)"
          + (f" (including {drafts} draft)" if drafts else "")
          + f" -> {os.path.relpath(OUTPUT_DIR, BASE_DIR)}/")
    return posts


def _write(rel_path, html):
    out = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)


def serve():
    import http.server
    import socketserver
    import functools

    socketserver.TCPServer.allow_reuse_address = True
    start = int(os.environ.get("PORT", "8000"))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUTPUT_DIR)

    last_err = None
    for port in range(start, start + 25):
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
        except OSError as e:
            last_err = e
            continue
        with httpd:
            if port != start:
                print(f"Port {start} was busy, using {port} instead.")
            print(f"Preview at http://127.0.0.1:{port}  (Ctrl+C to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nstopped")
        return
    print(f"Could not bind a free port in {start}-{start + 24}: {last_err}")
    print("Tip: pick one explicitly, e.g.  PORT=8090 python build.py --serve")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    drafts = "--drafts" in sys.argv
    build(include_drafts=drafts)
    if "--serve" in sys.argv:
        serve()
