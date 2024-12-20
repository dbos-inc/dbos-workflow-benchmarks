from contextlib import contextmanager
import gc
import time
from typing import TypedDict
from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import insert
import requests
from dbos import DBOS
import uvicorn

from .schema import dbos_hello, useless_facts

app = FastAPI()
DBOS(fastapi=app)

class UselessFact(TypedDict):
    id: str
    text: str

# Bare handler
@app.get("/bare/{num}")
def readme(num: int):
    with disable_gc():
        start = time.perf_counter_ns()
        output = f"hello world {num}!"
        end = time.perf_counter_ns()
        elapsed = end - start
        return {"output": output, "runtime": elapsed}

# Sync transaction
@DBOS.transaction()
def save_fact(id: str, fact: str) -> int:
    query = (
        insert(useless_facts)
        .values(id=id, fact=fact, fact_count=1)
        .on_conflict_do_update(
            index_elements=["id"], set_={"fact_count": useless_facts.c.fact_count + 1}
        )
        .returning(useless_facts.c.fact_count)
    )
    fact_count:int = DBOS.sql_session.execute(query).scalar_one()
    DBOS.logger.info(f"Fact: {fact}; id: {id}; count: {fact_count}")
    return fact_count

useless_fact_url = "https://uselessfacts.jsph.pl/api/v2/facts/random"

@DBOS.step()
def retrieve_fact() -> UselessFact:
    response = requests.get(useless_fact_url)
    useless_fact = response.json()
    return {'id': useless_fact["id"], 'text': useless_fact["text"]}

# Sync workflow
@DBOS.workflow()
def bench_workflow(num: int) -> list:
    output = []
    for i in range(num):
        fact: UselessFact = retrieve_fact()
        count = save_fact(fact['id'], fact['text'])
        output.append({"id": fact['id'], "fact": fact['text'], "count": count})

    return output


@contextmanager
def disable_gc():
    gc_old = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if gc_old:
            gc.enable()

# sync transaction handler
@app.get("/step/{num}")
def handler_step(num: int):
    with disable_gc():
        start = time.perf_counter_ns()
        output = retrieve_fact()
        end = time.perf_counter_ns()
        elapsed = end - start
        return {"output": output, "runtime": elapsed}


@app.get("/wf/{num}")
def handler_workflow(num: int):
    with disable_gc():
        start = time.perf_counter_ns()
        output = bench_workflow(int(num))
        end = time.perf_counter_ns()
        elapsed = end - start
        return {"output": output, "runtime": elapsed}

