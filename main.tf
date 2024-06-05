provider "aws" {
  region = "us-east-1"
}

####################################
### IAM Roles
####################################

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

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_sfn_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}

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

resource "aws_lambda_function" "lambda_transaction" {
  function_name = "LambdaTransaction"
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  filename      = "lambda/lambda_transaction.zip"
  role          = aws_iam_role.lambda_exec_role.arn
  memory_size   = 512
}


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

resource "aws_sfn_state_machine" "lambda_transaction_standard_workflow" {
  name     = "BenchmarkStandardWorkflow"
  role_arn = aws_iam_role.sfn_exec_role.arn

  definition = jsonencode({
    Comment = "A workflow that invokes LambdaTransaction multiple times",
    StartAt = "InvokeLambda1",
    States = {
      InvokeLambda1 = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = aws_lambda_function.lambda_transaction.arn,
          Payload = {
            "input.$" : "$"
          }
        },
        Next = "InvokeLambda2"
      },
      InvokeLambda2 = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = aws_lambda_function.lambda_transaction.arn,
          Payload = {
            "input.$" : "$"
          }
        },
        Next = "InvokeLambda3"
      }
      InvokeLambda3 = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = aws_lambda_function.lambda_transaction.arn,
          Payload = {
            "input.$" : "$"
          }
        },
        Next = "InvokeLambda4"
      }
      InvokeLambda4 = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = aws_lambda_function.lambda_transaction.arn,
          Payload = {
            "input.$" : "$"
          }
        },
        Next = "InvokeLambda5"
      }
      InvokeLambda5 = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = aws_lambda_function.lambda_transaction.arn,
          Payload = {
            "input.$" : "$"
          }
        },
        End = true
      }
    }
  })
}

resource "aws_sfn_state_machine" "lambda_transaction_express_workflow" {
  name     = "BenchmarkExpressWorkflow"
  role_arn = aws_iam_role.sfn_exec_role.arn

  definition = aws_sfn_state_machine.lambda_transaction_standard_workflow.definition

  type = "EXPRESS"
}

####################################
### API Gateway
####################################

resource "aws_api_gateway_rest_api" "lambda_api" {
  name = "LambdaBenchmarkingAPI"
}

resource "aws_api_gateway_resource" "lambda_gateway_resource" {
  rest_api_id = aws_api_gateway_rest_api.lambda_api.id
  parent_id   = aws_api_gateway_rest_api.lambda_api.root_resource_id
  path_part   = "hello-world"
}

resource "aws_api_gateway_method" "lambda_gateway_method" {
  rest_api_id   = aws_api_gateway_rest_api.lambda_api.id
  resource_id   = aws_api_gateway_resource.lambda_gateway_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.lambda_api.id
  resource_id = aws_api_gateway_resource.lambda_gateway_resource.id
  http_method = aws_api_gateway_method.lambda_gateway_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_transaction.invoke_arn
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_transaction.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.lambda_api.execution_arn}/*/*/hello-world"
}

resource "aws_api_gateway_deployment" "lambda_gateway_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.lambda_api.id
  stage_name  = "test"
}

####################################
### Output
####################################

output "invoke_url" {
  value = "${aws_api_gateway_deployment.lambda_gateway_deployment.invoke_url}/${aws_api_gateway_resource.lambda_gateway_resource.path_part}"
}
