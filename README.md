## AWS Academy Data Engineering [154382] 
EE300016 [A] 大數據資料處理(大三)
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

**分數** 45/45  
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

### [Module 8 — Storing and Analyzing Data by Using Amazon Redshift](module8/)

**分數** 滿分  
**重點技能**：
- Redshift Cluster 建立（ra3.large x2）+ Security Group（port 5439）
- Redshift Data API 建表（users, date, sales）
- COPY 指令從 S3 載入資料（tab/pipe 分隔，跨帳號 us-west-2）
- SQL 查詢：sum/join/group by/order by/limit
- Redshift Data API 程式化查詢（模擬 AWS CLI）
- Mary IAM 使用者跨身份 `execute_statement` + `get_statement_result` 測試

**關鍵陷阱**：
- COPY 指令的 S3 source 在 `us-west-2`，必須明確指定 `region 'us-west-2'`
- Cluster 建立約需 5-8 分鐘，需輪詢等待 `ClusterStatus=available`
- `MyRedshiftRole` ARN 每個帳號不同，執行前要動態取得

[👉 Module 8 完整指南](module8/SUCCESS.md)

---

### [Module 9 — Updating Dynamic Data in Place (Hudi + Glue + Kinesis)](module9/)

**分數** 30/30 滿分  
**重點技能**：
- AWS Glue Streaming Job（native Apache Hudi `--datalake-formats hudi`）
- Apache Hudi COPY_ON_WRITE upsert + schema evolution（`new_column` 自動擴展）
- Amazon Kinesis Data Streams 資料攝取
- Cognito Identity Pool federated credentials（SRP 認證 → 取 Kinesis 寫入權限）
- Athena 查詢 Hudi table（schema 自動跟隨）

**關鍵陷阱**：
- Task 4（KDG）grader 用 CloudTrail 檢查**瀏覽器**發出的 Cognito API 呼叫，boto3 PutRecord 不計分——必須真實瀏覽器登入 KDG，點 Send Data（🖐 唯一手動步驟）
- 原始 `glue_job_script.py` 有 Spark 3.x Bug（`commonConfig` 重複帶 `path`），不修則 Glue job 每次 FAILED，見 SUCCESS.md §3.2
- Learner Lab IAM 無 `kinesis:PutRecord`，Tasks 6/7 必須走 Cognito Identity Pool

[👉 Module 9 完整指南](module9/SUCCESS.md)

---

### [Module 9_1 — Processing Logs by Using Amazon EMR](module9_1/)

**分數** 滿分  
**重點技能**：
- Amazon EMR 建立（emr-5.29.0, Hadoop 2.8.5 + Hive 2.3.6, m4.large × 3）
- Apache Hive 外部表（impressions + clicks）MSCK REPAIR PARTITION
- Hive MapReduce INSERT：tmp_impressions / tmp_clicks → joined_impressions LEFT OUTER JOIN
- paramiko SSH 程式化執行 Hive（`hive -f HQL`）
- Hive 查詢結果輸出 `result.txt`（`hive -e "..." > /home/hadoop/result.txt`）

**關鍵陷阱**：
- `elasticmapreduce:AddTags` / `AddJobFlowSteps` / `ssm:SendCommand` 均 AccessDenied — 用 `RunJobFlow`（無 Steps）保持 WAITING，再走 paramiko SSH
- grader 檢查 `sg_configured`（TCP 22 Anywhere-IPv4）和 `pub_ip_set`（master public DNS）— 建 cluster 前先確認 subnet 是 public subnet，並對 master SG 加 SSH 規則
- `run_job_flow` 不能帶 `Tags` 參數（IAM explicit deny）

[👉 Module 9_1 完整指南](module9_1/SUCCESS.md)

---

## 使用方式

### 方式 A：按照 SUCCESS.md 逐步執行（推薦複刻）

1. 讀 `module4/SUCCESS.md` 的 Prerequisites
2. 在 Prerequisites 中找到 Placeholders（`{{STUDENT_ID}}`、`{{BUCKET}}`）
3. 按 Step 3.1–3.9 逐步執行
4. Wait 5 min → Submit → 應得 45/45

### 方式 B：參考 JOURNAL.md（首刷學習）

如果你想理解每個步驟為什麼這樣做：
- 讀 `module4/experiment/JOURNAL.md`
- 看事件 #2–#8 的 現象/原因/處理/驗證
- 自己重新思考並實踐

---


## 結構

```
aws_module_guides/
├── README.md                    # 你在這裡
├── module4/
│   ├── SUCCESS.md              # ⭐ 開始這裡（學號無關）
│   ├── module4.md              # 原始作業需求
│   ├── athenaquery.cf.yml       # CloudFormation template
│   └── experiment/
│       └── JOURNAL.md
├── module7/
│   ├── SUCCESS.md              # ⭐ 開始這裡（含 Console 手動步驟，55/60）
│   ├── module7.md              # 原始作業需求
│   ├── gluecrawler.cf.yml      # CloudFormation template
│   └── experiment/
│       └── JOURNAL.md
├── module8/
│   ├── SUCCESS.md              # ⭐ 開始這裡（全自動化，滿分）
│   ├── module8.md              # 原始作業需求
│   └── experiment/
│       └── JOURNAL.md
├── module9/
│   ├── SUCCESS.md              # ⭐ 開始這裡（Task 4 手動 KDG，其餘全自動，30/30）
│   ├── module9.md              # 原始作業需求
│   └── experiment/
│       └── JOURNAL.md
├── module9_1/
│   ├── SUCCESS.md              # ⭐ 開始這裡（全自動 paramiko SSH，滿分）
│   ├── module9_1.md            # 原始作業需求
│   └── experiment/
│       └── JOURNAL.md
```

---

## 聲明

- **成功紀錄**：Module 4 完成 45/45 滿分；Module 7 完成 55/60（Task 2c 的 5 分為 grader 結構性陷阱，見 module7/SUCCESS.md §5）；Module 8 完成滿分（全自動化）；Module 9 完成 30/30 滿分（Task 4 需一次手動 KDG，其餘全自動）；Module 9_1 完成滿分（全自動化 paramiko SSH）
- 此倉庫屬於 [AWS Homework Workspace](https://github.com/eason07-7/aws_autowork)自動腳本跑雲上實作的獨立模組指南子倉庫

---

**最後更新**：2026-04-30（Module 9_1 新增，滿分）
