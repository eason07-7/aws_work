# Lab 6.1 — Developing REST APIs with Amazon API Gateway

**分數**：100/100
**時間**：約 40 分鐘

## 這個 Lab 在做什麼

用 Python（boto3）在 API Gateway 建一個 `ProductsApi`，裡面三個**假資料（MOCK）**端點：`GET /products`、`GET /products/on_offer`、`POST /create_report`。部署成 `prod` stage 後，把 Invoke URL 寫進網站的 `config.js` 上傳 S3，咖啡店網站就會改從 API 拿菜單。
grader 看：API 與三個 resource/method 存在、`prod` stage 有部署、S3 上的 `config.js` 指到 Invoke URL。Console 的 TEST 動作不計分，但做一下能幫你確認每步沒錯。

## 開始前

- **Start Lab** → ready → **AWS** 開 Console
- 到 [whatismyip.com](https://www.whatismyip.com/) 記下你的 **IPv4**（setup 腳本會問）

## Task 1：準備 IDE、部署網站

1. **Details → AWS: Show** → 複製 LabIDEURL / LabIDEPassword → 新分頁登入 IDE
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/04-lab-api/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x resources/setup.sh && resources/setup.sh
   ```
   跳出 `Please enter a valid IP address:` 時貼你的 IPv4 按 Enter。腳本會把網站傳到預建的 bucket（名字含 `s3bucket`）並套 IP 白名單 policy，最後印 `DONE`
3. 確認工具：
   ```bash
   aws --version
   pip3 show boto3
   ```
4. Console → S3 → 那個 `...-s3bucket-...` → Objects → `index.html` → 複製 **Object URL**，用瀏覽器開。Browse Pastries 的「on offer」預設顯示 **6 個**、「view all」很多個——記住這個數字，做完會變。
   （可選）開瀏覽器開發者工具 Console，會看到 main.js 說正在用 hardcoded data。**這個分頁留著。**

## Task 2：第一個端點 GET /products

1. IDE 開 `python_3/create_products_api.py`，第 3 行 `boto3.client('<FMI>', ...)` 的 `<FMI>` 改成 `apigateway`
2. 執行：
   ```bash
   cd python_3
   python3 create_products_api.py
   ```
   印 `DONE`
3. Console → **API Gateway** → **ProductsApi** → Resources → `/products` → **GET**。會看到 Method Request → Integration Request (MOCK) → Integration Response → Method Response 的流程圖
4. 下方 **TEST** 分頁 → 拉到底按 **Test** → Response body 是 3 個商品的 JSON、status 200

## Task 3：第二個端點 GET /products/on_offer

1. 先拿兩個 ID（在 Console `/products` GET 那頁的上方麵包屑）：
   - **api_id**：`APIs > ProductsApi (xxxxxxxxxx)` 括號裡那串
   - **parent_id**：選到 `/products` 那行時右側顯示的 **Resource ID**（注意是 `/products` 的，不是根 `/` 的）
   > 終端也能查：`aws apigateway get-rest-apis --query items[0].id --output text` 拿 api_id；`aws apigateway get-resources --rest-api-id <api_id>` 找 path 為 `/products` 的 id
2. 開 `python_3/create_on_offer_api.py`，`<FMI_1>` → api_id，`<FMI_2>` → parent_id（都要加引號）
3. `python3 create_on_offer_api.py` → `DONE`
4. Console 重新整理，`/products` 底下多了 `/on_offer`。點 GET → TEST → 回 1 個商品

## Task 4：第三個端點 POST /create_report

1. 開 `python_3/create_report_api.py`，第 5 行 `<FMI_1>` → api_id（引號）
   > 這支跟 products 的差別：POST 而不是 GET；建在根目錄下（`/create_report`），不在 `/products` 底下；method response 的三個 CORS header 是 `False`；mock 回 `{"msg_str": "report requested, check your phone shortly"}`
2. `python3 create_report_api.py` → `DONE`
3. Console 重新整理 → `/create_report` → POST → TEST → 看到那句 msg

## Task 5：部署

1. Console → ProductsApi → Resources → 選最上面的根 **/**
2. 右上 **Deploy API**：Stage = **\*New stage\***，Stage name 填 `prod`，其他留白 → **Deploy**
   （若跳 WAF 權限警告直接關掉）
3. 複製頁面上的 **Invoke URL**，長得像 `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod`

## Task 6：讓網站改打 API

1. IDE 開 `resources/website/config.js`，第 2 行的 `null` 換成 Invoke URL，**要加引號、結尾不要有 `/`**：
   ```js
   window.COFFEE_CONFIG = {
   API_GW_BASE_URL_STR: "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod",
   COGNITO_LOGIN_BASE_URL_STR: null
   };
   ```
2. 開 `python_3/update_config.py`，`<FMI_1>` → 你的 bucket 名（`aws s3 ls` 可查）
3. `python3 update_config.py` → `DONE`
4. 回網站分頁**重新整理**：
   - 點 **login** → `No API to call`（正常，之後 lab 才做）
   - Browse Pastries「on offer」現在只剩 **1 個**、「view all」**3 個**——這就是 API 的 mock 資料
   - 開發者工具 Console 會說正在用 API Gateway；若有 `/bean_products` 被 CORS 擋的訊息可忽略

## 交作業

**Submit → Yes**，看 Grades。

## 會踩的坑

- Task 3 的 `parent_id` 要拿 `/products` 的 Resource ID；拿成根 `/` 會把 `on_offer` 建錯層（變成 `/on_offer`）
- `<FMI>` 全部要加引號（它們是字串）
- 忘記 Deploy，或 Deploy 後又改了 API 沒重新 Deploy，網站會拿不到資料
- `config.js` 的 URL 結尾多一個 `/` 會讓前端請求變 `//products` 而失敗
- 網站重新整理後沒變，先確認 `update_config.py` 有印 `DONE`，再用 Ctrl+F5 強制重載（config.js 設了 max-age=0 但瀏覽器有時還是快取）
- 網站打不開（403）→ 你換了網路，IP 跟 setup.sh 時填的不同；重新跑 `resources/permissions.py` 前先改 `resources/website_security_policy.json` 裡的 IP
