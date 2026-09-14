# Lab 3.1 — Working with Amazon S3

**分數**：100/100
**時間**：約 30 分鐘

## 這個 Lab 在做什麼

在 VS Code IDE 裡用 AWS CLI 建一個 S3 bucket、設「只有我的 IP 能看」的 bucket policy、把咖啡店網站的 80 個檔案上傳上去，然後用瀏覽器打開驗證。
grader 檢查的是最終狀態：bucket 存在且名字以 `s3site` 結尾、Block Public Access 設定正確、bucket policy 有 IP 條件、網站檔案在裡面。

## 開始前

- 按 **Start Lab** → ready → **AWS** 開 Console
- 先去 [whatismyip.com](https://www.whatismyip.com/) 記下你電腦的 **IPv4**（後面 policy 要用）

## Task 1：連上 VS Code IDE、準備檔案

1. Lab 頁 **Details → AWS: Show**，複製 **LabIDEURL** / **LabIDEPassword**，新分頁開啟並登入
2. 下方 Bash 終端依序執行：
   ```bash
   sudo pip3 install boto3
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/02-lab-s3/code.zip -P /home/ec2-user/environment
   unzip code.zip
   aws --version
   ```
   解壓後左側會多出 `resources/`（網站檔）和 `python_3/`（`permissions.py`）

## Task 2：建 bucket

1. 命名規則：`<你的縮寫小寫>-<今天 YYYY-MM-DD>-s3site`，例如 `sm-2026-09-14-s3site`
   ```bash
   aws s3api create-bucket --bucket <bucket-name> --region us-east-1
   ```
   回傳 `{"Location": "/<bucket-name>"}`。**把 bucket 名記到記事本。**
2. Console → **S3** → 點進 bucket → **Permissions** → Block public access 區塊按 **Edit**：
   - 取消勾選最上面的 **Block all public access**
   - 再勾回以下三個：
     - ☑ Block public access to buckets and objects granted through **new** access control lists (ACLs)
     - ☑ Block public access to buckets and objects granted through **any** access control lists (ACLs)
     - ☑ Block public and cross-account access to buckets and objects through **any public bucket or access point policies**
   - 唯一**不勾**的是「Block public access to buckets and objects granted through **new** public bucket or access point policies」（沒留這個，下一步 policy 會被擋）
   - **Save changes** → 輸入 `confirm`

## Task 3：套 bucket policy

1. IDE 裡 **☰ → File → New File**，命名 `website_security_policy.json`（存在 `/home/ec2-user/environment/`），貼入：
   ```json
   {
       "Version": "2008-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": "*",
               "Action": "s3:GetObject",
               "Resource": [
                   "arn:aws:s3:::<bucket-name>/*",
                   "arn:aws:s3:::<bucket-name>"
               ],
               "Condition": {
                   "IpAddress": {
                       "aws:SourceIp": [
                           "<ip-address>/32"
                       ]
                   }
               }
           },
           {
               "Sid": "DenyOneObjectIfRequestNotSigned",
               "Effect": "Deny",
               "Principal": "*",
               "Action": "s3:GetObject",
               "Resource": "arn:aws:s3:::<bucket-name>/report.html",
               "Condition": {
                   "StringNotEquals": {
                       "s3:authtype": "REST-QUERY-STRING"
                   }
               }
           }
       ]
   }
   ```
   把 **三個** `<bucket-name>` 換成你的 bucket 名，`<ip-address>` 換成剛記的 IPv4（保留 `/32`）
2. 打開 `python_3/permissions.py`，把 `<bucket-name>` 換成你的 bucket 名
3. 執行：
   ```bash
   cd python_3
   python3 permissions.py
   ```
   看到 `DONE`。回 Console 的 Permissions 頁重新整理，Bucket policy 區塊會出現剛才的 JSON

## Task 4：上傳網站

還在 `python_3` 目錄：
```bash
aws s3 cp ../resources/website s3://<bucket-name>/ --recursive --cache-control "max-age=0"
```
會刷過 80 行 `upload: ...`

## Task 5：測試

1. Console → S3 → bucket → **Objects** → 點 `index.html` → 複製 **Object URL**（`https://<bucket-name>.s3.amazonaws.com/index.html`）
2. 用**你自己的電腦**瀏覽器開 → 看到咖啡店網站；點右上 **Login** 會跳 `No API to call`，正常
3. 從別的網路測應該被擋——在 IDE 終端：
   ```bash
   curl https://<bucket-name>.s3.amazonaws.com/index.html
   ```
   回 `AccessDenied` 才對（IDE 的 IP 不在白名單）

## Task 6：看程式碼

純閱讀 `resources/website/` 裡的 `index.html`、`scripts/config.js`、`scripts/pastries.js`、`all_products.json`，不計分。

## 交作業

Lab 頁 **Submit → Yes**，看 Grades。

## 會踩的坑

- Block Public Access 那四個勾**只能留一個不勾**（new public bucket policies）；全勾著 `permissions.py` 會 `AccessDenied`
- IP 必須是你**瀏覽網站那台機器的公網 IPv4**；手機熱點、學校 NAT 換過網路就會 403，重新查 IP 改 policy 再跑一次 `permissions.py` 即可
- 不能填 `0.0.0.0/0`——S3 會視為公開存取直接擋掉
- policy 裡三個 `<bucket-name>` 漏改一個就整份套不上（會回 `MalformedPolicy`）
- `--cache-control "max-age=0"` 別省略，grader 會看 object 的 Cache-Control
- 上傳前確認自己在 `python_3/` 裡，`../resources/website` 路徑才對
