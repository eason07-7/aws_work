# Lab 11.1 — Orchestrating Serverless Functions with Step Functions

**分數**：100/100
**時間**：約 90 分鐘（開頭等 CloudFormation ~20 分；Task 8 Lambda 掛 VPC 要等 ~5 分）

## 這個 Lab 在做什麼

做一條「按一下 API → 產生庫存報表 → 寄 email 給老闆」的流程：
API Gateway 的 `/create_report` 觸發 Step Functions state machine → Lambda `generateReportData` 去 Aurora 撈供應商和豆子 → 平行跑兩個 Lambda：`generateHTML` 把資料寫成 report.html 放 S3、`GeneratePresignedURL` 產生 2 分鐘有效的下載連結 → SNS topic `EmailReport` 把連結寄到你的信箱。
grader 看：SNS topic、state machine 的定義（有 SNS Publish、有 Parallel、Lambda 名稱對）、三個 Lambda、API 整合。**state machine 一定要用 Workflow Studio 拖出來（新版 JSONata 格式）**，見最後的坑。

## 開始前

- **Start Lab** → **AWS** 開 Console
- **CloudFormation** 等 Description `ACD_2.0` 的 stack **CREATE_COMPLETE**（~20 分）
- 準備一個收得到信的 email（學校信箱 `<學號>@live.asia.edu.tw`）
- 記 IPv4

## Task 1：準備 IDE

**Details → AWS: Show** 拿 LabIDEURL / LabIDEPassword（如果表格沒這兩列，重新整理頁面再開一次）→ 登入 IDE → 終端：
```bash
wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/11-lab-step/code.zip -P /home/ec2-user/environment
unzip code.zip
chmod +x ./resources/setup.sh && ./resources/setup.sh
```
問 IP 貼 IPv4，最後 `done` 前沒有 `An error occurred` 才算好。S3 → bucket → index.html Object URL 開得起來。

## Task 2：SNS topic + email

Console → **SNS → Topics → Create topic**：Standard、Name `EmailReport`、展開 **Access policy**：publish 選 **Everyone**、subscribe 選 **Everyone** → Create。
→ **Create subscription**：Protocol **Email**、Endpoint 你的信箱 → Create。
**去信箱**找 AWS Notifications 的信 → 點 **Confirm subscription**（沒確認後面信都收不到）。
回 topic → **Publish message**：Subject `Test`、Message `Hello! This is a test.` → Publish → 信箱收到。

## Task 3：第一版 state machine（只寄信）

先看 IAM → Roles → `RoleForStepToCreateAReport`（Step Functions 用，能 invoke Lambda）。
Console → **Step Functions → State machines → Create state machine** → 選 **Blank** → Select：
- 左側搜 `SNS` → 把 **Amazon SNS Publish** 拖到畫布 "Drag first state here"
- 右側 Topic 選 `EmailReport`；Message 保持 **Use state input as message**
- 上方 **Config**：State machine name `MyStateMachine`、Execution role **Choose an existing role** → `RoleForStepToCreateAReport`、Log level **ALL** → **Create**
- **Execute** → 輸入改成
  ```json
  { "presigned_url_str": "Testing that my email message works" }
  ```
  → Start execution → 綠色成功 → 信箱收到那句話

## Task 4：presigned URL + 第一個 Lambda

1. IDE 新檔案 `report.html`（存在 `/home/ec2-user/environment`），內容 `<output>Hello! This is some sample HTML.</output>`
2. 終端：
   ```bash
   bucket=$(aws s3api list-buckets --query "Buckets[].Name" | grep s3bucket | tr -d ',' | sed -e 's/"//g' | xargs)
   aws s3 cp report.html s3://$bucket/ --cache-control "max-age=0"
   ```
3. S3 → bucket → Permissions → 看 bucket policy 第二段：`report.html` 沒簽名不給讀。Objects → report.html → Object URL 開 → **AccessDenied**（正確）
4. ```bash
   aws s3 presign s3://$bucket/report.html --expires-in 30
   ```
   點開回傳的網址 → 看到那句 HTML；30 秒後重新整理 → AccessDenied
5. 看 IAM → `RoleForAllLambdas`（S3 + EC2 權限，三個 Lambda 都用它）
6. **Lambda → Create function**：Author from scratch、Name `GeneratePresignedURL`、Runtime **Python 3.9**（沒有就選最接近的 3.x）、Execution role → Use existing → `RoleForAllLambdas` → Create
7. Code 貼作業的 Python（`generate_presigned_url`，120 秒），第 3 行 `BUCKET_NAME_STR` 換成你的 bucket 名 → **Deploy** → **Test**（Event name `test1`）→ 回 presigned_url_str，貼瀏覽器能開
8. 回 **Step Functions → MyStateMachine → Edit**：搜 `Lambda` → 把 **AWS Lambda Invoke** 拖到 SNS Publish **上方**的箭頭：State name `GeneratePresignedURL`、Function name `GeneratePresignedURL:$LATEST`、Payload **No payload**、Next state `SNS Publish` → **Save**
9. **Execute**，輸入只留 `{}` → 成功 → 信箱收到 presigned URL（2 分鐘內開）

## Task 5：API 觸發 state machine

1. IAM → `RoleForAPIGWToTriggerStep` → 複製 **Role ARN**
2. **API Gateway → ProductsApi → /create_report → POST → Integration Request → Edit**：
   - Integration type **AWS Service**、Region us-east-1、Service **Step Functions**、HTTP method POST
   - Action Type **Use action name**、Action `StartExecution`
   - Execution role 貼 ARN；Content Handling **Passthrough**；Request body passthrough **When there are no templates defined**
   - Mapping Templates → Content-Type `application/json` → Method request passthrough → 內容換成
     ```json
     {
       "input": "$util.escapeJavaScript($input.json('$'))",
       "stateMachineArn": "arn:aws:states:us-east-1:<account-number>:stateMachine:MyStateMachine"
     }
     ```
   → Save
3. **Test** → 回 `executionArn`；信箱又收到一封
4. 根 **/** → **Deploy API** → prod → Deploy → 複製 Invoke URL
5. IDE：`curl -X POST <Invoke URL>/create_report` → 回 executionArn（若回舊的 mock 訊息，等幾秒再試）

## Task 6：generateHTML Lambda

**Lambda → Create function**：Name `generateHTML`、Runtime **Node.js 20.x**、role `RoleForAllLambdas` → Create。
Configuration → General configuration → Edit → Timeout **2 min** → Save。
Code 貼作業那段 JS，**兩處** `ACTUAL_BUCKET_NAME` 換 bucket 名（第 4 行、倒數第 8 行附近）→ Deploy → Test（Event `test2`，貼作業給的 my_json_arr JSON）→ 回 `Report published to S3`。

## Task 7：state machine 加平行

Step Functions → MyStateMachine → **Edit**：
- **Flow** 分頁 → 把 **Parallel** 拖到 Lambda Invoke 上方
- 把現有的 `GeneratePresignedURL` 拖進 Parallel **右邊**的 "Drop state here"
- **Actions** 分頁搜 Lambda → **Lambda Invoke** 拖進 Parallel **左邊**：State name `generateHTML`、Function `generateHTML:$LATEST`、Payload **Use state input as payload**、Next **Go to end**
- 點 Parallel 方塊 → State name `Process Report` → **Save**
- **Execute**，貼作業 Task 7 那份 JSON（Dave coffee suppliers）→ 成功 → 信箱收到 `[{"msg_str":...},{"presigned_url_str":...}]`

## Task 8：generateReportData Lambda（撈資料庫）

1. **Lambda → Create function**：Name `generateReportData`、Node.js 20.x、role `RoleForAllLambdas`；Configuration → Timeout **1 min**
2. IDE：根目錄右鍵 **New Folder** `lambda`，裡面新增 `index.js`（貼作業的 mysql2 程式）和 `package.json`：
   ```json
   { "dependencies": { "mysql2": "*", "@aws-sdk/client-s3": "*" }, "type": "module" }
   ```
   `index.js` 第 9 行 `DB-ENDPOINT` 換成 RDS → supplierdb 的 **Writer endpoint**（保留單引號）
3. 終端：
   ```bash
   cd ~/environment/lambda
   npm install
   zip -r ../lambda.zip *
   ```
   左側檔案樹 `lambda.zip` 右鍵 **Download** 到電腦
4. Lambda Console → generateReportData → Code → **Upload from → .zip file** → 選 lambda.zip → Save
5. **Configuration → VPC → Edit**：VPC `Lab IDE VPC`、Subnets 勾 us-east-1a 和 us-east-1b 兩個、Security group 選 **ClusterSecurityGroup** → Save，**等約 5 分鐘**變 Active
6. Test（Event `vpcAdjusted`，內容預設）→ 回 8 家供應商的 my_json_arr（逾時就再按一次）

## Task 9：接上最後一塊

Step Functions → MyStateMachine → Edit → 搜 Lambda → **Lambda Invoke** 拖到 Process Report **上方**：State name `getRealData`、Function `generateReportData:$LATEST`、Payload **No payload** → Save。
**Execute** 輸入 `{}` → 成功 → 信箱收到報表連結，開起來是漂亮的 HTML 報表。
再用 IDE `curl -X POST <Invoke URL>/create_report` 跑一次 → 信箱再收一封。

## 交作業

**Submit → Yes**。

## 會踩的坑

- **state machine 不要用 JSON 手打舊格式**：grader 讀的是新版 Workflow Studio 產生的 JSONata 格式（`Arguments` 欄位）。用 Console 拖拉就會是對的；如果你自己貼 ASL 用了 `Parameters`，grader 會說「SNS Publish action not found」然後直接當掉（實測）。在 Config 頁 Query language 選 **JSONata**
- SNS 訂閱沒去信箱 Confirm → 後面每個 Task 的信都收不到，state machine 卻顯示成功
- presigned URL 只有 120 秒，信來太慢就過期了——到 Lambda 程式改 `expiration_in_seconds` 再 Deploy
- Task 5 Request body passthrough 要選 "When there are no templates defined"；選 "Never" 的話 `curl -X POST` 會 415
- Task 6/8 Node 20 用 `export const handler` 是 ESM：Console 內建編輯器檔名是 `index.mjs`；自己 zip 的話要有 `package.json` 的 `"type": "module"`
- Task 8 沒設 VPC → Lambda 連不到 Aurora，Test 逾時；設了要等 5 分鐘
- Task 8 zip 要在 `lambda/` 資料夾**裡面** `zip -r ../lambda.zip *`，不然多一層目錄 Lambda 找不到 index.js
- 每次 Edit 完 state machine 要 **Save**，Execute 才會用新定義
