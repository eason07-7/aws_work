# Lab 5.1 — Working with Amazon DynamoDB

**分數**：100/100
**時間**：約 45 分鐘（作業寫 90 分鐘，主要是等 GSI）

## 這個 Lab 在做什麼

在 VS Code IDE 裡用 CLI 和 Python 建一張 `FoodProducts` 表，體驗「重複 key 會覆寫 → 用條件式擋掉 → 批次寫入的兩種行為」，最後載入 26 筆菜單、加一個 `special_GSI` 索引並查詢。
grader 看最終狀態：表存在（PK `product_name`）、26 筆資料、`special_GSI` 為 Active。中間的失敗步驟是刻意的教學，不會影響分數。

## 開始前

按 **Start Lab** → ready → **AWS** 開 Console。Console 先開 **DynamoDB → Tables**，這頁後面會一直用。

## Task 1：連上 IDE、準備檔案

1. **Details → AWS: Show** → 複製 LabIDEURL / LabIDEPassword → 新分頁登入 IDE
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/03-lab-dynamo/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   aws --version
   pip3 show boto3
   ```

## Task 2：建表

1. 開 `python_3/create_table.py`，`<FMI_1>` 改成 `FoodProducts`
2. 執行（會等表變 Active，看起來像卡住，等它印 `Done`）：
   ```bash
   cd python_3
   python3 create_table.py
   aws dynamodb list-tables --region us-east-1
   ```
3. Console 重新整理，`FoodProducts` 應為 **Active**

## Task 3：體驗 put-item 與條件式

檔案 `resources/not_an_existing_product.json` 一開始是 `best cake` / `676767676767`。

1. 第一次寫入：
   ```bash
   aws dynamodb put-item --table-name FoodProducts \
     --item file://../resources/not_an_existing_product.json --region us-east-1
   ```
   Console → 表 → **Explore table items** 看到 1 筆
2. 把 JSON 的 `product_name` 改成 `best pie`（product_id 不動），再跑同一條指令 → 2 筆
3. 什麼都不改再跑一次 → 還是 2 筆（同 key 被原樣覆寫）
4. 把 `product_id` 改成 `3333333333` 再跑 → best pie 的 product_id 被換掉（這就是不想要的行為）
5. 用條件式擋：
   ```bash
   aws dynamodb put-item --table-name FoodProducts \
     --item file://../resources/an_existing_product.json \
     --condition-expression "attribute_not_exists(product_name)" --region us-east-1
   ```
   **預期看到** `ConditionalCheckFailedException`——這是對的

## Task 4：用 SDK 做條件寫入

1. 開 `python_3/conditional_put.py`，把 7 個 `<FMI_x>` 依註解填：`FoodProducts` / `apple pie` / `a444` / `595` / `It is amazing!` / `whole pie` / `apple`
2. `python3 conditional_put.py` → `Done`，Console 多一筆 apple pie
3. 把 `a444` 改 `a555` 再跑 → 印錯誤或無變化（被條件擋住，正確）
4. 把 `apple pie` 改 `cherry pie` 再跑 → `Done`，多一筆 cherry pie

## Task 5：批次載入

1. **Console 清空表**：Explore table items → 全選 → **Actions → Delete item(s)** → 輸入 `Delete`
2. 開 `python_3/test_batch_put.py`：`<FMI_1>` → `FoodProducts`，`<FMI_2>` → `product_name`
3. `python3 test_batch_put.py` → 印 6 行 Adding；Console 看 apple pie 的價格是 **4495**（最後一筆贏，因為有 `overwrite_by_pkeys`）
4. **再次清空表**（同步驟 1）
5. 把第 12 行改成 `with table.batch_writer() as batch:`（拿掉 `overwrite_by_pkeys`），注意縮排
6. `python3 test_batch_put.py` → **預期噴** `ValidationException: Provided list of item keys contains duplicates`，表裡 0 筆（fail-fast，正確）
7. 開 `python_3/batch_put.py`，`<FMI>` → `FoodProducts`
8. `python3 batch_put.py` → 印 26 行 Adding；Console 看到 26 筆

## Task 6：查詢

1. `python_3/get_all_items.py`（**不是** resources 底下那個）：`<FMI_1>` → `FoodProducts`
   ```bash
   python3 get_all_items.py
   ```
   印出 26 筆 dict，價格是 `Decimal('...')` 格式，正常
2. `python_3/get_one_item.py`：`<FMI_1>` → `product_name`
   ```bash
   python3 get_one_item.py
   ```
   印出 chocolate cake 那筆（`{'N': '4095'}` 這種 DynamoDB 原生格式）

## Task 7：加 GSI

1. `python_3/add_gsi.py`：`<FMI_1>` → `HASH`
   ```bash
   python3 add_gsi.py
   ```
   印 `DONE`
2. Console → 表 → **Indexes** 分頁，等 `special_GSI` 從 Creating 變 **Active**（實測 1–2 分鐘，最多 5 分鐘）
3. `python_3/scan_with_filter.py`：`<FMI_1>` → `special_GSI`，`<FMI_2>` → `tags`
   ```bash
   python3 scan_with_filter.py
   ```
   印出 6 筆 special 商品（blueberry jelly doughnut、plain bagel、apple pie slice…）

## 交作業

確認 Indexes 已 Active 再按 **Submit → Yes**。

## 會踩的坑

- Task 3 / Task 5 的錯誤訊息是**作業要你看到的**，不要去「修好」它再繼續
- Task 5 兩次清空表都要做，否則 `batch_put.py` 載進來的資料會混到舊的 apple pie / cherry pie
- `test_batch_put.py` 拿掉 `overwrite_by_pkeys` 時保持 `with ... as batch:` 那行的縮排，Python 縮排錯會是 IndentationError 不是 ValidationException
- GSI 還在 Creating 時再跑一次 `add_gsi.py` 會報 `ResourceInUseException`，等就好
- 表在 Lab 一開始不該存在；若 `create_table.py` 報 `ResourceInUseException` 代表已建過，直接往下做即可
- Console 的 Explore table items 有時要按 **Run**/重新整理才會更新
