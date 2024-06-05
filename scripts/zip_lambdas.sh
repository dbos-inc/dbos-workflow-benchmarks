#!/bin/bash
set -ex

SCRIPT_DIR=$(dirname "$(realpath "$0")")
cd "$SCRIPT_DIR/../lambda"

rm *.zip
zip -j sfn_executor.zip sfn_executor.js
cd lambda_transaction
zip -r ../lambda_transaction.zip .