"""
Kronos utilities for HTTP
"""

from requests import Response
from typing import Dict, Any
from urllib.parse import urlparse, parse_qsl


def parse_query_params(url: str) -> Dict[str, Any]:
    """
    Parse query parameters from a URL into a dictionary
    Handles both key=value pairs and standalone switches

    Args:
        url: The complete URL

    Returns:
        Dictionary of query parameters
    """
    parsed_url = urlparse(url)
    # Process standard key=value parameters
    query_params = dict(parse_qsl(parsed_url.query))

    # Process switches (parameters without values)
    # Look for parameters that appear in the query string but not in the dict from parse_qsl
    if parsed_url.query:
        raw_params = parsed_url.query.split("&")
        for param in raw_params:
            if "=" not in param and param:  # It's a switch
                query_params[param] = True

    return query_params


def format_human_readable_size(size: int) -> str:
    """
    Format the number to a human readable bytes size

    Args:
        size: Byte size number

    Returns:
        String with size and unity
    """
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    idx = 0

    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1

    return f"{size:.2f} {units[idx]}"


def format_http_response(response: Response) -> Dict[str, Any]:
    """
    Format an HTTP response object into a JSON-serializable dictionary with sensitive data redaction

    Args:
        response: HTTP response object

    Returns:
        Dictionary with formatted HTTP request and response details
    """
    try:
        # Calculate response size
        response_size = format_human_readable_size(len(response.content))

        # Extract request information
        request = response.request

        # Redact headers
        sensitive_headers = ['authorization', 'auth', 'x-auth', 'x-api-key', 'api-key', 'apikey','password', 'x-access-token', 'token', 'jwt', 'bearer','cookie', 'set-cookie', 'session', 'x-session-id', 'sessionid','csrf', 'x-csrf-token', 'x-xsrf-token','key', 'secret', 'private', 'signature','x-user-id', 'userid']

        request_headers = dict(request.headers)
        for header in list(request_headers.keys()):
            if header.lower() in sensitive_headers:
                request_headers[header] = "[REDACTED]"

        response_headers = dict(response.headers)
        for header in list(response_headers.keys()):
            if header.lower() in sensitive_headers:
                response_headers[header] = "[REDACTED]"

        # Parse URL and extract query parameters
        url = response.url
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path or "/"
        query_params = parse_query_params(url)

        # Format response data
        return {
            "request": {
                "host": host,
                "path": path,
                "method": request.method,
                "headers": request_headers,
                "query_params": query_params
            },
            "response": {
                "status_code": response.status_code,
                "elapsed_time_ms": f"{response.elapsed.total_seconds() * 1000:.3f}",
                "size": response_size,
                "headers": response_headers,
                "cookies": extract_cookies(response)
            }
        }
    except Exception as e:
        return {
            "error": f"Failed to format HTTP response: {str(e)}",
            "status_code": getattr(response, "status_code", None)
        }


def extract_cookies(response: Response) -> Dict[str, Any]:
    """
    Extract cookies from an HTTP response with sensitive data redaction

    Args:
        response: HTTP response object

    Returns:
        Dictionary with cookies information
    """
    cookies = {}

    # List of cookie names that typically contain sensitive information
    sensitive_cookies = ['auth', 'token', 'session', 'csrf', 'key','secret', 'password', 'access', 'user', 'id','jwt', 'refresh', 'api', 'credentials', 'oauth']

    # Extract cookies from response
    if hasattr(response, 'cookies') and response.cookies:
        for cookie in response.cookies:
            cookies[cookie.name] = {
                'value': "[REDACTED]" if cookie.name.lower() in sensitive_cookies else cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'secure': cookie.secure,
                'http_only': cookie.has_nonstandard_attr('HttpOnly')
            }

    return cookies