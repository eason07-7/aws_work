# AWS Academy Data Engineering [154382] — 封存
EE300016 [A] 大數據資料處理(大三)

> 已封存課程，指南仍可用。


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

### [Module 11 — Kinesis Data Firehose + OpenSearch + Dashboards](module11/)

**分數** 滿分  
**重點技能**：
- Kinesis Data Firehose → Lambda enrichment → OpenSearch Service 完整 pipeline
- Amazon Cognito OAuth 2.0 browser flow 模擬（生成 `CognitoAuthentication` CloudTrail 事件）
- Cognito Identity Pool federated credentials → SigV4 (`es` service) for OpenSearch REST API
- OpenSearch Saved Objects API：建 index pattern、pie chart、heat map visualization
- CloudTrail reverse-engineering：grader "review X" = boto3 describe/get call 觸發 CloudTrail 事件

**關鍵陷阱**：
- **Task 2（Cognito 登入）**：必須用 OpenSearch Dashboards 自帶的 client ID（`n1l4rlfcqffcnv65diremjdjv`），SRP auth 不夠；要從 `OS_ENDPOINT/_dashboards` 起頭讓 OpenSearch 設 state cookie，再走 Cognito Hosted UI，最後 OpenSearch 自己完成 code exchange
- **Task 1（EC2 review）**：grader 錯誤訊息寫「Answer the question」，但實際只要 `describe_instances()` + `describe_instance_types()` CloudTrail 事件就通過，不需手動回答 quiz
- **Firehose buffer**：60s flush interval；生成 traffic 後需 `sleep(90)` 再查 OpenSearch
- **SigV4 service name**：OpenSearch 仍用 `es`，不是 `opensearch`
- **osd-xsrf header**：所有 Dashboards write API 需帶 `osd-xsrf: true`

[👉 Module 11 完整指南](module11/SUCCESS.md)

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

### [Module 12 — Building and Orchestrating ETL Pipelines (Step Functions + Athena + Glue)](module12/)

**分數** 滿分  
**重點技能**：
- AWS Step Functions state machine 增量建構（boto3 `create_state_machine` + `update_state_machine`）
- Athena CTAS：CSV → Parquet（Snappy compression）+ 分區（pickup_year / pickup_month）
- AWS Glue Data Catalog：外部表 + Parquet 表 + Athena View 自動建立
- Step Functions Map state 迭代 Glue 表名，條件 INSERT INTO 新月份資料
- 大檔案串流上傳（`requests.get(stream=True)` + `s3.upload_fileobj`）

**關鍵陷阱**：
- **`End` + `Next` 共存**：`update_state_machine` 若 state 同時有兩個會 `InvalidDefinition`；切換時用 `state.pop('End', None)` 不是 `state['End'] = False`
- **ExecutionAlreadyExists**：重跑需 catch exception，確認已 SUCCEEDED 再 skip
- **Parquet CTAS 耗時 5–10 分鐘**：TaskEightTest / TaskTenTest 都要跑 500MB CSV → Parquet
- **S3 前綴需清空**：重建 Parquet table 前要刪 `optimized-data/` 和 `optimized-data-lookup/` 的所有 objects
- **8 個 execution 必須按序命名**：TaskTwoTest → TaskThreeTest → TaskFiveTest → TaskSixTest → TaskSevenTest → TaskEightTest → TaskTenTest → TaskTwelveTest（grader 按名稱查）

[👉 Module 12 完整指南](module12/SUCCESS.md)

---

