# Build a serverless store finder site using Amazon Location Service

This solution demonstrates how Amazon Location Service's Maps, Places and Routing APIs can be used to implement a simple "store finder" web page which lists the physical stores that are most accessible to the customer, along with pertinent store information such as opening hours and postal address.

The solution will outline two approaches: the first pattern is designed for an example business with less than 20 stores distributed across a geographic area the size of the United Kingdom (UK). The second approach is targeted at a business with greater than 20 locations distributed across a geographic area the size of the United States (US).

## AWS Blog post

The AWS blog post explaining how this solution works, and how to deploy the AWS SAM templates.

https://aws.amazon.com/blogs/mobile/build-a-serverless-store-finder-site-using-amazon-location-service/

## Using your own data sets

### API Pattern 1

During the deployment of the SAM template for API 1, an AWS Lambda custom resource is invoked by the Amazon CloudFormation stack provisioning process. This `storefinder-datageneration` Lambda function loads store data from the `stores.json` file found in `sam/api-pattern1/storefinder-datageneration`.

If you would like to use your own data set, update this file before the SAM template deployment. The results of the load are displayed in both the `storeFinderDataGenerationResult` output of the CloudFormation stack, and the Amazon CloudWatch Logs log stream for the Lambda function.

### API Pattern 2

During the deployment of the SAM template for API 2, a Lambda custom resource is invoked by the Amazon CloudFormation stack provisioning process. This `storefinder-datageneration` Lambda function loads simulated store data using the [us-post-offices.csv](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/NUKCNA) file found in `sam/api-pattern2/storefinder-datageneration`.

The contents of this file can be editted, or the storefinder-datageneration Lambda function modified, if you want to load your own store data into the Amazon Aurora Serverless V2 table.
