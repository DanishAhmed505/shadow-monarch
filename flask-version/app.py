"""
A personal, single-author, Medium-style blog.

- Public side: a clean reading experience for your published articles.
- Admin side: password-protected. Write / edit / publish articles in Markdown
  with a live preview.

Run:
    python app.py
Then open http://127.0.0.1:5000

Config via environment variables (all optional):
    BLOG_ADMIN_PASSWORD   admin login password        (default: changeme)
    BLOG_SECRET_KEY       Flask session secret        (default: random each run)
    BLOG_TITLE            site title                  (default: "My Blog")
    BLOG_AUTHOR           author name shown in byline (default: "Me")
    BLOG_TAGLINE          short site tagline
    BLOG_DB               sqlite file path            (default: blog.db)
"""

import os
import re
import math
import sqlite3
import secrets
from datetime import datetime, timezone
from functools import wraps

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from flask import (
    Flask, g, request, session, redirect, url_for, render_template,
    abort, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("BLOG_SECRET_KEY", secrets.token_hex(32)),
    DATABASE=os.environ.get("BLOG_DB", os.path.join(BASE_DIR, "blog.db")),
    SITE_TITLE=os.environ.get("BLOG_TITLE", "My Blog"),
    AUTHOR=os.environ.get("BLOG_AUTHOR", "Me"),
    TAGLINE=os.environ.get("BLOG_TAGLINE", "Security research, writeups, and field notes."),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# The admin password is hashed once at startup. Change it by setting
# BLOG_ADMIN_PASSWORD before launching.
_ADMIN_PASSWORD = os.environ.get("BLOG_ADMIN_PASSWORD", "changeme")
ADMIN_PASSWORD_HASH = generate_password_hash(_ADMIN_PASSWORD)


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            slug       TEXT    NOT NULL UNIQUE,
            subtitle   TEXT    NOT NULL DEFAULT '',
            content    TEXT    NOT NULL DEFAULT '',
            published  INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    NOT NULL,
            updated_at TEXT    NOT NULL
        )
        """
    )
    db.commit()
    db.close()


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def slugify(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "post"


def unique_slug(db, base, exclude_id=None):
    slug = base
    n = 2
    while True:
        row = db.execute(
            "SELECT id FROM posts WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None or row["id"] == exclude_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


def render_markdown(text):
    md = markdown.Markdown(
        extensions=[
            "extra",            # tables, fenced code, footnotes, etc.
            "sane_lists",
            "smarty",           # nice quotes / dashes
            "admonition",
            "toc",
            CodeHiliteExtension(guess_lang=False, css_class="codehilite"),
        ],
        output_format="html5",
    )
    return md.convert(text or "")


def reading_time(text):
    words = len(re.findall(r"\w+", text or ""))
    return max(1, math.ceil(words / 200))


def fmt_date(iso):
    try:
        dt = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return ""
    return dt.strftime("%b %-d, %Y")


app.jinja_env.filters["fmt_date"] = fmt_date


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("csrf")
        form_token = request.form.get("csrf") or request.headers.get("X-CSRF-Token")
        if not token or not form_token or not secrets.compare_digest(token, form_token):
            abort(400, "Invalid CSRF token")


@app.context_processor
def inject_globals():
    return {
        "SITE_TITLE": app.config["SITE_TITLE"],
        "AUTHOR": app.config["AUTHOR"],
        "TAGLINE": app.config["TAGLINE"],
        "is_admin": bool(session.get("is_admin")),
        "year": datetime.now().year,
    }


# --------------------------------------------------------------------------- #
# Public routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM posts WHERE published = 1 ORDER BY created_at DESC"
    ).fetchall()
    items = []
    for p in posts:
        items.append({
            "row": p,
            "reading_time": reading_time(p["content"]),
        })
    return render_template("index.html", items=items)


@app.route("/post/<slug>")
def post(slug):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
    if p is None:
        abort(404)
    if not p["published"] and not session.get("is_admin"):
        abort(404)
    html = render_markdown(p["content"])
    return render_template(
        "post.html",
        post=p,
        content_html=html,
        reading_time=reading_time(p["content"]),
    )


# --------------------------------------------------------------------------- #
# Auth routes
# --------------------------------------------------------------------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["is_admin"] = True
            csrf_token()
            nxt = request.args.get("next") or url_for("admin")
            if not nxt.startswith("/"):
                nxt = url_for("admin")
            return redirect(nxt)
        flash("Wrong password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Admin routes
# --------------------------------------------------------------------------- #
@app.route("/admin")
@login_required
def admin():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM posts ORDER BY updated_at DESC"
    ).fetchall()
    return render_template("admin.html", posts=posts)


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        return _save_post(None)
    empty = {"id": None, "title": "", "subtitle": "", "content": "", "published": 0}
    return render_template("editor.html", post=empty, is_new=True)


@app.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if p is None:
        abort(404)
    if request.method == "POST":
        return _save_post(post_id)
    return render_template("editor.html", post=p, is_new=False)


def _save_post(post_id):
    db = get_db()
    title = (request.form.get("title") or "").strip() or "Untitled"
    subtitle = (request.form.get("subtitle") or "").strip()
    content = request.form.get("content") or ""
    # "publish" button vs "save draft" button
    published = 1 if request.form.get("action") == "publish" else 0
    ts = now_iso()

    if post_id is None:
        slug = unique_slug(db, slugify(title))
        cur = db.execute(
            """INSERT INTO posts (title, slug, subtitle, content, published, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, slug, subtitle, content, published, ts, ts),
        )
        db.commit()
        new_id = cur.lastrowid
        flash("Published." if published else "Saved as draft.", "ok")
        return redirect(url_for("edit_post", post_id=new_id))
    else:
        existing = db.execute(
            "SELECT slug FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        # keep slug stable once created; only regenerate if empty
        slug = existing["slug"] if existing else unique_slug(db, slugify(title))
        db.execute(
            """UPDATE posts SET title=?, subtitle=?, content=?, published=?, updated_at=?
               WHERE id=?""",
            (title, subtitle, content, published, ts, post_id),
        )
        db.commit()
        flash("Published." if published else "Saved.", "ok")
        return redirect(url_for("edit_post", post_id=post_id))


@app.route("/admin/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("Deleted.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/preview", methods=["POST"])
@login_required
def preview():
    text = request.form.get("content", "")
    return jsonify({"html": render_markdown(text)})


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f" * Blog admin password is set from BLOG_ADMIN_PASSWORD "
          f"(currently: {'default \"changeme\"' if _ADMIN_PASSWORD == 'changeme' else 'custom'})")
    app.run(host="127.0.0.1", port=port, debug=bool(os.environ.get("BLOG_DEBUG")))
