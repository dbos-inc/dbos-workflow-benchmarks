provider "aws" {
  region = "us-east-1"
}

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

resource "aws_lambda_function" "hello_world" {
  function_name = "HelloWorldFunction"
  handler       = "hello_world.handler"
  runtime       = "nodejs20.x"
  filename      = "lambda/hello_world.zip"

  role = aws_iam_role.lambda_exec_role.arn
}

resource "aws_api_gateway_rest_api" "example_api" {
  name = "ExampleAPI"
}

resource "aws_api_gateway_resource" "example_resource" {
  rest_api_id = aws_api_gateway_rest_api.example_api.id
  parent_id   = aws_api_gateway_rest_api.example_api.root_resource_id
  path_part   = "example-path"
}

resource "aws_api_gateway_method" "example_method" {
  rest_api_id   = aws_api_gateway_rest_api.example_api.id
  resource_id   = aws_api_gateway_resource.example_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.example_api.id
  resource_id = aws_api_gateway_resource.example_resource.id
  http_method = aws_api_gateway_method.example_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.hello_world.invoke_arn
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hello_world.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.example_api.execution_arn}/*/*/example-path"
}


resource "aws_api_gateway_deployment" "example_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.example_api.id
  stage_name  = "test"
}

output "invoke_url" {
  value = "${aws_api_gateway_deployment.example_deployment.invoke_url}/${aws_api_gateway_resource.example_resource.path_part}"
}