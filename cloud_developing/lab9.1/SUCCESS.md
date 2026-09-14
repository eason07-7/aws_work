# Lab 9.1 — Caching Application Data with ElastiCache

**分數**：100/100
**時間**：約 40 分鐘（Memcached 建立 ~5 分、EB 更新 ~3 分）

## 這個 Lab 在做什麼

在 Aurora 前面放一層 **ElastiCache for Memcached**。先用四支 Python 小腳本驗證「先查快取、沒有再查資料庫、改資料就清快取」的邏輯，再把新版 node 程式（會用快取）重新 build 推上 ECR，並在 Elastic Beanstalk 加一個環境變數 `MEMC_HOST` 讓網站改走快取。
grader 看：Aurora SG 的兩條 11211 規則、subnet group、Memcached 叢集、beans 表最後的資料狀態（改過 / 新增 / 刪掉各一筆）、ECR 新 image、EB 環境變數。

## 開始前

- 這個 Lab 是**舊版介面**：上排有 **ⓘ AWS Details** 和 **ⓘ Details** 兩顆，IDE 網址密碼在 **AWS Details** 裡（Details 是空的）
- **Start Lab** → 等左上 AWS 旁邊的圓點變綠 → 點 **AWS** 開 Console
- 記 IPv4（whatismyipaddress.com）

## Task 1：準備 IDE

1. **AWS Details** → LabIDEURL / LabIDEPassword → 新分頁登入
2. 終端：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/08-lab-db-caching/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   問 IP 貼 IPv4。這支腳本做很多事（重建網站、灌 Aurora、build+push 容器、更新 Beanstalk、加 API resource），跑 2–3 分鐘，最後印 `done`
3. `aws --version`、`pip3 show boto3`。IDE 分頁留著

## Task 2：開防火牆 + 建 subnet group

Console → **EC2 → Security Groups** → 勾名字含 **ClusterSecurityGroup** 的那個（作業說「含 Aurora」，實際就是它）→ Inbound rules → Edit：
- Add rule：Custom TCP / **11211** / Source 選**這個 SG 自己**
- Add rule：Custom TCP / **11211** / Source 選 **Lab IDE SG**
- Save

Console → **ElastiCache** → 左側 **Subnet groups** → Create：
- Name `ElastiCacheSubnetGroup`、Description `Subnet Group for ElastiCache`、VPC 選 **IDE VPC**
- 下面應該自動選了 2 個子網（沒有就按 Manage 勾兩個）→ Create

## Task 3：建 Memcached

ElastiCache → **Memcached caches** → **Create Memcached cache**：
- Deployment option：Node-based cluster；Creation method：Cluster cache；Location：AWS Cloud
- Name `MemcachedCache`
- Engine version **1.6.6**、Port 11211、Parameter group **default.memcached.1.6**
- Node type **cache.r6g.large**、Number of nodes **3**
- Subnet group：Choose existing → `ElastiCacheSubnetGroup`
- Next → Security groups 按 Manage → 勾 **ClusterSecurityGroup** → Next → Create

要等 5 分鐘左右，先往下做。

## Task 4：第一支腳本 — 讀取（lazy loading）

IDE 終端：
```bash
cd ~/environment/python_3
sudo dnf install -y mariadb105-devel gcc python3-devel
sudo pip3 install PyMySQL
sudo pip3 install pymemcache
```
拿兩個 endpoint：
```bash
aws elasticache describe-cache-clusters     # 找 ConfigurationEndpoint.Address（memcachedcache.xxxx.cfg.use1.cache.amazonaws.com）
aws rds describe-db-cluster-endpoints       # 找 EndpointType=WRITER 的 Endpoint
```
（卡在 `:` 按 `q`）

打開 `python_3/find_all.py`：`<FMI_1>` → Memcached endpoint，`<FMI_2>` → Aurora WRITER endpoint。存檔。
**確認 Memcached 已 available** 再跑：
```bash
python3 find_all.py     # Data not found in cache → 從 DB 讀 → Setting result in cache
python3 find_all.py     # Data returned from cache（快很多）
```

## Task 5–7：改 / 新增 / 刪除（write-through）

三支腳本 `update_item.py`、`create_item.py`、`delete_item.py` 都一樣先填 `<FMI_1>`、`<FMI_2>`，然後：
```bash
python3 update_item.py    # id 1 改成 Best bean EVER，並清掉 all_beans 快取
python3 find_all.py       # 從 DB 讀到新資料
python3 find_all.py       # 從 cache

python3 create_item.py    # 新增 Worlds greatest bean（id 15）
python3 find_all.py
python3 find_all.py

python3 delete_item.py    # 刪 id 14
python3 find_all.py
```
每次改完資料，下一次 `find_all` 一定是「Data not found in cache」——這就是 write-through 在清快取。

## Task 8：讓網站用快取

1. 換新程式碼、重 build、推 ECR：
   ```bash
   mv ~/environment/resources/bean.controller_2.js ~/environment/resources/codebase_partner/app/controller/bean.controller.js
   cd ~/environment/resources/codebase_partner/
   npm install
   docker build --tag node_app .
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   aws ecr describe-repositories --query repositories[][repositoryUri] --output text
   docker tag node_app:latest <repository-uri>:latest
   docker push <repository-uri>:latest
   ```
   （account-id：Console 右上使用者名稱 → My Account）
2. Console → **Elastic Beanstalk** → MyEnv → 左側 **Configuration** → Updates, monitoring, and logging 那格 **Edit** → 拉到 **Environment properties** → Add：Name `MEMC_HOST`、Value = Memcached endpoint → **Apply**，等幾分鐘
3. 開 `http://<MyEnv 網址>/beans`：All beans 底下多一行小字，第一次 `results from Db`，重新整理變 `results from Cache`
4. S3 → s3bucket → Properties → 靜態網站連結 → **Buy Coffee** 有豆子列表

## 交作業

**Submit → Yes**。

## 會踩的坑

- 找不到「名字含 Aurora」的 SG：它叫 `...-ClusterSecurityGroup-...`
- Memcached 還在 creating 就跑 `find_all.py` → 連線逾時，等 available
- `python3 find_all.py` 報 `ModuleNotFoundError: pymysql` → `sudo pip3 install` 沒帶 sudo
- `update_item.py` 印的是 `Cache purged.`，跟作業截圖的 `Purged the cache` 不同，正常
- Task 8 忘記 `mv bean.controller_2.js` 就 build → 網站不會有 cache 那行字，也不吃 `MEMC_HOST`
- EB 環境變數 Apply 後要等狀態回 Ok 再測；`/beans` 第一次一定是 Db
- 換過網路 → 網站 403，重跑 setup.sh 填新 IP
