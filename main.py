from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

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
    return {"status": "Online", "message": "Watch Proxy API is running successfully!"}

@app.get("/api/resolve/tv")
async def resolve_tv(tmdbId: int, season: int, episode: int):
    target_url = f"https://vidsrc.sh/embed/tv/{tmdbId}/{season}/{episode}"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://vidsrc.sh/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            response = await client.get(target_url, headers=headers)
            
            # إذا طابقت استجابة سيرفر البث صفحة الحماية، سنحاول التعامل معها أو جلب بديل
            if "cf-browser-verification" in response.text or "I'm not a robot" in response.text:
                raise HTTPException(status_code=403, detail="Cloudflare block detected on proxy server")

            return {
                "status": "success",
                "tmdbId": tmdbId,
                "season": season,
                "episode": episode,
                "embed_url": target_url,
                "html": response.text  # إرجاع المحتوى لتحليله إن لزم
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
