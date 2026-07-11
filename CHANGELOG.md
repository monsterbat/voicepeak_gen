# CHANGELOG

## 2026-07-11 — 語音工作室（voice studio）+ 呼叫層抗當機

**Why:** 要把小說做成有聲書，得先替每個角色×每種語氣調出對味的參數。Voicepeak 的情緒是主觀美學、網路上沒有權威參數表，唯一可靠辦法是「試聽→微調→再聽」。手動在 GUI 一句句試太慢，做成本地工具讓 SC 拉 slider 即時聽、存配方。

**What:**
- **新增 `voicepeak-gen studio` 子指令**：啟動本地 FastAPI（`studio.py`），瀏覽器拉 slider（情緒混合 / 語速 / 音高）→ 呼叫 voicepeak → 即時播放 → 滿意就存回 `recipes/<narrator>.json`。
- **情緒配方預設 `studio_presets.py`**：15 種「目標語氣」（旁白/溫柔/暴怒/哀傷…，依 Ekman-6＋Plutchik-8＋配音實務歸納）× 3 角色的起始建議值。**關鍵設計：每角色只有 4–5 個原生情緒，十幾種人類語氣是靠「原生情緒混合＋語速＋音高」合成**；某角色缺對應原生情緒時用「近似」（程式內註解標明）。
- **依賴新增 fastapi / uvicorn**。
- **synthesizer 抗當機（重要）**：Voicepeak 1.2.22 在 macOS 26.5 會間歇性 segfault、且不能同時跑兩個實例。加 ① 全域鎖序列化每次呼叫、② 失敗自動重試 3 次。連打 5 次不同角色/情緒合成全部通過。

**踩到的雷（記下防再犯）：**
- FastAPI + `from __future__ import annotations` + **函式內定義的 Pydantic model** → body 參數被誤判成 query（422 missing）。**解法：request model 一律放 module 層**（annotation 變字串後靠 module globals 解析）。

**Open:**
- 音量 / 停頓還沒接（Voicepeak CLI 無原生參數，要靠 ffmpeg 後處理 / 句間 gap）——做整章有聲書時再一起加。
- studio 目前只服務「單句試聽」，還沒接「整段預先渲染」的有聲書輸出。

## 2026-05-25 — 初始版本 P1 MVP 完成

**Why:** SC 需要把 JLPT 考古題對話 / 廣播 / 小說等學習素材轉成音檔，手動操作 Voicepeak GUI 太耗時。Voicepeak 內建 CLI 支援多話者批次合成，可以全自動化。

**What:**
- 建立 uv 專案 + 五件套骨架
- Pipeline 全程跑通：`CSV → 拆句 → voicepeak CLI → ffmpeg concat → wav/mp3`
- 三個 typer 子指令：`synth` / `narrators` / `emotions` / `check`
- 內建 narrator alias：`moca` / `rikka` / `frimomen` / `茉歌` / `六花`
- 句間 silence gap 可調（預設 300ms）
- 輸出支援 `.wav`（PCM 16-bit）和 `.mp3`（libmp3lame VBR）

**Smoke test 結果：**
- `examples/hello.csv`（3 句）→ `outputs/hello.wav` 8.83 秒 ✓
- `examples/exam_dialogue.csv`（5 句辦公室對話）→ `outputs/exam_dialogue.mp3` 27 秒 ✓

**Open:**
- 還沒寫 pytest 測試（splitter 的 140 字邊界邏輯應該補）
- 還沒做 Markdown → CSV 自動萃取器（P3 計畫，給考古題對話直接抽出）
- 還沒整合進 Japanese 專案的 CLAUDE.md SOP 路由表
