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
    target_url = f"https://vidsrc.sh/embed/tv/{tmdbId}/{season}/{episode}"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://vidsrc.sh/"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            # 1. جلب صفحة الـ Embed الأساسية
            response = await client.get(target_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to reach provider")
            
            html_content = response.text

            # 2. البحث عن أي روابط تدفق مباشرة داخل الصفحة (مثل .m3u8 أو روابط الـ sources الداخلية)
            # (ملاحظة: بعض المزودات تضع الروابط ضمن ملفات جافاسكريبت أو Iframe ثانوي، سنبحث عن الروابط المباشرة إن وجدت)
            m3u8_match = re.search(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', html_content)
            if m3u8_match:
                stream_url = m3u8_match.group(0)
                return {
                    "status": "success",
                    "type": "stream",
                    "embed_url": stream_url
                }

            # 3. إذا لم نجد رابط مباشر، سنبحث عن مصدر الـ Iframe الداخلي ونتابع تتبعه
            iframe_match = re.search(r'src="(https?://[^"]+)"', html_content)
            if iframe_match:
                inner_url = iframe_match.group(1)
                # جلب محتوى الـ Iframe الداخلي
                inner_resp = await client.get(inner_url, headers={"User-Agent": USER_AGENT, "Referer": target_url})
                inner_m3u8 = re.search(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', inner_resp.text)
                if inner_m3u8:
                    return {
                        "status": "success",
                        "type": "stream",
                        "embed_url": inner_m3u8.group(0)
                    }

            # كحل احتياطي إذا تعذر استخراج الرابط المباشر، نعيد الرابط مع إذن خاص
            return {
                "status": "success",
                "type": "embed",
                "embed_url": target_url
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
