"""Read the saved Squarespace pages and turn each one into a simple JSON model.

Usage: python extract.py <raw_dir> <out_json>
"""
import html as H
import json
import re
import sys
import urllib.parse as U
from pathlib import Path

from bs4 import BeautifulSoup

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])

PAGES = [
    "home", "test-video-ayout", "sports-2", "fashion-2", "random", "portraits-2",
    "life-style", "music-1", "editor-1", "new-page-1", "canon-3", "camden",
    "money-super-market", "hienz", "lipton-ice-tea", "copper", "lenovo-1",
    "social-media-cuts-2", "flash-series", "excuse-me", "this-is-america", "japan",
    "south-america", "lockdown", "about",
]


def clean_src(u):
    if not u:
        return None
    u = u.split("?")[0]
    if u.startswith("//"):
        u = "https:" + u
    return u


def dims(img):
    d = img.get("data-image-dimensions") or ""
    m = re.match(r"(\d+)x(\d+)", d)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def img_info(img):
    if img is None:
        return None
    src = clean_src(img.get("data-src") or img.get("data-image") or img.get("src"))
    if not src:
        return None
    w, h = dims(img)
    return {"src": src, "w": w, "h": h, "alt": img.get("alt", "")}


def video_from(wrapper):
    """Pull the YouTube / Vimeo id out of a Squarespace video wrapper."""
    raw = wrapper.get("data-html", "") if wrapper else ""
    t = U.unquote(H.unescape(H.unescape(raw)))
    m = re.search(r"(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})", t)
    if m:
        return {"provider": "youtube", "id": m.group(1)}
    m = re.search(r"vimeo\.com/(?:video/)?([0-9]{6,})", t)
    if m:
        return {"provider": "vimeo", "id": m.group(1)}
    return None


def text_html(block, sel=".sqs-html-content"):
    c = block.select_one(sel)
    if not c:
        return ""
    for el in c.find_all(True):
        style = el.get("style", "")
        keep = re.search(r"text-align:\s*(left|center|right)", style)
        el.attrs = {k: v for k, v in el.attrs.items() if k in ("href", "target")}
        if keep:
            el["style"] = f"text-align:{keep.group(1)}"
    inner = "".join(str(x) for x in c.contents).strip()
    if not c.get_text(strip=True).replace("\xa0", ""):
        return ""
    return inner


def parse_block(b):
    cl = b.get("class", [])
    defn = b.get("data-definition-name", "")
    if "html-block" in cl:
        h = text_html(b)
        return {"type": "html", "html": h} if h else None
    if "image-block" in cl:
        img = b.select_one("img[data-src], img[data-image]")
        info = img_info(img)
        if not info:
            return None
        a = b.select_one("a[href]")
        cap = b.select_one(".image-caption")
        # Cropped image blocks carry their shape as padding-bottom (height as % of width).
        box = b.select_one(".has-aspect-ratio")
        m = re.search(r"padding-bottom:\s*([\d.]+)%", box.get("style", "")) if box else None
        return {"type": "image", **info, "crop": float(m.group(1)) if m else None,
                "link": a["href"] if a else None,
                "caption": text_html(b, ".image-caption") if cap else ""}
    if "gallery-block" in cl:
        j = json.loads(b.get("data-block-json", "{}"))
        items = []
        # Slider galleries put the images straight into .sqs-gallery with no .slide wrappers.
        slides = b.select(".slide") or b.select(".sqs-gallery > img.thumb-image")
        for s in slides:
            if s.name == "img":
                items.append({**img_info(s), "video": None, "title": ""})
                continue
            img = s.select_one("img[data-src], img[data-image]")
            info = img_info(img)
            vw = s.select_one(".sqs-video-wrapper")
            vid = video_from(vw) if vw else None
            if not info and vw is not None:
                info = img_info(vw.select_one("img"))
            if not info:
                continue
            a = s.select_one("a")
            mt = s.select_one(".meta-title")
            title = (a.get("data-title") if a else "") or (mt.get_text(" ", strip=True) if mt else "")
            items.append({**info, "video": vid, "title": title.strip()})
        fit = "contain" if b.select_one(".content-fit") else "cover"
        return {"type": "gallery", "design": j.get("design", "grid"), "fit": fit,
                "perrow": j.get("thumbnails-per-row") or 3,
                "ar": j.get("aspect-ratio") or "square",
                "pad": j.get("padding", 20) if j.get("padding") is not None else 20,
                "sliderHeight": j.get("aspectRatio") or 50,
                "autoplay": bool(j.get("autoplay")),
                "duration": j.get("autoplay-duration") or 4,
                "thumbs": bool(j.get("thumbnails")),
                "controls": bool(j.get("controls")),
                "items": items}
    if defn == "website.components.summary":
        w = b.select_one(".summary-block-wrapper")
        items = []
        for it in w.select(".summary-item"):
            vw = it.select_one(".sqs-video-wrapper")
            img = it.select_one("img[data-src], img[data-image]")
            info = img_info(img)
            if not info:
                continue
            t = it.select_one(".summary-title")
            items.append({**info, "video": video_from(vw) if vw else None,
                          "title": t.get_text(" ", strip=True) if t else ""})
        ar = w.get("data-image-aspect-ratio", "Auto")
        return {"type": "summary", "design": w.get("data-design", "autogrid"),
                "perrow": int(w.get("data-slides-per-row") or 3),
                "ar": None if ar in ("Auto", "", None) else float(ar),
                "gutter": int(w.get("data-gutter") or 20),
                "colwidth": int(w.get("data-column-width") or 0) or None,
                "items": items}
    if defn == "website.components.scrolling":
        m = b.select_one(".Marquee")
        items = [x["text"].strip() for x in json.loads(m.get("data-marquee-items", "[]"))]
        return {"type": "marquee", "items": items,
                "speed": float(m.get("data-animation-speed") or 1),
                "direction": m.get("data-animation-direction") or "left"}
    if defn == "website.components.spacer":
        return {"type": "spacer", "ar": float(b.get("data-aspect-ratio") or 5)}
    if defn == "website.components.video":
        v = video_from(b.select_one(".sqs-video-wrapper"))
        return {"type": "video", **v} if v else None
    print("  ! unhandled block", cl[:3], defn, file=sys.stderr)
    return None


def walk(el):
    """Squarespace 7.0 layout: rows hold columns (span-N of 12), columns hold blocks or rows."""
    out = []
    for c in el.find_all(recursive=False):
        cl = c.get("class", [])
        if "row" in cl:
            cols = []
            for col in c.find_all(recursive=False):
                span = next((int(x[5:]) for x in col.get("class", []) if x.startswith("span-")), 12)
                cols.append({"span": span, "children": walk(col)})
            out.append({"type": "row", "cols": cols})
        elif "sqs-block" in cl:
            blk = parse_block(c)
            if blk:
                out.append(blk)
    return out


def simplify(nodes):
    """Collapse rows with a single full-width column into plain blocks."""
    flat = []
    for n in nodes:
        if n["type"] == "row":
            for col in n["cols"]:
                col["children"] = simplify(col["children"])
            n["cols"] = [c for c in n["cols"] if c["children"] or c["span"] < 12]
            if len(n["cols"]) == 1:
                flat.extend(n["cols"][0]["children"])
            elif any(c["children"] for c in n["cols"]):
                flat.append(n)
        else:
            flat.append(n)
    return flat


site = {"pages": {}}
for p in PAGES:
    soup = BeautifulSoup((RAW / f"{p}.html").read_text(encoding="utf-8"), "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else p
    layout = soup.select_one('.sqs-layout[data-type="page"]') or soup.select_one(
        "#content .sqs-layout, .main-content .sqs-layout")
    blocks = simplify(walk(layout)) if layout else []
    site["pages"][p] = {"title": title, "blocks": blocks}
    print(f"{p:22} {len(blocks):3} top-level blocks")

OUT.write_text(json.dumps(site, indent=1, ensure_ascii=False), encoding="utf-8")
