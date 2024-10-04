# DBOS Workflow Benchmarks

This repository contains code to benchmark the performance of workflows in DBOS and in AWS Step Functions (both standard and express workflows).

# Benchmark Information

The benchmark runs a workflow with a varying number of steps.
Each step is a function that performs a simple database transaction.
This transaction is implemented in a [Lambda](https://aws.amazon.com/lambda/) in Step Functions and as a [transaction function](https://docs.dbos.dev/tutorials/transaction-tutorial) in DBOS.
Benchamrks report server-side workflow duration in each system.

# Benchmark Instructions

To run the benchmarks, first deploy the Step Functions workflows:

```
scripts/zip_lambdas.sh
terraform init
terraform apply
```

Then deploy the DBOS application (assuming you already have a DBOS Cloud account):

```
cd dbos-benchmark-app
npm i
npx dbos-cloud login
npx dbos-cloud db provision <db-name> -U <db-username> -W <db-password>
npx dbos-cloud app deploy
```

To benchmark Step Functions standard workflows, run:

```
python3 benchmarks/benchmark_standard_workflow.py -H <database-hostname> -U <database-username> -W <database-password> -i <functions-per-workflow> -n <number-of-iterations>
```

To provide a fair comparison, we recommend using the database hostname, username, and password from your DBOS app.
To obtain the DBOS database hostname, run `npx dbos-cloud db list` in the DBOS application directory.

To benchmark Step Functions express workflows, run:

```
python3 benchmarks/benchmark_express_workflow.py -H <database-hostname> -U <database-username> -W <database-password> -i <functions-per-workflow> -n <number-of-iterations>
```

All parameters are the same as for standard workflows.

To benchmark DBOS workflows, run:

```
python3 benchmarks/benchmark_dbos.py -u <app-url> -i <functions-per-workflow> -n <number-of-iterations>
```

To obtain your DBOS app URL, run `npx dbos-cloud app status` in the DBOS app directory.