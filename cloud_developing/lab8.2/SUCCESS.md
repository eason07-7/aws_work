# Lab 8.2 — Running Containers on a Managed Service

**分數**：100/100
**時間**：約 75 分鐘（Aurora 建立 ~8 分、Elastic Beanstalk 建環境 ~5 分、部署 ~3 分，大多在等）

## 這個 Lab 在做什麼

把上個 Lab 的咖啡豆供應商 app 搬到託管服務：資料庫改用 **Aurora Serverless v2**、網站容器改由 **Elastic Beanstalk** 從 ECR 拉 image 跑，最後在 API Gateway 加一個 `/bean_products` 端點把 EB 的 `beans.json` 轉給咖啡店網站的 Buy Coffee 頁。
grader 檢查 9 項：新子網、Aurora 叢集、IDE SG、資料庫裡的 suppliers / beans（兩項）、EB application、EB environment、bean inventory 頁有回應、`/bean_products` resource。
**最容易掉的是資料庫那兩項**——見最後「會踩的坑」。

## 開始前

- **Start Lab** → ready → **AWS** 開 Console
- 到 [whatismyipaddress.com](https://whatismyipaddress.com/) 記 IPv4
- 開一個記事本，準備記這幾個值（後面 Task 9 的設定檔要用）：
  ```
  IDE VPC ID:
  IDE Availability Zone:
  IDE subnet ID:
  extraSubnetForRds subnet ID:
  IDE security group ID:
  Database endpoint:
  Repository URI:
  Elastic Beanstalk URL:
  ```

## Task 1：準備 IDE

1. **Details → AWS: Show** → LabIDEURL / LabIDEPassword → 登入 IDE
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/07-lab-deploy/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   問 IP 時貼 IPv4。腳本會重建之前 lab 的網站/DynamoDB/API，然後 **build 容器並 push 到 ECR**（會跑一兩分鐘，最後印 `done`）
3. `aws --version`、`pip3 show boto3`
4. Console → S3 → `...-s3bucket-...` → Properties → 最下面 Static website hosting 的 URL 開一下，咖啡店網站要出得來（出不來 = IP 填錯，重跑 setup.sh）

## Task 2：多開一個子網

Console → **VPC**：
1. Your VPCs → 勾 **IDE VPC** → 記 VPC ID
2. Subnets → 勾 **IDE Public Subnet One** → 下方記 Availability Zone（如 us-east-1a）和 Subnet ID
3. **Create subnet**：VPC = IDE VPC、名稱 `extraSubnetForRds`、AZ **選一個不同的**（如 us-east-1b）、CIDR `10.0.2.0/24` → Create
4. 勾 extraSubnetForRds → Actions → **Edit subnet settings** → 勾 **Enable auto-assign public IPv4 address** → Save；記 Subnet ID
5. 還是勾著它 → 下方 **Route table** 分頁 → **Edit route table association** → 換成**另一個**路由表（有 `0.0.0.0/0 → igw-...` 那個）→ Save

## Task 3：建 Aurora Serverless

Console → **RDS** → **Create database**：
- Standard create
- Engine：**Aurora (MySQL-Compatible)**，Version 選 **Aurora MySQL 3.07.0**（找不到就選最接近的 3.0x，grader 只看是 Aurora MySQL）
- Templates：**Dev/Test**
- DB cluster identifier：`supplierdb`
- Credentials：Self managed、**不要**勾 Auto generate、密碼 `coffee_beans_for_all`（兩次）
- Instance configuration：**Serverless v2**（容量 2–16 ACU 預設不動）
- Connectivity：VPC = **IDE VPC**；VPC security group 選 **Choose existing** → 移掉 default → 加 **Lab IDE SG**
- **RDS Data API：勾 Enable**
- Monitoring：**取消** Performance Insights；展開 Additional configuration **取消** Enhanced Monitoring
- 最下面 Additional configuration → Initial database name：`suppliers`
- **Create database**（跳出 add-ons 建議直接關）

等幾分鐘。點 `supplierdb` → `supplierdb-instance-1` → Status 變 **Available** 後，Connectivity & security 的 **Endpoint** 記到記事本（`supplierdb.cluster-xxxx.us-east-1.rds.amazonaws.com`）。Security 的 VPC security groups 點進去記 SG ID（就是 Lab IDE SG）。

## Task 4：看一下 ECR 裡的 image

Console → **Elastic Container Registry** → `cafe/node-web-app` → 記 **URI**（`<帳號>.dkr.ecr.us-east-1.amazonaws.com/cafe/node-web-app`）。
IDE 終端也看一次：
```bash
aws ecr describe-repositories
aws ecr describe-images --repository-name cafe/node-web-app
```

## Task 5：容器先在 IDE 上接 Aurora 試跑

```bash
docker run -d --name node-web-app-1 -p 8000:3000 -e APP_DB_HOST="<Database endpoint>" cafe/node-web-app
curl http://localhost:8000
```
Console → EC2 → Security Groups → **Lab IDE SG** → Inbound rules → Edit：
- Add rule：Custom TCP / **8000** / My IP
- Add rule：**MYSQL/Aurora** / Source Custom → 選 **Lab IDE SG 自己**（self-reference，讓容器連得到 DB）
- Save

EC2 → Instances → Lab IDE → 記 Public IPv4 → 瀏覽器開 `http://<IDE IP>:8000` → 點 List of suppliers → **會看到錯誤**（DB 裡還沒有東西），這是預期的。分頁留著。

## Task 6：用 Query Editor 建資料庫物件（★ 一定要用 Console 的 Query Editor）

Console → RDS → 左側 **Query Editor**：
- Database instance or cluster：`supplierdb`
- Database username：**Add new database credentials**
- username `admin`、password `coffee_beans_for_all`
- Database name：`suppliers`
- **Connect to database**（第一次失敗就再按一次）

貼進編輯器 → **Run**：
```sql
CREATE USER "nodeapp" IDENTIFIED WITH mysql_native_password BY "coffee";
CREATE DATABASE COFFEE;
USE COFFEE;
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, RELOAD, PROCESS, REFERENCES, INDEX, ALTER, SHOW DATABASES, CREATE TEMPORARY TABLES, LOCK TABLES, EXECUTE, REPLICATION SLAVE, REPLICATION CLIENT, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, CREATE USER, EVENT, TRIGGER ON *.* TO 'nodeapp'@'%' WITH GRANT OPTION;
CREATE TABLE suppliers(
                    id INT NOT NULL AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    address VARCHAR(255) NOT NULL,
                    city VARCHAR(255) NOT NULL,
                    state VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(100) NOT NULL,
                    PRIMARY KEY ( id ));
```
再跑 `use COFFEE; select * from suppliers` → 空表。
回 `:8000` 的網站分頁重新整理 → 變成空列表 + **Add a new supplier** → 加一筆 → 回 Query Editor 再 Run 一次會看到它。

## Task 7：灌供應商資料

IDE 終端：
```bash
cd ~/environment/resources
mysql -h <Database endpoint> -P 3306 -u admin -p
```
密碼 `coffee_beans_for_all`，進到 `mysql>` 後：
```sql
use COFFEE; select * from suppliers;
source coffee_db_dump.sql
use COFFEE; select * from suppliers;
select * from beans;
exit
```
suppliers 8 筆、beans 14 筆。網站重新整理會列出 8 家。

## Task 8：看 IAM（純閱讀）

IAM → Policies 搜 `aws-elasticbeanstalk-ec2-instance-policy` 看 JSON（ecr:GetAuthorizationToken、BatchGetImage…）；Roles 搜 `aws-elasticbeanstalk-ec2-role` 看 Trust relationships 是 ec2.amazonaws.com。

## Task 9：Elastic Beanstalk

1. 先建 application 和設定檔：
   ```bash
   cd ~/environment && mkdir bean && cd bean
   aws elasticbeanstalk create-application --application-name MyNodeApp
   ```
   在 `bean/` 新增 `options.txt`，貼下面並把五個 `<FMI>` 換成記事本的值（SG ID / VPC ID / IDE subnet ID / extraSubnetForRds ID / DB endpoint）：
   ```json
   [
       {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "IamInstanceProfile", "Value": "aws-elasticbeanstalk-ec2-role"},
       {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "SecurityGroups", "Value": "<FMI_1>"},
       {"Namespace": "aws:ec2:vpc", "OptionName": "VPCId", "Value": "<FMI_2>"},
       {"Namespace": "aws:ec2:vpc", "OptionName": "Subnets", "Value": "<FMI_3>,<FMI_4>"},
       {"Namespace": "aws:elasticbeanstalk:application:environment", "OptionName": "APP_DB_HOST", "Value": "<FMI_5>"}
   ]
   ```
2. 查 Docker 平台名稱，**用查到的那個**（現在只會有 Amazon Linux 2023 一項，AL2 已被 AWS 下架）：
   ```bash
   aws elasticbeanstalk list-available-solution-stacks | grep 'running Docker'
   aws elasticbeanstalk create-environment --application-name MyNodeApp --environment-name MyEnv --solution-stack-name "64bit Amazon Linux 2023 v4.13.8 running Docker" --region us-east-1 --option-settings file://options.txt
   ```
   （名稱與版本號照你查到的原樣複製）。卡在 `:` 按 `q`
3. 停掉 IDE 上的測試容器：
   ```bash
   docker stop node-web-app-1 && docker rm node-web-app-1
   ```
4. Console → **Elastic Beanstalk** → MyEnv，看 Events 等 Health 變 **Ok**（約 5 分鐘）。點上方 domain 連結 → 看到 Congratulations 範例頁
5. 換成我們的 image：在**你的電腦**建 `Dockerrun.aws.json`：
   ```json
   {
   "AWSEBDockerrunVersion": "1",
   "Image": {
       "Name": "<Repository URI>",
       "Update": "true"
   },
   "Ports": [ { "ContainerPort" : 3000 } ]
   }
   ```
   MyEnv 頁 → **Upload and deploy** → 選這個檔 → Version label 改成 `MyNodeApp-version-1a` → **Deploy**，等幾分鐘
6. 記 MyEnv 的網址到記事本。開 `http://<EB 網址>/suppliers` 有 8 家；把 `/suppliers` 改 `/beans` 看豆子；再改 `/beans.json` 看 JSON——下一步用這個

## Task 10：API Gateway 加 /bean_products

1. Lab 頁 Details → AWS: Show 記 **WebsiteURL**，開它 → 左上選單 **Buy Coffee** → 現在寫 coming soon
2. Console → **API Gateway** → ProductsApi → 選根 **/** → **Create resource**：Resource name `bean_products`（底線）、**勾 CORS** → Create
3. 選 `/bean_products` → **Create method**：GET、Integration type **HTTP**、**開啟 HTTP proxy integration**、HTTP method GET、Endpoint URL `http://<EB 網址>/beans.json` → Create method
4. Test 分頁 → Test → 回 JSON 陣列
5. 根 **/** → **Deploy API** → Stage `prod` → Deploy（WAF 警告忽略）
6. 回咖啡店網站重新整理 → **Buy Coffee** 出現豆子庫存

## 交作業

**Submit → Yes**，看 Grades（9 項）。

## 會踩的坑

- **「Unable to connect to the coffee database」×2**：grader 是用 **Query Editor 連線時自動建立的 Secrets Manager 密鑰**（名稱 `rds-db-credentials/cluster-.../admin/...`）透過 RDS Data API 去讀 suppliers / beans。如果你 Task 6 沒用 Console 的 Query Editor（例如全在 IDE 用 mysql 指令做），資料再對也會這兩項 0 分。補救：回 Query Editor 用 Add new database credentials 連一次、隨便跑一句 `select 1`，再 Submit
- Aurora 版本清單找不到 3.07.0 就選最接近的 3.0x，不影響分數
- RDS Data API 忘記勾 → Query Editor 連不上
- SG 少了 3306 self-reference → 容器和 EB 都連不到 DB
- Task 5 網站看到錯誤是正常的，Task 6 做完才會好
- **`aws elasticbeanstalk list-available-solution-stacks | grep 'running Docker'` 現在只會列出 Amazon Linux 2023**（AWS 已於 2026 年 9 月下架 AL2 的 Docker 平台）。直接用它就好——實測 AL2023 一樣吃 `Dockerrun.aws.json v1`，後面的 Upload and deploy 與 `/beans.json` 都正常。作業截圖裡的 `64bit Amazon Linux 2 v4.0.5 running Docker` 已經找不到了，不用找
- Upload and deploy 時 Version label 一定要改（預設名字重複會失敗）
- `/bean_products` 忘記 Deploy API → 網站 Buy Coffee 還是 coming soon
- IP 換了（換網路）→ 網站 403，重跑 setup.sh；`:8000` 打不開改 SG 8000 規則的 IP
