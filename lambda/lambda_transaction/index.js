const { Client } = require('pg');

exports.handler = async (event) => {
    const { hostname, username, password } = event;

    const client = new Client({
        host: hostname,
        user: username,
        password: password,
        database: "dbos_benchmark",
        ssl: { rejectUnauthorized: false }
    });

    try {
        await client.connect();
        const res = await client.query('SELECT 1');
        await client.end();

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
