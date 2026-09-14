# -*- coding: utf-8 -*-
"""
Lab 2.1 — Exploring AWS CloudShell and IDE — 一鍵完成（100/100）

用法：
    pip install boto3
    python lab2_1.py
先把 Learner Lab「Details → AWS: Show」的三組憑證填進下面。
"""
import boto3

AWS_ACCESS_KEY_ID = "PASTE_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_HERE"
AWS_SESSION_TOKEN = "PASTE_HERE"

LIST_BUCKETS_PY = """import boto3
session = boto3.Session()
s3_client = session.client('s3')
b = s3_client.list_buckets()
for item in b['Buckets']:
    print(item['Name'])
"""
INDEX_HTML = "<body> Hello World. </body>\n"

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1",
)
print("Account:", session.client("sts").get_caller_identity()["Account"])
s3 = session.client("s3")

# Step 2.1 — aws s3 ls；bucket 實名是 *-samplebucket-*（文件寫 -sample-bucket-）
buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
bucket = next(b for b in buckets if "samplebucket" in b.replace("-", ""))
print("bucket:", bucket)

# Step 2.2 — aws s3 cp list-buckets.py s3://<bucket>
s3.put_object(Bucket=bucket, Key="list-buckets.py", Body=LIST_BUCKETS_PY.encode())

# Step 2.3 — aws s3 cp s3://<bucket>/list-buckets.py .
assert "list_buckets" in s3.get_object(Bucket=bucket, Key="list-buckets.py")["Body"].read().decode()

# Step 2.4 — aws s3 cp index.html s3://<bucket>/index.html
s3.put_object(Bucket=bucket, Key="index.html", Body=INDEX_HTML.encode(), ContentType="text/html")

keys = [o["Key"] for o in s3.list_objects_v2(Bucket=bucket)["Contents"]]
print("objects:", keys)
assert {"list-buckets.py", "index.html"} <= set(keys)
print("DONE — 回 Lab 頁面按 Submit")
