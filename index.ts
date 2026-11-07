// @ts-nocheck
import * as cheerio from "cheerio";
import { decrypt } from "./helpers/decoder.js";

let BASEDOM = "https://vidsrc.net";

const COMMON_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.9",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
};

async function serversLoad(html: string) {
  const $ = cheerio.load(html);
  const servers = [];
  const title = $("title").text() ?? "";
  const base = $("iframe").attr("src") ?? "";
  if (base) {
    BASEDOM = new URL(base.startsWith("//") ? "https:" + base : base).origin ?? BASEDOM;
  }
  $(".serversList .server").each((index, element) => {
    const server = $(element);
    servers.push({
      name: server.text().trim(),
      dataHash: server.attr("data-hash") ?? null,
    });
  });
  return { servers, title };
}

async function PRORCPhandler(prorcp: string): Promise<string | null> {
  try {
    const prorcpFetch = await fetch(`${BASEDOM}/prorcp/${prorcp}`, {
      headers: { ...COMMON_HEADERS, "Referer": `${BASEDOM}/` }
    });
    const prorcpResponse = await prorcpFetch.text();
    const scripts = prorcpResponse.match(/<script\s+src="\/([^"]*\.js)\?\_=([^"]*)"><\/script>/gm);
    if (!scripts || scripts.length === 0) return null;
    
    const scriptTag = scripts[scripts.length - 1].includes("cpt.js") && scripts.length > 1
      ? scripts[scripts.length - 2]
      : scripts[scripts.length - 1];
      
    const script = scriptTag.replace(/.*src="\/([^"]*\.js)\?\_=([^"]*)".*/, "$1?_=$2");
  
    const jsFileReq = await fetch(`${BASEDOM}/${script}`, { 
      headers: { ...COMMON_HEADERS, "Referer": `${BASEDOM}/` } 
    });
    const jsCode = await jsFileReq.text();
    const decryptRegex = /{}\}window\[([^"]+)\("([^"]+)"\)/;
    const decryptMatches = jsCode.match(decryptRegex);
    const $ = cheerio.load(prorcpResponse);
    if (!decryptMatches || decryptMatches.length < 3) return null;
    
    const id = decrypt(decryptMatches[2].toString().trim(), decryptMatches[1].toString().trim());
    const data = $("#" + id);
    return await decrypt(await data.text(), decryptMatches[2].toString().trim());
  } catch (e) {
    return null;
  }
}

async function rcpGrabber(html: string) {
  const regex = /src:\s*'([^']*)'/;
  const match = html.match(regex);
  if (!match) return null;
  return { metadata: { image: "" }, data: match[1] };
}

async function tmdbScrape(tmdbId: string, type: "movie" | "tv", season?: number, episode?: number) {
  const url = (type === "movie")
    ? `https://vidsrc.net/embed/${type}?tmdb=${tmdbId}`
    : `https://vidsrc.net/embed/${type}?tmdb=${tmdbId}&season=${season}&episode=${episode}`;
  
  const embed = await fetch(url, { headers: COMMON_HEADERS });
  const embedResp = await embed.text();
  const { servers, title } = await serversLoad(embedResp);

  const rcpFetchPromises = servers.map(element => 
    fetch(`${BASEDOM}/rcp/${element.dataHash}`, { 
      headers: { ...COMMON_HEADERS, "Referer": url } 
    })
  );
  const rcpResponses = await Promise.all(rcpFetchPromises);
  const prosrcrcp = await Promise.all(rcpResponses.map(async (res) => rcpGrabber(await res.text())));

  const apiResponse = [];
  for (const item of prosrcrcp) {
    if (!item) continue;
    if (item.data.startsWith("/prorcp/")) {
      const streamUrl = await PRORCPhandler(item.data.replace("/prorcp/", ""));
      if (streamUrl) {
        apiResponse.push({
          name: title,
          mediaId: tmdbId,
          stream: streamUrl,
          referer: BASEDOM,
        });
      }
    }
  }
  return apiResponse;
}

// Handler for Vercel Serverless
export default async function handler(req, res) {
  const urlParams = new URL(req.url, `https://${req.headers.host}`).searchParams;
  const tmdb = urlParams.get("tmdb");
  const type = urlParams.get("type") || "tv";
  const season = urlParams.get("season") ? parseInt(urlParams.get("season")) : undefined;
  const episode = urlParams.get("episode") ? parseInt(urlParams.get("episode")) : undefined;

  if (!tmdb) {
    return res.status(400).json({ error: "Missing tmdb parameter" });
  }

  try {
    const data = await tmdbScrape(tmdb, type, season, episode);
    return res.status(200).json(data);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
