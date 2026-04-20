## LINE 聯絡

有興趣進一步交流，歡迎掃描下方 QR Code 加我 LINE：

<p align="left">
	<a href="https://line.me/ti/p/mJUnfzW_Pr" target="_blank" rel="noopener noreferrer">
		<img src="assets/line-qr.jpg" alt="LINE QR Code" width="220" />
	</a>
</p>

<p>
	<a href="https://line.me/ti/p/mJUnfzW_Pr" target="_blank" rel="noopener noreferrer">點我直接加 LINE 好友</a>
</p>

# AWS Learner Lab Module Guides

清晰的逐步執行指南，用於 AWS Learner Lab 作業。每個 module 包含成功路徑、陷阱提示與驗收清單。

## 快速開始

每個 module 資料夾包含：

| 檔案 | 用途 |
|---|---|
| `SUCCESS.md` | ⭐ **開始這裡** — 完整執行手冊（45/45 滿分） |
| `module*.md` | 原始作業需求（來自 AWS Training） |
| `*.cf.yml` | CloudFormation 模板 |
| `experiment/` | 首刷流水帳與 workflow 狀態（僅供參考） |

## Module 列表

### [Module 4 — Querying Data by Using Athena](module4/)

**分數** 45/45（完美）   
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

### [Module 7 — Glue ETL + Athena View + CloudFormation Crawler + IAM](module7/)

**分數** 55/60（Task 2c 的 5 分有結構性陷阱，見下）   
**重點技能**：
- Glue Crawler 爬 NOAA GHCN 公開資料集（`s3://noaa-ghcn-pds/csv/by_year/`）
- Glue `update_table` 重新命名欄位
- Athena CTAS 建 Parquet 外部表（`late20th`）
- Athena `CREATE VIEW` + `Preview View` UI 操作
- CloudFormation 部署 Glue Crawler + Database
- Mary IAM 使用者跨身份 `start_crawler` 測試

**🚨 關鍵陷阱（必讀 SUCCESS.md §3 + §5）**：
- Task 2c/2d 的 grader **對 user-agent 敏感** — boto3 路徑被判 0 分，必須由使用者在 Athena Console Query Editor 手動操作
- Task 2c 的 5 分結構性卡死：必須**第一次就在 Console 用 `CREATE VIEW tmax`**（不能 OR REPLACE，也不能先用 boto3），因為 `glue:DeleteTable` 被 IAM explicit deny，一旦錯了無法 DROP 重建
- 最現實的滿分是 55/60；要拚 60/60 需要全新 Lab session + 第一次就 Console-native

[👉 Module 7 完整指南](module7/SUCCESS.md)

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


## 專案結構

```
aws_module_guides/
├── README.md                    # 你在這裡
├── module4/
│   ├── SUCCESS.md              # ⭐ 開始這裡（學號無關）
│   ├── module4.md              # 原始作業需求
│   ├── athenaquery.cf.yml       # CloudFormation template
│   └── experiment/             # 首刷紀錄（JOURNAL + CHECKPOINT）
│       └── JOURNAL.md
├── module7/
│   ├── SUCCESS.md              # ⭐ 開始這裡（學號無關，含 Console 手動步驟）
│   ├── module7.md              # 原始作業需求
│   ├── gluecrawler.cf.yml      # CloudFormation template
│   └── experiment/
│       └── JOURNAL.md          # 首刷流水帳 + user-agent 陷阱診斷
```

---

## 聲明

- **成功紀錄**：Module 4 完成 45/45 滿分；Module 7 完成 55/60（Task 2c 的 5 分為 grader 結構性陷阱，見 module7/SUCCESS.md §5）
- 此倉庫屬於 [AWS Homework Workspace](https://github.com/eason07-7/aws_autowork) 的獨立模組指南子倉庫

---

**最後更新**：2026-04-21（Module 7 新增，55/60 + user-agent 陷阱記錄）
