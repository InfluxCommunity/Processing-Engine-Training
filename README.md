# Processing Engine Training

This guide provides a foundational training of the InfluxDB 3 Processing Engine that can be done by yourself. Refer to the [official documentation](https://docs.influxdata.com) and the community plugins [repository](https://github.com/influxdata/influxdb3_plugins) to discover more advanced use cases and capabilities.

### Pre-Requisites:

1. **Python**: Make sure you have Python version 3.x on your system.
2. **Code Editor**: Your favorite code editor.
3. **Install InfluxDB 3**: Either InfluxDB 3 Core or Enterprise.

   InfluxDB 3 Core
   ```shell
   curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh
   ```
   InfluxDB 3 Enterprise
   ```shell
   curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh enterprise
   ```
4. **Verify installation**: Open terminal window and run `influxdb3` command without error to ensure it installed successfully.


## Processing Engine

It is an embedded Python VM that runs inside your InfluxDB 3 database and lets you:
- Process data as it’s written to the database.
- Run code on a schedule.
- Create API endpoints that execute Python code.
- Maintain state between executions with an in-memory cache.

## Plugins & Triggers

- **Plugins**: Python scripts executed by InfluxDB, containing callback functions defined for specific tasks.

- **Triggers**: Mechanisms that activate plugins based on specific conditions or schedules.
   - Configure triggers with arguments (--trigger-arguments) to control plugin behavior.
   - Multiple triggers can run plugins simultaneously, synchronously or asynchronously.

### Workflow

+-----------------+
|   Data Source   |
| (Telegraf, CSV, |
|  CLI, API etc)  |
+-----------------+
         |
         | Write Data
         V
+-----------------+
|   InfluxDB 3    |
| Core/Enterprise |
+-----------------+
         |
         | WAL Flush
         V
+-----------------+       +-----------------+
|  Set Trigger(s) |------>| Executes Plugin |
| (Data Write,    |       |  (Python Code)  |
|  Scheduled,     |       |                 |
| HTTP Request)   |       |                 |
+-----------------+       +-----------------+
         |                |       |
         |                |       |  Read/Write via API
         |                |       V
         |                | +-----------------+
         |                | |  InfluxDB 3     |
         |                | |  Data Storage   |
         |                | | (Tables, etc.)  |
         |                | +-----------------+
         |                |       |
         |                |       |  Optional APIs
         |                |       V
         |                | +---------------------------------------+
         |                | |In-Memory Cache, Write, Query, Log etc |
         |                | |                                       |
         |                | +---------------------------------------+
         +----------------+

### Setup

To enable the Processing Engine, you need to tell InfluxDB where to find your Python plugin files. Use the `--plugin-dir` option when starting the server.

1. Create a Plugin directory if it doesn't exist where python scripts also referred as plugins will reside. Optionally, you also reference plugin from a GitHub repository in which case you can omit directory creation and start InfluxDB 3 without providing it plugin folder path.
   
```shell
mkdir plugins
```

2. Stop and Start InfluxDB 3 with Plugin Support if using plugins from local directory

2.1 Stop InfluxDB3

If InfluxDB 3 is running in the foreground, you can usually stop it by pressing `Ctrl+C` otherwise in a new terminal window execute the following commands:
```shell
ps aux | grep influxdb3  # Find the process ID (PID)
kill -9 <PID>            # Replace <PID> with the actual process ID
```

2.2 Start InfluxDB with Processing Engine
```shell
influxdb3 serve \
  --node-id node0 \                       # Node identifier
  --object-store file \                   # Object storage type, here we chose file but you can chose memory or remote object store like S3
  --plugin-dir ~/.influxdb3/plugins       # Directory for your local python plugins
```
> [!TIP]
Omit `--plugin-dir` if using plugins directly from GitHub

3. Create a Token using the CLI

Most `influxdb3` commands require an authentication token. Create an admin token using the following command and save it somewhere securely:
```shell
influxdb3 create token --admin
```

> [!IMPORTANT]
> Remember, tokens give full access to InfluxDB. It is recommended to secure your token string as it is not saved within the database thus can't be retreived if lost. You can save it as a local **INFLUXDB3_AUTH_TOKEN** enviornment variable or in a keystore.

4. Create Database using the cli (optionally it is created automatically when line protocol data is first written to it)
```shell
influxdb3 create database my_awesome_db
```

5. Write Data using the CLI
```shell
influxdb3 write \
  --database my_awesome_db \
  --token YOUR_TOKEN \
  --precision ns \
  'cpu,host=server01,region=us-west value=0.64 1641024000000000000'
```

6. Query Data using the CLI
```shell
influxdb3 query \
  --database my_awesome_db \
  --token YOUR_TOKEN \
  "SELECT * FROM cpu"
``` 

### Plugin & Triggers

A plugin is a Python file containing a callback function with a specific signature that corresponds to the trigger type. The trigger defines and configures the plugin including providing any optional information using `--trigger-arguments` option. One or more trigger can be setup to run simultaneously either synchnorously (default behavior) or asynchnorously.

#### Install Python dependencies (optional)

InfluxDB 3 provides a virtual enviornment for running python processing engine plugins. Those plugins are often dependent on python packages such as those from PyPy. They can be installed using influxdb3 cli for example `influxdb3 install package pandas` to install pandas package.

**There are three main trigger types**:

#### 1. WAL-Flush

This trigger executes your plugin whenever data is written to specified tables and the Write-Ahead Log (WAL) is flushed to the object store (typically every second).

1.1 Create a WAL-Flush trigger that runs when data is written to any table. It can also be modified to run on a specific table.
```shell
influxdb3 create trigger \
  --trigger-spec "all_tables" \       # Process all tables in the database
  --plugin-filename "hello-wal.py" \  # Python plugin file in your plugin directory
  --database my_awesome_db \          # Database to monitor
  hello_wal_trigger                   # Name of the trigger
```

1.2 Create a plugin for WAL-Flush trigger. [Sample file](hello-wal.py)
```python
from influxdb3 import LineBuilder
"""
Entry point for WAL flush triggers that is called when data is written to the database.
Arguments: influxdb3_local (API object), table_batches (data written), args (optional trigger arguments).
"""
def process_writes(influxdb3_local, table_batches, args=None):
    # Log that the plugin was triggered
    influxdb3_local.info("Hello from WAL plugin!")
    
    # Process each table's data
    for table_batch in table_batches:
        table_name = table_batch["table_name"]
        rows = table_batch["rows"]

        # Log information about the data
        influxdb3_local.info(f"Received {len(rows)} rows from table {table_name}")

        # Write a summary record back to the database
        line = LineBuilder("hello_summary")
        line.tag("source", "wal_plugin")
        line.tag("table", table_name)
        line.int64_field("row_count", len(rows))
        influxdb3_local.write(line)
```

1.3 Test WAL-Flush plugin

Run the following command to write sample data.
```shell
influxdb3 write \
  --database my_awesome_db \
  --table test_data \
  --field value=123 \
  --tag tag1=value1
```

Verify the following:

**InfluxDB Server Logs**: You should see the "Hello from WAL plugin!" message, and a message indicating the number of rows processed.

**Table - hello_summary **: Query the hello_summary table in your database `influxdb3 query --database my_awesome_db 'SELECT * FROM hello_summary'`

You should see a new data point confirming that the WAL Flush trigger is working correctly and your plugin is processing the data written to InfluxDB.

#### 2. Schedule plugin

2.1 Create a Scchedule trigger that runs on any particular schedule:
```shell
influxdb3 create trigger \
  --trigger-spec "every:1m" \             # Run every minute (can use cron syntax too)
  --plugin-filename "hello-schedule.py" \ # Python plugin file
  --database my_awesome_db \                # Database to use
  hello_schedule_trigger                  # Name of the trigger
```

2.2 Create a plugin for WAL-Flush trigger. [Sample file](hello-schedule.py)
```python
"""
Entry point for scheduled triggers that is called based on defined schedule.
Arguments: influxdb3_local (API object), call_time (trigger time), args (optional trigger arguments).
"""
def process_scheduled_call(influxdb3_local, call_time, args=None):
    # Log that the plugin was triggered
    influxdb3_local.info(f"Hello from scheduled plugin! Called at {call_time}")
    
    # Query some data
    results = influxdb3_local.query("SELECT count(*) FROM hello_summary")
    
    # Write a heartbeat record
    line = LineBuilder("scheduler_heartbeat")
    line.tag("source", "schedule_plugin")
    line.string_field("status", "running")
    line.time_ns(int(call_time * 1e9))  # Convert to nanoseconds
    influxdb3_local.write(line)
```

#### 3. HTTP Request plugin

3.1 Create a HTTP trigger that responds to HTTP requests such as a webhook.
```shell
# Create a trigger that responds to HTTP requests
influxdb3 create trigger \
  --trigger-spec "request:hello" \        # Create endpoint at /api/v3/engine/hello
  --plugin-filename "hello-http.py" \     # Python plugin file
  --database my_awesome_db \              # Database to use
  hello_http_trigger                      # Name of the trigger
```

3.2 Create a plugin to handle HTTP requests. [Sample file](hello-http.py)
```python
"""
Entry point for HTTP request triggers that is called when requests hit custom endpoint.
Arguments: influxdb3_local (API), query_parameters, request_headers, request_body, args (optional).
Returns response object to the client.
"""
def process_request(influxdb3_local, query_parameters, request_headers, request_body, args=None):
    # Log that the plugin was triggered
    influxdb3_local.info("Hello from HTTP plugin!")
    
    # Log request details
    influxdb3_local.info(f"Query parameters: {query_parameters}")
    
    # Write a record of the request
    line = LineBuilder("api_requests")
    line.tag("endpoint", "hello")
    line.int64_field("received", 1)
    influxdb3_local.write(line)
    
    # Return a response (automatically converted to JSON)
    return {
        "message": "Hello from InfluxDB 3 Processing Engine!",
        "timestamp": influxdb3_local.query("SELECT now()")[0]["now"]
    }
```

3.3 Test the HTTP Request plugin

Send a GET or POST request to your custom endpoint such as http://localhost:8181/api/v3/engine/webhook
```shell
curl http://localhost:8181/api/v3/engine/webhook -X POST -H "Content-Type: application/json" -d '{"message": "Hello from webhook!"}'
```
You should see logs in the InfluxDB server output, and the hello-http.py plugin will process the request and return a JSON response.

### Extending Plugin with APIs

Extend your plugin's fuctionality using Python APIs:

- Writing Data: Use influxdb3_local.write(line_protocol_string) or the LineBuilder class.
- Querying Data: Use influxdb3_local.query(sql_query, params=None).
- Logging: Use influxdb3_local.info(), influxdb3_local.warn(), and influxdb3_local.error() for logging messages.
- In-Memory Cache: Use influxdb3_local.cache to store and retrieve data between plugin executions.

### Using Community created Plugin

You can directly use plugins from the official [InfluxData Plugins GitHub repository](https://github.com/influxdata/influxdb3_plugins) or other public repositories using the gh: prefix in the `--plugin-filename argument` 

Example - using sample system_metrics schedule plugin
```shell
influxdb3 create trigger \
  --trigger-spec "every:1m" \
  --plugin-filename "gh:examples/schedule/system_metrics/system_metrics.py" \
  --database my_awesome_db \
  system_metrics
```

### Get Involved and Contribute!

We encourage you to contribute to the InfluxDB community and help make the Processing Engine even better!

- **Report Issues**: If you encounter any problems or have questions, please open an issue on the GitHub repository.
- **Share Your Plugins**: Create your own InfluxDB 3 plugins and share them with the community by contributing to the InfluxData Plugins Repository.
- **Join the Community**: Connect with other InfluxDB users and developers through our community channels on [Discord](https://discord.com/invite/vZe2w2Ds8B), [Slack](https://influxdata.com/slack) and website [forum](https://community.influxdata.com)
- **Star the Repository**: If you found this valuable, please star this repository.

