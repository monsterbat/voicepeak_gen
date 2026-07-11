"""情緒配方預設（voice studio 用）。

每個角色只有 4–5 個 Voicepeak 原生情緒，所以「十幾種人類語氣」是靠
「原生情緒混合 + 語速 + 音高」合成出來的。這裡是 AI（Claude）依各角色
情緒盤給的**起始建議值**，使用者在 studio 裡試聽微調後覆寫存回 recipes/。

recipe schema:
    {"emotion": {<原生情緒名>: 0-100, ...}, "speed": 50-200, "pitch": -300-300}

「近似」註記：該角色沒有對應原生情緒，只能用其他情緒＋語速/音高逼近。
"""

from __future__ import annotations

# 15 種目標語氣，固定順序（studio 下拉依此排）
TARGETS: list[str] = [
    "旁白/中性",
    "平常對話",
    "朋友閒聊/暖",
    "溫柔",
    "開心/雀躍",
    "情緒高漲/興奮",
    "得意/自滿",
    "揶揄/俏皮",
    "嘀咕/碎念",
    "緊張/不安",
    "驚訝",
    "生氣/惱怒(輕)",
    "暴怒/憤怒(重)",
    "難過/悲傷",
    "哀傷/哭泣",
]

# 每角色的示範句（試聽時只變情緒、不變內容，方便對比）
SAMPLE_TEXT: dict[str, str] = {
    "Koharu Rikka": "今日はこれから、駅の向こうまで歩いていくつもりなんだ。",
    "Miyamai Moca": "今日はこれから、駅の向こうまで歩いていくつもりなんだ。",
    "Frimomen": "今日はこれから、駅の向こうまで歩いていくつもりなんだ。",
}

# recipe: {"emotion": {...}, "speed": int, "pitch": int}
# ── Koharu Rikka（小春六花）: hightension / livid / lamenting / despising / narration
_RIKKA = {
    "旁白/中性":       {"emotion": {"narration": 50}, "speed": 100, "pitch": 0},
    "平常對話":       {"emotion": {"narration": 25}, "speed": 100, "pitch": 0},
    "朋友閒聊/暖":     {"emotion": {"hightension": 20}, "speed": 102, "pitch": 5},
    "溫柔":           {"emotion": {"lamenting": 12}, "speed": 92, "pitch": 0},   # 近似：無溫柔
    "開心/雀躍":       {"emotion": {"hightension": 55}, "speed": 106, "pitch": 10},
    "情緒高漲/興奮":   {"emotion": {"hightension": 90}, "speed": 112, "pitch": 12},
    "得意/自滿":       {"emotion": {"despising": 25, "hightension": 30}, "speed": 100, "pitch": 4},  # 近似
    "揶揄/俏皮":       {"emotion": {"despising": 35}, "speed": 104, "pitch": 6},
    "嘀咕/碎念":       {"emotion": {"narration": 20}, "speed": 90, "pitch": -8},   # 近似：無嘀咕
    "緊張/不安":       {"emotion": {"lamenting": 30}, "speed": 108, "pitch": 6},
    "驚訝":           {"emotion": {"hightension": 60}, "speed": 110, "pitch": 14},
    "生氣/惱怒(輕)":   {"emotion": {"livid": 40}, "speed": 104, "pitch": 2},
    "暴怒/憤怒(重)":   {"emotion": {"livid": 95}, "speed": 116, "pitch": 8},
    "難過/悲傷":       {"emotion": {"lamenting": 60}, "speed": 90, "pitch": -15},
    "哀傷/哭泣":       {"emotion": {"lamenting": 95}, "speed": 84, "pitch": -22},
}

# ── Miyamai Moca（宮舞モカ）: bosoboso / doyaru / honwaka / angry / teary
_MOCA = {
    "旁白/中性":       {"emotion": {}, "speed": 100, "pitch": 0},               # 無旁白情緒→中性空
    "平常對話":       {"emotion": {"honwaka": 15}, "speed": 100, "pitch": 0},
    "朋友閒聊/暖":     {"emotion": {"honwaka": 45}, "speed": 102, "pitch": 3},
    "溫柔":           {"emotion": {"honwaka": 80}, "speed": 96, "pitch": 0},
    "開心/雀躍":       {"emotion": {"honwaka": 40, "doyaru": 20}, "speed": 106, "pitch": 8},
    "情緒高漲/興奮":   {"emotion": {"doyaru": 30, "honwaka": 30}, "speed": 110, "pitch": 10},  # 近似：無亢奮
    "得意/自滿":       {"emotion": {"doyaru": 85}, "speed": 102, "pitch": 5},
    "揶揄/俏皮":       {"emotion": {"doyaru": 50}, "speed": 104, "pitch": 6},
    "嘀咕/碎念":       {"emotion": {"bosoboso": 85}, "speed": 92, "pitch": -6},
    "緊張/不安":       {"emotion": {"bosoboso": 40, "teary": 20}, "speed": 106, "pitch": 4},
    "驚訝":           {"emotion": {"doyaru": 25}, "speed": 110, "pitch": 14},    # 近似
    "生氣/惱怒(輕)":   {"emotion": {"angry": 40}, "speed": 104, "pitch": 2},
    "暴怒/憤怒(重)":   {"emotion": {"angry": 95}, "speed": 114, "pitch": 8},
    "難過/悲傷":       {"emotion": {"teary": 55}, "speed": 92, "pitch": -12},
    "哀傷/哭泣":       {"emotion": {"teary": 95}, "speed": 86, "pitch": -18},
}

# ── Frimomen（男聲）: happy / angry / sad / ochoushimono
_FRIMOMEN = {
    "旁白/中性":       {"emotion": {}, "speed": 100, "pitch": 0},
    "平常對話":       {"emotion": {"happy": 10}, "speed": 100, "pitch": 0},
    "朋友閒聊/暖":     {"emotion": {"happy": 30}, "speed": 102, "pitch": 2},
    "溫柔":           {"emotion": {"happy": 15, "sad": 10}, "speed": 94, "pitch": -2},  # 近似：無溫柔
    "開心/雀躍":       {"emotion": {"happy": 70}, "speed": 106, "pitch": 6},
    "情緒高漲/興奮":   {"emotion": {"happy": 60, "ochoushimono": 40}, "speed": 112, "pitch": 8},
    "得意/自滿":       {"emotion": {"ochoushimono": 85}, "speed": 102, "pitch": 4},
    "揶揄/俏皮":       {"emotion": {"ochoushimono": 55}, "speed": 104, "pitch": 5},
    "嘀咕/碎念":       {"emotion": {"sad": 15}, "speed": 90, "pitch": -8},        # 近似：無嘀咕
    "緊張/不安":       {"emotion": {"sad": 25}, "speed": 108, "pitch": 5},        # 近似
    "驚訝":           {"emotion": {"happy": 40, "ochoushimono": 30}, "speed": 110, "pitch": 12},  # 近似
    "生氣/惱怒(輕)":   {"emotion": {"angry": 40}, "speed": 104, "pitch": 1},
    "暴怒/憤怒(重)":   {"emotion": {"angry": 95}, "speed": 116, "pitch": 6},
    "難過/悲傷":       {"emotion": {"sad": 60}, "speed": 90, "pitch": -14},
    "哀傷/哭泣":       {"emotion": {"sad": 95}, "speed": 84, "pitch": -20},
}

PRESETS: dict[str, dict[str, dict]] = {
    "Koharu Rikka": _RIKKA,
    "Miyamai Moca": _MOCA,
    "Frimomen": _FRIMOMEN,
}
