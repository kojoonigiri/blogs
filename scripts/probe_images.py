import json, urllib.request, urllib.parse, time, re, urllib.request as ur

# --- WIKIMEDIA broad ---
def wikimedia_all(query, limit=15):
    params = {"action":"query","format":"json","generator":"search","gsrsearch":query,"gsrnamespace":6,"gsrlimit":limit,"prop":"imageinfo","iiprop":"url|extmetadata|size"}
    req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params),headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.load(r)

print("=== WIKIMEDIA broad (all licences shown) ===")
for q in ["jajanan bandung", "wisata jawa barat", "kopi jawa"]:
    d = wikimedia_all(q, 8)
    print(f"[{q}] total={len(d.get('query',{}).get('pages',{}))}")
    for p in d.get("query",{}).get("pages",{}).values():
        ext=p.get("imageinfo",[{}])[0].get("extmetadata",{})
        lic=str(ext.get("LicenseShortName",{}).get("value","")).lower()
        print(f"   [{lic[:22]}] {p.get('title','')[:50]}")
    time.sleep(1)

# --- BING html ---
print("\n=== BING html ===")
try:
    r=ur.request.urlopen(ur.Request("https://www.bing.com/images/search?q=jajanan%20bandung&form=HDRSC2",headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}),timeout=20)
    html=r.read().decode("utf-8","ignore")
    urls=re.findall(r'https?://[^"\'\\s]+\.(?:jpg|jpeg|png|webp)',html)
    print(f"found {len(urls)} urls; sample:")
    for u in urls[:6]: print("  ",u[:90])
except Exception as e:
    print("BING ERR",e)
