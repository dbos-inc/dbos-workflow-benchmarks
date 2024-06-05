import { TransactionContext, Transaction, GetApi, WorkflowContext, Workflow } from '@dbos-inc/dbos-sdk';
import { Knex } from 'knex';

// The schema of the database table used in this example.
export interface dbos_hello {
  name: string;
  greet_count: number;
}

export class Hello {

  @Transaction()
  static async helloTransaction(ctxt: TransactionContext<Knex>, user: string) {
    // Retrieve and increment the number of times this user has been greeted.
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

  @GetApi('/:num')
  @Workflow()
  static async helloWorkflow(ctxt: WorkflowContext, num: number) {
    const start = performance.now();
    for (let i = 0; i < num; i++) {
      await ctxt.invoke(Hello).helloTransaction("dbos");
    }
    const end = performance.now();
    return end - start;
  }
}
