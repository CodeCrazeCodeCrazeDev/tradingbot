"""
Elite Trading Bot - Web Client

This module provides a secure and robust web client for making HTTP requests
with advanced features like retry logic, timeout handling, and security measures.
"""

import asyncio
import enum
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import ssl

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None
    HTTPAdapter = None
    Retry = None
from typing import Set
from enum import Enum
import json

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class RequestMethod(enum.Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class WebClient:
    """
    Secure web client for making HTTP requests with advanced features.
    
    Features:
    - Synchronous and asynchronous request support
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - SSL/TLS security with certificate verification
    - Request/response logging
    - Timeout management
    - Session pooling for performance
    """
    
    def __init__(self, 
                 base_url: Optional[str] = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 verify_ssl: bool = True,
                 headers: Optional[Dict[str, str]] = None,
                 proxies: Optional[Dict[str, str]] = None):
        """
        Initialize the web client.
        
        Args:
            base_url: Optional base URL for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            verify_ssl: Whether to verify SSL certificates
            headers: Default headers to include in all requests
            proxies: Proxy configuration for requests
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.default_headers = headers or {
            "User-Agent": "EliteTradingBot/1.0",
            "Accept": "application/json",
        }
        self.proxies = proxies
        
        # Configure session for synchronous requests
        self.session = self._create_session()
        
        # Async session will be created on demand
        self._async_session = None
        
        logger.info("WebClient initialized")
    
    def _create_session(self) -> requests.Session:
        """
        Create a configured requests session with retry logic.
        
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update(self.default_headers)
        
        # Set proxies if provided
        if self.proxies:
            session.proxies.update(self.proxies)
        
        return session
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp client session.
        
        Returns:
            aiohttp.ClientSession object
        """
        if self._async_session is None or self._async_session.closed:
            # Configure SSL context
            ssl_context = None
            if self.verify_ssl:
                ssl_context = ssl.create_default_context()
            else:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create session with default headers
            self._async_session = aiohttp.ClientSession(
                headers=self.default_headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            )
        
        return self._async_session
    
    def request(self, 
                method: RequestMethod, 
                endpoint: str, 
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Any] = None,
                json_data: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None,
                timeout: Optional[int] = None,
                verify_ssl: Optional[bool] = None) -> requests.Response:
        """
        Make a synchronous HTTP request.
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint (will be appended to base_url if set)
            params: URL parameters
            data: Request body data
            json_data: JSON request body
            headers: Additional headers for this request
            timeout: Request timeout (overrides default)
            verify_ssl: Whether to verify SSL certificates (overrides default)
            
        Returns:
            requests.Response object
        """
        # Build URL
        url = endpoint
        if self.base_url:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Set timeout and SSL verification
        request_timeout = timeout if timeout is not None else self.timeout
        request_verify = verify_ssl if verify_ssl is not None else self.verify_ssl
        
        # Log request
        logger.debug(f"Making {method.value} request to {url}")
        
        start_time = time.time()
        try:
            response = self.session.request(
                method=method.value,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=request_timeout,
                verify=request_verify
            )
            
            # Log response
            elapsed = time.time() - start_time
            logger.debug(f"Received response from {url} in {elapsed:.2f}s: {response.status_code}")
            
            # Raise for status
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"Request to {url} failed after {elapsed:.2f}s: {str(e)}")
            raise
    
    async def async_request(self, 
                           method: RequestMethod, 
                           endpoint: str, 
                           params: Optional[Dict[str, Any]] = None,
                           data: Optional[Any] = None,
                           json_data: Optional[Dict[str, Any]] = None,
                           headers: Optional[Dict[str, str]] = None,
                           timeout: Optional[int] = None) -> aiohttp.ClientResponse:
        """
        Make an asynchronous HTTP request.
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint (will be appended to base_url if set)
            params: URL parameters
            data: Request body data
            json_data: JSON request body
            headers: Additional headers for this request
            timeout: Request timeout (overrides default)
            
        Returns:
            aiohttp.ClientResponse object
        """
        # Build URL
        url = endpoint
        if self.base_url:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Set timeout
        request_timeout = timeout if timeout is not None else self.timeout
        
        # Get async session
        session = await self._get_async_session()
        
        # Log request
        logger.debug(f"Making async {method.value} request to {url}")
        
        start_time = time.time()
        try:
            response = await session.request(
                method=method.value,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=request_timeout
            )
            
            # Log response
            elapsed = time.time() - start_time
            logger.debug(f"Received async response from {url} in {elapsed:.2f}s: {response.status}")
            
            # Check status
            if response.status >= 400:
                error_text = await response.text()
                logger.error(f"Request to {url} failed with status {response.status}: {error_text}")
                response.raise_for_status()
            
            return response
            
        except aiohttp.ClientError as e:
            elapsed = time.time() - start_time
            logger.error(f"Async request to {url} failed after {elapsed:.2f}s: {str(e)}")
            raise
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self.request(RequestMethod.GET, endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request."""
        return self.request(RequestMethod.POST, endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PUT request."""
        return self.request(RequestMethod.PUT, endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request."""
        return self.request(RequestMethod.DELETE, endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PATCH request."""
        return self.request(RequestMethod.PATCH, endpoint, **kwargs)
    
    async def async_get(self, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an async GET request."""
        return await self.async_request(RequestMethod.GET, endpoint, **kwargs)
    
    async def async_post(self, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an async POST request."""
        return await self.async_request(RequestMethod.POST, endpoint, **kwargs)
    
    async def async_put(self, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an async PUT request."""
        return await self.async_request(RequestMethod.PUT, endpoint, **kwargs)
    
    async def async_delete(self, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an async DELETE request."""
        return await self.async_request(RequestMethod.DELETE, endpoint, **kwargs)
    
    async def async_patch(self, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an async PATCH request."""
        return await self.async_request(RequestMethod.PATCH, endpoint, **kwargs)
    
    def close(self):
        """Close the synchronous session."""
        if self.session:
            self.session.close()
    
    async def async_close(self):
        """Close the asynchronous session."""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.async_close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
