# Lab 12.1 — Implementing Application Authentication Using Amazon Cognito

**分數**：100/100
**時間**：約 50 分鐘（開頭等三個 stack ~12 分）

## 這個 Lab 在做什麼

幫咖啡店網站加登入：建一個 Cognito user pool `the_cafe` 和 app client，網站 LOGIN 按鈕導到 Cognito hosted 登入頁；建一個使用者 `frank`；然後在 API Gateway 幫 `/create_report` 加 Cognito authorizer，沒帶 token 的請求一律 401，登入後網站按 REPORT 才能收到報表 email。
grader 看：user pool / app client 設定（callback、sign-out、implicit、scopes、auth flow）、resource server、S3 上 config.js 的 Cognito URL、使用者 frank、authorizer `cafe_lockdown` 綁在 POST create_report。

## 開始前

- **Start Lab** → **AWS** 開 Console
- **CloudFormation**：三個 stack 都要 **CREATE_COMPLETE**（~12 分）
- 記 IPv4；準備一個收得到信的 email（學校信箱）
- 記事本準備記：CloudFront domain、create_report Invoke URL、User pool ID、hosted login URL

## Task 1：準備 IDE + 確認訂閱

**Details → AWS: Show** → LabIDEURL / 密碼 → 登入 IDE → 終端：
```bash
wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/12-lab-cognito/code.zip -P /home/ec2-user/environment
unzip code.zip
chmod +x ./resources/setup.sh && ./resources/setup.sh
```
會先問 IP（貼 IPv4），跑很久之後再問 **email**（貼你的信箱）。結束前有一行 `This is the Cloudfront Distribution created for the lab: EXXXX`，記下來。
**去信箱**點 AWS Notifications 的 **Confirm subscription**。
CloudFront → 那個 distribution → 複製 **Distribution domain name**（`xxxx.cloudfront.net`）→ 瀏覽器開 → 咖啡店網站；右上 **LOGIN** 現在只會跳 "No API to call"。分頁留著。

## Task 2：Cognito user pool + app client

Console → **Cognito → Create user pool**：
- Application type **Traditional web application**；Name your application `the_cafe_app_client`
- Configure options → Sign-in identifiers 勾 **Username**
- Required attributes for sign-up 選 **email**
- Add a return URL：`https://<cloudfront-domain>/callback.html`
- **Create user directory**
- 下一頁有 **View login page** 可以先看一眼登入頁（關掉即可）

回 **User pools** → 點剛建的（名字像 `User pool - xxxxxx`）→ **Rename** → `the_cafe` → Save。記 **User pool ID**。
下方 Recommendations 點 **the_cafe_app_client** → **Login pages** 分頁 → Managed login pages configuration **Edit**：
- Allowed sign-out URLs → Add → `https://<cloudfront-domain>/sign_out.html`
- OAuth 2.0 grant types：**取消** Authorization code grant，改勾 **Implicit grant**
- OpenID Connect scopes：留 **Email、OpenID**，取消 Phone
- Save changes

回 **App client: the_cafe_app_client** 頁 → **Edit** → Authentication flows：勾 **ALLOW_USER_PASSWORD_AUTH**、取消 **ALLOW_USER_SRP_AUTH** → Save changes。

## Task 3：resource server + 登入頁網址

先拿 Invoke URL：API Gateway → ProductsApi → Stages → prod 展開 → `/create_report` → POST → 複製 **Invoke URL**（`https://xxxx.execute-api.us-east-1.amazonaws.com/prod/create_report`）。
Cognito → the_cafe → 左側 **Domain** → Resource servers → **Create resource server**：Name `cafe_resource_server`、Identifier 貼 Invoke URL → Create。
Overview → the_cafe_app_client → **View login page** → 登入頁出現後，**複製整個網址列**（長這樣：`https://xxxx.auth.us-east-1.amazoncognito.com/login?client_id=...&response_type=token&scope=email+openid&redirect_uri=https%3A%2F%2F....cloudfront.net%2Fcallback.html`）。

## Task 4：網站接上 Cognito

IDE 開 `resources/website/config.js`，`COGNITO_LOGIN_BASE_URL_STR: null` 的 `null` 換成剛複製的網址（**加雙引號**）。關檔。終端：
```bash
bucket=$(aws s3api list-buckets --query "Buckets[].Name" | grep s3bucket | tr -d ',' | sed -e 's/"//g' | xargs)
aws s3 cp ./resources/website/config.js s3://$bucket/ --cache-control "max-age=0"
```
網站分頁重新整理 → LOGIN → 跳到 Cognito 登入頁（還沒使用者，先按上一頁）。

## Task 5：看 API 設定並測一次

API Gateway → ProductsApi → Resources → `/create_report` → **OPTIONS** → Integration Response → 展開 200 → Header Mappings：`Access-Control-Allow-Origin` 已經是你的 CloudFront 網址（不用改）。
→ **POST** → **Test** → 下方 Test → 200 + executionArn；信箱一兩分鐘內收到報表連結（60 秒內要點開；太慢就到 Lambda `GeneratePresignedURL` 把秒數改大再 Deploy）。
> 沒收到信：WAF → IP sets → `office_regional` 確認裡面是你現在的 IP/32

## Task 6：建使用者 frank

Cognito → the_cafe → **Users → Create user**：Don't send an invitation、Username `frank`、Temporary password → Set a password `!CoffeeIsGreat34` → Create user。
網站 → LOGIN → `frank` / `!CoffeeIsGreat34` → 要求改密碼 → `!CoffeeIsGreat35` 兩次 → Change password → 回到網站，右上變成 **REPORT** → 點 → "Report is being generated" → 信箱收到報表。
測「沒登入也能打」：
- IDE：`curl -X POST <Invoke URL>` → `{"message":"Forbidden"}`（IDE 的 IP 不在 WAF 白名單，正常）
- **你自己電腦**的 cmd / PowerShell：`curl -X POST <Invoke URL>` → 回 executionArn（沒驗證就能產報表，這就是要修的洞）。視窗留著

## Task 7：API 加 Cognito authorizer

API Gateway → ProductsApi → **Authorizers → Create authorizer**：Name `cafe_lockdown`、Type **Cognito**、User pool 選 `the_cafe`、Token source `Authorization` → Create。
重新整理頁面 → Resources → `/create_report` → **POST** → **Method Request** → Edit：
- Authorization 選 **cafe_lockdown**（在 Cognito user pool authorizers 底下）
- HTTP request headers → Add header：Name `Authorization`、勾 **Required**
- Save
根 **/** → **Deploy API** → prod → Deploy。
本機 cmd 再跑一次同樣的 `curl -X POST ...` → `{"message":"Unauthorized"}`（若還是 executionArn，等 30 秒再試）。

## Task 8：從網站再測一次

網站（若登出了就 LOGIN `frank` / `!CoffeeIsGreat35`）→ **REPORT** → 信箱收到報表 = 帶 token 的請求還是能過。
（可選）F12 → Network → 再按 REPORT → 點 `create_report` 那筆 → Request Headers 複製 `Authorization: Bearer ...` 整串 → 本機 `curl -X POST <Invoke URL> -H "Authorization: Bearer ..."` → 成功。

## 交作業

**Submit → Yes**。

## 會踩的坑

- setup.sh 問 email 是在**跑了幾分鐘之後**，別以為卡住；訂閱信要 Confirm，不然報表信全收不到
- Task 2 的 return URL / sign-out URL 都要 **https** 加 CloudFront 網域，路徑分別是 `/callback.html`、`/sign_out.html`
- grant type 要換成 **Implicit**（網站 JS 用 token 直接回 callback），留 Authorization code 會登入後拿不到 token
- 忘記 rename 成 `the_cafe` → grader 找不到 pool
- config.js 的網址要用**雙引號**包，且 `redirect_uri` 那段保持 View login page 網址列原樣
- Task 7 authorizer 要選 **Cognito** 類型、Token source 一定是 `Authorization`；改完 Method Request 一定要 **Deploy API**
- 本機 curl 回 Forbidden（不是 Unauthorized）= 你的 IP 不在 WAF `office_regional` 裡，去加
- 網站 LOGIN 後跳錯 "redirect_mismatch" = callback URL 打錯或少了 https
