# DESIGN

## 1. 設計目標

把「文本素材（含話者標記）」轉成「一個合併好的音檔」，全程自動，使用者不打開任何 GUI。

## 2. 不變條件（invariants）

- Voicepeak CLI 每次 ≤ 140 字（硬限制，無法繞過）
- Voicepeak CLI 一次只能指定一個 narrator → 多話者必須逐段呼叫
- ffmpeg concat demuxer 要求所有輸入檔取樣率/聲道一致；Voicepeak 輸出固定 48kHz mono，所以可以直接 concat
- 中間 wav 不入 git（在 `.gitignore`）
- **Voicepeak 不能同時跑兩個實例，且 1.2.x on macOS 26 會間歇性 segfault** → 每次 CLI 呼叫必須序列化（全域鎖）＋失敗重試（見 D7）。呼叫 studio 前也不能開 Voicepeak GUI。

## 3. 主要模組

```
src/voicepeak_gen/
├── cli.py              ← typer 入口（synth / narrators / emotions / check）
├── config.py           ← yaml 設定 + narrator alias
├── models.py           ← Line / Segment（pydantic）
├── parsers/
│   ├── __init__.py     ← dispatch by extension
│   ├── csv_parser.py   ← CSV/TSV/TXT → List[Line]
│   └── json_parser.py  ← JSON → List[Line]
├── splitter.py         ← Line → Segment（140 字切句）
├── synthesizer.py      ← Segment → wav（subprocess Voicepeak；全域鎖＋重試）
├── merger.py           ← List[wav] → 最終音檔（ffmpeg concat + silence gap）
├── studio.py           ← 本地語音工作室（FastAPI；即時試聽調參存配方）
└── studio_presets.py   ← 15 種目標語氣 × 3 角色的情緒配方起始值
```

## 4. 關鍵設計決策

### D1：為什麼有 `Line` 和 `Segment` 兩個 model？

- **Line** = 使用者輸入的一句（可能超過 140 字）
- **Segment** = 拆句後一定 ≤ 140 字的單元，1:1 對應一個 wav

分開好處：parser 不需要知道 140 字限制；splitter 不需要知道輸入格式。

### D2：拆句策略

優先順序：
1. 主要終止符 `。！？!?` → 句號切割
2. 次要 `、，,` → 逗號切割（只在第一步切完仍超過時用）
3. 硬切（fallback，理論上不會發生於日文）

切完後用 greedy 合併把小段重新打包到 ≤ 140 字，避免過多 segment 影響流暢度。

### D3：silence gap 用 ffmpeg lavfi anullsrc

不用 sox（多一個依賴）；不在 Voicepeak 那邊加靜音（增加合成時間）。
直接用 `ffmpeg -f lavfi -i anullsrc=...` 生成一個小 wav，加入 concat list。

### D4：subprocess 不用 capture_output 的 stderr 嗎？

有 capture，但 Voicepeak 會吐 `[debug]` log 到 stderr 是正常的，所以僅在 `returncode != 0` 或 wav 沒生成時才當錯誤。

### D5：narrator alias 寫在程式碼 vs config

兩邊都支援：
- 程式碼 `BUILTIN_DEFAULTS` 提供 SC 當前語音包的 alias（換電腦帶著走）
- 使用者 `~/.config/voicepeak_gen/config.yaml` 可覆寫（不入 git）

### D6：語音工作室（studio）——情緒是「合成」出來的

Voicepeak 每個角色只有 4–5 個**原生情緒**（`--list-emotion` 撈得到），但小說朗讀需要十幾種人類語氣。所以：

- 定一組 **15 種「目標語氣」**（旁白/平常對話/溫柔/暴怒/哀傷…，骨架＝ Ekman-6 ＋ Plutchik-8 ＋配音實務）。
- 每個角色替每種目標語氣寫一份**配方** `{"emotion": {原生情緒: 0-100 可疊加}, "speed": …, "pitch": …}`，用「原生情緒混合＋語速＋音高」逼近。角色缺對應原生情緒時標「近似」。
- 情緒是主觀美學、**沒有權威參數表**，所以配方是「起始值」，靠 studio 試聽微調後覆寫存回 `recipes/<narrator>.json`。存出來的配方＝專案的「情緒配方表」，供之後有聲書逐句套用、保持全書一致。
- studio 用 FastAPI 而非 typer/rich，因為要「即時互動＋播音」，靜態 HTML（`file://`）無法呼叫 voicepeak。前端拉 slider → `POST /api/synth` → 回傳 wav bytes → 瀏覽器 `Audio` 播放。

### D7：呼叫層抗當機（全域鎖＋重試）

Voicepeak 1.2.22 在 macOS 26.5 會間歇性 segfault，且**同時兩個實例必當**。`synthesizer.synthesize` 因此：

- 用 module 層 `threading.Lock` 把每次 `subprocess.run` 序列化（studio 的併發 HTTP 執行緒也共用這把鎖）。
- 對「returncode≠0 或 wav 沒生出來」**重試 3 次**（間隔 0.8s），連敗才拋 `RuntimeError`。
- 呼應母專案紀律「工具失敗要能扛住、退回不能比人工更糟」——呼叫方不該因為被呼叫的 app 抽風就整個爆掉。

## 5. 未來擴充點

- **Markdown → CSV 萃取器**：考古題 markdown 裡的對話有固定格式（`男：…` / `女：…`），可以自動轉 CSV
- **YAML 輸入**：人類最易讀，可以做為第三種 parser
- **章節分割輸出**：長小說可以每 10 句切一個 mp3，方便手機聽
- **batch mode**：一次處理一個資料夾下所有 csv

## 6. 已知限制

- Voicepeak CSV 規格不支援雙引號 / 換行 escape → 我們也不處理
- Voicepeak 沒有 SSML 等級的細粒控制 → 用 JSON 模式設 emotion 已足夠
- 沒有 streaming，必須等所有 segment 跑完才合併 → 長文本可能要等幾分鐘
