# reference_code/

> **放這裡的東西**：老師給的範例、同事寫的核心邏輯、Stack Overflow 抄來的、官方 demo 等**不是自己寫的參考材料**。
> **目的**：讓 Claude 寫新代碼前**先看這**，避免使用者每次把參考碼貼在對話裡炸 context。

## 使用規則

### 使用者（放檔）

1. 把參考碼放進這資料夾，**檔名要有意義**（`teacher_cleaning.py` 比 `code1.py` 好）
2. 編輯 `_meta/sources.yaml`，記錄這支檔的**來源、用途、可改動程度**
3. 若有多支來自同一來源，建個子資料夾放

### Claude（用檔）

寫任何新代碼**前**：

1. `ls reference_code/` 看有沒有相關檔
2. 讀 `_meta/sources.yaml` 確認該檔的 `usage` 約定
3. 按約定處理（可 copy / 只看概念 / 不准 copy）
4. 寫的代碼若借鑒參考 → 在註解標：`# ref: reference_code/<file> L<start>-<end>`
5. **不要把 reference_code 的原文貼到新檔或對話裡** — 用相對路徑引用即可

## sources.yaml 範例

```yaml
- file: teacher_cleaning.py
  source: "資料科學課期中課堂範例"
  author: "某某老師"
  date: 2026-03-15
  purpose: "CSV 讀檔 + 基礎欄位清洗的概念示範"
  usage: "概念參考，不直接 copy；欄位名稱與資料表結構需要改"
  modifiable: false

- file: peer_visualization.ipynb
  source: "同學 xxx 寫的繪圖 utilities"
  purpose: "matplotlib 中文字體設定 + 圖表風格"
  usage: "可以直接 copy plt.rcParams 段落，其他自行發揮"
  modifiable: true

- file: stackoverflow_s3_download.py
  source: "https://stackoverflow.com/questions/..."
  purpose: "boto3 處理 expired session token 的範例"
  usage: "抓概念即可，實作時加自己的錯誤處理"
  modifiable: true
  license: "CC BY-SA 4.0"
```

## 資料夾示意

```
reference_code/
├── README.md             # 本檔
├── _meta/
│   └── sources.yaml      # 每個檔的元資料
├── teacher_cleaning.py
├── peer_visualization.ipynb
└── stackoverflow_s3_download.py
```

## 為什麼要這樣做

- **省 token**：不用每次把參考碼貼在對話裡
- **可追溯**：日後翻原始出處很方便
- **版權清楚**：`sources.yaml` 記來源與授權
- **Claude 行為一致**：有一套固定動作而不是每次即興
