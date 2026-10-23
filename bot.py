# -*- coding: utf-8 -*-
"""
هيكل أساسي للمكالمات الصوتية الحية:
Telegram Mini App (الصفحة في المتصفح)  <--WebSocket-->  هذا السيرفر  <--Live API-->  Gemini
 
التشغيل:  uvicorn live_server:app --host 0.0.0.0 --port 8000
(يجب نشره على HTTPS، مثلاً خلف Nginx/Cloudflare، لأن Telegram Mini Apps والميكروفون يتطلبان HTTPS)
"""
import os
import asyncio
 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
 
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
# اسم موديل Live يتغير باستمرار؛ راجع صفحة Live API في توثيق Gemini للاسم الحالي.
LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025")
 
client = genai.Client(api_key=API_KEY)
app = FastAPI()
 
LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction="You are a friendly voice assistant. Reply in the user's language, briefly.",
)
 
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://telegram.org/js/telegram-web-app.js"></script></head>
<body style="font-family:sans-serif;text-align:center;padding:30px">
<h3>🎙️ مكالمة صوتية مع Gemini</h3>
<button id="btn" style="font-size:20px;padding:14px 28px">ابدأ المكالمة</button>
<script>
const tg = window.Telegram.WebApp; tg.expand();
let ws, ctx, stream, node, playTime = 0;
 
document.getElementById('btn').onclick = async () => {
  ws = new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');
  ws.binaryType = 'arraybuffer';
  stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true}});
  ctx = new AudioContext({sampleRate:16000});
  await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([`
    class P extends AudioWorkletProcessor{process(i){const c=i[0][0];if(c){
      const p=new Int16Array(c.length);for(let k=0;k<c.length;k++)p[k]=Math.max(-1,Math.min(1,c[k]))*32767;
      this.port.postMessage(p.buffer,[p.buffer]);}return true;}}
    registerProcessor('p',P);`],{type:'application/javascript'})));
  const src = ctx.createMediaStreamSource(stream);
  node = new AudioWorkletNode(ctx,'p');
  node.port.onmessage = e => ws.readyState===1 && ws.send(e.data);   // PCM16 @16kHz -> السيرفر
  src.connect(node);
 
  ws.onmessage = e => {                                               // PCM16 @24kHz <- السيرفر
    const i16 = new Int16Array(e.data), f32 = new Float32Array(i16.length);
    for (let k=0;k<i16.length;k++) f32[k]=i16[k]/32768;
    const buf = ctx.createBuffer(1,f32.length,24000); buf.copyToChannel(f32,0);
    const s = ctx.createBufferSource(); s.buffer=buf; s.connect(ctx.destination);
    playTime = Math.max(playTime, ctx.currentTime); s.start(playTime); playTime += buf.duration;
  };
  document.getElementById('btn').textContent='جارٍ الاتصال... تحدّث الآن';
};
</script></body></html>"""
 
 
@app.get("/", response_class=HTMLResponse)
async def index():
    return PAGE
 
 
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as session:
 
            async def browser_to_gemini():
                while True:
                    chunk = await ws.receive_bytes()
                    await session.send_realtime_input(
                        audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                    )
 
            async def gemini_to_browser():
                while True:
                    async for resp in session.receive():
                        if resp.data:
                            await ws.send_bytes(resp.data)
 
            t1 = asyncio.create_task(browser_to_gemini())
            t2 = asyncio.create_task(gemini_to_browser())
            done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print("live error:", e)
    finally:
        try:
            await ws.close()
        except Exception:
            pass