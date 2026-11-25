"""fetch_image.py — download recommended (commercial-free) images.

Source: Wikimedia Commons (free-licensed media: CC0 / CC BY / CC BY-SA / PD).
No API key required.
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

COMMOM_LICENSES = {"cc0", "public domain", "cc by", "cc by-sa", "cc by 4.0", "pd", "public domain dedication"}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".jfif", ".svg", ".tif", ".tiff"}

USER_AGENT = "Mozilla/5.0 (compatible; blog-auto/1.0)"


def _is_image_url(url):
    """True if the URL points to an image file."""
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    # ignore query/fragment noise
    if ext in IMAGE_EXTENSIONS:
        return True
    # some generators put the extension in the query; fall back to filename hints
    return False


def _open_with_retry(req, timeout):
    """Buka URL dengan backoff untuk 429/5xx sementara dari Wikimedia."""
    delay = 5
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("retry exhausted")


def _search_wikimedia(query, limit=10):
    params = {
        "action": "query", "format": "json",
        "generator": "search", "gsrsearch": query,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size",
    }
    req = urllib.request.Request(
        "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params),
        headers={"User-Agent": USER_AGENT},
    )
    with _open_with_retry(req, 25) as r:
        return json.load(r)


def search(query):
    """Return list of dicts {"title","url","license","width","height"} filtered to free-licensed images."""
    raw = _search_wikimedia(query)
    out = []
    for page in raw.get("query", {}).get("pages", {}).values():
        ii = page.get("imageinfo")
        if not ii:
            continue
        info = ii[0]
        ext = info.get("extmetadata", {})
        lic = str(ext.get("LicenseShortName", {}).get("value", "")).lower()
        if lic not in COMMOM_LICENSES:
            continue
        url = info.get("thumburl") or info.get("url")
        if not _is_image_url(url):
            continue
        out.append({
            "title": page.get("title", ""),
            "url": url,
            "license": lic,
            "width": info.get("width"),
            "height": info.get("height"),
        })
    return out


def download(url, dest):
    """Download image (with http/https redirect) to dest. Returns True on success."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with _open_with_retry(req, 40) as r, open(dest, "wb") as f:
        f.write(r.read())
    return os.path.exists(dest)
