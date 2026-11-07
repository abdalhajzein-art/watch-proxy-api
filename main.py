from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re

app = FastAPI(title="Watch Proxy API", version="1.0")

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
    return {"status": "Online", "message": "Watch Proxy API is running!"}

@app.get("/api/resolve/tv")
async def resolve_tv(tmdbId: int, season: int, episode: int):
    # استخدام مصدر بديل يزود روابط ميديا أو استجابة JSON مباشرة للمسلسلات
    target_url = f"https://vidsrc.cc/v2/embed/tv/{tmdbId}/{season}/{episode}"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://vidsrc.cc/"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            response = await client.get(target_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to reach provider")
            
            html_content = response.text

            # البحث عن أي رابط ميديا مباشر أو ملف تشغيل
            m3u8_match = re.search(r'https?://[^\s<>"]+?\.(?:m3u8|mp4)[^\s<>"]*', html_content)
            if m3u8_match:
                return {
                    "status": "success",
                    "embed_url": m3u8_match.group(0)
                }

            # إذا لم يتم العثور على رابط مباشر، نعيد رابط الـ vidsrc.cc المباشر كحل بديل يدعم التشغيل
            return {
                "status": "success",
                "embed_url": target_url
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
