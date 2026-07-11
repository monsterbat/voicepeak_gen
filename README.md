# voicepeak_gen

把劇本（CSV / JSON，含話者+台詞）變成一個合併好的音檔，全程用 Voicepeak CLI + ffmpeg，**不開 Voicepeak GUI**。

## 為什麼用這個

需要一段「多人對話」或「長文本朗讀」的音檔，例如：
- JLPT 考古題對話自製練習音檔
- 把小說章節做成自家有聲書
- 廣播風格的講解配音

如果手動操作 Voicepeak GUI，每句要點選 narrator、貼上文字、按合成，數十句下來非常耗時。本工具讓你寫好 CSV 一條指令就跑完。

## 需要先裝

- macOS（其他平台沒測過）
- [Voicepeak](https://www.ah-soft.com/voice/)（必須先在 GUI 內 activate 你買的語音包）
- ffmpeg：`brew install ffmpeg`
- [uv](https://docs.astral.sh/uv/)：`brew install uv`

## 安裝

```bash
cd /path/to/voicepeak_gen
uv sync
```

## 快速試用

```bash
# 看你裝了哪些 narrator + 對應的 alias
uv run voicepeak-gen narrators

# 用內建範例跑一次（3 句、用三個 narrator 各說一句）
uv run voicepeak-gen synth examples/hello.csv -o outputs/hello.wav
```

## CSV 格式

```csv
# 註解行（以 # 開頭）會被略過
narrator_or_alias,要講的句子
moca,こんにちは、私は宮舞茉歌です。
rikka,こんにちは、私は小春六花です。
```

- 分隔符可以是逗號或 tab
- 第一欄可以是 narrator 全名（`Miyamai Moca`）或 alias（`moca` / `茉歌`）
- UTF-8 編碼
- 一句一行，不支援雙引號 / `\n` escape

## JSON 格式（要精細控制 emotion / speed / pitch 時）

```json
[
  {"narrator": "moca", "text": "本当に嬉しい！", "emotion": {"honwaka": 50}, "speed": 105},
  {"narrator": "rikka", "text": "ええ、よかったですね。", "speed": 95, "pitch": -20}
]
```

## 語音工作室（studio）——即時試聽、調語氣、存配方

要替角色調出「暴怒」「溫柔」「哀傷」等對味的語氣時，用這個：

```bash
voicepeak-gen studio          # 開 http://127.0.0.1:8000/
```

瀏覽器裡：**選角色 → 選目標語氣（載入內建起始配方）→ 拉 slider（情緒混合／語速／音高）→ ▶ 即時聽 → 💾 存**。存出來的配方寫進 `recipes/<narrator>.json`，成為你自己的「情緒配方表」，之後做整章有聲書逐句套用、保持全書語氣一致。

- 每個角色只有 4–5 個 Voicepeak 原生情緒，十幾種人類語氣是靠「原生情緒混合＋語速＋音高」**合成**出來的（缺對應情緒的會標「近似」）。
- 情緒數值是主觀美學、沒有標準答案 → 內建配方只是**起始值**，靠你試聽微調。
- ⚠️ 用 studio 時**別開 Voicepeak GUI 主程式**（兩個實例會讓 Voicepeak 當掉）。

## CLI 指令一覽

```bash
voicepeak-gen synth <input> -o <output> [--gap-ms 300] [--keep-temp]
voicepeak-gen studio [--port 8000] [--recipes-dir recipes]   # 本地語音工作室
voicepeak-gen check <input>          # 驗證輸入檔（不合成）
voicepeak-gen narrators              # 列出可用 narrator + alias
voicepeak-gen emotions <narrator>    # 列出某 narrator 的 emotion 選項
```

## 設定檔（可選）

複製 `config.example.yaml` 到 `~/.config/voicepeak_gen/config.yaml` 編輯，可覆寫內建 alias / 路徑 / 預設值。

## 限制

- Voicepeak CLI 一次最多 140 字 → 工具會自動拆句（在句號/逗號處）
- 一個 segment 只能一個 narrator → 多話者必須拆成多行 CSV
- 不支援 Voicepeak 那邊「無限合成版授權」之外的商業用途

## 開發

- 五件套：[CLAUDE.md](CLAUDE.md) / [CHANGELOG.md](CHANGELOG.md) / [DESIGN.md](DESIGN.md) / [TODO.md](TODO.md)
- 進入點：[src/voicepeak_gen/cli.py](src/voicepeak_gen/cli.py)
- Pipeline 圖：見 [DESIGN.md](DESIGN.md) 第 3 節
