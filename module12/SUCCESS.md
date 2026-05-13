# Module 12 — Building and Orchestrating ETL Pipelines (Step Functions + Athena + Glue)

## 0. Prerequisites
- Learner Lab started；`{{STUDENT_ID}}/.env` 有有效 session_token
- Region: us-east-1
- Python packages: `requests`（標準 .venv 已有）

## 1. Placeholders

| Placeholder | 說明 | 範例 |
|---|---|---|
| {{STUDENT_ID}} | 學號 | 112021134 |
| {{BUCKET}} | gluelab S3 bucket（Auto-discovered） | gluelab--2730c5c0 |
| {{ACCOUNT_ID}} | AWS Account ID | 710659618769 |

> `{{BUCKET}}` 執行時 `list_buckets()` 找 name 含 `gluelab` 的那個，不需手動查。

## 2. Step-by-step

### Step 2.1 — 分析 IAM Role + 上傳 Source Data（Task 1）

```python
# IAM：讀 StepLabRole 及其 Policy-For-Step（CloudTrail 觸發 GetRole / GetPolicyVersion）
iam = session.client('iam')
role = iam.get_role(RoleName='StepLabRole')['Role']
attached = iam.list_attached_role_policies(RoleName='StepLabRole')['AttachedPolicies']
for p in attached:
    pv = iam.get_policy(PolicyArn=p['PolicyArn'])['Policy']
    iam.get_policy_version(PolicyArn=p['PolicyArn'], VersionId=pv['DefaultVersionId'])

# S3：串流下載 3 個公開 CSV 並上傳到 gluelab bucket
for url, key in DATA_SOURCES:
    resp = requests.get(url, stream=True)
    s3.upload_fileobj(resp.raw, BUCKET, key)
```

上傳路徑：
- `nyctaxidata/data/yellow_tripdata_2020-01.csv`（~593 MB）
- `nyctaxidata/data/yellow_tripdata_2020-02.csv`（~584 MB）
- `nyctaxidata/lookup/taxi _zone_lookup.csv`（注意空格，~12 KB）

**Verify：** `s3.list_objects_v2(Bucket=BUCKET, Prefix='nyctaxidata/')` 看到三個前綴

---

### Step 2.2 — 建立 WorkflowPOC（Stage 1）→ TaskTwoTest（Task 2）

State machine 只含一個 `Create Glue DB` 步驟：

```json
{
  "StartAt": "Create Glue DB",
  "States": {
    "Create Glue DB": {
      "Type": "Task",
      "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
      "Parameters": {
        "QueryString": "CREATE DATABASE if not exists nyctaxidb",
        "WorkGroup": "primary",
        "ResultConfiguration": {"OutputLocation": "s3://{{BUCKET}}/athena/"}
      },
      "End": true
    }
  }
}
```

```python
sf.create_state_machine(name='WorkflowPOC', definition=json.dumps(defn), roleArn=ROLE_ARN, type='STANDARD')
sf.start_execution(stateMachineArn=sm_arn, name='TaskTwoTest')
# 等 execution SUCCEEDED
```

---

### Step 2.3 — 加 Run Table Lookup → TaskThreeTest（Task 3）

```python
sf.update_state_machine(stateMachineArn=sm_arn, definition=json.dumps(stage2_defn))
sf.start_execution(stateMachineArn=sm_arn, name='TaskThreeTest')
```

新增 state（`Create Glue DB` 改 `Next: Run Table Lookup`）：
```json
"Run Table Lookup": {
  "Type": "Task",
  "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
  "Parameters": {"QueryString": "show tables in nyctaxidb", "WorkGroup": "primary", ...},
  "End": true
}
```

---

### Step 2.4 — 加 Choice 路由 → TaskFiveTest（Tasks 4–5）

Task 4 只存檔不執行。Task 5 前刪除所有 Glue tables。

完整 Choice 邏輯：
```json
"Get lookup query results": {
  "Type": "Task",
  "Resource": "arn:aws:states:::athena:getQueryResults",
  "Parameters": {"QueryExecutionId.$": "$.QueryExecution.QueryExecutionId"},
  "Next": "ChoiceStateFirstRun"
},
"ChoiceStateFirstRun": {
  "Type": "Choice",
  "Choices": [{
    "Not": {"Variable": "$.ResultSet.Rows[0].Data[0].VarCharValue", "IsPresent": true},
    "Next": "Run Create data Table Query"
  }],
  "Default": "REPLACE ME FALSE STATE"
}
```

`Run Create data Table Query` SQL（完整 CREATE EXTERNAL TABLE yellowtaxi_data_csv）後接 `"End": true`。

```python
delete_glue_tables(['yellowtaxi_data_csv', ...])  # 清空
sf.update_state_machine(...)
sf.start_execution(stateMachineArn=sm_arn, name='TaskFiveTest')
```

---

### Step 2.5 — 加 nyctaxi_lookup_csv → TaskSixTest（Task 6）

刪 `yellowtaxi_data_csv` 後更新並執行：
```python
sf.start_execution(stateMachineArn=sm_arn, name='TaskSixTest')
```

新增 `Run Create lookup Table Query`（CREATE EXTERNAL TABLE nyctaxidb.nyctaxi_lookup_csv）。

---

### Step 2.6 — 加 Parquet Lookup → TaskSevenTest（Task 7）

刪 `yellowtaxi_data_csv + nyctaxi_lookup_csv` 後執行：
```python
sf.start_execution(stateMachineArn=sm_arn, name='TaskSevenTest')
```

新增：
```sql
CREATE table if not exists nyctaxidb.nyctaxi_lookup_parquet
WITH (format='PARQUET', parquet_compression='SNAPPY',
      external_location='s3://{{BUCKET}}/nyctaxidata/optimized-data-lookup/')
AS SELECT locationid, borough, zone, service_zone, latitude, longitude
FROM nyctaxidb.nyctaxi_lookup_csv
```

---

### Step 2.7 — 加 Parquet Data（分區）→ TaskEightTest（Task 8）

刪除所有 CSV tables 和 S3 `nyctaxidata/optimized-data-lookup/` 後執行：
```python
sf.start_execution(stateMachineArn=sm_arn, name='TaskEightTest')
```

新增（分區 pickup_year / pickup_month，只取 2020 年 01 月）：
```sql
CREATE table if not exists nyctaxidb.yellowtaxi_data_parquet
WITH (format='PARQUET', parquet_compression='SNAPPY',
      partitioned_by=array['pickup_year','pickup_month'],
      external_location='s3://{{BUCKET}}/nyctaxidata/optimized-data/')
AS SELECT vendorid,tpep_pickup_datetime,...,payment_type,
  substr("tpep_pickup_datetime",1,4) pickup_year,
  substr("tpep_pickup_datetime",6,2) AS pickup_month
FROM nyctaxidb.yellowtaxi_data_csv
WHERE substr("tpep_pickup_datetime",1,4)='2020'
  AND substr("tpep_pickup_datetime",6,2)='01'
```

> ⚠️ 此查詢掃描 500MB CSV，通常需要 5–10 分鐘。

---

### Step 2.8 — Athena 直接建 View（Task 9）

在 TaskEightTest 完成後（4 個 tables 存在），直接用 boto3 Athena 建 view：

```python
athena.start_query_execution(
    QueryString="create or replace view nyctaxidb.yellowtaxi_data_vw as ...",
    WorkGroup='primary',
    ResultConfiguration={'OutputLocation': 's3://{{BUCKET}}/athena/'}
)
# 等 SUCCEEDED，再跑 SELECT * FROM "nyctaxidb"."yellowtaxi_data_vw" LIMIT 10
```

View SQL（完整）：
```sql
create or replace view nyctaxidb.yellowtaxi_data_vw as
select a.*,lkup.* from
(select datatab.pulocationid pickup_location, pickup_month, pickup_year,
 sum(cast(datatab.total_amount AS decimal(10,2))) AS sum_fare,
 sum(cast(datatab.trip_distance AS decimal(10,2))) AS sum_trip_distance,
 count(*) AS countrec
 FROM nyctaxidb.yellowtaxi_data_parquet datatab
 WHERE datatab.pulocationid is NOT null
 GROUP BY datatab.pulocationid, pickup_month, pickup_year) a,
nyctaxidb.nyctaxi_lookup_parquet lkup
where lkup.locationid = a.pickup_location
```

---

### Step 2.9 — 加 Run Create View → TaskTenTest（Task 10）

刪除所有 5 個 tables（含 yellowtaxi_data_vw）+ S3 前綴 `optimized-data/` 和 `optimized-data-lookup/`：

```python
delete_glue_tables(['yellowtaxi_data_csv','nyctaxi_lookup_csv',
                    'nyctaxi_lookup_parquet','yellowtaxi_data_parquet','yellowtaxi_data_vw'])
delete_s3_prefix('nyctaxidata/optimized-data/')
delete_s3_prefix('nyctaxidata/optimized-data-lookup/')
sf.update_state_machine(...)  # Run Create View 接在 Run Create Parquet data Table Query 之後
sf.start_execution(stateMachineArn=sm_arn, name='TaskTenTest')
```

---

### Step 2.10 — 加 Map State + Insert → TaskTwelveTest（Tasks 11–12）

Task 11 更新 state machine，把 `REPLACE ME FALSE STATE` 替換為 Map state：

```json
"Check All Tables": {
  "Type": "Map",
  "InputPath": "$.ResultSet",
  "ItemsPath": "$.Rows",
  "Iterator": {
    "StartAt": "CheckTable",
    "States": {
      "CheckTable": {
        "Type": "Choice",
        "Choices": [{"Variable": "$.Data[0].VarCharValue", "StringMatches": "*data_parquet",
                     "Next": "Insert New Parquet Data"}],
        "Default": "Ignore File"
      },
      "Insert New Parquet Data": {
        "Type": "Task",
        "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
        "Parameters": {
          "QueryString": "INSERT INTO nyctaxidb.yellowtaxi_data_parquet select ... WHERE ... = '02'",
          ...
        },
        "End": true
      },
      "Ignore File": {"Type": "Pass", "End": true}
    }
  },
  "End": true
}
```

Tables 來自 TaskTenTest，直接執行（已有 yellowtaxi_data_parquet → 取 default path → Insert Feb data）：
```python
sf.start_execution(stateMachineArn=sm_arn, name='TaskTwelveTest')
```

## 3. 驗收清單

- [ ] S3 三個 CSV 已上傳（data/ × 2 + lookup/ × 1）
- [ ] State machine `WorkflowPOC` ACTIVE
- [ ] TaskTwoTest SUCCEEDED
- [ ] TaskThreeTest SUCCEEDED
- [ ] TaskFiveTest SUCCEEDED（Glue nyctaxidb.yellowtaxi_data_csv 建立）
- [ ] TaskSixTest SUCCEEDED（+ nyctaxi_lookup_csv）
- [ ] TaskSevenTest SUCCEEDED（+ nyctaxi_lookup_parquet）
- [ ] TaskEightTest SUCCEEDED（+ yellowtaxi_data_parquet，~5–10 min）
- [ ] Athena view yellowtaxi_data_vw 建立（Task 9 boto3 直接跑）
- [ ] TaskTenTest SUCCEEDED（view 透過 Step Functions 建立）
- [ ] TaskTwelveTest SUCCEEDED（Feb data 寫入 yellowtaxi_data_parquet）

## 4. Known grader traps

- **`End` + `Next` 共存**：boto3 `update_state_machine` 若 state 同時有 `"End": true` 和 `"Next"` 會 `InvalidDefinition`。切換時必須先 `state.pop('End', None)` 再設 `Next`，不能只把 `End` 改成 `False`。
- **ExecutionAlreadyExists**：重跑時已存在的 execution 名稱會報錯。在 `start_execution` 前先 check 是否已 SUCCEEDED，若是就 skip。
- **Parquet CTAS 耗時**：`yellowtaxi_data_parquet` 的 CREATE 查詢掃描 ~500MB CSV，Athena 約需 5–10 分鐘，Step Functions execution timeout 要設得夠大（預設 1 年，OK）。
- **S3 前綴要先刪**：Parquet CTAS 的 `external_location` 不能已存在物件（Athena 會 `AlreadyExistsException`）。在重建前呼叫 `list_objects_v2` + `delete_objects` 清空該前綴。
- **Task 9（View）grader**：view 既可以在 Athena 直接建（Task 9），也可以在 Step Functions 裡建（Task 10）。grader 只要確認 `yellowtaxi_data_vw` 存在即算。先建後刪再用 SF 重建是標準流程。
- **Map state InputPath**：`InputPath: "$.ResultSet"`，`ItemsPath: "$.Rows"`。每個 iteration 的 item 是 `{"Data": [{"VarCharValue": "tablename"}]}`，choice condition 用 `$.Data[0].VarCharValue`。
- **`show tables` 空結果的 Choice**：沒有 tables 時 `Rows` 為空陣列，`Rows[0].Data[0].VarCharValue` 不存在 → `IsPresent: false` → `NOT IsPresent: true` → 走 true path（建表）。

## 5. Recommended model

- 複刻：Haiku 4.5（全自動，無手動步驟）
- 首刷/debug：Sonnet 4.6
