"""Configuration management for Donetick MCP server."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration for Donetick MCP server."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.donetick_base_url = os.getenv("DONETICK_BASE_URL")
        self.donetick_username = os.getenv("DONETICK_USERNAME")
        self.donetick_password = os.getenv("DONETICK_PASSWORD")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.rate_limit_per_second = float(os.getenv("RATE_LIMIT_PER_SECOND", "10.0"))
        self.rate_limit_burst = int(os.getenv("RATE_LIMIT_BURST", "10"))

        # Transport configuration
        self.transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
        self.host = os.getenv("MCP_HOST", "0.0.0.0")
        self.port = int(os.getenv("MCP_PORT", "8000"))

        # Stateless streamable HTTP: no session state between requests. Needed
        # behind aggregators and proxies that open a fresh session per call.
        self.stateless_http = os.getenv("MCP_STATELESS", "false").lower() in ("1", "true", "yes")

        # API token (Settings -> API tokens in Donetick, "dt_..."). Sent in the
        # `secretkey` header, which Donetick's multi-auth middleware accepts on
        # every /api/v1 route. Takes precedence over username/password.
        self.donetick_api_token = os.getenv("DONETICK_API_TOKEN")

        # Validate required configuration (skip if in test mode)
        if os.getenv("PYTEST_CURRENT_TEST") is None:
            self._validate()

    def _validate(self):
        """Validate that required configuration is present and secure."""
        errors = []
        warnings = []

        # Check base URL
        if not self.donetick_base_url:
            errors.append(
                "DONETICK_BASE_URL environment variable is required. "
                "Please set it to your Donetick instance URL."
            )
        else:
            # Allow HTTP for local/private network instances
            if not (self.donetick_base_url.startswith("https://") or
                    self.donetick_base_url.startswith("http://")):
                errors.append(
                    f"DONETICK_BASE_URL must use HTTP or HTTPS. "
                    f"Got: {self.donetick_base_url[:50]}"
                )

        # Username and password are only needed without an API token
        if not self.donetick_api_token and not self.donetick_username:
            errors.append(
                "DONETICK_USERNAME environment variable is required "
                "(or set DONETICK_API_TOKEN instead)."
            )

        if not self.donetick_api_token and not self.donetick_password:
            errors.append(
                "DONETICK_PASSWORD environment variable is required "
                "(or set DONETICK_API_TOKEN instead)."
            )

        # Log warnings
        if warnings:
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)

        # Raise all errors together
        if errors:
            raise ValueError(
                "Configuration validation failed:\n" +
                "\n".join(f"  - {error}" for error in errors)
            )

        # Normalize base URL (remove trailing slash)
        self.donetick_base_url = self.donetick_base_url.rstrip("/")

    def configure_logging(self):
        """Configure logging based on log level."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Global configuration instance
config = Config()
