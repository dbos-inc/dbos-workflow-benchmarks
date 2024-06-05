import boto3
import json
import time
import argparse
import statistics

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

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Run Step Functions express workflow and measure latencies.')
    parser.add_argument('--hostname', required=True, help='The hostname of the database')
    parser.add_argument('--username', required=True, help='The username for the database')
    parser.add_argument('--password', required=True, help='The password for the database')

    args = parser.parse_args()

    # Parameters
    state_machine_arn = 'arn:aws:states:us-east-1:500883621673:stateMachine:BenchmarkExpressWorkflow'
    execution_name_prefix = 'ExecutionTest'
    num_executions = 1000
    input_data = {
        "hostname": args.hostname,
        "username": args.username,
        "password": args.password
    }

    # Run the express workflow 1000 times and report latencies
    latencies = []
    for i in range(num_executions):
        latency_ms, response = start_sync_workflow(state_machine_arn, input_data, execution_name_prefix)
        latencies.append(latency_ms)
        print(f'Execution {i+1} latency: {latency_ms:.2f} milliseconds')

    # Compute summary statistics
    average_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    median_latency = statistics.median(latencies)

    print("\nSummary of Latencies:")
    print(f'Average Latency: {average_latency:.2f} milliseconds')
    print(f'Max Latency: {max_latency:.2f} milliseconds')
    print(f'Min Latency: {min_latency:.2f} milliseconds')
    print(f'Median Latency: {median_latency:.2f} milliseconds')
