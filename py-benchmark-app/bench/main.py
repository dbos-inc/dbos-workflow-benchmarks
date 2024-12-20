from contextlib import contextmanager
import gc
import time
from typing import TypedDict
from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import insert
import requests
from dbos import DBOS

from .schema import dbos_hello, useless_facts

app = FastAPI()
DBOS(fastapi=app)

class UselessFact(TypedDict):
    id: str
    text: str

import random

first_names = ["John", "Jane", "Alex", "Emily", "Chris", "Katie", "Michael", "Sarah", "David", "Laura"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Hernandez"]

def random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

@DBOS.transaction()
def save_greeting(name: str) -> str:
    query = (
        insert(dbos_hello)
        .values(name=name, greet_count=1)
        .on_conflict_do_update(
            index_elements=["name"], set_={"greet_count": dbos_hello.c.greet_count + 1}
        )
        .returning(dbos_hello.c.greet_count)
    )
    greet_count = DBOS.sql_session.execute(query).scalar_one()
    greeting = f"Greetings, {name}! You have been greeted {greet_count} times."
    DBOS.logger.info(greeting)
    return greeting

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


@DBOS.step()
def retrieve_name() -> str:
    name = random_name()
    time.sleep(0.1)
    return name


# Sync workflow
@DBOS.workflow()
def bench_workflow(num: int) -> list:
    output = []
    for _ in range(num):
        name = retrieve_name()
        greeting = save_greeting(name)
        output.append({"name": name, "greeting": greeting})

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
        output = retrieve_name()
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



# Bare handler
@app.get("/bare/{num}")
def bare(num: int):
    with disable_gc():
        start = time.perf_counter_ns()
        output = f"{random_name()}"
        time.sleep(0.1)
        end = time.perf_counter_ns()
        elapsed = end - start
        return {"output": output, "runtime": elapsed}

