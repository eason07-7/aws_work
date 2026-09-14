# Lab 9.2 — Implementing CloudFront for Caching and Application Security

**分數**：100/100
**時間**：約 75 分鐘（開頭等 CloudFormation ~15 分、CloudFront 每次部署 ~5 分）

## 這個 Lab 在做什麼

把咖啡店網站從「S3 Object URL + IP 白名單」改成「CloudFront（HTTPS）+ WAF 白名單」：
1. 建 CloudFront distribution 指向 S3 bucket，bucket policy 改成只准 CloudFront 讀
2. 用 WAF 的 IP set 讓網站（全球）和 API Gateway（區域）都只有你的 IP 能存取
3. 寫一個 CloudFront Function 在回應時塞一個隨機 cookie，讓首頁圖片每次重新整理都換
4. 把 S3 物件的 Cache-Control 從 max-age=0 改成 180，觀察 x-cache 從 Miss 變 Hit

grader 看：distribution 設定（root object、origin header）、bucket policy、兩個 web ACL 與關聯、function 已 publish 並關聯、物件的 Cache-Control。

## 開始前

- **Start Lab** → **AWS** 開 Console
- **先去 CloudFormation → Stacks**，Description 是 `ACD_2.0` 的那個 stack 要等到 **CREATE_COMPLETE**（它在建 RDS 和 Elastic Beanstalk，實測要 15 分鐘上下）。沒等到就跑 setup.sh 會出錯
- 記 IPv4（whatismyipaddress.com）

## Task 1：準備 IDE

1. **Details → AWS: Show** → LabIDEURL → 新分頁登入
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/09-lab-cloudfront/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   問 IP 貼 IPv4。跑 2–3 分鐘印 `done`。**看倒數幾行有沒有 `An error occurred`**，有就是 stack 還沒好，再跑一次
3. S3 → `...-s3bucket-...` → `index.html` → Metadata 看到 `Cache-Control: max-age=0`（setup.sh 設的）→ 上方 Object URL 開一下，網站要出得來。分頁留著

## Task 2：建 CloudFront distribution

Console → **CloudFront → Create distribution**（問 plan 選 Pay as you go）：
- Distribution name `access-identity-cafe-website`、type **Single website or app** → Next
- Origin type **Amazon S3** → Browse S3 選 `...-s3bucket-...`
- Settings → Origin settings 選 **Customize origin settings** → **Add header**：name `cf`、value `1`
- Cache settings 選 **Customize cache settings** → Next
- WAF 頁直接 Next → **Create distribution**

上方 Last modified 顯示 **Deploying**，等 5–10 分鐘變成時間戳。然後：
- distribution 頁 **Edit** → Default root object `index.html`、IPv6 **Off** → Save changes（再等幾分鐘）
- 複製 **Distribution domain name**（`xxxx.cloudfront.net`）新分頁開 → 網站出現

**改 bucket policy 只留 CloudFront**：S3 → bucket → Permissions → Bucket policy → Edit → 刪掉第 4–17 行（你 IP 那段 Allow 和 report.html 那段 Deny）→ Save changes。
回剛才 S3 Object URL 的分頁重新整理 → **AccessDenied**（正確，以後只能走 CloudFront）。關掉那個分頁。
CloudFront → Distributions 確認 Status **Enabled**，用 cloudfront.net 網址再開一次 → 正常。
IDE 終端 `wget https://<xxxx>.cloudfront.net` 回 200 = 別的網路也看得到（現在還沒鎖）。

## Task 3：WAF 鎖網站只給你的 IP

Console 搜 **WAF & Shield**（若左側有「switch to old console」就切過去）：
1. **IP sets → Create IP set**：name `office`、description `office IP`、Region **Global (CloudFront)**、IP addresses `<你的 IPv4>/32` → Create
2. **Web ACLs → Create web ACL**：
   - Resource type **CloudFront distributions**、Name `cafe-website-office-only-during-dev`、Description `Allow access to the cafe website through CloudFront from the cafe office`、metric name 同名
   - Associated AWS resources → **Add AWS resources** → 勾**你建的**那個 distribution（會有兩個，另一個是 IDE 的）→ Add → Next
   - Rules → **Add rules → Add my own rules and rule groups**：Rule type **IP set**、Name `only_office_please`、IP set `office`、Action **Allow** → Add rule
   - Default action 選 **Block** → Next → Next → Next → **Create web ACL**
3. CloudFront → distribution 的 Security 區塊出現 AWS WAF。網站重新整理還看得到；IDE `wget` 現在回 **403**

## Task 4：WAF 鎖 API 只給你的 IP

同樣在 WAF：
1. **IP sets → Create**：name `office_regional`、description `IP of the office for API Gateway`、Region **US East (N. Virginia)**、`<IPv4>/32`
2. **Web ACLs → Create**：Resource type **Regional resources**、Region US East、Name `website-api-gw-office-only-during-dev`、Description `To allow us to access the API GW calls used by the website from the office`
   - Add AWS resources → 類型 **Amazon API Gateway** → 勾 **ProductsApi - prod** → Add → Next
   - Add my own rules：IP set、Name `ip_for_apigw`、IP set `office_regional`、Allow；Default **Block** → 一路 Next → Create
3. 點進剛建的 ACL → **Associated AWS resources** 分頁確認有 ProductsApi - prod（沒有就 Add）
4. 測：API Gateway → ProductsApi → Stages → prod → `/bean_products` GET → Invoke URL 用瀏覽器開 → JSON（你的 IP 可以）；IDE `wget <Invoke URL>` → **403 Forbidden**

## Task 5：CloudFront Function 隨機換圖

CloudFront → **Functions → Create function**：Name `random_image_header` → Create。
Function code 整段換成作業給的 code（下方），把第 15 行 `distro_str = "dp880v3pwdoto"` 換成**你的 distribution 網域前綴**（cloudfront.net 前面那串）→ **Save changes**。
```js
function handler(event) {
  var
    pastry_name_arr = [
        "apple_pie",
        "apple_pie_slice",
        "chocolate_chip_cupcake",
        "strawberry_cupcake",
        "blueberry_jelly_doughnut",
        "plain_bagel"
    ],
    random_int = Math.floor(Math.random() * (pastry_name_arr.length)),
    response = event.response,
    date = new Date(),
    attr_str = "",
    distro_str = "dp880v3pwdoto"; //change this
date.setTime(+ date + (365 * 86400000)); //24 \* 60 \* 60 \* 100
attr_str = "Secure; Path=/; Domain=" + distro_str + ".cloudfront.net; Expires=" + date + ";";
response.cookies = {
    "the_image": {
        "value": pastry_name_arr[random_int],
        "attributes": attr_str
    }
};
return response;
}
```
- **Test** 分頁：Event type **Viewer Response** → Test function → Status 200，Output 有一個隨機 the_image
- **Publish** 分頁 → **Publish function** → Associated distributions → **Add association**：Distribution 選你的、Event type **Viewer Response**、Cache behavior **Default (\*)** → Add
- Distributions 頁又會 Deploying 幾分鐘。好了之後網站重新整理幾次，咖啡杯右邊的圖會換

## Task 6：調快取時間

網站分頁 F12 → **Network** → 重新整理 → 點最上面那個 cloudfront.net 請求 → Response Headers 看到 `cache-control: max-age=0`、`x-cache: RefreshHit from cloudfront`（Firefox 是 Miss）。

IDE 終端：
```bash
BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 's3bucket')].Name" --output text)
echo $BUCKET_NAME
aws s3 ls s3://$BUCKET_NAME/ | awk '{print $4}' | xargs -I {} aws s3api copy-object \
    --bucket $BUCKET_NAME \
    --copy-source $BUCKET_NAME/{} \
    --key {} \
    --cache-control "max-age=180" \
    --metadata-directive REPLACE
```
會刷過一堆 JSON。S3 隨便點一個檔案 → Metadata 變 `max-age=180`。
網站重新整理 → headers 變 `max-age=180`、`x-cache: Hit from cloudfront`。等 3 分鐘再整理 → `RefreshHit`。圖片還是會隨機換（cookie 是 viewer-response 加的，不受快取影響）。

## 交作業

**Submit → Yes**。

## 會踩的坑

- **stack 沒 CREATE_COMPLETE 就跑 setup.sh** → 一堆 `An error occurred`，重跑一次就好
- Task 3 關聯 distribution 時有**兩個** distribution，別選到 IDE 那個（看 origin 是不是 s3bucket）
- 全球 IP set 的 Region 要選 **Global (CloudFront)**；區域的選 **US East**，選反了 ACL 找不到 IP set
- Task 5 `distro_str` 沒改成自己的 → cookie 的 Domain 不對，瀏覽器不收，圖片不會換
- Function 要 **Publish** 再關聯；只 Save 不算
- 每次改 distribution 都要等 Deploying 結束再測，不然看到的是舊行為
- Task 6 那個 `xargs` 指令要在 IDE 跑（本機沒 aws CLI）；只改頂層物件是正常的，作業就是這樣寫
- 換網路 → IP 變了，WAF 兩個 IP set 都要改，網站和 API 才打得開
