# lab10.1 — 實驗記錄

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

### [2026-09-14 19:11] 事件 #1 — 專題初始化

**當下模型**：opus-4-7
**現象**：從零建立 `lab10.1` 專題骨架。
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
### [2026-09-14 19:37] 事件 #2 — 首刷 Task1 手動(IDE setup.sh) + Task2–7 全 boto3（SQS FIFO ×2 + policy、SNS FIFO + policy、subscribe、publish、EB env、DLQ）

**當下模型**：opus-5
**現象**：ACD_2.0 stack ~25 分鐘才 CREATE_COMPLETE；setup.sh 要 docker 只能 IDE 跑；之後不需 SSH
**原因**：Console/CLI 對應：create_queue(Attributes from json)、set_queue_attributes(Policy)、create_topic(FifoTopic)、set_topic_attributes(Policy)、subscribe(sqs)、publish(MessageGroupId, MessageAttributes)、eb.update_environment(SQS_ENDPOINT/SQS_REGION)
**處理**：lab10_1_steps.py 一次跑完；publish_file() 重現 send_beans_update.py；輪詢 DLQ 直到 3 筆（app 5 次失敗 ×30s visibility ≈ 3 分鐘）；輪詢 /beans 直到 209/306
**驗證**：dedup：第 1、3 筆同 SequenceNumber；queue 收 3 筆、最大那筆帶 inventory_alert=out_of_stock；DLQ 3 筆；/beans 209 & 306
**Tags**：#sqs #sns #fifo #dead-letter-queue #dedup #elastic-beanstalk #manual-required #first-pass

---

### [2026-09-14 19:43] 事件 #3 — Submit → 100/100；提煉 SUCCESS.md

**當下模型**：opus-5
**現象**：grader 滿分
**原因**：queue/topic/policy/DLQ/EB env/資料狀態全由 boto3 達成
**處理**：寫 SUCCESS.md，同步公開倉 cloud_developing/lab10.1
**驗證**：Grades 100/100
**Tags**：#pass #full-marks

---

