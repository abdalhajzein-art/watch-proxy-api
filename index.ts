// @ts-nocheck
import fetch from "node-fetch";

const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
const VIDEASY_API = "https://api.videasy.net";
const VIDEASY_DEC = "https://enc-dec.app/api/dec-videasy";

export default async function handler(req, res) {
  const urlParams = new URL(req.url, `https://a.b`).searchParams;
  const tmdb = urlParams.get("tmdb");
  const type = urlParams.get("type") || "tv";
  const season = urlParams.get("season") || "1";
  const episode = urlParams.get("episode") || "1";

  if (!tmdb) {
    return res.status(400).json({ error: "Missing tmdb parameter" });
  }

  try {
    // 1. جلب البيانات المشفرة للمسلسل من Videasy API
    const extractUrl = `${VIDEASY_API}/mb-flix/sources-with-title?mediaType=${type}&tmdbId=${tmdb}&season=${season}&episode=${episode}&title=`;
    
    const extractResp = await fetch(extractUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        "Referer": "https://player.videasy.net/",
        "Origin": "https://player.videasy.net"
      }
    });

    if (!extractResp.ok) {
      return res.status(500).json({ error: "Failed to fetch source from provider" });
    }

    const encData = await extractResp.text();

    // 2. فك التشفير عبر خدمة فك التشفير الخارجية
    const decResp = await fetch(VIDEASY_DEC, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
      },
      body: JSON.stringify({ text: encData, id: tmdb })
    });

    if (!decResp.ok) {
      return res.status(500).json({ error: "Failed to decrypt source data" });
    }

    const decJson = await decResp.json();
    let result = decJson.result;
    
    if (typeof result === "string") {
      result = JSON.parse(result);
    }

    const sources = result?.sources || [];
    if (sources.length === 0) {
      return res.status(404).json({ error: "No streaming sources found" });
    }

    // إرجاع النتيجة بالهيكلية التي ينتظرها تطبيق الأندرويد
    const apiResponse = sources.map(src => ({
      name: "Server 1",
      mediaId: tmdb,
      stream: src.url,
      referer: "https://player.videasy.net/"
    }));

    return res.status(200).json(apiResponse);

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
