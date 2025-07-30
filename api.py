from __future__ import annotations
import logging
from aiohttp import (
    ClientSession,
    ClientTimeout,
    ClientError,
    ClientResponseError,
    ClientConnectorError,
    ContentTypeError,
    ServerTimeoutError
)
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)

class KarakeepClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        session: ClientSession,
        timeout: Optional[int] = 15
    ):
        """Initialize the Karakeep API client.
        
        Args:
            base_url: Base URL of the Karakeep API
            token: Authentication token
            session: aiohttp ClientSession
            timeout: Request timeout in seconds (default: 15)
        """
        self._url = base_url.rstrip("/")
        self._token = token
        self._session = session
        self._timeout = ClientTimeout(total=timeout)
        
        _LOGGER.debug(
            "Initialized KarakeepClient with base URL: %s, timeout: %s seconds",
            self._url,
            timeout
        )

    async def async_get_stats(self) -> dict[str, Any]:
        """Return /users/me/stats response.
        
        Returns:
            Dictionary containing user statistics
            
        Raises:
            ClientResponseError: If the API returns an error status code
            ClientConnectorError: If connection to the API fails
            ContentTypeError: If the response is not valid JSON
            ServerTimeoutError: If the API request times out
            ClientError: For other aiohttp client errors
            Exception: For any other unexpected errors
        """
        endpoint = f"{self._url}/api/v1/users/me/stats"
        headers = {"Authorization": f"Bearer {self._token[:5]}...{self._token[-5:] if len(self._token) > 10 else ''}"}
        
        _LOGGER.debug(
            "Preparing request to Karakeep API endpoint: %s with headers: %s",
            endpoint,
            headers
        )

        try:
            _LOGGER.debug("Sending GET request to Karakeep API: %s", endpoint)
            async with self._session.get(
                endpoint,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self._timeout
            ) as resp:
                _LOGGER.debug(
                    "Received response from Karakeep API with status: %s, content-type: %s",
                    resp.status,
                    resp.headers.get("content-type", "unknown")
                )
                
                resp.raise_for_status()
                _LOGGER.debug("Response status code is valid, parsing JSON response")
                
                data = await resp.json()
                _LOGGER.debug(
                    "Successfully retrieved stats from Karakeep API, data keys: %s",
                    ", ".join(data.keys()) if isinstance(data, dict) else "not a dictionary"
                )
                return data
                
        except ClientResponseError as err:
            _LOGGER.debug(
                "ClientResponseError details - Method: %s, URL: %s, Status: %s, Message: %s, Headers: %s",
                err.request_info.method if hasattr(err, 'request_info') else "unknown",
                err.request_info.url if hasattr(err, 'request_info') else "unknown",
                err.status,
                err.message,
                err.headers if hasattr(err, 'headers') else "unknown"
            )
            _LOGGER.error(
                "HTTP error when accessing Karakeep API: %s - %s",
                err.status, err.message
            )
            raise
            
        except ClientConnectorError as err:
            _LOGGER.debug(
                "ClientConnectorError details - Host: %s, Port: %s, SSL: %s",
                getattr(err, 'host', 'unknown'),
                getattr(err, 'port', 'unknown'),
                getattr(err, 'ssl', 'unknown')
            )
            _LOGGER.error(
                "Connection error when accessing Karakeep API: %s",
                str(err)
            )
            raise
            
        except ContentTypeError as err:
            _LOGGER.debug(
                "ContentTypeError details - Expected content type: application/json"
            )
            _LOGGER.error(
                "Invalid response format from Karakeep API: %s",
                str(err)
            )
            raise
            
        except ServerTimeoutError as err:
            _LOGGER.debug(
                "ServerTimeoutError details - Timeout settings: %s seconds",
                self._timeout.total
            )
            _LOGGER.error(
                "Timeout when accessing Karakeep API (timeout=%s seconds): %s",
                self._timeout.total, str(err)
            )
            raise
            
        except ClientError as err:
            _LOGGER.debug(
                "ClientError details - Type: %s",
                type(err).__name__
            )
            _LOGGER.error(
                "Error accessing Karakeep API: %s",
                str(err)
            )
            raise
            
        except Exception as err:
            _LOGGER.debug(
                "Unexpected exception details - Type: %s",
                type(err).__name__
            )
            _LOGGER.exception(
                "Unexpected error when accessing Karakeep API: %s",
                str(err)
            )
            raise
