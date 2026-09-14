# Lab 3.1 — Working with Amazon S3

**分數**：100/100（首刷 2026-09-14，全 boto3 自動化，無 🖐 MANUAL 步驟）

## 0. Prerequisites
- Learner Lab started；`<學號>/.env` 有有效 session_token；Region us-east-1
- 下載並解壓作業 `code.zip` 到腳本旁邊（得到 `code/resources/website/` 與 `code/python_3/`）
  來源：`https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/02-lab-s3/code.zip`
- 執行機器的對外 IPv4 就是要放行的 IP（腳本用 api.ipify.org 自動抓）

## 1. Placeholders
| Placeholder | 說明 | 範例 |
|---|---|---|
| {{STUDENT_ID}} | 此次執行的學號 | 112021134 |
| {{INITIALS}} | 姓名縮寫小寫（腳本頂端 `INITIALS`） | el |
| {{BUCKET}} | `{{INITIALS}}-<YYYY-MM-DD>-s3site`（腳本自動組） | el-2026-09-14-s3site |
| {{IP}} | 放行的公網 IPv4 | 203.222.22.102 |

## 2. Step-by-step（boto3）

一鍵：填憑證後 `python lab3_1.py`（腳本會自動下載 code.zip）。

### Step 2.1 — 建 bucket（Task 2：`aws s3api create-bucket --bucket {{BUCKET}} --region us-east-1`）
**Command:** `s3.create_bucket(Bucket=BUCKET)`（us-east-1 不帶 LocationConstraint）
**Expected output:** `{'Location': '/el-2026-09-14-s3site'}`

### Step 2.2 — Public access block（Task 2 Console 的「取消 Block all，再勾回三個」）
**Command:** `put_public_access_block(BlockPublicAcls=True, IgnorePublicAcls=True, BlockPublicPolicy=False, RestrictPublicBuckets=True)`
**Verify:** `get_public_access_block` 回傳同樣四值

### Step 2.3 — Bucket policy（Task 3：website_security_policy.json + permissions.py）
**Command:** `s3.put_bucket_policy(Bucket, Policy=json)`；policy = Allow `s3:GetObject` on `arn:aws:s3:::{{BUCKET}}/*` 與 bucket ARN，Condition `IpAddress aws:SourceIp [{{IP}}/32]` + `DenyOneObjectIfRequestNotSigned`（report.html，`s3:authtype != REST-QUERY-STRING`）
**Verify:** `get_bucket_policy` 有 2 statements

### Step 2.4 — 上傳網站（Task 4：`aws s3 cp ../resources/website s3://{{BUCKET}}/ --recursive --cache-control "max-age=0"`）
**Command:** 對 `resources/website/**` 每檔 `upload_file(ExtraArgs={'CacheControl':'max-age=0','ContentType':<mimetypes>})`
**Verify:** 80 檔；`head_object('index.html').CacheControl == 'max-age=0'`

### Step 2.5 — 測試（Task 5）
**Command:** 本機無簽名 `GET https://{{BUCKET}}.s3.amazonaws.com/index.html`
**Expected:** HTTP 200（本機 IP 在白名單）；他處/IDE curl 會 AccessDenied（正確行為）

## 3. 驗收清單
- [ ] bucket `*-s3site` 存在，PAB 三勾一不勾
- [ ] bucket policy 2 statements、IP 條件
- [ ] `index.html` 等 80 檔，Cache-Control max-age=0
- [ ] 本機瀏覽器開 Object URL 看得到咖啡店網站
- [ ] Submit → 100/100

## 4. Known grader traps
- `BlockPublicPolicy` 必須 False，否則 put_bucket_policy 直接 AccessDenied
- IP 條件要用執行/瀏覽那台機器的**公網 IPv4**；走 NAT 或 IPv6 會 403（腳本已從 api.ipify.org 抓）
- 作業說 `<ip>/32` 不能寫 `0.0.0.0`
- 上傳要自己給 ContentType，否則 boto3 `upload_file` 預設 binary/octet-stream，瀏覽器會下載而不是顯示
- Task 6 純閱讀 code，不計分

## 5. Recommended model
- 複刻：Haiku 4.5（一條指令跑完；只需改 `INITIALS`）
