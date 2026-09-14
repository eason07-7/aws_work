# -*- coding: utf-8 -*-
"""
Lab 5.1 — Working with Amazon DynamoDB — 一鍵完成（100/100）

用法：pip install boto3 && python lab5_1.py
先填三組憑證（Learner Lab「Details → AWS: Show」）。腳本自動下載 code.zip，
依作業順序重現 Task 2–7（含兩處刻意失敗），最終：FoodProducts 26 筆 + special_GSI ACTIVE。
"""
import boto3, json, time, io, zipfile, urllib.request
from pathlib import Path
from boto3.dynamodb.conditions import Attr, Not
from botocore.exceptions import ClientError

AWS_ACCESS_KEY_ID = "PASTE_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_HERE"
AWS_SESSION_TOKEN = "PASTE_HERE"

CODE_ZIP = "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/03-lab-dynamo/code.zip"
HERE = Path(__file__).resolve().parent
RES = HERE / "code" / "resources"
TABLE = "FoodProducts"


def _delete_all(table):
    items = table.scan(ProjectionExpression="product_name")["Items"]
    with table.batch_writer() as b:
        for it in items:
            b.delete_item(Key={"product_name": it["product_name"]})
    print(f"    (deleted {len(items)} items)")


def _expect_fail(fn, code):
    try:
        fn()
        print(f"    [WARN] expected {code} but succeeded")
    except ClientError as e:
        got = e.response["Error"]["Code"]
        print(f"    expected error: {got}" + ("" if got == code else f"  (!= {code})"))


def run(session, student_id):
    ddb = session.client("dynamodb")
    res = session.resource("dynamodb")

    # Task 2 — create_table.py
    existing = ddb.list_tables()["TableNames"]
    print(f"[Task2] existing tables: {existing}")
    if TABLE not in existing:
        res.create_table(
            TableName=TABLE,
            KeySchema=[{"AttributeName": "product_name", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "product_name", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
    res.Table(TABLE).wait_until_exists()
    print(f"[Task2] Done; list-tables = {ddb.list_tables()['TableNames']}")
    table = res.Table(TABLE)

    # Task 3 — put-item 系列（CLI 等價）
    ddb.put_item(TableName=TABLE, Item={"product_name": {"S": "best cake"}, "product_id": {"S": "676767676767"}})
    ddb.put_item(TableName=TABLE, Item={"product_name": {"S": "best pie"}, "product_id": {"S": "676767676767"}})
    ddb.put_item(TableName=TABLE, Item={"product_name": {"S": "best pie"}, "product_id": {"S": "676767676767"}})  # duplicate
    ddb.put_item(TableName=TABLE, Item={"product_name": {"S": "best pie"}, "product_id": {"S": "3333333333"}})   # overwrite
    print("[Task3] 4 put-item done; conditional put on existing key ->")
    _expect_fail(lambda: ddb.put_item(
        TableName=TABLE,
        Item={"product_name": {"S": "best cake"}, "product_id": {"S": "66662222"}},
        ConditionExpression="attribute_not_exists(product_name)"), "ConditionalCheckFailedException")
    ddb.scan(TableName=TABLE)  # Console「Scan → Run」等價

    # Task 4 — conditional_put.py x3
    def cput(name, pid):
        ddb.put_item(TableName=TABLE, Item={
            "product_name": {"S": name}, "product_id": {"S": pid},
            "price_in_cents": {"N": "595"}, "description": {"S": "It is amazing!"},
            "tags": {"L": [{"S": "whole pie"}, {"S": "apple"}]}},
            ConditionExpression="attribute_not_exists(product_name)")
    cput("apple pie", "a444"); print("[Task4] apple pie a444 Done")
    _expect_fail(lambda: cput("apple pie", "a555"), "ConditionalCheckFailedException")
    cput("cherry pie", "a555"); print("[Task4] cherry pie Done")
    ddb.scan(TableName=TABLE)

    # Task 5 — 清空 -> test_batch_put (overwrite) -> 清空 -> test_batch_put (fail) -> batch_put
    print("[Task5] delete all, test_batch_put with overwrite_by_pkeys")
    _delete_all(table)
    test = json.loads((RES / "test.json").read_text(encoding="utf-8"))
    with table.batch_writer(overwrite_by_pkeys=["product_name"]) as b:
        for f in test:
            b.put_item(Item={"product_name": f["product_name_str"], "price_in_cents": f["price_in_cents_int"]})
    ap = table.get_item(Key={"product_name": "apple pie"})["Item"]
    print(f"    apple pie after overwrite batch = {ap['price_in_cents']} (expect 4495)")
    print("[Task5] delete all, test_batch_put without overwrite -> expect ValidationException")
    _delete_all(table)

    def dup_batch():
        with table.batch_writer() as b:
            for f in test:
                b.put_item(Item={"product_name": f["product_name_str"], "price_in_cents": f["price_in_cents_int"]})
    _expect_fail(dup_batch, "ValidationException")
    print(f"    items now = {table.scan(Select='COUNT')['Count']} (expect 0)")

    foods = json.loads((RES / "website" / "all_products.json").read_text(encoding="utf-8"))["product_item_arr"]
    with table.batch_writer() as b:
        for f in foods:
            item = {"product_name": f["product_name_str"], "product_id": f["product_id_str"],
                    "price_in_cents": f["price_in_cents_int"], "description": f["description_str"],
                    "tags": f["tag_str_arr"]}
            if "special_int" in f:
                item["special"] = f["special_int"]
            b.put_item(Item=item)
    print(f"[Task5] batch_put loaded {len(foods)} items; table count = {table.scan(Select='COUNT')['Count']}")

    # Task 6 — get_all_items.py / get_one_item.py
    resp = table.scan(); data = resp["Items"]
    while resp.get("LastEvaluatedKey"):
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"]); data.extend(resp["Items"])
    print(f"[Task6] get_all_items -> {len(data)} items")
    one = ddb.get_item(TableName=TABLE, Key={"product_name": {"S": "chocolate cake"}})["Item"]
    print(f"[Task6] get_one_item chocolate cake -> {one['price_in_cents']}")

    # Task 7 — add_gsi.py -> wait ACTIVE -> scan_with_filter.py
    idx = [g["IndexName"] for g in ddb.describe_table(TableName=TABLE)["Table"].get("GlobalSecondaryIndexes", [])]
    if "special_GSI" not in idx:
        ddb.update_table(
            TableName=TABLE,
            AttributeDefinitions=[{"AttributeName": "special", "AttributeType": "N"}],
            GlobalSecondaryIndexUpdates=[{"Create": {
                "IndexName": "special_GSI",
                "KeySchema": [{"AttributeName": "special", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1}}}])
        print("[Task7] add_gsi DONE, waiting for ACTIVE ...")
    st = None
    for _ in range(60):
        g = ddb.describe_table(TableName=TABLE)["Table"].get("GlobalSecondaryIndexes", [])
        st = next((x["IndexStatus"] for x in g if x["IndexName"] == "special_GSI"), None)
        if st == "ACTIVE":
            break
        time.sleep(10)
    print(f"[Task7] special_GSI status = {st}")
    sp = table.scan(IndexName="special_GSI", FilterExpression=Not(Attr("tags").contains("out of stock")))["Items"]
    print(f"[Task7] scan_with_filter -> {len(sp)} specials: {[i['product_name'] for i in sp]}")

    t = ddb.describe_table(TableName=TABLE)["Table"]
    assert t["TableStatus"] == "ACTIVE" and st == "ACTIVE"
    print(f"[OK] Lab 5.1 done for {student_id}: table ACTIVE, {len(data)} items, GSI ACTIVE")

if __name__ == "__main__":
    if not (HERE / "code" / "resources" / "test.json").exists():
        zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(CODE_ZIP).read())).extractall(HERE / "code")
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            aws_session_token=AWS_SESSION_TOKEN, region_name="us-east-1")
    print("Account:", session.client("sts").get_caller_identity()["Account"])
    run(session, "me")
    print("DONE — 回 Lab 頁面按 Submit")
