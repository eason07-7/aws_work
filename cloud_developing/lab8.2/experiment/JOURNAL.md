# lab8.2 — 實驗記錄

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

### [2026-09-14 17:05] 事件 #1 — 專題初始化

**當下模型**：opus-4-7
**現象**：從零建立 `lab8.2` 專題骨架。
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
### [2026-09-14 17:29] 事件 #2 — 首刷 Task1 手動(IDE setup.sh + 加公鑰) + Task2–10 全自動（子網/Aurora Serverless v2/Data API/EB/API GW）

**當下模型**：opus-5
**現象**：setup.sh 需 docker build+push 只能在 IDE 跑；本次不留 c9key，改由貼指令時把本機公鑰 <學號>/lab_ide_key.pub 加進 authorized_keys
**原因**：自動化優先；Console 操作全有 SDK 對應：create_subnet/associate_route_table、create_db_cluster(EnableHttpEndpoint, ServerlessV2ScalingConfiguration)+create_db_instance(db.serverless)、rds-data execute_statement（=Query Editor）、EB create_application/create_environment/create_application_version/update_environment、apigateway HTTP_PROXY
**處理**：lab8_2_steps.py idempotent 可分段跑：先跑 Task2/3 讓 Aurora 開建，setup.sh 完成後重跑接 Task4–10。Aurora 3.07.0 已下架改 3.08.0；Data API 需 Secrets Manager secret supplierdb-admin；Dockerrun.aws.json 上傳 EB storage bucket 後 create_application_version(MyNodeApp-version-1a)；IDE 容器在 EB 建立後 stop/rm
**驗證**：Aurora available、/suppliers 8 筆、beans 14 筆；EB MyEnv Green，/beans.json 回 Arabica；API TEST /bean_products 200；prod 已 deploy。全程約 25 分鐘（Aurora 8 分 + EB 建環境 4 分 + 部署 2 分）
**Tags**：#aurora-serverless #rds-data-api #elastic-beanstalk #dockerrun #api-gateway-http-proxy #manual-required #first-pass

---

### [2026-09-14 17:40] 事件 #3 — 第一次 Submit 少 Task 6 兩項 → 補 Query-Editor 格式 secret → 100/100

**當下模型**：opus-5
**現象**：報告：PROBLEM: Unable to connect to the coffee database ×2，其餘 7 項過；但 admin/nodeapp 走 Data API、IDE 上 mysql 皆可連
**原因**：grader 找 Console Query Editor 建的 Secrets Manager secret（rds-db-credentials/<DbClusterResourceId>/admin/<epoch>）走 Data API；boto3 自建的 supplierdb-admin 名字不符
**處理**：建同格式 secret（含 dbInstanceIdentifier/engine/host/port/resourceId/username/password）並用它 execute_statement 查 suppliers/beans；已寫進 lab8_2_steps.py Task 6
**驗證**：重新 Submit → 100/100；提煉 SUCCESS.md
**Tags**：#pass #full-marks #grader-trap #secrets-manager #rds-data-api

---

