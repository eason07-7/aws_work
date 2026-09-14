# Module 4 — Querying Data by Using Athena

> **學號無關的純執行手冊。** 任何 AI 拿到這份檔 + 目標學號的 `.env`，即可完成作業。
> 首刷由 Sonnet 4.6 完成，後續複刻用 **Haiku 4.5** 或本地 30B+ 即可。
> 滿分紀錄：45/45（2026-04-19，學號 112021134）

---

## 0. Prerequisites

- [ ] AWS Learner Lab 已按下 Start Lab、顯示綠燈
- [ ] `{{STUDENT_ID}}/.env` 的 `aws_session_token` 尚未過期
- [ ] 驗證：`python -c "import boto3,os; [os.environ.update({k.strip():v.strip()}) for l in open(r'{{STUDENT_ID}}/.env') if '=' in l for k,v in [l.strip().split('=',1)]]; print(boto3.client('sts',region_name='us-east-1').get_caller_identity()['Arn'])"`
- [ ] Python 環境有 boto3（`pip install boto3` 若沒有）
- [ ] Region：`us-east-1`

---

## 1. Placeholders（執行前替換）

| Placeholder | 說明 | 範例 |
|---|---|---|
| `{{STUDENT_ID}}` | 學號（資料夾名） | `112021134` |
| `{{BUCKET}}` | lab 帳號唯一的 S3 bucket（查法見下） | `ade-s3lab-bucket--a9cb78d0` |

**找 BUCKET 的方法**（在 Python 載入 .env 後執行）：
```python
import boto3
s3 = boto3.client('s3', region_name='us-east-1')
print([b['Name'] for b in s3.list_buckets()['Buckets']])
# → 只有一個 bucket，就是 {{BUCKET}}
```

---

## 2. 環境準備（每個 Python 腳本開頭都要貼）

```python
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

env_path = r"D:\p\awshomework\{{STUDENT_ID}}\.env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

import boto3
BUCKET = '{{BUCKET}}'   # 替換成此帳號的 S3 bucket
REGION = 'us-east-1'
athena = boto3.client('athena', region_name=REGION)
glue   = boto3.client('glue',   region_name=REGION)
cf     = boto3.client('cloudformation', region_name=REGION)

def run_query(sql, database=None, timeout=180):
    kwargs = {
        'QueryString': sql,
        'ResultConfiguration': {'OutputLocation': f's3://{BUCKET}/athena-results/'},
    }
    if database:
        kwargs['QueryExecutionContext'] = {'Database': database}
    resp = athena.start_query_execution(**kwargs)
    qid = resp['QueryExecutionId']
    elapsed = 0
    while elapsed < timeout:
        r = athena.get_query_execution(QueryExecutionId=qid)
        state = r['QueryExecution']['Status']['State']
        if state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
            break
        time.sleep(3); elapsed += 3
    stats = r['QueryExecution'].get('Statistics', {})
    if state != 'SUCCEEDED':
        raise Exception(f"Query {state}: {r['QueryExecution']['Status'].get('StateChangeReason','')}")
    return qid, stats
```

---

## 3. Step-by-step 執行步驟

### Step 3.1 — [Task 1a] 建立 taxidata Glue Database

```python
run_query("CREATE DATABASE taxidata;")
```

**Expected:** Query SUCCEEDED（無 output）

**Verify:** `glue.get_database(Name='taxidata')` 回傳 JSON 含 `"Name": "taxidata"`

**If fails:** `AlreadyExistsException` → 無視，已存在即可

---

### Step 3.2 — [Task 1b] 建立 yellow 外部表格

```python
run_query("""
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
""", database='taxidata')
```

**Expected:** Query SUCCEEDED

**Verify:** `glue.get_table(DatabaseName='taxidata', Name='yellow')` 存在

**If fails:** `AlreadyExistsException` → IF NOT EXISTS 已保護，不會發生

---

### Step 3.3 — [Task 1c] Preview yellow table ⚠️ 格式關鍵

```python
# ⚠️ 必須用雙引號包覆、小寫 limit — grader 在 CloudTrail 比對這個格式
qid, _ = run_query('SELECT * FROM "taxidata"."yellow" limit 10', database='taxidata')
results = athena.get_query_results(QueryExecutionId=qid)
print(f"Rows: {len(results['ResultSet']['Rows'])-1}")  # 預期 10
```

**Expected:** 回傳 10 rows

**⚠️ Grader 陷阱：** 若用 `SELECT * FROM taxidata.yellow LIMIT 10`（無雙引號、大寫 LIMIT）CloudTrail 事件不符合 grader pattern → **0/5**

**Verify:** 回傳 10 rows，第一欄 `vendor` 值為 "1" 或 "2"

---

### Step 3.4 — [Task 2] 建立 jan 表格 + 驗證 bucketizing 效果

```python
run_query("""
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
""", database='taxidata')

# 比較查詢（可選，驗收用）
qid, stats = run_query("""
SELECT count(count) AS "Number of trips", sum(total) AS "Total fares", pickup AS "Trip date"
FROM yellow WHERE pickup between TIMESTAMP '2017-01-01 00:00:00' and TIMESTAMP '2017-02-01 00:00:01'
GROUP BY pickup
""", database='taxidata')
print(f"yellow Jan: {stats['TotalExecutionTimeInMillis']/1000:.2f}s, {stats['DataScannedInBytes']/1e9:.2f} GB")

qid, stats = run_query("""
SELECT count(count) AS "Number of trips", sum(total) AS "Total fares", pickup AS "Trip date"
FROM jan GROUP BY pickup
""", database='taxidata')
print(f"jan bucket: {stats['TotalExecutionTimeInMillis']/1000:.2f}s, {stats['DataScannedInBytes']/1e9:.2f} GB")
```

**Expected:** jan bucket 掃描量遠小於 yellow（約 0.85 GB vs 10 GB）

**Verify:** `glue.get_table(DatabaseName='taxidata', Name='jan')` 存在，第一欄名稱 `vendor`

---

### Step 3.5 — [Task 3] 建立 creditcard Parquet 分區表

```python
# ⚠️ 需要 ~12 秒，會掃描 10 GB 轉換為 Parquet 存入 {{BUCKET}}
run_query("""
CREATE TABLE taxidata.creditcard
WITH (format = 'PARQUET') AS
SELECT * from "yellow" WHERE paytype = '1'
""", database='taxidata', timeout=180)

# 驗證效果
qid, stats = run_query("SELECT sum(total), paytype FROM yellow WHERE paytype='1' GROUP BY paytype", database='taxidata')
print(f"yellow: {stats['DataScannedInBytes']/1e9:.2f} GB")

qid, stats = run_query("SELECT sum(total), paytype FROM creditcard WHERE paytype='1' GROUP BY paytype", database='taxidata')
print(f"creditcard Parquet: {stats['DataScannedInBytes']/1e9:.2f} GB")
```

**Expected:** creditcard 約 0.08 GB（vs yellow 10 GB），sum(total) 兩者相同 = `1351232654`

**If fails:** `AlreadyExistsException` → 表示之前已建立，用 `glue.get_table(DatabaseName='taxidata',Name='creditcard')` 確認

---

### Step 3.6 — [Task 4] 建立 views + 執行查詢 ⚠️ 需等 5 分鐘再 submit

```python
# 建立 3 個 views
run_query("CREATE VIEW cctrips AS SELECT \"sum\"(\"fare\") \"CreditCardFares\" FROM yellow WHERE (\"paytype\"='1')", database='taxidata')
run_query("CREATE VIEW cashtrips AS SELECT \"sum\"(\"fare\") \"CashFares\" FROM yellow WHERE (\"paytype\"='2')", database='taxidata')
run_query("""
CREATE VIEW comparepay AS
WITH
  cc AS (SELECT sum(fare) AS cctotal, vendor FROM yellow WHERE paytype='1' GROUP BY paytype, vendor),
  cs AS (SELECT sum(fare) AS cashtotal, vendor, paytype FROM yellow WHERE paytype='2' GROUP BY paytype, vendor)
SELECT cc.cctotal, cs.cashtotal FROM cc JOIN cs ON cc.vendor = cs.vendor
""", database='taxidata')

# 查詢所有 views（grader 需要這些 CloudTrail 事件）
qid, _ = run_query("Select * from cctrips", database='taxidata')
r = athena.get_query_results(QueryExecutionId=qid)
print("CreditCardFares:", r['ResultSet']['Rows'][1]['Data'][0]['VarCharValue'])  # 1044600010

qid, _ = run_query("Select * from cashtrips", database='taxidata')
r = athena.get_query_results(QueryExecutionId=qid)
print("CashFares:", r['ResultSet']['Rows'][1]['Data'][0]['VarCharValue'])  # 450031761

qid, _ = run_query('SELECT * FROM "taxidata"."comparepay" limit 10', database='taxidata')
r = athena.get_query_results(QueryExecutionId=qid)
for row in r['ResultSet']['Rows']:
    print([c.get('VarCharValue','') for c in row['Data']])
# 預期: ['cctotal','cashtotal'], ['584502884','250849783'], ['460097126','199181978']
```

**⚠️ Grader 陷阱：** View 建立後直接 Submit 可能得 0 分。需要 SELECT 查詢的 CloudTrail 事件，且 **Submit 前等至少 5 分鐘**。

**If fails** (view already exists): 加 `OR REPLACE`：`CREATE OR REPLACE VIEW cctrips AS ...`

---

### Step 3.7 — [Task 5] CloudFormation template → named query

```python
import os

CF_TEMPLATE = '''AWSTemplateFormatVersion: 2010-09-09
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
'''

# 先跑 example query（Task 5a）
run_query(
    "SELECT distance, paytype, fare, tip, tolls, surcharge, total FROM yellow WHERE total >= 100.0 ORDER BY total DESC",
    database='taxidata'
)

# 驗證 template
validate_resp = cf.validate_template(TemplateBody=CF_TEMPLATE)
print("Template valid, Parameters:", validate_resp.get('Parameters', []))

# 建立 stack
stack_resp = cf.create_stack(StackName='athenaquery', TemplateBody=CF_TEMPLATE)
print("StackId:", stack_resp['StackId'])

# 等待 CREATE_COMPLETE
for _ in range(30):
    time.sleep(3)
    stack = cf.describe_stacks(StackName='athenaquery')['Stacks'][0]
    if stack['StackStatus'] in ('CREATE_COMPLETE', 'ROLLBACK_COMPLETE', 'CREATE_FAILED'):
        break
print("Stack status:", stack['StackStatus'])  # 預期 CREATE_COMPLETE

# 確認 named query
nq_ids = athena.list_named_queries()['NamedQueryIds']
print("Named query IDs:", nq_ids)
NQ_ID = nq_ids[0]
nq = athena.get_named_query(NamedQueryId=NQ_ID)['NamedQuery']
print(f"Name: {nq['Name']}, Database: {nq['Database']}")
```

**Expected:**
- Stack status: `CREATE_COMPLETE`
- Named query `FaresOver100DollarsUS` 存在於 `primary` workgroup

**If fails** (AlreadyExistsException on stack): `cf.describe_stacks(StackName='athenaquery')` 確認已存在即可

---

### Step 3.8 — [Task 6] 查看 IAM Policy（Console 操作，無 API 動作）

IAM Console → Users → mary → Permissions → Policy-For-Data-Scientists。

Policy 允許：S3 讀寫（不含建桶）、Glue DB/Table 建立、Athena query、CloudFormation create stack、CloudShell。

**此 task 無 grader 評分項目。**

---

### Step 3.9 — [Task 7] 用 mary 的 credentials 測試 get-named-query

```python
# 從 main lab stack 取 mary 的 credentials
stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])['StackSummaries']
stacks.sort(key=lambda x: x['CreationTime'])
marys_ak = marys_sak = None
for s in stacks:
    if s['StackName'] == 'athenaquery':
        continue
    detail = cf.describe_stacks(StackName=s['StackName'])['Stacks'][0]
    outputs = {o['OutputKey']: o['OutputValue'] for o in detail.get('Outputs', [])}
    if 'MarysAccessKey' in outputs:
        marys_ak = outputs['MarysAccessKey']
        marys_sak = outputs['MarysSecretAccessKey']
        print(f"Found in stack: {s['StackName']}")
        break

# 用 mary 的 credentials 呼叫
athena_mary = boto3.client('athena', region_name=REGION,
                            aws_access_key_id=marys_ak,
                            aws_secret_access_key=marys_sak)
result = athena_mary.get_named_query(NamedQueryId=NQ_ID)
print("Mary CAN access:", result['NamedQuery']['Name'])
# 預期: FaresOver100DollarsUS
```

**Expected:** Mary 成功取回 `FaresOver100DollarsUS` 詳細資料

**Verify:** grader Task7 成功條件 = CloudTrail 有 `IAMUser/mary` 的 `GetNamedQuery` 事件

---

## 4. 驗收清單

- [ ] Glue DB `taxidata` 存在
- [ ] Glue Table `taxidata.yellow` 存在（17 欄，vendor/pickup/... 順序）
- [ ] Preview query `SELECT * FROM "taxidata"."yellow" limit 10` 執行成功（雙引號格式）
- [ ] Glue Table `taxidata.jan` 存在（第一欄名稱 `vendor`）
- [ ] Glue Table `taxidata.creditcard` 存在（Parquet 格式）
- [ ] Views `cctrips`, `cashtrips`, `comparepay` 存在且已被 SELECT 查詢
- [ ] comparepay 結果：`[584502884, 250849783]` 和 `[460097126, 199181978]`
- [ ] CloudFormation stack `athenaquery` 狀態 CREATE_COMPLETE
- [ ] Named query `FaresOver100DollarsUS` 存在，NamedQueryId 記下備用
- [ ] mary 以自己的 credentials 成功呼叫 get-named-query
- [ ] Submit 前等至少 5 分鐘（CloudTrail 寫入延遲）

---

## 5. 已知 Grader 陷阱（首刷踩到的坑）

| Task | 陷阱 | 解法 |
|---|---|---|
| 1c | Preview SQL 格式錯 → 0/5 | 必須用 `SELECT * FROM "taxidata"."yellow" limit 10`（雙引號 + 小寫 limit） |
| 4 | View SELECT 事件未寫入 CloudTrail → 0/5 | 建立 view 後必須跑 SELECT；且 Submit 前等 5 分鐘 |
| UpdateWorkGroup | AccessDeniedException | LabRole 無此權限；但每條 query 個別指定 OutputLocation 即可繞過 |

---

## 6. 完成宣告

> Module 4 已執行完畢。請去 AWS Console 截圖交作業，截圖放進 `{{STUDENT_ID}}/submissions/module4/`。
> 
> Submit 前務必等 **至少 5 分鐘**，確保 CloudTrail 事件寫入完成。

---

## 7. Recommended Model

| 模式 | 建議模型 | 理由 |
|---|---|---|
| **複刻**（此 SUCCESS.md 已存在） | **Haiku 4.5**（雲）或本地 **30B+ instruct with tool-use** | 所有指令已逐字列出，只需替換 `{{STUDENT_ID}}` 和 `{{BUCKET}}` 後順序執行 |
| **首刷 / debug** | **Sonnet 4.6** | 需理解 Athena API 行為與 grader 陷阱 |
| **IAM 邊界 debug** | **Opus 4.7** | Lab 的 IAM 限制（UpdateWorkGroup 等）需要深度理解策略差異 |

本地最低可用模型：**Qwen2.5-32B-Coder** 或 **Llama 3.3 70B**（需穩定 function-calling）。7B-13B 不建議。

---

## 8. 首刷紀錄對照

JOURNAL.md 事件 #2–#8（位於 `experiment/JOURNAL.md`）記錄了完整首刷流程，包含試錯過程。
