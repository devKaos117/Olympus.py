import time, requests
from typing import Dict, Any, Optional

from .utils.user_agent import UserAgent

from .. import kronos
from ..utils.configuration import ConfigManager


class HTTPy:
    """
    HTTPy

    A flexible HTTP client with built-in retry, timeout, proxy rotation,
    cookies and session maintanability. Buit-in usage of kronos.Logger
    and kronos.RateLimiter
    """

    def __init__(self, logger: kronos.Logger, rate_limiter: Optional[kronos.RateLimiter] = None):
        """
        Initialize the HTTP client with the provided configuration

        Args:
            config: Configuration dictionary
            logger: kronos.Logger instance to use
        """
        self._logger = logger
        self._rate_limiter = rate_limiter

        self._config = ConfigManager.load()
        self._session = self._create_session()

        self._logger.debug("HTTPy config", self._config)
        self._logger.info("HTTPy client initialized")

    def _create_session(self) -> requests.Session:
        """
        Create and configure a requests Session

        Returns:
            requests.Session: Configured session object
        """
        session = requests.Session()

        # Set default headers
        session.headers = self._config['request']['headers']
        self._logger.debug("Session initialized")

        return session

    def _execute_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Execute an HTTP request with the given method and parameters

        Args:
            method: HTTP method
            url: URL to send the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server or None
        """
        # Apply default timeout if not specified in kwargs
        if "timeout" not in kwargs:
            kwargs['timeout'] = self._config['request']['timeout']

        # Merge default headers with any provided in kwargs
        if "headers" in kwargs:
            merged_headers = ConfigManager.deep_merge(kwargs['headers'], self._config['request']['headers'].copy())
            kwargs['headers'] = merged_headers

        # Make requests
        response = None
        retries = 0

        while retries <= self._config['request']['retries']['max']:
            # Apply rate limiting if enabled
            if self._rate_limiter:
                self._rate_limiter.acquire()
            try:
                if self._config['request']['randomize_agent']:
                    self._session.headers.update({"User-Agent": UserAgent.random()})

                response = self._session.request(method, url, **kwargs)
                
                # Handle different status codes
                self._handle_response_status(response)

                # Stop retries if successful
                if response.status_code in self._config['request']['success_codes']:
                    break    
                # Stop retries if not configured to repeat
                if response.status_code not in self._config['request']['retries']['codes']:
                    break
            except requests.RequestException as e:
                self._logger.exception(f"Network error making request: {str(e)}")
                self._logger.log_http_response(response)
            except Exception as e:
                self._logger.exception(f"Error making request: {str(e)}")
                self._logger.log_http_response(response)
                time.sleep(1)

            retries += 1

        if response is None or response.status_code not in self._config['request']['success_codes']:
            self._logger.error(f"HTTP request failed after {retries - 1 if retries > 0 else 0} retries")
            raise Exception("Unsuccessful request")
        else:
            self._logger.log_http_response(response)

        return response

    def _handle_response_status(self, response: requests.Response) -> None:
        """
        Handle the response based on its status code

        Args:
            response (requests.Response): The response to handle
        """
        if response.status_code < 200 or response.status_code > 299:
            self._logger.log_http_response(response)
        
        if 400 <= response.status_code < 500:
            if response.status_code == 401:
                self._logger.error(f"Authentication error: {response.status_code} - {response.text}")
            elif response.status_code == 403:
                self._logger.error(f"Forbidden: {response.status_code} - {response.text}")
            elif response.status_code == 404:
                self._logger.error(f"Not found: {response.status_code} - {response.text}")
            elif response.status_code == 429:
                self._logger.error(f"Too many requests: {response.status_code} - {response.text}")
                time.sleep(15)
            else:
                self._logger.error(f"Client error: {response.status_code} - {response.text}")
        elif 500 <= response.status_code < 600:
            self._logger.error(f"Server error ({response.status_code}): {response.text}")
            time.sleep(1)

    def get(self, url: str, params: Optional[Dict[str, Any]] = {}, **kwargs) -> requests.Response:
        """
        Send a GET request to the specified URL

        Args:
            url : URL to send the request to
            params : Query parameters for the request
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server
        """
        return self._execute_request("GET", url, params=params, **kwargs)

    def post(self, url: str, data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,**kwargs) -> requests.Response:
        """
        Send a POST request to the specified URL

        Args:
            url: URL to send the request to
            data: Data to send in the request body
            json: JSON data to send in the request body
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server
        """
        return self._execute_request("POST", url, data=data, json=json, **kwargs)

    def close(self) -> None:
        """Close the session and release resources."""
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit that ensures session closure."""
        self.close()