# voicepeak_gen — AI 入口指令

## 這個專案是什麼

把「劇本」（CSV 或 JSON，含話者+台詞）轉成一個合併好的音檔，全程用 Voicepeak CLI + ffmpeg，不需要打開 Voicepeak GUI。

主要使用情境：
- 日文學習素材 TTS（JLPT 考古題對話 / 廣播文本 / 小說章節 / 報章雜誌）
- 自製有聲書、自製聽力練習音檔
- 跨多話者的劇本朗讀
- **語音工作室（`studio`）**：本地 web 工具，即時拉 slider 調情緒/語速/音高、試聽、存配方——替角色調出對味的語氣，成果存成可重用的「情緒配方表」。

## 技術棧 / 架構概覽

- **語言:** Python 3.11+
- **套件管理:** uv
- **CLI 框架:** typer（不用 argparse、不用 click 原生）
- **資料驗證:** pydantic v2
- **顯示:** rich（進度條 + 表格）
- **音檔處理:** subprocess → ffmpeg / ffprobe（系統裝的，不用 ffmpeg-python）
- **本地 web（studio）:** FastAPI + uvicorn（僅 studio 用；主 pipeline 不碰 web）
- **架構模式:** 單向 pipeline，模組化（parsers / splitter / synthesizer / merger）；studio 另掛一個薄 web 層
- **編碼風格:** 絕對匯入（不用相對 import）；`from __future__ import annotations`；型別註記完整

**明確排除：**
- 不直接呼叫 Voicepeak GUI 自動化（AppleScript / pyautogui）—— CLI 已足夠
- 不用 ffmpeg-python（增加依賴沒必要）
- 不假設使用者裝特定 narrator —— 由 `--list-narrator` 決定

⚠️ **FastAPI 的 request model MUST 放 module 層，不可定義在函式內**——本專案有 `from __future__ import annotations`，函式內的 Pydantic model 會被 FastAPI 誤判成 query 參數（422）。踩過，見 CHANGELOG 2026-07-11。

## Pipeline 流程

```
INPUT (.csv / .json)
    → parsers/  ── List[Line]
    → splitter  ── 140 字切句 → List[Segment]
    → synthesizer ── voicepeak CLI 逐段 → temp/segment_NNNN.wav
    → merger    ── ffmpeg concat (+ silence gap) → out.wav/mp3
    → cleanup temp/
```

## 對 AI 的操作指引

### 接到「幫我把 X 變音檔」的請求時
1. 先決定話者分配（誰講哪句）
2. 生成 CSV：第一欄是 narrator 名稱或 alias（`moca` / `rikka` / `frimomen`），第二欄是文字
3. 用 `voicepeak-gen check examples/foo.csv` 驗證 narrator 都存在
4. 用 `voicepeak-gen synth examples/foo.csv -o outputs/foo.wav` 跑完整 pipeline

### 接到「要調某角色的語氣 / 試聽情緒」的請求時
1. `voicepeak-gen studio` 啟動本地工作室（預設 `http://127.0.0.1:8010/`），`open` 給使用者。
2. 情緒是主觀的、**沒有標準參數**：先載 `studio_presets.py` 的起始配方，讓使用者試聽微調、存回 `recipes/<narrator>.json`。
3. **每角色只有 4–5 個原生情緒**（`--list-emotion` 撈），十幾種語氣靠「原生情緒混合＋語速＋音高」合成。新增/改配方 → 改 `studio_presets.py`。
4. ⚠️ 呼叫前確認 **Voicepeak GUI 沒開**（兩個實例會 crash）；synthesizer 已有鎖＋重試扛間歇性 segfault。

### 修改規則
- 拆句邏輯改動 → 改 [splitter.py](src/voicepeak_gen/splitter.py) + 加 pytest 案例
- 新增 narrator alias → 改 [config.py](src/voicepeak_gen/config.py) 的 `BUILTIN_DEFAULTS["narrator_aliases"]`（或讓使用者在 `~/.config/voicepeak_gen/config.yaml` 覆寫）
- 新增輸入格式（如 markdown / yaml） → 在 [parsers/](src/voicepeak_gen/parsers/) 加新檔，並在 `parsers/__init__.py` 的 `parse()` dispatch

### 不要做的事
- 不要把暫存 wav 留下來（除非 `--keep-temp`）
- 不要 hardcode `/Applications/voicepeak.app/...` 路徑到 synthesizer / merger —— 一律從 `Config` 拿
- 不要在 CSV parser 裡塞 escape 處理（Voicepeak 原生 CSV 也不支援，照規格走）
- 不要拿掉 synthesizer 的全域鎖／重試（那是扛 Voicepeak 間歇 segfault 的保命機制，見 DESIGN D7）
- 不要把 FastAPI request model 塞進函式內（會 422，見上）

## 五件套

- [CHANGELOG.md](CHANGELOG.md) — 變更/決策時間軸
- [DESIGN.md](DESIGN.md) — 架構與設計決策
- [TODO.md](TODO.md) — 待辦與想法
- [README.md](README.md) — 給人類使用者
