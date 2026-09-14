# Lab 8.1 — Migrating a Web Application to Docker Containers

**分數**：100/100
**時間**：約 50 分鐘（含兩次 docker build 拉 image）

## 這個 Lab 在做什麼

咖啡豆供應商的網站（node.js）和資料庫（MySQL）原本各裝在一台 EC2 上。你要在 VS Code IDE 那台機器上，把兩者各自包成 Docker container 跑起來，讓 node 容器連到 MySQL 容器，最後把 node image 推上 ECR。
grader 會用 `setup.sh` 留下的 SSH key 登入你的 IDE 機器檢查：`node_app_1` 和 `mysql_1` 兩個容器**必須還在跑**、ECR 有 `node-app:latest`。所以做完不要 stop 容器。

## 開始前

- **Start Lab** → ready → **AWS** 開 Console
- 到 [whatismyip.com](https://www.whatismyip.com/) 記下 IPv4（Task 3 開 SG 用）
- EC2 → Instances 有三台：`Lab IDE`（你操作的機器）、`AppServerNode`（網站）、`MysqlServerNode`（資料庫）。把後兩台的 **Public IPv4** 記下來，後面會一直用

## Task 1：準備 IDE（這步一定要做，grader 靠它）

1. **Details → AWS: Show** → LabIDEURL / LabIDEPassword → 新分頁登入 IDE
2. 終端（沒看到就 ☰ → Terminal → New Terminal）：
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/06-lab-containers/code.zip -P /home/ec2-user/environment
   unzip code.zip
   chmod +x ./resources/setup.sh && ./resources/setup.sh
   ```
   `setup.sh` 會產生 SSH key 存到 Secrets Manager（`c9key`）並開 port 22——這是給評分程式進來看容器用的。畫面最後印一段 JSON；如果停在 `:` 不動，那是 AWS CLI 的分頁器，按 `q`
3. `aws --version`、`pip3 show boto3` 確認一下

## Task 2：先看原本的網站怎麼跑

1. 瀏覽器開 `http://<AppServerNode IP>`（http，不是 https）
2. **List of suppliers → Add a new supplier**，隨便填一筆（例：Nikki Wolf / 100 Main Street / Anytown / CA / nwolf@example.com / 4155551212）→ Submit
3. 列表點 **edit** 改電話 → Submit，確認有存
   > 這筆資料之後會拿來驗證容器版的資料庫有沒有接對，地址請用 **Main Street** 之類好認的字

## Task 3：把 node 網站包成容器

IDE 終端：
```bash
mkdir containers && cd containers
mkdir node_app && cd node_app
mv ~/environment/resources/codebase_partner ~/environment/containers/node_app
cd ~/environment/containers/node_app/codebase_partner
touch Dockerfile
```
左側檔案樹打開 `containers/node_app/codebase_partner/Dockerfile`，貼：
```dockerfile
FROM node:11-alpine
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN npm install
EXPOSE 3000
CMD ["npm", "run", "start"]
```
存檔後：
```bash
docker build --tag node_app .
docker images
docker run -d --name node_app_1 -p 3000:3000 node_app
docker container ls
curl http://localhost:3000
```
curl 會吐出一整頁 HTML（title 是 Coffee suppliers）= 容器活著。

**開 port 3000 給你的電腦**：Console → EC2 → 選 `Lab IDE` → Security 分頁 → 點 security group → Inbound rules → Edit → Add rule：Custom TCP / 3000 / Source **My IP** → Save。
然後瀏覽器開 `http://<Lab IDE IP>:3000`，首頁會出現；但點 **List of suppliers** 會報錯——容器不知道資料庫在哪。

看一下原因（可選）：
```bash
docker ps                       # 記 container id
docker exec -ti <container-id> sh
su node
env                             # 沒有 APP_DB_HOST
exit
exit
```
重新用正確的環境變數起容器：
```bash
docker stop node_app_1 && docker rm node_app_1
docker run -d --name node_app_1 -p 3000:3000 -e APP_DB_HOST="<MysqlServerNode IP>" node_app
```
再開 `http://<Lab IDE IP>:3000/suppliers` → 看得到 Task 2 那筆了。

## Task 4：把 MySQL 也包成容器

1. 先把現在的資料 dump 出來（還在 `codebase_partner` 目錄）：
   ```bash
   cd /home/ec2-user/environment/containers/node_app/codebase_partner
   mysqldump -P 3306 -h <MysqlServerNode IP> -u nodeapp -p --databases COFFEE > ../../my_sql.sql
   ```
   密碼輸入 `coffee`。沒有輸出就是成功；檔案樹的 `containers/` 會多出 `my_sql.sql`（看不到就檔案樹右上 ⟳ 重新整理）
2. 打開 `my_sql.sql`，找 `INSERT INTO` 那行（約 51 行），把你的地址 `Main` 改成 `Container`（例：`100 Container Street`）→ 存檔。這是等下分辨「新舊資料庫」的記號
3. 建 MySQL image：
   ```bash
   cd /home/ec2-user/environment/containers
   mkdir mysql && cd mysql
   touch Dockerfile
   mv ../my_sql.sql .
   ```
   `containers/mysql/Dockerfile` 貼：
   ```dockerfile
   FROM mysql:8.0.23
   COPY ./my_sql.sql /
   EXPOSE 3306
   ```
   ```bash
   docker rmi -f $(docker image ls -a -q)     # 清空間，有 Error 訊息可忽略
   sudo docker image prune -f && sudo docker container prune -f
   docker build --tag mysql_server .
   docker images
   docker run --name mysql_1 -p 3306:3306 -e MYSQL_ROOT_PASSWORD=rootpw -d mysql_server
   docker container ls
   ```
   > ⚠️ `docker rmi -f $(...)` 會連 `node_app` image 一起砍，但 `node_app_1` 容器還在跑不受影響；Task 6 要 push 時若 image 不見了，回 `node_app/codebase_partner` 再 `docker build --tag node_app .` 一次
4. **等 30 秒左右**再匯入（MySQL 8 第一次啟動會初始化再重啟一次，太早匯入會 connection refused；`docker logs mysql_1` 看到第二次 `ready for connections` 就可以）：
   ```bash
   sed -i '1d' my_sql.sql
   docker exec -i mysql_1 mysql -u root -prootpw < my_sql.sql
   docker exec -i mysql_1 mysql -u root -prootpw -e "CREATE USER 'nodeapp' IDENTIFIED WITH mysql_native_password BY 'coffee'; GRANT all privileges on *.* to 'nodeapp'@'%';"
   ```
   `-prootpw` 中間**沒有空格**。密碼警告忽略

## Task 5：讓 node 容器改連 MySQL 容器

```bash
docker stop node_app_1 && docker rm node_app_1
docker inspect mysql_1 | grep '"IPAddress"'        # 例如 172.17.0.3
docker run -d --name node_app_1 -p 3000:3000 -e APP_DB_HOST=<那個 172.17.x.x> node_app
docker ps
```
瀏覽器 `http://<Lab IDE IP>:3000/suppliers` → 地址顯示 **Container Street** = 已經在讀容器裡的資料庫。

**兩個容器留著，別停。**

## Task 6：推到 ECR

1. Console 右上角使用者名稱 → **My Account** 那串 12 位數 = account id（或終端 `aws sts get-caller-identity --query Account --output text`）
2. ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   aws ecr create-repository --repository-name node-app
   docker tag node_app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/node-app:latest
   docker images
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/node-app:latest
   aws ecr list-images --repository-name node-app
   ```
   最後看到 `"imageTag": "latest"`

## 交作業

`docker ps` 確認 `node_app_1`、`mysql_1` 都 Up → Lab 頁 **Submit → Yes**。

## 會踩的坑

- **忘記跑 setup.sh 或跑在自己電腦上** → grader 進不了 IDE，容器再對也 0 分。指令要貼在瀏覽器 IDE 下方的終端（提示字元 `ec2-user@ip-10-...`），不是本機 PowerShell
- 容器 stop 了再 Submit → 扣分；重開 `docker start node_app_1 mysql_1` 即可
- MySQL 匯入太早 → `ERROR 2002/2003 Can't connect`，等一下重跑 `docker exec -i mysql_1 mysql ... < my_sql.sql`
- `mysqldump` 的 `-p` 後面直接 Enter 再輸密碼；若寫 `-p coffee`（有空格）會把 coffee 當資料庫名
- `sed -i '1d'` 只能跑一次，跑兩次會把 `CREATE DATABASE` 那行也砍掉
- Task 5 的 `APP_DB_HOST` 要用 `docker inspect` 看到的容器內網 IP，不是 IDE 的公網 IP
- `docker rmi -f $(docker image ls -a -q)` 把 `node_app` image 也刪了 → Task 6 `docker tag` 找不到 image，回去重 build
- 網站 `:3000` 打不開 → SG 3000 規則的 IP 跟你現在的公網 IP 不同（換網路了）
