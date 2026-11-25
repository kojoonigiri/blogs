"""generate_posts.py — auto-generate blog articles into content/posts/ + featured images.

Flow (per run):
  1. pick N random topics (N = random 3-6) from the 6 categories
  2. for each topic:
     - search a free-licensed image (Wikimedia Commons)
     - download it to public/images/blog/<date>-<slug>.jpg
     - write content/posts/<date>-<slug>.md
  3. commit + push to GitHub main
  4. refresh sitemap.xml

No API keys needed (image source = Wikimedia Commons, free for commercial use).
"""
import datetime
import json
import os
import random
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_fetch import search, download  # noqa: E402

REPO = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(REPO)
CONTENT_DIR = os.path.join(REPO_ROOT, "content", "posts")
IMAGE_DIR = os.path.join(REPO_ROOT, "public", "images", "blog")
SITEMAP_SCRIPT = os.path.join(REPO_ROOT, "update-sitemap.py")
USED_IMAGES_FILE = os.path.join(REPO, ".used_images.json")
BASE_URL = "https://kojoonigiri.biz.id/blogs"

# ---------------------------------------------------------------------------
# Topics (one per category). 'keywords' is used for the image search,
# 'body' is the article body (markdown), 'tags' for front-matter.
# ---------------------------------------------------------------------------
TOPICS = [
    {
        "id": "jajanan-indonesia",
        "title": "Jajanan Indonesia",
        "keywords": "jajanan indonesia, kue tradisional indonesia, camilan khas indonesia",
        "tags": ["jajanan indonesia", "kuliner", "kulinari", "kue", "indonesia"],
        "body": """## Apa Itu Jajanan Indonesia?

Jajanan Indonesia merupakan kumpulan camilan, kue, dan makanan ringan yang beragam, lahir dari kekayaan bumi dan budaya masyarakat Nusantara. Mulai dari yang dibuat dari beras, ketan, pisang, singkong, tepung terigu, hingga campuran rempah, jajanan Indonesia mencerminkan keseimbangan rasa manis, gurih, pedas, dan renyah dalam satu piringan.

## Macam-Macam Jajanan Khas Indonesia

Berikut ini beberapa jajanan yang sering ditemukan di pasar, kaki lima, maupun kafe kecil di seluruh Indonesia:

### 1. Kue Basah & Kue Kering

- **Klepon** — kue bola kecil berisi cenir atau lumpur tepung beras dengan gula aren, digoreng atau dimasukkan ke dalam air kuah.
- **Dodol** — kue ketan atau beras yang diseduh dengan gula aren, memiliki tekstur pekat, manis, dan kental.
- **Lupis** — kue tradisional Kalimantan yang terbuat dari tepung beras, disajikan dengan sirup gula merah.
- **Kue cilor** — kue dari Kudus yang berbentuk cilik, dipanggang dan diisi cokelat atau keju.

### 2. Camilan Berbasis Singkong

- **Cireng** — camilan singkong yang disentuk dan digoreng, disajikan dengan saus satay atau kecap.
- **Getuk** — biskuit singkong yang diparut dan digoreng hingga golden, biasa disajikan dengan kelapa parut.
- **Pisang goreng** — pisang yang digoreng dengan tepung dan gula batu, memberikan rasa yang harum dan renyah.

### 3. Camilan Berbasis Tahu & Kedelai

- **Tahu isi** — tahu yang diisi daging, sayuran, atau kuah pedas, diiris dan digoreng.
- **Tauco** — tanaman yang dimasak dengan bumbu, sering menjadi pelengkap jajanan.

## Tips Memilih Jajanan Indonesia yang Segar

- Perhatikan tekstur dan aroma: yang baru digoreng atau dipanggang biasanya lebih harum.
- Hindari camilan yang menggunakan bahan basah yang terlalu lama dibiarkan.
- Bawa uang kembalian karena sebagian jajanan dijual per porsi.

## Penutup

Jajanan Indonesia adalah kenangan rasa yang sederhana namun memikat. Mulai dari klepon yang manis, dodol yang pekat, hingga getuk yang renyah, setiap jenis memiliki cerita serta kemanisan yang membuat Rasanya tahan lama diingat.""",
    },
    {
        "id": "wisata-indonesia",
        "title": "Wisata Indonesia",
        "keywords": "wisata indonesia, destinasi wisata indonesia, liburan Indonesia",
        "tags": ["wisata indonesia", "destinasi", "liburan", "wisata", "indonesia"],
        "body": """## Apa Itu Wisata Indonesia?

Indonesia adalah negara kepulauan yang terletak di antara dua benua dan dua samudra, memiliki keberagaman alam yang luar biasa. Dari pantai pasir putih, gunung berapi yang berapi aktif, hutan hujan tropis, hingga situs sejarah kuno, Indonesia menawarkan pengalaman wisata yang beragam untuk dikunjungi.

## Destinasi Wisata di Berbagai Daerah

### Pulau Jawa

- **Borobudur** — candi Buddha terbesar di dunia di Magelang, Jawa Tengah.
- **Prambanan** — kompleks candi Hindu kuno di Yogyakarta.
- **Ubud** — pusat seni dan budaya di Bali, terkenal dengan padang sawahnya.

### Nusa Tenggara

- **Komodo** — desa yang terkenal dengan komodo di NTT.
- **Padangbai** — pantai dengan air jernih di Bali.

### Sulawesi & Maluku

- **Raja Ampat** — perairan dengan keanekaragaman hayati terkaya di dunia.
- **Tanjung Pandan** — kota di Kepulauan Bangka Belitung.

## Tips Menyusun Rute Wisata di Indonesia

- Sesuaikan rute dengan kondisi cuaca dan musim.
- Libatkan pejalan lokal untuk mendukung ekonomi komunitas.
- Perhatikan aturan adat dan budaya lokal.

## Penutup

Wisata Indonesia adalah subjek yang hidup, penuh keindahan alam, budaya, dan keramahan. Baik Anda mencari petualangan, budaya, maupun keheningan, Indonesia punya hal yang bisa ditemukan di setiap pelosoknya.""",
    },
    {
        "id": "jajanan-lokal",
        "title": "Jajanan Local di Berbagai Daerah Indonesia",
        "keywords": "jajanan lokal, kuliner daerah, jajanan khas daerah, kuliner lokal Indonesia",
        "tags": ["jajanan lokal", "kuliner daerah", "kuliner lokal", "jajanan", "indonesia"],
        "body": """## Pengertian Jajanan Lokal

Jajanan lokal adalah camilan dan makanan ringan yang berkembang di suatu daerah tertentu, dengan ciri khas bahan dan cara penyajian yang khas. Setiap wilayah di Indonesia memiliki jajanan setempat yang mencerminkan budaya, bahan lokal, dan tradisi masyarakatnya.

## Jajanan Lokal dari Berbagai Wilayah

### Jawa Barat

- **Klepon** — kue bolong berisi cenir, digoreng.
- **Peteh** — kue terigu yang digoreng.
- **Geplak** — asinan buah khas Sunda.

### Jawa Tengah

- **Gudeg** — masakan asal Yogyakarta, terbuat dari nangka muda yang dimasak lambat.
- **KLT** — kerupuk tempe, lotek, dan tahu.

### Bali

- **Lawar** — campuran daging dan sayuran yang dipotong kecil.
- **Babi panggang** — hidangan wajib di Bali (dalam adat tertentu).

### Kalimantan

- **Lupis** — kue beras dari Kalimantan Barat.
- **Ketayap** — kue yang terbuat dari beras, dibungkus daun pisang.

### Sulawesi

- **Coto Makassar** — sup berbahan bumbu kaya.
- **Pakkek** — jajanan tradisional Sulawesi Selatan.

## Tips Menikmati Jajanan Lokal

- Cobalah setiap daerah dengan bervariasi.
- Riset terlebih dahulu lokasi jajanan yang tersedia.
- Simpan catatan rasa dan foto untuk dijadikan bahan diskusi.

## Penutup

Jajanan lokal adalah cerminan sejarah dan budaya masyarakat setempat. Dengan mencicipi, kita tidak hanya menikmati rasa, tetapi juga menjembatani budaya.""",
    },
    {
        "id": "jajanan-bandung",
        "title": "Jajanan Khas Bandung",
        "keywords": "jajanan bandung, jajanan khas bandung, kuliner bandung, camilan bandung",
        "tags": ["jajanan bandung", "kuliner bandung", "jajanan", "bandung"],
        "body": """## Apa Itu Jajanan Khas Bandung?

Jajanan khas Bandung adalah kumpulan camilan tradisional yang berkembang dari kuliner Sunda. Ciri khasnya adalah rasa manis, gurih, pedas, dan renyah yang bervariasi, mudah ditemukan di pasar tradisional, kaki lima, maupun kafe-kafe kecil.

## Jenis-Jenis Jajanan Khas Bandung

### 1. Kue Tradisional

- **Peteh krumif** — kue terigu yang digoreng, varian madu, keju, atau cokelat.
- **Kembang goyang** — kue kering berbentuk bunga dari tepung terigu dan telur.
- **Geplak** — asinan buah khas Sunda yang kenyal, manis, dan sedikit renyah.
- **Klepon** — kue bola kecil berisi cenir atau lumpur tepung beras dengan gula aren.
- **Dodol Bandung** — dodol ketan dan gula aren dengan tekstur pekat, manis, dan kental.
- **Cireng** — camilan singkong yang disentuk dan digoreng, disajikan dengan saus rujuk atau tauco.
- **Surabi Bandung** — surabi yang dibakar dari tepung beras tanpa telur.

### 2. Camilan Berbasis Bahan Lokal

- **Pisang kriuk** — roti pisang yang digoreng, renyah di luar, lembut di dalam.
- **Pisang goreng** — pisang yang digoreng dengan tepung dan gula batu.
- **Getuk Bandung** — biskuit singkong yang diparut dan digoreng, disajikan dengan kelapa parut.

## Cara Menemukan Jajanan Bandung yang Autentik

- Jelajahi pasar tradisional atau kaki lima sekitar tempat Anda.
- Perhatikan warna dan bau; hindari pewarnaan kuning atau merah yang mencolok.
- Perlihatkan tekstur: yang baru digoreng atau dibakar lebih renyah dan harum.
- Pilih harga yang wajar; hal yang terlalu murah bisa jadi tanda kualitas rendah.
- Bawa uang kembalian karena sebagian jualan per porsi.

## Penutup

Jajanan Bandung menawarkan harum manis, kenyal, dan gurih yang sulit ditemukan di tempat lain. Mulailah menjelajahi pasar lokal untuk merasakan kesan asli jajanan khas Bandung.""",
    },
    {
        "id": "tempat-wisata-bandung",
        "title": "Tempat Wisata di Bandung dan Sekitarnya",
        "keywords": "tempat wisata bandung, wisata bandung, destinasi wisata bandung, liburan bandung",
        "tags": ["tempat wisata bandung", "wisata bandung", "destinasi", "bandung"],
        "body": """## Apa Itu Tempat Wisata di Bandung?

Bandung dan sekitarnya menawarkan beragam destinasi wisata, mulai dari perkotaan, pegunungan, sawah terasering, kaki gunung, hingga kawasan sejarah dan kuliner. Lokasi ini cocok untuk liburan harian atau weekend dengan keluarga.

## Tempat Wisata yang Cocok Dikunjungi

### 1. Di Kota Bandung

- **Kota Manga** — kawasan kuliner dan kafe yang terkenal dengan keliling mobil.
- **Dago** — kawasan perkotaan dengan kafe, restoran, dan akses dekat pusat kota.
- **Alun-Alun Bandung** — persimpangan wajib dikunjungi saat fajar atau senja.

### 2. Pegunungan & Alam

- **Lembang** — kota dengan udara sejuk, perkebunan teh, dan sunset.
- **Cimindi** — kawasan perkebunan dan pertanian.
- **Situ Ciburuy** — danau buatan yang indah serta kawasan wisata sekitar.
- **Papandayan** — kawah gunung berapi di Garut yang masih aktif.

### 3. Kuliner & Pekan

- **Kota Pasar** — pasar tradisional dengan jajanan khas Bandung.
- **Pekan Baru Bandung** — panggung seni dan tradisi yang langsung dapat dilihat.
- **Kota Kembang** — kawasan kuliner dan kafe.

## Tips Mengunjungi Tempat Wisata Bandung

- Periksa kondisi cuaca dan waktu hujan sebelum pergi.
- Libatkan warga lokal untuk mendukung ekonomi komunitas.
- Pelajari aturan yang berlaku di daerah yang dikunjungi.

## Penutup

Tempat wisata di Bandung menawarkan keindahan alam, budaya, dan kuliner sekaligus kesosialan. Dari pagi sampai senja, setiap hari berbeda menu dan suasana yang bisa dinikmati.""",
    },
    {
        "id": "tempat-wisata-jawa-barat",
        "title": "Tempat Wisata di Jawa Barat",
        "keywords": "tempat wisata jawa barat, wisata jawa barat, destinasi jawa barat, liburan jawa barat",
        "tags": ["wisata jawa barat", "destinasi", "jawa barat", "wisata", "liburan"],
        "body": """## Apa Itu Wisata Jawa Barat?

Jawa Barat adalah provinsi di ujung barat Pulau Jawa yang memiliki keberagaman alam, dari pantai, pegunungan, pertanian, hingga kekayaan budaya. Dibatasi dengan Ujung Kulon dan Gunung Krakatoa, Jawa Barat menawarkan pengalaman wisata yang asri.

## Destinasi Wisata di Jawa Barat

### 1. Pantai

- **Pantai Pangandaran** — pantai terpencil dengan air jernih.
- **Pantai Circemplung** — pantai dengan panorama indah di Cirebon.
- **Pantai Srono** — pantai selatan yang sejuk.

### 2. Pegunungan & Gunung

- **Gunung Papandayan** — gunung api aktif di Garut.
- **Kawah Ratu Boko** — kawah berapi di Priangan.
- **Gunung Ciremai** — puncak tertinggi di Jawa Barat.

### 3. Kawasan Perbukitan & Sawah

- **Kawah Ratu Boko** — kawah yang penuh warna dan keindahan.
- **Sawah Ciater** — sawah terasering yang asri.
- **Kawasan Selabintana** — perkebunan teh di Garut.

### 4. Budaya & Khasnya

- **Tari Jaipong** — tari tradisional Sunda yang hidup.
- **Pekan Baru Cinere** — panggung seni dan tradisi.

## Tips Menikmati Wisata Jawa Barat

- Pecah perjalanan ke kota-kota besar seperti Bandung, Garut, Cianjur, Sukabumi, dan Cirebon.
- Libatkan warga lokal untuk mendukung ekonomi komunitas.
- Silakan kenali dan patuhi aturan adat setempat.

## Penutup

Jawa Barat adalah provinsi dengan keindahan beragam, baik alam, budaya, maupun kuliner. Setiap daerah memiliki nuansa sendiri; mulai dari pantai yang tenang sampai gunung yang menantang, semuanya bisa diakses dengan memadai.""",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now():
    return datetime.date.today().isoformat()


def make_slug(topic, date):
    base = topic["id"].replace("-", " ")
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return f"{date}-{base}"


def get_used_images():
    if os.path.exists(USED_IMAGES_FILE):
        try:
            with open(USED_IMAGES_FILE, encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_used_images(used):
    with open(USED_IMAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(used), f, ensure_ascii=False, indent=2)


def is_image_used(url):
    return url in get_used_images()


def mark_image_used(url):
    used = get_used_images()
    used.add(url)
    save_used_images(used)


# ---------------------------------------------------------------------------
# Main worker
# ---------------------------------------------------------------------------
def _clean_filename(path, default_ext=".jpg"):
    """Extract a safe filename from a URL path (strip query/fragment, keep the extension)."""
    name = os.path.basename(path)
    if not name:
        name = "image" + default_ext
    name = re.sub(r"[^\w\-.]+", "_", name)
    if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".jfif")):
        name += default_ext
    return name


def fetch_image_for_topic(topic, slug):
    """Return (filename, metadata) or (None, None)."""
    candidates = topic["keywords"].split(",")
    for kw in candidates:
        kw = kw.strip()
        results = search(kw)
        if not results:
            continue
        chosen = random.choice(results)
        url = chosen["url"]
        if is_image_used(url):
            continue
        parsed = urllib.parse.urlparse(url)
        name = _clean_filename(parsed.path)
        dest = os.path.join(IMAGE_DIR, name)
        if download(url, dest):
            mark_image_used(url)
            return name, chosen
    return None, None


def write_post(topic, slug, cover, date):
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(os.path.join(IMAGE_DIR, slug), exist_ok=True)
    title = topic["title"]
    desc = (f"Penyajian jajanan tradisional khas {slug} yang mudah ditemukan di "
            f"pasar, kaki lima, maupun kafe kecil. Ciri khas jajanan ini bervariasi, "
            f"mulai dari yang digoreng, dipanggang, hingga diseduh.")
    tags = topic["tags"]
    tags_list = [t.strip() for t in tags.split(",")] if isinstance(tags, str) else list(tags)
    tags_md = "\n  - " + "\n  - ".join(tags_list)
    md = (
        "---\n"
        f'title: "{title}"\n'
        f"date: {date}\n"
        f"description: {desc}\n"
        f"coverImage: /images/blog/{cover}\n"
        "tags:\n"
        f"{tags_md}\n"
        "draft: false\n"
        "---"
    )
    return md


def git(args):
    subprocess.run(["git"] + args, cwd=REPO, check=True, capture_output=True, text=True)


def commit_and_push(msg):
    git(["add", "-A"])
    git(["commit", "-m", msg])
    git(["push", "origin", "main"])


def update_sitemap():
    subprocess.run([sys.executable, SITEMAP_SCRIPT, "--push"], cwd=REPO,
                   check=True, capture_output=True, text=True)


def run_article(topic, verbose=True):
    slug = make_slug(topic, now())
    cover, meta = fetch_image_for_topic(topic, slug)
    if cover is None:
        print(f"  [GAGAL] tidak dapat gambar unik untuk: {topic['title']}")
        return False
    date = now()
    md = write_post(topic, slug, cover, date)
    md_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    if verbose:
        print(f"  [OK] post: {slug}.md | gambar: {cover} ({meta['license']})")
    return True


def generate_posts(n_topics=None):
    used = get_used_images()
    print(f"  [INFO] gambar yang sudah dipakai: {len(used)}")
    n = n_topics or random.randint(3, 6)
    selected = random.sample(TOPICS, min(n, len(TOPICS)))
    ok = 0
    for t in selected:
        if run_article(t, verbose=False):
            ok += 1
    return ok


def main():
    force = "--force" in sys.argv
    n = None
    if "--count" in sys.argv:
        i = sys.argv.index("--count")
        n = int(sys.argv[i + 1])
    if not force and get_used_images():
        print(f"[INFO] ditemukan {len(get_used_images())} gambar yang sudah dipakai. "
              f"Jalankan --force untuk menambahkan lebih banyak.")
    n = n or random.randint(3, 6)
    print(f"[INFO] memilih {n} topik secara acak dari {len(TOPICS)} kategori")
    selected = random.sample(TOPICS, min(n, len(TOPICS)))
    ok = 0
    for t in selected:
        if run_article(t):
            ok += 1
    if ok == 0:
        print("[INFO] tidak ada yang dihasilkan.")
        return
    date = now()
    commit_and_push(f"chore: publish {ok} artikel ({date})")
    update_sitemap()
    print(f"\n[OK] selesai: {ok} artikel dipublish ke main.")


if __name__ == "__main__":
    main()
