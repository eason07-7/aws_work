# Module 4 — Querying Data by Using Athena（手動 Console 指南）

> **這份指南完全不需要寫程式**，所有步驟在 AWS Management Console 點選完成。
> 適合想「照著點」完成作業的學生。
>
> 若你需要自動化版本，見 [`SUCCESS.md`](SUCCESS.md)（boto3 script 版）。
>
> 滿分記錄：**45/45**（2026-04-19）

---

## 0. 事前準備

1. 點 **Start Lab** → 等左上角出現**綠燈**
2. 點「**AWS**」進 AWS Management Console
3. 右上角確認 Region 是 **US East (N. Virginia) us-east-1**（如果不是就切換）
4. 在頂端搜尋列找 **S3** → 記下那個以 `ade-s3lab-bucket--` 開頭的桶名（你的 `{{BUCKET}}`，整份作業只有這一個桶）

---

## Task 1 — 建立 Database 和 yellow 外部表

### Task 1a — 建立 taxidata database（Athena 執行 DDL）

1. 頂端搜尋 **Athena** → 點進去
2. 左上如果看到「**Before you run your first query...**」提示，點 **View settings** → 填入 query result location：
   ```
   s3://ade-s3lab-bucket--XXXX/athena-results/
   ```
   （XXXX 換成你 Step 0 記下的尾碼）→ 點 **Save**
3. 點左側 **Query editor**
4. 在 editor 框貼入：
   ```sql
   CREATE DATABASE taxidata;
   ```
5. 點 **Run**（或 Ctrl+Enter）
6. 下方 **Query results** 顯示 `Query successful` → ✅

**Verify**：左側 **Database** 下拉列表出現 `taxidata`

---

### Task 1b — 建立 yellow 外部表

1. 確認左側 **Database** 已選 `taxidata`
2. 點 **+** 開一個新 query tab，貼入：
   ```sql
   CREATE EXTERNAL TABLE IF NOT EXISTS taxidata.yellow (
       `vendor` string, `pickup` timestamp, `dropoff` timestamp,
       `count` int, `distance` int, `ratecode` string, `storeflag` string,
       `pulocid` string, `dolocid` string, `paytype` string,
       `fare` decimal, `extra` decimal, `mta_tax` decimal,
       `tip` decimal, `tolls` decimal, `surcharge` decimal, `total` decimal
     )
     ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
     WITH SERDEPROPERTIES ('serialization.format' = ',', 'field.delim' = ',')
     LOCATION 's3://aws-tc-largeobjects/CUR-TF-200-ACDSCI-1/Lab2/yellow/'
     TBLPROPERTIES ('has_encrypted_data'='false');
   ```
3. 點 **Run**
4. `Query successful` → ✅

**Verify**：左側 **Tables** 欄位出現 `yellow`（17 欄）

---

### Task 1c — Preview yellow table ⚠️ SQL 格式非常重要

> **Grader 陷阱**：這個 query 的格式必須**完全符合**，grader 在 CloudTrail 做 exact-match。

1. 點 **+** 開新 query tab
2. 貼入**完全這段**（不要改大小寫、不要改引號）：
   ```sql
   SELECT * FROM "taxidata"."yellow" limit 10
   ```
   注意：
   - `FROM` 後面是**雙引號** `"taxidata"."yellow"`，不是反引號
   - `limit` 是**小寫**
   - **結尾沒有分號**
3. 點 **Run**
4. 下方出現 10 行資料 → ✅

**截圖建議**：截這個 query results 畫面存進 `<學號>/submissions/module4/task1c.png`

---

## Task 2 — 建立 jan 表格（Bucketizing）

1. 點 **+** 開新 query tab，貼入：
   ```sql
   CREATE EXTERNAL TABLE IF NOT EXISTS jan (
     `vendor` string, `pickup` timestamp, `dropoff` timestamp,
     `count` int, `distance` int, `ratecode` string, `storeflag` string,
     `pulocid` string, `dolocid` string, `paytype` string,
     `fare` decimal, `extra` decimal, `mta_tax` decimal,
     `tip` decimal, `tolls` decimal, `surcharge` decimal, `total` decimal
     )
     ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
     WITH SERDEPROPERTIES ('serialization.format' = ',', 'field.delim' = ',')
     LOCATION 's3://aws-tc-largeobjects/CUR-TF-200-ACDSCI-1/Lab2/January2017/'
     TBLPROPERTIES ('has_encrypted_data'='false');
   ```
2. 點 **Run** → `Query successful` → ✅

**Verify**：左側 **Tables** 出現 `jan`

**（可選）比較效果**：分別對 `yellow`（加 WHERE 篩 1 月）和 `jan` 跑 count query，你會看到 `jan` 掃描的資料量（右下角 Data scanned）遠小於 `yellow`，這就是 bucketizing 的好處。

---

## Task 3 — 建立 creditcard Parquet 表（CTAS）

> CTAS = Create Table As Select，把查詢結果直接存成新表並轉成 Parquet 格式。
> 這個 query 需要 **~12–30 秒**，請耐心等待。

1. 點 **+** 開新 query tab，貼入：
   ```sql
   CREATE TABLE taxidata.creditcard
   WITH (format = 'PARQUET') AS
   SELECT * from "yellow" WHERE paytype = '1'
   ```
2. 點 **Run**，等進度條跑完（State 變 SUCCEEDED）→ ✅

**Verify**：左側 **Tables** 出現 `creditcard`，type 是 PARQUET

**（可選）比較效果**：對 `creditcard` 和 `yellow`（加 WHERE paytype='1'）各跑一次 `SELECT sum(total)`，creditcard 掃描量約 0.08 GB vs yellow 約 10 GB。

---

## Task 4 — 建立 Views 並查詢 ⚠️ Submit 前等 5 分鐘

> Grader 需要看到：(1) VIEW 建立事件 + (2) SELECT 查詢事件，兩者都在 CloudTrail 內。
> **Submit 前等至少 5 分鐘**，讓 CloudTrail 有時間寫入。

### 4.1 建立 cctrips view

1. 點 **+** 開新 query tab，確認 Database 是 `taxidata`，貼入：
   ```sql
   CREATE VIEW cctrips AS SELECT "sum"("fare") "CreditCardFares" FROM yellow WHERE ("paytype"='1')
   ```
2. 點 **Run** → `Query successful` → ✅

### 4.2 建立 cashtrips view

1. 點 **+** 開新 query tab，貼入：
   ```sql
   CREATE VIEW cashtrips AS SELECT "sum"("fare") "CashFares" FROM yellow WHERE ("paytype"='2')
   ```
2. 點 **Run** → ✅

### 4.3 建立 comparepay view

1. 點 **+** 開新 query tab，貼入：
   ```sql
   CREATE VIEW comparepay AS
   WITH
     cc AS (SELECT sum(fare) AS cctotal, vendor FROM yellow WHERE paytype='1' GROUP BY paytype, vendor),
     cs AS (SELECT sum(fare) AS cashtotal, vendor, paytype FROM yellow WHERE paytype='2' GROUP BY paytype, vendor)
   SELECT cc.cctotal, cs.cashtotal FROM cc JOIN cs ON cc.vendor = cs.vendor
   ```
2. 點 **Run** → ✅

### 4.4 查詢所有三個 views（必做！）

> **這步非常關鍵**：grader 需要看到 SELECT 查詢的 CloudTrail 事件。

對每個 view，各開新 tab 跑一次 SELECT（**用裸名，不加 schema 前綴**）：

```sql
Select * from cctrips
```
```sql
Select * from cashtrips
```
```sql
Select * from comparepay
```

三個都跑出結果 → ✅

**Verify**：
- `cctrips` 結果：CreditCardFares 約 `1044600010`
- `cashtrips` 結果：CashFares 約 `450031761`
- `comparepay` 結果：兩行，每行兩欄（cctotal, cashtotal）

**等 5 分鐘後再 Submit！**（不要立刻點 Submit）

---

## Task 5 — CloudFormation Template 部署 Named Query

> 這個任務要在 CloudFormation 部署一個 Named Query，讓 Athena 的 Saved queries 裡出現 `FaresOver100DollarsUS`。

### 5a — 先在 Athena 手動跑一次 example query（必做）

1. 點 **+** 開新 query tab，貼入：
   ```sql
   SELECT distance, paytype, fare, tip, tolls, surcharge, total
   FROM yellow
   WHERE total >= 100.0
   ORDER BY total DESC
   ```
2. 點 **Run** → 等結果出現 → ✅

### 5b — 在 CloudFormation 部署 Named Query

1. 頂端搜尋 **CloudFormation** → 點進去
2. 點右上 **Create stack** → **With new resources (standard)**
3. **Specify template** → 選 **Upload a template file**
4. 從 [`athenaquery.cf.yml`](athenaquery.cf.yml) 下載（或在右側複製以下 YAML 存成 `.yml` 檔）：

   ```yaml
   AWSTemplateFormatVersion: 2010-09-09
   Resources:
     AthenaNamedQuery:
       Type: AWS::Athena::NamedQuery
       Properties:
         Database: "taxidata"
         Description: "A query that selects all fares over $100.00 (US)"
         Name: "FaresOver100DollarsUS"
         QueryString: >
                       SELECT distance, paytype, fare, tip, tolls, surcharge, total
                       FROM yellow
                       WHERE total >= 100.0
                       ORDER BY total DESC
   Outputs:
     AthenaNamedQuery:
       Value: !Ref AthenaNamedQuery
   ```

5. 上傳後點 **Next**
6. **Stack name** 填 `athenaquery` → **Next** → **Next** → **Submit**
7. 等 Status 變 **CREATE_COMPLETE** → ✅

**Verify**：
- CloudFormation stack `athenaquery` = CREATE_COMPLETE
- 回 Athena → **Saved queries** → 看到 `FaresOver100DollarsUS`

---

## Task 6 — 檢視 IAM Policy（僅查看，無 grader 評分）

1. 頂端搜尋 **IAM** → 點進去
2. 左側 **Users** → 點 **mary**
3. **Permissions** 頁籤 → 展開 `Policy-For-Data-Scientists`
4. 確認 policy 允許：S3 讀寫、Glue 操作、Athena query、CloudFormation create stack、CloudShell

> 這個 task 只需要查看，沒有 grader 評分項目。

---

## Task 7 — 用 Mary 的 Credentials 測試（Athena Get Named Query）

Mary 是 Lab 預建的 IAM user，已有 Athena 查詢的 Policy。grader 會確認有 `IAMUser/mary` 發出 `GetNamedQuery` 的 CloudTrail 事件。

> **推薦方式**：用 Athena Console 的 CloudShell 或讓執行腳本幫你測試。
>
> 若你不想寫程式，可以在 Console 右上角點 **CloudShell**（`>_` 圖示），然後輸入：
>
> ```bash
> # 先確認有 Named Query
> aws athena list-named-queries --region us-east-1
> # 拿到 NamedQueryId 後替換下面的 ID
> aws athena get-named-query --named-query-id <NamedQueryId> --region us-east-1
> ```
>
> 不過 CloudShell 跑的是 LabRole，不是 Mary 本人。若要真的測 Mary，需要先拿到她的 Access Key（在 Lab 的 CloudFormation 主 stack outputs 裡）。
>
> **最簡做法**：讓執行腳本（`module4_execute.py`）的 Step 3.10 幫你跑，它已經自動從 CloudFormation 取得 Mary 的 credentials 並測試。

---

## 驗收清單（Submit 前勾一遍）

- [ ] Glue DB `taxidata` 存在（Athena 左側下拉可見）
- [ ] Tables `yellow`（17 欄）、`jan`、`creditcard` 存在
- [ ] Task 1c preview query 用了正確格式（雙引號 + 小寫 limit）
- [ ] Views `cctrips`、`cashtrips`、`comparepay` 都建立且各跑過一次 SELECT
- [ ] CloudFormation stack `athenaquery` = CREATE_COMPLETE
- [ ] Named query `FaresOver100DollarsUS` 在 Athena Saved queries 出現
- [ ] 已等 **至少 5 分鐘** 再按 Submit

**預期分數：45/45**

---

## 常見陷阱提醒

| 症狀 | 原因 | 解法 |
|---|---|---|
| Task 1c 0/5 | SQL 格式不對（LIMIT 大寫 or 無雙引號） | 重跑 `SELECT * FROM "taxidata"."yellow" limit 10`（完全照抄） |
| Task 4 0/5 | 建了 view 但沒 SELECT，或 comparepay 用了 schema prefix | 補跑三個裸名 SELECT；Submit 前等 5 分鐘 |
| 上傳 CF template 後 error | YAML 格式問題 | 直接從本 repo 下載 `athenaquery.cf.yml` |
| Task 7 0/5 | Mary 的 GetNamedQuery 未被 CloudTrail 記到 | 用 `module4_execute.py` 跑或在 CloudShell 用 Mary credentials 再呼叫一次 |

---

## 需要 CLI / Script 版？

見 [`SUCCESS.md`](SUCCESS.md)（boto3 自動化版，可讓 AI 代跑）。
