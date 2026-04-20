# @workflow 專案守則

> 這個專案用 `workflow` skill 起家。Claude Code 進來**一定要讀這份檔 + PROJECT_STATE.md**。
> 接著再看 `JOURNAL.md` 最後 3 筆條目。總讀取成本目標 < 5k tokens。

## 專題資訊

- **專題名**：module4
- **類型**：generic
- **起始**：2026-04-20 07:15
- **workflow 版本**：0.3.0

## 工作範圍（硬規則）

- **可修改**：本專案資料夾內所有檔案
- **唯讀參考**：`D:\p\workflow\`（skill 本體，不要改）
- **絕對禁止**：動 `D:\p\` 下其他專案的檔案

## Claude 必讀三件套

每次對話開場順序：

1. 本檔 `CLAUDE.md`（現在讀這個）
2. `PROJECT_STATE.md`（一頁入場券）
3. `JOURNAL.md` 最後 3 筆條目（grep `^## \[` 拿最新）

**禁止**：開場就掃整個專案資料夾。先讀這三件套，你會知道該看哪。

## 寫新代碼前的標準動作

1. **掃 `reference_code/`**：`ls reference_code/`，若非空讀 `_meta/sources.yaml`
2. 找到相關參考 → 只讀該檔，按 `usage` 欄位的約定處理（可 copy / 只看概念 / 不准 copy）
3. 寫的代碼**若借鑒參考**，在註解標：`# ref: reference_code/<file> L<start>-<end>`
4. **不要把 reference_code 的原文貼到新檔或對話裡** — 用路徑引用即可

## 關鍵決策必須記錄

以下事件**強制**追加到 `JOURNAL.md`（用 `log_experiment.py` 或手動按格式）：

- 架構決策（選用 A 不用 B，原因）
- 失敗與修正（錯誤訊息 + 根因 + 修法）
- 重要數字（檔案大小、資料列數、模型參數、實驗結果）
- 外部依賴（API key、特定版本、特殊環境）
- 踩坑（編碼、權限、相容性等非預期問題）

**不記**：臨時 TODO、git log 已有的資訊、每次對話的閒聊。

## PPT 素材邊做邊丟

每當產生以下東西，**同時 copy 到 `_ppt_workspace/artifacts/`**：

- 任何圖表 PNG
- 重要的 CSV 片段（< 100 行的 preview）
- 關鍵截圖
- AI 分析報告的摘錄

到 Present 階段 `harvest_to_ppt.py` 會自動把實驗記錄的決策 + 這裡的素材整理成 PPT 骨架。

## 模型策略（雙軸，關鍵度優先）

| 情境 | 模型 |
|---|---|
| Plan mode / 大型設計 / 專題初期 | **Opus 4.6** |
| 🔴 核心演算法 / API 合約 / 資料 schema（其他碼要照這個寫） | **Opus 4.6** |
| 🟡 衍生邏輯 / CRUD / glue / 照範本延伸 | **Sonnet 4.6** |
| 🟢 lint / rename / 搬檔 / typo | **Haiku 4.5** |
| 建構期 / 探索期（不在上述特例） | **Sonnet 4.6** |

**主動建議切換**：Claude 發現要寫核心介面 / schema / 錯誤處理策略 → 說「建議切 Opus」；發現是批次 mechanical refactor → 說「建議切 Haiku」。

細節見 `D:\p\workflow\references\model_switching_policy.md`。

## 預核准指令

`.claude/settings.local.json` 已經預核准常用無害指令（pip、pytest、git status/log、python scripts/*.py 等）。
若要加新的 auto-approve 項目，編輯該檔而不是每次 prompt 核准。

## 禁區

*（v0.2 init 時為空，使用者可後續補充）*

（v0.1 init 時為空，使用者可後續補：例如「不要動 step0_download 的結果、不要重跑 24 小時的實驗」等）

## 需要協助時

- 不確定下一步 → 讀 `PROJECT_STATE.md` 的 Next Actions
- 不確定用哪個 skill → 看 `D:\p\workflow\references\skill_composition.md`
- 專案要產 PPT → 跑 `python D:\p\workflow\scripts\build_ppt.py .`
- 要交接給下個 AI / 同事 → 跑 `python D:\p\workflow\scripts\snapshot_state.py .` 重產 PROJECT_STATE
