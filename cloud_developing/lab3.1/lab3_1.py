# -*- coding: utf-8 -*-
"""
Lab 3.1 — Working with Amazon S3 — 一鍵完成（100/100）

用法：pip install boto3 && python lab3_1.py
先填三組憑證（Learner Lab「Details → AWS: Show」）與 INITIALS。
腳本自動：下載 code.zip → 建 bucket → PAB → IP 白名單 policy → 上傳網站(80 檔) → GET 測試。
"""
import boto3, json, io, zipfile, mimetypes, datetime, urllib.request
from pathlib import Path

AWS_ACCESS_KEY_ID = "PASTE_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_HERE"
AWS_SESSION_TOKEN = "PASTE_HERE"
INITIALS = "sm"          # 你的姓名縮寫小寫

CODE_ZIP = "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/02-lab-s3/code.zip"
HERE = Path(__file__).resolve().parent
WEBSITE = HERE / "code" / "resources" / "website"

session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        aws_session_token=AWS_SESSION_TOKEN, region_name="us-east-1")
print("Account:", session.client("sts").get_caller_identity()["Account"])
s3 = session.client("s3")

# Task 1 — code.zip
if not WEBSITE.exists():
    zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(CODE_ZIP).read())).extractall(HERE / "code")
ip = urllib.request.urlopen("https://api.ipify.org").read().decode().strip()
bucket = f"{INITIALS}-{datetime.date.today().isoformat()}-s3site"
print("bucket:", bucket, "| allowed ip:", ip)

# Task 2 — create bucket + public access block（三勾一不勾）
if bucket not in [b["Name"] for b in s3.list_buckets()["Buckets"]]:
    s3.create_bucket(Bucket=bucket)
s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
    "BlockPublicAcls": True, "IgnorePublicAcls": True,
    "BlockPublicPolicy": False, "RestrictPublicBuckets": True})

# Task 3 — bucket policy（= website_security_policy.json + permissions.py）
policy = {"Version": "2008-10-17", "Statement": [
    {"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject",
     "Resource": [f"arn:aws:s3:::{bucket}/*", f"arn:aws:s3:::{bucket}"],
     "Condition": {"IpAddress": {"aws:SourceIp": [f"{ip}/32"]}}},
    {"Sid": "DenyOneObjectIfRequestNotSigned", "Effect": "Deny", "Principal": "*",
     "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{bucket}/report.html",
     "Condition": {"StringNotEquals": {"s3:authtype": "REST-QUERY-STRING"}}}]}
s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
print("DONE (policy)")

# Task 4 — aws s3 cp ../resources/website s3://<bucket>/ --recursive --cache-control "max-age=0"
n = 0
for f in WEBSITE.rglob("*"):
    if f.is_file():
        s3.upload_file(str(f), bucket, f.relative_to(WEBSITE).as_posix(),
                       ExtraArgs={"CacheControl": "max-age=0",
                                  "ContentType": mimetypes.guess_type(f.name)[0] or "binary/octet-stream"})
        n += 1
print(f"uploaded {n} files")

# Task 5 — 本機 GET 應 200
url = f"https://{bucket}.s3.amazonaws.com/index.html"
try:
    print("GET", url, "->", urllib.request.urlopen(url).getcode())
except urllib.error.HTTPError as e:
    print("GET", url, "->", e.code, "(檢查 IP 是否與瀏覽機器一致)")
print("DONE — 回 Lab 頁面按 Submit")
