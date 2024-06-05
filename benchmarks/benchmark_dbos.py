import requests
import json
import argparse
import statistics
import numpy as np

# Function to send GET request and get latency
def get_request_latency(session, url, num_invocations):
    response = session.get(f"{url}/{num_invocations}")
    response_json = response.json()
    return response_json.get('runtime')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Measure DBOS server-side latency')
    parser.add_argument('-u', '--url', required=True, help='The DBOS application URL')
    parser.add_argument('-n', '--num-executions', required=True, type=int, help='The number of executions to benchmark')
    parser.add_argument('-i', '--num-invocations', required=True, type=int, help='The number of times the workflow should invoke the transaction')

    args = parser.parse_args()

    # Parameters
    url = args.url
    num_executions = args.num_executions
    num_invocations = args.num_invocations

    # Send GET request specified number of times and report latencies
    latencies = []
    with requests.Session() as session:
        for i in range(num_executions):
            latency_ms = get_request_latency(session, url, num_invocations)
            latencies.append(latency_ms)
            print(f'Execution {i+1} latency: {latency_ms:.2f} milliseconds')

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
