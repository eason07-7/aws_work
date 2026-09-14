# Lab 13.1 — Automating Code Deployments with a CI/CD Pipeline

**分數**：100/100
**時間**：約 45 分鐘（開頭等三個 stack ~12 分；每次 push 後 pipeline 跑 ~2 分）

## 這個 Lab 在做什麼

把咖啡店網站的程式碼放進 **CodeCommit** repo，用 **CodePipeline** 自動部署到 S3：以後只要 git push，網站就更新。先用一個 test.html 試三次（建立 → 改標題 → 換成整個網站），最後確認 CloudFront 上的檔案 cache-control 變成 pipeline 設的 `max-age=14`。
grader 看：repo `front_end_website` 與 commit 紀錄、pipeline `cafe_website_front_end_pipeline` 執行成功、S3/CloudFront 上是網站且 cache-control 正確。

## 開始前

- **Start Lab** → **AWS** 開 Console
- **CloudFormation** 三個 stack 都 **CREATE_COMPLETE**（~12 分）
- 記 IPv4；準備 email

## Task 1：準備 IDE

**Details → AWS: Show** → LabIDEURL / 密碼 → 登入 IDE → 終端：
```bash
wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/13-lab-ci-cd/code.zip -P /home/ec2-user/environment
unzip code.zip
chmod +x ./resources/setup.sh && ./resources/setup.sh
```
問 IP 貼 IPv4；跑幾分鐘後問 email 貼信箱。`aws --version`、`pip3 show boto3` 確認。IDE 留著。

## Task 2：建 CodeCommit repo

Console 搜 **CodeCommit → Create repository**：Name `front_end_website`、Description `Repository for the cafe website front end` → Create。
repo 頁 → **Create file**，貼：
```html
<!DOCTYPE html>
<html>
    <head>
    <title>Test page</title>
    </head>
    <body>
        <h1>
           This is a sample HTML page.
        </h1>
    </body>
</html>
```
下方：File name `test.html`、Author name 你的名字、Email 同 Task 1、Commit message `This is my first commit.` → **Commit changes**。
左側 **Commits** → 點那個 commit ID → test.html 區塊第 4 行滑到行號旁 **+** → 點留言圖示 → 輸入 `I must add a better title at some point.` → Save。

## Task 3：建 pipeline

IDE 打開 `resources/cafe_website_front_end_pipeline.json`：
- 兩個 `<FMI_1>` → 你的 account ID（終端 `aws sts get-caller-identity` 看 Account）
- `<FMI_2>` → 名字含 `s3bucket` 的 bucket（`aws s3 ls`）
存檔後：
```bash
cd ~/environment/resources
aws codepipeline create-pipeline --cli-input-json file://cafe_website_front_end_pipeline.json
```
（卡在 `:` 按 `q`；報錯就是 account ID 或 bucket 名打錯）
Console → **CodePipeline** → `cafe_website_front_end_pipeline` → Source、Deploy 兩格都變綠 Succeeded（第一次會自動跑）。
```bash
aws cloudfront list-distributions --query DistributionList.Items[0].DomainName --output text
```
瀏覽器開 `https://<那個 domain>/test.html` → "This is a sample HTML page." 分頁留著。

## Task 4：把 repo clone 到 IDE

CodeCommit → Repositories → front_end_website → Clone URL 欄 **Clone HTTPS (GRC)**（複製到剪貼簿，長得像 `codecommit::us-east-1://front_end_website`）。
IDE：
```bash
cd ~/environment
git clone codecommit::us-east-1://front_end_website
```
左側檔案樹出現 `front_end_website/test.html`。

## Task 5：用 IDE 改檔、commit、push

1. 左側打開 `front_end_website/test.html`，第 4 行 title 改成 `Best test page ever.` → 存檔（Ctrl+S）
2. 左邊欄的 **Source Control** 圖示（分叉那個）會出現數字 1
3. 點進 Source Control → Message 填 `Updated the title` → Commit 按鈕旁 **⌄** → **Commit & Push** → Yes
4. CodeCommit → Commits → 最新那筆 → 看到 `-` 紅行 `+` 綠行的 diff
5. 回 test.html 分頁重新整理幾次 → 分頁標題變 "Best test page ever."（pipeline 自動跑了）

## Task 6：換成真正的網站

1. 左側 `front_end_website/test.html` 右鍵 **Delete**
2. 終端：
   ```bash
   cd ~/environment
   cp -r ./resources/website/* front_end_website
   rm -r ./resources/website
   ```
3. Source Control → Message `Providing the website` → **Commit & Push** → Yes（檔案很多，會跑一下）
4. 等 pipeline 綠 → 瀏覽器把網址的 `/test.html` 拿掉 → 咖啡店網站
5. F12 → Network → 重新整理 → 點 `pastries.js` → Headers → Response Headers：`cache-control: max-age=14`（還是 0 就等幾秒再整理）

## 交作業

**Submit → Yes**。

## 會踩的坑

- `create-pipeline` 報 `RoleForCodepipeline` 或 bucket 找不到 → JSON 的 `<FMI_1>` 有**兩個**（roleArn 和 artifactStore），漏改一個就掛
- pipeline 每次 push 後要 1–2 分鐘才開始跑；網站沒變先看 CodePipeline 是不是還 In progress
- Task 4 的 clone 若問帳密 = 沒用 GRC 網址（要 `codecommit::us-east-1://...`，不是 https://git-codecommit...）
- Source Control 看不到變更 → 檔案沒存檔，或不是在 `front_end_website/` 資料夾裡改
- Commit & Push 找不到 → 按 Commit 旁邊的小箭頭 ⌄ 展開
- Task 6 `cp -r ./resources/website/*` 要在 `~/environment` 執行；`rm -r ./resources/website` 是刻意的（只留 repo 一份）
- 瀏覽器顯示舊頁面是 CloudFront 快取，多重新整理幾次或 Ctrl+F5
