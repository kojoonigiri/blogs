#!/usr/bin/env python3
"""
update-sitemap.py

Fungsionalitas:
  1. Membaca seluruh artikel di content/posts/*.md (Pages CMS)
  2. Mengekstrak title + date dari frontmatter
  3. Menghasilkan sitemap.xml (root repo: kojoonigiri/blogs)
     -> https://kojoonigiri.biz.id/blogs/sitemap.xml

 Cara pakai:
   Seteleh publish artikel baru (juga update index.html blog), jalankan:
     python3 update-sitemap.py
   Script akan menulis sitemap.xml, lalu opsi --push akan
   add/commit/push ke GitHub.

 Opsi:
   --push   commit & push ke origin/main
   --dry-run| -n   cuma cetak isi sitemap.xml tanpa tulis file
"""

import glob
import os
import re
import sys
import subprocess
from datetime import datetime

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BLOG_DIR, "content", "posts")
SITEMAP_PATH = os.path.join(BLOG_DIR, "sitemap.xml")

BASE = "https://kojoonigiri.biz.id"
BLOG_URL = BASE + "/blogs/"


def parse_frontmatter(md_path):
    """Return (title, date) atau None kalau tidak ada frontmatter."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    m_title = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    m_date = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", content, re.MULTILINE)
    if not m_title or not m_date:
        return None
    title = m_title.group(1).strip()
    # hilangkan tanda kutip jika ada di sekitar judul
    if len(title) >= 2 and title[0] == title[-1] and title[0] in ('"', "'"):
        title = title[1:-1]
    return title, m_date.group(1)


def build_sitemap_xml(entries):
    """entries = list of (title, date, slug)"""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    # Home
    lines.append("  <url>")
    lines.append(f"    <loc>{BLOG_URL}</loc>")
    lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
    lines.append("    <changefreq>daily</changefreq>")
    lines.append("    <priority>1.0</priority>")
    lines.append("  </url>")
    # Blog index
    lines.append("  <url>")
    lines.append(f"    <loc>{BLOG_URL}</loc>")
    lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
    lines.append("    <changefreq>weekly</changefreq>")
    lines.append("    <priority>0.9</priority>")
    lines.append("  </url>")
    # Posts sorted by date desc
    for title, date, slug in sorted(entries, key=lambda x: x[2], reverse=True):
        lines.append("  <url>")
        lines.append(f"    <loc>{BLOG_URL}{slug}</loc>")
        lines.append(f"    <lastmod>{date}</lastmod>")
        lines.append("    <changefreq>weekly</changefreq>")
        lines.append("    <priority>0.8</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def collect_posts():
    posts = []
    for md_path in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        parsed = parse_frontmatter(md_path)
        if not parsed:
            continue
        title, date = parsed
        slug = os.path.basename(md_path).replace(".md", "")
        posts.append((title, date, slug))
    return posts


def generate_sitemap(entries, dry_run=False):
    xml = build_sitemap_xml(entries)
    if dry_run:
        print(xml)
        return
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[OK] sitemap.xml ditulis ({len(entries)} artikel)")


def commit_and_push():
    subprocess.run(["git", "add", "sitemap.xml"], check=True)
    subprocess.run(["git", "commit", "-m",
                    "ci: update sitemap.xml daftar artikel blog"],
                   check=True)
    r = subprocess.run(["git", "push", "origin", "main"], check=False)
    if r.returncode == 0:
        print("[OK] sitemap.xml terkirim ke origin/main")
    else:
        print("[WARN] push gagal (remote mungkin ada perubahan baru)")


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    do_push = "--push" in sys.argv
    entries = collect_posts()
    if not entries:
        print("[GAGAL] tidak ada artikel di content/posts/")
        sys.exit(1)
    if dry_run:
        print(build_sitemap_xml(entries))
        print(f"[DRY-RUN] {len(entries)} artikel, file TIDAK ditulis.")
        return
    generate_sitemap(entries)
    if do_push:
        commit_and_push()
    else:
        print(f"[INFO] Jalankan --push nanti kalau mau kirim ke GitHub.")

if __name__ == "__main__":
    main()
