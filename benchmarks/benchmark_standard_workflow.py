import boto3
import json
import time
from datetime import datetime
import argparse
import statistics
import numpy as np

# Initialize the Lambda client
client = boto3.client('lambda', region_name='us-east-1')

# Function to invoke the Lambda function and get latency
def invoke_lambda(lambda_arn, input_data):
    response = client.invoke(
        FunctionName=lambda_arn,
        InvocationType='RequestResponse',
        Payload=json.dumps(input_data)
    )
    response_payload = json.loads(response['Payload'].read())
    body = json.loads(response_payload.get('body', '{}'))
    runtime_seconds = body.get('runtimeSeconds', 0)
    return runtime_seconds * 1000  # Convert to milliseconds

# Parse command line arguments
parser = argparse.ArgumentParser(description='Invoke Lambda function and measure latencies.')
parser.add_argument('--hostname', required=True, help='The hostname of the database')
parser.add_argument('--username', required=True, help='The username for the database')
parser.add_argument('--password', required=True, help='The password for the database')

args = parser.parse_args()

# Parameters
lambda_arn = 'arn:aws:lambda:us-east-1:500883621673:function:SfnExecutor'
num_invocations = 10

# Invoke the Lambda function 1000 times and report latencies
latencies = []

input_data = {
  "hostname": args.hostname,
  "username": args.username,
  "password": args.password
}

for i in range(num_invocations):
    latency_ms = invoke_lambda(lambda_arn, input_data)
    latencies.append(latency_ms)
    print(f'Invocation {i+1} latency: {latency_ms:.2f} milliseconds')

# Compute summary statistics
average_latency = sum(latencies) / len(latencies)
max_latency = max(latencies)
min_latency = min(latencies)
median_latency = statistics.median(latencies)
p99_latency = np.percentile(latencies, 99)

print("\nSummary of Latencies:")
print(f'Average Latency: {average_latency:.2f} milliseconds')
print(f'Max Latency: {max_latency:.2f} milliseconds')
print(f'Min Latency: {min_latency:.2f} milliseconds')
print(f'Median Latency: {median_latency:.2f} milliseconds')
print(f'99th Percentile Latency: {p99_latency:.2f} milliseconds')
