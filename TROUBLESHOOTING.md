# Troubleshooting Guide

## Resource Leak Warnings

If you encounter warnings about resource leaks when interrupting the crawler, such as:

```
WARNING: Resource leak detected
```

This warning indicates that some resources were not properly released. To resolve this issue, ensure that all resources are properly closed in your code. For example, if you are using file streams, make sure to close them in a `finally` block.

## Connectivity Issues

If you experience connectivity issues, such as the crawler being unable to connect to the target server, try the following steps:

1. Check your network connection to ensure it is stable.
2. Verify that the target server is up and running.
3. Ensure that the target server's URL is correct.
4. Check for any firewall or security settings that might be blocking the connection.

## Other Common Problems

### Slow Performance

If the crawler is running slower than expected, consider the following:

1. Optimize your code to reduce unnecessary computations.
2. Increase the resources allocated to the crawler, such as CPU and memory.
3. Check for any network latency issues that might be affecting performance.

### Unexpected Errors

If you encounter unexpected errors, try the following steps:

1. Review the error message to understand the cause of the issue.
2. Check the logs for any additional information that might help diagnose the problem.
3. Ensure that all dependencies are properly installed and up to date.
4. If the issue persists, consider reaching out to the support team for further assistance.

