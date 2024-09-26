from typing import cast
import requests
import json
import argparse
import statistics
import numpy as np
import pprint

# https://devhawkgoogle-dbos-py-benchmark-app.cloud.dbos.dev/
# https://devhawkgoogle-dbos-py-benchmark-app-async.cloud.dbos.dev/

# Function to send GET request and get latency
# def get_request_latency(session, url, num_invocations):
#     response = session.get(f"{url}/{num_invocations}")
#     response_json = response.json()
#     return response_json.get('runtime')

def benchmark_app(url: str, num_executions: int, async_handlers: bool = False):
    handlers = ["txn", "asynctxn", "wf", "asyncwf"] if async_handlers else ["txn", "wf"]

    endpoints: dict[str, list[int]] = {}
    for handler in handlers:
        print(f"Executing {handler}")
        responses: list[int] = []
        for i in range(num_executions+20):
            r = requests.get(f"{url}/{handler}/{i}")
            responses.append(cast(int, r.json().get('runtime')))
        endpoints[handler] = responses[10:-10]

    return endpoints


if __name__ == '__main__':
    # results = benchmark_app("https://devhawkgoogle-dbos-py-benchmark-app-async.cloud.dbos.dev/", 100, True)
    results = benchmark_app("https://devhawkgoogle-dbos-py-benchmark-app.cloud.dbos.dev/", 100, False)

    for handler, latencies in results.items():
        average_latency = (sum(latencies) / len(latencies))/1000000
        max_latency = max(latencies)/1000000
        min_latency = min(latencies)/1000000
        median_latency = statistics.median(latencies)/1000000
        p99_latency = np.percentile(latencies, 99)/1000000

        print(f"\nSummary of Latencies for {handler}:")
        print(f'  Average Latency: {average_latency:.2f} ms')
        print(f'  Max Latency: {max_latency:.2f} ms')
        print(f'  Min Latency: {min_latency:.2f} ms')
        print(f'  Median Latency: {median_latency:.2f} ms')
        print(f'  99th Percentile Latency: {p99_latency:.2f} ms')

