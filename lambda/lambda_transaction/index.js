const { Client } = require('pg');

let client;
const user = "dbos";

const connectToDatabase = async (hostname, username, password) => {
    if (!client) {
        client = new Client({
            host: hostname,
            user: username,
            password: password,
            database: "dbos_benchmark",
            ssl: { rejectUnauthorized: false }
        });
        await client.connect();
    }
};

exports.handler = async (event) => {
    const { hostname, username, password } = event;

    try {
        await connectToDatabase(hostname, username, password);
        await client.query("BEGIN");
        const read_query = "SELECT COALESCE((SELECT greet_count FROM dbos_hello WHERE name = $1), 0) AS greet_count;";
        const { rows } = await client.query(read_query, [user]);
        const greet_count = rows[0].greet_count;
        let write_query;
        if (greet_count > 0) {
          write_query = "UPDATE dbos_hello SET greet_count=$1 WHERE name=$2;";
        } else {
          write_query = "INSERT INTO dbos_hello (greet_count, name) VALUES ($1, $2);";
        }
        await client.query(write_query, [greet_count + 1, user]);
        await client.query("COMMIT");
        const response = {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(`Hello, ${user}! You have been greeted ${greet_count + 1} times.\n`)
        };
        return response;
    } catch (error) {
        const response = {
            statusCode: 500,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ error: error.message })
        };
        return response;
    }
};
