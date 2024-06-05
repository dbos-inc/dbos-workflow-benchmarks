const { Client } = require('pg');

let client;

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
        const res = await client.query('SELECT 1');

        const response = {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(res.rows)
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
