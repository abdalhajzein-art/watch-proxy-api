from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Watch Proxy API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Online", "message": "Watch Proxy API is running!"}

@app.get("/api/resolve/tv")
async def resolve_tv(tmdbId: int, season: int, episode: int):
    # إرجاع رابط الـ Embed الجاهز والمباشر للمسلسلات دون فشل
    target_url = f"https://vidsrc.cc/v2/embed/tv/{tmdbId}/{season}/{episode}"
    return {
        "status": "success",
        "embed_url": target_url
    }
