const { SFNClient, StartExecutionCommand, DescribeExecutionCommand } = require("@aws-sdk/client-sfn");

// Initialize Step Functions Client
const client = new SFNClient({ region: "us-east-1" });

exports.handler = async (event) => {
    // Parameters for starting the Step Functions execution
    const startParams = {
        stateMachineArn: "arn:aws:states:us-east-1:500883621673:stateMachine:BenchmarkStandardWorkflow",
        input: JSON.stringify(event)  // Pass event data as input to the Step Functions
    };

    const startCommand = new StartExecutionCommand(startParams);

    try {
        // Start execution of the Step Functions state machine
        const startResult = await client.send(startCommand);
        const executionArn = startResult.executionArn;

        // Initialize variables for the loop
        let status = 'RUNNING';
        let startTime, endTime, runtime;

        // Polling loop to wait for the Step Functions execution to complete
        while (status === 'RUNNING') {
          const describeParams = {
              executionArn: executionArn
          };
          const describeCommand = new DescribeExecutionCommand(describeParams);
          const executionDetails = await client.send(describeCommand);

          status = executionDetails.status;
          if (status !== 'RUNNING') {
              endTime = new Date(executionDetails.stopDate);
              if (!startTime) { // Capture start time once
                  startTime = new Date(executionDetails.startDate);
              }
          }

          // Delay to avoid hitting the API rate limits
          await new Promise(resolve => setTimeout(resolve, 1000));
      }

        // Calculate runtime duration in seconds
        if (startTime && endTime) {
          runtime = (endTime - startTime) / 1000; // convert milliseconds to seconds
      }

      // Return the final output of the Step Functions execution and the runtime
      return {
          statusCode: 200,
          body: JSON.stringify({
              runtimeSeconds: runtime
          })
      };

    } catch (error) {
        console.error("Error executing Step Functions:", error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error executing Step Functions", details: error })
        };
    }
};
