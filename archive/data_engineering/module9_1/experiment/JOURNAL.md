# module9_1 — 實驗記錄

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

### [2026-04-30 20:20] 事件 #1 — 專題初始化

**當下模型**：opus-4-7
**現象**：從零建立 `module9_1` 專題骨架。
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
### [2026-04-30 20:20] 事件 #2 — 首刷初探：自動化邊界確認

**當下模型**：sonnet-4-6
**現象**：嘗試用 boto3 全自動完成 module9_1（EMR+Hive），Task 5 通過（S3 joined_impressions 5.7MB），但 Task 3/4/6 因 grader SSH 驗證失敗拿不到分
**原因**：grader 需要 SSH 進 EMR master 確認本地檔案（/var/log/hive/user/hadoop, /home/hadoop/result.txt）。voclabs IAM 無 AddJobFlowSteps / s3:PutObject / ssm:SendCommand，改用 RunJobFlow 內嵌 Step（bash base64 HQL）成功跑完 Hive，但 grader SSH 連線失敗原因未知（SG 規則與 Public IP 均確認正確）
**處理**：建立兩個 cluster（j-EMKW9D15KBEO WAITING, j-1MOF0XMK75ZN2 WAITING+Step COMPLETED），HQL 跑完寫入 S3，需要重開 Lab 用 paramiko SSH 方式再試
**驗證**：Task 5 grader 通過；S3 output/tables/joined_impressions/day=2009-04-13/hour=08/000000_0 存在 5719937 bytes

---

### [2026-04-30 20:20] 事件 #3 — 下次執行計畫：paramiko SSH 方式

**當下模型**：sonnet-4-6
**現象**：新 Lab 開好後需要 labsuser.pem 才能 SSH 進 EMR master 執行 Hive
**原因**：grader 用 SSH 驗證本地檔案（/var/log/hive/user/hadoop, /home/hadoop/result.txt），只有 SSH 路徑才能讓 Task 3/4/6 過關
**處理**：計畫：1) pip install paramiko  2) 用 RunJobFlow 建 cluster + 加 SSH 規則  3) 等 WAITING  4) paramiko SSH 跑 Hive（sudo chown/mkdir log dir, CREATE tables, MSCK, tmp tables, INSERT, JOIN, hive -e query > result.txt）  5) 確認 S3 output 存在後 Submit
**驗證**：待執行

---

### [2026-04-30 21:25] 事件 #4 — 首刷完成：paramiko SSH 方式，全任務通過，滿分

**當下模型**：sonnet-4-6
**現象**：用 paramiko SSH 進 EMR master，跑 hive -f 執行所有 Table creation + MapReduce INSERT，再用 hive -e 寫出 result.txt，所有 grader 檢查通過
**原因**：前次 RunJobFlow 內嵌 Step 方式無法讓 grader SSH 驗證成功（sg_configured/pub_ip_set=False）；改用 cluster 保持 WAITING + paramiko 直接 SSH 後，grader 可正確驗證本地檔案
**處理**：run_job_flow (無 Steps, KeepAlive=True) → 加 SG SSH 0.0.0.0/0 → WAITING → paramiko SSH → sudo chown /var/log/hive + mkdir /var/log/hive/user/hadoop → hive -f HQL (impressions/clicks/tmp tables + INSERT JOIN) → hive -e SELECT > result.txt
**驗證**：cat /home/hadoop/result.txt 有 10 筆 referrer；S3 joined_impressions 5719937 bytes；submit 滿分

---

