# root_notes

A personal, single-author blog for a security researcher. You write each post as
a **Markdown** file, run one build command, and get a fully **static website**
(plain HTML + CSS). There is no server, no database, and no login, so there is
nothing to hack, patch, or pay for. Host it **free** on Cloudflare Pages or
GitHub Pages. It keeps a dark, terminal-inspired theme with syntax-highlighted
code.

## Project layout

```
myblog/
  build.py            the static site generator (run this)
  posts/              your articles, one Markdown file per post
  images/             pictures you reference from posts
  templates/          HTML theme (Jinja2)
  assets/             style.css + pygments.css (the dark theme)
  public/             GENERATED output (this is what you deploy)
  requirements.txt
  .github/workflows/  optional auto-deploy to GitHub Pages
  flask-version/      the earlier "web editor" version, kept as a backup
```

## Write a post

Create a file in `posts/`, for example `posts/my-first-writeup.md`. The file name
becomes the URL (`my-first-writeup.html`). Start it with a small header:

```
Title: My First Writeup
Subtitle: An optional one-line summary
Date: 2026-07-07
Tags: recon, idor
Draft: false

# Your first heading

Write the article in **Markdown** here.
```

Supported: headings, **bold**/*italic*, lists, links, tables, blockquotes,
footnotes, `!!! note` callouts, and fenced code blocks with syntax highlighting.

### Add pictures

Drop image files into `images/` and reference them in a post:

```markdown
![A short caption](images/screenshot.png)
```

PNG, JPG, GIF, WebP, and SVG all work. They are copied into the built site
automatically.

## Build it

```bash
pip install -r requirements.txt     # first time only

python build.py           # build published posts into ./public
python build.py --drafts  # also include posts marked "Draft: true"
python build.py --serve   # build, then preview at http://127.0.0.1:8000
```

Customize the site name and byline with environment variables (optional):

```bash
export BLOG_TITLE="root_notes"
export BLOG_AUTHOR="danish"
export BLOG_TAGLINE="Security research, writeups, and field notes."
python build.py
```

## Deploy for free (pick one)

### Option A: Cloudflare Pages (easiest, no CI file needed)

1. Push this folder to a GitHub/GitLab repo.
2. Cloudflare dashboard -> Workers & Pages -> Create -> Pages -> connect your repo.
3. Build settings:
   - **Build command:** `pip install -r requirements.txt && python build.py`
   - **Build output directory:** `public`
4. Deploy. You get a free `*.pages.dev` URL with HTTPS. Every `git push` rebuilds
   and redeploys. A custom domain is free to attach.

### Option B: GitHub Pages (uses the included workflow)

1. Push this folder to a GitHub repo (branch `main`).
2. In the repo: **Settings -> Pages -> Source: GitHub Actions**.
3. The included `.github/workflows/deploy.yml` builds and publishes on every push.
   Your site appears at `https://<user>.github.io/<repo>/`.

Both are $0. HTTPS is included. A custom domain (`yourname.com`) is optional and
costs about $10 to $12 per year from any registrar.

> Tip: you never commit the `public/` folder; it is rebuilt automatically on
> deploy (that is why it is in `.gitignore`).

## The backup "web editor" version

`flask-version/` contains the original dynamic app (browser login + live-preview
editor, backed by SQLite). You do **not** need it for the static site. Keep it if
you ever want to draft posts in a browser locally:

```bash
cd flask-version
pip install Flask Markdown Pygments
python app.py   # http://127.0.0.1:5000
```
