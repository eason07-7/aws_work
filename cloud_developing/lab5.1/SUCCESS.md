# Lab 5.1 — Working with Amazon DynamoDB

**分數**：100/100（首刷 2026-09-14，全 boto3 自動化，無 🖐 MANUAL 步驟）

## 0. Prerequisites
- Learner Lab started；`<學號>/.env` 有有效 session_token；Region us-east-1
- 腳本會自動下載並解壓作業 `code.zip`
  來源：`https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/03-lab-dynamo/code.zip`

## 1. Placeholders
| Placeholder | 說明 | 範例 |
|---|---|---|
| {{STUDENT_ID}} | 此次執行的學號 | 112021134 |

（表名 `FoodProducts`、索引名 `special_GSI` 都是作業固定值，無需替換）

## 2. Step-by-step（boto3）

一鍵（約 2–5 分鐘，大多在等 GSI ACTIVE）：填憑證後 `python lab5_1.py`。

### Step 2.1 — 建表（Task 2：create_table.py）
**Command:** `resource.create_table(TableName='FoodProducts', KeySchema=[product_name HASH], AttributeDefinitions=[product_name S], ProvisionedThroughput 1/1)` → `wait_until_exists()`
**Verify:** `list_tables()` 含 `FoodProducts`（idempotent：已存在則沿用）

### Step 2.2 — put-item 系列（Task 3）
**Command:** 依序 `put_item` best cake / best pie / best pie（重複）/ best pie product_id=3333333333（覆寫）；再 `put_item(best cake, ConditionExpression='attribute_not_exists(product_name)')`
**Expected:** 最後一個 → `ConditionalCheckFailedException`（正確）

### Step 2.3 — conditional_put.py（Task 4）
**Command:** `put_item(apple pie a444 …, Condition attribute_not_exists)` → Done；同 key a555 → `ConditionalCheckFailedException`；`cherry pie` → Done

### Step 2.4 — batch（Task 5）
1. 清空（`scan` + `batch_writer.delete_item`）
2. `batch_writer(overwrite_by_pkeys=['product_name'])` 載 test.json 6 筆 → apple pie 最終 4495（last write wins）
3. 清空；`batch_writer()` 無 overwrite 載同資料 → `ValidationException: Provided list of item keys contains duplicates`，表 0 筆
4. `batch_writer()` 載 all_products.json 26 筆（欄位映射：`product_name_str→product_name`, `product_id_str→product_id`, `price_in_cents_int→price_in_cents`, `description_str→description`, `tag_str_arr→tags`, 可選 `special_int→special`）
**Verify:** `scan(Select='COUNT')` = 26

### Step 2.5 — 查詢（Task 6）
**Command:** 分頁 `table.scan()` → 26 items；`client.get_item(Key={'product_name':{'S':'chocolate cake'}})` → price 4095

### Step 2.6 — GSI（Task 7）
**Command:** `update_table(AttributeDefinitions=[special N], GlobalSecondaryIndexUpdates=[Create special_GSI, KeySchema special HASH, Projection ALL, 1/1])`；輪詢 `describe_table` 直到 `IndexStatus == ACTIVE`（實測 < 2 分鐘）
**Then:** `table.scan(IndexName='special_GSI', FilterExpression=Not(Attr('tags').contains('out of stock')))` → 6 筆

## 3. 驗收清單
- [ ] `FoodProducts` ACTIVE，PK `product_name`
- [ ] 26 筆 items
- [ ] `special_GSI` ACTIVE
- [ ] Submit → 100/100

## 4. Known grader traps
- 沒有陷阱，純最終狀態檢查；中間的 Console 操作（Explore items / Delete items）不計分，但腳本仍完整重現流程
- GSI 建立中不能再 `update_table`，重跑腳本前確認 GSI 已 ACTIVE
- `batch_writer` 沒有 `overwrite_by_pkeys` 時遇重複 key 整批失敗——這是作業要的行為，不要「修好」它

## 5. Recommended model
- 複刻：Haiku 4.5（一條指令跑完）
