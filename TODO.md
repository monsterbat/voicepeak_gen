# TODO

## Now（P2）

- [ ] **小說有聲書：逐句預先渲染 + 閱讀器每行喇叭鍵**（給電子書/HTML；離線 e-ink 可播）。詳見 Japanese 專案 novel-reading skill / CLAUDE。用 studio 存的 `recipes/` 逐句套語氣。
- [ ] **音量 / 停頓** 接進 Line/Segment：音量＝ffmpeg gain 後處理、停頓＝句間 gap 或標點；studio slider 也補這兩軌。
- [ ] 把 splitter 的 140 字邊界邏輯加 pytest（特別是長文本、混合句號逗號的情境）
- [ ] CLI 加 `--dry-run`（只列出 segment 不實際呼叫 voicepeak）
- [ ] CLI 加 `--narrator-override`（全局換 narrator，方便試聽不同聲音）
- [ ] config 加 `narrator_presets`：每個 narrator 預設 emotion（如 Moca 預設 honwaka=30）

## Later（P3）

- [ ] Markdown 解析器：從考古題 markdown 抽出 `**[說話者]：句子`格式的對話 → 自動轉 CSV
- [ ] 把 `voicepeak-gen` 整合進 Japanese 專案 `CLAUDE.md` 的 SOP 路由表
- [ ] 寫 `notes/TTS_SOP.md`（Japanese 專案內），記錄如何從考古題/小說產生 CSV
- [ ] batch mode：`voicepeak-gen synth-dir input_csvs/ -o outputs/`
- [ ] 章節分割：`--split-every 10` 把長劇本切成多個 mp3

## Ideas（未排程）

- [ ] 字幕同步輸出 SRT（每 segment 都知道起始時間）
- [ ] 跟 VocaNode 反向整合：VocaNode 萃取的 transcript.json → 直接生成 narrator 版本（用不同聲音重新講一遍）
- [ ] GUI wrapper（rich textual 或 streamlit），給不想用 CLI 的場合

## Done

- [x] uv 專案骨架 + 五件套
- [x] CSV / JSON parser
- [x] Splitter（140 字）
- [x] Synthesizer（voicepeak CLI 包裝）
- [x] Merger（ffmpeg concat + silence gap）
- [x] CLI（typer：synth / narrators / emotions / check）
- [x] Pipeline 全程 smoke test 通過
- [x] 語音工作室 studio（FastAPI 即時試聽調參存配方）＋ 15 種語氣 × 3 角色配方預設（2026-07-11）
- [x] synthesizer 全域鎖＋重試（扛 Voicepeak 間歇 segfault，2026-07-11）
