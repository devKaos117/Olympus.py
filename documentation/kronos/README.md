# Kronos ![v2.0.0](https://img.shields.io/badge/version-2.0.0-informational)
<a href="https://github.com/devKaos117/Kronos.py/blob/main/LICENSE" target="_blank">![Static Badge](https://img.shields.io/badge/License-%23FFFFFF?style=flat&label=MIT&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fgithub%2Ecom%2FdevKaos117%2FKronos%2Epy%2Fblob%2Fmain%2FLICENSE)</a>
## Index

-   [About](#about)
    -   [Summary](#about-summary)
    -   [Features](#about-features)
- [Usage](#usage)
    -   [Installation](#usage-installation)
    -   [Examples](#usage-examples)
-   [Technical Description](#technical-description)
    -   [Applied Technologies](#technical-description-techs)
    -   [Dependencies](#technical-description-dependencies)

---

## About <a name = "about"></a>

### Summary <a name = "about-summary"></a>
Kronos is a Python utility package for dealing with time, analysis and logging. It was designed to simplify the development of robust, high-performance applications with clean observability and controlled resource usage

### Features <a name = "about-features"></a>

- **Advanced Logging**
    - Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Process and thread information tracking
    - Detailed request/response logging for HTTP operations
    - Different log levels for console and file outputs
    - Cookie extraction and logging
    - Encoding-aware text handling

- **Rate Limiting**
    - Token bucket algorithm implementation
    - Support for both multithreading and multiprocessing
    - Context manager interface for clean resource management

- **Future Improvements**
    - TimeTracker: Class for measuring and recording time intervals
    - Handling of log rotation
    - Support for JSON logging
    - Logging packets with socket info
    - Sampling for High-Volume

---

## Usage <a name = "usage"></a>

### Installation <a name = "usage-installation"></a>

For development installation:

```bash
git clone https://github.com/devKaos117/Kronos.py.git
cd ./Kronos.py/Kronos
pip install -e
```

### Examples <a name = "usage-examples"></a>

#### Basic Logging

```json
// ./configuration/logger.json
{
    "console_level": "INFO",
    "file_level": "DEBUG",
    "log_directory": "log"
}
```

```python
from kronos import Logger

# Initialize the logger
logger = Logger()

# Log messages at different levels
logger.debug("This won't show because it's below INFO level")
logger.info("Starting application...")
logger.warning("Configuration file not found, using defaults")
logger.error("Could not connect to database")
logger.critical("System shutdown initiated due to critical error")

# Log an exception
try:
    result = 10 / 0
except Exception as e:
    logger.exception(e)  # Will log the full stack trace
```

#### HTTP Request Logging

```python
import requests
from kronos import Logger

# Initialize a logger with debug level to capture HTTP details
config = {
    "console_level": None,
    "file_level": "DEBUG",
    "log_directory": "log"
}

logger = Logger(config)

# Make an HTTP request
response = requests.get("https://www.google.com.br/search?q=python")

# Log the full HTTP request and response
logger.log_http_response(response, "Web page")
```

#### Rate Limiting

```json
// ./configuration/ratelimiter.json
{
    "limit": 30,
    "time_period": 60,
    "multiprocessing_mode": false
}
```

```python
import time, threading
from kronos import Logger, RateLimiter

# Initialize logger
logger = Logger()
# Initialize RateLimiter
rate_limiter = RateLimiter(logger=logger, config=config)

def make_api_call(call_id):
    # Use the rate limiter before making the call
    rate_limiter.acquire()

    logger.info(f"Making API call {call_id}")
    # ... API call code here

# Using as a context manager
def make_api_call_with_context(call_id):
    with rate_limiter:  # Acquires and releases automatically
        logger.info(f"Making API call {call_id}")
        # ... API call code here

# Start multiple threads
threads = []
for i in range(20):
    thread = threading.Thread(target=make_api_call, args=(i,))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()
```

#### Multi-processing Rate Limiting

```python
import multiprocessing
from kronos import Logger, RateLimiter

# Initialize logger
logger = Logger()
# Initialize RateLimiter
config = {
    "limit": 5,
    "time_period": 10,
    "multiprocessing_mode": True
}

rate_limiter = RateLimiter(logger=logger, config=config)

def worker_process(worker_id):
    for i in range(20):
        rate_limiter.acquire()

        logger.info(f"Worker {worker_id} - Task {i}")
        # ... resource-intensive task ...

if __name__ == "__main__":
    # Start multiple processes
    processes = []
    for i in range(8):
        p = multiprocessing.Process(target=worker_process, args=(i,))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()
```

---

## Technical Description <a name = "technical-description"></a>

### Applied Technologies <a name = "technical-description-techs"></a>

#### Development Environment
&emsp;&emsp;<a href="https://archlinux.org/">![Static Badge](https://img.shields.io/badge/v2025-%23FFFFFF?style=flat&logo=archlinux&logoColor=%1793D1&logoSize=auto&label=Arch&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fwww.archlinux.org)</a>
<br>
&emsp;&emsp;<a href="https://www.zsh.org" target="_blank">![Static Badge](https://img.shields.io/badge/v5.9-%23FFFFFF?style=flat&logo=zsh&logoColor=%23F15A24&logoSize=auto&label=zsh&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fwww.zsh.org)</a>
<br>
&emsp;&emsp;<a href="https://code.visualstudio.com" target="_blank">![Static Badge](https://img.shields.io/badge/v1.99.3-%23FFFFFF?style=flat&logo=codecrafters&logoColor=%230065A9&logoSize=auto&label=VS%20Code&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fcode.visualstudio.com)</a>


#### Application Components
&emsp;&emsp;<a href="https://www.python.org/" target="_blank">![Static Badge](https://img.shields.io/badge/v3.13.2-%23FFFFFF?style=flat&logo=python&logoColor=%233776AB&logoSize=auto&label=Python&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fwww%2Epython%2Eorg%2F)</a>