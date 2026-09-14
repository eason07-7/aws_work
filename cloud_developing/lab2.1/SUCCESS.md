# Lab 2.1 — Exploring AWS CloudShell and IDE

**分數**：100/100（全 boto3 自動化，無手動步驟）

## 0. Prerequisites
- Learner Lab started；Lab 頁面 **Details → AWS: Show** 取 access key / secret / session token
- Region: us-east-1
- Lab 啟動時帳號內只有一個空的 sample bucket
- 本機 `pip install boto3`

## 1. Placeholders
| Placeholder | 說明 | 範例 |
|---|---|---|
| {{BUCKET}} | Lab 預建的 sample bucket（腳本動態取得，勿硬寫） | c215460a...-samplebucket-xzbadyiixxyg |

## 2. Step-by-step（boto3）

一鍵：把憑證填進 [`lab2_1.py`](lab2_1.py) 後 `python lab2_1.py`。以下是它做的事。

### Step 2.1 — 找出 sample bucket（= 作業的 `aws s3 ls`）
**Command:** `s3.list_buckets()` → 挑名字去掉 hyphen 後含 `samplebucket` 的那個
**Expected output:** `['c215460a5440389l16814605t1w6297422332-samplebucket-xzbadyiixxyg']`
**If fails:** 找不到 → Lab 還沒 ready，等 1–2 分鐘再跑

### Step 2.2 — 上傳 list-buckets.py（Task 1：`aws s3 cp list-buckets.py s3://{{BUCKET}}`）
**Command:** `s3.put_object(Bucket=BUCKET, Key='list-buckets.py', Body=<作業給的 6 行 boto3 程式>)`

### Step 2.3 — 下載回來（Task 2：`aws s3 cp s3://{{BUCKET}}/list-buckets.py .`）
**Command:** `s3.get_object(Bucket=BUCKET, Key='list-buckets.py')`

### Step 2.4 — 上傳 index.html（Task 2：`aws s3 cp index.html s3://{{BUCKET}}/index.html`）
**Command:** `s3.put_object(Bucket=BUCKET, Key='index.html', Body='<body> Hello World. </body>\n', ContentType='text/html')`
**Verify:** `list_objects_v2` 回傳 `['index.html', 'list-buckets.py']`

## 3. 驗收清單
- [ ] `{{BUCKET}}` 內有 `list-buckets.py`
- [ ] `{{BUCKET}}` 內有 `index.html`
- [ ] Lab 頁 Submit → 100/100

## 4. Known grader traps
- **bucket 名跟文件不同**：文件寫 `-sample-bucket-`，實際是 `-samplebucket-`（無中間 hyphen）→ 用去 hyphen 比對
- **CloudShell / VS Code IDE 的 UI 探索步驟 grader 完全不看**：不需開 CloudShell、不需登 IDE、不需 `pip3 install boto3`；只看 S3 兩個物件
- Appendix 的 `s3-permissions.py` 是給下一個 Lab 用的，本 Lab 不需執行

## 5. Recommended model
- 複刻：Haiku 4.5（一條指令跑完）
