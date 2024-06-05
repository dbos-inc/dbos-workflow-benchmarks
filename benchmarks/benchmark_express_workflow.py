import boto3
import json
import time
from datetime import datetime

# Initialize the Step Functions client
client = boto3.client('stepfunctions', region_name='us-east-1')

# Function to start the express workflow and get latency
def start_sync_workflow(state_machine_arn, input_data, execution_name_prefix):
    response = client.start_sync_execution(
        stateMachineArn=state_machine_arn,
        name=f'{execution_name_prefix}-{int(time.time() * 1000)}',
        input=json.dumps(input_data)
    )
    start_date = response['startDate']
    stop_date = response['stopDate']
    latency_ms = (stop_date - start_date).total_seconds() * 1000 
    return latency_ms, response

# Parameters
state_machine_arn = 'arn:aws:states:us-east-1:500883621673:stateMachine:BenchmarkExpressWorkflow'
input_data = {"key": "value"}  # Example input data
execution_name_prefix = 'ExecutionTest'
num_executions = 1000

# Run the express workflow 1000 times and report latencies
latencies = []

for i in range(num_executions):
    latency_ms, response = start_sync_workflow(state_machine_arn, input_data, execution_name_prefix)
    latencies.append(latency_ms)
    print(f'Execution {i+1} latency: {latency_ms:.2f} milliseconds')

print("\nSummary of Latencies:")
print(f'Average Latency: {sum(latencies)/len(latencies):.2f} milliseconds')
print(f'Max Latency: {max(latencies):.2f} milliseconds')
print(f'Min Latency: {min(latencies):.2f} milliseconds')
