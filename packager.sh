#!/usr/bin/env bash
set -x

pFlag=0
rFlag=0
nFlag=0
zFlag=0

CreateZipFile(){
cd package
zip -r9 ../${ZIP_NAME}.zip .
cd ../
zip -g ${ZIP_NAME}.zip appflow_ga.py
}


UsageMessage(){
echo "usage : packager -p <aws profile> -r <aws_region> -n <name of the function> -z <zipname> -h <dbhost> -i <GOOGLE_SPREADSHEET_ID> -t <GOOGLE_SPREADSHEET_TAB_PAGE> -d <DB_TEMP_TABLE>"
}

while getopts "p:r:n:z:" option
do
case ${option} in
  "p" ) AWS_PROFILE=${OPTARG}
        pFlag=1
        ;;
  "r" ) AWS_REGION=${OPTARG}
        rFlag=1
        ;;
  "n" ) FUNCTION_NAME=${OPTARG}
        nFlag=1
        ;;
  "z" ) ZIP_NAME=${OPTARG}
        zFlag=1
        ;;
  \?  ) UsageMessage
        exit 4
        ;;
esac
done


if [ ${pFlag} -eq 0 ] || [ ${rFlag} -eq 0 ] || [ ${nFlag} -eq 0 ] || [ ${zFlag} -eq 0 ]; then
    UsageMessage
    exit 4
fi

CreateZipFile



function_name_cli=`aws lambda get-function --function-name ${FUNCTION_NAME} --profile ${AWS_PROFILE} --region=${AWS_REGION} | jq -r '.Configuration | .FunctionName'`

if [ ${function_name_cli} == ${FUNCTION_NAME} ]; then
  echo "Found the function. Ready to update."
  aws lambda update-function-code --function-name ${FUNCTION_NAME} --zip-file fileb://${ZIP_NAME}.zip --profile ${AWS_PROFILE} --region=${AWS_REGION}
  aws lambda update-function-configuration --function-name ${FUNCTION_NAME} --profile ${AWS_PROFILE} --region=${AWS_REGION}

else
  echo "Unable to find the function. We will create the function for you."

  ACCOUNTID=`aws sts get-caller-identity --region=${AWS_REGION} --profile=${AWS_PROFILE} | jq -r '.Account'`
  ROLEARN=`aws iam get-role --role-name lambda-cli-role --region=${AWS_REGION} --profile=${AWS_PROFILE} | jq -r '.Role | .Arn'`

  if [ -z ${ROLEARN} ]; then
    echo "The lambda role does not exist. Please ask your admin to create the role with the AWSLambdaBasicExecutionRole policy."
  else
    aws lambda create-function --function-name ${FUNCTION_NAME} --zip-file fileb://${ZIP_NAME}.zip --handler appflow_ga.lambda_handler --runtime python3.7 --role arn:aws:iam::${ACCOUNTID}:role/lambda-cli-role --profile ${AWS_PROFILE} --region=${AWS_REGION}
    aws lambda update-function-configuration --function-name ${FUNCTION_NAME} --profile ${AWS_PROFILE} --region=${AWS_REGION}

  fi
fi
