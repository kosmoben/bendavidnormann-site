#!/usr/bin/env python3
"""Build the static bendavidnormann.com site from content.json into ../dist.

Usage:
  python3 build.py                 # build HTML only (images referenced from /img/)
  python3 build.py --fetch-images  # also download images missing from src/img from the Squarespace CDN
Images live in src/img (copied from Squarespace on 2026-11-21), so the site no longer depends on Squarespace.
"""
import html, json, os, re, shutil, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
SITE = "Ben David Normann"
# Contact link: all mail from the site goes to normann.formidling@gmail.com (Ben, 2026-11-21).
CONTACT = "mailto:normann.formidling@gmail.com?subject=Contact%20from%20bendavidnormann.com"
# Two languages: Norwegian (default on .no) and English (default on .com).
# The Worker (worker.js) picks the front page by domain, or by the visitor's own choice (?lang=).
T = {
 "no": {"nav": [("Kosmologi med Ben", "https://filmfreeway.com/projects/4033265"),
                ("Nyans", "https://www.ntnu.no/nyans"), ("Om meg", "/about")],
        "book": "/no/book-ben", "book_me": "Book meg", "clients": "Oppdragsgivere blant annet", "projects": "Prosjekter", "follow": "Følg meg",
        "hi": "Hei, jeg er Ben", "more": "Mer om meg →", "explore": "Utforsk", "scroll": "Bla ned",
        "back": "← Tilbake", "contact": "Kontakt", "menu": "Meny", "front": "forsiden",
        "switch": ("EN", "English", "/?lang=en"),
        "desc": "Ben David Normann: kosmolog, fysiker, foredragsholder og konferansier. "
                "Kosmologi, fysikk og matematikk ved NTNU i Ålesund."},
 "en": {"nav": [("Cosmology-with-Ben", "https://filmfreeway.com/projects/4033265"),
                ("Nyans", "https://www.ntnu.no/nyans"), ("About", "/about")],
        "book": "/book-ben", "book_me": "Book me", "clients": "Clients include", "projects": "Projects", "follow": "Follow",
        "hi": "Hi, I'm Ben", "more": "More about me →", "explore": "Explore", "scroll": "Scroll down",
        "back": "← Back", "contact": "Contact", "menu": "Menu", "front": "front page",
        "switch": ("NO", "Norsk", "/?lang=no"),
        "desc": "Ben David Normann: presenter, academic, teacher and author. "
                "Cosmology, physics and mathematics at NTNU Ålesund."},
}
FLAGS = {
 # Small inline flags for the language switch.
 "no": '<svg viewBox="0 0 22 16" width="26" height="19" aria-hidden="true"><rect width="22" height="16" fill="#ba0c2f"/>'
       '<path d="M6 0h4v16H6zM0 6h22v4H0z" fill="#fff"/><path d="M7 0h2v16H7zM0 7h22v2H0z" fill="#00205b"/></svg>',
 "en": '<svg viewBox="0 0 60 30" width="26" height="13" aria-hidden="true"><clipPath id="uk"><path d="M0 0v30h60V0z"/></clipPath>'
       '<clipPath id="ukt"><path d="M30 15h30v15zv15H0zH0V0zV0h30z"/></clipPath><g clip-path="url(#uk)">'
       '<path d="M0 0v30h60V0z" fill="#012169"/><path d="M0 0l60 30m0-30L0 30" stroke="#fff" stroke-width="6"/>'
       '<path d="M0 0l60 30m0-30L0 30" clip-path="url(#ukt)" stroke="#C8102E" stroke-width="4"/>'
       '<path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></g></svg>',
}
LINKS = json.load(open(os.path.join(HERE, "links.json"), encoding="utf-8"))
CHANNELS = [c for c in LINKS["channels"] if c.get("url")]
SOCIAL = [(c["name"], c["url"], c.get("icon", "link")) for c in CHANNELS]
ICONS = {
 "yt": '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M23 7.2a3 3 0 00-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 001 7.2 31 31 0 00.6 12a31 31 0 00.4 4.8 3 3 0 002.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 002.1-2.1 31 31 0 00.4-4.8 31 31 0 00-.4-4.8zM9.7 15.1V8.9l5.8 3.1z"/></svg>',
 "tt": '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M16.6 3c.3 2.3 1.7 3.9 4 4.1v3.2a7.5 7.5 0 01-4-1.2v6.3a6 6 0 11-6-6c.3 0 .7 0 1 .1v3.3a2.8 2.8 0 102 2.6V3z"/></svg>',
 "x": '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M17.8 3h3.3l-7.2 8.2L22.3 21h-6.6l-5.2-6.8L4.6 21H1.3l7.7-8.8L1 3h6.8l4.7 6.2zm-1.2 16h1.8L6.6 4.9H4.7z"/></svg>',
 "link": '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 14a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 10a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1"/></svg>',
 "ig": '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>',
 "fb": '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M14 8h3V4h-3c-2.8 0-4 1.7-4 4.3V10H7v4h3v8h4v-8h3l1-4h-4V8.6c0-.4.3-.6.6-.6z"/></svg>',
 "in": '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M4 9h3.5v11H4zM5.8 3.5a2 2 0 110 4 2 2 0 010-4zM9.5 9h3.4v1.5c.5-.9 1.7-1.8 3.4-1.8 3.6 0 4.2 2.3 4.2 5.3V20H17v-5.3c0-1.3 0-2.9-1.8-2.9s-2.1 1.4-2.1 2.8V20H9.5z"/></svg>',
}

images = {}  # remote url -> local file name


def img(url):
    """Map a Squarespace CDN url to a stable local /img/ path."""
    if url not in images:
        name = urllib.parse.unquote(url.rstrip("/").split("/")[-1]).replace("+", "-")
        name = re.sub(r"[^A-Za-z0-9._-]", "-", name).lower()
        stem, ext = os.path.splitext(name)
        ext = ext if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp") else ".jpg"
        candidate, i = stem + ext, 2
        while candidate in images.values():
            candidate, i = f"{stem}-{i}{ext}", i + 1
        images[url] = candidate
    return "/img/" + images[url]


def tr(v, lang):
    """Text in links.json is either one string or {"no": ..., "en": ...}."""
    if isinstance(v, dict):
        return v.get(lang) or v.get("en") or v.get("no") or ""
    return v or ""


def esc(s):
    return html.escape(s or "", quote=True)


def link_attrs(href):
    href = CONTACT if href == "@CONTACT@" else href
    ext = href.startswith("http")
    return f'href="{esc(href)}"' + (' target="_blank" rel="noopener"' if ext else "")


def figure(src, alt="", cap=None, href=None, cls=""):
    inner = f'<img src="{img(src)}" alt="{esc(alt or cap)}" loading="lazy">'
    if href:
        inner = f"<a {link_attrs(href)}>{inner}</a>"
    c = f"<figcaption>{esc(cap)}</figcaption>" if cap else ""
    return f'<figure class="{cls}">{inner}{c}</figure>'


def tile(i):
    if i.get("href"):
        return (f'<a class="tile" {link_attrs(i["href"])}><img src="{img(i["img"])}" alt="{esc(i.get("cap"))}" '
                f'loading="lazy"><span>{esc(i.get("cap"))}</span></a>')
    return figure(i["img"], i.get("cap", ""), i.get("cap"), cls="tile")


def render_block(b):
    if "html" in b:
        return f'<div class="prose">{b["html"]}</div>'
    if "youtube" in b:
        v = esc(b["youtube"])
        return (f'<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{v}" '
                'title="YouTube video" loading="lazy" allowfullscreen '
                'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"></iframe></div>')
    if "button" in b:
        return f'<p class="btn-row"><a class="btn" {link_attrs(b["href"])}>{esc(b["button"])}</a></p>'
    if "grid" in b:
        return '<div class="grid">' + "".join(tile(i) for i in b["grid"]) + "</div>"
    if "cards" in b:
        out = [f'<div class="card"><h3>{esc(c["title"])}</h3>'
               f'{figure(c["img"], c.get("alt"), None, c.get("href"))}<p>{esc(c["text"])}</p></div>'
               for c in b["cards"]]
        return f'<div class="cards">{"".join(out)}</div>'
    if "gallery" in b:
        return '<div class="gallery">' + "".join(
            figure(g["img"], g.get("cap") or SITE, g.get("cap")) for g in b["gallery"]) + "</div>"
    if "img" in b:
        return figure(b["img"], b.get("alt", ""), b.get("cap"), b.get("href"), cls="wide")
    raise ValueError(b)


def hero_variant(v, lang):
    """Simplified hero proposals (2026-11-22): a = centred, b = text left/logo right, c = name only, tiny logo."""
    t = T[lang]; intro = LINKS["intro"]
    who, book = esc(tr(intro.get("who"), lang)), esc(tr(intro.get("bookable"), lang))
    cta = (f'<p class="hero-cta"><a class="btn" href="{t["book"]}">Book Ben!</a> '
           f'<a class="btn ghost" href="#projects">{t["explore"]}</a></p>')
    logo = '<img class="hl" src="/brand/logo-arc.svg" alt="" width="560" height="390">'
    if v == "a":
        inner = f'{logo}<h1>Ben David Normann</h1><p class="who">{who}</p><p class="book">{book}</p>{cta}'
    elif v == "b":
        inner = (f'<div class="hv-text"><h1>Ben David Normann</h1><p class="who">{who}</p><p class="book">{book}</p>{cta}</div>'
                 f'<div class="hv-logo">{logo}</div>')
    else:
        inner = f'<h1>Ben David Normann</h1><p class="who">{who}</p><p class="book">{book}</p>{cta}'
    return (f'<section class="hero hv hv-{v}">{inner}'
            f'<a class="scroll" href="#about" aria-label="{t["scroll"]}">↓</a></section>\n')


def render_home(p, lang):
    t = T[lang]
    intro = LINKS["intro"]
    chans = "".join(
        f'<a class="chan" {link_attrs(c["url"])}>{ICONS.get(c.get("icon"), ICONS["link"])}'
        f'<span><b>{esc(c["name"])}</b><small>{esc(c.get("handle"))}</small></span></a>' for c in CHANNELS)
    projects = []
    for pr in LINKS["projects"]:
        pic = f'<img src="{img(pr["img"])}" alt="" loading="lazy">' if pr.get("img") else ""
        extra = pr.get("extra")
        title_html = (f'<img class="title-logo" src="{pr["title_img"]}" alt="{esc(tr(pr["title"], lang))}">'
                      if pr.get("title_img") else esc(tr(pr["title"], lang)))
        extra_html = f'<a class="more" {link_attrs(extra["href"])}>{esc(tr(extra["label"], lang))} →</a>' if extra else ""
        projects.append(
            f'<article class="project"><a class="cover" {link_attrs(pr["href"])} tabindex="-1">{pic}</a>'
            f'<div class="body"><p class="status">{esc(tr(pr.get("status"), lang))}</p>'
            f'<h3><a {link_attrs(pr["href"])}>{title_html}</a></h3>'
            f'<p>{esc(tr(pr.get("text"), lang))}</p>{extra_html}</div></article>')
    booking = ""
    clients = ""
    if LINKS.get("clients"):
        names = "".join(f"<li>{esc(tr(c, lang))}</li>" for c in LINKS["clients"])
        clients = f'<div class="clients"><p>{t["clients"]}</p><ul>{names}</ul></div>'
    if LINKS.get("booking"):
        cards = "".join(f'<div class="book-card"><span class="spark" aria-hidden="true">✦</span>'
                        f'<h3>{esc(tr(b["title"], lang))}</h3><p>{esc(tr(b["text"], lang))}</p></div>'
                        for b in LINKS["booking"])
        booking = (f'<section class="band"><h2><span class="spark">✦</span> {t["book_me"]}</h2><div class="booking">{cards}</div>'
                   f'{clients}<p class="btn-row"><a class="btn" href="{t["book"]}">Book Ben!</a></p></section>')
    if p.get("hero"):
        hero = hero_variant(p["hero"], lang)
    else:
        hero = None
    split = f"""<section class="hero split">
  <div class="hero-text">
    <p class="eyebrow">Ben David Normann</p>
    <h1>{esc(tr(intro.get("title"), lang))}</h1>
    <p class="lead">{esc(tr(intro.get("lead"), lang))}</p>
    <p class="hero-cta"><a class="btn" href="{t["book"]}">Book Ben!</a> <a class="btn ghost" href="#projects">{t["explore"]}</a></p>
  </div>
  <div class="hero-logo"><p class="tagline">{esc(tr(intro.get("tagline"), lang))}</p><img src="/brand/logo-arc.svg" alt="Ben David Normann" width="560" height="390"></div>
  <a class="scroll" href="#about" aria-label="{t["scroll"]}">↓</a>
</section>
"""
    return (hero or split) + f"""<section class="band about" id="about">
  <img class="portrait" src="{img(intro["img"])}" alt="Ben David Normann" loading="lazy">
  <div><h2><span class="spark">✦</span> {t["hi"]}</h2>{"".join(f"<p>{esc(par)}</p>" for par in tr(intro["text"], lang).split(chr(10) + chr(10)))}
  <p><a class="more" href="/about">{t["more"]}</a></p></div>
</section>
{booking}
<section class="band" id="projects"><h2><span class="spark">✦</span> {t["projects"]}</h2><div class="projects">{"".join(projects)}</div></section>
<section class="band"><h2><span class="spark">✦</span> {t["follow"]}</h2><div class="chans">{chans}</div></section>"""


def page(path, p, theme=None):
    lang = p.get("lang", "en")
    t = T[lang]
    home = p.get("kind") == "home"
    title = SITE if home else f'{p["title"]} — {SITE}'
    nav = "".join(
        f'<a {link_attrs(h)}' + (' aria-current="page"' if h == path or (h == "/" and home) else "")
        + f'>{esc(label)}</a>' for label, h in t["nav"])
    code, name, href = t["switch"]
    if path in ("/book-ben", "/no/book-ben"):
        href = T["en" if lang == "no" else "no"]["book"]
    nav += (f'<a class="lang" href="{href}" hreflang="{code.lower()}" lang="{code.lower()}" title="{name}" '
            f'aria-label="{name}">{FLAGS[code.lower()]}</a>')
    stamp = tr(LINKS.get("stamp"), lang)
    stamp_html = f'<div class="stamp-overlay" aria-hidden="true"><span>{esc(stamp)}</span></div>' if stamp else ""
    social = "".join(
        f'<a href="{h}" target="_blank" rel="noopener" aria-label="{t}">{ICONS[k]}</a>' for t, h, k in SOCIAL)
    body = render_home(p, lang) if home else "".join(render_block(b) for b in p["blocks"])
    theme_css = (f'\n<link rel="stylesheet" href="/themes/{theme}.css"><meta name="robots" content="noindex">'
                 if theme else "")
    back = f'<p class="back"><a href="{esc(p["back"])}">{t["back"]}</a></p>' if p.get("back") else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(t["desc"])}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/brand/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/brand/apple-touch-icon-180.png">
<meta name="theme-color" content="#050505">
<meta property="og:title" content="{esc(title)}">
<meta property="og:image" content="/brand/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Architects+Daughter&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">{theme_css}
</head>
<body>
<canvas id="sky" aria-hidden="true"></canvas>
<header class="site-header">
  <a class="brand" href="/" aria-label="{SITE}, {t["front"]}"><img src="/brand/stamp.svg" alt="{SITE}" width="56" height="56"></a>
  <input type="checkbox" id="menu" hidden><label for="menu" class="burger" aria-label="{t["menu"]}">☰</label>
  <nav>{nav}<span class="social">{social}</span><a class="btn" href="{t["book"]}">Book Ben!</a></nav>
</header>
<main>{back}{body}</main>
<footer class="site-footer">
  <a class="stamp" href="/" aria-label="{SITE}"><img src="/brand/stamp.svg" alt="" width="96" height="96" loading="lazy"></a>
  <span class="copy">© Ben David Normann</span>
  <span class="social">{social}</span>
  <a {link_attrs("@CONTACT@")}>{t["contact"]}</a>
</footer>
{stamp_html}
<script src="/sky.js" defer></script>
</body>
</html>
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    content = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    img_dir = os.path.join(DIST, "img")
    if os.path.isdir(DIST):
        for n in os.listdir(DIST):
            if n != "img":
                q = os.path.join(DIST, n)
                shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
    for path, p in content.items():
        out = os.path.join(DIST, path.strip("/"), "index.html") if path != "/" else os.path.join(DIST, "index.html")
        write(out, page(path, p))
        if path == "/":
            write(os.path.join(DIST, "no", "index.html"), page(path, p))
    # Design proposals: the front page with an alternative theme stylesheet.
    themes_dir = os.path.join(HERE, "themes")
    if os.path.isdir(themes_dir):
        shutil.copytree(themes_dir, os.path.join(DIST, "themes"), dirs_exist_ok=True)
        for f in sorted(os.listdir(themes_dir)):
            name = os.path.splitext(f)[0]
            write(os.path.join(DIST, f"design-{name}", "index.html"), page("/", content["/"], theme=name))
    write(os.path.join(DIST, "404.html"), page("/404", {"title": "Not found", "blocks": [
        {"html": "<h1>Page not found</h1><p>Sorry, that page does not exist.</p>"},
        {"button": "Go to the front page", "href": "/"}]}))
    for f in ("style.css", "sky.js", "favicon.svg", "_redirects", "_headers"):
        shutil.copy(os.path.join(HERE, f), os.path.join(DIST, f))
    shutil.copytree(os.path.join(HERE, "brand"), os.path.join(DIST, "brand"), dirs_exist_ok=True)
    with open(os.path.join(ROOT, "images.json"), "w") as f:
        json.dump(images, f, indent=1)
    print(f"Built {len(content)} pages, {len(images)} images referenced.")
    # Images committed to the repo live in src/img; copy them into dist/img.
    os.makedirs(img_dir, exist_ok=True)
    src_img = os.path.join(HERE, "img")
    if os.path.isdir(src_img):
        for n in os.listdir(src_img):
            shutil.copy(os.path.join(src_img, n), os.path.join(img_dir, n))
    if "--fetch-images" in sys.argv:
        for url, name in images.items():
            dest = os.path.join(img_dir, name)
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                continue
            src = url + ("&" if "?" in url else "?") + "format=1500w"
            print("fetch", name)
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                f.write(r.read())
        missing = [n for n in images.values() if not os.path.exists(os.path.join(img_dir, n))]
        print("All images present." if not missing else f"MISSING: {missing}")


if __name__ == "__main__":
    main()
