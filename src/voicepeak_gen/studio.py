"""本地語音工作室（voice studio）。

跑一個本地 FastAPI，前端可即時拉 slider（情緒混合 / 語速 / 音高）→ 呼叫
Voicepeak 合成 → 瀏覽器馬上播。滿意的配方存回 recipes/<narrator>.json，
成為專案的「情緒配方表」（可重用、跨章一致）。

啟動：voicepeak-gen studio      （見 cli.py）
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from voicepeak_gen.config import Config
from voicepeak_gen.models import Segment
from voicepeak_gen.studio_presets import PRESETS, SAMPLE_TEXT, TARGETS
from voicepeak_gen.synthesizer import list_emotions, list_narrators, synthesize


class SynthReq(BaseModel):
    narrator: str
    text: str
    emotion: dict[str, int] = {}
    speed: int = 100
    pitch: int = 0


class SaveReq(BaseModel):
    narrator: str
    target: str
    emotion: dict[str, int] = {}
    speed: int = 100
    pitch: int = 0


def _recipes_path(recipes_dir: Path, narrator: str) -> Path:
    safe = narrator.replace(" ", "_").replace("/", "_")
    return recipes_dir / f"{safe}.json"


def _load_saved(recipes_dir: Path, narrator: str) -> dict[str, Any]:
    p = _recipes_path(recipes_dir, narrator)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def build_app(config: Config, recipes_dir: Path):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse, Response

    recipes_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="voicepeak_gen studio")

    # 啟動時抓一次角色＋情緒清單（voicepeak CLI 慢，不要每 request 打）
    narrators = list_narrators(config)
    emotions_by_narrator: dict[str, list[str]] = {}
    for n in narrators:
        try:
            emotions_by_narrator[n] = list_emotions(config, n)
        except RuntimeError:
            emotions_by_narrator[n] = []

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return INDEX_HTML

    @app.get("/api/config")
    def api_config() -> JSONResponse:
        out = []
        for n in narrators:
            saved = _load_saved(recipes_dir, n)
            # 存過的覆蓋預設
            presets = {t: dict(PRESETS.get(n, {}).get(t, {"emotion": {}, "speed": 100, "pitch": 0})) for t in TARGETS}
            for t, r in saved.items():
                presets[t] = r
            out.append({
                "name": n,
                "emotions": emotions_by_narrator.get(n, []),
                "sample": SAMPLE_TEXT.get(n, "今日はこれから、駅の向こうまで歩いていくつもりなんだ。"),
                "presets": presets,
                "saved": list(saved.keys()),
            })
        return JSONResponse({"narrators": out, "targets": TARGETS})

    @app.post("/api/synth")
    def api_synth(req: SynthReq) -> Response:
        speed = max(50, min(200, req.speed))
        pitch = max(-300, min(300, req.pitch))
        emotion = {k: max(0, min(100, int(v))) for k, v in req.emotion.items() if int(v) > 0}
        seg = Segment(index=0, narrator=req.narrator, text=req.text or " ",
                      emotion=emotion, speed=speed, pitch=pitch)
        tmp = Path(tempfile.mkdtemp(prefix="vp_studio_")) / "out.wav"
        try:
            synthesize(seg, tmp, config)
            data = tmp.read_bytes()
        finally:
            try:
                tmp.unlink(missing_ok=True)
                tmp.parent.rmdir()
            except OSError:
                pass
        return Response(content=data, media_type="audio/wav")

    @app.post("/api/save")
    def api_save(req: SaveReq) -> JSONResponse:
        p = _recipes_path(recipes_dir, req.narrator)
        saved = _load_saved(recipes_dir, req.narrator)
        saved[req.target] = {
            "emotion": {k: int(v) for k, v in req.emotion.items() if int(v) > 0},
            "speed": int(req.speed),
            "pitch": int(req.pitch),
        }
        # 依 TARGETS 順序寫出，好讀
        ordered = {t: saved[t] for t in TARGETS if t in saved}
        for t in saved:  # 自訂 target（不在 TARGETS）也保留
            ordered.setdefault(t, saved[t])
        p.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return JSONResponse({"ok": True, "path": str(p), "saved": list(ordered.keys())})

    return app


def run_studio(config: Config, recipes_dir: Path, host: str = "127.0.0.1", port: int = 8010) -> None:
    import uvicorn

    app = build_app(config, recipes_dir)
    uvicorn.run(app, host=host, port=port, log_level="warning")


INDEX_HTML = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>voicepeak 語音工作室</title>
<style>
:root{
  --bg:#f6f7f9; --panel:#fff; --ink:#1c2024; --sub:#5b6672; --line:#e2e6ea;
  --accent:#3b6fe0; --accent-ink:#fff; --warn:#c26a00; --ok:#1a8f4c; --track:#dfe4ea;
}
@media (prefers-color-scheme:dark){
  :root{--bg:#14171b;--panel:#1d2126;--ink:#e8ecef;--sub:#9aa5b1;--line:#2c3238;
        --accent:#5b8bff;--track:#2c3238;}
}
:root[data-theme="dark"]{--bg:#14171b;--panel:#1d2126;--ink:#e8ecef;--sub:#9aa5b1;--line:#2c3238;--accent:#5b8bff;--track:#2c3238;}
:root[data-theme="light"]{--bg:#f6f7f9;--panel:#fff;--ink:#1c2024;--sub:#5b6672;--line:#e2e6ea;--accent:#3b6fe0;--track:#dfe4ea;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,"Hiragino Sans","Noto Sans TC",sans-serif}
header{position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--line);padding:12px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;z-index:5}
header h1{font-size:16px;margin:0;font-weight:700}
header .sp{flex:1}
.wrap{max-width:880px;margin:0 auto;padding:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:18px}
label{font-size:13px;color:var(--sub);font-weight:600}
select,textarea,button{font:inherit;color:inherit}
select{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:7px 10px}
textarea{width:100%;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px;resize:vertical;color:inherit}
.row{display:flex;align-items:center;gap:12px;margin:10px 0}
.row .name{width:110px;font-size:13px;color:var(--sub);flex:none}
.row input[type=range]{flex:1;accent-color:var(--accent)}
.row .val{width:52px;text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.btn{background:var(--accent);color:var(--accent-ink);border:none;border-radius:8px;padding:9px 16px;font-weight:600;cursor:pointer}
.btn:disabled{opacity:.5;cursor:default}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.hint{font-size:12px;color:var(--sub)}
.approx{color:var(--warn);font-size:12px;font-weight:600}
pre{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto;font-size:12.5px;margin:0}
.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:var(--ok);color:#fff;padding:10px 18px;border-radius:8px;opacity:0;transition:.25s;pointer-events:none}
.toast.show{opacity:1}
h2.sec{font-size:13px;color:var(--sub);text-transform:uppercase;letter-spacing:.5px;margin:0 0 10px}
</style>
</head>
<body>
<header>
  <h1>🎙️ voicepeak 語音工作室</h1>
  <label>角色 <select id="narrator"></select></label>
  <label>目標語氣 <select id="target"></select></label>
  <span class="sp"></span>
  <button class="btn ghost" id="theme">☀︎/☾</button>
</header>

<div class="wrap">
  <div class="card">
    <label>示範句（可改）</label>
    <textarea id="text" rows="2"></textarea>
    <div class="row" style="margin-top:12px">
      <button class="btn" id="play">▶ 合成並播放</button>
      <button class="btn ghost" id="save">💾 存成此語氣配方</button>
      <span class="hint" id="status"></span>
    </div>
    <audio id="audio" style="display:none"></audio>
  </div>

  <div class="card">
    <h2 class="sec">情緒混合（原生情緒，0–100，可疊加）</h2>
    <div id="emotions"></div>
    <span class="approx" id="approxNote"></span>
  </div>

  <div class="card">
    <h2 class="sec">語速 / 音高</h2>
    <div class="row"><span class="name">語速 speed</span><input type="range" id="speed" min="50" max="200" step="1"><span class="val" id="speedV"></span></div>
    <div class="row"><span class="name">音高 pitch</span><input type="range" id="pitch" min="-300" max="300" step="1"><span class="val" id="pitchV"></span></div>
  </div>

  <div class="card">
    <h2 class="sec">目前配方（存檔就是這串）</h2>
    <pre id="recipe"></pre>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let CFG=null, cur=null; // cur = current narrator config
const $=id=>document.getElementById(id);

async function load(){
  CFG=await (await fetch('/api/config')).json();
  const nsel=$('narrator');
  CFG.narrators.forEach(n=>{const o=document.createElement('option');o.value=n.name;o.textContent=n.name;nsel.appendChild(o);});
  const tsel=$('target');
  CFG.targets.forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=t;tsel.appendChild(o);});
  nsel.onchange=onNarrator; tsel.onchange=onTarget;
  onNarrator();
}
function onNarrator(){
  cur=CFG.narrators.find(n=>n.name===$('narrator').value);
  $('text').value=cur.sample;
  // build emotion sliders for this narrator's native emotions
  const box=$('emotions'); box.innerHTML='';
  cur.emotions.forEach(e=>{
    const row=document.createElement('div'); row.className='row';
    row.innerHTML=`<span class="name">${e}</span><input type="range" data-emo="${e}" min="0" max="100" step="1"><span class="val"></span>`;
    box.appendChild(row);
    const r=row.querySelector('input'); r.oninput=()=>{row.querySelector('.val').textContent=r.value; refreshRecipe();};
  });
  onTarget();
}
function onTarget(){
  const rec=cur.presets[$('target').value]||{emotion:{},speed:100,pitch:0};
  // set emotion sliders
  document.querySelectorAll('#emotions input').forEach(r=>{
    const v=rec.emotion[r.dataset.emo]||0; r.value=v; r.parentElement.querySelector('.val').textContent=v;
  });
  $('speed').value=rec.speed; $('speedV').textContent=rec.speed;
  $('pitch').value=rec.pitch; $('pitchV').textContent=rec.pitch;
  const approx = JSON.stringify(rec).includes('近似'); // never true; marker handled server-side
  $('approxNote').textContent = cur.saved.includes($('target').value) ? '✔ 這個語氣你已存過自訂配方' : '';
  refreshRecipe();
}
function gather(){
  const emotion={};
  document.querySelectorAll('#emotions input').forEach(r=>{const v=+r.value; if(v>0)emotion[r.dataset.emo]=v;});
  return {narrator:$('narrator').value, text:$('text').value, emotion,
          speed:+$('speed').value, pitch:+$('pitch').value};
}
function refreshRecipe(){
  const g=gather();
  $('recipe').textContent=JSON.stringify({emotion:g.emotion,speed:g.speed,pitch:g.pitch},null,2);
}
$('speed').oninput=()=>{$('speedV').textContent=$('speed').value; refreshRecipe();};
$('pitch').oninput=()=>{$('pitchV').textContent=$('pitch').value; refreshRecipe();};

async function play(){
  const b=$('play'); b.disabled=true; $('status').textContent='合成中…';
  try{
    const r=await fetch('/api/synth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(gather())});
    if(!r.ok){throw new Error(await r.text());}
    const blob=await r.blob(); const url=URL.createObjectURL(blob);
    const a=$('audio'); a.src=url; a.style.display='block'; a.controls=true; await a.play();
    $('status').textContent='';
  }catch(e){$('status').textContent='✗ '+e.message;}
  b.disabled=false;
}
async function save(){
  const g=gather();
  const r=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({narrator:g.narrator,target:$('target').value,emotion:g.emotion,speed:g.speed,pitch:g.pitch})});
  const j=await r.json();
  if(j.ok){cur.presets[$('target').value]={emotion:g.emotion,speed:g.speed,pitch:g.pitch};
    if(!cur.saved.includes($('target').value))cur.saved.push($('target').value);
    toast('已存 → '+j.path); onTarget();}
}
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800);}
$('play').onclick=play; $('save').onclick=save;
$('theme').onclick=()=>{const r=document.documentElement;const d=r.getAttribute('data-theme')==='dark';r.setAttribute('data-theme',d?'light':'dark');};
load();
</script>
</body>
</html>"""
