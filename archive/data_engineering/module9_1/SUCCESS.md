# Module 9_1 — Processing Logs by Using Amazon EMR

**Score**: 滿分  
**Lab**: Processing Logs by Using Amazon EMR (EMR + Hive + S3)

---

## 0. Prerequisites

- Learner Lab started; `{{STUDENT_ID}}/.env` 有有效 session_token
- Region: us-east-1
- `{{STUDENT_ID}}/labsuser.pem` 已下載（EC2 key pair，SSH 進 EMR master 用）
- `paramiko` 已安裝：`pip install paramiko`

---

## 1. Placeholders

| Placeholder | 說明 | 範例 |
|---|---|---|
| `{{STUDENT_ID}}` | 此次執行的學號 | 112021161 |
| `{{HIVE_BUCKET}}` | hive-output S3 bucket（從 CF outputs 取） | hive-output-t9xui49o |

---

## 2. Architecture

```
S3 source (公開帳號)              EMR cluster (emr-5.29.0)
aws-tc-largeobjects/...  ──→  Hive metastore (Derby)
  tables/impressions/               impressions (external, S3)
  tables/clicks/                    clicks (external, S3)
                                    tmp_impressions (HDFS)
                                    tmp_clicks (HDFS)
                          ──→  joined_impressions (external, S3 output)

SSH (paramiko)  ──→  hadoop@master  ──→  hive -f / hive -e
```

---

## 3. Step-by-step

### Step 3.1 — 取 CF outputs，找 hive-output bucket

```python
import boto3, os

session = boto3.Session(
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'],
    region_name='us-east-1',
)
cf = session.client('cloudformation')
outputs = {}
for stack in cf.describe_stacks()['Stacks']:
    for o in stack.get('Outputs', []):
        outputs[o['OutputKey']] = o['OutputValue']

hive_bucket = outputs['HiveOutputBucket']  # e.g. hive-output-t9xui49o
subnet_id   = outputs.get('SubnetId') or outputs.get('PublicSubnetId')
output_loc  = f's3://{hive_bucket}/output/'
```

**Expected**: `{'HiveOutputBucket': 'hive-output-xxxxxx'}`

### Step 3.2 — 建 EMR cluster（不帶 Steps，保持 WAITING）

```python
emr = session.client('emr')
instances = {
    'MasterInstanceType': 'm4.large',
    'SlaveInstanceType':  'm4.large',
    'InstanceCount': 3,
    'Ec2KeyName': 'vockey',
    'KeepJobFlowAliveWhenNoSteps': True,
}
if subnet_id:
    instances['Ec2SubnetId'] = subnet_id

resp = emr.run_job_flow(
    Name='Hive EMR cluster',
    ReleaseLabel='emr-5.29.0',
    Applications=[{'Name': 'Hadoop'}, {'Name': 'Hive'}],
    Instances=instances,
    JobFlowRole='EMR_EC2_DefaultRole',
    ServiceRole='EMR_DefaultRole',
    LogUri=f's3://{hive_bucket}/logs/',
)
cluster_id = resp['JobFlowId']
```

**注意**: 不要帶 `Tags`（`elasticmapreduce:AddTags` AccessDenied）

### Step 3.3 — 取 master SG，加 SSH Anywhere-IPv4 規則

```python
import time
ec2 = session.client('ec2')

master_sg = None
for _ in range(40):
    desc = emr.describe_cluster(ClusterId=cluster_id)
    master_sg = desc['Cluster'].get('Ec2InstanceAttributes', {}).get('EmrManagedMasterSecurityGroup')
    if master_sg:
        break
    time.sleep(15)

ec2.authorize_security_group_ingress(
    GroupId=master_sg,
    IpPermissions=[{
        'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
    }]
)
```

**Verify**: grader 檢查 `sg_configured: True`（SSH 0.0.0.0/0 TCP 22 必須存在）

### Step 3.4 — 等 cluster WAITING state（約 5–7 分鐘）

```python
master_dns = None
for i in range(90):
    desc = emr.describe_cluster(ClusterId=cluster_id)
    state = desc['Cluster']['Status']['State']
    master_dns = desc['Cluster'].get('MasterPublicDnsName')
    if state == 'WAITING':
        break
    time.sleep(20)
```

**Expected**: `State=WAITING`, `MasterPublicDnsName=ec2-x-x-x-x.compute-1.amazonaws.com`  
**Verify**: grader 檢查 `pub_ip_set: True`（master 有 public DNS）

### Step 3.5 — paramiko SSH，設 Hive log dir（Task 3）

```python
import paramiko

key = paramiko.RSAKey.from_private_key_file('{{STUDENT_ID}}/labsuser.pem')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for attempt in range(12):
    try:
        ssh.connect(master_dns, username='hadoop', pkey=key, timeout=30)
        break
    except Exception:
        time.sleep(30)

def run(cmd, timeout=900):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    return rc, stdout.read().decode(), stderr.read().decode()

run('sudo chown hadoop -R /var/log/hive 2>/dev/null; true')
run('mkdir -p /var/log/hive/user/hadoop')
```

**Verify**: `ls /var/log/hive/user/` shows `hadoop/` directory

### Step 3.6 — 上傳 HQL，執行 Hive -f（Tasks 4 + 5，約 15 分鐘）

HQL 內容（所有 table + INSERT）：

```sql
CREATE EXTERNAL TABLE impressions (
  requestBeginTime string, adId string, impressionId string,
  referrer string, userAgent string, userCookie string, ip string)
PARTITIONED BY (dt string)
ROW FORMAT serde 'org.apache.hive.hcatalog.data.JsonSerDe'
WITH SERDEPROPERTIES ('paths'='requestBeginTime, adId, impressionId, referrer, userAgent, userCookie, ip')
LOCATION '${SAMPLE}/tables/impressions';

set hive.msck.path.validation=ignore;
MSCK REPAIR TABLE impressions;

CREATE EXTERNAL TABLE clicks (impressionId string, adId string)
PARTITIONED BY (dt string)
ROW FORMAT serde 'org.apache.hive.hcatalog.data.JsonSerDe'
WITH SERDEPROPERTIES ('paths'='impressionId')
LOCATION '${SAMPLE}/tables/clicks';

MSCK REPAIR TABLE clicks;

CREATE EXTERNAL TABLE joined_impressions (
  requestBeginTime string, adId string, impressionId string,
  referrer string, userAgent string, userCookie string, ip string,
  clicked Boolean)
PARTITIONED BY (day string, hour string)
STORED AS SEQUENCEFILE
LOCATION '${OUTPUT}/tables/joined_impressions';

CREATE TABLE tmp_impressions (
  requestBeginTime string, adId string, impressionId string,
  referrer string, userAgent string, userCookie string, ip string)
STORED AS SEQUENCEFILE;

INSERT OVERWRITE TABLE tmp_impressions
SELECT from_unixtime(cast((cast(i.requestBeginTime as bigint)/1000) as int)),
  i.adId, i.impressionId, i.referrer, i.userAgent, i.userCookie, i.ip
FROM impressions i
WHERE i.dt >= '${DAY}-${HOUR}-00' AND i.dt < '${NEXT_DAY}-${NEXT_HOUR}-00';

CREATE TABLE tmp_clicks (impressionId string, adId string) STORED AS SEQUENCEFILE;

INSERT OVERWRITE TABLE tmp_clicks
SELECT impressionId, adId FROM clicks c
WHERE c.dt >= '${DAY}-${HOUR}-00' AND c.dt < '${NEXT_DAY}-${NEXT_HOUR}-20';

INSERT OVERWRITE TABLE joined_impressions PARTITION (day='${DAY}', hour='${HOUR}')
SELECT i.requestBeginTime, i.adId, i.impressionId, i.referrer,
  i.userAgent, i.userCookie, i.ip, (c.impressionId is not null) clicked
FROM tmp_impressions i
LEFT OUTER JOIN tmp_clicks c ON i.impressionId = c.impressionId;
```

執行：

```python
SAMPLE   = 's3://aws-tc-largeobjects/CUR-TF-200-ACDENG-1/emr-lab'
DAY      = '2009-04-13'
HOUR     = '08'
NEXT_DAY = '2009-04-13'
NEXT_HOUR= '09'

sftp = ssh.open_sftp()
with sftp.open('/tmp/hive_all.hql', 'w') as f:
    f.write(HQL)
sftp.close()

cmd = (f'hive -d SAMPLE={SAMPLE} -d DAY={DAY} -d HOUR={HOUR} '
       f'-d NEXT_DAY={NEXT_DAY} -d NEXT_HOUR={NEXT_HOUR} '
       f'-d OUTPUT={output_loc} -f /tmp/hive_all.hql')
run(cmd, timeout=1800)
```

**Verify**: S3 `output/tables/joined_impressions/day=2009-04-13/hour=08/000000_0` 存在（~5.7MB）

### Step 3.7 — 跑 referrer 查詢 → result.txt（Task 6）

```python
run(
    'hive -e "SELECT referrer, count(*) as hits FROM joined_impressions '
    'WHERE clicked = true GROUP BY referrer ORDER BY hits DESC LIMIT 10;" '
    '> /home/hadoop/result.txt',
    timeout=600
)
```

**Expected output**（`cat /home/hadoop/result.txt`）：

```
ibibo.com       49
lowes.com       33
odnoklassniki.ru        33
files.wordpress.com     30
...
```

**Verify**: `ls -lh /home/hadoop/result.txt` 顯示 167 bytes

---

## 4. 驗收清單

- [ ] Task 1: EMR cluster "Hive EMR cluster" emr-5.29.0 建立成功，m4.large × 3
- [ ] Task 2: SSH 連線到 master（paramiko 自動完成）
- [ ] Task 3: `/var/log/hive/user/hadoop/` 目錄存在，`hive.log` 已產生
- [ ] Task 4: `impressions`、`clicks` 外部表建立，241 partitions MSCK REPAIR
- [ ] Task 5: S3 `output/tables/joined_impressions/day=2009-04-13/hour=08/000000_0` 存在（5,719,937 bytes）
- [ ] Task 6: `/home/hadoop/result.txt` 存在，top-10 referrer 資料正確

---

## 5. Known grader traps

- **sg_configured: False** — 必須對 master SG 加 TCP 22 `0.0.0.0/0` 規則（Step 3.3）；不加則 Task 1 失分
- **pub_ip_set: False** — cluster 需建在有 auto-assign public IP 的 subnet（Lab VPC 的 public subnet）；subnet_id 從 CF outputs 取
- **AddTags AccessDenied** — `run_job_flow` 不能帶 `Tags` 參數，voclabs IAM explicit deny
- **AddJobFlowSteps AccessDenied** — 不能用 `add_job_flow_steps`；改用 `run_job_flow` 時不帶 Steps（cluster 保持 WAITING）
- **ssm:SendCommand AccessDenied** — 不能用 SSM，只能 paramiko SSH
- **s3:PutObject 部分 bucket 拒絕** — 只能寫 `hive-output-*` bucket，不能寫 UUID bucket

---

## 6. Recommended model

- 複刻：Haiku 4.5（全自動，無 🖐 MANUAL 步驟）
- 首刷/debug：Sonnet 4.6
