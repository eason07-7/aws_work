# 常見問題與排查紀錄（Troubleshooting）

AWS Academy Cloud Developing 的 lab 跑在 Vocareum（Learner Lab）上。有些問題跟作業內容無關，而是平台本身的限制或 AWS 環境的變動。作業說明不會提到，卡住時也很難自己查出原因。

這份文件整理我們在做 lab 時實際遇到、也實際解決的問題。每條依照 **症狀 → 怎麼查出來 → 根因 → 解法** 的順序寫，希望你遇到時不用從頭查起。

> 以上皆為 **2026-09** 的實測結果。平台和 AWS 服務會持續變動，看到的畫面或版本號可能已經不同。

---

## 快速索引

依照你看到的錯誤訊息找：

| 你看到的狀況 | 條目 |
|---|---|
| 按 Submit 顯示 `Submit already in progress` / `Operation failed`，一直交不出去 | [A1](#a1-submit-一直失敗already-in-progress--504) |
| Lab 頁面的 Details 裡找不到 IDE 網址或密碼 | [A2](#a2-找不到-vs-code-ide-的網址和密碼) |
| IDE 登入頁一直說密碼錯誤 | [A3](#a3-ide-密碼正確卻一直登不進去) |
| `Lab is in CREATE_FAILED state` | [A4](#a4-lab-顯示-create_failed) |
| 重開 lab 後出現 `belongs to a different VPC` | [A5](#a5-重開-lab-後出現-belongs-to-a-different-vpc) |
| 評分顯示 `SecretsErrorException ... wasn't found` | [A6](#a6-評分顯示-secret-wasnt-found但-secret-明明存在) |
| Elastic Beanstalk 找不到作業指定的 Amazon Linux 2 Docker 平台 | [B1](#b1-elastic-beanstalk-找不到-amazon-linux-2-的-docker-平台) |
| 建 Aurora 時作業指定的引擎版本不能選 | [B2](#b2-作業指定的-aurora-引擎版本不存在) |
| S3 bucket 名稱已被使用 | [B3](#b3-s3-bucket-名稱被佔用) |
| Lab 2.1：`PROBLEM: The S3 bucket is empty` | [C1](#c1-lab-21評分說-bucket-是空的) |
| Lab 5.1：DynamoDB 都做完了卻拿不到分 | [C2](#c2-lab-51dynamodb-都做了但分數是-0) |
| Lab 7.1：API 部署後測試還是舊的回應 | [C3](#c3-lab-71api-部署後測試還是舊的結果) |
| Lab 8.1：匯入 MySQL 資料失敗 | [C4](#c4-lab-81mysql-容器說-ready-了匯入卻失敗) |
| Lab 8.2：`Unable to connect to the coffee database` | [C5](#c5-lab-82評分說-unable-to-connect-to-the-coffee-database) |
| Lab 9.2：建 WAF 時出現 `WAFUnavailableEntityException` | [C6](#c6-lab-92建-waf-時說-entity-不可用) |
| Lab 11.1：`An SNS Publish action using the EmailReport topic was not found` | [C7](#c7-lab-111評分說找不到-sns-publish) |
| Lab 9.1：評分到最後一步崩潰，Task 8B 沒分，`Name or service not known` | [C8](#c8-lab-91評分最後一步崩潰task-8b-沒分name-or-service-not-known) |

---

## A. 平台（Vocareum / Learner Lab）

### A1. Submit 一直失敗（already in progress / 504）

**症狀**

- 按 Submit 後跳出 `Submit already in progress. Please wait` 和 `Operation failed. Please try again`
- 重新整理、換瀏覽器、End Lab 再 Start Lab 都沒用
- Grades 面板一直顯示 `Your assignment has not been graded yet`
- 但你在 AWS 裡做的東西都是對的

**怎麼查出來的**

1. **不要只看前端的錯誤提示，要看實際的網路請求。** lab 畫面是嵌在課程頁裡的 **iframe**（`labs.vocareum.com`，跟外層頁面不同網域）。在 DevTools 的 Network 面板找到 Submit 對應的請求：
   ```
   POST https://labs.vocareum.com/util/vcput.php?...&a=submitAssignmentStep&submitscript=1...
   → 504 Gateway Timeout，Waiting for server response 等了 1 分鐘
   ```
   回應內容是 Cloudflare 的錯誤頁（Gateway time-out）。
2. **這代表什麼**：Submit 是**同步請求**，伺服器要處理完才會回應。它等滿 1 分鐘才回 504，而不是立刻被擋下的 403，所以請求確實送到了 Vocareum，只是伺服器沒在前端 Cloudflare 的 60 秒上限內處理完。第一次逾時後，那筆工作在後端還卡著，所以之後再按都顯示 already in progress。
3. **伺服器在忙什麼**：打開 lab 內建的 terminal（Launch Terminal），量家目錄：
   ```bash
   pwd                                    # /mnt/vocwork*/work/<你的使用者>/.../work
   find ~ -xdev -type f | wc -l           # 檔案數
   du -sh ~/* ~/.[!.]* | sort -h | tail   # 看哪個資料夾最大
   ```
   我們量到 **403 MB、9944 個檔案**，其中 `~/environment/aws/` 佔 272 MB（7562 個檔案）、`~/environment/awscliv2.zip` 佔 71 MB。

**根因**

- **Vocareum terminal 的家目錄 `~`，就是 Submit 時要打包的提交目錄。**
- 作業的 Task 1 要你在 **VS Code IDE**（另一台 EC2）裡跑 `setup.sh`。如果你在 **Vocareum 自己的 terminal** 裡跑了，它會把 AWS CLI 安裝包下載並解壓到提交目錄裡，而且腳本不會清掉解壓出來的 `aws/`。
- Submit 時，Vocareum 要先把整個提交目錄打包完才開始評分。近一萬個檔案、放在網路掛載的磁碟上，打包就超過 60 秒 → 504。

**解法**

在 Vocareum terminal 裡刪掉安裝程式（這些跟評分無關，lab 本身的 `code.zip`、`resources/` 不要動）：
```bash
rm -rf ~/environment/aws ~/environment/awscliv2.zip ~/.cache
du -sh ~        # 確認變小了
```
接著**等幾分鐘**，讓之前卡住的提交工作結束（Network 裡 `vcput.php?a=chkResubmit` 回 `status:done` 就代表可以交了），然後再按一次 Submit。

| | 提交目錄 | 結果 |
|---|---|---|
| 清理前 | 403 MB / 9944 個檔案 | 超過 60 秒 → 504 |
| 清理後 | 45 MB / 2353 個檔案 | 約 22 秒 → 滿分 |

**預防**：作業說「在 VS Code IDE 的 terminal 執行」的指令，就在 **IDE** 裡跑，不要在 lab 頁面右邊那個 terminal 跑。兩個長得很像，但後者是提交目錄。

---

### A2. 找不到 VS Code IDE 的網址和密碼

**症狀**：作業叫你到 `Details → AWS: Show` 複製 `LabIDEURL` 和 `LabIDEPassword`，但新版頁面上沒有。

**解法**：這兩個值都在 CloudFormation 的輸出裡。

1. 開 AWS Console → **CloudFormation → Stacks**
2. 找名稱裡含 `VSCodeStack` 的 stack，或描述是 `ACD_2.0`、`ACDv2 ...` 的主 stack
3. 打開 **Outputs** 分頁：
   - `LabWorkspaceURL` / `LabWorkspacePassword`，或
   - `LabIDEURL` / `LabIDEPassword`
   - 有些 lab 的網址本身帶 `?tkn=...`，直接點開就能進去，不需要密碼

> 如果 stack 還在 `CREATE_IN_PROGRESS`，Outputs 會是空的，等它變成 `CREATE_COMPLETE` 再看。

---

### A3. IDE 密碼正確卻一直登不進去

**症狀**：用上面查到的密碼登入 code-server，一直被拒絕，其他同學用同樣方法都沒問題。

**我們試過的**

- 確認 Outputs 裡的密碼，跟 IDE 開機腳本實際寫入的值一致
- 在 EC2 把 IDE instance 重開機 → **沒用**
- 想從 API 直接進去看設定 → 被擋（見下方補充）

**解法**：**End Lab → 等它結束 → Start Lab**，讓環境重建一台新的 IDE。新 IDE 的密碼就正常了。根因我們沒能確認。

**補充**：Learner Lab 的 `voclabs` 角色會擋掉 `ssm:SendCommand`、`ssm:StartSession` 和 EC2 Instance Connect，所以沒辦法從外部取得 IDE 的 shell 來查。能進 IDE 的方式只有網頁版 terminal。

---

### A4. Lab 顯示 CREATE_FAILED

**症狀**：
```
Lab status: failed. Lab is in CREATE_FAILED state, so this lab is now set to be
deleted which can take a few minutes. Please wait for it to complete to do the start lab again.
```

**解法**：照訊息說的做：**等它自動刪除完**（幾分鐘），再按 Start Lab。還在刪除時按 Start Lab 會失敗。

**注意**：重開後 **AWS 憑證會全部換新**。如果你有在本機用 AWS CLI 或 SDK，記得更新 `aws configure` 或 credentials，否則會連到已經不存在的舊環境。

---

### A5. 重開 lab 後出現 belongs to a different VPC

**症狀**（Lab 9.1 建 ElastiCache 時遇到）：
```
InvalidParameterCombination: Subnet group [elasticachesubnetgroup] belongs to a different VPC
```

**根因**：lab 重開後，**VPC 和子網路都換了新的**，但你上一輪建的部分資源（例如 ElastiCache 的 subnet group）還留在帳號裡，而且綁的是**舊 VPC**。建新叢集時沿用了這個舊的 subnet group，就對不上。

**解法**：刪掉舊的 subnet group，用**目前 VPC** 的子網路重建一個同名的，再建叢集。

**通則**：lab 重開後，如果遇到「資源已存在」或「VPC 不符」，先檢查是不是上一輪留下的東西。

---

### A6. 評分顯示 secret wasn't found，但 secret 明明存在

**症狀**（Lab 9.1）：評分前幾項通過，接著出現
```
SecretsErrorException ... The secret arn:aws:secretsmanager:...:secret:rds-db-credentials/... wasn't found.
```
但到 Secrets Manager 看，這個 secret 確實存在。

**我們查到的**：這個 secret 的建立時間，只比評分執行早了 **2 秒**。事後用 RDS Data API 帶這個 secret 查詢，已經可以正常通過驗證。

**判斷與解法**：這是 Secrets Manager 還沒同步完成造成的時間差。**等幾分鐘再 Submit 一次**就好，不需要改任何東西。

---

### A7. Submit 立刻失敗：`cp: cannot stat .../.aws/credentials` + `except HTTPError, URLError:` SyntaxError

**症狀**（Lab 8.2，2026-10-27）：按 Submit 後幾秒就結束，輸出：

```
cp: cannot stat '/mnt/vocwork2/grader/.../work/.aws/credentials': No such file or directory
Traceback (most recent call last):
  File "/mnt/ro/voccontent2/gradinglib/eee_C_XXXXXXX/.../grade.py", line 14, in
    from commands.linux import LinuxRequests
  File ".../lib/grading_common/commands/linux.py", line 25
    except HTTPError, URLError:
SyntaxError: invalid syntax
Back in submit.sh...
end
```

**性質**：這是**平台（Vocareum / 課程評分庫）端的問題，學生端無法修正**。

**為什麼**：

- `except HTTPError, URLError:` 是 **Python 2 專屬語法**；`grade.py` 第 14 行**無條件 import**，所以在 import 階段就 `SyntaxError`，早於任何作業檢查
- 該檔在 `/mnt/ro/voccontent2/...`（**唯讀的課程評分庫**），學生改不了
- 合理推測：評分 runtime 已升為 Python 3，但課程的 `gradinglib` 仍是 Python 2

**與 `cp ... .aws/credentials` 的關係**：那是另一件事（Vocareum 家目錄只有 `config` 沒有 `credentials`，目錄還是 555），但**即使補上，第 14 行的 SyntaxError 照樣讓 grade.py 立刻結束**。不要在這上面浪費時間。

**先排除的三件事**（都做過）：

1. `du -sh ~` = 36K、5 個檔案 → **不是** A1 那種打包逾時
2. Chrome / Edge 都試過，錯誤逐字相同 → 不是瀏覽器
3. AWS 端 33 項驗收全過 → 不是作業沒做完

**解法**：帶證據報助教／講師，請平台方確認評分庫版本或改人工評分。證據清單：

- 上述錯誤原文（含 `grade.py` 行號與 `linux.py` 第 25 行）
- `ls -la ~/.aws`（只有 config、目錄 555）
- `du -sh ~`（36K，排除檔案太大）
- AWS 端資源截圖與驗收表
- 補充：**同一份作業 2026-09-14 可正常評分滿分**，2026-10-27 起每次都卡在同一行 → 屬平台改版造成的回歸

---

## B. AWS 服務版本變動

### B1. Elastic Beanstalk 找不到 Amazon Linux 2 的 Docker 平台

**症狀**（Lab 8.2）：作業要選 `Docker running on 64bit Amazon Linux 2`，但清單裡沒有。

**原因**：AWS 已經下架 Amazon Linux 2 的 Docker 平台，現在只剩 **Amazon Linux 2023**。

**解法**：直接選 `64bit Amazon Linux 2023 ... running Docker`。我們實測作業附的 `Dockerrun.aws.json`（v1 格式）在 AL2023 上照樣能部署，其他步驟不用改。

### B2. 作業指定的 Aurora 引擎版本不存在

**症狀**（Lab 8.2）：選作業寫的 Aurora MySQL `3.07.0` 會出現 `InvalidParameterCombination`，或者清單裡根本沒有這個版本。

**解法**：改選最接近的較新版本。我們用的是 `8.0.mysql_aurora.3.08.0`，評分正常。

### B3. S3 bucket 名稱被佔用

**症狀**（Lab 3.1 等）：`BucketAlreadyExists`。

**原因**：S3 bucket 名稱是**全球唯一**的。作業範例的命名方式很多人會用到一樣的名字。

**解法**：在名稱裡加上自己的識別字，例如姓名縮寫加日期或學號，名稱格式照作業要求就好。

---

## C. 各 Lab 評分陷阱

### C1. Lab 2.1：評分說 bucket 是空的

**症狀**：`Testing Report - PROBLEM: The S3 bucket is empty.`

**原因**（我們遇過兩種）：

1. **上傳還沒完成就按了 Submit**
2. **你操作的 AWS 帳號不是這個 lab 的**：例如本機的 AWS 憑證還是舊的，檔案其實傳到了另一個帳號

**解法**：到這個 lab 的 AWS Console 確認 bucket 裡真的有檔案，再按 Submit。

### C2. Lab 5.1：DynamoDB 都做了，但分數是 0

**原因**：評分只看**最終狀態**：`FoodProducts` 表是 ACTIVE、裡面**剛好 26 筆**資料、`special_GSI` 是 ACTIVE。Task 5 要求**批次載入前先清空整張表**。如果漏了這步，Task 3 留下的 `best cake`、`best pie` 會殘留，變成 **28 筆**，就拿不到分。

**解法**：確認表裡剛好 26 筆（可以在 Console 用 Scan 看 Items returned），多出來的刪掉。

**另一個坑**：在一個**已經做過一次**的環境重做 Task 4，會因為 `apple pie` 已經存在，讓條件寫入出錯。這是正常現象，先清空表再照順序重做即可。

> 如果 26 筆都對卻交不出去，請看 [A1](#a1-submit-一直失敗already-in-progress--504)。

### C3. Lab 7.1：API 部署後，測試還是舊的結果

**原因**：API Gateway 部署需要一點時間才會生效。剛部署完就測，可能還會拿到舊版的回應（例如 mock 的資料）。

**解法**：部署後等 1 到 3 分鐘再測。

### C4. Lab 8.1：MySQL 容器說 ready 了，匯入卻失敗

**原因**：MySQL 容器第一次啟動時會先跑一個**暫時的初始化伺服器**，它也會印出 `ready for connections`。這時候去匯入資料，會在它關閉、切換成正式伺服器的過程中失敗。

**解法**：等 log 出現**第二次**、而且帶 port 的那行再匯入：
```bash
docker logs mysql_1 2>&1 | grep "ready for connections"
# 要看到 ... ready for connections ... port: 3306
```

### C5. Lab 8.2：評分說 Unable to connect to the coffee database

**症狀**：資料都匯入正確，評分卻說連不上 coffee database。

**原因**：評分腳本是透過 RDS Data API 連資料庫，而它用的是 **RDS Query Editor 連線時建立的那個 Secrets Manager secret**，名稱格式是 `rds-db-credentials/<叢集資源 ID>/<使用者>/<時間戳>`。如果你不是透過 Query Editor 連過資料庫，就不會有這個 secret，評分就連不上。

**解法**：到 RDS Console 的 **Query Editor**，選擇用新的資料庫帳密連線到叢集，它會自動建立這個 secret。之後再 Submit。

### C6. Lab 9.2：建 WAF 時說 entity 不可用

**症狀**：剛建好 IP set 或 Web ACL，馬上建下一個或做關聯時，出現 `WAFUnavailableEntityException`。

**解法**：WAF 資源建立後要幾秒鐘才能使用，**等一下再試**就好。

### C7. Lab 11.1：評分說找不到 SNS Publish

**症狀**：
```
An SNS Publish action using the EmailReport topic was not found
```
（評分腳本接著可能出現 `KeyError: 'Arguments'`）

**原因**：評分腳本讀的是 **JSONata** 格式的 state machine 定義（使用 `Arguments` 欄位）。如果你把 state machine 改成舊的 **JSONPath** 格式（使用 `Parameters` 欄位），評分就讀不到。

**解法**：用 Step Functions Workflow Studio **預設的 JSONata** 格式建立，不要切換成 JSONPath。

---

### C8. Lab 9.1：評分最後一步崩潰，Task 8B 沒分（`Name or service not known`）

**症狀**：Grades 顯示 `Total score 35/40`，其他項都 5/5，只有 `[TASK 8B] Updated Docker application` 是 `-/5`。Submit 的輸出前面幾項都是 `Testing report - ... configured correctly`，最後崩潰：

```
File ".../grade.py", line 245, in main
    html = urllib.request.urlopen(request_url, context=ctx).read()
...
socket.gaierror: [Errno -2] Name or service not known
urllib.error.URLError: <urlopen error [Errno -2] Name or service not known>
```

**怎麼查出來的**

1. 前面的檢查都過，代表 AWS 端的作業是對的；崩潰點是評分程式要**抓一個網頁**，而那個**主機名稱解析失敗**。所以重點是：評分程式抓的是哪個名稱？
2. 盤點帳號裡所有會被當成網址的名稱，逐一測試能不能解析。結果：**有兩個叫 `MyEnv` 的 EB 環境，其中一個是 `Terminated`，它的網址解析不了**。
3. 用評分程式最可能的幾種呼叫方式列環境清單（什麼參數都不給、只給名稱、只給應用程式名稱），**三種都會回傳那個已終止的環境**；只有加了 `IncludeDeleted=False` 才看不到它。
4. 那個舊環境的終止時間是在你這次 lab 啟動**之前**（是帳號上一位使用者留下、平台回收時終止的）。EB 會把已終止環境的紀錄保留**約 1 小時**才從清單消失，實測約 60 分鐘。

**根因（有信心的部分與推論的部分）**

- **確證**：舊的已終止環境在預設清單裡、它的網址解析不了、約 1 小時後它從清單消失
- **確證**：它消失後，**沒有改動任何 AWS 資源**，重新 Submit 就拿到 `40/40`
- **推論**：評分程式實際取到了舊環境的網址。我們看不到評分程式的 `request_url`，所以這一步沒辦法 100% 證明，但上面幾點使它非常可能

**解法**：不用改任何東西，**等舊紀錄消失再重新 Submit**。在 CloudShell 確認：

```bash
aws elasticbeanstalk describe-environments --environment-names MyEnv --query 'Environments[].[Status,CNAME]' --output table
```

只剩 1 列、狀態 `Ready` 就可以交。已經拿到的分數不會因為重交而消失。

**預防**：lab 啟動後**一個小時內**交最容易撞到這個，交之前先跑上面那行檢查。其他會去抓 EB 網址的 lab（例如 8.2、10.1）理論上也可能遇到，我們沒有實測。

---

## D. 通用排查方法

1. **看實際的網路請求，不要只看錯誤提示。** 前端顯示的「Operation failed」看不出原因，Network 面板裡的**狀態碼**和**等待時間**才看得出來：
   - 403 而且立刻回應 → 請求被擋
   - 504 而且等滿 60 秒 → 伺服器處理太久
2. **lab 畫面是跨網域的 iframe。** 在外層頁面看不到 iframe 裡的請求和 Console。要在 DevTools Console 左上角把 `top` 切換成 `labs.vocareum.com` 那個 frame，才能在 lab 的環境裡執行指令。
3. **分清楚兩個 terminal。** lab 頁面右邊的 terminal 是 **Vocareum 的容器**，家目錄就是提交目錄；VS Code IDE 是**另一台 EC2**。作業指定在哪裡跑，就在哪裡跑。
4. **用 Grades 面板看評分項目。** 它會列出評分實際檢查哪幾項（例如 Lab 5.1 只檢查 Task 2、5、7），可以用來判斷問題出在資料還是平台。
5. **找對照組。** 同學交得出去、你交不出去，就代表平台正常，問題在你的環境或帳號狀態，可以縮小範圍。
6. **不確定是不是自己的錯時，先查 AWS 端的真實狀態。** 例如直接用 Console 看表裡有幾筆資料、GSI 狀態是什麼，再決定下一步。
7. **評分程式看資源的方式，不一定跟你一樣。** 你自己查「有哪些環境／資源」時，習慣會過濾掉已刪除的；評分程式不一定這樣做。遇到評分在最後一步崩潰、前面都通過時，用**不加任何過濾**的方式列一次資源，看看有沒有殘留的已終止資源（見 [C8](#c8-lab-91評分最後一步崩潰task-8b-沒分name-or-service-not-known)）。
