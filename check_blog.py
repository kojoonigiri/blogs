import time
goto_url('https://kojoonigiri.biz.id/blogs/')
time.sleep(15)
print("CURRENT URL:", window.location.href)
print("TITLE:", document.title)
app = document.getElementById('app')
print("APP_FOUND:", app is not None)
if app:
    art = app.innerHTML
    print("APP_LEN:", len(art))
    print("HAS_GRID:", 'grid' in art or 'grid-cols' in art)
    print("HAS_NOArtIFLES:", 'Belum Ada Artikel' in art)
    print("HAS_POST_TILE:", 'text-3xl' in art or 'artikel' in art.lower())
    print("---APP HTML (first 600)---")
    print(art[:600])
