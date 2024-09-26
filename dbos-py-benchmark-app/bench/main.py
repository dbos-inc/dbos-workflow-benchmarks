import time
from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import insert

from dbos import DBOS

from .schema import dbos_hello

app = FastAPI()
DBOS(fastapi=app)

# Bare handler
@app.get("/bare/{num}")
def readme(num: int):
    start = time.time()
    output = f"hello world {num}!"
    duration = (time.time() - start) * 1000
    return {"output": output, "runtime": duration}


# Sync transaction
@DBOS.transaction()
def bench_transaction(name: str) -> str:
    query = (
        insert(dbos_hello)
        .values(name="dbos", greet_count=1)
        .on_conflict_do_update(
            index_elements=["name"], set_={"greet_count": dbos_hello.c.greet_count + 1}
        )
        .returning(dbos_hello.c.greet_count)
    )
    greet_count = DBOS.sql_session.execute(query).scalar_one()
    greeting = f"Greetings, {name}! You have been greeted {greet_count} times."
    DBOS.logger.info(greeting)
    return greeting

# Sync workflow
@DBOS.workflow()
def bench_workflow(num: int) -> str:
    output = ""
    for i in range(num):
        output = bench_transaction(f"dbos-{i}")
    return output

# sync transaction handler
@app.get("/txn/{num}")
def handler_transaction(num: int):
    start = time.time()
    output = bench_transaction(f"dbos-{num}")
    duration = (time.time() - start) * 1000
    return {"output": output, "runtime": duration}

# sync workflow handler
@app.get("/wf/{num}")
def handler_workflow(num: int):
    start = time.time()
    output = bench_workflow(int(num))
    duration = (time.time() - start) * 1000
    return {"output": output, "runtime": duration}


# async transaction
@DBOS.transaction()
async def async_bench_transaction(name: str) -> str:
    query = (
        insert(dbos_hello)
        .values(name="dbos", greet_count=1)
        .on_conflict_do_update(
            index_elements=["name"], set_={"greet_count": dbos_hello.c.greet_count + 1}
        )
        .returning(dbos_hello.c.greet_count)
    )
    greet_count = (await DBOS.async_sql_session.execute(query)).scalar_one()
    greeting = f"Greetings, {name}! You have been greeted {greet_count} times."
    DBOS.logger.info(greeting)
    return greeting

# async workflow
@DBOS.workflow()
async def async_bench_workflow(num: int) -> str:
    output = ""
    for i in range(num):
        output = await async_bench_transaction(f"dbos-{i}")
    return output

# async transaction handler
@app.get("/asynctxn/{num}")
async def async_handler_transaction(num: int):
    start = time.time()
    output = await async_bench_transaction(f"dbos-{num}")
    duration = (time.time() - start) * 1000
    return {"output": output, "runtime": duration}

# async workflow handler
@app.get("/asyncwf/{num}")
async def async_handler_workflow(num: int):
    start = time.time()
    output = await async_bench_workflow(int(num))
    duration = (time.time() - start) * 1000
    return {"output": output, "runtime": duration}
