# Increase customer visits to your physical stores using Amazon Location Service

This repository demonstrates how Amazon Location Service's Maps, Places and Routing APIs can be used to implement a simple "store finder" web page which lists the physical stores that are most accessible to the customer, along with pertinent store information such as opening hours, address, and services provided. 

There are two approaches being covered:

- **Pattern 1** The first pattern is designed for a business with a small number of stores. The solution consists of the Vue.js frontend, as well as Amazon Location Service, Amazon Cognito, AWS Lambda and Amazon API Gateway resources. The store information is stored in an Amazon DynamoDB table.
- **Pattern 2** The second pattern is targeted at a business with many hundreds or thousands of stores distributed across a large geographic area. The store information is stored in an Amazon Aurora Serverless (PostgreSQL) database.

//TODO: Link to blog post

## Getting started

### Prerequisites

- Both patterns are deployed using the [AWS Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/). Follow the [official documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) to install the latest release of the AWS Serverless Application Model Command Line Interface (AWS SAM CLI).
  - The AWS SAM CLI requires appropriate permissions to provision AWS resources. Ensure that [access key and secret access keys](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/prerequisites.html) have been created using AWS IAM, and that `aws configure` has been used to register them locally on your machine.
- The store finder frontend has been developed using [Vue.js 3.X](https://vuejs.org/). Follow the [Vite documentation](https://vitejs.dev/guide/) to install the prerequisites required to build and test your Vue.js application.
- All code and templates required by both patterns are stored in this aws-samples repository. Run `git clone REPLACE WITH REPO NAME` to download the files to your local machine.

### Store Finder - Core

The Core SAM template will deploy the core infrastructure required by the solution, including Amazon S3 bucket and Amazon CloudFront distribution for frontend hosting, and Amazon Location Service map, place index and route calculator resources. This template also provisions Amazon Cognito resources. 

1. Navigate to the root of the repository. Make a copy of the `.env.local.template` file and name it `env.local`. You will need to update this file following SAM deployments in the following steps.
2. Navigate to the `sam/core` directory on your local machine. Run `sam build` to build the application ready for deployment. 
3. Run `sam deploy --guided`. Confirm that the `Successfully created/updated stack` message is shown.
4. Populate Amazon Location Service and Amazon Cognito details in the `env.local` file.

### Store Finder - Pattern 1

1. Navigate to the `sam/api-pattern1` directory on your local machine. Run `sam build` to build the application ready for deployment.
2. Run `sam deploy --guided`. When prompted, provide the name of the Amazon CloudFormation stack of the core infrastructure. Confirm that the `Successfully created/updated stack` message is shown.
3. Populate the API details in the `env.local` file.

### Store Finder - Pattern 2

1. Navigate to the `sam/api-pattern2` directory on your local machine. Run `sam build` to build the application ready for deployment.
2. Run `sam deploy --guided`. When prompted, provide the name of the Amazon CloudFormation stack of the core infrastructure. Confirm that the `Successfully created/updated stack` message is shown.
3. Download, unzip and upload the `us-post-offices.csv` file to the Amazon S3 API2 data assets bucket. The `aws s3 cp` command can be used, e.g. `aws s3 cp us-post-offices.csv s3://<NAME OF API2 DATA ASSETS BUCKET FROM API2 CLOUDFORMATION OUTPUT>`.
4. Populate the API details in the `env.local` file.

### Build and deploy the Vue.js application

1. When all the missing details have been populated in the `env.local` file, run `npm build` in the root of the folder structure.
2. Copy the resulting files in the `/dist` folder to the Amazon S3 core hosting bucket. The `aws s3 cp` command can be used, e.g. `aws s3 cp . s3://<NAME OF CORE HOSTING BUCKET FROM CORE CLOUDFORMATION OUTPUT> --recursive`.
If you make changes to the env.local, rebuild, copy and invalidate cache.