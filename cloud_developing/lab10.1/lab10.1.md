Lab 10.1: Implementing a Messaging System Using Amazon SNS and Amazon SQS
Lab overview and objectives
In this lab, you will use Amazon Simple Queue Service (Amazon SQS) and Amazon Simple Notification Service (Amazon SNS) to set up a system to receive, queue, and send data for an application to process. You will use a Python publisher to send messages to a notification topic. You will also review the Node.js consumer that a web application will use to retrieve and process the data from a queue.

 

After completing this lab, you should be able to:

Configure SNS topics and SQS queues to support programmatic receipt of messages

Develop an Amazon SNS publisher to send messages to an SNS topic

Develop an Amazon SQS consumer to read messages from an SQS queue

 

Duration
This lab will require approximately 90 minutes to complete.

 

AWS service restrictions
In this lab environment, access to AWS services and service actions might be restricted to the ones that are needed to complete the lab instructions. You might encounter errors if you attempt to access other services or perform actions beyond the ones that are described in this lab.

 

Scenario
Customers love being able to buy coffee beans from the café, but maintaining the bean inventory is time-consuming. Café employees must call each coffee supplier and then use the coffee suppliers web application to manually update each record. Frank has asked Sofía if she can find a better way to keep the coffee inventory current. He would like café staff to spend more time helping customers and less time doing data entry.

Sofía has researched setting up a messaging system to automatically receive and process inventory updates. Mateo, a café regular and AWS consultant, suggested using an SNS topic to receive messages from suppliers, and an SQS queue to store the messages until the application is ready to process them. This way, the café application won't lose any messages if the application or database happens to be unavailable. He also highly recommended that she create a dead-letter queue to handle messages that cannot be processed. Mateo also explained that suppliers will need to run a script called a producer to publish their updates to the SNS topic. The coffee suppliers application code will need to include a consumer to poll and retrieve messages from the SQS queue.

In this lab, you will again play the role of Sofía as you develop the automated inventory processing for the café's coffee suppliers application.

When you start the lab, the coffee suppliers application is set up for a café employee to manually update inventory information on the website after calling the suppliers, as shown in the following diagram.

Architecture at the beginning of the lab.

By the end of this lab, you will have a producer script that suppliers can use to send inventory updates to an SNS topic. The topic will forward the messages to the SQS queue to wait to be processed. The coffee suppliers application will include a new Amazon SQS consumer to poll and retrieve messages from the queue. If the application successfully processes a record, the database will be updated. If a record fails to process, it will be returned to the SQS queue. If the record fails to process several times, it will be moved to the dead-letter queue.

The following diagram shows what the architecture of the coffee suppliers application will look like at the end of the lab.

Architecture at the end of the lab.

Note: The application details in these diagrams have been simplified to highlight how the inventory data moves through the system. Caching is still being used in the data layer.

 

Accessing the AWS Management Console
At the top of these instructions, choose Start Lab to launch your lab.

A Start Lab panel opens, and it displays the lab status.

Tip: If you need more time to complete the lab, choose the Start Lab button again to restart the timer for the environment.

 

Wait until you see the message Lab status: ready, then close the Start Lab panel by choosing the X.

 

At the top of these instructions, choose AWS.

This opens the AWS Management Console in a new browser tab. The system will automatically log you in.

Tip: If a new browser tab does not open, a banner or icon is usually at the top of your browser with a message that your browser is preventing the site from opening pop-up windows. Choose the banner or icon and then choose Allow pop ups.

 

Arrange the AWS Management Console tab so that it displays along side these instructions. Ideally, you will be able to see both browser tabs at the same time so that you can follow the lab steps more easily.

Tip: If you want the lab instructions to display across the entire browser window, you can hide the terminal in the browser panel. In the top-right area, clear the Terminal  check box.

 

Task 1: Preparing the development environment
In this first task, you will configure your Visual Studio Code Integrated Development Environment (VS Code IDE). You will also run the script to recreate the work you completed in previous labs.

 

Before proceeding to the next step, verify that the AWS CloudFormation stack creation process for the lab has successfully completed.

In a new browser tab, navigate to the CloudFormation console.

In the left navigation pane, choose Stacks.

For the stack with "ACD_2.0" in the Description column, verify that the Status says CREATE_COMPLETE. 

⚠️ If the stack does not yet show status CREATE_COMPLETE, wait until it does. Because this stack is creating an Amazon Relational Database Service (Amazon RDS) database instance, it might take about 5 minutes to complete.

 

Connect to the VS Code IDE.

At the top of these instructions, choose Details followed by  AWS: Show 

Copy values from the table for the following and paste it into an editor of your choice for use later.

LabIDEURL

LabIDEPassword

In a new browser tab, paste the value for LabIDEURL to open the VS Code IDE.

On the prompt window Welcome to code-server: 

Enter the value for LabIDEPassword you copied to the editor earlier

Choose Submit to open the VS Code IDE similar to below.

 

Download and extract the files that you need for this lab.

In the same terminal, run the following command:



wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/10-lab-sqs/code.zip -P /home/ec2-user/environment
Notice that a code.zip file was downloaded to the VS Code IDE. The file is listed in the environment window.

Extract the file:


unzip code.zip
 

Run a script to upgrade the version of Python and the AWS CLI that are installed on the VS Code IDE. The script also recreates the work that you completed in earlier labs into this AWS account.

Set permissions on the script so that you can run it, and then run the script:


chmod +x ./resources/setup.sh && ./resources/setup.sh
When prompted for an IP address, enter the IPv4 address that the internet uses to contact your computer. You can find your IPv4 address at https://whatismyipaddress.com.

Note: The IPv4 address that you set is the one that will be used in the bucket policy. Only requests that originate from this IPv4 address will be allowed to load the website pages. Do not set it to 0.0.0.0 because the S3 bucket's block public access settings will prevent access.

Verify that the script did not encounter any errors. 

If you see any "An error occurred" lines just before the "done" line, the script might have been run too soon after you started the lab. Run the setup.sh script again to clear errors.

If you don't see any error lines, you can assume that the script ran successfully.

Analysis: The CloudFormation template that ran when you started this lab created resources in the AWS account. The script that you ran also created resources. Between the two of them, resources have been created to replicate what you built in previous labs.

 

Verify the version of AWS CLI installed.

In the VS Code IDE Bash terminal (at the bottom of the IDE), run the following command:


aws --version
The output should indicate that version 2 is installed.

 

Verify that the SDK for Python is installed.

Run the following command:


pip3 show boto3
Note: If you see a message about not using the latest version of pip, ignore the message.

  

In VS Code IDE, open a new file, and copy and paste the following text. You will capture a few pieces of information to use during the lab. Keep this file open as you work through the lab.


DeadLetterQueue QueueUrl:
AWS Account ID:
updated_beans.fifo QueueUrl: 
updated_beans.fifo QueueArn: 
updated_beans_sns.fifo TopicArn:
 

Task 2: Configuring the Amazon SQS dead-letter queue
In a perfect world, all messages sent to queues would be formatted correctly and processed successfully. However, this doesn't happen in the real world. An important part of your queue configuration is to build error handling for messages that cannot be processed.

In this task, you will create a dead-letter queue. Later, when you configure the main processing queue, you will define this dead-letter queue as the target for messages that cannot be processed. The dead-letter queue must already exist for you to define it as the target for another queue, so create the dead-letter queue first.

 

Create your dead-letter queue
Review the attributes that will define your Amazon SQS dead-letter queue.

In the VS Code IDE, expand resources/sqs-sns and open the create-dlq.json file.

Review the contents of the file:


{
    "FifoQueue": "true",
    "VisibilityTimeout": "20",
    "ReceiveMessageWaitTimeSeconds": "0",
    "ContentBasedDeduplication": "false",
    "DeduplicationScope": "queue"
}
Analysis: This input file will configure an SQS queue to use First-In-First-Out (FIFO) message ordering. The VisibilityTimeout is set to 20 seconds to make messages temporarily invisible to other potential consumers while the message is being processed. To immediately receive new messages, ReceiveMessageWaitTimeSecond is set to 0, which is also known as short polling. Because the ContentBasedDeduplicaiton option is set to false, using a message deduplication ID will be optional.

For more information about SQS queue configuration, see the Amazon Simple Queue Service Developer Guide.

Create an Amazon SQS dead-letter queue.

In the VS Code IDE bash terminal, change to the sns-sqs directory:


cd ~/environment/resources/sqs-sns
Create a dead-letter queue named DeadLetterQueue.fifo:


aws sqs create-queue --queue-name DeadLetterQueue.fifo --attributes file://create-dlq.json
The output is similar to the following:


{
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/111111111111/DeadLetterQueue.fifo"
}
In your text file, save the DeadLetterQueue QueueURL to use in a later step.

 

Secure the DeadLetterQueue.fifo queue
Review the access policy that you will apply to the DeadLetterQueue.fifo queue.


{
  "Version": "2008-10-17",
  "Id": "DlqSqsPolicy",
  "Statement": [
    {
      "Sid": "dead-letter-sqs",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<FMI_1>:root"
      },
      "Action": [
        "SQS:*"
      ],
      "Resource": "arn:aws:sqs:us-east-1:<FMI_1>:DeadLetterQueue.fifo"
    }
  ]
}
Analysis: This policy will restrict the ability to send and receive messages to the dead-letter queue. Only the owner of the queue will be able to communicate with the queue.

   

Update the policy statement with your AWS account ID.

In the environment window, under resources/sqs-sns, open the dlq-policy.json file.

The Policy attribute's value is the same as the policy that you just reviewed. However, to work with the AWS Command Line Interface (AWS CLI), the entire policy must be formatted on a single line. In addition, the double quotes (") that are part of the policy definition must be escaped with a backslash (\) for the AWS CLI to correctly interpret the policy definition.


{"Policy": "{\"Version\": \"2008-10-17\",\"Id\": \"DlqSqsPolicy\",\"Statement\": [{\"Sid\": \"dead-letter-sqs\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:iam::<FMI_1>:root\"},\"Action\": [\"SQS:*\"],\"Resource\": \"arn:aws:sqs:us-east-1:<FMI_1>:DeadLetterQueue.fifo\"}]}"}
In the dlq-policy.json file, replace the two <FMI_1> placeholders with your AWS account ID.

Note: To find your account ID, run the aws sts get-caller-identity command. Save the account ID in the text file you opened so that you don't have to look it up again.

After you update the file, it looks similar to the following:


{"Policy": "{\"Version\": \"2008-10-17\",\"Id\": \"DlqSqsPolicy\",\"Statement\": [{\"Sid\": \"dead-letter-sqs\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:iam::111111111111:root\"},\"Action\": [\"SQS:*\"],\"Resource\": \"arn:aws:sqs:us-east-1:111111111111:DeadLetterQueue.fifo\"}]}"}
Save your changes.

  

In the terminal window, run the following command to update the dead-letter queue's access policy. Replace the <FMI_1> placeholder with the DeadLetterQueue QueueURL from your text file:


aws sqs set-queue-attributes --queue-url "<FMI_1>" --attributes file://dlq-policy.json
The updated command is similar to the following:


aws sqs set-queue-attributes --queue-url "https://sqs.us-east-1.amazonaws.com/111111111111/DeadLetterQueue.fifo" --attributes file://dlq-policy.json
If the command completes successfully, you are returned to the command prompt, and output doesn't display in the terminal.

 

Task 3: Configuring the SQS queue
Now that your dead-letter queue is ready, you need a separate queue to receive and store messages that the coffee suppliers application will process. You will use the default message retention of 4 days. However, the queue message retention can range from as short as 1 minute to as long as 14 days.

In this task, you will create a new queue named updated_beans.fifo to store records that the application hasn't yet processed. This new queue will send messages that fail to process to the dead-letter queue, as shown in the following diagram.

updated_beans.fifo queue sends bad messages to DeadLetterQueue.fifo.

 

Create the queue to receive messages from the SNS topic
Review the attributes that will define your SQS queue.

In the environment window, under resources/sqs-sns, open the create-beans-queue.json file.

Review the contents of the file:


{
    "FifoQueue": "true",
    "VisibilityTimeout": "30",
    "ReceiveMessageWaitTimeSeconds": "20",
    "ContentBasedDeduplication": "true",
    "DeduplicationScope": "queue",
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:<FMI_1>:DeadLetterQueue.fifo\",\"maxReceiveCount\":\"5\"}"
}
Analysis: The dead-letter queue and queues that will forward messages to it must use the same message ordering, so this queue is also configured to use FIFO. The VisibilityTimeout will make messages temporarily invisible to other potential consumers for 30 seconds. With ReceiveMessageWaitTimeSeconds set to 20, this queue will use long polling to query messages. Because ContentBasedDeduplication is set to true, all messages will require a unique deduplication ID. Finally, notice the new attribute named RedrivePolicy. This attribute identifies the dead-letter queue that will receive messages that fail to process.

For more information about queue short and long polling, see the Amazon Simple Queue Service Developer Guide.

 

In the create-beans-queue.json file, replace the <FMI_1> placeholder with your AWS account ID.

 

Save your changes.

 

In the terminal window, run the following command to create a queue named updated_beans.fifo:


aws sqs create-queue --queue-name updated_beans.fifo --attributes file://create-beans-queue.json 
The output is similar to the following:


{
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/111111111111/updated_beans.fifo"
}
 

In your text file, save the updated_beans.fifo QueueURL to use in a later step.

 

Secure the updated_beans.fifo queue
Review the access policy that you will apply to the updated_beans.fifo queue.


{
  "Version": "2008-10-17",
  "Id": "BeansSqsPolicy",
  "Statement": [
    {
      "Sid": "beans-sqs",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<FMI_1>:root"
      },
      "Action": "SQS:*",
      "Resource": "arn:aws:sqs:us-east-1:<FMI_1>:updated_beans.fifo"
    },
    {
      "Sid": "topic-subscription",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<FMI_1>:root",
        "Service": "sns.amazonaws.com"
      },
      "Action": "SQS:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:<FMI_1>:updated_beans.fifo",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:sns:us-east-1:<FMI_1>:updated_beans_sns.fifo"
        }
      }
    },
    {
      "Sid": "get-messages",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::<FMI_1>:role/aws-elasticbeanstalk-ec2-role",
          "arn:aws:iam::<FMI_1>:root"
        ]
      },
      "Action": [
        "sqs:ChangeMessageVisibility",
        "sqs:DeleteMessage",
        "sqs:ReceiveMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:<FMI_1>:updated_beans.fifo"
    }
  ]
}
Analysis: The Sid named BeansSqsPolicy gives full Amazon SQS access to the queue owner. The Sid named topic-subscription allows the updated_beans_sns.fifo topic to send messages to the queue. The Sid named get-messages allows resources that are assigned the aws-elasticbeanstalk-ec2-role role (the role that AWS Elastic Beanstalk instances use) to retrieve and manage messages in the queue. The SNS topic doesn't exist yet. You will create it in a later task. However, you can include it in the access policy now because you know that it will be named updated_beans_sns.fifo.

 

Update the policy statement with your AWS account ID.

In the environment window, under resources/sqs-sns, open the beans-queue-policy.json file.

Replace all eight <FMI_1> placeholders with your AWS account ID.

 

  After you update the file, it looks similar to the following:


{"Policy": "{\"Version\": \"2008-10-17\",\"Id\": \"BeansSqsPolicy\",\"Statement\": [{\"Sid\": \"beans-sqs\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:iam::111111111111:root\"},\"Action\": \"SQS:*\",\"Resource\": \"arn:aws:sqs:us-east-1:111111111111:updated_beans.fifo\"},{\"Sid\": \"topic-subscription\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:iam::111111111111:root\",\"Service\": \"sns.amazonaws.com\"},\"Action\": \"SQS:SendMessage\",\"Resource\": \"arn:aws:sqs:us-east-1:111111111111:updated_beans.fifo\",\"Condition\": {\"ArnLike\": {\"aws:SourceArn\": \"arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo\"}}},{\"Sid\": \"get-messages\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": [\"arn:aws:iam::111111111111:role/aws-elasticbeanstalk-ec2-role\",\"arn:aws:iam::111111111111:root\"]},\"Action\": [\"sqs:ChangeMessageVisibility\",\"sqs:DeleteMessage\",\"sqs:ReceiveMessage\"],\"Resource\": \"arn:aws:sqs:us-east-1:111111111111:updated_beans.fifo\"}]}"}
Save your changes.

 

In the terminal window, run the following command to update the updated_beans.fifo queue's policy. Replace the <FMI_1> placeholder with the updated_beans.fifo QueueURL that you saved earlier:


aws sqs set-queue-attributes --queue-url "<FMI_1>" --attributes file://beans-queue-policy.json
The updated command is similar to the following:


aws sqs set-queue-attributes --queue-url "https://sqs.us-east-1.amazonaws.com/111111111111/updated_beans.fifo" --attributes file://beans-queue-policy.json
If the command completes successfully, you are returned to the command prompt, and output doesn't display in the terminal.

   

Retrieve the ARN for the updated_beans.fifo queue to use later.

Run the following command. Replace the <FMI_1> placeholder with your AWS account ID.


aws sqs get-queue-attributes --queue-url "https://sqs.us-east-1.amazonaws.com/<FMI_1>/updated_beans.fifo" --attribute-names QueueArn
The output is similar to the following:


{
    "Attributes": {
        "QueueArn": "arn:aws:sqs:us-east-1:111111111111:updated_beans.fifo"
    }
}
In a text editor, make a note of the ARN for the updated_beans.fifo queue. 

 

Now you have a queue that can store messages in the order they are received and also prevent data duplication. The coffee suppliers application will process messages in this queue. Well done!

 

Next, you need to set up an SNS topic for the coffee suppliers to use to send inventory updates to your application.

Task 4: Configuring the SNS topic
Amazon SQS and Amazon SNS can work closely together to create a reliable, fault-tolerant architecture to process messages. For more information about using Amazon SNS and Amazon SQS together, see the Amazon Simple Notification Service Developer Guide.

In this task, you will create a new topic named updated_beans_sns.fifo. You will also configure its security settings so that it's only open to the account owner while you develop the new application functionality.

 

Create the SNS topic to receive inventory updates from suppliers
To create the SNS topic, run the following command:


aws sns create-topic --name updated_beans_sns.fifo --attributes DisplayName="updated beans sns",ContentBasedDeduplication="true",FifoTopic="true"
Notice that this topic is also using FIFO ordering, just like the updated_beans.fifo queue. Content-based deduplication helps prevent publishers from passing the same message twice in the same batch of records. You don't want accidental compounding increments in your inventory data.

Note: When you configure message deduplication in Amazon SNS, messages with identical content won't be processed again for 5 minutes. After the 5-minute deduplication interval has expired, if the message is sent again, it will be processed.

 

The output is similar to the following:


{
    "TopicArn": "arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo"
}
 

In your text file, save the updated_beans_sns.fifo TopicArn to use in a later step.

 

Secure the updated_beans_sns.fifo topic
Review the access policy that you will apply to the SNS topic. 


{
  "Version": "2008-10-17",
  "Id": "BeansTopicPolicy",
  "Statement": [
    {
      "Sid": "BeansAllowActions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<FMI_2>:root"
      },
      "Action": [
        "SNS:Publish",
        "SNS:RemovePermission",
        "SNS:SetTopicAttributes",
        "SNS:DeleteTopic",
        "SNS:ListSubscriptionsByTopic",
        "SNS:GetTopicAttributes",
        "SNS:Receive",
        "SNS:AddPermission",
        "SNS:Subscribe"
      ],
      "Resource": "arn:aws:sns:us-east-1:<FMI_2>>:updated_beans_sns.fifo",
      "Condition": {
        "StringEquals": {
          "AWS:SourceOwner": "<FMI_2>"
        }
      }
    },
    {
      "Sid": "BeansAllowPublish",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<FMI_2>:root"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:us-east-1:<FMI_2>:updated_beans_sns.fifo"
    }
  ]
}
Analysis: The Sid named BeansAllowActions gives full Amazon SNS privileges to the topic owner. The second Sid limits publish privileges to the topic owner. In the real world, you would update the BeansAllowPublish permissions to include other principals such as AWS Identity and Access Management (IAM) users, IAM groups, or other AWS accounts that need to be able to send messages to the topic; for example, the coffee bean suppliers. For more information about granting access to SNS topics, see the Amazon Simple Notification Service Developer Guide.

 

Update the policy statement with your AWS account ID.

In the environment window, under resources/sqs-sns, open the beans-topic-policy.json file.

Note: When you work with the AWS CLI, the Amazon SNS policy definition must follow the same syntax that you used for the Amazon SQS policies. The definition must be on a single line, and the double quotes must be escaped using a backslash.

Update the placeholders:

Replace the <FMI_1> placeholder with the updated_beans_sns.fifo TopicArn that you saved earlier. 

Replace the five <FMI_2> placeholders with your AWS account ID. 

 

After you update the file, it looks similar to the following:


{
    "TopicArn": "arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo",
    "AttributeName": "Policy",
    "AttributeValue": "{\"Version\": \"2008-10-17\",\"Id\": \"BeansTopicPolicy\",\"Statement\": [{\"Sid\": \"BeansAllowActions\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"arn:aws:iam::111111111111:root\"},\"Action\": [\"SNS:Publish\",\"SNS:RemovePermission\",\"SNS:SetTopicAttributes\",\"SNS:DeleteTopic\",\"SNS:ListSubscriptionsByTopic\",\"SNS:GetTopicAttributes\",\"SNS:Receive\",\"SNS:AddPermission\",\"SNS:Subscribe\"],\"Resource\": \"arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo\",\"Condition\": {\"StringEquals\": {\"AWS:SourceOwner\": \"111111111111\"}}},{\"Sid\": \"BeansAllowPublish\",\"Effect\": \"Allow\",\"Principal\": {\"AWS\": \"*\"},\"Action\": \"SNS:Publish\",\"Resource\": \"arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo\"}]}"
}
Save your changes.

To apply the policy to your queue, run the following command.


aws sns set-topic-attributes --cli-input-json file://beans-topic-policy.json
If the command completes successfully, you are returned to the command prompt, and output doesn't display in the terminal.

 

 

Task 5: Linking Amazon SQS and Amazon SNS
When a message is pushed to an SNS topic, the SQS queue needs to know. Therefore, you must configure a subscription to loosely couple these two systems together.

In this task, you will set up a subscription so that notifications sent to the updated_beans_sns.fifo topic are forwarded to the updated_beans.fifo queue. Remember that the updated_beans.fifo queue will send messages that can't be processed to the dead-letter queue. This process flow is shown in the following diagram.

The SNS topic sends messages to the SQS queue, which then sends bad messages to the dead-letter queue.

Create a subscription from the SQS queue to the SNS topic.

Update the following command:

Replace the <FMI_1> placeholder with the update_beans_sns.fifo TopicArn.

Replace the <FMI_2> placeholder with the updated_beans.fifo QueueArn.


aws sns subscribe --topic-arn "<FMI_1>" --protocol sqs --notification-endpoint "<FMI_2>"
The updated command is similar to the following:


aws sns subscribe --topic-arn "arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo" --protocol sqs --notification-endpoint "arn:aws:sqs:us-east-1:111111111111:updated_beans.fifo"
 

Run the command in the terminal window.

 

The output is similar to the following:


{
    "SubscriptionArn": "arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo:858ff46f-4013-440b-9da8-f923ccf258ff"
}
 

Great work! 

Task 6: Testing message publishing
Now that the components are configured to communicate together, it's time to test the integration between the SNS topic and the SQS queue. In addition to verifying that the queue can receive messages from the topic, you need to ensure that content deduplication works. You also want to understand how the queue receives message metadata, because you might want to use the metadata to filter messages when you refine notification processing in the future.

To test the integration, you will use a Python script and text files containing a few records to publish four messages to the topic. To test the duplication, two messages in one of the text files are identical. Also, one message will include metadata so that you can see what that information looks like in the queue.

Note: You cannot change the deduplication interval. For FIFO queues, the deduplication interval is fixed at 5 minutes. Deduplication will monitor for duplication of the message even if it is deleted from the queue.

The integration is set up to work as shown in the following diagram.

A human uses the publisher script to send messages to the SNS topic. The topic forwards messages to the queue. The queue sends bad messages to the dead-letter queue.

 

Review the Python publisher code
In the environment window, under resources/sqs-sns, open the send_beans_update.py file.

 

Review the code associated with the following snippets:

The sns_topic variable defines the SNS topic's ARN.


sns_topic = 'arn:aws:sns:us-east-1:<FMI>:updated_beans_sns.fifo'
 

The following line sets up the Amazon SNS Boto3 client connection.


sns_client = boto3.client('sns')
 

A for loop cycles through the messages that are read from the text file.


...
for message_data in file_handle:
...
 

If the supplier has coffee beans available, the final number in the batch data will be greater than 0. In this case, the adding_beans variable sends the record to the SNS topic for processing.

However, if a supplier doesn't have inventory of a particular bean, they send a zero for the Quantity value. When this happens, the no_beans variable sends a message to the topic. Such messages will include metadata to clarify that the bean variety is out of stock.


...
if quantity > 0:
    adding_beans = sns_client.publish(
        TopicArn=sns_topic,
        Message=message_data.strip(),
        Subject='New bean delivery',
        MessageGroupId='bean_message_group'
    )
...
else:
    no_beans = sns_client.publish(
        TopicArn=sns_topic,
        Message=message_data.strip(),
        Subject='New bean delivery',
        MessageAttributes={
            'inventory_alert': {
                'DataType': 'String',
                'StringValue': 'out_of_stock'
            }
        },
        MessageGroupId='bean_message_group'
    )
...
 

Update the Python publisher and review the test records
In the send_beans_update.py file, replace the <FMI_1> placeholder with your AWS account ID to update the sns_topic value.

The updated line is similar to the following:


sns_topic = 'arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo'
   

Save your changes.

  ​    

Review the first set of records that you will publish to the SNS topic.

In the environment window, under resources/sqs-sns, open the beans_update_1.txt file.

The file contains four records in the following format: SupplierId:BeanType:Quantity. While you review the records, notice that two of them are exactly the same. Remember that you have enabled content-based deduplication on the topic.

 

Run the Python publisher
In the terminal, use the following commands to run the Python publisher:


cd ~/environment/resources/sqs-sns
python3 send_beans_update.py beans_update_1.txt
The output is similar to the following:


{'MessageId': 'd2c8d8ae-53fd-5cc9-ae65-812018f8bec7', 'SequenceNumber': '10000000000000000003', 'ResponseMetadata': {'RequestId': 'ce3152bb-7b8e-5cd4-8f11-0b35308b6eda', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'ce3152bb-7b8e-5cd4-8f11-0b35308b6eda', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:01:41 GMT'}, 'RetryAttempts': 0}}
{'MessageId': '67399c1a-fab8-50bc-82cf-c594b1bed2b2', 'SequenceNumber': '10000000000000000004', 'ResponseMetadata': {'RequestId': '86f7cb8d-4e70-5c83-a71d-92030576fe8d', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '86f7cb8d-4e70-5c83-a71d-92030576fe8d', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:01:41 GMT'}, 'RetryAttempts': 0}}
{'MessageId': 'd2c8d8ae-53fd-5cc9-ae65-812018f8bec7', 'SequenceNumber': '10000000000000000003', 'ResponseMetadata': {'RequestId': 'ee9d7047-afaa-5e21-8ba0-29c9e4accc2f', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'ee9d7047-afaa-5e21-8ba0-29c9e4accc2f', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:01:41 GMT'}, 'RetryAttempts': 0}}
{'MessageId': 'cb2748ad-7912-50fe-b449-1123321432f0', 'SequenceNumber': '10000000000000000005', 'ResponseMetadata': {'RequestId': 'bb6d8002-12b5-527f-90dc-d98c59b38071', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'bb6d8002-12b5-527f-90dc-d98c59b38071', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:01:41 GMT'}, 'RetryAttempts': 0}}
Note: Because the first and third messages in the file are identical, and both were sent within the 5-minute deduplication interval, they are only acknowledged once. Therefore, they have the same SequenceNumber. This demonstrates that the configuration is working and preventing the same information from being processed multiple times.

 

At this point, Amazon SNS should have forwarded these messages to your SQS queue.

 

Use the AWS Management Console to verify that the updated_beans.fifo queue received the messages from the updated_beans_sns.fifo topic.

Navigate to the Amazon SQS console.

In the AWS Management Console, search for and select Simple Queue Service

The DeadLetterQueue.fifo and updated_beans.fifo queues are listed.

 

Choose the link for the updated_beans.fifo queue and choose Send and receive messages

Poll for new messages.

In the bottom pane, choose Poll for messages.

Three messages are listed, as shown in the following image. Remember that one of the four messages was a duplicate. Therefore, that information was only processed and sent to the queue the first time it was received.

Three messages in the Amazon SQS console.

 

Review a message.

Locate the message with the largest Size.

To examine the message details, choose the ID hyperlink.

Review the message body. 

Note: By default, the Body tab is selected. If it isn't, choose it. 

 

  The message body is similar to the following:


{
  "Type": "Notification",
  "MessageId": "529dd3dc-e856-5f96-bf80-8a5b60759014",
  "SequenceNumber": "10000000000000000005",
  "TopicArn": "arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo",
  "Subject": "New bean delivery",
  "Message": "333333333:Unprocessable:0",
  "Timestamp": "2021-08-09T19:45:02.554Z",
  "UnsubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:111111111111:updated_beans_sns.fifo:bfcbb49b-bfba-4751-838f-b10b49514d64",
  "MessageAttributes": {
    "inventory_alert": {
      "Type": "String",
      "Value": "out_of_stock"
    }
  }
}
  Recognize the Subject and MessageAttributes values from the Python script. Notice that the Message value is one of the records from the beans_update_1.txt file. In addition, you can identify important message information such as the message type, the topic that sent the message, the order in which the message was received, and when the message was received.

 

Clean up the queue and send the second set of test records
Delete messages from the queue.

Select all messages in the queue.

Choose Delete, and choose Delete again when you are prompted to confirm this action.

Note: If more than a few minutes have passed since you polled for messages, the token used to fetch them might have expired. In that case, messages similar to the following are listed. 


Id: db0022b1-0f65-4609-b585-aa4e6d3c3142. Reason: The receipt handle has expired.
Id: af19228e-391c-4dc9-a954-db98f185cf34. Reason: The receipt handle has expired.
If you are not able to delete one or more of the messages, refresh the browser page, poll for messages again, and then try to delete the messages again.

Keep this browser tab open to return to later.

 

Next, you will send three new messages to the SNS topic. You will use these messages later when you test the coffee suppliers application integration with the queue.

In the VS Code IDE bash terminal window, run the Python publisher again. This time, send a new set of records:


python3 send_beans_update.py beans_update_2.txt
 

The output is similar to the following:


{'MessageId': '8347854b-3262-5118-8448-dcc57fafe5e4', 'SequenceNumber': '10000000000000000009', 'ResponseMetadata': {'RequestId': '16e28404-ff0c-5fd8-b090-dd8ab2c16b24', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '16e28404-ff0c-5fd8-b090-dd8ab2c16b24', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:13:33 GMT'}, 'RetryAttempts': 0}}
{'MessageId': '270e4cb7-093d-5c8f-8e35-153944f0f873', 'SequenceNumber': '10000000000000000010', 'ResponseMetadata': {'RequestId': '577613d4-7237-51b4-8b10-4a5a3ffa3548', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '577613d4-7237-51b4-8b10-4a5a3ffa3548', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:13:33 GMT'}, 'RetryAttempts': 0}}
{'MessageId': 'd9f361c0-cae6-5984-8a92-384e872bdd78', 'SequenceNumber': '10000000000000000011', 'ResponseMetadata': {'RequestId': '84ac2e43-1ebd-533d-895a-77cd537017c1', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '84ac2e43-1ebd-533d-895a-77cd537017c1', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:13:33 GMT'}, 'RetryAttempts': 0}}
 

Nice job! You now have three messages in the queue. They will wait there until you configure the coffee suppliers application to poll the queue and process them.

 

Task 7: Configuring the application to poll the queue
The application code has already been updated for you to be able to poll the SQS queue. However, to enable this new functionality, you must first define a new environment variable named SQS_ENDPOINT in Elastic Beanstalk. 

Before you make any changes to Elastic Beanstalk, review the current inventory data in the coffee suppliers application.

View the coffee bean inventory.

Return to the browser tab that is open to the Amazon SQS console.

Choose Services, and choose Elastic Beanstalk.

Choose the hyperlink for MyEnv.

To open the currently deployed coffee suppliers application, choose the URL directly under MyEnv.

The coffee suppliers application opens in a new browser tab.

Append /beans to the URL in your browser tab.

The URL is similar to the following:


https://myenv.eba-xxxxxxxx.us-east-1.elasticbeanstalk.com/beans
Note: You might receive an error the first time that you load the page. If you do, wait 10 seconds and reload the page.

Near the top of the page, notice the message results from Db, followed by the coffee bean inventory.

In the All beans table, review the Quantity column. 

Notice that all inventory items have quantity values that end with a zero (for example, 1000, 800, 500). Pay particular attention to the following records:

The record that has Supplier Id=3 and Type=Excelsa has a Quantity of 200.

The record that has Supplier Id=6 and Type=Arabica has a Quantity of 300.

 

Update the Elastic Beanstalk configuration.

Return to the browser tab that is open to Elastic Beanstalk console.

In the left navigation pane, choose Configuration.

In the Software category, choose Edit.

Scroll down to the Environment properties section, and add the following two entries:

Name: Enter SQS_ENDPOINT

Value: Enter https://sqs.us-east-1.amazonaws.com/<FMI_1>/updated_beans.fifo and replace the <FMI_1> placeholder with your account AWS account ID.

Name: Enter SQS_REGION

Value: Enter the AWS Region that you created the SQS queue in (for example, us-east-1)

Choose Apply.

A message indicates that Elastic Beanstalk is updating your environment.

It takes a few minutes for the environment to be updated. After the build has finished, the application will start to poll the updated_beans.fifo queue. 

 

Review the application consumer code
While the application is being redeployed, review the application code that acts as a consumer for the updated_beans.fifo queue. 

Return to the browser tab open to the VS Code IDE bash terminal.

In the environment window, expand resources/codebase_partner/app/sqs and open the consumer.js file.

Review the contents along with the following code snippets.

The application uses a variable called sqs_url to define the queue's endpoint. The function named get_sqs_endpoint sets this value for the variable. This is where the application uses the SQS_ENDPOINT value that you set earlier.


...
const sqs_url = get_sqs_endpoint()
...
function get_sqs_endpoint() {
    if (process.env["SQS_ENDPOINT"] === undefined) {
        console.log("SQS endpoint not found")
        return false
    }
    return process.env["SQS_ENDPOINT"]
}
...
 

The variable sqs_client_params stores the client-side parameters that the application uses to interact with the queue.


const sqs_client_params = {
    QueueUrl: sqs_url,
    // Only set up to do one message at a time
    MaxNumberOfMessages: 1,
    VisibilityTimeout: config.VISIBILITY_TIMEOUT_IN_SEC,
    WaitTimeSeconds: config.LONG_POLL_WAIT_IN_SEC
};
 

The following section of code reads the message information from the queue.


...
module.exports = bean_model => {
  if (sqs_url) {
      AWS.config.update({region: sqs_region});
      const sqs = new AWS.SQS({apiVersion: '2012-11-05'});
      console.log("Listening to SQS:", sqs_client_params)
      read_message(sqs, bean_model)
  } else {
...
 

Multiple functions then process the message data that the application receives. These functions parse the messages, update the database, and delete successfully processed messages from the queue.

 

By now, the application should be redeployed and should have attempted to process the messages that were waiting in the updated_beans.fifo queue.
​
​Because the coffee suppliers application will not respond to Amazon SQS if a problem occurs, you must rely on the queue configuration to remove messages that cannot be processed. To test the dead-letter queue functionality, the last messages that you sent to the updated_beans.fifo queue were purposely not valid, and the application cannot process them.

 

When an item cannot be processed, its visibility timeout eventually expires, and the queue receives it again. Then, the calling process can pick up the message and try to process it again. The updated_beans.fifo queue is configured with a maxReceiveCount of 5. This means that if a message fails to process five times, the sixth time it's received, it will be sent to the dead-letter queue (DeadLetterQueue.fifo). After the dead-letter queue receives the items, they are removed from the updated_beans.fifo queue. This prevents the main queue from perpetually processing data that isn't valid and frees it up to process new valid messages.

 

Review the new messages in the Amazon SQS console
Review the messages in the dead-letter queue.

Return to the browser tab that is open to the Elastic Beanstalk console.

Choose Services, and then choose Simple Queue Service.

Choose the hyperlink for the DeadLetterQueue.fifo queue.

Choose Send and receive messages.

In the bottom pane, choose Poll for messages.

Three messages are listed in the dead-letter queue. 

 

 

Send the last batch of test data
Now that all of the messages that can't be processed have been moved to the dead-letter queue, you can test by sending valid data. If these messages are processed successfully, the inventory quantities in the coffee suppliers application will change.

Return to the browser tab open to the VS Code IDE bash terminal.

 

Use the following command to run the Python publisher again. This time you will send a new set of records:


python3 send_beans_update.py beans_update_3.txt
 

The output is similar to the following:


{'MessageId': 'f0777426-21fa-5b4f-bbfd-2da870f157c7', 'SequenceNumber': '10000000000000000015', 'ResponseMetadata': {'RequestId': '8108524e-0eb4-543e-8049-0bc05fbf28b6', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '8108524e-0eb4-543e-8049-0bc05fbf28b6', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:27:23 GMT'}, 'RetryAttempts': 0}}
{'MessageId': '2611af39-fdc1-53ff-af2b-f6b7acca9f77', 'SequenceNumber': '10000000000000000016', 'ResponseMetadata': {'RequestId': 'b2731f6d-4add-59ca-85e7-46e31bd62542', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'b2731f6d-4add-59ca-85e7-46e31bd62542', 'content-type': 'text/xml', 'content-length': '352', 'date': 'Wed, 11 Aug 2021 22:27:23 GMT'}, 'RetryAttempts': 0}}
The application picked up these messages for processing as soon as you ran the script.

 

Check the coffee suppliers inventory to verify that the records were updated.

Return to the browser tab open to the coffee suppliers application.

Refresh the page.

For the record that has Supplier Id=3 and Type=Excelsa, the Quantity should now be 209.

For the record that has Supplier Id=6 and Type=Arabica, the Quantity should now be 306.

 

This has been a productive day! You created an SNS topic to receive messages from the coffee suppliers, and an SQS queue to receive and hold those messages for future processing. You also set up a dead-letter queue to handle messages that aren't valid. Two scripts are prepared to work with your messaging system. One script will publish messages to your topic, and the other will consume messages from your queue. Finally, you configured the coffee suppliers application to use the new functionality and automatically process inventory updates.

 

Update from the café
Frank is thrilled. Café staff no longer need to spend time away from customers to perform boring data entry tasks. As an additional benefit, data accuracy has improved now that employees aren't entering the data manually. 

You could enhance the application in other ways by using queueing. For example, you could use the "out of stock" metadata to launch an email or text notification to Frank to inform him that a supplier doesn't have the coffee beans that he needs. Then, he could quickly start to look for a supplier that has the beans his customers want before the café runs out of stock.

 

Submitting your work
At the top of these instructions, choose Submit to record your progress and when prompted, choose Yes.

Tip: If you previously hid the terminal in the browser panel, expose it again by selecting the Terminal  check box. This action will ensure that the lab instructions remain visible after you choose Submit.

 

If the results don't display after a couple of minutes, return to the top of these instructions and choose Grades

Tip: You can submit your work multiple times. After you change your work, choose Submit again. Your last submission is what will be recorded for this lab.

 

To find detailed feedback on your work, choose Details followed by  View Submission Report

 

Lab complete 
 Congratulations! You have completed the lab.

Choose End Lab at the top of this page, and then select Yes to confirm that you want to end the lab.

A panel indicates that DELETE has been initiated... You may close this message box now.

 

Select the X in the top-right corner to close the panel.

 

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This work may not be reproduced or redistributed, in whole or in part, without prior written permission from Amazon Web Services, Inc. Commercial copying, lending, or selling is prohibited.

 