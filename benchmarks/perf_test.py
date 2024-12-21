import time
import asyncio
import aiohttp
import random
import traceback
import argparse
import sys
from aiohttp import TCPConnector

# Shared list to store latencies
latencies = []
latency_lock = asyncio.Lock()
errors = 0
errors_lock = asyncio.Lock()


async def send_request(session):
    global latencies
    global errors
    url = "https://devhawkgoogle-async-py-bench.cloud.dbos.dev/async-wf/10"
    start = time.time()
    try:
        async with session.get(url) as response:
            end = time.time()
            status = response.status
            bob = await response.text()
            # assert "runtime" in bob
            if status != 200:
                # print(f"Request failed with status {status}", file=sys.stderr)
                async with errors_lock:
                    errors += 1
            else:
                async with latency_lock:
                    latencies.append((end - start) * 1000)
    except Exception as e:
        async with errors_lock:
            errors += 1
        # print(f"Exception in request: {type(e).__name__}: {str(e)}", file=sys.stderr)
        # traceback.print_exc()


async def generate_load(rate, duration):
    print(
        f"Sending an average of {rate} RPS for {duration} seconds (approximately {rate * duration} requests)", file=sys.stderr
    )
    print(
        f"Sending an average of {rate} RPS for {duration} seconds (approximately {rate * duration} requests)"
    )
    end_time = time.time() + duration

    # Configure connection pooling
    connector = TCPConnector(
        limit=0,  # No limit on concurrent connections
        force_close=False,  # Keep connections alive
        enable_cleanup_closed=True,
        ttl_dns_cache=300,  # Cache DNS results
    )

    # Configure session with keepalive
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={"Connection": "keep-alive", "Keep-Alive": "timeout=300"},
    ) as session:
        tasks = set()  # Use set for faster removal of completed tasks

        try:
            while time.time() < end_time:
                # Clean up completed tasks
                tasks = {t for t in tasks if not t.done()}

                # Create new task
                task = asyncio.create_task(send_request(session))
                tasks.add(task)

                # Exponential interval based on the specified rate
                interval = random.expovariate(rate)
                await asyncio.sleep(interval)

            # Wait for remaining tasks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            # print(f"Error in generate_load: {e}", file=sys.stderr)
            # Cancel any remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to cancel
            await asyncio.gather(*tasks, return_exceptions=True)

class Record:
    def __init__(self, latencies: list, rate: int, duration: int, errors: int):
        self.rate = rate
        self.duration = duration
        self.errors = errors
        self.responses = len(latencies)
        self.throughput = self.responses / duration
        self.p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0
        self.p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0

async def run_load_test(minn, max_load, steps, step_duration):
    global latencies
    global errors

    records: list[Record] = []

    for load in range(minn, max_load + 1, steps):
        if load == 0: continue
        print("=================================================")
        latencies = []
        errors = 0

        await generate_load(load, step_duration)

        if latencies:
            latencies.sort()
            print(f"Responses received: {len(latencies)}")
            print(f"Throughput: {len(latencies) / step_duration:.2f} RPS")
            print(f"p50 Latency: {latencies[int(len(latencies) * 0.5)]:.2f}ms")
            print(f"p99 Latency: {latencies[int(len(latencies) * 0.99)]:.2f}ms")
        print(f"Errors: {errors}")

        record = Record(latencies, load, step_duration, errors)
        records.append(record)

    
    print("=================================================")
    print("rate, duration, requests,  responses, throughput, p50, p99, errors")
    for record in records:
        print(f"{record.rate}, {record.duration}, {record.rate * record.duration}, {record.responses}, {record.throughput:.2f}, {record.p50:.2f}, {record.p99:.2f}, {record.errors}")

def test_autoscaling(minn, max_rps, step_rps_increase, step_duration):
    async def run():
        await run_load_test(minn, max_rps, step_rps_increase, step_duration)

    asyncio.run(run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaling test configuration.")
    parser.add_argument(
        "--min-rps", type=int, default=0, help="Minimum requests per second to reach."
    )
    parser.add_argument(
        "--max-rps",
        type=int,
        default=3000,
        help="Maximum requests per second to reach.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="RPS increments for each load increase step",
    )
    parser.add_argument(
        "--step-duration", type=int, default=20, help="Step duration in seconds."
    )

    args = parser.parse_args()
    print(f"Max RPS: {args.max_rps}")
    print(f"Steps: {args.steps}")
    print(f"Step Duration: {args.step_duration} seconds")
    test_autoscaling(args.min_rps, args.max_rps, args.steps, args.step_duration)