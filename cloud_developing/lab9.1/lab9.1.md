Lab 9.1: Caching Application Data with ElastiCache
Lab overview and objectives
In this lab, you will deploy an Amazon ElastiCache cluster. You will also test synchronizing the cache with the Amazon Aurora Serverless database by using Python scripts. Finally, you will update the coffee suppliers application with new Node.js code that will use data caching.

 

After completing this lab, you should be able to:

Create a new ElastiCache for Memcached cluster

Query the ElastiCache for Memcached cluster by using Python and the pymemcache client

 

Duration
This lab will require approximately 45 minutes to complete.

 

AWS service restrictions
In this lab environment, access to AWS services and service actions might be restricted to the ones that are needed to complete the lab instructions. You might encounter errors if you attempt to access other services or perform actions beyond the ones that are described in this lab.

 

Scenario
Frank and Martha are excited that the bean inventory from the coffee suppliers application is integrated into the café website. Unfortunately, they are getting occasional negative feedback from customers who say that the bean inventory information takes too long to display on the page. Frank and Martha have asked Sofía if she can have the site display the information more quickly.

Luckily, one of the café's customers, Olivia, is an AWS consultant and has a lot of database experience. She has offered to help with the website. Olivia proposed adding database caching to improve the speed of the database query. This way, frequently used data would be stored in memory instead of having to be retrieved from the database, which could also require information to be read from database storage.

Olivia explained that you could cache data locally on the Amazon Elastic Compute Cloud (Amazon EC2) instance that is hosting the application containers. However, that architecture would not provide fault tolerance. This strategy would also require more administration because you would need to install and maintain the caching software yourself. Olivia recommended using the Amazon ElastiCache managed service. ElastiCache is similar to Aurora Serverless in that it simplifies the process to deploy and maintain a cache cluster.

Olivia - AWS consultant

In this lab, you will act as Olivia to work through the process to deploy and test the ElastiCache cluster. You will also play the role of Nikhil to update and redeploy the coffee suppliers application to use caching on the website.

 

When you start the lab, your application will be using the Aurora Serverless database to query data. Your architecture will look like the following diagram.

Architecture at the beginning of the lab. Application and database

 

By the end of this lab, you will have deployed an ElastiCache for Memcached cluster and configured the application to query the cache before going to the database. Your architecture will then look like the following diagram.

Architecture at the end of the lab. Application, cache, and database

 

Accessing the AWS Management Console
At the top of these instructions, choose  Start Lab.

The lab session starts.

A timer displays at the top of the page and shows the time remaining in the session.

 Tip: To refresh the session length at any time, choose  Start Lab again before the timer reaches 0:00.

Before you continue, wait until the circle icon to the right of the AWS  link in the upper-left corner turns green.

 

To connect to the AWS Management Console, choose the AWS link in the upper-left corner, above the terminal window.

A new browser tab opens and connects you to the console.

 Tip: If a new browser tab does not open, a banner or icon is usually at the top of your browser with the message that your browser is preventing the site from opening pop-up windows. Choose the banner or icon, and then choose Allow pop-ups.

 

if you see a message The credentials in your login link were invalid... To logout, click here, choose the here link, then double-click the AWS  link above these instructions again.  

 

Arrange the AWS Management Console tab so that it displays along side these instructions. Ideally, you will be able to see both browser tabs at the same time so that you can follow the lab steps more easily.

Tip: If you want the lab instructions to display across the entire browser window, you can hide the terminal in the browser panel. In the top-right area, clear the Terminal  check box.

 

Task 1: Preparing the development environment
In this first task, you will configure your Visual Studio Code Integrated Development Environment (VS Code IDE) so that you can use Python and the AWS Command Line Interface (AWS CLI) to interact with AWS services.

 

Connect to the VS Code IDE.

At the top of these instructions, choose i AWS Details.

Copy values from the table for the following and paste it into an editor of your choice for use later.

LabIDEURL

LabIDEPassword

In a new browser tab, paste the value for LabIDEURL to open the VS Code IDE.

On the prompt window Welcome to code-server, enter the value for LabIDEPassword you copied to the editor earlier, choose Submit to open the VS Code IDE.

 

Download and extract the files that you need for this lab.

In the same terminal, run the following command:



wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/08-lab-db-caching/code.zip -P /home/ec2-user/environment
Notice that a code.zip file was downloaded to the VS Code IDE. The file is listed in the Environment window.

To extract the files, run the following command:


unzip code.zip
 

Run a script to upgrade the AWS CLI that are installed on the VS Code IDE. It will also recreate the work that you completed in earlier labs into this AWS account.

Note: This script deploys the architecture that you created across the previous labs. This includes populating and configuring the Amazon Simple Storage Service (Amazon S3) bucket that the café website uses. The script creates the Amazon DynamoDB table and populates it with data. The script recreates the REST API that you created in the Amazon API Gateway lab. Finally, the script deploys the containerized coffee suppliers AWS Elastic Beanstalk application.

Set permissions on the script so that you can run it, and then run the script:


chmod +x ./resources/setup.sh && ./resources/setup.sh
When prompted for an IP address, enter the IPv4 address that the internet uses to contact your computer. You can find your IPv4 address at https://whatismyipaddress.com.

Note: The IPv4 address that you set is the one that will be used in the bucket policy. Only requests that originate from the IPv4 address you identify will be allowed to load the website pages. Do not set it to 0.0.0.0 because the S3 bucket's block public access settings will prevent access.

 

Verify the version of AWS CLI installed.

In the VS Code IDE Bash terminal (at the bottom of the IDE), run the following command:


aws --version
The output should indicate that version 2 is installed.

 

Verify that the SDK for Python is installed.

Run the following command:


pip3 show boto3
Note: If you see a message about not using the latest version of pip, ignore the message.

Keep the VS Code IDE open in your browser. You will use it later in this lab.

 

Task 2: Configuring the subnets for ElastiCache to use
The Memcached database must be able to communicate with the Aurora Serverless database. In addition, the application needs to be able to access both the Memcached database and the Aurora Serverless database.

In this task, you will act as Olivia to configure a security group to enable the necessary communication between the application, database, and cache. You will use the security group that the Aurora Serverless cluster is already using rather than creating an additional security group.

 

Configure the security group that the Aurora Serverless instance will use, as shown in the following diagram.  

Security group diagram

Return to the AWS Management Console browser tab.

From the Services menu, choose EC2.

In the left navigation pane, choose Security Groups.

Select the checkbox for the security group that has Aurora in the name.

In the lower pane, choose the Inbound rules tab.

Choose Edit inbound rules.

Add an entry to enable access to the Memcached port from all sources that are assigned to the Aurora security group:

Choose Add rule

Type: Choose Custom TCP

Port range: Enter 11211

Source: Choose the security group with Aurora in the name. This is the same group that you are currently editing.

Add an entry to enable access to the Memcached port from all sources that are assigned to the Lab IDE SG security group:

Choose Add rule

Type: Choose Custom TCP

Port range: Enter 11211

Source: Choose the security group with Lab IDE SG in the name

Choose Save rules.

 

Configure the database subnet group that the Aurora Serverless instance will use, as shown in the following diagram.

Security group diagram

In the search box at the top of the AWS management console, type and choose ElastiCache.

From the left navigation pane, choose Subnet groups.

Choose Create subnet group.

Configure the following settings:

Name: Enter ElastiCacheSubnetGroup

Description: Enter Subnet Group for ElastiCache

VPC ID: From the dropdown, choose IDE VPC

Notice that two subnets are already chosen for the cluster Selected subnets (2)

If you do not see this, choose Manage button on the right and select two subnets.

Choose Create.

Message is displayed stating that The subnet group was created successfully.

Next, you will deploy an ElastiCache cluster.

Task 3: Creating the ElastiCache cluster
As with the database deployment in a previous lab, the café has chosen to deploy a managed service instead of manually installing software in a container or on an EC2 instance. ElastiCache offers two engine options, Memcached and Redis. Olivia decided to use Memcached for the coffee suppliers application because the application does not require advanced features that Redis offers. Memcached will be a simple way to get started with caching, and the café could move to Redis later if needed.

In this task, you will again act as Olivia to create an ElastiCache for Memcached cluster.

 

Create an ElastiCache for Memcached instance.

Remain in the ElastiCache console.

In the left navigation pane, choose Memcached caches.

Choose Create Memcached cache. 

Configure the ElastiCache cluster with the following settings:

Engine: Ensure that Memcached is selected

Deployment option: Choose Node-based cluster

Creation method : Choose Cluster cache

In the Location section, choose AWS Cloud.

In the Cluster info section: 

Name: Enter MemcachedCache

In the Cache settings section:

Engine version: Choose 1.6.6

Port: Enter 11211 (If not already mentioned).

Parameter group: Choose default.memcached.1.6

Node type: Choose cache.r6g.large (13.07GiB)

Number of nodes: Enter 3

Under the Connectivity section, for Subnet groups

choose Choose existing subnet group

then, under Subnet groups, choose ElastiCacheSubnetGroup.

Choose Next.

On the Advanced settings page

For Selected security groups (0) choose Manage.

Select the Security group having ClusterSecurityGroup in the name.

Choose Next .

Choose Create.

 

The Memcached cluster will take up to 5 minutes to become available. Move to the next task while the cluster is being created.

You need to make sure that the cache is working correctly. In the next few tasks, you continue as Olivia to create some proof-of-concept Python code to test different data operations.

 

Task 4: Loading records into the cache from the database
The first thing you want to test is a simple read operation. Reading from cache is faster than reading from the database, so the coffee suppliers application will try to read from the cache first.

Initially, the cache will be empty and will be loaded when the database is queried. This cache management strategy is called lazy loading. Rather than proactively loading the data into cache, data is loaded after the first time that it is requested from the database. You will also configure the time to live (TTL) to limit how long the data will persist in the cache.

As you progress through the scripts, you will notice that the application code must control when the cache gets updated and how long data persists in cache.

 

To change to the directory that holds the proof-of-concept scripts, return to the VS Code IDE Bash terminal, and run the following command:


cd ~/environment/python_3
 

To install the libraries that Python needs to interact with the database and the cache, run the following commands:


sudo dnf install -y mariadb105-devel gcc python3-devel
sudo pip3 install PyMySQL
sudo pip3 install pymemcache
In the scripts, you will need to define the connection to both the Aurora database and the Memcached cache. In the following steps, you find the endpoints for these resources.

 

Find the ElastiCache for Memcached endpoint.

In the VS Code IDE Bash terminal, run the following command:


aws elasticache describe-cache-clusters
The output should be similar to the following:


{
    "CacheClusters": [
        {
            "CacheClusterId": "memcachedcache",
            "ConfigurationEndpoint": {
                "Address": "memcachedcache.xxxxxxx.cfg.use1.cache.amazonaws.com",
                "Port": 11211
            },
....
In the ConfigurationEndpoint section, make a note of the Address value. This is the ElastiCache endpoint.

Note: You may need to type q to exit back to the terminal.

 

Find the Aurora Serverless cluster endpoint.

In the VS Code IDE Bash terminal, run the following command:


aws rds describe-db-cluster-endpoints
The output should be similar to the following:


    "DBClusterEndpoints": [
        {
            "DBClusterIdentifier": "supplierdb",
            "Endpoint": "supplierdb.cluster-xxxxxxxxxxx.us-east-1.rds.amazonaws.com",
            "Status": "available",
            "EndpointType": "WRITER"
        },
        {
            "DBClusterIdentifier": "supplierdb",
            "Endpoint": "supplierdb.cluster-ro-xxxxxxx  .us-east-1.rds.amazonaws.com",
            "Status": "available",
            "EndpointType": "READER"
        }
    ]
}
Make a note of the Endpoint value where EndpointType is WRITER. 
    

Review the script that will be used to test loading data into the cache.

In the VS Code IDE window, expand the python_3 directory, and open the find_all.py file.

Review the code.

This code returns all of the coffee bean inventory information.

First, the script queries the Memcached cache. If the all_beans key is found in the cache, the data returned is printed to the console.


data = memcached_client.get('all_beans')
If no data is found in the cache, the script then queries the Aurora Serverless database. 


db_query = "SELECT * FROM beans"
mycursor = mydb.cursor()
mycursor.execute(db_query)
Any records returned from the database are also added to the cache. That way, the next time that the script is run, the data will be returned more quickly as it will be served from the cache instead of the database.


memcached_call = memcached_client.set('all_beans', output_json, TTL_INT)
Note: Note the time to live (TTL) configuration, which is set by the TTL_INT variable. The all_beans key automatically expires from the cache if it has not been accessed after 3 minutes.

 

Update the script to define the database and cache connections.

In the find_all.py file, replace <FMI_1> with the ElastiCache endpoint address.

The updated code should be similar to the following:


memcached_client = base.Client(('memcachedcache.xxxxxxx.cfg.use1.cache.amazonaws.com', 11211))
Replace <FMI_2> with the Aurora endpoint.

The updated code should be similar to the following:


mydb = pymysql.connect(
  "supplierdb.cluster-xxxxxxxxxxx.us-east-1.rds.amazonaws.com",
  "nodeapp",
  "coffee",
  "COFFEE"
)
From the navigation pane, choose  menu, then choose File > Save.

      

Test the find_all.py script.

First, ensure that the status of the Memcached cluster is available before you continue.

In the VS Code IDE Bash terminal, run the following command:


python3 find_all.py
It might take several seconds for the query to respond the first time that you run it.

The output should be similar to the following:


current time:- 2021-07-06 20:04:51.715942
Finding all items
Data not found in cache. Retrieving data from the database:
[
  {
    "id": 1,
    "supplier_id": 1,
    "type": "Arabica",
    "product_name": "Best bean",
    "price": "18.00",
    "description": "Delicious, smooth coffee.",
    "quantity": 1000
  },
  {
    "id": 2,
    "supplier_id": 1,
    "type": "Robusta",
    "product_name": "Great bean",
    "price": "12.00",
    "description": "Full bodied, good to the last drop.",
    "quantity": 800
  },

..truncated for brevity...

Setting the result in cache
True
current time:- 2021-07-06 20:05:17.784851
You can tell from the output that the cache was empty when the script ran. The message also confirms that the beans data has been written to the cache.

Make a note of the timestamps from when the script started and when it ended. What do you think will happen when you run the script again before the 3-minute TTL expires?

In the VS Code IDE Bash terminal, run the command again:


python3 find_all.py
The output should be similar to the following:


current time:- 2021-07-06 20:06:13.352247
Finding all items
Data returned from cache:
[
  {
    "id": 1,
    "supplier_id": 1,
    "type": "Arabica",
    "product_name": "Best bean",
    "price": "18.00",
    "description": "Delicious, smooth coffee.",
    "quantity": 1000
  },
  {
    "id": 2,
    "supplier_id": 1,
    "type": "Robusta",
    "product_name": "Great bean",
    "price": "12.00",
    "description": "Full bodied, good to the last drop.",
    "quantity": 800
  },

  ..truncated for brevity..
current time:- 2021-07-06 20:06:13.409011
Notice that the data is now being retrieved from the cache instead of the database. If you compare the start and end timestamps between the previous run and this one, you will find that the data is coming back much more quickly.

 

Next, you will test an update to a record. The rest of the test scripts will be very similar to find_all.py.

 

Task 5: Updating data
The next operation you need to test is an update to an item in the database. You know that the application will try to read data from the cache before looking for data in the database. This means that you must ensure that the cache continues to return current information when records change in the database. Otherwise, the cache becomes stale, and the application can provide inaccurate results. Imagine a customer thinking that they have ordered an item when it was really out of stock. You don't want unhappy customers. Keep the cache current to prevent this from happening.

 

Review the script that will be used to test an update to a record in the Aurora database.

In the VS Code IDE window, expand the python_3 directory, and open the update_item.py file.

Review the code to understand what it does.

Notice that instead of sending a SELECT statement to the database, the cursor sends an UPDATE statement. The bean item will be updated with the values defined in the vals variable.


db_query = "UPDATE beans SET supplier_id=%s, type=%s, product_name=%s, price=%s, description=%s, quantity=%s WHERE id=%s"
vals = (1, "Arabica Arabica","Best bean EVER","28.00","So delicious, smooth coffee.", 800, 1)
The cursor sends both the query and the replacement values to the database.


mycursor.execute(db_query, vals)
Also notice that, instead of reading the all_beans key from the cache, the cache is deleted.


memcached_call = memcached_client.delete('all_beans')
This code is using the write-through caching strategy because it updates the cache when the database receives a change. This strategy ensures that the data in the cache does not become stale. In this example, the key is completely removed from the cache. The cache will be refreshed with current database records the next time that the find_all.py script is run.

Note: Depending on how cache keys are structured, updating an item in the cache rather than purging the key could also be a good option. In this simplified example, the key contains all items, which makes updating a single item more cumbersome.

 

Test the update_item.py script.

Update the <FMI_1> and <FMI_2> placeholders as you did previously.

Run the update.py script:


python3 update_item.py
The output should be similar to the following:


Updating a bean item
Updated item in RDS
FLUSH the CACHE as it is stale
Purged the cache: True
 

Now, to test the cache refresh.

Run the find_all.py script:


python3 find_all.py
The output should be similar to the following:


Finding all items
Data not found in cache. Retrieving data from the database:
[
  {
    "id": 1,
    "supplier_id": 1,
    "type": "Arabica Arabica",
    "product_name": "Best bean EVER",
    "price": "28.00",
    "description": "So delicious, smooth coffee.",
    "quantity": 800
  },
  ..truncated for brevity..
Run the script again to ensure that the data is being returned from the cache.

The output should be similar to the following:


Finding all items
Data returned from cache:
[
  {
    "id": 1,
    "supplier_id": 1,
    "type": "Arabica Arabica",
    "product_name": "Best bean EVER",
    "price": "28.00",
    "description": "So delicious, smooth coffee.",
    "quantity": 800
  },
  {
    "id": 2,

..truncated for brevity..
  
​  
​    Well done! You've created a script that updates the database and also ensures that the cache stays up to date. 

    

Next, you will create a script to test adding a new coffee item to the database.

 

Task 6: Creating a new record
In this task, you will create a new item in the database. You will use the write-through caching strategy to prevent the cache from becoming stale.

 

Review the script that will be used to test creating a record in the Aurora database.

In the VS Code IDE window, expand the python_3 directory, and open the create_item.py file.

Review the code to understand what it is doing.

The key difference between update_item.py and create_item.py is the database query. The create_item.py script adds a record instead of updating an existing one. 


db_query = "INSERT INTO beans (supplier_id, type, product_name, price, description, quantity) VALUES (%s, %s, %s, %s, %s, %s)"
vals = (1, 'Java Java','Worlds greatest bean','38.00','Nutty tasting coffee.',400 )
 

Test the create_item.py script.

Update the <FMI_1> and <FMI_2> placeholders as you did previously.

Run the update.py script:


python3 create_item.py
The output should be similar to the following:


Adding a new bean item
1 record(s) inserted into RDS.
FLUSH the CACHE as it is stale
Purged the cache: True
 

Test the cache refresh again.

Run the find_all.py script:


python3 find_all.py
The output should be similar to the following:


Finding all items
Data not found in cache. Retrieving data from the database:
[
  {
    "id": 1,
    "supplier_id": 1,
    "type": "Arabica Arabica",
    "product_name": "Best bean EVER",
    "price": "28.00",
    "description": "So delicious, smooth coffee.",
    "quantity": 800
  },
  {
    "id": 2,

..truncated for brevity..

  {
    "id": 15,
    "supplier_id": 1,
    "type": "Java Java",
    "product_name": "Worlds greatest bean",
    "price": "38.00",
    "description": "Nutty tasting coffee.",
    "quantity": 400
  }
]
Setting result in cache
True

Run find_all.py again to see the new item return from the cache:


Finding all items
FROM CACHE: [ { id: 1,
    supplier_id: 1,
    type: 'Arabica Arabica',
    product_name: 'Best bean EVER',
    price: '28.00',
    description: 'So delicious, smooth coffee.',
    quantity: 800 },

..truncated for brevity..

  { id: 15,
    supplier_id: 1,
    type: 'Java Java',
    product_name: 'Worlds greatest bean',
    price: '38.00',
    description: 'Nutty tasting coffee.',
    quantity: 400 } ]
Note: If the data is not returning from the cache wait a minut and run the command again.

Nicely done!

 

In the final test, you will remove a record from the database.

 

Task 7: Deleting a record
The final proof-of-concept script tests deleting an item from the database. You will again use the write-through strategy to ensure the cache stays in sync with the database.

 

Review the script that will be used to test deleting a record from the Aurora database.

In the VS Code IDE window, expand the python_3 directory, and open the delete_item.py file.

Review the code:


db_query = "DELETE FROM beans WHERE id=%s"
val = (14,)
Again, the main difference in this script is in the database query. The SQL statement deletes (removes) an item from the database.

You should also recognize the caching pattern in the code. Any time a change is made to the database, the cache will be purged to force a clean refresh during the next read operation.

 

Test the delete_item.py script.

Update the <FMI_1> and <FMI_2> placeholders as you did previously.

Run the delete_item.py script:


python3 delete_item.py
The output should be similar to the following:


Deleting a bean item
1 record(s) deleted from RDS.
FLUSH the CACHE as it is stale
Purged the cache: True
 

You can test the find_all.py script again to verify that the record was removed from the database and that the cache is refreshing as expected.

 

Awesome job! You have created and tested a few scripts to prove that the cache and database are working properly.

 

Nikhil has started helping Sofía with the café's application code. You are going to send this proof-of-concept code to Nikhil so that he can follow these examples and incorporate caching into the coffee suppliers application Node.js code.

 

Task 8: Updating the application container
Nikhil quickly updated the coffee suppliers application. His code expanded on the examples from the proof of concept. He restructured the code, and now rather than having a script for each type of operation (SELECT, INSERT, UPDATE, DELETE), one script handles all database calls, and another interacts with the cache. He also modified the code to use an environment variable to identify the ElastiCache for Memcached endpoint.

You will perform the following steps as Nikhil to review the application code that interacts with the cache. Then, you will update the application.

 

Review the new code. Notice how similarly Node.js and Python work with Memcached. Also, recognize the changes that have been made to optimize cache utilization.

Note: Don't worry about understanding everything that is happening in the Node.js script. Focus on the larger patterns. It can be helpful to follow the messages that are included in the code.

In VS Code IDE, in the Environment window, expand the resources directory, and open the bean.controller_2.js file. 

Locate and review the following lines of code:


const memcachedHost = process.env.MEMC_HOST || "localhost";
const memcachedPort = '11211';
const cacheTtlInSec = 300;
The code above sets up the endpoint, port, and Time to Live settings for the Memcached connection. The MEMC_HOST value will be populated by an environment variable that you will set up later.

 


return res.render("bean-list-all", {beans: JSON.parse(data), cache_msg: "results from Cache"});

res.render("bean-list-all", {beans: data, cache_msg: "results from Db"});
The two lines of code above were added to display a note on the website about whether the response came from cache or the database.

 


memcached.set('beans_' + data.id, JSON.stringify(data), cacheTtlInSec, function (err) {
The line of code above optimizes the cache usage by storing individual items. To return all items, you can still use the all_beans key. However, to return a single item, you can now use a key that is associated with a specific inventory item. This limits the amount of data that must be read and returned over the network to the application.

 


exports.findOne = (req, res) => {
 Finally, you added code to select individual keys when it is not necessary to return everything.

    

To update the application code, run the following command:


mv ~/environment/resources/bean.controller_2.js \
~/environment/resources/codebase_partner/app/controller/bean.controller.js
 

To rebuild and update the Docker image, run the following commands:


cd ~/environment/resources/codebase_partner/
npm install
docker build --tag node_app .
 

Authorize your Docker client to connect to the Amazon Elastic Container Registry (Amazon ECR) service.

Discover your AWS account ID:

In the AWS Management Console, in the upper-right corner, choose your user name, which begins with voclabs/user.

Copy the My Account value from the menu. This is your AWS account ID.

Return to the VS Code IDE Bash terminal.

To authorize your VS Code IDE Docker client, run the following command. Replace  with the actual account ID that you just found in the console:


aws ecr get-login-password \
--region us-east-1 | docker login --username AWS \
--password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
A message indicates that the login succeeded.

 

Push the updated container image to Amazon ECR.

To find the URI for the repository, run the following command:


aws ecr describe-repositories --query repositories[][repositoryUri] --output text
The output should be similar to the following:


xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/cafe/node-web-app
 

Next, to tag the Amazon ECR image, run the following command. Replace <FMI_1> with the repository URI:


docker tag node_app:latest <FMI_1>:latest
The updated command should be similar to the following:


docker tag node_app:latest xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/cafe/node-web-app:latest
 

Now, to push the image to Amazon ECR, run the following command. Again, replace <FMI_1> with the repository URI:


docker push <FMI_1>:latest
The updated command should be similar to the following:


docker push xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/cafe/node-web-app:latest
The output should be similar to the following:


8df1a11d2c34: Pushed 
3a21fd1e1e85: Pushed 
78c260a1577d: Layer already exists 
d81d715330b7: Layer already exists 
1dc7f3bb09a4: Layer already exists 
dcaceb729824: Layer already exists 
f1b5933fe4b5: Layer already exists 
latest: digest: sha256:8a9137a92347982bbf368ae500131cf8c7f2c69d227dfe7d7c529c81cba1b5ee size: 1786
These messages verify that the existing image was updated.

 

Test your Elastic Beanstalk website.

On the search bar at the top, search for and select Elastic Beanstalk.

In the list of environments, choose the MyEnv link.

On the MyEnv page, choose the URL directly under MyEnv to open the currently deployed application.

The application opens in a new browser tab.

Append /beans to the URL in the application browser tab.

Note: If you receive an error page, wait a few seconds and reload the beans page. This error can occur because the database did not respond quickly enough. It should work on the second try.

The application is still using the old code and needs to be updated to use the container that you just pushed to the repository.

Keep this browser tab open because you will return to it shortly.

 

 

Recall that the updated Node.js application requires an environment variable to set the Memcached endpoint.

Configure the new Memcached environment variable, MEMC_HOST.

Return to the browser tab with the MyEnv page.

In the left navigation pane, choose Configuration.

In the Updates, monitoring, and logging category, choose Edit.

Scroll down to the Environment properties section, and add Add environment property as follows:

Name: Enter MEMC_HOST

Value: Enter the same Memcached endpoint that you used when testing the Python scripts

Choose Apply.

A message indicates that Elastic Beanstalk is updating your environment.

It takes a few minutes for the environment to be updated. Once the build has finished, you can continue.

Revisit the browser tab with the coffee suppliers application, and refresh the page.

A note now appears under All beans to indicate when the results were returned from the database and when they were returned from the cache.
    

Test the code update from the café website.

Return to the browser tab with the MyEnv page.

From the Services menu, choose S3.

Locate the bucket that has s3bucket in the name and choose the associated link.

Choose the Properties tab and then scroll down to the Static website hosting section.

Choose the website endpoint link to open the café's website in a new tab.

On the café's website, choose the menu, and then choose Buy Coffee.

The list of beans is returned and is the same as the list that was returned when you were testing from the command line.

 

Congratulations! You have created an ElastiCache for Memcached cluster, configured network security to allow calls to the cache, and updated the application code to use the cache to front end the database call. These actions will speed up performance for the café's customers.

 

Update from the café
Olivia and Nikhil made a great team on this update to the website. Frank and Martha are happy with the improvements and are getting even more compliments about the website now. To celebrate, they give Olivia and Nikhil free coffee and pastries for the next week! The café will enjoy this success and will continue to find new ways that they can improve the customer experience.

 

Submitting your work
To record your progress, choose Submit at the top of these instructions.

 

When prompted, choose Yes.

After a couple of minutes, the grades panel appears and shows you how many points you earned for each task. If the results don't display after a couple of minutes, choose Grades at the top of these instructions.

 Tip: You can submit your work multiple times. After you change your work, choose Submit again. Your last submission is recorded for this lab.

 

To find detailed feedback about your work, choose Submission Report.
    

 

Lab complete 
 Congratulations! You have completed the lab.

At the top of this page, choose  End Lab, and then choose Yes to confirm that you want to end the lab.

A message panel indicates that the lab is terminating.

 

To close the panel, choose Close in the upper-right corner.

 

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This work may not be reproduced or redistributed, in whole or in part, without prior written permission from Amazon Web Services, Inc. Commercial copying, lending, or selling is prohibited.