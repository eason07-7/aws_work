# Lab 2.1 — Exploring AWS CloudShell and IDE

**分數**：100/100
**時間**：約 15 分鐘（作業寫 45 分鐘，大多是探索 UI）

## 這個 Lab 在做什麼

用兩種方式（CloudShell、VS Code IDE）操作同一個 S3 bucket：上傳一個 Python 檔、再抓回來跑、最後上傳一個 `index.html`。
**grader 只看 bucket 裡最後有沒有 `list-buckets.py` 和 `index.html` 這兩個檔案**，CloudShell / IDE 裡的探索動作不計分。

## 開始前

1. 按 **Start Lab**，等 `Lab status: ready`
2. 按 **AWS** 開 Console（記得允許彈出視窗）
3. 帳號裡只有一個預建的空 bucket，名字長得像 `c215460a...-samplebucket-xzbadyiixxyg`

## Task 1：CloudShell

1. Console 右上角點 **CloudShell** 圖示（終端機符號），等 1–2 分鐘出現提示字元
2. 確認 CLI 版本：
   ```bash
   aws --version
   ```
   看到 `aws-cli/2.x.x` 即可
3. 列 bucket：
   ```bash
   aws s3 ls
   ```
   把那個含 `samplebucket` 的名字**複製到記事本**，後面要用很多次
4. **Actions → Tabs layout → Split into columns** 開第二個終端（純體驗，不計分）
5. 把作業提供的 `list-buckets.py` 下載到電腦，再 **Actions → Files → Upload file** 傳上 CloudShell
   > 如果懶得下載，直接在 CloudShell 建檔也行：
   > ```bash
   > cat > list-buckets.py <<'EOF'
   > import boto3
   > session = boto3.Session()
   > s3_client = session.client('s3')
   > b = s3_client.list_buckets()
   > for item in b['Buckets']:
   >     print(item['Name'])
   > EOF
   > ```
6. 跑一下確認：
   ```bash
   python3 list-buckets.py
   ```
   會印出同一個 bucket 名
7. **上傳到 bucket（這一步計分）**：
   ```bash
   aws s3 cp list-buckets.py s3://<bucket-name>
   ```
   看到 `upload: ./list-buckets.py to s3://.../list-buckets.py`

## Task 2：VS Code IDE

1. 回到 Lab 說明頁，按 **Details → AWS: Show**，複製 **LabIDEURL** 和 **LabIDEPassword**
2. 新分頁開 LabIDEURL，貼密碼 → Submit
3. 下方 Bash 終端：
   ```bash
   aws s3 ls
   aws s3 cp s3://<bucket-name>/list-buckets.py .
   ```
   左側檔案樹會出現 `list-buckets.py`
4. 跑它：
   ```bash
   python3 list-buckets.py
   ```
   **會失敗** `ModuleNotFoundError: No module named 'boto3'`——這是作業預期的，接著裝：
   ```bash
   sudo pip3 install boto3
   python3 list-buckets.py
   ```
   這次會印出 bucket 名
5. 建 `index.html`：**☰ → File → New Text File**，內容貼
   ```html
   <body> Hello World. </body>
   ```
   **File → Save**，檔名 `index.html`，存在 `/home/ec2-user/environment/`
   > 或直接在終端：`echo '<body> Hello World. </body>' > index.html`
6. **上傳（這一步計分）**：
   ```bash
   aws s3 cp index.html s3://<bucket-name>/index.html
   ```

## 交作業

回 Lab 說明頁按 **Submit → Yes**，1–2 分鐘後看 Grades；要看細項按 **Details → View Submission Report**。

## 會踩的坑

- 作業文字寫 bucket 名含 `-sample-bucket-`，實際是 `-samplebucket-`（中間沒有連字號），照 `aws s3 ls` 印出來的為準
- `aws s3 cp` 目的地寫 `s3://<bucket-name>` 結尾不要多打東西；檔名會自動沿用
- IDE 第一次跑 Python 缺 boto3 是正常的，別在那裡卡住
- Appendix 的 `s3-permissions.py` 是給 Lab 3.1 用的，這裡不用碰
- 兩個檔案都在 bucket 裡才按 Submit；可以重複 Submit，以最後一次為準
