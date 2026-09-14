# lab8.1 — 實驗記錄

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

### [2026-09-14 16:26] 事件 #1 — 專題初始化

**當下模型**：opus-4-7
**現象**：從零建立 `lab8.1` 專題骨架。
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
### [2026-09-14 16:54] 事件 #2 — 首刷 Task1 手動(IDE 終端 setup.sh) + Task2–6 經 SSH 全自動（docker/mysqldump/ECR）

**當下模型**：opus-5
**現象**：所有 docker 動作都在 Lab IDE EC2 上；IDE 無 KeyName、SSM 與 EC2 Instance Connect 皆 AccessDenied，無法從本機直接進入
**原因**：setup.sh 會產生 SSH key 存 Secrets Manager c9key 並開 port 22（給 grader 用）→ 本機 get_secret_value 拿同一把 key 即可 paramiko SSH 進 IDE；setup.sh 本身必須在 IDE 終端跑（用 instance metadata）
**處理**：使用者在 IDE 終端跑 wget/unzip/setup.sh（用 Chrome 自動化代打）；lab8_1_steps.py：HTTP POST 新增+修改 supplier、SG +3000、SSH 跑 Dockerfile/build/run(APP_DB_HOST)、mysqldump -pcoffee 非互動、sed Main→Container、mysql_server build、等第二次 ready for connections 再 import、CREATE USER、node_app_1 改指 mysql_1 172.17.0.3、ECR create/login/tag/push
**驗證**：http://<IDE>:3000/suppliers 顯示 Container Street；docker ps = node_app_1+mysql_1；ecr list-images node-app:latest。踩坑：(1) paramiko exec_command 用 repr 包多行腳本 → \n 變字面，改 stdin 餵 bash -ls；(2) mysql 8.0.23 首啟動 init 後重啟，mysqladmin ping 過早通過導致 import 失敗 → 改等 log 'ready for connections.*port: 3306'；(3) f-string 內 sed 的 {} 要 {{}}
**Tags**：#docker #dockerfile #mysql #mysqldump #ecr #paramiko #manual-required #first-pass

---

### [2026-09-14 17:00] 事件 #3 — Submit → 100/100；提煉 SUCCESS.md

**當下模型**：opus-5
**現象**：grader 滿分
**原因**：容器狀態 + ECR 由 SSH 自動化達成
**處理**：寫 SUCCESS.md（Step 2.1 標 MANUAL），同步公開倉 cloud_developing/lab8.1
**驗證**：Grades 100/100
**Tags**：#pass #full-marks

---

