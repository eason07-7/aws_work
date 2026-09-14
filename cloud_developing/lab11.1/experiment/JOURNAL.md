# lab11.1 — 實驗記錄

> **事件日誌（append-only）**。關鍵決策、失敗、踩坑、量化結果都寫這。
> 狀態類摘要看 `CHECKPOINT.md`（現況） 與 `TASKS.md`（未來）。
> 追加方式：`python d:\p\awshomework\workflow\scripts\log_experiment.py <project_path> ...` 或手動按格式。

## 格式

```markdown
### [YYYY-MM-DD HH:MM] 事件 #N — <標題>

**當下模型**：haiku-4-5 / sonnet-4-6 / opus-4-7
**現象**：發生了什麼（1-2 句具體、可驗證）
**原因**：根因（不是表象）
**處理**：做了什麼（命令 / 程式變更 / 決策）
**驗證**：怎麼確認有效（log / metric / 人眼確認）
**數據/指標**：關鍵數字（query 耗時、成績、資料列數）
**量化驗收**：PASS / WARN / FAIL（若有預設門檻）
**對應輸出檔案**：`path/to/artifact.py`、`path/to/output.txt`
**Tags**：#tag-a #tag-b
```

### 事件編號規則
- **全專案連續編號**（`#1`, `#2`, ... 跨 Phase 不重置）
- `log_experiment.py` 會自動遞增

### 欄位寫法建議
- **現象 / 原因 / 處理 / 驗證**：必填四段
- **量化驗收**：若沒有數字門檻可略；若 FAIL 要寫明門檻是什麼
- **Tags**：小寫、hyphen-case、以 `#` 開頭。`INDEX.md` 會自動建反向索引

**不記**：臨時 TODO、git log 已有的資訊、每次對話的閒聊、工具輸出原文（除非是關鍵錯誤訊息）

---

## Phase 1 — <第一階段名稱>（進行中）

### [2026-09-14 20:51] 事件 #1 — 專題初始化

**當下模型**：opus-4-7
**現象**：從零建立 `lab11.1` 專題骨架。
**原因**：套用 workflow v0.3.0-aws-nopatch 標準結構。
**處理**：執行 `init_project.py --type generic`，產出 CLAUDE.md、PROJECT_STATE.md、CHECKPOINT.md、TASKS.md、JOURNAL.md、experiments/INDEX.md。
**驗證**：骨架檔案已就位，`python d:\p\awshomework\workflow\scripts\checkpoint.py . status` 可跑。
**數據/指標**：初始化時間 < 5s。
**量化驗收**：PASS
**對應輸出檔案**：`CLAUDE.md`、`PROJECT_STATE.md`、`CHECKPOINT.md`、`TASKS.md`
**Tags**：#init #workflow-bootstrap

---

<!-- 後續事件請由 log_experiment.py 追加，或手動沿用格式 -->
<!-- Phase 封存方式：當此 Phase 結束時，此檔 rename 為 experiments/phaseN_<name>.md，然後新開一份空的 JOURNAL.md 給下一個 Phase -->
### [2026-09-14 21:34] 事件 #2 — 首刷 Task1 手動(setup.sh+公鑰) + Task2 email 確認手動 + Task2–9 boto3/SSH 全自動（SNS、Step Functions 增量建構、3 Lambda、API→StartExecution）

**當下模型**：opus-5
**現象**：ACD_2.0 stack ~25 分鐘；AWS Details 面板一開始沒 LabIDEURL（VSCodeStack 未建完），從 CloudFormation outputs 撈；SNS email 訂閱需使用者點 Confirm
**原因**：Console 對應：sns create_topic+policy(Everyone)、stepfunctions create/update_state_machine（lambda:invoke + OutputPath $.Payload + Retry，= Workflow Studio 預設）、lambda create_function(ZipFile)、apigateway put_integration(type AWS, uri states:action/StartExecution, credentials role, requestTemplates)、Lambda VPC config
**處理**：lab11_1_steps.py 分段 idempotent；state machine 依 Task 3/4/7/9 四次 update；generateReportData 的 mysql2 依賴經 SSH 在 IDE npm install 後 sftp 抓 lambda.zip；踩坑：(1) passthroughBehavior 要 WHEN_NO_MATCH（Console 的 When there are no templates defined）；(2) urllib POST 帶 data 會自動加 x-www-form-urlencoded Content-Type 導致不套 template → 改成無 body 的 POST 才等於 curl -X POST
**驗證**：四次執行皆 SUCCEEDED；test_invoke 與 curl 皆回 executionArn；generateReportData 回 8 suppliers；email 收到報表 presigned URL
**Tags**：#step-functions #sns #lambda #api-gateway-aws-integration #presigned-url #lambda-vpc #manual-required #first-pass

---

### [2026-09-14 21:39] 事件 #3 — 第一次 Submit：SNS Publish not found + grader KeyError 'Arguments' → 改 JSONata 定義 → 100/100

**當下模型**：opus-5
**現象**：報告：topic/state machine/GeneratePresignedURL 過，但 'An SNS Publish action using the EmailReport topic was not found'，grader 在 branch_stage['States'][x]['Arguments']['FunctionName'] KeyError
**原因**：grader 假設新版 Workflow Studio 產生的 JSONata 格式（Arguments/Output），我用舊版 JSONPath Parameters/OutputPath
**處理**：sm_definition() 改為 QueryLanguage=JSONata：lambda Arguments{FunctionName, Payload='{% $states.input %}'} + Output='{% $states.result.Payload %}'；sns Arguments{TopicArn, Message='{% $states.input %}'}；update_state_machine 重跑 Task 4/7/9 執行皆 SUCCEEDED
**驗證**：重新 Submit → 100/100；提煉 SUCCESS.md
**Tags**：#pass #full-marks #grader-trap #jsonata #step-functions

---

