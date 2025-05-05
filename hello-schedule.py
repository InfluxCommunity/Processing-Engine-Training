"""
Entry point for scheduled triggers that is called based on defined schedule. It logs a message and writes to the scheduler_heartbeat table.
Arguments: influxdb3_local (API object), call_time (trigger time), args (optional trigger arguments).
"""
def process_scheduled_call(influxdb3_local, call_time, args=None):
    # Log that the plugin was triggered
    influxdb3_local.info(f"Hello from scheduled plugin! Called at {call_time}")
    
    # Log a dummy alert
    influxdb3_local.info("ALERT: This is a dummy alert from the scheduler plugin!")
    
    # Query some data
    results = influxdb3_local.query("SELECT count(*) FROM data_insights")
    
    # Write a heartbeat record
    line = LineBuilder("scheduler_heartbeat")
    line.tag("source", "schedule_plugin")
    line.string_field("status", "running")
    line.string_field("alert_type", "dummy_alert")
    
    influxdb3_local.write(line)
