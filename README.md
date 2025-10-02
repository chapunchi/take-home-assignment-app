# GIC Web Application

## Background
This assignment focuses on designing and implementing a cloud infrastructure for a banking application. The application provides support and efficient CRUD operations on a banking account.

The customer would be able to access the bank account operations via three endpoints,

* GET endpoint to get the current balance of an account.
* POST endpoint to deposit money to account.
* POST endpoint to withdraw money from an account.

## Implementation Overview
For this assignment, the infrastructure is provisioned via Terraform and deployed through Github pipeline. 

Likewise, the web application has been implemented and deployed via a different Github pipeline.

There are two Github workflows,
1.	[Infrastructure workflow](https://github.com/chapunchi/take-home-assignment-iac)
2.	[Web application workflow](https://github.com/chapunchi/take-home-assignment-app)

The setup was separated into two Github workflows to improve manageability and maintenance.

## Setup infrastructure
To setup infrastructure use this pipeline, [iac](https://github.com/chapunchi/take-home-assignment-iac)

The Github workflow of the above pipeline is used to provision infrastructure,
![Infrastructure](resources/workflow.png)

Once there is an update pushed to the repository pipeline will be triggered and Continuous Deployment will provision the resources to the cloud environment.

If developer want to make any changes he/she should perform changes to the modules as depicted below,
![Modules](resources/modules.png)

## Deploy web application
To deploy the web application push the changes to the repo, [webapp](https://github.com/chapunchi/take-home-assignment-app)

Before deploying the web application it is always recommended for the developer to run the test cases mentioned in,
```
* tests/unit_tests
* tests/integration_tests
```

Developer can execute the test cases using the following commands in terminal,
```bash
pytest tests/unit_tests/
pytest tests/integration_tests/
```

Once all the test cases are successful same as in iac, push the changes to the repo, [webapp](https://github.com/chapunchi/take-home-assignment-app)

This change will trigger a Continuous Deployment and will update the ECS cluster.

## Verify Installation
Once the CI/CD pipeline succeeds as depicted below,
![pipeline_success](resources/pipeline_success.png)
 
login to the AWS management portal,
1. Click on ECS 
2. Go to Clusters 
3. Select, 
```
web-cluster
```
![web-cluster](resources/web-cluster.png)
4. Select 
```
web-service
```
![web-service](resources/web-svc.png)
5. Click on Events
![events](resources/events.png)
6. Check if,
deployment completed or reached a steady state.
![healthy](resources/healthy.png)

Furthermore to check if application is healthy,
1. Go to Cloudwatch
2. Click on Log groups
3. Click on,
```
/ecs/web-task
```
![web-task](resources/webtask.png)

4. Click on the latest log stream
![log-stream](resources/log-stream.png)
5. Check if you have a 200 http response
![200-response](resources/200-res.png)

If you have a 200 response the web application is working as expected.

## Test Application

First configure AWS credentials in terminal,
```bash
export AWS_ACCESS_KEY_ID=AKIATJAWX6WOP5KJ6FHU
export AWS_SECRET_ACCESS_KEY=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
export AWS_DEFAULT_REGION=ap-southeast-1
```

To test application you can open a terminal and input below parameters,
1. Get the balance from the bank account,
```bash
curl -u dev:68h@Dp^#9rdu http://web-alb-1183205142.ap-southeast-1.elb.amazonaws.com/balance/12345
```

2. Deposit money to the account,
```bash
curl -X POST \
  -u dev:68h@Dp^#9rdu \
  -H "Content-Type: application/json" \
  -d '{"account_id": "12345", "amount": 334.14}' \
  http://web-alb-1183205142.ap-southeast-1.elb.amazonaws.com/deposit
```

3. Withdraw money from account,
```bash
curl -X POST \
  -u dev:68h@Dp^#9rdu \
  -H "Content-Type: application/json" \
  -d '{"account_id": "12345", "amount": 11.67}' \
  http://web-alb-1183205142.ap-southeast-1.elb.amazonaws.com/withdraw
```

## Monitoring
* Security Hub
![security hub](resources/sec-hub.png)
As mentioned earlier cannot deploy fix in github runner as it is not managed by us.

* CloudTrail
![cloudtrail](resources/cloudtrail.png)

* AWS Config
![config](resources/config.png)

* Cloudwatch
![cloudwatch](resources/cloudwatch.png)

* GuardDuty
![guardduty](resources/guardduty.png)
As mentioned earlier cannot deploy fix in github runner as it is not managed by us.

* Inspector
![inspector](resources/inspector.png)
As mentioned earlier cannot deploy fix in github runner as it is not managed by us.

* VPC Flow Logs
![vpc-flow-logs](resources/flow-logs.png)

* ECS
![container-insights-1](resources/container-1.png)
![container-insights-2](resources/container-2.png)
![ecs-metrics](resources/ecs.png)

## Accessing the Cloud Environment
```bash
Console login: https://chapunchi.signin.aws.amazon.com/console
user name: dev-readonly
Password: lLqz6/@7{u3^
```

Change the region to ***ap-southeast-1***

All the resources are deployed in ***ap-southeast-1*** region.


## Tasks during the interview
1. Deposit to get the daily_amount_withdrawn and daily_limit 
![deposit_acc](resources/deposit_acc.png)

2. First daily withdrawal
Now the daily_amount_withdrawn = 100
daily_limit = 500

we are going to withdraw = 100
![daily_first_withdrawal](resources/daily_first_withdrawal.png) 

3. Second daily withdrawal
Now daily_amount_withdrawn = 500
daily_limit = 500

![limit_exceeded](resources/daily_limit_exceeded.png) 

Giving the error Daily Limit exceeded