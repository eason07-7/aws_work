# Lab 7.1 — Creating Lambda Functions Using the AWS SDK for Python

**分數**：100/100
**時間**：約 60 分鐘

## 這個 Lab 在做什麼

把上一個 Lab 的三個假資料（MOCK）端點換成真的 Lambda：
- `get_all_products` — 掃 `FoodProducts` 表；如果 event 裡有 `path`，改掃 `special_GSI` 索引只回 on offer 商品
- `create_report` — 目前只回一句話（大寫 R 的 "Report processing…"，跟 mock 的小寫 r 區分）

然後在 API Gateway 把 `/products`、`/products/on_offer` 的 GET 和 `/create_report` 的 POST 從 Mock 改成呼叫 Lambda、補回 CORS、重新 Deploy。做完網站就是真的從 DynamoDB 讀菜單。
grader 看：兩個 Lambda 存在、三個 method 的 Integration 指向 Lambda、CORS 有開、`prod` 有重新部署。

## 開始前

- **Start Lab** → ready → **AWS** 開 Console
- 到 [whatismyipaddress.com](https://whatismyipaddress.com/) 記下 **IPv4**
- 帳號裡已預建：bucket（名含 `s3bucket`）、`FoodProducts` 表 + `special_GSI`（空的）、`ProductsApi`（三個 mock + `prod` stage）、IAM role `LambdaAccessToDynamoDB`

## Task 1：準備環境

1. **Details → AWS: Show** → LabIDEURL / LabIDEPassword → 登入 IDE
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/05-lab-lambda/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   問 IP 時貼 IPv4。腳本會上傳網站、套 policy、把 26 筆菜單塞進 DynamoDB
   ```bash
   pip3 show boto3
   ```
3. 逛一圈確認：S3 → bucket → `index.html` 的 Object URL 開得起來；DynamoDB → `FoodProducts` → Explore table items 有資料、Indexes 有 `special_GSI`；API Gateway → `ProductsApi` 三個 resource 各 TEST 一下都 200
4. API Gateway → **Stages → prod** → 複製 **Invoke URL**
5. IDE 開 `resources/website/config.js`，第 2 行 `null` 改成 `"<Invoke URL>"`（引號、結尾無 `/`）
6. `python_3/update_config.py` 的 `<FMI_1>` → bucket 名，然後：
   ```bash
   cd ~/environment/python_3
   python3 update_config.py
   ```
7. 重新整理網站：Browse Pastries 只剩 1 個（mock 資料）。**分頁留著。**

## Task 2：第一個 Lambda — get_all_products

1. 開 `python_3/get_all_products_code.py`：`<FMI_1>` → `FoodProducts`，`<FMI_2>` → `special_GSI`
2. 本地先跑：
   ```bash
   python3 get_all_products_code.py
   ```
   印 `running scan on table` + 26 筆
3. 體驗分支：第 12 行 `if offer_path_str is not None:` 暫時把 `not` 拿掉 → 再跑一次 → `running scan on index` + 6 筆。**看完把 `not` 加回去**
4. 最後一行 `print(lambda_handler({}, None))` 前面加 `#` 註解掉（部署後不能留）
5. Console → **IAM → Roles** → 搜 `LambdaAccessToDynamoDB` → 複製 **Role ARN**
6. 開 `python_3/get_all_products_wrapper.py`，第 5 行 `<FMI_1>` → 剛複製的 ARN（引號內）
7. 打包上傳、建 function：
   ```bash
   zip get_all_products_code.zip get_all_products_code.py
   aws s3 ls
   aws s3 cp get_all_products_code.zip s3://<bucket-name>
   python3 get_all_products_wrapper.py
   ```
   印 `DONE`
8. Console → **Lambda → get_all_products** → **Test**：
   - Event name `Products`，其他預設 → Save → Test → 回 26 筆
   - 再 **Configure test event → Create new event**，名稱 `onOffer`，內容改成
     ```json
     { "path": "on_offer" }
     ```
     Save → Test → 只回 6 筆，log 有 `running scan on index`

## Task 3：把兩個 GET 端點接到 Lambda

### /products
1. API Gateway → ProductsApi → `/products` → **GET** → 右側還寫 Mock Endpoint；TEST 一下確認還是 mock
2. **Integration Request → Edit**：Integration type = **Lambda Function**，Region `us-east-1`，Function `get_all_products` → **Save**（跳權限提示按確定）
3. 再 TEST → 回 26 筆真資料，但往下看 Response Headers **沒有** `Access-Control-Allow-Origin`——換整合把 CORS 弄掉了
4. 選著 `/products` → 上方 **Enable CORS**：勾 **Default 4XX**、**Default 5XX**、Access-Control-Allow-Methods 勾 **GET** → **Save**
5. 再 TEST → headers 出現 `Access-Control-Allow-Origin: *`

### /products/on_offer
6. `/products/on_offer` → GET → Integration Request → Edit → Lambda `get_all_products` → Save
7. 選著 `/on_offer` → Enable CORS（同上勾法）→ Save
8. TEST → headers 有 CORS，但 body 是 **26 筆**而不是 6 筆——因為 Lambda 沒收到 `path`
9. GET → **Integration Request → Edit** → 展開 **Mapping Templates → Add mapping template**：
   - Content-Type：`application/json`
   - Generate template 選 **Method request passthrough**，然後把內容整個換成
     ```json
     {
     "path": "$context.resourcePath"
       }
     ```
   → **Save**
10. TEST → 6 筆
11. Resources 選根 **/** → **Deploy API** → Stage 選 **prod** → Deploy

## Task 4：第二個 Lambda — create_report

1. IDE：
   ```bash
   python3 create_report_code.py
   ```
   印 `{'msg_str': 'Report processing, check your phone shortly'}`（注意大寫 R）
2. 最後一行 `print(lambda_handler(None, None))` 註解掉
3. `python_3/create_report_wrapper.py` 第 5 行 `<FMI_1>` → 同一個 Role ARN
4. ```bash
   zip create_report_code.zip create_report_code.py
   aws s3 cp create_report_code.zip s3://<bucket-name>
   python3 create_report_wrapper.py
   ```
5. Console → Lambda → `create_report` → Test：Event name `ReportTest` → Save → Test → 回大寫 R 那句

## Task 5：POST 端點接到 Lambda

1. API Gateway → `/create_report` → **POST** → TEST（還是小寫 r 的 mock）
2. Integration Request → Edit → Lambda `create_report` → Save
3. TEST → 大寫 R。這個不用開 CORS（之後 lab 才會從網站呼叫）
4. 根 **/** → **Deploy API** → prod → Deploy

## Task 6：用網站驗證

1. 回網站分頁重新整理（deploy 後可能要等 1–2 分鐘才會換過去，等一下再 Ctrl+F5）
2. on offer 預設 **6 個**；點 view all → **26 個**。看到就代表 CORS 也對了
3. 挑一個 on offer 商品記價格 → DynamoDB → FoodProducts → 點該商品的 `product_name` → 改 `price_in_cents` → Save → 網站重新整理，價格跟著變

## 交作業

**Submit → Yes**，看 Grades。

## 會踩的坑

- **Deploy 後網站沒變**：regional endpoint 要 1–2 分鐘才切到新 deployment，先等再懷疑設定；TEST 按鈕不受影響
- 換成 Lambda 整合後 CORS 一定會掉，`/products` 和 `/on_offer` 都要各自再 Enable CORS 一次
- `/on_offer` 沒加 mapping template 會回 26 筆而不是 6 筆；template 的 Content-Type 必須是 `application/json`
- Lambda 程式最後那行本地測試 `print(...)` 忘記註解 → 建好的 function 每次冷啟動都多跑一次 scan，onOffer 測試也會怪怪的
- Role ARN 要整串 `arn:aws:iam::<帳號>:role/LambdaAccessToDynamoDB`，不是 role 名稱
- 兩個 wrapper 用 `aws s3 ls | grep s3bucket` 自動找 bucket，所以 zip 一定要傳到那個含 `s3bucket` 的 bucket
- 網站 403 → 換過網路，IP 跟 setup 時不同；改 `resources/public_policy.json` 的 IP 後重跑 `python3 resources/permissions.py`
