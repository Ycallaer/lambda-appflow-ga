# lambda-appflow-ga
Lambda function in python to transform AWS Appflow Google Analytics data to tabular data.

## Description
This lambda is to be used in combination with Appflow for google analytics.
The lambda will trigger every time a file is written to S3 and will convert the RAW JSON to a table
structure that can be written to Postgresql.
Only google analytics has been tested, test compatibility with others if needed.

This solution is part of a larger blog on medium, check the complete story there (`https://medium.com/@yvescallaert`)


## Requirements
You will need the following to contribute to this project
* Python 3.7
* Pip install of requirements.txt
* Pip install boto3

## Deploying
A deployment to AWS can be done using the following command from the root of the directory
`./packager.sh -n test_appflow -z test_appflow -p webanalytics -r eu-central-1`

Note that the script will look for an IAM role called `lambda-cli-role`, if this role is not present you will need to
create it. The role should contain the following policies:
* AWSLambdaBasicExecutionRole
* AWSLambdaVPCAccessExecutionRole
* SecretsManagerReadWrite (optional if you don't want to store your secrets in AWS Secrets Manager)
* Custom Policy that gives full access to the S3 destionation folder used in AppFlow

## Note
Please note that this script has been tested with a max of 2 metrics and 5 dimensions. The total result during testing
was never bigger than 2K records. If your use case is over 2K records you might need to alter parts of this script.