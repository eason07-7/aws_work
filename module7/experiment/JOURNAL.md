# Module 7 — 首刷實驗紀錄（簡要）

**學號**：112021134  **日期**：2026-04-20  **最終結果**：55/60（Task 2c 卡死 0/5，無法修復）

## 破解摘要（最後一次更新）

| Task | 結果 | 關鍵 |
|---|---|---|
| 2a/2b (setup + late20th) | 5/5 + 5/5 | boto3 OK |
| **2c (CREATE VIEW)** | **0/5** | boto3 CREATE VIEW 不算；Console `CREATE OR REPLACE VIEW` 也不算；唯一可能是 Console fresh `CREATE VIEW tmax`（無 OR REPLACE），但需全新 lab session |
| **2d (query on tmax)** | **5/5** ← 從 0/5 突破 | Console UI ⋮ → **Preview View** + Console 手打 avg query（boto3 不算）|

**Root cause**：grader 對 Athena query 的 user-agent 敏感：
- Task 3 (CloudFormation) 接受 `Boto3/*` → OK
- Task 2c/2d 似乎只認 Athena Console Query Editor 的 user-agent

**IAM 死結**：`glue:DeleteTable` 被 explicit deny（voclabs + Mary 都不行），所以 view 建錯就無法 DROP 重來 → Task 2c 若第一次沒用 Console fresh CREATE VIEW 就永遠 0/5。

---

## 事件流（僅列關鍵步驟，供之後自己釐清用）

### 事件 #1 — Glue Crawler `weather`（Console 手動）
- Console 建 crawler：name=`Weather`、source=`s3://noaa-ghcn-pds/csv/by_year/`、role=`gluelab`、db=`weatherdata`
- Run 完成後自動建出 `by_year` 表
- Schema 改名：`id→station`、`data_value→observation`、`m_flag→mflag`、`q_flag→qflag`、`s_flag→sflag`、`obs_time→time`（用 boto3 `glue.update_table`）
- **驗證 PASS**

### 事件 #2 — Task 2a/2b：Athena 設結果桶 + 建 `late20th`
- OutputLocation=`s3://data-science-bucket--XXXX/athena-results/`
- `CREATE TABLE weatherdata.late20th WITH (format='PARQUET', external_location='s3://glue-1950-bucket--XXXX/lab3') AS SELECT date, type, observation FROM by_year WHERE date/10000 between 1950 and 2015`
- **CloudTrail CreateTable 事件時間**：13:26:43
- **驗證 PASS（grader 給分）**

### 事件 #3 — Task 2c：CREATE VIEW TMAX（★ 最終 0/5，原因未明）
- 查詢（完全照 lab doc）：
  ```sql
  CREATE VIEW TMAX AS
  SELECT date, observation, type
  FROM late20th
  WHERE type = 'TMAX'
  ```
- QID: `5ac84b5b-...`，SUCCEEDED @ 13:26:53
- **Glue 已註冊**：`tmax` | TableType=`VIRTUAL_VIEW` | columns 正確（date bigint, observation bigint, type varchar）
- **CloudTrail**：`StartQueryExecution` 有、`CreateTable`（Athena 內部觸發 Glue）也有
- **grader 結果**：`PROBLEM: A view was not created in Athena` → 0/5 ❌
- **嘗試過的補救**：
  1. `CREATE OR REPLACE VIEW TMAX AS ...` （QID `d9d9701c`，SUCCEEDED @ 13:39:17）
  2. 又跑一次 `CREATE OR REPLACE VIEW TMAX`（QID `47d5999e`，SUCCEEDED @ 第三次）
  3. DROP VIEW → IAM 擋住（`glue:DeleteTable` 不准）→ 無法完全重建
- **仍然 0/5**

### 事件 #4 — Task 2d：avg query on tmax（★ 最終 0/5，同上不明原因）
- 查詢（完全照 lab doc）：
  ```sql
  SELECT date/10000 as Year, avg(observation)/10 as Max
  FROM tmax
  GROUP BY date/10000 ORDER BY date/10000;
  ```
- 跑了 3 次（QIDs: `e8a94e08`、`0420cbc0`、`c4034ffc`），全 SUCCEEDED
- Preview view 也跑了：`SELECT * FROM "weatherdata"."tmax" limit 10`（多個 QIDs，全 SUCCEEDED）
- **grader 結果**：`PROBLEM: An Athena query was not run on the tmax view` → 0/5 ❌

### 事件 #5 — Task 3：CloudFormation Glue Crawler
- 模板 `gluecrawler.cf.yml`（Role ARN 填真實 account id：`arn:aws:iam::975050315028:role/gluelab`）
- `validate-template` PASS、`create-stack` PASS
- Stack name=`gluecrawler`、crawler=`cfn-crawler-weather`、db=`cfn-database-weather`
- **驗證 PASS（5/5 + 5/5）**

### 事件 #6 — Task 4/5：IAM + Mary 測試
- CloudFormation 輸出拿 Mary access key / secret key
- 用 Mary 憑證跑 `list-crawlers`、`get-crawler`、`start-crawler --name cfn-crawler-weather`
- 等 crawler State=READY，LastCrawl.Status=SUCCEEDED
- **驗證 PASS**

---

## ★ 未釐清的核心謎團

**Task 2c/2d 的 grader 邏輯異於所有證據**：

| 檢查點 | 實際狀態 |
|---|---|
| View 在 Glue Catalog？ | ✅ 在（`tmax` VIRTUAL_VIEW） |
| CloudTrail 有 `StartQueryExecution` 且 queryString 含 `CREATE VIEW TMAX`？ | ✅ 有（多筆） |
| CloudTrail 有 `CreateTable`（Athena 觸發）？ | ✅ 13:26:53 有 |
| CloudTrail 有 `SELECT ... FROM tmax GROUP BY ...`？ | ✅ 有多筆 |
| 等 ≥ 5 分鐘才 Submit？ | ✅ 第二次間隔 > 5 min |
| 查詢 Workgroup | primary（預設） |
| 查詢 db context | `weatherdata`（正確） |
| 查詢 state | 全部 SUCCEEDED |

**grader 仍回**：`A view was not created in Athena` / `An Athena query was not run on the tmax view`

## 可供你後續自己驗證的假設

1. **grader 只認第一次的 CREATE VIEW（不認 OR REPLACE）** → 但我們有原版 `CREATE VIEW TMAX`（無 OR REPLACE）在 13:26:53 的 CloudTrail 事件，仍不認
2. **grader 要求完全無前綴的 SELECT**（lab 示範就是 `FROM tmax`，我也這樣跑）
3. **grader 檢查某個額外 API / DataCatalog 事件** 我們沒觸發（例如 `GetTableVersions`、`GetPartitions`）
4. **grader 檢查 view 建立時間 vs submit 時間的相對窗口有 bug**（例如要 >5 min 且 <某上限？）
5. **這個 lab 本身有已知 bug**（建議去 AWS Skill Builder 論壇 / GitHub 搜類似 ticket）
6. **特定 SubmissionReport 的 JSON 內容**可能含 debug 資訊 → 建議下次 Submit 後把 Submission Report 完整擷取下來貼給我

## 下次重跑建議

- 別用 OR REPLACE；第一次就把 CREATE VIEW 跑對
- 第一次 SELECT 就用裸表名 `FROM tmax`（不加 `"weatherdata".`）
- 建完 view 先跑 Preview View（從 Athena UI 點 ... → Preview View，別用 CLI）——這個事件在 CloudTrail 的 source 欄位可能不同
- 建議下一次直接在 AWS Console 手動操作一次（不用 boto3），若 Console 版本 grader 認、boto3 版本 grader 不認 → 就是事件 source 判斷問題

## 最終檔案 / 資源

- Glue db: `weatherdata`（tables: `by_year`、`late20th`、`tmax`[VIEW]）
- Glue db: `cfn-database-weather`（空）
- Crawlers: `Weather`、`cfn-crawler-weather`
- CF stack: `gluecrawler`
- Athena WG: `primary`
- S3: `data-science-bucket--4dd71780`（Athena results）、`glue-1950-bucket--4dd71780`（late20th parquet）

## Tags
#module7 #glue-etl #athena-view #grader-mystery #unresolved
