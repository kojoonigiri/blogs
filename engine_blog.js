
    const REPO_OWNER = "kojoonigiri";
    const REPO_NAME = "blogs";
    const POSTS_PATH = "content/posts";
    const app = document.getElementById("app");

    // Pagination
    const POSTS_PER_PAGE = 9;
    let posts = [];
    let currentPage = 0;

    // Toggle Mobile Menu
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const mobileMenu = document.getElementById("mobile-menu");
    if (mobileMenuBtn) {
      mobileMenuBtn.addEventListener("click", () => {
        mobileMenu.classList.toggle("hidden");
      });
    }

    // Parse YAML Frontmatter dari file .md Pages CMS
    function parseFrontmatter(raw) {
      const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
      if (!match) return { meta: {}, body: raw };
      const meta = {};
      match[1].split(/\r?\n/).forEach(line => {
        const idx = line.indexOf(":");
        if (idx > -1) {
          const key = line.slice(0, idx).trim();
          let val = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "");
          meta[key] = val;
        }
      });
      return { meta, body: match[2] };
    }

    // Format Tanggal Indonesia
    function formatDateIndo(dateStr) {
      if (!dateStr) return "";
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" });
    }

    // Menyesuaikan path gambar dari Pages CMS (/images/blog/... -> /images/blog/...)
    function fixImagePath(imgPath) {
      if (!imgPath) return "https://placehold.co/800x500/dc2626/ffffff?text=Kojo+Onigiri+Blog";
      if (imgPath.startsWith("http")) return imgPath;
      const clean = imgPath.replace(/^\/+/, "").replace(/[?&].*$/, "");
      return `/${clean}`;
    }

    // Ambil seluruh artikel dari GitHub API
    async function fetchAllPosts() {
      const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${POSTS_PATH}`);
      if (!res.ok) throw new Error("Gagal mengambil daftar artikel dari GitHub.");
      const files = await res.json();
      const mdFiles = files.filter(f => f.name.endsWith(".md"));

      const posts = await Promise.all(mdFiles.map(async file => {
        const rawRes = await fetch(file.download_url);
        const rawText = await rawRes.text();
        const { meta, body } = parseFrontmatter(rawText);
        return {
          slug: file.name.replace(/\.md$/, ""),
          title: meta.title || file.name.replace(/^\d{4}-\d{2}-\d{2}-/, "").replace(/\.md$/, "").replace(/-/g, " "),
          date: meta.date || "",
          description: meta.description || body.replace(/[#>*_`]/g, "").slice(0, 140) + "...",
          coverImage: fixImagePath(meta.coverImage),
          draft: meta.draft === "true",
          body
        };
      }));

      return posts
        .filter(p => !p.draft)
        .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
    }

    // Render Halaman Grid Daftar Artikel atau Halaman Detail Artikel
    async function render() {
      const hash = window.location.hash;
      try {
        posts = await fetchAllPosts();

        // Inisialisasi pagination (hanya aktif untuk halaman utama blog)
        currentPage = parseInt(new URLSearchParams(window.location.search).get("page")) || 0;
        const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
        const paginatedPosts = posts.slice(currentPage * POSTS_PER_PAGE, (currentPage + 1) * POSTS_PER_PAGE);

        // TAMPILAN BACA DETAIL ARTIKEL
        if (hash.startsWith("#/post/")) {
          const slug = decodeURIComponent(hash.replace("#/post/", ""));
          const post = posts.find(p => p.slug === slug);

          if (!post) {
            app.innerHTML = `
              <div class="max-w-3xl mx-auto px-4 py-20 text-center">
                <div class="bg-white p-10 rounded-3xl shadow-sm border border-gray-100">
                  <i class="fa-solid fa-file-circle-question text-4xl text-kojo-red mb-4"></i>
                  <h2 class="text-2xl font-extrabold text-gray-900 mb-2">Artikel Tidak Ditemukan</h2>
                  <p class="text-gray-500 text-sm mb-6">Artikel yang Anda cari mungkin sudah dihapus atau belum diterbitkan.</p>
                  <a href="#/" class="inline-flex items-center gap-2 bg-kojo-red hover:bg-kojo-redhover text-white font-bold px-6 py-3 rounded-xl text-sm transition-all">
                    <i class="fa-solid fa-arrow-left"></i> Kembali ke Daftar Artikel
                  </a>
                </div>
              </div>
            `;
            return;
          }

          document.title = `${post.title} - Blog Kojo Onigiri`;
          app.innerHTML = `
            <section class="py-12 lg:py-16">
              <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <a href="#/" class="inline-flex items-center gap-2 text-sm font-bold text-kojo-red hover:text-kojo-redhover mb-6 bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-100 transition-all">
                  <i class="fa-solid fa-arrow-left"></i> Kembali ke Semua Artikel
                </a>

                <article class="bg-white rounded-3xl p-6 sm:p-10 lg:p-12 shadow-sm border border-gray-100">
                  <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-red-50 text-kojo-red text-xs font-extrabold uppercase tracking-wider mb-4">
                    <i class="fa-regular fa-calendar"></i> ${formatDateIndo(post.date)}
                  </div>

                  <h1 class="text-2xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-6">
                    ${post.title}
                  </h1>

                  <div class="w-full aspect-[16/9] rounded-2xl overflow-hidden bg-gray-100 mb-8 shadow-inner">
                    <img src="${post.coverImage}" alt="${post.title}" class="w-full h-full object-cover" onerror="this.onerror=null; this.src='https://placehold.co/800x450/dc2626/ffffff?text=Kojo+Onigiri';" />
                  </div>

                  <div class="prose max-w-none">
                    ${marked.parse(post.body)}
                  </div>

                  <!-- CTA Banner di Bawah Artikel -->
                  <div class="mt-12 pt-8 border-t border-gray-100">
                    <div class="bg-gradient-to-r from-kojo-red via-red-600 to-amber-600 rounded-2xl p-6 sm:p-8 text-white flex flex-col sm:flex-row items-center justify-between gap-6 shadow-lg">
                      <div class="text-center sm:text-left">
                        <span class="bg-white/20 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider">Lapar Setelah Baca?</span>
                        <h3 class="text-xl sm:text-2xl font-extrabold mt-2">Cobain Kojo Onigiri Sekarang!</h3>
                        <p class="text-red-100 text-xs sm:text-sm mt-1">Praktis, mengenyangkan, 100% Halal & dibuat fresh setiap hari.</p>
                      </div>
                      <a href="https://wa.me/6285165935577?text=Halo%20Kojo%20Onigiri,%20saya%20habis%20baca%20artikel%20di%20blog%20dan%20mau%20pesan%20menu" target="_blank" class="bg-white text-kojo-red hover:bg-amber-50 font-extrabold px-6 py-3.5 rounded-xl text-sm transition-all whitespace-nowrap shadow-md flex items-center gap-2">
                        <i class="fa-brands fa-whatsapp text-lg text-kojo-green"></i>
                        <span>Pesan via WA</span>
                      </a>
                    </div>
                  </div>
                </article>
              </div>
            </section>
          `;
          window.scrollTo({ top: 0, behavior: "smooth" });
          return;
        }

        // TAMPILAN HALAMAN UTAMA BLOG (GRID ARTIKEL)
        document.title = "Blog & Artikel Kuliner - Kojo Onigiri";
        app.innerHTML = `
          <!-- Blog Hero Header -->
          <section class="bg-gradient-to-b from-red-50/80 via-white to-transparent pt-12 pb-8 border-b border-gray-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center max-w-3xl">
              <span class="text-kojo-red font-extrabold text-xs uppercase tracking-widest bg-red-50 px-3.5 py-1.5 rounded-full border border-red-100">
                Jurnal Kuliner & Gaya Hidup
              </span>
              <h1 class="text-3xl sm:text-5xl font-extrabold text-gray-900 tracking-tight mt-4 mb-4">
                Blog <span class="text-transparent bg-clip-text bg-gradient-to-r from-kojo-red via-red-600 to-amber-500">Kojo Onigiri</span>
              </h1>
              <p class="text-base sm:text-lg text-gray-600 leading-relaxed">
                Temukan inspirasi kuliner, rekomendasi jajanan favorit, tips bekal praktis, dan cerita seru seputar dunia makanan.
              </p>
            </div>
          </section>

          <!-- Grid Daftar Artikel -->
          <section class="py-12 lg:py-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              ${paginatedPosts.length === 0 ? `
                <div class="text-center py-16 bg-white rounded-3xl border border-gray-100 shadow-sm max-w-lg mx-auto p-8">
                  <i class="fa-regular fa-newspaper text-4xl text-gray-300 mb-3"></i>
                  <h3 class="text-lg font-bold text-gray-900">Belum Ada Artikel</h3>
                  <p class="text-sm text-gray-500 mt-1">Artikel baru akan segera hadir di sini.</p>
                </div>
              ` : `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  ${paginatedPosts.map(p => `
                    <article onclick="location.hash='#/post/${encodeURIComponent(p.slug)}'" class="cursor-pointer bg-white rounded-2xl border border-gray-100 overflow-hidden flex flex-col shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1.5 group">
                      <div class="relative w-full aspect-[16/10] bg-gray-100 overflow-hidden">
                        <img
                          src="${p.coverImage}"
                          alt="${p.title}"
                          class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          onerror="this.onerror=null; this.src='https://placehold.co/600x375/dc2626/ffffff?text=Kojo+Onigiri';"
                        />
                        <span class="absolute top-3 left-3 bg-white/95 backdrop-blur-sm text-gray-800 font-bold text-[11px] px-3 py-1 rounded-full shadow-sm flex items-center gap-1.5">
                          <i class="fa-regular fa-calendar text-kojo-red"></i> ${formatDateIndo(p.date)}
                        </span>
                      </div>

                      <div class="p-6 flex flex-col flex-grow">
                        <h2 class="text-lg sm:text-xl font-bold text-gray-900 mb-2.5 group-hover:text-kojo-red transition-colors line-clamp-2">
                          ${p.title}
                        </h2>
                        <p class="text-gray-600 text-xs sm:text-sm leading-relaxed mb-6 flex-grow line-clamp-3">
                          ${p.description}
                        </p>

                        <div class="pt-4 border-t border-gray-100 flex items-center justify-between text-xs font-bold text-kojo-red">
                          <span>Baca Selengkapnya</span>
                          <i class="fa-solid fa-arrow-right group-hover:translate-x-1 transition-transform"></i>
                        </div>
                      </div>
                    </article>
                  `).join("")
                </div>

                <!-- Pagination: 9 artikel per halaman -->
                <div class="flex justify-center items-center gap-2 mt-10">
                  <button onclick="changePage(-1)" class="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-sm font-bold text-gray-700 hover:bg-gray-50 hover:border-kojo-red transition-all disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                    <i class="fa-solid fa-chevron-left"></i> Prev
                  </button>
                  ${Array.from({ length: totalPages }, (_, i) => `
                    <button onclick="changePage(0)" class="w-9 h-9 rounded-xl text-sm font-bold transition-all ${i === currentPage ? 'bg-kojo-red text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'}">${i + 1}</button>
                  `).join("")}
                  <button onclick="changePage(1)" class="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-sm font-bold text-gray-700 hover:bg-gray-50 hover:border-kojo-red transition-all disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                    Next <i class="fa-solid fa-chevron-right"></i>
                  </button>
                </div>

              </div>
            </div>
          </section>
        `;
      } catch (err) {
        app.innerHTML = `
          <div class="max-w-xl mx-auto px-4 py-20 text-center">
            <div class="bg-white p-8 rounded-3xl border border-red-100 shadow-sm">
              <i class="fa-solid fa-triangle-exclamation text-3xl text-kojo-red mb-3"></i>
              <h3 class="text-lg font-bold text-gray-900">Gagal Memuat Artikel</h3>
              <p class="text-xs text-gray-500 mt-1">${err.message}</p>
            </div>
          </div>
        `;
      }
    }

    function changePage(dir) {
      const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
      currentPage = Math.max(0, Math.min(currentPage + dir, totalPages - 1));
      history.replaceState(null, '', '?page=' + currentPage);
      render();
    }

    window.addEventListener("hashchange", render);
    render();
  