import datetime

"""
Entry point for WAL flush triggers that does basic data processing and it to a new table.
Arguments: influxdb3_local (API object), table_batches (data written), args (optional trigger arguments).
"""
def process_writes(influxdb3_local, table_batches, args=None):
    # Log that the plugin was triggered
    influxdb3_local.info("Processing data with enhanced WAL plugin!")
    
    # Process each table's data
    for table_batch in table_batches:
        table_name = table_batch["table_name"]
        rows = table_batch["rows"]
        
        # Skip processing our own output table to avoid recursion
        if table_name == "data_insights":
            continue
            
        # Log information about the data
        influxdb3_local.info(f"Processing {len(rows)} rows from table {table_name}")
        
        # Calculate some basic statistics if we have numeric fields
        total_values = 0
        max_value = float('-inf')
        min_value = float('inf')
        has_numeric = False
        
        for row in rows:
            # Look for numeric fields we can analyze
            for field_name, value in row.items():
                if isinstance(value, (int, float)) and field_name != "time":
                    has_numeric = True
                    total_values += value
                    max_value = max(max_value, value)
                    min_value = min(min_value, value)
        
        # Write insights to a dedicated table
        line = LineBuilder("data_insights")
        line.tag("source_table", table_name)
        line.int64_field("row_count", len(rows))
        
        # Add statistics if we found numeric values
        if has_numeric:
            line.float64_field("max_value", max_value)
            line.float64_field("min_value", min_value)
            if len(rows) > 0:
                line.float64_field("avg_value", total_values / len(rows))
        
        # Add a timestamp field showing when this processing occurred
        line.string_field("processed_at", datetime.datetime.utcnow().isoformat())
        
        # Write the insights back to the database
        influxdb3_local.write(line)
        
        # Log completion
        influxdb3_local.info(f"Generated insights for {table_name}")
