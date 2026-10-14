"""Download every image the site model uses into <site>/images and record the local names.

Usage: python download.py <site.json> <site_dir>
"""
import json
import re
import sys
import urllib.parse as U
import urllib.request as R
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODEL = Path(sys.argv[1])
SITE = Path(sys.argv[2])
IMG = SITE / "images"
IMG.mkdir(parents=True, exist_ok=True)

EXT = {"image/webp": ".webp", "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif"}

model = json.loads(MODEL.read_text(encoding="utf-8"))
srcs = set()


def collect(blocks):
    for b in blocks:
        if b["type"] == "row":
            for c in b["cols"]:
                collect(c["children"])
            continue
        if b.get("src"):
            srcs.add(b["src"])
        for i in b.get("items", []):
            if isinstance(i, dict):
                srcs.add(i["src"])


for p in model["pages"].values():
    collect(p["blocks"])


def local_name(src):
    parts = src.rstrip("/").split("/")
    key = parts[-2][:24]  # Squarespace's per-upload id, keeps names unique
    stem = U.unquote_plus(parts[-1]).rsplit(".", 1)[0]
    stem = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower()[:50] or "image"
    return f"{stem}-{key[-8:].lower()}"


def fetch(src):
    gif = src.lower().endswith(".gif")
    url = src + ("?format=1000w" if gif else "?format=1500w")
    name = local_name(src)
    existing = list(IMG.glob(name + ".*"))
    if existing:
        return src, existing[0].name, 0
    req = R.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with R.urlopen(req, timeout=60) as r:
        data = r.read()
        ext = EXT.get(r.headers.get_content_type(), Path(src).suffix.lower())
    (IMG / (name + ext)).write_bytes(data)
    return src, name + ext, len(data)


mapping, total, failed = {}, 0, []
with ThreadPoolExecutor(8) as ex:
    for fut in [ex.submit(fetch, s) for s in sorted(srcs)]:
        try:
            src, fn, n = fut.result()
            mapping[src] = fn
            total += n
        except Exception as e:  # keep going, report at the end
            failed.append(str(e))

MODEL.with_name("image-map.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")
print(f"{len(mapping)} images ok, {len(failed)} failed, {total/1e6:.1f} MB downloaded this run")
for f in failed[:10]:
    print("  FAILED:", f)
