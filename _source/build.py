"""Turn site.json + image-map.json into static HTML pages.

Usage: python build.py <site.json> <image-map.json> <site_dir>

Every page lives at <slug>/index.html so the old Squarespace links keep working,
and all links are relative so the site also works from a GitHub Pages sub-path.
"""
import html
import json
import sys
from pathlib import Path

MODEL = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
IMAGES = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
SITE = Path(sys.argv[3])

EMAIL = "GEORGEGARNISH@YAHOO.CO.UK"
INSTAGRAM = "https://www.instagram.com/grgarnish/"
VIMEO = "https://vimeo.com/georgegarnish"

# Menu, copied from the live site. Folders open on click; the slug is the page the
# old folder URL now redirects to.
NAV = [
    ("VIDEOS", "test-video-ayout"),
    ("PHOTOGRAPHY", [("SPORTS", "sports-2"), ("FASHION", "fashion-2"), ("MISCELLANEOUS", "random"),
                     ("PORTRAITS", "portraits-2"), ("LIFESTYLE", "life-style"), ("MUSIC", "music-1")]),
    ("EDITOR", "editor-1"),
    ("UNIT STILLS", [("SAMSUNG", "new-page-1"), ("CANON", "canon-3"), ("CAMDEN", "camden"),
                     ("MONEY SUPER MARKET", "money-super-market"), ("HIENZ", "hienz"),
                     ("LIPTON ICE TEA", "lipton-ice-tea"), ("COPPER", "copper"), ("LENOVO", "lenovo-1")]),
    ("SOCIAL MEDIA CUTS", "social-media-cuts-2"),
    ("CONCEPT PHOTOGRAPHY", [("FLASH SERIES", "flash-series"), ("EXCUSE ME", "excuse-me")]),
    ("TRAVEL SERIES", [("THIS IS AMERICA", "this-is-america"), ("JAPAN", "japan"),
                       ("SOUTH AMERICA", "south-america")]),
    ("LOCKDOWN MOVIE", "lockdown"),
]
# Old Squarespace folder URLs -> first page inside the folder.
REDIRECTS = {"portraits": "sports-2", "bts-stills-1": "new-page-1",
             "concept-photography": "flash-series", "travel-series": "this-is-america"}

ICON_INSTAGRAM = ('<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" '
                  'fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" '
                  'stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/></svg>')
ICON_VIMEO = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M22 7.4c-.1 2-1.5 4.7-4.2 '
              '8.2-2.8 3.6-5.1 5.4-7.1 5.4-1.2 0-2.3-1.1-3.1-3.4L6 11.9C5.4 9.6 4.8 8.5 4.1 8.5c-.1 0-.7.3-1.6 1L1.5 '
              '8.2l2.9-2.6C5.7 4.5 6.7 3.9 7.4 3.8c1.5-.1 2.5.9 2.8 3.2.4 2.4.6 3.9.8 4.5.4 2 .9 3 1.4 3 .4 0 1-.6 '
              '1.8-1.9.8-1.2 1.2-2.2 1.3-2.8.1-1.1-.3-1.6-1.3-1.6-.5 0-.9.1-1.4.3 1-3.1 2.8-4.6 5.4-4.5 2 .1 2.9 1.3 '
              '2.8 3.4z"/></svg>')

esc = html.escape


def img_tag(src, w, h, alt="", cls="", root="", eager=False):
    local = IMAGES[src]
    attrs = f' width="{w}" height="{h}"' if w and h else ""
    load = "" if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return f'<img src="{root}images/{local}" alt="{esc(alt)}"{attrs}{c}{load} decoding="async">'


def video_attrs(v):
    return f' data-video="{v["provider"]}:{v["id"]}"' if v else ""


def full_src(item, root):
    return f"{root}images/{IMAGES[item['src']]}"


def render_item_tile(item, root, cls, eager=False):
    """A clickable gallery/summary tile that opens the lightbox (photo or video)."""
    vid = item.get("video")
    inner = img_tag(item["src"], item["w"], item["h"], item.get("alt") or item.get("title", ""), root=root,
                    eager=eager)
    play = '<span class="play" aria-hidden="true"></span>' if vid else ""
    label = "Play video" if vid else "View full size"
    if item.get("title"):
        label += ": " + item["title"]
    return (f'<button type="button" class="{cls}" data-full="{full_src(item, root)}"{video_attrs(vid)} '
            f'aria-label="{esc(label)}">{inner}{play}</button>')


def render_block(b, root, first):
    t = b["type"]
    if t == "row":
        cols = "".join(
            f'<div class="col" style="--span:{c["span"]}">'
            + "".join(render_block(x, root, first and i == 0) for i, x in enumerate(c["children"]))
            + "</div>" for c in b["cols"])
        return f'<div class="row">{cols}</div>'

    if t == "html":
        return f'<div class="block text">{b["html"]}</div>'

    if t == "spacer":
        return f'<div class="block spacer" style="--h:{b["ar"]}%"></div>'

    if t == "video":
        return f'<div class="block video"><div class="embed" data-embed="{b["provider"]}:{b["id"]}"></div></div>'

    if t == "marquee":
        words = "".join(f"<span>{esc(w)}</span>" for w in b["items"])
        speed = max(20, int(40 / max(b["speed"], 0.1)))
        rev = " reverse" if b["direction"] == "right" else ""
        return (f'<div class="block marquee{rev}" style="--dur:{speed}s" aria-label="{esc(" ".join(b["items"]))}">'
                f'<div class="track" aria-hidden="true"><div class="run">{words}</div><div class="run">{words}</div>'
                f'<div class="run">{words}</div><div class="run">{words}</div></div></div>')

    if t == "image":
        if b["crop"]:
            img = img_tag(b["src"], b["w"], b["h"], b["alt"], root=root, eager=first)
            pic = f'<div class="crop" style="--pb:{b["crop"]}%">{img}</div>'
        else:
            pic = img_tag(b["src"], b["w"], b["h"], b["alt"], root=root, eager=first)
        if b.get("link"):
            pic = f'<a href="{esc(b["link"])}">{pic}</a>'
        else:
            pic = (f'<button type="button" class="tile plain" data-full="{full_src(b, root)}" '
                   f'aria-label="View full size">{pic}</button>')
        cap = f'<div class="caption">{b["caption"]}</div>' if b.get("caption") else ""
        # Squarespace never stretched an image past its own size, so small ones stay small and centred.
        small = f' style="max-width:{b["w"]}px"' if b["w"] and b["w"] < 1000 else ""
        return f'<figure class="block image"{small}>{pic}{cap}</figure>'

    if t == "gallery":
        items = b["items"]
        d = b["design"]
        if d == "grid":
            ar = {"square": "1/1", "standard": "3/2"}.get(b["ar"], "1/1")
            tiles = "".join(render_item_tile(it, root, "tile", eager=first and i < 6) for i, it in enumerate(items))
            return (f'<div class="block gallery-grid lb-group fit-{b["fit"]}" style="--cols:{b["perrow"]};--gap:{b["pad"]}px;'
                    f'--ar:{ar}">{tiles}</div>')
        if d == "slider":
            tiles = "".join(render_item_tile(it, root, "tile", eager=first and i < 3) for i, it in enumerate(items))
            auto = f' data-autoplay="{b["duration"]}"' if b["autoplay"] else ""
            ctrl = ('<button type="button" class="arrow prev" aria-label="Previous"></button>'
                    '<button type="button" class="arrow next" aria-label="Next"></button>')
            return (f'<div class="block slider lb-group" style="--h:{b["sliderHeight"]}"{auto}>'
                    f'<div class="strip">{tiles}</div>{ctrl}</div>')
        if d == "slideshow":
            slides = "".join(
                f'<div class="slide{" on" if i == 0 else ""}">{render_item_tile(it, root, "tile", eager=first and i == 0)}'
                + (f'<div class="meta">{esc(it["title"])}</div>' if it["title"] else "") + '</div>'
                for i, it in enumerate(items))
            thumbs = "".join(
                f'<button type="button" class="thumb{" on" if i == 0 else ""}" aria-label="Show image {i + 1}">'
                f'{img_tag(it["src"], it["w"], it["h"], "", root=root)}</button>' for i, it in enumerate(items))
            auto = f' data-autoplay="{b["duration"]}"' if b["autoplay"] else ""
            return (f'<div class="block slideshow lb-group"{auto}><div class="stage">{slides}'
                    f'<button type="button" class="arrow prev" aria-label="Previous"></button>'
                    f'<button type="button" class="arrow next" aria-label="Next"></button></div>'
                    f'<div class="thumbs">{thumbs}</div></div>')
        raise ValueError(f"unknown gallery design {d}")

    if t == "summary":
        cards = []
        for i, it in enumerate(b["items"]):
            tile = render_item_tile(it, root, "tile", eager=first and i < 4)
            title = f'<div class="title">{esc(it["title"])}</div>' if it["title"] else ""
            ratio = (f' style="--ar:{b["ar"]}"' if b["ar"] and b["design"] == "autogrid" else "")
            cards.append(f'<div class="card"{ratio}>{tile}{title}</div>')
        if b["design"] == "autocolumns":
            return (f'<div class="block masonry lb-group" style="--colw:{b["colwidth"] or 300};--gap:{b["gutter"]}px">'
                    + "".join(cards) + "</div>")
        fixed = " fixed-ar" if b["ar"] else ""
        return (f'<div class="block autogrid lb-group{fixed}" style="--colw:{b["colwidth"] or 300};'
                f'--cols:{b["perrow"]};--gap:{b["gutter"]}px">'
                + "".join(cards) + "</div>")

    raise ValueError(f"unknown block {t}")


def nav_html(current, root):
    def link(label, slug):
        on = ' class="on" aria-current="page"' if slug == current else ""
        return f'<li><a href="{root}{slug}/"{on}>{label}</a></li>'

    items = []
    for label, target in NAV:
        if isinstance(target, str):
            items.append(link(label, target))
        else:
            open_ = any(s == current for _, s in target)
            sub = "".join(link(l, s) for l, s in target)
            items.append(f'<li class="folder{" open" if open_ else ""}">'
                         f'<button type="button" aria-expanded="{str(open_).lower()}">{label}</button>'
                         f'<ul>{sub}</ul></li>')
    about_on = ' class="on" aria-current="page"' if current == "about" else ""
    return f"""<header class="side">
  <a class="logo" href="{root or './'}"><img src="{root}assets/logo.png" alt="George Garnish — Director | Photographer | Editor" width="750" height="167"></a>
  <button type="button" class="menu-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button>
  <nav id="site-nav">
    <ul class="main">{''.join(items)}</ul>
    <ul class="secondary">
      <li><a href="{root}about/"{about_on}>ABOUT ME</a></li>
      <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
    </ul>
    <div class="social">
      <a href="{INSTAGRAM}" target="_blank" rel="noopener" aria-label="Instagram">{ICON_INSTAGRAM}</a>
      <a href="{VIMEO}" target="_blank" rel="noopener" aria-label="Vimeo">{ICON_VIMEO}</a>
    </div>
  </nav>
</header>"""


def page_html(slug, page, root):
    title = page["title"]
    body = "\n".join(render_block(b, root, i == 0) for i, b in enumerate(page["blocks"]))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="George Garnish — video director, photographer and editor based in London.">
<link rel="icon" href="{root}favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800;900&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
{nav_html(slug, root)}
<main>
{body}
</main>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


def redirect_html(target):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>GEORGE GARNISH</title>
<meta http-equiv="refresh" content="0; url=../{target}/">
<link rel="canonical" href="../{target}/"></head>
<body><a href="../{target}/">Continue</a></body></html>
"""


for slug, page in MODEL["pages"].items():
    if slug == "home":
        (SITE / "index.html").write_text(page_html("home", page, ""), encoding="utf-8")
    else:
        d = SITE / slug
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page_html(slug, page, "../"), encoding="utf-8")

for old, target in REDIRECTS.items():
    d = SITE / old
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(redirect_html(target), encoding="utf-8")

# Friendly 404 that GitHub Pages serves for unknown URLs (root-relative on purpose:
# it can be served from any depth). Uses the home page layout.
notfound = {"title": "Page not found — GEORGE GARNISH",
            "blocks": [{"type": "html", "html": '<h1 style="text-align:center">PAGE NOT FOUND</h1>'
                        '<p style="text-align:center"><a href="/">Back to the home page</a></p>'}]}
(SITE / "404.html").write_text(page_html("404", notfound, "/"), encoding="utf-8")

print("built", len(MODEL["pages"]), "pages +", len(REDIRECTS), "redirects + 404")
