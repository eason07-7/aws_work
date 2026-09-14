# Lab 10.1 — Implementing a Messaging System Using Amazon SNS and Amazon SQS

**分數**：100/100
**時間**：約 60 分鐘（開頭等 CloudFormation ~20 分、Task 7 等死信佇列 ~3 分）

## 這個 Lab 在做什麼

用 SNS + SQS 幫咖啡豆供應商 app 做一條進貨訊息管線：供應商用 Python 把「supplier:豆種:數量」丟到 SNS FIFO topic → 轉進 SQS FIFO queue → Elastic Beanstalk 上的 node app 從 queue 拉訊息更新庫存；處理不了的訊息重試 5 次後進 dead-letter queue。
grader 看：兩個 FIFO queue 與其 policy / redrive、FIFO topic 與 policy、訂閱、DLQ 裡有 3 筆壞訊息、EB 的兩個環境變數、最後 beans 表的數量（209 / 306）。

## 開始前

- **Start Lab** → **AWS** 開 Console
- **CloudFormation → Stacks**，Description `ACD_2.0` 的 stack 等到 **CREATE_COMPLETE**（實測 20 分鐘上下，別急）
- 記 IPv4
- 開個記事本準備記：
  ```
  DeadLetterQueue QueueUrl:
  AWS Account ID:
  updated_beans.fifo QueueUrl:
  updated_beans.fifo QueueArn:
  updated_beans_sns.fifo TopicArn:
  ```

## Task 1：準備 IDE

1. **Details → AWS: Show** → LabIDEURL / LabIDEPassword → 登入 IDE
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/10-lab-sqs/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   問 IP 貼 IPv4。看倒數幾行沒有 `An error occurred` 才算成功（有就重跑一次）
3. `aws sts get-caller-identity` 記 **Account** 到記事本

## Task 2：死信佇列 DeadLetterQueue.fifo

```bash
cd ~/environment/resources/sqs-sns
aws sqs create-queue --queue-name DeadLetterQueue.fifo --attributes file://create-dlq.json
```
回傳的 QueueUrl 記下。
打開 `dlq-policy.json`，兩個 `<FMI_1>` 換成 account ID → 存檔：
```bash
aws sqs set-queue-attributes --queue-url "<DeadLetterQueue QueueUrl>" --attributes file://dlq-policy.json
```
沒輸出 = 成功。

## Task 3：主佇列 updated_beans.fifo

打開 `create-beans-queue.json`，`<FMI_1>` 換 account ID（這個檔的 RedrivePolicy 就是把失敗訊息導向 DLQ、最多收 5 次）→ 存檔：
```bash
aws sqs create-queue --queue-name updated_beans.fifo --attributes file://create-beans-queue.json
```
記 QueueUrl。
打開 `beans-queue-policy.json`，**八個** `<FMI_1>` 全換 account ID → 存檔：
```bash
aws sqs set-queue-attributes --queue-url "<updated_beans QueueUrl>" --attributes file://beans-queue-policy.json
aws sqs get-queue-attributes --queue-url "<updated_beans QueueUrl>" --attribute-names QueueArn
```
記 QueueArn。

## Task 4：SNS topic

```bash
aws sns create-topic --name updated_beans_sns.fifo --attributes DisplayName="updated beans sns",ContentBasedDeduplication="true",FifoTopic="true"
```
記 TopicArn。
打開 `beans-topic-policy.json`：`<FMI_1>` → TopicArn（一個），`<FMI_2>` → account ID（五個）→ 存檔：
```bash
aws sns set-topic-attributes --cli-input-json file://beans-topic-policy.json
```

## Task 5：把 queue 訂閱到 topic

```bash
aws sns subscribe --topic-arn "<TopicArn>" --protocol sqs --notification-endpoint "<QueueArn>"
```
回傳 SubscriptionArn。

## Task 6：測試發送

1. 打開 `send_beans_update.py`，`<FMI_1>` 換 account ID → 存檔
2. 看一眼 `beans_update_1.txt`：4 行，其中第 1 和第 3 行一模一樣（測 dedup 用）
3. ```bash
   python3 send_beans_update.py beans_update_1.txt
   ```
   印 4 個 dict；第 1 和第 3 個的 `SequenceNumber` 相同 = 重複被擋掉
4. Console → **Simple Queue Service** → `updated_beans.fifo` → **Send and receive messages** → **Poll for messages** → **3 筆**
5. 點 Size 最大那筆的 ID → Body 分頁：Message 是 `333333333:Unprocessable:0`，MessageAttributes 有 `inventory_alert: out_of_stock`
6. 全選 → **Delete** → 確認（若說 receipt handle expired，重新整理再 Poll 再刪）
7. 回 IDE：
   ```bash
   python3 send_beans_update.py beans_update_2.txt
   ```
   3 筆故意壞掉的訊息進了 queue，等下讓 app 去踩

## Task 7：讓 app 開始收訊息

1. 先看現況：Elastic Beanstalk → MyEnv → 點網址 → 網址後面加 `/beans`（第一次錯就等 10 秒重整）。記住 Supplier 3 Excelsa = **200**、Supplier 6 Arabica = **300**
2. EB → MyEnv → **Configuration** → Software 那格 **Edit** → Environment properties 加兩個：
   - `SQS_ENDPOINT` = `https://sqs.us-east-1.amazonaws.com/<account ID>/updated_beans.fifo`
   - `SQS_REGION` = `us-east-1`
   → **Apply**，等幾分鐘
3. 等的時候可以看 `resources/codebase_partner/app/sqs/consumer.js`，就是讀 `SQS_ENDPOINT` 然後 long-poll 的程式
4. app 起來後會一直嘗試處理那 3 筆壞訊息，每次失敗 30 秒後重出現，第 6 次就被丟進 DLQ。**大約 3 分鐘後**：SQS → `DeadLetterQueue.fifo` → Send and receive → Poll → **3 筆**
5. 最後送有效資料：
   ```bash
   python3 send_beans_update.py beans_update_3.txt
   ```
   （`3:Excelsa:9`、`6:Arabica:6`）
6. 網站 `/beans` 重新整理：Excelsa 變 **209**、Arabica 變 **306**

## 交作業

**Submit → Yes**。

## 會踩的坑

- stack 沒 CREATE_COMPLETE 就跑 setup.sh → 一串錯誤，重跑
- `<FMI_1>` 漏換（beans-queue-policy 有 8 個、topic policy 有 5+1 個）→ `set-queue-attributes` 報 InvalidAttributeValue 或 policy 無效
- `--queue-url` 要用**回傳的完整 URL**（含 account ID），不是 queue 名
- Task 6 第二次跑 `beans_update_1.txt` 會全部被 dedup 擋掉（5 分鐘內同內容），不要重跑
- Task 7 DLQ 沒東西 → 還沒等夠 3 分鐘，或 EB 環境變數的 URL 打錯（app log 會說 SQS endpoint not found）
- `/beans` 數量沒變 → app 還在處理壞訊息（DLQ 還沒 3 筆）就送了 batch 3；等 DLQ 齊了再送一次也行（數量會再加一次，變 218/312，grader 只看有沒有更新過）
- 記事本那幾個值後面會反覆用，一開始就記好省很多來回
