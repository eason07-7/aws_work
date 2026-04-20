# _ppt_workspace/

> **邊做邊堆 PPT 素材的空間**。整個專題產出的圖、決策、數字都往這丟，到 Present 階段 `build_ppt.py` 會自動整理。

## 結構

```
_ppt_workspace/
├── README.md              # 本檔
├── artifacts/             # 圖、截圖、CSV 片段、關鍵檔案
├── decisions.md           # 從實驗記錄萃取的關鍵決策
├── findings.md            # 值得上 PPT 的數據結論
└── content_draft.md       # PPT 骨架（隨專案成長）
```

## 使用時機

### 建構期（Build / Iterate）

Claude 每產生以下東西 → **立即 copy 到 artifacts/**：

- 任何 `.png` 圖表
- 關鍵 CSV 的 head(n=20) preview
- 有意義的截圖
- AI 分析報告的摘錄

### 中期（Harvest）

使用者說「整理一下 PPT 素材」→ Claude 執行：

```bash
python D:\p\workflow\scripts\harvest_to_ppt.py <project_path>
```

會自動：
1. 掃 `JOURNAL.md` 的 **Why / Result** 欄位 → 追加到 `decisions.md`
2. 找出包含數字 / 百分比 / z-score 的段落 → 追加到 `findings.md`
3. 提醒 artifacts/ 裡哪些圖還沒被引用

### 產出（Present）

```bash
python D:\p\workflow\scripts\build_ppt.py <project_path>
```

讀 `content_draft.md`，呼叫內建 ppt-master 產生 `.pptx`。

## content_draft.md 結構

init 時是空的，隨專案成長而填充。建議結構：

```markdown
# 專題標題

## Slide 1 — 封面
...

## Slide 2 — 目錄
...

## Slide N — 方法
![method](artifacts/method_flow.png)
...
```

Markdown 圖片連結用相對路徑指向 `artifacts/` 即可。
