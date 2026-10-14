# Editor Website: how this site was made

A static copy of www.georgegarnish.co.uk, rebuilt from the Squarespace site on 14 Oct 2026.
Hosted on GitHub Pages. No build step is needed to publish: the HTML in the folder above *is* the site.

- `site.json`: every page's content (photos, videos, text, scrolling banners) as extracted from Squarespace.
- `image-map.json`: Squarespace image URL → local file in `../images/`.
- `extract.py`, `download.py`, `build.py`: the scripts that made it. To change the menu or a page,
  edit `site.json` (or `NAV` in `build.py`) and re-run:

      python build.py site.json image-map.json ..

  (needs `pip install beautifulsoup4` only for `extract.py`.)

Look and behaviour live in `../assets/style.css` and `../assets/site.js`.
Fonts: Montserrat (free, Google Fonts) stands in for Squarespace's Proxima Nova, which is a paid Adobe font.
