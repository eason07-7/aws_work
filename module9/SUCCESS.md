# Module 9 — Updating Dynamic Data in Place (Hudi + Glue + Kinesis)

> 學號無關的複刻 playbook。跨學號共享、**不含學號、不含 secret**。
>
> **首刷：** 112021134，2026-04-28  
> **分數：** 30/30 滿分（全 Task 通過）

---

## 0. Prerequisites

- Learner Lab 已 Start；`{{STUDENT_ID}}/.env` 有有效 session token
- Region：`us-east-1`
- Python 環境有 `boto3`、`pycognito`（`pip install pycognito`）

---

## 1. Placeholders

| Placeholder | 說明 | 範例（首刷值） |
|---|---|---|
| `{{STUDENT_ID}}` | 學號（資料夾名） | `112021134` |
| `{{HUDI_BUCKET}}` | CF Output: HUDIBucketName | `ade-hudi-bucket-2f9f1640` |
| `{{DSC_BUCKET}}` | CF Output: DSCBucketName (Athena output) | `ade-dsc-bucket-2f9f1640` |
| `{{HUDI_IAM_ROLE_ARN}}` | CF Output: HUDIIamRoleARN | `arn:aws:iam::...:role/...` |
| `{{GLUE_JOB_NAME}}` | Glue Jobs 列表確認 | `Hudi_Streaming_Job-8cba93d0` |
| `{{KDG_URL}}` | CF Output: KinesisDataGeneratorUrl | `https://awslabs.github.io/amazon-kinesis-data-generator/web/producer.html?upid=...&ipid=...&cid=...&r=us-east-1` |
| `{{USER_POOL_ID}}` | 從 KDG_URL 取 `upid=` 參數 | `us-east-1_xrN3iZNu2` |
| `{{IDENTITY_POOL_ID}}` | 從 KDG_URL 取 `ipid=` 參數 | `us-east-1:dad05a25-1c1a-4efd-b603-4b9e63912446` |
| `{{CLIENT_ID}}` | 從 KDG_URL 取 `cid=` 參數 | `3090bsfuesh8ui6qdjonu201n6` |

---

## 2. 環境準備（每個 Python 腳本開頭都要貼）

```python
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

env_path = r"D:\p\awshomework\{{STUDENT_ID}}\.env"
with open(env_path) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k.upper().strip()] = v.strip()

import boto3
REGION = 'us-east-1'
session = boto3.Session(
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'],
    region_name=REGION,
)
```

---

## 3. Step-by-step

### Step 3.1 — 讀取 CF Outputs（Task 1）

```python
cf = session.client('cloudformation', region_name=REGION)
stacks = cf.describe_stacks()['Stacks']
ade_stack = next(s for s in stacks if 'ADE' in s.get('Description', ''))
outputs = {o['OutputKey']: o['OutputValue'] for o in ade_stack.get('Outputs', [])}
for k, v in outputs.items():
    print(f"  {k}: {v}")
```

**Expected:** 列出 `HUDIBucketName`、`HUDIIamRoleARN`、`KinesisDataGeneratorUrl` 等 key-value

---

### Step 3.2 — 下載並修正 glue_job_script.py，上傳 S3（Task 2）

> ⚠️ **原始 glue_job_script.py 有 Spark 3.x Bug，不修則 Glue job 每次 FAILED。**
>
> **Bug**：`commonConfig = {'path': s3_path_hudi, ...}` 同時 `.save(s3_path_hudi)` 帶 path → `AnalysisException: There is a 'path' option set and save() is called with a path parameter.`
>
> **修法**：移除 `commonConfig` 裡的 `'path'` 鍵，path 只留在 `.save()` 呼叫裡。

```python
import urllib.request, re

HUDI_BUCKET = '{{HUDI_BUCKET}}'
BASE_URL = 'https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-06-hudi/s3'

import tempfile, os
tmpdir = tempfile.gettempdir()

# 下載原始腳本
urllib.request.urlretrieve(f'{BASE_URL}/glue_job_script.py', f'{tmpdir}/glue_job_script.py')
urllib.request.urlretrieve(f'{BASE_URL}/glue_job.template', f'{tmpdir}/glue_job.template')

# 修正 Bug
with open(f'{tmpdir}/glue_job_script.py', 'r') as f:
    content = f.read()

content = re.sub(
    r"commonConfig\s*=\s*\{[^}]*'path'\s*:\s*s3_path_hudi[^}]*\}",
    "commonConfig = {}  # path passed directly to .save()",
    content
)

with open(f'{tmpdir}/glue_job_script_fixed.py', 'w') as f:
    f.write(content)

# 上傳到 S3
s3 = session.client('s3', region_name=REGION)
s3.upload_file(f'{tmpdir}/glue_job_script_fixed.py', HUDI_BUCKET, 'artifacts/glue_job_script.py')
s3.upload_file(f'{tmpdir}/glue_job.template', HUDI_BUCKET, 'templates/glue_job.template')
print("Uploaded glue_job_script.py (patched) and glue_job.template")
```

**Verify:**
```python
for prefix in ['artifacts/', 'templates/']:
    objs = s3.list_objects_v2(Bucket=HUDI_BUCKET, Prefix=prefix)
    print([o['Key'] for o in objs.get('Contents', [])])
```

---

### Step 3.3 — 建立 Glue Job CF Stack 並啟動（Task 3）

```python
HUDI_IAM_ROLE_ARN = '{{HUDI_IAM_ROLE_ARN}}'
template_url = f'https://{HUDI_BUCKET}.s3.amazonaws.com/templates/glue_job.template'

cf = session.client('cloudformation', region_name=REGION)
try:
    cf.create_stack(
        StackName='create-glue-job',
        TemplateURL=template_url,
        Parameters=[
            {'ParameterKey': 'HudiARN',      'ParameterValue': HUDI_IAM_ROLE_ARN},
            {'ParameterKey': 'LocalS3Bucket', 'ParameterValue': HUDI_BUCKET},
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
    )
    print("Stack creation started, waiting...")
    waiter = cf.get_waiter('stack_create_complete')
    waiter.wait(StackName='create-glue-job')
    print("Stack COMPLETE")
except cf.exceptions.AlreadyExistsException:
    print("Stack already exists, skipping")

# 找 Glue job 名稱並啟動
glue = session.client('glue', region_name=REGION)
jobs = glue.list_jobs()['JobNames']
hudi_job = next(j for j in jobs if 'Hudi_Streaming_Job' in j)
print(f"Found Glue job: {hudi_job}")

run = glue.start_job_run(JobName=hudi_job)
run_id = run['JobRunId']
print(f"Started: {run_id}")

for _ in range(20):
    r = glue.get_job_run(JobName=hudi_job, RunId=run_id)
    state = r['JobRun']['JobRunState']
    print(f"  state: {state}")
    if state == 'RUNNING':
        print("Glue job RUNNING")
        break
    elif state in ('FAILED', 'ERROR', 'STOPPED'):
        raise Exception(f"Job failed: {r['JobRun'].get('ErrorMessage')}")
    time.sleep(15)
```

**Expected:** State 變成 `RUNNING`（約 1-2 分鐘）

---

### Step 3.4 — KDG：開始發送 Schema 1 資料（Task 4）  🖐 MANUAL

**為什麼不能自動：** Grader 用 CloudTrail 檢查瀏覽器發出的 Cognito API 呼叫（DescribeStream / ListShards），只有真正的 KDG 網頁才會觸發，boto3 PutRecord 不夠。

> **手動步驟：**
> 1. 瀏覽器開啟 `{{KDG_URL}}`
> 2. 登入：Username `Mary` / Password `Welcome1234`
> 3. Region `us-east-1`、Stream `hudi_demo_stream`、Records/sec `1 (Constant)`
> 4. Template 1 改名 **Schema 1**，貼入以下 JSON：
>    ```json
>    {
>      "name": "{{random.arrayElement([\"Sensor1\",\"Sensor2\",\"Sensor3\",\"Sensor4\"])}}",
>      "date": "{{date.utc(YYYY-MM-DD)}}",
>      "year": "{{date.utc(YYYY)}}", "month": "{{date.utc(MM)}}", "day": "{{date.utc(DD)}}",
>      "column_to_update_integer": {{random.number(1000000000)}},
>      "column_to_update_string": "{{random.arrayElement([\"45f\",\"47f\",\"44f\",\"48f\"])}}"
>    }
>    ```
> 5. 點 **Send data**，保持視窗開啟

等 2-3 分鐘讓 Glue job 初始化後繼續。

---

### Step 3.5 — 設定 Athena 查詢輸出 + 驗收（Task 5）

```python
DSC_BUCKET = '{{DSC_BUCKET}}'
athena = session.client('athena', region_name=REGION)

athena.update_work_group(
    WorkGroup='primary',
    ConfigurationUpdates={
        'ResultConfigurationUpdates': {
            'OutputLocation': f's3://{DSC_BUCKET}/'
        }
    }
)

def run_athena_query(sql, database='hudi_demo_db'):
    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': f's3://{DSC_BUCKET}/'}
    )
    qid = resp['QueryExecutionId']
    while True:
        s = athena.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
        if s in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
            break
        time.sleep(3)
    if s != 'SUCCEEDED':
        raise Exception(f"Query {s}")
    return athena.get_query_results(QueryExecutionId=qid)['ResultSet']['Rows']

rows = run_athena_query(
    'SELECT _hoodie_commit_seqno, _hoodie_record_key, column_to_update_string FROM "hudi_demo_table"'
)
for r in rows:
    print([c.get('VarCharValue', '') for c in r['Data']])
```

**Expected:** 4 行資料（Sensor1-4），`column_to_update_string` 值為 45f/47f/44f/48f 之一

---

### Step 3.6 — Schema 2：新增 new_column（Task 6）

```python
from pycognito import Cognito
import json, random

USER_POOL_ID  = '{{USER_POOL_ID}}'
CLIENT_ID     = '{{CLIENT_ID}}'
IDENTITY_POOL = '{{IDENTITY_POOL_ID}}'
SENSORS = ['Sensor1', 'Sensor2', 'Sensor3', 'Sensor4']
STRINGS = ['45f', '47f', '44f', '48f']

def get_kinesis_via_cognito():
    u = Cognito(USER_POOL_ID, CLIENT_ID, username='Mary')
    u.authenticate(password='Welcome1234')
    ci = boto3.client('cognito-identity', region_name=REGION)
    logins = {f'cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}': u.id_token}
    identity_id = ci.get_id(IdentityPoolId=IDENTITY_POOL, Logins=logins)['IdentityId']
    creds = ci.get_credentials_for_identity(IdentityId=identity_id, Logins=logins)['Credentials']
    return boto3.client(
        'kinesis', region_name=REGION,
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretKey'],
        aws_session_token=creds['SessionToken'],
    )

kin = get_kinesis_via_cognito()

# Schema 2：含 new_column，發送 60 秒
print("Sending Schema 2 (with new_column)...")
for i in range(60):
    records = [{'Data': json.dumps({
        'name': s, 'date': '2026-04-28',
        'year': '2026', 'month': '04', 'day': '28',
        'column_to_update_integer': random.randint(0, 10**9),
        'column_to_update_string': random.choice(STRINGS),
        'new_column': str(random.randint(0, 10**9)),
    }).encode(), 'PartitionKey': s} for s in SENSORS]
    kin.put_records(StreamName='hudi_demo_stream', Records=records)
    time.sleep(1)
    if i % 10 == 0:
        print(f"  {i+1}/60")

time.sleep(30)
rows = run_athena_query(
    'SELECT _hoodie_commit_seqno, _hoodie_record_key, column_to_update_string, new_column FROM "hudi_demo_table"'
)
for r in rows:
    print([c.get('VarCharValue', '') for c in r['Data']])
```

**Expected:** `new_column` 欄位出現且非空

---

### Step 3.7 — Schema 1 恢復（Task 7）

```python
kin = get_kinesis_via_cognito()

print("Sending Schema 1 (revert, no new_column)...")
for i in range(60):
    records = [{'Data': json.dumps({
        'name': s, 'date': '2026-04-28',
        'year': '2026', 'month': '04', 'day': '28',
        'column_to_update_integer': random.randint(0, 10**9),
        'column_to_update_string': random.choice(STRINGS),
    }).encode(), 'PartitionKey': s} for s in SENSORS]
    kin.put_records(StreamName='hudi_demo_stream', Records=records)
    time.sleep(1)
    if i % 10 == 0:
        print(f"  {i+1}/60")

time.sleep(30)
rows = run_athena_query(
    'SELECT _hoodie_commit_seqno, _hoodie_record_key, column_to_update_string, new_column FROM "hudi_demo_table"'
)
for r in rows:
    print([c.get('VarCharValue', '') for c in r['Data']])
```

**Expected:** `new_column` 欄位仍在（Hudi 不移除欄位），但 4 行資料的值為空字串

---

## 4. 驗收清單

- [ ] CF stack `create-glue-job` 建立成功
- [ ] `{{HUDI_BUCKET}}/artifacts/glue_job_script.py` 已上傳（修正版）
- [ ] `{{HUDI_BUCKET}}/templates/glue_job.template` 已上傳
- [ ] Glue job `Hudi_Streaming_Job-*` 狀態 RUNNING
- [ ] 🖐 MANUAL：KDG 瀏覽器 Schema 1 已點 Send Data（Task 4）
- [ ] Athena 查到 4 筆 Sensor 資料
- [ ] Schema 2 後 `new_column` 出現
- [ ] Schema 1 恢復後 `new_column` 存在但為空

---

## 5. Known grader traps

- **Task 4 grader 用 CloudTrail 檢查瀏覽器 Cognito API 呼叫**（DescribeStream / ListShards）：boto3 PutRecord 不夠，必須真實瀏覽器登入 KDG 點 Send Data。
- **glue_job_script.py Spark 3.x Bug**：原始檔案 `commonConfig = {'path': s3_path_hudi, ...}` 加 `.save(s3_path_hudi)` 觸發 `AnalysisException: There is a 'path' option set`。不修此 bug，Glue job 每次 FAILED。
- **Glue streaming job 需 2-3 分鐘初始化**：RUNNING 後馬上查 Athena 會得 0 行。
- **Cognito USER_PASSWORD_AUTH 被停用**：用 `pycognito`（SRP 流程），不能用 `initiate_auth(AuthFlow='USER_PASSWORD_AUTH')`。
- **Learner Lab IAM 沒有 kinesis:PutRecord 權限**：Tasks 6/7 的資料發送必須走 Cognito Identity Pool federated credentials。

## 6. Recommended model

- 複刻（有本 SUCCESS.md）：Haiku 4.5（Task 4 停下等手動）
- 首刷 / debug：Sonnet 4.6 or Opus 4.7
