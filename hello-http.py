import datetime

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
    
    # Return a response with timezone-aware UTC timestamp
    return {
        "message": "Hello from InfluxDB 3 Processing Engine!",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
