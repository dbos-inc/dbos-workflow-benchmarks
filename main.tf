provider "aws" {
  region = "us-east-1"
}

####################################
### Lambda IAM Roles
####################################

# IAM role for the Lambdas
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Effect = "Allow",
      Sid    = "",
    }],
  })
}

# Give the Lambdas permission to write logs
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Give the Lambdas permission to manage Step Functions
resource "aws_iam_role_policy_attachment" "lambda_sfn_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}

####################################
### Step Functions IAM Roles
####################################

# IAM role for the Step Functions
resource "aws_iam_role" "sfn_exec_role" {
  name = "sfn_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = {
        Service = "states.amazonaws.com"
      },
      Effect = "Allow",
      Sid    = "",
    }],
  })
}

# Give the Step Functions permission to invoke Lambdas
resource "aws_iam_role_policy" "sfn_exec_policy" {
  role = aws_iam_role.sfn_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "lambda:InvokeFunction"
        ],
        Effect = "Allow",
        Resource = [
          aws_lambda_function.lambda_transaction.arn
        ]
      }
    ]
  })
}

####################################
### Lambda
####################################

# A Lambda function that performs a database transaction
resource "aws_lambda_function" "lambda_transaction" {
  function_name = "LambdaTransaction"
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  filename      = "lambda/lambda_transaction.zip"
  role          = aws_iam_role.lambda_exec_role.arn
  memory_size   = 512
}

# A Lambda function that executes the standard workflow and returns its execution duration
resource "aws_lambda_function" "sfn_executor" {
  function_name = "SfnExecutor"
  handler       = "sfn_executor.handler"
  runtime       = "nodejs20.x"
  filename      = "lambda/sfn_executor.zip"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 15
}

####################################
### Step Functions
####################################

# A Step Functions standard workflow that calls LambdaTransaction steps times
resource "aws_sfn_state_machine" "lambda_transaction_standard_workflow" {
  name     = "BenchmarkStandardWorkflow"
  role_arn = aws_iam_role.sfn_exec_role.arn

  definition = jsonencode({
    Comment : "A Step Functions state machine that calls Lambda steps times",
    StartAt : "Initialize",
    States : {
      Initialize : {
        Type : "Pass",
        Parameters : {
          "currentIndex" : 0,
          "totalSteps.$" : "$.steps"
        },
        ResultPath : "$.iterator",
        Next : "Loop"
      },
      Loop : {
        Type : "Choice",
        Choices : [
          {
            Variable : "$.iterator.currentIndex",
            NumericLessThanPath : "$.iterator.totalSteps",
            Next : "CallLambda"
          }
        ],
        Default : "Done"
      },
      CallLambda : {
        Type : "Task",
        Resource : aws_lambda_function.lambda_transaction.arn,
        Parameters : {
          "hostname.$" : "$.hostname",
          "username.$" : "$.username",
          "password.$" : "$.password"
        },
        ResultPath : "$.lambdaResult",
        Next : "IncrementIndex"
      },
      IncrementIndex : {
        Type : "Pass",
        Parameters : {
          "currentIndex.$" : "States.MathAdd($.iterator.currentIndex, 1)",
          "totalSteps.$" : "$.iterator.totalSteps"
        },
        ResultPath : "$.iterator",
        Next : "Loop"
      },
      Done : {
        Type : "Succeed"
      }
    }
  })
}

# A Step Functions express workflow that calls LambdaTransaction steps times
resource "aws_sfn_state_machine" "lambda_transaction_express_workflow" {
  name     = "BenchmarkExpressWorkflow"
  role_arn = aws_iam_role.sfn_exec_role.arn

  definition = aws_sfn_state_machine.lambda_transaction_standard_workflow.definition

  type = "EXPRESS"
}

####################################
### Outputs
####################################

output "express_workflow_arn" {
  value = aws_sfn_state_machine.lambda_transaction_express_workflow.arn
}

output "sfn_executor_arn" {
  value = aws_lambda_function.sfn_executor.arn
}
