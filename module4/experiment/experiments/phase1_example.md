# Phase 1 範例事件（給人類閱讀用）

> 這是**示範檔**，展示事件寫法的完整樣貌。
> 實際 Phase 1 封存時，這個檔案會被實際 Phase 1 的 `JOURNAL.md` 取代（rename）。
> 使用者可刪除此範例檔，或保留當參考。

---

### [2026-04-14 02:30] 事件 #2 — boto3 找不到 credentials

**現象**：`python -c "import boto3; s3.list_objects_v2(...)"` 報 `NoCredentialsError`。
**原因**：Python 子行程沒繼承 `.env`；`load_dotenv` 未在 `import boto3` 前呼叫。
**處理**：`download_from_s3.py` 開頭自寫 `load_dotenv_file()`，在 `import boto3` 前 `os.environ.setdefault(...)`。
**驗證**：同樣命令改跑 `python download_from_s3.py --dry-run` 成功列出 10 個 keys。
**數據/指標**：修正前 100% 失敗、修正後 100% 成功；載入 .env 增加 < 50 ms。
**量化驗收**：PASS（驗收條件：boto3 能連上 S3 不報 NoCredentialsError）
**可放入簡報的重點句**：
- boto3 憑證問題 80% 是環境變數載入時機不對，不是憑證本身錯
- 寫 AWS 腳本永遠把 `load_dotenv` 放在 `import boto3` **之前**
**對應輸出檔案**：`src/download_from_s3.py`、`.env.example`
**Tags**：#aws #boto3 #dotenv #env-var

---

### [2026-04-14 04:25] 事件 #5 — S3 下載到 3/22 斷線，部分資料

**現象**：下載到第 517 檔（3/22 13:00）崩潰 `AccessDenied`。
**原因**：AWS Learner Lab session 3.5 小時到期，`list_objects_v2` 仍可用但 `GetObject` 被拒。
**處理**：不等 Lab 重啟，直接用已下載的 3/1~3/21 共 21 天資料進下一階段；在清洗腳本明確排除 day=22。
**驗證**：手動跑 `head_object` 對 3/22/23/31 各抽一檔驗證都是 403；清洗結果行數比預期少 10 天相符。
**數據/指標**：下載成功 504 檔；3/22 部分 13/24 檔；總完整日 21 天。
**量化驗收**：WARN（驗收目標是整個 3 月，但 21 天統計意義充足）
**可放入簡報的重點句**：
- Learner Lab session 3.5 小時限制要當成「硬」邊界規劃
- 21 天資料對日均分析已夠，不必為 30 天完美而等
**對應輸出檔案**：`step0_s3_download/download_log.txt`、`step1_cleaning/clean_202603_21days.csv`
**Tags**：#aws #s3 #learner-lab #session-expiry #data-completeness

---

### 寫法重點

1. **現象要具體、可驗證**：「100% 失敗」比「一直錯」清楚。
2. **原因寫根因不寫表象**：「session 到期」比「權限錯誤」更有用。
3. **處理要能還原**：命令、檔名、行為都寫出來；下次可直接對著做。
4. **驗證回扣到現象**：「修正前 100% 失敗、修正後成功」對應一開始的現象。
5. **重點句是 PPT 金礦**：`harvest_to_ppt.py` 會 grep `**可放入簡報的重點句**`，直接抓進簡報骨架。
6. **Tags 要能被後續 grep**：`#aws` 比 `#amazon-web-services` 好；`INDEX.md` 會反向索引。
