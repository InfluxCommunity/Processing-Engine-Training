# Processing Engine 101
InfluxDB 3 Processing Engine Tutorial

## Pre-Requisites:

1. Install Python Version 3.x
2. Install InfluxDB 3 Core ```curl -O curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh``` or Enterprise ```curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh enterprise```

## Processing engine

It is an embedded Python VM that runs inside your InfluxDB 3 database and lets you:
- Process data as it’s written to the database
- Run code on a schedule
- Create API endpoints that execute Python code
- Maintain state between executions with an in-memory cache

### Setup

Processing Engine executes python script also known as 'plugin' inside a python virtual enviornment. These plugins can be located either in a local directory on your machine or they can be in a public GitHub repository. To configure the location of the plugins, you need to provide the path as an argument at the time of starting InfluxDB 3 as follows:

```shell
influxdb3 serve \
  --node-id [YOUR_NODE_ID] \
  --object-store [YOUR_OBJECT_STORE_TYPE] \
  --plugin-dir [YOUR_PLUGIN_DIR_PATH]
```

**Example**

```shell
influxdb3 serve \
  --node-id node0 \
  --object-store file \
  --plugin-dir ~/.plugins
```

#### Install Python dependencies (optional)

InfluxDB 3 creates a virtual enviornment for running python processing engine plugins. Those plugins are often dependent on python packages such as those from PyPy. They can be installed using influxdb3 cli `influxdb3 install package pandas`

### Plugin & Triggers

A trigger connects your plugin to a specific database event. The plugin function signature in your plugin file determines which trigger specification you can choose for configuring and activating your plugin.

Create a trigger with the influxdb3 create trigger command.

### 3 Types of Plugin Triggers

#### 1. WAL-Flush

```python
def process_writes(influxdb3_local, table_batches, args=None):
    # Process data as it's written to the database
    for table_batch in table_batches:
        table_name = table_batch["table_name"]
        rows = table_batch["rows"]
        
        # Log information about the write
        influxdb3_local.info(f"Processing {len(rows)} rows from {table_name}")
        
        # Write derived data back to the database
        line = LineBuilder("processed_data")
        line.tag("source_table", table_name)
        line.int64_field("row_count", len(rows))
        influxdb3_local.write(line)
```

#### 2. Schedule

#### 3. HTTP Request


### Trigger Execution
One or more trigger can be setup to run simultaneously either synchnorously (default behavior) or asynchnorously.

### Testing Plugin

### Extending Plugin with APIs

### Using Community created Plugin

You can reference plugins directly from the GitHub repository by using the `gh: prefix`

```shell
influxdb3 create trigger \
  --trigger-spec "every:1m" \
  --plugin-filename "gh:examples/schedule/system_metrics/system_metrics.py" \
  --database my_database \
  system_metrics
```

   
