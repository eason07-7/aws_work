Lab 11.1: Orchestrating Serverless Functions with Step Functions
Lab overview and objectives
In this lab, you will use AWS Step Functions to coordinate the actions necessary to generate and deliver a report upon request. The report will contain data from a database.

After completing this lab, you should be able to:

Create an asynchronous state machine by using Step Functions

Configure an Amazon Simple Notification Service (Amazon SNS) topic to deliver email alerts

Configure AWS Lambda functions to be invoked from a Step Functions state machine

Use a parallel state flow object in the design of a Step Functions state machine

Invoke a state machine to start when a REST API endpoint is invoked

Generate a presigned URL for an object stored in an Amazon Simple Storage Service (Amazon S3) bucket

 

Duration
This lab will require approximately 90 minutes to complete.

 

AWS service restrictions
In this lab environment, access to AWS services and service actions might be restricted to the ones that are needed to complete the lab instructions. You might encounter errors if you attempt to access other services or perform actions beyond the ones that are described in this lab.

 

Scenario
Thanks to Sofía, the coffee suppliers inventory now automatically updates on the café website. But the work is not finished! Frank asks if it would be possible to log in to the website to request a report with the latest inventory information.

Yesterday, Mateo, who is an AWS consultant and Sofía's friend, came into the café for a macchiato, his favorite espresso drink. While he was enjoying his beverage, Sofía told him about how she needs to build a reporting mechanism for Frank. After discussing the high-level business requirements, Mateo suggested that she use AWS Step Functions to coordinate the steps to generate the report. He described how Step Functions can help a developer to automate business processes by creating workflows, and providing parallelization and service integrations, among other features.

In this lab, Sofía will build the functionality to create and deliver the report. Then, in the next lab, she will improve the design further and implement authentication on the website to limit who can request and access reports.

The following diagram shows the architecture that was created for you in AWS at the beginning of the lab.

Architecture with S3 bucket, create_report API, and suppliers database

By the end of this lab, you will have created the architecture shown in the following diagram.

Architecture now includes a state machine, three Lambda functions, SNS topic, and email report

The following table describes the steps that are labeled in the diagram.

Step in Diagram	Explanation
1	A user (Frank) requests a report by using the create_report REST API endpoint. You created this REST API in a previous lab. The request invokes a Step Functions state machine that you will build.
2	The state machine first invokes a Lambda function that looks up the latest coffee supply information. The information is in a MySQL database hosted on Amazon Relational Database Service (Amazon RDS).
3	The state machine then invokes two Lambda functions to run in parallel.
4	One of the functions transforms the JSON data from the database into an HTML report that is nicely formatted for readability. The report is uploaded to an S3 bucket.
5	The other function generates a presigned URL to access the report and then sends the presigned URL to an SNS topic.
6	Frank is subscribed to the SNS topic, so he receives an email with the presigned URL. He can then access the report from Amazon S3. Only he knows the presigned URL, and it will expire after a short period.
In this lab, you will again play the role of Sofía to build the functionality described. Let's get started!

 

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
In this first task, you will configure your Visual Studio Code Integrated Development Environment (VS Code IDE). You will also run the script to re-create the work you completed in previous labs.

 

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

On the prompt window Welcome to code-server, enter the value for LabIDEPassword you copied to the editor earlier, choose Submit to open the VS Code IDE.

 

Download and extract the files that you need for this lab.

In the VS Code IDE bash terminal, run the following command:



wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/11-lab-step/code.zip -P /home/ec2-user/environment
The code.zip file is downloaded to the the VS Code IDE. The file is listed in the left navigation pane.

Extract the file:


unzip code.zip
 

Run a script to the configure VS Code IDE and re-create the work that you completed in earlier labs into this AWS account.

Set permissions on the script so that you can run it, and then run it:


chmod +x ./resources/setup.sh && ./resources/setup.sh
When prompted for an IP address, enter the IPv4 address that the internet uses to contact your computer. You can find your IPv4 address at https://whatismyipaddress.com.

Note: The IPv4 address that you set is the one that will be used in the bucket policy. Only requests that originate from this IPv4 address will be allowed to load the website pages. Do not set it to 0.0.0.0 because the S3 bucket's block public access settings will prevent access.

Verify that the script did not encounter any errors.

If you see any "An error occurred" lines just before the "done" line, the script might have been run too soon after you started the lab. Run the setup.sh script again to clear errors.

If you don't see any error lines, you can assume that the script ran successfully.

 

Analysis: The CloudFormation template that ran when you started this lab created resources in the AWS account. The script you just ran also created resources. Between the two of them, the following resources have been created to replicate what you built in previous labs:

An S3 bucket with an associated bucket policy. The bucket contains the café website code.

An Amazon DynamoDB table populated with menu data.

A REST API configured using Amazon API Gateway.

A Lambda function that retrieves data from DynamoDB when invoked.

A Memcached cluster that caches supplier data from Amazon Aurora Serverless for the suppliers application.

A café/node-web-app Docker image, which is stored in the Amazon Elastic Container Registry (Amazon ECR).

An AWS Elastic Beanstalk environment and application that runs an Amazon Elastic Compute Cloud (Amazon EC2) instance named MyEnv. The EC2 instance hosts a Docker container created from the Docker image that is stored in Amazon ECR.

An Aurora Serverless database running MySQL on Amazon RDS, which contains the supplierdb database, which stores coffee supplier information.

 

Verify the version of AWS CLI installed.

In the VS Code IDE Bash terminal (at the bottom of the IDE), run the following command:


aws --version
The output should indicate that version 2 is installed.

 

Verify that the SDK for Python is installed.

Run the following command:


pip3 show boto3
Note: If you see a message about not using the latest version of pip, ignore the message.

 

Verify that you can access the café website.

Navigate to the Amazon S3 console.

Choose the link for the bucket that has -s3bucket in the name.

Open the index.html file.

In the Object overview section, open the Object URL in a new browser tab.

The café website displays. If it doesn't, see the following troubleshooting tip.

Troubleshooting tip: If you are using a VPN, the IP address returned by whatismyipaddress.com might not allow access to the café website. If you can't connect to the café website, disconnect from VPN. Find your IP address again using whatismyipaddress.com, and then run setup.sh again. Then, stay off of the VPN for the duration of this lab.

 

Task 2: Configuring an SNS topic and subscribing to it
In this task, you will configure an SNS topic that can be used to alert Frank when a requested report is available.

The following diagram shows the solution architecture for this lab, with the part that you will build in tasks 2 and 3 highlighted.

Architecture with SNS topic and email highlighted

 

Create an SNS topic for email notification.

Navigate to the Amazon SNS console.

In the left navigation pane, choose Topics.

Choose Create topic and configure the following:

Type: Choose Standard.

Name: Enter EmailReport

Expand the Access policy - optional section.

Define who can publish messages to the topic: Choose Everyone.

Define who can subscribe to this topic: Choose Everyone.

At the bottom of the page, choose Create topic.

 

Create an email subscription to the SNS topic.

Choose Create subscription and configure the following:

Topic ARN: Notice that the Amazon Resource Number (ARN) of the topic that you just created is already filled in.

Protocol: Choose Email.

Endpoint: Enter an email address where you can receive emails during this lab. (In the café story, Sofía would enter Frank's email address.)

Choose Create subscription.

 

Check your email and confirm the subscription.

Check your email for a message from AWS Notifications.

In the email body, choose the Confirm subscription link.

A webpage opens and displays a message that the subscription was successfully confirmed.

 

Publish a test message to confirm that messages can be published to the EmailReport SNS topic.

Return to the Amazon SNS console, and return to the EmailReport topic page.

Tip: In the breadcrumbs at the top of the page, choose EmailReport.

Choose Publish message and configure the following:

Subject - optional: Enter Test

Message body: Enter Hello! This is a test.

At the bottom of the page, choose Publish message.

 

Confirm that you received the message at your email address.

The subject and message body should match the details that you configured in the previous step.

  

 

Task 3: Creating a Step Functions state machine
In this task, you will create a Step Functions state machine that can send an email notification by using the SNS topic.

The Step Functions state machine will need permissions to access the Lambda service. Start by looking at an AWS Identity and Access Management (IAM) role that has already been created for you for this purpose.

 

Review the IAM role for Step Functions
Analyze the details of the IAM role that Step Functions will use.

Navigate to the IAM console.

Review the details of the RoleForStepToCreateAReport IAM role.

In the left navigation pane, choose Roles.

In the search box under Roles, search for and choose the RoleForStepToCreateAReport role.

On the Permissions tab, expand the stepPolicyForCreateReport policy, and choose {} JSON.

Notice that this role allows all Lambda and log actions on all resources.

Expand the AWSLambdaRole managed policy, which is also attached to the role.

Notice that this role allows the lambda:InvokeFunction action on all resources. This will allow you to test the function from the Lambda console.

Choose the Trust relationships tab.

Notice that this role allows the Step Functions service to assume this role (as indicated by the states.amazonaws.com service endpoint).

Note: In this lab environment, we cannot grant you permissions to create an IAM role. Therefore, later in this lab, you will observe the details for other IAM roles that have already been created for you. However, in an AWS account where you have more permissions to use the IAM service, you could create the IAM role that you just observed, attach the managed policy, and also create the custom IAM policy and attach it to the role.

 

Create a state machine to send an email
Begin to create a Step Functions state machine.

Navigate to the Step Functions console.

In the left navigation pane, choose State machines.

Choose Create state machine and configure the following for step 1:

Choose a template: Choose Blank.

Choose Select.

The Workflow Studio appears for step 2.

 

Design the workflow.

In the search box under Step 2: Design workflow, enter SNS

Drag the Amazon SNS Publish object onto the canvas, to the box labeled Drag first state here.

In the SNS Publish pane that displays, configure the following:

Topic: Choose the ARN of the EmailReport SNS topic that you created earlier.

Notice that Message is set to Use state input as message, as shown in the following image.

State machine with SNS Publish object

Choose {} Code in the upper part of the screen. 

The generated Amazon States Language (ASL) code for the state machine displays, as shown in the following image.

  ASL code for current state machine

Choose Config and configure the following:

State machine name: Enter MyStateMachine

Execution role: Choose Choose an existing role.

Existing roles: Choose RoleForStepToCreateAReport.

Note: This is the role that you reviewed earlier.

Log level: Choose ALL.

At the top of the page, choose Create.

    

Test the state machine.

Choose Execute button at the top and configure the following:

In the code editor, replace the existing JSON code with the following.


{
  "presigned_url_str": "Testing that my email message works"
}
Choose Start execution.

A message displays and indicates that the execution started successfully.

To see the details, choose Execution input and output.

Details about the execution are displayed.

 

Check your email for a new notification.

It might take a few minutes to arrive.

The notification includes the Testing that my email message works text.

Congratulations! You have created a basic state machine that invokes an SNS topic to send an email.

 

Task 4: Creating a Lambda function to generate a presigned URL
In this task, you will create a report.html page with sample inventory data and upload the file to Amazon S3. You will then use the AWS Command Line Interface (AWS CLI) to create and test a presigned URL to access the page. You will observe how the bucket policy allows access to the report. Finally, you will create a Lambda function to generate a presigned URL and deliver the report with sample data in it.

 

Create a sample report, upload it to Amazon S3, and test access
Create a sample report.html page.

Return to the VS Code IDE.

In the Environment window, choose   File > New Text File.

In the new file that opens, paste in the following code.


<output>Hello! This is some sample HTML.</output>
Choose  File > Save.

Save the file under /home/ec2-user/environment directory.

Name the file report.html and choose Save.

 

Upload the sample report file to your S3 bucket, and observe the bucket policy settings.

To upload the file to the S3 bucket and set the cache-control max-age value on the file to 0, run the following two commands in the VS Code IDE terminal:


bucket=$(aws s3api list-buckets --query "Buckets[].Name" | grep s3bucket | tr -d ',' | sed -e 's/"//g' | xargs)
aws s3 cp report.html s3://$bucket/ --cache-control "max-age=0"
The terminal shows that the file was successfully uploaded, as shown in the following image. Note that your bucket name is different.

CLI successful response

In a separate browser tab, navigate to the Amazon S3 console.

Choose the link for the bucket that has -s3bucket in the name.

Verify that the report.html file is now in the bucket.

Choose the Permissions tab.

Review the information in the Bucket policy section.

Notice the second statement in the policy, which is provided in the following code block. This statement denies the s3:GetObject action to be taken for the report.html object, unless the authorization type is a REST query string.


{
    "Sid": "DenyOneObjectIfRequestNotSigned",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::c24306a339482l1034433t1w221264991720-s3bucket-1f3zb2vbj7axe/report.html",
    "Condition": {
        "StringNotEquals": {
            "s3:authtype": "REST-QUERY-STRING"
        }
    }
}
 

Test direct access to the sample report.

In the Amazon S3 console, choose the Objects tab, and then choose report.html.

Copy the Object URL and paste it into a new browser tab.

You receive an AccessDenied error, as shown in the following image. This is expected because of the bucket policy details that you just observed.

Access denied error

Create a presigned URL to access the report and test it.

Return to the VS Code IDE.

To generate a presigned URL that is valid for 30 seconds, run the following command:


aws s3 presign s3://$bucket/report.html --expires-in 30
Choose the presigned URL that was returned, and then choose Open.

The text in the report.html file displays, as shown in the following image.

Webpage says "Hello! This is some sample HTML."

Analysis: The page loads without error, as long as you open it within 30 seconds of generating the presigned URL.

Wait until at least 30 seconds have passed since you generated the presigned URL, and then refresh the webpage.

The URL has expired, and you see an AccessDenied message. This is the expected behavior.

 

Excellent! You have tested the presigned URL functionality and confirmed that the report can only be accessed by using a presigned URL and not the S3 Object URL. The bucket policy details determine the permitted access.

 

Create the Lambda function
Now you will update the Step Functions state machine to generate and send a presigned URL to Frank so that he can access the report, just like you tested. First, you need to create a Lambda function that can generate the presigned URL. Then, you can add the Lambda function to the state machine.

The following diagram shows the solution architecture for this lab, with the part that you will build in this task highlighted in yellow. The part that you built previously is highlighted in grey.

Architecture, generate presigned URL function highlighted

 

First, analyze the details of the IAM role that the Lambda functions in this lab will use.

Navigate to the IAM console.

Review the details of the RoleForAllLambdas IAM role.

In the left navigation pane, choose Roles.

In the search box under Roles, search for and choose the RoleForAllLambdas role.

On the Permissions tab, expand the lambdaPolicyForAllLambdaSteps policy, and choose {} JSON.

Notice that this role allows Amazon S3 and Amazon EC2 actions on all resources.

Choose the Trust relationships tab.

Notice that this role allows the Lambda service to assume this role (as indicated by the lambda.amazonaws.com service endpoint).

 

Create a Lambda function that will generate a presigned URL for the report.

Navigate to the Lambda console.

Verify that you are in the N. Virginia (us-east-1) Region.

Choose Create function and configure the following:

Choose Author from scratch.

Function name: Enter GeneratePresignedURL

Runtime: Choose Python 3.9.

Expand the Change default execution role section.

Execution role: Choose Use an existing role.

Existing role: Choose RoleForAllLambdas.

At the bottom of the page, choose Create function.

In the Code source section, replace the existing code with the following.


import logging
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = "BUCKET_NAME_STR"
    object_name = "report.html"
    expiration_in_seconds = 120

    try:
        presigned_url_str = s3_client.generate_presigned_url('get_object',Params={
            'Bucket': bucket_name,'Key': object_name},ExpiresIn=expiration_in_seconds)
        response = { "presigned_url_str": presigned_url_str }
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response
In the code editor, replace BUCKET_NAME_STR on line 3 with the actual name of the bucket that contains the café website code. This bucket has -s3-bucket in the name.

To save the changes, choose File > Save.

 

Test the GeneratePresignedURL Lambda function.

Choose Deploy.

Choose Test, and for Event name, enter test1

Choose Save, and then choose Test again.

The response includes a presigned URL, as shown in the following image.

Presigned URL in Lambda test response

Copy the presigned URL and paste it in a new browser tab to confirm that it works.

If you load the page within 2 minutes, it will return the sample report contents, as shown in the following image.

Webpage says "Hello! This is some sample HTML."

Add the Lambda function to the state machine
Add the GeneratePresignedURL Lambda function to the Step Functions state machine.

Navigate to the Step Functions console.

Select MyStateMachine, and then choose Edit.

Search for Lambda

Drag the AWS Lambda Invoke object onto the canvas to the arrow just above the SNS Publish object, as shown in the following image.

State machine with Lambda Invoke object before SNS Publish object

 

Configure the function details in the Lambda Invoke pane.

State name: Enter GeneratePresignedURL

Function name: Choose GeneratePresignedURL:$LATEST.

Payload: Choose No payload.

Next state: Choose SNS Publish.

Choose Save.

 

Test the update to the state machine.

Choose Execute.

In the code editor, delete the name-value pair that appears on line 2. The input code should only include the brackets, as shown in the following code block.


{
}
Choose Start execution.

To see the details, choose Execution input and output

Check your email for a notification, and choose the presigned URL in the message to verify that you can load the report.

Troubleshooting tip #1: The Lambda function sets the URL to expire 60 seconds after it is generated. If the email does not arrive that quickly, you could adjust the Lambda code details to allow more time (for example, 120 seconds), and save and deploy the change to the Lambda function details. Then, return to the Step Functions state machine, and run the execution again to generate a new email.

Troubleshooting tip #2: Your email client might not recognize the entire presigned URL as a URL, so if you choose the hyperlink in the email, it might not take you to the proper URL. You might need to copy the entire URL from the email body and then paste it into a browser tab to test access.

 

Task 5: Configuring the REST API to invoke the state machine
You might recall in the API Gateway lab earlier in the course that you defined three resources to create the café's REST API. Then, in the Lambda lab, you created two Lambda functions: one to respond to product information requests and the other to respond to report requests.

You configured the get_all_products function to perform DynamoDB database lookups at that time. However, the create_report Lambda function was configured to return a hardcoded response. In this task, you will configure the REST API create_report endpoint so that it invokes the state machine to generate the report.

The following diagram shows the solution architecture for this lab, with the part that you will build in this task highlighted in yellow. The parts that you built previously are highlighted in grey.

Architecture, create_report API Gateway endpoint highlighted

 

Analyze the IAM role that will be used, and copy the role's ARN.

Navigate to the IAM console.

In the left navigation pane, choose Roles.

Search for and choose the RoleForAPIGWToTriggerStep role.

On the Permissions tab, expand the AmazonAPIGatewayPushToCloudWatchLogs AWS managed policy. This policy allows some logging actions.

Expand the AWSStepFunctionsFullAccess AWS managed policy. This policy allows full access to the Step Functions service.

Choose the Trust Relationships tab.

Notice that this role allows the API Gateway service to assume this role (as indicated by the apigateway.amazonaws.com service endpoint).

Copy the Role ARN value to your clipboard. You will need this value in the next step.

 

Configure API Gateway to invoke the Step Functions state machine.

Navigate to the API Gateway console.

Choose the link for ProductsApi.

In the Resources pane, under /create_report, choose POST.

Choose Integration Request and Edit. Configure the following:

Integration type: Choose AWS Service.

AWS Region: Choose us-east-1.

AWS Service: Choose Step Functions.

HTTP method: Choose POST.

Action Type: Choose Use action name.

Action: Enter StartExecution

Execution role: Paste the ARN that you copied in the previous step.

The ARN format is arn:aws:iam::account-number:role/RoleForAPIGWToTriggerStep, where account-number is your AWS account number.

Content Handling: Choose Passthrough.

Request body passthrough: When there are no templates defined(recommended).

Expand the Mapping Templates section.

In the Content-Type field, enter application/json and then choose the check mark icon to confirm the entry.

Choose Method request passthrough

Replace the contents in Template body with the following code.


{
  "input": "$util.escapeJavaScript($input.json('$'))",
  "stateMachineArn": "arn:aws:states:us-east-1:account-number:stateMachine:MyStateMachine"
}
In the code that you pasted in, replace account-number with your AWS account number.

Tip: To get your account number, choose the username at the top of the console. Alternatively, you can find the full ARN of MyStateMachine in the Step Functions console.

Choose Save.

 

Test the modification to the API.

Choose the Test tab.

Keep all the default settings, and at the bottom of the page, choose Test.

The Response Body section displays a JSON message similar to the following.


{
  "executionArn": "arn:aws:states:us-east-1:112983786782:express:MyStateMachine:7ae836af-e2b0-47df-a3c7-589e256b89ee:970b4ee6-093b-4aac-92e9-138635232148",
  "startDate": 1632506152.764
}
Check your email for a new notification with a presigned URL.

 

Deploy the API updates.

In the Resources pane, choose the root resource (/).

Choose Deploy API.

For Deployment stage, choose prod.

Choose Deploy.

Copy the Invoke URL that displays. You will need it in a moment.

 

Test generating the presigned URL by using the Invoke URL endpoint.

Return to the VS Code IDE.

To generate a new presigned URL, run the following command. Replace invoke-url with the Invoke URL that you just copied.


curl -X POST invoke-url/create_report
The full command looks similar to the following:


curl -X POST https://unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report
The result includes a JSON response that contains executionArn and startDate name-value pairs.

Tip: If you see {"message_str": "report requested, check your phone shortly."} instead, try again. The older API might remain in the cache for a brief time.

Check your email for a new notification with a presigned URL.

Open the URL to verify that it works. You must open the URL quickly after it is generated.

 

Great! The REST API for the café can now be used to invoke a link to a report to be emailed to Frank. Sofía decides that now she is ready to start filling the report with real data.

 

Task 6: Configuring a Lambda function to generate an HTML report
In this task, you will create a Lambda function to generate an HTML report that contains data from a JavaScript object that looks like a JSON document. The function will store the resulting file to Amazon S3 and overwrite the existing report.html file.

The following diagram shows the solution architecture for this lab with the part that you will build in tasks 6 and 7 highlighted in yellow. The parts that you built previously are highlighted in grey.

Architecture, generate HTML function and S3 bucket highlighted

 

Create a Lambda function that will generate an HTML report with data extracted from a JSON object.

Navigate to the Lambda console.

Verify that you are in the N. Virginia (us-east-1) Region.

Choose Create function and configure the following:

Choose Author from scratch.

Function name: Enter generateHTML

Runtime: Choose Node.js 20.x.

Expand the Change default execution role section.

Execution role: Choose Use an existing role.

Existing role: Choose RoleForAllLambdas.

At the bottom of the page, choose Create function.

Choose the Configuration tab, and then choose Edit in the General configuration section.

Adjust the timeout to 2 minutes, and then choose Save.

Choose the Code tab, and in the Code source section, replace the existing code with the following.


import { S3Client, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const BUCKET_NAME_STR = "ACTUAL_BUCKET_NAME";
const s3Client = new S3Client({ apiVersion: "2006-03-01" });

export const handler = async (event) => {
    let parsedEvent;
    
    try {
        // First level parsing: Handle if entire event is a string . This is needed when executed via state machine
        const firstLevelParse = typeof event === 'string' ? JSON.parse(event) : event;
        
        // Second level parsing: Handle if body exists and is a string. This is required when lambda is invoked via test event.
        if (firstLevelParse.body) {
            parsedEvent = typeof firstLevelParse.body === 'string' 
                ? JSON.parse(firstLevelParse.body) 
                : firstLevelParse.body;
        } else {
            parsedEvent = firstLevelParse;
        }

        // Handle cases where my_json_arr might be a string representation of an array
        if (typeof parsedEvent.my_json_arr === 'string') {
            try {
                parsedEvent.my_json_arr = JSON.parse(parsedEvent.my_json_arr);
            } catch (e) {
                throw new Error('Failed to parse my_json_arr string to array');
            }
        }

        // Validate that my_json_arr is an array
        if (!Array.isArray(parsedEvent.my_json_arr)) {
            throw new TypeError('Expected my_json_arr to be an array, but got ' + typeof parsedEvent.my_json_arr);
        }

        // Proceed with generating and uploading the report
        const htmlContent = await createHTML(parsedEvent);
        await writeReport(htmlContent);

        // Generate a presigned URL for accessing the uploaded report
        const presignedUrl = await generatePresignedUrl();

        return {
            "msg_str": "Report published to S3",
            "presigned_url_str": presignedUrl
        };

    } catch (error) {
        console.error('Error processing event:', error);
        throw new Error(`Failed to process event: ${error.message}`);
    }
};

function getCSSLink() {
    return `
html, body, section, h1, h2, h3, h4, p {
    margin: 0;
    padding: 0;
}
.report {
    background-color: whitesmoke;
    padding: 0;
    margin: 0;
    position: relative;
}
.report h1 {
    color: #e7e2e2;
    font-size: 42px;
    text-align: center;
    background-color: #434343;
    border-bottom: 1px solid #b9b4b4;
    padding: 12px 24px;
}
.report h2 {
    font-size: 24px;
}
.report p {
    font-size: 18px;
    padding: 12px 0px;
    font-style: italic;
}
.report [data-role="timestamp"] {
    font-size: 16px;
    color: #cac6c6;
    position: absolute;
    top: 32px;
    right: 24px;
}
.report [data-role="supplier_info"] {
    width: 90%;
    margin: 12px auto;
    color: #434343;
    border-bottom: 2px dotted #505951;
    padding-bottom: 12px;
    padding-top: 16px;
}
.report [data-role="bean_info"] {
    display: inline-block;
    color: #434343;
    margin-bottom: 12px;
    border-radius: 6px;
    margin-right: 12px;
    border: 1px solid #434343;
}
.report [data-role="bean_info"] h3 {
    padding: 12px 24px;
    font-size: 20px;
}
.report [data-role="bean_info"] h4 {
    padding: 12px 24px;
    font-size: 18px;
}
.report [data-role="bean_info"] span {
    padding: 12px 24px;
    font-size: 16px;
    display: block;
}
`;
}

async function createHTML(event) {
    const item_obj_arr = event.my_json_arr; 

    let html_str = '';

    html_str += '<!DOCTYPE html>';
    html_str += '<html>';
    html_str += '<head>';
    html_str += '<title>Bean quantity report</title>';
    html_str += '<style>' + getCSSLink() + '</style>';
    html_str += '</head>';
    html_str += '<body>';
    html_str += '<section class="report">';
    html_str += '<h1>Report</h1>';
    html_str += '<span data-role="timestamp">' + new Date().toLocaleTimeString() + '</span>';

    for (const o of item_obj_arr) {
        html_str += '<section data-role="supplier_info">';
        html_str += '<h2>' + o.supplier_name_str + '</h2>';
        html_str += '<p>' + o.supplier_address_str + " : " + o.supplier_phone_str + '</p>';

        for (const k of o.bean_info_obj_arr) {
            html_str += '<div data-role="bean_info">';
            html_str += '<h3>' + k.type_str + '</h3>';
            html_str += '<h4>' + k.quantity_int.toString() + '</h4>';
            html_str += '<span>' + k.product_name_str + '</span>';
            html_str += '</div>';
        }

        html_str += '</section>'; // end supplier info
    }

    html_str += '</section>'; // end report
    html_str += '</body>';
    html_str += '</html>';

    return html_str;
}

async function writeReport(html_str) {
    const params = {
        Bucket: BUCKET_NAME_STR,
        Key: "report.html",
        Body: html_str,
        CacheControl: "max-age=0",
        ContentType: "text/html"
    };

    const command = new PutObjectCommand(params);
    await s3Client.send(command); // Correct usage of s3Client
}

async function generatePresignedUrl() {
    const command = new GetObjectCommand({
        Bucket: BUCKET_NAME_STR,
        Key: "report.html"
    });

    // Generate presigned URL with a 1-hour expiration
    const presignedUrl = await getSignedUrl(s3Client, command, { expiresIn: 3600 });
    return presignedUrl;
}
In the code editor, replace both occurrences of ACTUAL_BUCKET_NAME with the name of the bucket that contains the report.html file. The first occurrence is on line 4, and the second occurrence is 8 lines above the last line of code.

 

Test the new generateHTML Lambda function.

Choose Deploy.

Choose the down arrow next to Test, and choose Configure test event.

For Event name, enter test2

Paste the following code in as the input (replace the existing lines):


{
    "my_json_arr": [
      {
        "suppliers_id_int": 1,
        "supplier_name_str": "AnyCompany coffee suppliers",
        "supplier_address_str": "123 Any Street",
        "bean_info_obj_arr": [
          {
            "type_str": "Arabica",
            "product_name_str": "Best bean",
            "quantity_int": "300",
            "price_int_str": "18.00"
          },
          {
            "type_str": "Robusta",
            "product_name_str": "Great bean",
            "quantity_int": "100",
            "price_int_str": "12.00"
          }
        ]
      },
      {
        "suppliers_id_int": 2,
        "supplier_name_str": "Central Example Corp. coffee",
        "supplier_address_str": "100 Main Street",
        "bean_info_obj_arr": [
          {
            "type_str": "Robusta",
            "product_name_str": "Top bean",
            "quantity_int": "200",
            "price_int_str": "10.00"
          },
          {
            "type_str": "Liberica",
            "product_name_str": "Better bean",
            "quantity_int": "150",
            "price_int_str": "14.00"
          }
        ]
      }
   ]
}
Choose Save, and then choose Test again.

The response includes the following JSON message.


{
"msg_str": "Report published to S3"
}
Note: If the Lambda function ran successfully, it overwrote the report.html file in the S3 bucket. You are not able to open the file directly in the Amazon S3 console. However, you might optionally download the report.html file from the console and open it on your computer to observe the changes. You will also see the report in action in the next task.

 

Task 7: Adding the GenerateHTML function to the state machine
In this task, you will add an additional state to your state machine to invoke the GenerateHTML Lambda function. However, you want this state to run in parallel with the GeneratePresignedURL state, which you added earlier. This is because the presigning doesn't depend on this step. By running the two states in parallel, the state machine will run more quickly. In Step Functions, the workflow advances to the next task only after the slowest of the parallel states completes.

 

Edit the Step Functions state machine to add a parallel state.

Navigate to the Step Functions console.

In the left navigation pane, choose State machines.

Select MyStateMachine, and then choose Edit.

Choose the Flow tab in the left pane.

Drag the Parallel object onto the canvas, just above the Lambda Invoke object.

Drag the GeneratePresignedURL object to the box labeled Drop state here on the right, under the Parallel state object, as shown in the following image.

State machine with parallel state object that goes to the presigned URL function invoke object, and then to SNS Publish object

 

Add the GenerateHTML function to the state machine, and configure it.

Choose the Actions tab in the left pane.

Search for Lambda

Drag the AWS Lambda Invoke object onto the canvas to the box labeled Drop state here on the left, under the Parallel state object.

Choose the new Lambda Invoke object and configure the following function details in the Lambda Invoke pane.

State name: Enter generateHTML

Function name: Choose generateHTML:$LATEST.

Payload: Choose Use state input as payload.

Next state: Choose Go to end.

 

Configure the Parallel state card details, and then save the changes.

On the canvas, choose the Parallel state object.

For State name, enter Process Report

Choose Save. 

 

 

Test the updated state machine.

Choose Execute and configure the following:

In the code editor, replace the existing JSON code with the following.


{
  "my_json_arr": [
    {
      "suppliers_id_int": 1,
      "supplier_name_str": "Dave coffee suppliers",
      "supplier_address_str": "123 Any Street",
      "bean_info_obj_arr": [
        {
          "type_str": "Arabica",
          "product_name_str": "Best bean",
          "quantity_int": "300",
          "price_int_str": "18.00"
        },
        {
          "type_str": "Robusta",
          "product_name_str": "Great bean",
          "quantity_int": "100",
          "price_int_str": "12.00"
        }
      ]
    },{
      "suppliers_id_int": 2,
      "supplier_name_str": "Central Example Corp. coffee",
      "supplier_address_str": "100 Main Street",
      "bean_info_obj_arr": [
        {
          "type_str": "Robusta",
          "product_name_str": "Top bean",
          "quantity_int": "200",
          "price_int_str": "10.00"
        },
        {
          "type_str": "Liberica",
          "product_name_str": "Better bean",
          "quantity_int": "150",
          "price_int_str": "14.00"
        }
      ]
    }
  ]
}
Notice that the input now consists of an array.

Choose Start execution.

To see the details, choose Execution input and output.

Check your email for a new notification with a presigned URL.

The email now includes two name-value pairs, in the following format, which is truncated for brevity: [{"msg_str":"Report published to S3"},{"presigned_url_str":"https://...&Expires=..."}]

 

Task 8: Creating a Lambda function to retrieve supplier records
In this task, you will create a third Lambda function. This function will query the MySQL database, which is hosted on Amazon RDS, to extract the actual coffee suppliers data that is needed for the report.

The following diagram shows the solution architecture for this lab, with the part that you will build in this task highlighted in yellow. The parts that you built previously are highlighted in grey.

Architecture, generate report data function and RDS database highlighted

 

Create a Lambda function to query the database.

Navigate to the Lambda console.

Verify that you are in the N. Virginia (us-east-1) Region.

Choose Create function and configure the following:

Choose Author from scratch.

Function name: Enter generateReportData

Runtime: Choose Node.js 20.x.

Expand the Change default execution role section.

Execution role: Choose Use an existing role.

Existing role: Choose RoleForAllLambdas.

At the bottom of the page, choose Create function.

Choose the Configuration tab, and then choose Edit.

Set the timeout for this function to 1 minute and save the change.

Note: This function needs to use a library, so you will upload a .zip file instead of pasting code into the code editor.

 

Create an index.js file.

Return to the VS Code IDE.

In the Environment window, open the context (right-click) menu for the root directory, and then choose New Folder.

Name the folder lambda

Inside the lambda folder, create a new file named index.js

Paste the following code into the file.


import { S3Client } from '@aws-sdk/client-s3';
import mysql from 'mysql2/promise';

const s3Client = new S3Client({ region: "us-east-1" });

export const handler = async (event, context) => {
    try {
        // Establish MySQL connection
        const connection = await mysql.createConnection({
            host: 'DB-ENDPOINT',
            user: 'nodeapp',
            password: 'coffee',
            database: 'COFFEE'
        });

        // Query suppliers
        const [suppliers] = await connection.query('SELECT * FROM suppliers');

        // Query beans
        const [beans] = await connection.query('SELECT * FROM beans');

        // Close connection
        await connection.end();

        // Merge data
        const mergedData = mergeData(suppliers, beans);

        // Return the merged result
        return {
            statusCode: 200,
            body: JSON.stringify({
                my_json_arr: mergedData
            })
        };
    } catch (err) {
        console.error("Error executing query:", err);
        return {
            statusCode: 500,
            body: JSON.stringify({
                error: 'Failed to retrieve data from MySQL',
                details: err.message
            })
        };
    }
};

// Function to merge suppliers and beans data
function mergeData(suppliers_arr, beans_arr) {
    const fine_tunes_data_arr = [];

    for (const supplier of suppliers_arr) {
        const o = {
            suppliers_id_int: supplier.id,
            supplier_name_str: supplier.name,
            supplier_address_str: supplier.address,
            supplier_phone_str: supplier.phone,
            bean_info_obj_arr: []
        };

        for (const bean of beans_arr) {
            if (supplier.id === bean.supplier_id) {
                const b = {
                    type_str: bean.type,
                    product_name_str: bean.product_name,
                    quantity_int: bean.quantity
                };
                o.bean_info_obj_arr.push(b);
            }
        }

        fine_tunes_data_arr.push(o);
    }

    return fine_tunes_data_arr;
}
Retrieve the value for the database endpoint:

In a new browser tab, navigate to the Amazon RDS console.

Choose Databases, and then choose the supplierdb link.

Copy the  Writer - Endpoint value for the database. The value displays in the Connectivity & security section.

Return to the VS Code IDE.

In the index.js file, replace the DB-ENDPOINT placeholder, which appears on line 9, with the database endpoint that you just copied. Be sure to keep the single quotes around it.

Save the file.

 

Create a package.json file.

In the VS Code IDE, create a new file named package.json in the lambda folder.

Paste the following code into the new file, and save the changes.


{
  "dependencies": {
    "mysql2": "*", 
    "@aws-sdk/client-s3": "*" 
  },
  "type": "module" 
}
 

Generate the .zip package.

To install npm and then create a .zip archive file named lambda.zip that contains the two files that you just created, as well as the node modules, run the following commands in the VS Code IDE terminal.


cd ~/environment/lambda
npm install
zip -r ../lambda.zip *
Download the resulting lambda.zip file from the VS Code IDE to your computer:

In the Environment window, open the context (right-click) menu for the lambda.zip file, and then choose Download.

When prompted, save the file.

 

Finish configuring the generateReportData Lambda function.

Return to the Lambda console, where you were configuring the generateReportData function.

Choose the Code tab.

In the Code source section, choose Upload from, and then choose .zip file.

Choose Upload, and then browse to and open the lambda.zip file that you just saved to your computer.

Choose Save.

Verify that the Environment panel in the Code source section now shows that the files contained in the .zip file were uploaded and extracted successfully, as shown in the following image.

Extracted files listed in Environment window

 

Configure the generateReportData Lambda function to access resources in the virtual private cloud (VPC).

In the Lambda console, choose the Configuration tab, and then choose VPC.

In the VPC section, choose Edit.

Choose the VPC named Lab IDE VPC.

For Subnets, choose both us-east-1a and us-east-1b.

For Security groups, choose the security group that has ClusterSecurityGroup in the name.

When you are satisfied that your settings are correct, choose Save.

A message that says Updating the function generateReportData appears in a blue bar at the top of the console.   

Note: The update might take about 5 minutes to complete. When the update completes, the function will be able to connect to the database.

 

Test the generateReportData function with the new VPC settings applied.

In the Lambda console, return to the Code tab.

Choose the down arrow next to Test, and choose Configure test event.

Choose Create new test event.

For Event name, enter vpcAdjusted

Choose Save, and then choose Test again.

The response includes all eight records from the Amazon RDS database.

Note: If the test times outs and does not show the results, choose Test again.

The following code block shows the first and last records for reference.


{
  "my_json_arr": [
    {
      "suppliers_id_int": 1,
      "supplier_name_str": "AnyCompany coffee suppliers",
      "supplier_address_str": "123 Any Street",
      "bean_info_obj_arr": [
        {
          "type_str": "Arabica",
          "product_name_str": "Best bean",
          "price_int_str": "18.00"
        },
        {
          "type_str": "Robusta",
          "product_name_str": "Great bean",
          "price_int_str": "12.00"
        }
      ]
    },
    {
      "suppliers_id_int": 8,
      "supplier_name_str": "Southern AnyCompany coffee suppliers",
      "supplier_address_str": "555 Main st",
      "bean_info_obj_arr": [
        {
          "type_str": "Liberica",
          "product_name_str": "Ace bean",
          "price_int_str": "10.00"
        },
        {
          "type_str": "Excelsa",
          "product_name_str": "Unrivaled bean",
          "price_int_str": "16.00"
        }
      ]
    }
  ]
}
Excellent! Your function now retrieves coffee supplier inventory records from the database.

Task 9: Adding the generateReportData function to the state machine
In this final task, you will update the Step Functions state machine to invoke the generateReportData Lambda function that you just created. This function needs to run prior to the parallel step. You must retrieve the inventory records in JSON format from the database before you can run the generateHTML function to create the HTML report.

 

Add the generateReportData function to the state machine.

Navigate to the Step Functions console.

Select MyStateMachine, and then choose Edit.

Search for Lambda

Drag an AWS Lambda Invoke object onto the canvas, above the Process Report parallel state object.

 

Configure the function details in the Lambda Invoke pane.

State name: Enter getRealData

Function name: Choose generateReportData:$LATEST.

Payload: Choose No payload.

Choose Save.

Test the completed state machine by using the Step Functions console.

Choose Execute and configure the following:

In the code editor, delete the name-value pair that appears on line 2. The input code should only include the brackets, as shown in the following code block.


{
}
Choose Start execution.

Check your email for a notification, and choose the presigned URL in the message to verify that you can load the report.

Troubleshooting tips:

If the express execution does not succeed the first time due to a timeout error, try it again.

Check your email for a notification, and choose the presigned URL in the message to verify that you can load the report.When testing the presigned URL that arrives in your email inbox, be sure to copy the entire URL into a browser tab. Sometimes the email client does not place a hyperlink behind the entire URL, which includes &Expires=some-number at the end.

If the emails arrive too slowly, the URL might expire before you receive it. Consider increasing the timeout in the GeneratePresignedURL function code source. Save the change and deploy it. You can also try increasing the timeout of the other Lambda functions.

 

Test the create_report REST API endpoint.

Navigate to the API Gateway console.

Choose the link for ProductsApi.

In the navigation pane, choose Stages.

In the Resources pane, choose prod.

Copy the Invoke URL.

Return to the VS Code IDE.

In the terminal, enter curl -X POST but do not run the command yet.

Add a space and then paste in the invoke URL that you just copied. Do not run the command yet.

Add /create_report to the end of the invoke URL.

The resulting command looks similar to the following, where unique-string is some unique string:

curl -X POST https://unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report

Run the command.

The response looks similar to the following.


{
  "executionArn":"arn:aws:states:us-east-1:221264991720:express:MyStateMachine:453b6f3d-ab5a-4ac3-a2d2-0d74f728a740:243fcd35-ff80-4f8d-bc2a-b0580391277e","startDate":1.632788164722E9
}
Check your email for a notification, and load the report using the presigned URL contained in the email.

The HTML report displays, as shown in the following image.

Inventory report formatted in HTML

As you can see, the link gives Frank a report! The report shows the latest data from the suppliers database, which is running in a private subnet.

Refresh the report after the presigned URL has expired to verify that the link no longer allows access to the report.

Excellent! The whole state machine works as intended! The following diagram shows the final state machine that you created.

Final state machine workflow

 

Update from the café
Café counter

Now that Sofía has the report functionality working, she shows her work to Frank. She subscribes his email address to the SNS topic so that he will receive an email with the report link, which she generates by posting to the REST API endpoint.

Sofía explains that the presigned URL approach is only a temporary solution. She will connect the café website to an authentication service so that Frank can log in to the website and request a report by simply choosing a report icon. That usability enhancement will use the state machine that Sofía finished building in this lab.

Sofía knows that she has more work to do, but for the moment, she is pleased to have reached this milestone. She rewards herself with a slice of chocolate cake. Delicious!

 

Submitting your work
At the top of these instructions, choose Submit to record your progress and when prompted, choose Yes.

Tip: If you previously hid the terminal in the browser panel, expose it again by selecting the Terminal  checkbox. This action will ensure that the lab instructions remain visible after you choose Submit.

 

If the results don't display after a couple of minutes, return to the top of these instructions and choose Grades

Tip: You can submit your work multiple times. After you change your work, choose Submit again. Your last submission is what will be recorded for this lab.

 

To find detailed feedback on your work, choose Details followed by  View Submission Report.

 

Lab complete 
 Congratulations! You have completed the lab.

Choose End Lab at the top of this page, and then select Yes to confirm that you want to end the lab.

A panel indicates that DELETE has been initiated... You may close this message box now.

 

Select the X in the top-right corner to close the panel.

 

© 2025 Amazon Web Services, Inc. and its affiliates. All rights reserved. This work may not be reproduced or redistributed, in whole or in part, without prior written permission from Amazon Web Services, Inc. Commercial copying, lending, or selling is prohibited.