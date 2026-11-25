#!/usr/bin/env bash
# Creates the DynamoDB table for the stock tracker (on-demand, partition key itemId).
# Run in AWS CloudShell or any shell where the AWS CLI is signed in to the lab account.
# Usage: ./scripts/create_table.sh            (uses the CLI's default region)
#        AWS_REGION=us-east-1 ./scripts/create_table.sh
set -euo pipefail

TABLE_NAME="${TABLE_NAME:-SmallBusinessItems}"

if aws dynamodb describe-table --table-name "$TABLE_NAME" >/dev/null 2>&1; then
  echo "Table $TABLE_NAME already exists, not creating it again."
else
  echo "Creating table $TABLE_NAME ..."
  aws dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=itemId,AttributeType=S \
    --key-schema AttributeName=itemId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    >/dev/null
  aws dynamodb wait table-exists --table-name "$TABLE_NAME"
fi

# Evidence: name, status (should be ACTIVE), key and billing mode. ARN left out: it contains the account ID.
aws dynamodb describe-table --table-name "$TABLE_NAME" \
  --query 'Table.{Name:TableName,Status:TableStatus,Key:KeySchema,Billing:BillingModeSummary.BillingMode}' \
  --output json
