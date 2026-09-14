Lab 12.1: Implementing Application Authentication Using Amazon Cognito
Lab overview and objectives
In this lab, you will work as Sofía to integrate Amazon Cognito into the café website. Frank wants to be able to log in and request a coffee bean inventory report directly from the café website. Amazon Cognito provides an authentication service, which Sofía wants to use for this website enhancement. This usability enhancement will use the state machine that you built in the previous lab using AWS Step Functions.

After completing this lab, you should be able to:

Create an Amazon Cognito user pool

Create an Amazon Cognito user pool user

Configure an app client to use Amazon Cognito as an authentication service

Integrate an Amazon Cognito app client into a website

Update REST API endpoints that are built with Amazon API Gateway to call Amazon Cognito for authentication purposes

Configure an API Gateway authorizer

Duration
This lab will require approximately 90 minutes to complete.


AWS service restrictions
In this lab environment, access to AWS services and service actions might be restricted to the ones that are needed to complete the lab instructions. You might encounter errors if you attempt to access other services or perform actions beyond the ones that are described in this lab.

 

Scenario
Frank wants to be able to log in to the café website and request an inventory report to be sent to his email address (on his phone). He wants to be able to see the latest coffee bean inventory data quickly. In this lab, you will play the role of Sofía to implement this technical feature request.

In the previous lab, Sofía created a Step Functions state machine that, once invoked, can generate the report that Frank wants. However, the state machine can currently only be invoked by using the test feature in the Step Functions console or by running a curl command to invoke the create_report REST API endpoint.

In this lab, Sofía will use Amazon Cognito to integrate an authentication mechanism into the website. Frank will be able to log in to the website to confirm his identity before he requests the report. Then, she will connect the REST API endpoint to the café website so that he can make his report request directly from the site. The API request will include the ID token that is retrieved as part of the authentication process, and Amazon Cognito will be used to validate the token. Then, the Step Functions state machine will be invoked, which will then invoke the AWS Lambda functions that generate the report.

The following diagram shows the architecture that was created for you in AWS at the start of the lab. The highlighted section is the part that you will modify in this lab. Notice that the login action does not yet work, and the website is not connected to the create_report API endpoint.

Café website architecture at start of lab

 

By the end of this lab, you will have created the architecture shown in the following diagram. Notice that authentication is tied into the website. Frank can use his authenticated session from the café website to directly invoke report creation.

Café website architecture at end of lab

 

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

For all three stacks, verify that the Status says CREATE_COMPLETE. 

⚠️ If any stack doesn't yet have that status, wait until it does. It might take about 12 minutes to complete from the time that you chose Start Lab.

 

Connect to the VS Code IDE.

At the top of these instructions, choose Details followed by  AWS: Show 

Copy values from the table for the following and paste it into an editor of your choice for use later.

LabIDEURL

LabIDEPassword

In a new browser tab, paste the value for LabIDEURL to open the VS Code IDE.

On the prompt window Welcome to code-server, enter the value for LabIDEPassword you copied to the editor earlier, choose Submit to open the VS Code IDE.

 

Download and extract the files that you need for this lab.

In the VS Code IDE bash terminal, run the following command:



wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/12-lab-cognito/code.zip -P /home/ec2-user/environment
Notice that a code.zip file was downloaded to the VS Code IDE. The file is listed in the Environment window.

Extract the file:


unzip code.zip
 

Run the script that re-creates the work that you completed in earlier labs into this AWS account.

Set permissions on the script so that you can run it, and then run it:


chmod +x ./resources/setup.sh && ./resources/setup.sh
When prompted for an IP address, enter the IPv4 address that the internet uses to contact your computer. You can find your IPv4 address at https://whatismyipaddress.com.

Note: The IPv4 address that you set is the one that will be used in the bucket policy. Only requests that originate from this IPv4 address will be allowed to load the website pages. Do not set it to 0.0.0.0 because the S3 bucket's block public access settings will prevent access.

When prompted for an email address, enter one that you have access to as you complete the lab.

Verify that the script did not encounter any errors.

If you see any "An error occurred" lines just before the "done" line, the script might have been run too soon after you started the lab. Run the setup.sh script again to clear errors.

If you don't see any error lines, you can assume that the script ran successfully.

Analysis: The CloudFormation template that ran when you started this lab created resources in the AWS account. The script you just ran also created resources. Between the two of them, resources have been created to replicate what you built in previous labs.

 

Verify the version of AWS CLI installed.

In the VS Code Bash terminal, run the following command:


aws --version
The output should indicate that version 2 is installed.

 

Verify that the SDK for Python is installed.

Run the following command:


pip3 show boto3
Note: If you see a message about not using the latest version of pip, ignore the message.

 

Confirm the Amazon Simple Notification Service (Amazon SNS) email subscription.

Check your email for a message from AWS Notifications.

In the email body, choose the Confirm subscription link.

A webpage opens and displays a message that the subscription was successfully confirmed. You can close this page.

 

Verify that you can access the café website through Amazon CloudFront, and test the current login button behavior.

Navigate to the CloudFront console.

Note: You cannot access the website through an Amazon Simple Storage Service (Amazon S3) URL. You must access the site by using CloudFront.

Choose the hyperlink for the distribution that was created for the lab. You can get the ID from the script output you ran earlier. Look for the message This is the Cloudfront Distribution created for the lab: in the output.

Copy the Distribution domain name value, and then load that URL in a new browser tab.

The café website displays. If it doesn't, see the following troubleshooting tip.

Troubleshooting tip: If you are using a VPN, the IP address returned by whatismyipaddress.com might not allow access to the café website. If you can't connect to the café website, disconnect from VPN. Find your IP address again using whatismyipaddress.com, and then run setup.sh again. Then, stay off of the VPN for the duration of this lab.

Choose the LOGIN link in the upper-right corner.

Notice that the link does not currently work. Instead, it returns the message No API to call. This is expected. You will configure the login functionality during this lab.

Keep the café website open in this browser tab. You will return to it later in this lab.

 

Task 2: Configuring an Amazon Cognito user pool and app client
In this task, you will configure an Amazon Cognito user pool and begin the process of creating an app client.

Begin to create an Amazon Cognito user pool.

Navigate to the Amazon Cognito console.

Choose Create user pool. 

If this is not visible, choose  menu and choose User pools and then choose Create user pool.

On the Set up resources for your application page, configure the following options:

For Application type, ensure that Traditional web application is already selected.

For Name your application: the_cafe_app_client

Under the Configure options, choose Username

For Required attributes for sign-up, choose email from the dropdown.

For Add a return URL - optional, enter https://<cloudfront-domain>/callback.html, and replace  with the CloudFront distribution domain from your text editor.

Note: The updated URL should be similar to the following: https://d123456acbdef.cloudfront.net/callback.html

Choose Create user directory button.

On the next page displayed, under Check out your sign-in page, choose View login page.

Notice the Sign-in page which you will configure later, close the browser tab.

Go back to the User pools and choose the pool you created.

User pool Name should be similar to User pool - zzzzzz

On the Overview: page, you notice the pool details and other configuraiton information.

Choose Rename button and under User pool name enter the_cafe, choose Save changes.

Copy the value for User pool ID to the editor.

From the bottom Recommendations pane, choose the_cafe_app_client link.

Go to Login pages:

On the Managed login pages configuration choose edit.

Under Allowed sign-out URLs - optional:

Choose Add sign-out URL

in the URL field, enter https://<cloudfront-domain>/sign_out.html, and replace the  placeholder with the CloudFront distribution domain. 

For OAuth 2.0 grant types, Clear the Authorization code grant. 

From the dropdown list, choose Implicit grant.

For OpenID Connect scopes, ensure that Email and OpenID are chosen, and clear Phone.

Choose Save changes button.

On the App client: the_cafe_app_client page, choose Edit.

For Authentication flows, from the dropdown list 

Choose ALLOW_USER_PASSWORD_AUTH, 

Clear ALLOW_USER_SRP_AUTH.

Choose Save changes.

Next you create and add users to the user pool.

 

Task 3: Configuring the app client
In this task, you will configure the app client that you created in the previous task, so that the app client will invoke the create_report REST API endpoint. 

 

Configure a resource server for the user pool to call the create_report REST API endpoint.

In the the_cafe user pool page, from the navigation on the left, choose the Domain.

In the Resource servers area, choose Create resource server and configure:

Resource server name: Enter cafe_resource_server

Resource server identifier: Use the following steps to retrieve the invoke URL and paste it here.

To find the invoke URL:

In a new browser tab, navigate to the API Gateway console.

Choose the link for ProductsApi.

In the left navigation pane, choose Stages.

In the Stages tree, expand the prod stage.

Under /create_report, choose POST.

Copy the Invoke URL, which looks similar to the following: https://some-unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report

Return to the Amazon Cognito console, and paste the invoke URL into the Identifier field, as shown in the following image: 

Identifier field in the Amazon Cognito console

Choose Create resource server.

Confirm that the hosted UI is now available.

Choose overview, and choose the the_cafe_app_client link

Choose View login page.

A webpage opens and displays a login screen.

Analysis: You have not yet defined a user to log in with, so you cannot log in. However, you need to capture the URL of this page to help you complete the next task.

Copy the full URL from the address bar in your browser to your clipboard.

The URL looks similar to the following,    


https://us-east-1n4owktjfa.auth.us-east-1.amazoncognito.com/login?client_id=6u5emdk4tfulegqqi12de3f692&response_type=token&scope=email+openid&redirect_uri=https%3A%2F%2Fdtqfgmz405sjd.cloudfront.net%2Fcallbackhtml
Keep the copied link in your clipboard so that you can use it in the next task.

Congratulations! You have configured an app client that can use the Amazon Cognito user pool that you created. The next step is to integrate this new Amazon Cognito hosted login user interface into the café website.

 

Task 4: Integrating the Amazon Cognito hosted UI into the website
In this task, you will update the website so that it calls Amazon Cognito to confirm whether access should be granted to the user to generate a report.

Configure the website to invoke the new app.

Return to the VS Code IDE.

Open the resources/website/config.js file in the text editor.

Analysis: This is a copy of the configuration file in Amazon S3 where the website .js and .html files are hosted. You will use the config.js file to integrate authentication into the café website. As you can see, COGNITO_LOGIN_BASE_URL_STR does not have a value yet. In this task, you will update this local copy of the configuration file and then upload it to Amazon S3 to deploy the change to the application behavior.

Replace the null value for COGNITO_LOGIN_BASE_URL_STR with the hosted login URL that you just copied. Surround the URL in double quotation marks.

The file contents should now look similar to the following (where each unique-string is a unique string value that reflects the configurations in your account). Be sure to surround the URL in double quotes.


window.COFFEE_CONFIG = {
API_GW_BASE_URL_STR: "https://unique-string.execute-api.us-east-1.amazonaws.com/prod",
COGNITO_LOGIN_BASE_URL_STR: "https://unique-string.auth.us-east-1.amazoncognito.com/login?client_id=unique-string&response_type=token&scope=email+openid&redirect_uri=https://unique-string.cloudfront.net/callback.html"
};
Close the file using X, the changes to the file are saved automatically.

In the VS Code IDE Bash terminal, to update the copy of the config.js file that is hosted on Amazon S3, run the following two commands.


bucket=$(aws s3api list-buckets --query "Buckets[].Name" | grep s3bucket | tr -d ',' | sed -e 's/"//g' | xargs)
aws s3 cp ./resources/website/config.js s3://$bucket/ --cache-control "max-age=0"
 

Confirm the café website's updated behavior.

Return to the browser tab where you have the café website open.

Note: If you no longer have the café website tab open, browse to the CloudFront console, choose the link for the distribution, and copy the Distribution domain name value. Load that URL in a new browser tab.

Refresh the browser tab to load the change to the website configuration into the browser session.

Choose the LOGIN link in the upper-right corner.

Notice that the Amazon Cognito login interface now displays. The login link has redirected the user to an Amazon Cognito hosted login page. You cannot log in yet, because a user is not yet defined, but this represents progress toward the solution.

Choose the browser's back button to return to the main café website page. Keep this browser tab open to return to later in this lab.

 

Task 5: Observing the REST API endpoint details and testing
In this task, you will redeploy the REST API so that the updates that were made to the create_report endpoint when the lab started are applied.

Analysis: Sofía needs to configure the API so that when an authentication request is made to Amazon Cognito (when a user logs in), logic is in place to handle the token that comes back from Amazon Cognito. Amazon Cognito will redirect the user to the website's /callback page. The JavaScript code in that page simply takes the token and stores it in the browser, so that it can be used in a future AJAX request. That AJAX request will send the token in a header called an Authentication header. Originally, cross-origin resource sharing (CORS) for the create_report REST API endpoint was configured to work with the Amazon S3 website. This configuration was updated to accept the header from the CloudFront distribution.

 

Observe the CORS settings for the create_report API endpoint.

Navigate to the API Gateway console.

Choose the link for ProductsApi.

Choose Resources.

In the Resources tree, under /create_report, choose OPTIONS.

Choose Integration Response.

Expand the existing row that has a 200 method response status.

Expand the Header Mappings section.

Notice that the Access-Control-Allow-Origin setting already points to your CloudFront distribution and looks similar to the following (the unique-string value in your setting will be a unique string):

Note: You do not need to update this setting.


'https://unique-string.cloudfront.net'
Note: This configuration was set when you started the lab.

 

Test sending a report from the API Gateway console.

In the Resources tree, under /create_report, choose POST.

From the lower pane, choose TEST , and then scroll down and choose the Test button.

Observe the Response Body and Response Headers in the test panel. JSON code is displayed in both.

Also observe the Logs panel details. A final line states Method completed with status: 200.

Check your email. You receive an email with a presigned URL for the inventory report. Open the presigned URL in a new browser tab or window.

Note: It might take a minute or two for the email to arrive. By choosing Test, you invoked the Step Functions state machine, which in turn invokes a few Lambda functions to generate the report.

Troubleshooting tip if you don't receive the email: If you do not receive the email after waiting at least 2 minutes, follow these steps:

In a new browser tab, navigate to the WAF & Shield console.

In the navigation pane, choose IP sets.

Choose the link for office_regional to view the details.

Verify that the IP address entry contains your IP address as returned by https://whatismyipaddress.com with /32 appended.

If your IP address is not listed, choose Add IP address, and add it (append /32 to the address).

 

Troubleshooting tip if the URL in the email doesn't display a report: If you do receive the email, but the URL in the email does not display the report, follow these steps:

If the email arrives, but it has been more than 60 seconds between when you chose Test and when you try to load the presigned URL received in the email, the URL might have expired.

Navigate to the Lambda console. For the GeneratePresignedURL function code source, change the expires_in_seconds_int value from 60 to a higher value, such as 240.

Save the change, and then choose Deploy at the top of the Code source section.

Then, return to the API Gateway console and run the test again.

Analysis: It was a good idea to confirm that you can successfully receive a report by invoking the create_report API endpoint. However, you don't want just anyone to be able to create a report and have it emailed to them. In the API Gateway lab earlier in this course, you secured requests to the API endpoint so that only calls from a certain IP range were accepted. However, that approach would still allow anyone on the café network to invoke the call. In the next tasks, you will implement an improved application security posture. You will modify the configuration to take advantage of the Amazon Cognito configuration that you have made.

 

 

Task 6: Creating a user for the Amazon Cognito user pool
In this task, you will create a user named frank. You will then configure the REST API to only allow authenticated calls to the create_report endpoint.

 

Create a user for the Amazon Cognito user pool.

In the Amazon Cognito console choose the link for the the_cafe user pool.

From the navigation pane, under User management choose Users.

In the Users panel, choose Create user and configure:

Invitation message: Don't send an invitation

Username: frank

Temporary password: Set a password

Password: Enter a password that you will remember; for example: !CoffeeIsGreat34

Choose Create user.

A new row appears on the Users tab with the details of the new user.

 

Test logging in as Frank.

Return to the café website.

If you closed it, you can load the website by using the CloudFront distribution domain name.

Choose LOGIN and enter the credentials that you just created:

Username: Enter frank

Password: Enter the password that you created a moment ago.

Choose Sign in.

If successful, you are prompted to enter a new password.

For example, you could enter: !CoffeeIsGreat35

Enter the new password in both fields, and then choose Change password.

If successful, you see a link named REPORT where the LOGIN button previously appeared.

Analysis: The website redirected the frank user to the callback page, and then it immediately returned the user to the café website.

Choose the REPORT hyperlink.

You see the message Report is being generated, please check your email.

Check your email, and verify that you can access the report by using the presigned URL that is included in the email.

If you can access the report, excellent! It looks like everything is working as intended. If you cannot access the report, follow the steps in the troubleshooting tips at the end of Task 5.

 

Test the ability to bypass the website and instead invoke create_report by using a curl command.

In the VS Code IDE Bash terminal, run the following command. Replace the URL with the create_report invoke URL, which you copied from the API Gateway console earlier.


curl -X POST https://unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report
You see the following response:


{"message":"Forbidden"}
Analysis: This is expected! It fails because the AWS WAF settings that you configured in the previous lab only allow calls to API Gateway from the café office. (In the café scenario, the café office IP is the one that your local computer uses to connect to the internet.) This is the same IP address that you entered in Task 1 of this lab when prompted by the setup script. The VS Code IDE connects to the internet through a different IP address; therefore, the request is denied.

Now try to run the same command from your local machine. For example, if you are using a Windows machine, run the command in a Command Prompt window. If you are using macOS, run the command in a Terminal window.

You see a response similar to the following:


{"executionArn":"arn:aws:states:us-east-1:628920026067:express:MyStateMachine:3baf0092-d43c-4652-9502-b3132d366fdd:f26ce13a-681e-4763-a448-e1de052f05f4","startDate":1.632520615488E9}
In addition, another report link is sent to your email address.

Note: Keep the Command Prompt or Terminal window open to use again later in this lab.

Analysis: This is not ideal. Sofía doesn't want just anyone who is on the café's office network to be able to generate a report. She decides to further lock down access to this API endpoint. She decides to configure it so that API Gateway needs to authorize the create_report request as well. To accomplish that, she needs to configure a custom authorizer.

 

Task 7: Configuring an API Gateway authorizer
In this task, you will configure an API Gateway authorizer. The authorizer will provide the ability to use a request parameter that can be used to verify the identify of a user who requests the create_report method.

 

Add an authorizer to the ProductsApi REST API.

Return to the API Gateway console.

Choose the link for ProductsApi.

In the navigation pane, choose Authorizers.

Choose Create authorizer and configure:

Name: Enter cafe_lockdown

Type: Choose Cognito.

Cognito User Pool: Choose the dialog box to the right of us-east-1, and then select the_cafe.

Token Source: Enter Authorization

Keep Token Validation blank.

Choose Create authorizer.

The page refreshes.

 

Configure the create_report method request to call Amazon Cognito to verify authorization.

Refresh the API Gateway console page.

In the navigation pane, choose Resources.

In the Resources tree, under /create_report, choose POST.

Choose Method Request.

In the Settings area, notice that Authorization is currently set to NONE.

Edit the authorization setting:

Choose the pencil icon next to Authorization.

In the dropdown menu, under Cognito user pool authorizers, choose cafe_lockdown.

To save the setting change, choose the check mark icon.

Expand the HTTP Request Headers section.

Choose Add header and configure:

For Name, enter Authorization

To save the setting change, choose the check mark icon.

Select Required.

 

Deploy the REST API updates.

In the Resources tree, choose /, which is the root of the API.

From the Actions menu, choose Deploy API and configure:

Deployment stage: Choose prod.

Choose Deploy.

Choose Save Changes.

 

Test sending a report by using the curl command again.

Return to the Command Prompt or Terminal on your local machine.

Press the Up arrow key to load the same curl command that you ran previously. Then, press Enter on your keyboard to run it.

The command looks like the following:


curl -X POST https://unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report
You receive the following response:


{“message”: “Unauthorized”}
Important: If you first get a different response (with an executionArn name-value pair), wait a moment. Then, try the command again. It might take a moment for the setting changes to propagate, but you should then receive the Unauthorized response.

Analysis: The Unauthorized response is expected, because the endpoint now expects to receive an authorization header, and you did not send one.

 

Task 8: Testing the request process from the website
In this final task in the lab, you test the full solution. You will log in to the café website as the frank user and then use the website to request the report. The call should still succeed, even with the authorization check now applied to the method request on the API endpoint.

 

Test the ability to create the report from the website.

Return to the café website.

If you closed it, you can load the website by using the CloudFront distribution domain name.

If you are not already logged in, choose LOGIN and enter the credentials that you created previously:

Username: Enter frank

Password: Enter the password; for example: !CoffeeIsGreat35

Choose Sign in.

On the website, choose the REPORT hyperlink.

You see the message Report is being generated, please check your email.

Check your email, and verify that you can access the report by using the presigned URL.

If you can access the report, excellent! It looks like everything is working as intended. If you cannot access the report, follow the steps in the troubleshooting tips at the end of Task 5.

 

Optional step: Find the authorization token in the browser session and test it with the curl command.

On the café website page, open the context menu (right-click) and choose Inspect (if using Chrome) or Inspect Element (if using Firefox).

In the developer tools area that appears, choose the Network tab.

On the café website, choose the REPORT hyperlink again.

A list of all the files and accessed locations displays in the developer tools area.

Choose (double-click) the create_report entry for the POST action that appears.

Note: Depending on your browser, you might need to choose All to see the entry. In Chrome, the entry type for create_report is xhr. In Firefox, choose the create_report entry that shows POST in the Method column.

Observe the Request Headers details. Notice the field that shows authorization and contains the word Bearer followed by a long credentials value.

Copy the entire string value, including Authorization: Bearer.

Return to the Command Prompt window (or Terminal window) on your local machine.

Press the Up arrow key to load the last curl command that you ran. Do not run the command yet.

At the end of the command, add -H. Then, paste in the credentials value that you just copied from your browser. Surround the credentials value in double quotation marks.

The resulting command looks similar to the following (where unique-string is part of your API Gateway invoke URL and  VeryLongStringValue is the authorization token value that you copied):


curl -X POST https://unique-string.execute-api.us-east-1.amazonaws.com/prod/create_report -H "Authorization: Bearer VeryLongStringValue"
Run the command.

This time the curl command should succeed, because you passed in the authorization token.

 

Optional step: Test by using the API Gateway authorizer tester.

Navigate to the API Gateway console.

In the navigation pane, choose Authorizers.

On the cafe_lockdown card, choose Test.

In the Authorization Token area, for Authorization (header), paste in the Bearer VeryLongStringValue string, and then choose Test.

The result looks similar to the following:

Authorizer test window showing response

 

Optional step: Observe the café website application logic that sends the authorization header.

In the VS Code IDE, open the resources/website/scripts/main.js file in the text editor.

Scroll down and observe the logic that appears in the attemptCreateReport function, which starts around line 71.

As you can see, the code checks whether the API Gateway URL string has been configured (you configured this in the config.js website file in Task 4). If it has been configured, the function passes the Authorization HTTP header value.

 

Update from the café
Café counter

Sofía is proud of the work that she has done. She always intended to implement an authorization system to protect the parts of the café website that should not be open to everyone, and now she has done so. She knows that she could expand her use of Amazon Cognito to other parts of the website as well. But for now, she is glad that the report creation feature is more secure from unauthorized access than it was before.

Frank is also impressed. He finds it easy to go to the website to request a report whenever he wants one. And he likes that the site now prompts him to log in before granting him access to do that.

 

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