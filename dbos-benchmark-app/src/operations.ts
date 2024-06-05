import { TransactionContext, Transaction, GetApi, WorkflowContext, Workflow, HandlerContext } from '@dbos-inc/dbos-sdk';
import { Knex } from 'knex';

export interface dbos_hello {
  name: string;
  greet_count: number;
}

export class Hello {
  @Transaction()
  static async benchmarkTransaction(ctxt: TransactionContext<Knex>, user: string) {
    const read_query = "SELECT COALESCE((SELECT greet_count FROM dbos_hello WHERE name = ?), 0) AS greet_count;";
    const { rows } = await ctxt.client.raw(read_query, [user]) as { rows: dbos_hello[] };
    const greet_count = rows[0].greet_count;
    let write_query;
    if (greet_count > 0) {
      write_query = "UPDATE dbos_hello SET greet_count=? WHERE name=?;";
    } else {
      write_query = "INSERT INTO dbos_hello (greet_count, name) VALUES (?, ?);";
    }
    await ctxt.client.raw(write_query, [greet_count + 1, user]);
    return `Hello, ${user}! You have been greeted ${greet_count + 1} times.\n`;
  }

  @Workflow()
  static async benchmarkWorkflow(ctxt: WorkflowContext, num: number) {
    let output;
    for (let i = 0; i < num; i++) {
      output = await ctxt.invoke(Hello).benchmarkTransaction("dbos");
    }
    return output;
  }

  @GetApi('/:num')
  static async benchmarkHandler(ctxt: HandlerContext, num: number) {
    const startTime = performance.now();
    const output = await ctxt.invokeWorkflow(Hello).benchmarkWorkflow(num);
    const elapsedTime = performance.now() - startTime;
    return {
      output: output,
      runtime: elapsedTime,
    };
  }
}
