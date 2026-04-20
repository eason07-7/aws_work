# AWS Learner Lab Module Guides

清晰的逐步執行指南，用於 AWS Learner Lab 作業的複刻和重現。每個 module 包含成功路徑、陷阱提示與驗收清單。

## 快速開始

每個 module 資料夾包含：

| 檔案 | 用途 |
|---|---|
| `SUCCESS.md` | ⭐ **開始這裡** — 學號無關的完整執行手冊（45/45 滿分） |
| `module*.md` | 原始作業需求（來自 AWS Training） |
| `*.cf.yml` | CloudFormation 模板 |
| `experiment/` | 首刷流水帳與 workflow 狀態（僅供參考） |

## Module 列表

### [Module 4 — Querying Data by Using Athena](module4/)

**成功率** 45/45（完美）  
**模型推薦** Haiku 4.5（複刻）、Sonnet 4.6（首刷）  
**耗時** ~90 分鐘  
**重點技能**：
- Athena 查詢 S3 CSV
- AWS Glue database + table schema
- Bucketizing & partitioning 優化查詢
- Athena views 簡化分析
- CloudFormation 部署 named query
- IAM 最小權限原則

**關鍵陷阱**：
- Task 1c Preview SQL 格式必須用 `SELECT * FROM "taxidata"."yellow" limit 10`（雙引號 + 小寫 limit）
- Task 4 View 查詢後 Submit 前要等 5 分鐘讓 CloudTrail 寫入

[👉 Module 4 完整指南](module4/SUCCESS.md)

---

## 使用方式

### 方式 A：按照 SUCCESS.md 逐步執行（推薦複刻）

1. 讀 `module4/SUCCESS.md` 的 Prerequisites
2. 準備 `.env`（AWS credentials）
3. 在 Prerequisites 中找到 Placeholders（`{{STUDENT_ID}}`、`{{BUCKET}}`）
4. 按 Step 3.1–3.9 逐步執行
5. Wait 5 min → Submit → 應得 45/45

### 方式 B：參考 JOURNAL.md（首刷學習）

如果你想理解每個步驟為什麼這樣做：
- 讀 `module4/experiment/JOURNAL.md`
- 看事件 #2–#8 的 現象/原因/處理/驗證
- 自己重新思考並實踐

---

## 推薦模型

| 情況 | 模型 | 理由 |
|---|---|---|
| 複刻 SUCCESS.md（已有完整指令） | **Haiku 4.5** | 無需推理，逐字執行 + 替換 placeholder |
| 首刷新 module（探索階段） | **Sonnet 4.6** | 理解需求、組合 CLI、除錯 |
| IAM/Lab 邊界 debug | **Opus 4.7** | 深度策略分析 |
| 本地部署 | **30B+ instruct** 如 Qwen2.5-32B-Coder | 穩定 tool-calling；7B-13B 不建議 |

---

## 專案結構

```
aws_module_guides/
├── README.md                    # 你在這裡
├── module4/
│   ├── SUCCESS.md              # ⭐ 開始這裡（學號無關）
│   ├── module4.md              # 原始作業需求
│   ├── athenaquery.cf.yml       # CloudFormation template
│   └── experiment/             # 首刷紀錄（JOURNAL + CHECKPOINT）
│       ├── JOURNAL.md
│       └── ...
```

---

## 聲明

- 所有指令與步驟已在 AWS Learner Lab 驗證（學號 112021014 & 112021134）
- **成功紀錄**：Module 4 完成 45/45 滿分
- 學號與個人憑證已從本倉庫排除（見 `.gitignore`）
- 此倉庫屬於 [AWS Homework Workspace](https://github.com/eason07-7/aws_autowork) 的獨立模組指南子倉庫

---

**最後更新**：2026-04-20（Module 4 满分完成）
