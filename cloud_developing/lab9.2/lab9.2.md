Lab 9.2: Implementing CloudFront for Caching and Application Security
Lab overview and objectives
In this lab, you will create an Amazon CloudFront distribution to reduce network latency for café website users and deliver the website securely over HTTPS. You will also secure access to the website and REST API endpoints using AWS WAF, which is a service that provides a web application firewall. Finally, you will configure a CloudFront function on the website and adjust the cached file expiration time on the website content.

After completing this lab, you should be able to:

Create a CloudFront distribution to cache Amazon Simple Storage Service (Amazon S3) objects

Configure a website hosted on Amazon S3 to be available through HTTPS using CloudFront

Secure access to the CloudFront distribution based on the network origin of the request

Secure a REST API endpoint based on the network origin of the request using AWS WAF

Configure a CloudFront function to affect website behavior from the edge

Adjust max-age caching settings on a CloudFront distribution

 

Duration
This lab will require approximately 90 minutes to complete.


AWS service restrictions
In this lab environment, access to AWS services and service actions might be restricted to the ones that are needed to complete the lab instructions. You might encounter errors if you attempt to access other services or perform actions beyond the ones that are described in this lab.

 

Scenario
Sofía is pleased with how the café website development project is coming along. She has developed the core serverless application that displays menu items on the website. She also integrated the coffee suppliers web application into the main site and is using Amazon ElastiCache features for the suppliers part of the site.

However, she knows that some essential features are still missing. One feature is that the website still runs on HTTP and does not yet support HTTPS. Sofía also wants to ensure that the website will load quickly for users globally. She knows that AWS has many Regions and Availability Zones, but they also have edge locations, which are even closer to users around the globe. She decides to host the café website on a proper content delivery network (CDN), and she has opted to use the CloudFront service.

In this lab, you will again play the role of Sofía to continue to develop the café's web application.

When you start the lab, your architecture will look like the following diagram, with several preconfigured resources.

Café website architecture at the beginning of the lab

By the end of this lab, you will have created the architecture in the following diagram. The highlighted portion shows the part of the architecture that you will work on in the lab.

Café website architecture at the end of the lab

 

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
In this first task, you will configure your VS Code IDE. You will also run the script to recreate the work you completed in previous labs.

 

Before proceeding to the next step, verify that the AWS CloudFormation stack creation process for the lab has successfully completed.

In a new browser tab, navigate to the CloudFormation console.

In the left navigation pane, choose Stacks.

For the stack with "ACD_2.0" in the Description column, verify that the Status says CREATE_COMPLETE. 

⚠️ If it doesn't show CREATE_COMPLETE yet, wait until it does. Because this stack is creating an Amazon Relational Database Service (Amazon RDS) database instance, it might take about 5 minutes to complete.

 

Connect to the VS Code IDE.

At the top of these instructions, choose Details followed by  AWS: Show 

Copy values from the table for the following and paste it into an editor of your choice for use later.

LabIDEURL

In a new browser tab, paste the value for LabIDEURL to open the VS Code IDE.

 

Download and extract the files that you need for this lab.

In the same terminal, run the following command:



wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCDEV-2-91558/09-lab-cloudfront/code.zip -P /home/ec2-user/environment
The code.zip file is downloaded to the VS Code IDE. The file is listed in the left navigation pane.

Extract the file:


unzip code.zip
 

Run a script to upgrade the version of Python and the AWS CLI that are installed on the VS Code IDE. The script also recreates the work that you completed in earlier labs into this AWS account.

Set permissions on the script so that you can run it, and then run the script:


chmod +x ./resources/setup.sh && ./resources/setup.sh
When prompted for an IP address, enter the IPv4 address that the internet uses to contact your computer. You can find your IPv4 address at https://whatismyipaddress.com.

Note: The IPv4 address that you set is the one that will be used in the bucket policy. Only requests that originate from this IPv4 address will be allowed to load the website pages. Do not set it to 0.0.0.0 because the S3 bucket's block public access settings will prevent access.

Verify that the script did not encounter any errors:

If you see any "An error occurred" lines just before the "done" line, the script might have been run too soon after you started the lab. Run the setup.sh script again to clear errors.If you don't see any error lines, you can assume that the script ran successfully.

 

Analysis: The CloudFormation template that ran when you started this lab created resources in the AWS account. The script you ran also created resources. Between the two of them, the following resources have been created to replicate what you built in previous labs:

An S3 bucket with an associated bucket policy. The bucket contains the café website code.

An Amazon DynamoDB table populated with menu data.

A REST API configured using Amazon API Gateway.

An AWS Lambda function that retrieves data from DynamoDB when invoked.

A Memcached cluster that caches supplier data from Amazon Aurora Serverless for the suppliers application.
A café/node-web-app Docker image, which is stored in the Amazon Elastic Container Registry (Amazon ECR).

An AWS Elastic Beanstalk environment and application that runs an EC2 instance named MyEnv. The EC2 instance hosts a Docker container created from the Docker image that is stored in Amazon ECR.

An Aurora Serverless database running MySQL on Amazon RDS, which contains the supplierdb database, which stores coffee supplier information.

 

Verify the version of AWS CLI installed.

In the VS COde IDE Bash terminal (at the bottom of the IDE), run the following command:


aws --version
The output should indicate that version 2 is installed.

 

Verify that the SDK for Python is installed.

Run the following command:


pip3 show boto3
Note: If you see a message about not using the latest version of pip, ignore the message.

Keep the VS Code IDE open in your browser. You may use it later in this lab.

 

Note the metadata settings on the objects stored in the S3 bucket, and then verify that you can access the café website.

Navigate to the Amazon S3 console.

Choose the link for the bucket that has -s3bucket in the name.

Choose the index.html link.

Scroll down to the Metadata section.

Two key-value pairs are listed. The Cache-Control key-value pair has a value of max-age=0. This was set when you ran setup.sh in an earlier step. Line 21 of that script ran the command aws s3 cp ./resources/website s3://$bucket/ --recursive --cache-control "max-age=0" to set this metadata value on every file that it uploaded to the bucket. You'll learn about the significance of this setting later in the lab.

At the top of the page, open the Object URL in a new browser tab.

The café website displays. If it doesn't, see the following troubleshooting tip.

Troubleshooting tip: If you are using a VPN, the IP address returned by whatismyipaddress.com might not allow access to the café website. If you can't connect to the café website, disconnect from VPN. Find your IP address again using whatismyipaddress.com, and then run setup.sh again. Then, stay off of the VPN for the duration of this lab.

Keep the website open in this browser tab, because you will return to it later in this lab.

 

 

Task 2: Configuring a distribution for static website content
In this task, you will configure the café website, which is hosted on Amazon S3, to be available through a CloudFront distribution. With the distribution, you can enable HTTPS access to the website.

Detailed analysis: Recall from earlier labs that static website hosting, which would make the site available at https://.s3-website.amazon.com, is not configured on the café website S3 bucket. Instead, you access the website by loading the Object URL of the index.html file from the bucket, which is in the form http://.s3.amazon.com/index.html. Therefore, the site is not currently accessed using HTTPS. Sofía hasn't worried about this until now, because she knew she would integrate other AWS services into the website design and would use CloudFront as part of the final application design.

 

Begin to configure a CloudFront distribution for the café website hosted on Amazon S3.

Navigate to the CloudFront console.

Choose Create distribution.

If prompted to Choose a plan, choose Pay as you go, choose Next

Tip: You will configure several settings for the distribution over the next few steps. Pay careful attention not to miss any steps, and don't finish creating the distribution until you are specifically instructed to.

 

Configure the settings for the distribution as follows:

Distribution name: Enter access-identity-cafe-website

Distribution type: Choose Single website or app 

Choose Next.

For Origin type: Choose Amazon S3 if not already selected.

Under Origin ==> S3 Origin: Choose Browse S3 and select the bucket that has -s3bucket in the name. This bucket contains the website code.

Under Settings

For Origin settings

Choose Customize origin settings

Choose Add header

Header name: Enter cf

Value: Enter 1

For Cache settings

Choose Customize cache settings 

Choose Next

On the Enable security page, for Web Application Firewall (WAF), choose Next

On the Review and create page

Choose Create distribution

While the distribution is being created, Last modified at the top of the page displays Deploying as shown in the following image.

CloudFront distribution status

 

Note: It might take 5 to 10 minutes for the deployment to complete.

After the distribution is ready, you notice the timestamp against Last modified.

On the distribution page, choose Edit

Default root object: Enter index.html

IPv6: Off

Choose Save changes.

Note: It might take 5 minutes for the deployment to complete.

Copy the value for Distribution domain name on the same page and paste it in a new browser window to check that the website is displayed.

Note: This is the café website homepage hosted in the S3 bucket accessed via the CloudFront distriution you created.     

   

Update the bucket policy.

In a new browser tab, navigate to the Amazon S3 console.

Choose the link for the bucket that has -s3bucket in the name.

Choose the Permissions tab.

In the Bucket policy section, choose Edit.

In the Policy code section, delete lines 4 through 17, which are highlighted in the following image.

Bucket policy with lines 4 to 17 highlighted

At the bottom of the page, choose Save changes.

 

Retest access to the café website after the update to the bucket policy.

Return to the browser tab where the café website is open, and refresh the browser page.

You no longer see the site. Instead, you see an AccessDenied error similar to the following image.

Access denied error

Note: This outcome is expected, because you removed the lines from the bucket policy that granted s3:GetObject access for requests coming in from your IP address. You don't want anyone to access the website directly using the Amazon S3 URL. Instead, you want users to access the site through CloudFront.

Close the browser tab where the café website is open.

 

Verify that the CloudFront distribution is now enabled.

Return to the CloudFront console.

In the left navigation pane, choose Distributions.

Verify that the distribution you created now has a Status of Enabled, as shown in the following image.

CloudFront distribution with Enabled status

⚠️ If the status is not Enabled yet, wait until it is before moving to the next step.

 

Test the CloudFront distribution.

Choose the link for the distribution ID.

Copy the Distribution domain name URL and open it in a new browser tab.

Note: The URL ends in .cloudfront.net.

The café website displays.

Try to load the website on a mobile device that is not connected to the same network as your computer. For example, the device is connected to the internet through a cellular connection and not the same WiFi network that your computer is connected to.

Notice that you can still access the site.

Tip: If you don't have a mobile device, an alternate way to test that the café website is available from another network is to use the VS Code IDE. In the terminal, run wget <distribution-domain-name> where <distribution-domain-name> is the distribution URL. If the HTTP request returns an HTTP status code of 200, then the site is available from the VS Code IDE, which runs on a different network than your computer.

 

Congratulations! You successfully created a CloudFront distribution. The website is running on a secure HTTPS connection, and you secured the site so that it is only available through CloudFront.

 

Task 3: Securing network access to the distribution using AWS WAF
In this task, you will configure the website so that it can only be accessed from a specific IP address range again. In the café scenario, this is the IP address range that Sofía uses to connect to the internet.

Recall that the S3 bucket policy enforced this previously. Now that the website is configured to be accessed through CloudFront, Sofía needs to find an alternative way to implement this. She will use the AWS WAF service to create an access control list (ACL) to restrict access to the café website.

 

First, create an IP set for your IP address.

In the AWS Management Console, search for waf and choose WAF & Shield.

If the left navigation pane, choose switch to old was console.

In the left navigation pane, choose IP sets.

Choose Create IP set and configure:

IP set name: Enter office

Description: Enter office IP

Region: Choose Global (CloudFront).

IP addresses: Enter <ip-address>/32 where <ip-address> is your public IPv4 address, as identified by whatismyipaddress.com.

Note: Be sure to include the /32 at the end of the IP address.

Choose Create IP set.

 

Begin to create a web ACL.

In the left navigation pane, choose Web ACLs.

Choose Create web ACL.

In the Web ACL details section, configure:

Resource type: Choose CloudFront distributions.

Name: Enter cafe-website-office-only-during-dev

Description: Enter Allow access to the cafe website through CloudFront from the cafe office

CloudWatch metric name: Enter cafe-website-office-only-during-dev

In the Associated AWS resources section, configure:

Choose Add AWS resources.

Two distributions are displayed, Select the CloudFront distribution that you created.

Choose Add.

Select the CloudFront distribution again, and then choose Next.

 

Add a rule to the web ACL configuration to allow requests from the office IP set.

In the Rules section, choose Add rules, Add my own rules and rule groups.

Rule type: Choose IP set.

Name: Enter only_office_please

IP set: Choose the office IP set that you just created.

IP address to use as the originating address: Keep the default Source IP address setting.

Action: Choose Allow.

Choose Add rule.

 

Update the new web ACL rule to block any requests that don't match the rule.

In the Rules section, select the only_office_please rule.

In the Default web ACL action section, for Default action, choose Block.

Choose Next.

 

Set the rule priority, configure metrics, and create the web ACL.

Choose the only_office_please rule.

Choose Next.

Keep all of the default metrics settings, and choose Next again.

Review the settings, and at the bottom of the page, choose Create web ACL.

 

Confirm that the web ACL configuration has been applied to the CloudFront distribution.

Return to the CloudFront console.

In the left navigation pane, choose Distributions.

Note: The Last modified column might display Deploying for the distribution. The deployment will complete within about 5 minutes; however, you can proceed to the next step without waiting.

Choose the link for the distribution ID.

In the Security section, notice that the distribution now has an AWS WAF value.

 

Test the AWS WAF configuration that was applied to the CloudFront distribution.

Return to the browser tab where the café website is open, and refresh the browser page.

The website displays, because your computer's IP address is in the IP set that you specified when you configured the web ACL.

Tip: To open the café website again, navigate to the CloudFront console. Open the details page for the distribution and locate the Distribution domain name. Enter that URL into a new browser tab.

Next, try to load the website on a mobile device that is not connected to the same network as your computer. For example, the device is connected to the internet through a cellular connection and not the same WiFi network that your computer is connected to.

You cannot access the site through a different network now.

Tip: If you don't have a mobile device, an alternate way to test is to use the VS Code IDE. In the terminal, run wget <distribution-domain-name> where <distribution-domain-name> is the distribution URL. If the HTTP request returns an HTTP status code of 403, then the site is not available from the VS Code IDE, which runs on a different network than your computer.

Congratulations! You have blocked direct access to the website through Amazon S3, configured a global CDN, and also secured the website to prevent anyone who isn't using your IP address from viewing the café website during this development phase.

Analysis: At this point, because your CloudFront distribution URL has an obscure value, someone would need to both guess the URL and use your IP address to access the website. Doing this would be difficult for anyone other than yourself. However, to truly secure the site, you should configure a login system. In a later lab in this course, you will use the Amazon Cognito service to implement authentication and to secure parts of the website.

 

Task 4: Securing a REST API endpoint using AWS WAF
The café website is now configured so that it can only be viewed from the café office network (your IP address). However, the REST API URLs that the website's AJAX use are not yet secured and could be invoked from anywhere on the internet.

In this task, you will secure access to one of the REST API endpoints.

 

Create a regional AWS WAF IP set.

Return to the WAF & Shield console.

In the left navigation pane, choose IP sets.

Choose Create IP set and configure:

IP set name: Enter office_regional

Description: Enter IP of the office for API Gateway

Region: Choose US East (N. Virginia).

IP addresses: Enter <ip-address>/32 where <ip-address> is your public IPv4 address, as identified by whatismyipaddress.com.

Note: Be sure to include the /32 at the end of the IP address.

Choose Create IP set.

 

Begin to create a regional web ACL.

In the left navigation pane, choose Web ACLs.

Choose Create web ACL.

In the Web ACL details section, configure:

Resource type: Choose Regional resources.

Region: Choose US East (N. Virginia).

Name: Enter website-api-gw-office-only-during-dev

Description: Enter To allow us to access the API GW calls used by the website from the office

CloudWatch metric name: Enter website-api-gw-office-only-during-dev

In the Associated AWS resources section, configure:

Choose Add AWS resources.

For Resource type, select Amazon API Gateway.

Select the ProductsApi - prod API Gateway resource.

Choose Add.

Select the ProductsApi - prod resource again, and then choose Next.

 

Add a rule to the web ACL configuration to allow requests from API Gateway.

In the Rules section, choose Add rules, Add my own rules and rule groups.

Rule type: Choose IP set.

Name: Enter ip_for_apigw

IP set: Choose the office_regional IP set that you just created.

IP address to use as the originating address: Keep the default Source IP address setting.

Action: Choose Allow.

Choose Add rule.

 

Update the new web ACL rule to block any requests that don't match the rule.

In the Rules section, select the ip_for_apigw rule.

In the Default web ACL action section, for Default action, choose Block.

Choose Next.

 

Set the rule priority, configure metrics, and create the web ACL.

Choose the ip_for_apigw rule.

Choose Next.

Keep all of the default metrics settings, and choose Next again.

Review the settings, and at the bottom of the page, choose Create web ACL.

 

When the web ACL creation process is complete, check the resources associated with the ACL.

Choose the link for the website-api-gw-office-only-during-dev ACL, which you just created.

Choose the Associated AWS resources tab.

Confirm that the ProductsApi - prod resource is listed. If it isn't, add it:

Choose Add AWS resources.

Choose the ProductsApi - prod resource.

Choose Add.

 

Test the new ACL from your computer.

In a new browser tab, go to the API Gateway console.

Choose the link for the ProductsApi.

In the left navigation pane, choose Stages.

In the Stages navigation pane, expand the prod stage.

Under /bean_products, choose GET.

Copy the Invoke URL, which has the format https://.execute-api.us-east-1.amazonaws.com/prod/bean_products, and load the URL in a new browser tab.

A JSON-formatted document with product information displays. This is the expected behavior.

 

Test the new ACL from another network.

On the browser tab on your computer where you just opened the invoke URL, open the context menu (right-click) for the page and choose Create QR Code for this page as shown in the following image.

Context menu with Create QR code for this Page selected

Tip: These instructions are for the Google Chrome browser. Other browsers might not provide this feature. If this feature is not available, see Alternative steps.

A pop-up window displays a QR code as shown in the following image. Keep the window open and continue to the next step.

QR code pop-up window

 

Verify that your mobile device is not connected to the same network as your computer.

On your mobile device, use the camera app or a QR Code reader app to scan the QR Code on your computer.

The app prompts you to load the link.

The page displays {"message": "Forbidden"}. This is the expected behavior.

 Alternative steps: If you don't have a mobile device or cannot create a QR code from your browser, an alternate way to test is to use the VS Code IDE. In the terminal, run wget <invoke-URL> where <invoke-URL> is the Invoke URL for GET for the /bean_products API. It should return a 403 Forbidden response message.


Congratulations! The AJAX URI that the café website uses is now also secured so that it can only be invoked from the café network (your computer). In a later lab, you will secure access to the coffee suppliers web application.

Analysis: To use AWS WAF to make the suppliers application available only from the café's office IP address, Sofía would need to use an Application Load Balancer. To use a load balancer, she would need to upgrade the Elastic Beanstalk application. However, because the suppliers website is not meant for public access, even when the website moves to production, this method would not be sufficient to try to secure the website. Sofía decides to leave the suppliers website configuration as it is for now. In a later lab, she will implement authentication to properly secure that part of the site.


How the café plans to use a CloudFront function
Note: This section explains how the café will use a CloudFront function. You don't have any steps to complete until you get to the next task.

Frank is pleased that the café website has been secured and cannot be accessed outside of the café's office network during this development phase. However, it seems that an effective cloud developer's work is never done because Frank has one more request.

He can't decide which promotional image to use on the homepage. He likes the apple pie image, but he also likes the pictures of his homemade pastries. He has asked Sofía (you) if it's possible to randomly display an image from a collection when the site is loaded.

Sofía first considered using JavaScript code on the client side to randomize the image. However, she chatted with Faythe, the AWS developer who often comes into the café to get a morning coffee. Faythe mentioned that Sofía could use the CloudFront Functions feature to achieve the same result.

Sofía could configure a CloudFront function to be invoked each time a request comes into (or out of) CloudFront. Therefore, she could manage the randomize logic at the edge rather than bloating the website with randomizing code logic.

To invoke the function, Sofía can add code such as the following to the website:


  function changeImage(){
    var pastry_name_str = "apple_pie";

    if(document.cookie !== "" && document.cookie.split('=')[1] !== ""){
      pastry_name_str = document.cookie.split("=")[1];
    }
    $("[data-role2='special_highlight']")
        .css({
          "background-image": "url(/images/items/" + pastry_name_str + ".png)"
        });
  }
This code checks for the existence of a cookie, which CloudFront Functions will add. If the cookie exists, the website will dynamically swap the image to display.

The CloudFront Functions code has already been written and made available for you in the resources/website/scripts.main.js file, so you don't need to update the website code in this lab. However, you will need to send a special cookie to the CloudFront distribution. The cookie will reference an image that can be used to override the default image on the website. If the cookie isn't found, the website will display the apple pie image.

 

Task 5: Configuring a CloudFront function on the website
In this final task, you will create a new CloudFront function. You will add code to the function to run each time that the café website is loaded. You will then test the website to verify that the desired result has been achieved.

 

Create a CloudFront function.

Navigate to the CloudFront console.

In the left navigation pane, choose Functions.

Choose Create function.

For Name, enter random_image_header

Choose Create function.

In the Function code section, replace the existing code with the following code:


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
In the code you pasted, replace the distro_str value of dp880v3pwdoto on line 15, with your unique distribution string value.

Tip: To find this value, if you have the café website open in your browser, copy the portion of the site's URL between https:// and .cloudfront.net. An alternative is to look up the value in the CloudFront console.

To apply the update, choose Save changes.

Analyze the function code. Notice that it generates a response cookie that contains a value from the pastry_name_array.

 

Test the function.

Choose the Test tab.

For Event Type, choose Viewer Response.

Keep the other default settings, and at the bottom of the page, choose Test function.

A results area appears at the bottom of the page. Confirm that the Status is 200 OK. The output should show that a single random item from the pastry_name_array was returned in the cookie.

Note: No log results are expected.

 

Publish the CloudFront function, and associate it with the CloudFront distribution.

Choose the Publish tab.

Choose Publish function.

A message at the top of the page indicates that the random_image_header function was successfully published.

In the Associated distributions section, choose Add association and configure:

Distribution: Choose the distribution.

Event type: Choose Viewer Response.

Cache behavior: Select Default (*).

Choose Add association.

In the left navigation pane, choose Distributions.  

Notice that the distribution is being deployed again.

 

Test the functionality on the café website.

Return to the café website browser tab, and refresh the page a few times.

Each time you refresh, the graphic that appears to the right of the cup of coffee should change.

Congratulations! You have successfully implemented a CloudFront function on the website.
    

 

Task 6: Adjusting the cache duration
Recall from earlier in the lab that all objects in the website S3 bucket have a metadata key-value for Cache-Control with the value set to max-age=0. In addition, recall that when you configured the CloudFront distribution, you chose to use the legacy cache settings and let the origin cache headers determine the object caching behavior. You also configured the CloudFront distribution with a path pattern of *, which means that the distribution will forward all object requests to the origin (the S3 bucket).

During development, these configurations helped you to immediately notice the effect of any changes made. However, now that the distribution has been tested and found to be stable, Sofía has decided to adjust the caching settings.

 

Confirm the cache settings that are in place on the café website.

Return to the café website browser tab.

Open the context menu (right-click) on the page and choose Inspect (if using Chrome) or Inspect Element (if using Firefox).

In the developer tools area that appears, choose the Network tab.

Next, refresh the café website by using the browser's refresh icon.

A list of all the files and accessed locations displays in the developer tools area.

At the top of the file list, choose the CloudFront distribution URL (the URL ends in cloudfront.net).

Note: Depending on your browser, you might need to choose All to see a cloudfront.net URL entry.

Analyze the Response Headers information.

Notice the header cache-control: max-age=0.

Also notice the header x-cache: RefreshHit from cloudfront. (In Firefox, it says Miss from cloudfront.) This means that a matching cache key wasn't found in the cache.

The following image shows the Response Headers area in the browser developer tools.

Response Headers area in developer tools


Sofía has a functional CloudFront distribution, but the configuration isn't taking advantage of the caching features. She could remove the Cache-Control metadata from all of the S3 objects and then update the behavior settings in the CloudFront distribution to use the CloudFront CachingOptimized managed policy. That would apply a default time to live (TTL) of 86,400 seconds (24 hours) to the requested objects. However, that cache setting would be too long for testing purposes.

Sofía decides to begin by applying a caching file expiration time of 3 minutes for testing purposes. She decides to make this change by updating the origin response headers. In this case, the origin is the S3 bucket, and the response headers are configured by updating the Cache-Control key-value pairs set on the Amazon S3 objects. After Sofía finishes testing, she can remove the Cache-Control metadata from the objects in the S3 bucket and use the CloudFront cache settings to control the cache file expiration behavior.

You need to use AWS CLI for this.

Edit the Cache-Control header set on each object in the S3 bucket.

Go to the VS Code IDE bash terminal and run the following command:


BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 's3bucket')].Name" --output text)
echo $BUCKET_NAME
aws s3 ls s3://$BUCKET_NAME/ | awk '{print $4}' | xargs -I {} aws s3api copy-object \
    --bucket $BUCKET_NAME \
    --copy-source $BUCKET_NAME/{} \
    --key {} \
    --cache-control "max-age=180" \
    --metadata-directive REPLACE
This command updates cache-control setting for all objects in the bucket. Notice the multiple files getting updated and output similar to the following:


{
    "ServerSideEncryption": "AES256",
    "CopyObjectResult": {
        "ETag": "\"82e9c8cb72608751aee8077bc72df441\"",
        "LastModified": "2025-01-10T00:06:21+00:00"
    }
}
Navigate to the Amazon S3 console.

Choose the link for the bucket that has -s3bucket in the name.

Select hyperlink for any file to open its properties

Go to the Metadata section, you should see a Cache-Control property with a value max-age=180

 

 

Test the effects of updating the caching settings on the CloudFront origin (the S3 bucket).

Reload the café website.

In the developer tools area, notice that the new max-age setting of 180 seconds was applied to the cache.

Notice that x-cache now says Hit from cloudfront, as shown in the following image.

A hit indicates that the cache key matches the request, and the object was served from the CloudFront edge cache.

Cache-control: max-age=180 header

 

Wait 3 minutes, and then test again.

Reload the café website.

Notice that x-cache now says RefreshHit from cloudfront, as shown in the following image.

A refresh hit means the objects were in the edge cache, but the cached objects were expired. Therefore, CloudFront had to get a new copy from the origin.

x-cache header after 3 minutes

Refresh the webpage a few times to observe how it behaves.

Also notice that the image at the top right of the page still changes on each page refresh, even though the page is fully cached.

 

Update from the café
Sofía shows the site to Frank, and he is very pleased! The site will load faster, because CloudFront uses edge locations and can cache web content. By using AWS WAF features, she has updated the site so that it is only available on the café office network during this development phase. She has also learned to modify how long website files are cached. Finally, she used the CloudFront Functions feature to rotate which dessert is highlighted on the website. Not bad for a day's work!

 

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

 

 

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This work may not be reproduced or redistributed, in whole or in part, without prior written permission from Amazon Web Services, Inc. Commercial copying, lending, or selling is prohibited.