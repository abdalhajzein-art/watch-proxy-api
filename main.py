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
    return {"status": "Online", "message": "Watch Proxy API with Multi-Fallback is running!"}

@app.get("/api/resolve/tv")
async def resolve_tv(tmdbId: int, season: int, episode: int):
    # قائمة المزودين الذين نجح فحصهم وأعطوا استجابة 200 OK
    providers = [
        f"https://vidsrc.to/embed/tv/{tmdbId}/{season}/{episode}",
        f"https://multiembed.mov/?video_id={tmdbId}&tmdb=1&s={season}&e={episode}",
        f"https://vidlink.pro/tv/{tmdbId}/{season}/{episode}",
        f"https://vidsrc.pm/embed/tv/{tmdbId}/{season}/{episode}",
        f"https://www.2embed.cc/embedtv/{tmdbId}&s={season}&e={episode}"
    ]

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://google.com"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for url in providers:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "embed_url": url
                    }
            except Exception:
                continue

    raise HTTPException(status_code=404, detail="All providers failed to respond.")
