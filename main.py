from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Watch Proxy API", version="1.0")

# السماح بالاتصال من أي تطبيق (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

@app.get("/")
def home():
    return {"status": "API is running successfully", "author": "Abdul Ghani"}

@app.get("/api/resolve/tv")
async def resolve_tv(tmdbId: int, season: int, episode: int):
    """
    سيرفر وسيط لجلب روابط المسلسلات وتجاوز الحماية
    """
    target_url = f"https://vidsrc.sh/embed/tv/{tmdbId}/{season}/{episode}"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://vidsrc.sh/"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            response = await client.get(target_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch from upstream provider")
            
            # هنا يمكنك إضافة منطق استخراج رابط الفيديو الصافي أو إرجاع الصفحة/البيانات المعالجة
            return {
                "status": "success",
                "tmdbId": tmdbId,
                "season": season,
                "episode": episode,
                "embed_url": target_url,
                "html_content": response.text[:500] # عينة من الاستجابة للتأكد
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
