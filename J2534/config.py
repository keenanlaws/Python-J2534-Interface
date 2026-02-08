"""
J2534 Configuration Module
==========================

This module provides centralized configuration for the J2534 library,
including debug output control and error handling mode selection.

The configuration uses a singleton pattern to ensure consistent behavior
across all modules in the library. Changes to the configuration take
effect immediately for all subsequent operations.

Configuration Options:
    debug_enabled: When True, detailed debug information is logged
        to help diagnose communication issues. When False (default),
        only errors are logged.

    raise_exceptions: When True, functions raise J2534Exception subclasses
        on errors, providing detailed error information. When False (default),
        functions return False or None on errors, allowing for simpler
        error checking in scripts.

Example:
    Basic configuration for debugging::

        from J2534.config import j2534_config

        # Enable verbose debug output
        j2534_config.enable_debug()

        # Enable exception-based error handling
        j2534_config.enable_exceptions()

        # Check current settings
        if j2534_config.debug_enabled:
            print("Debug mode is active")

Example:
    Production configuration (silent errors)::

        from J2534.config import j2534_config

        # Disable debug output for production
        j2534_config.disable_debug()

        # Use return-value error handling
        j2534_config.disable_exceptions()

        # Now functions return False on error instead of raising
        device_id = pt_open()
        if device_id is False:
            print("Failed to open device")

Architecture:
    This module is imported by all other J2534 modules. The configuration
    singleton is created on first import and shared across the entire
    library. This ensures consistent behavior regardless of which module
    is used first.

    Import hierarchy::

        config.py (this module)
            ^
            |
        exceptions.py, logging_utils.py
            ^
            |
        structures.py, constants.py
            ^
            |
        dll_interface.py
            ^
            |
        api.py
            ^
            |
        __init__.py (public API)

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

import logging
from typing import Optional


class J2534Configuration:
    """
    Singleton configuration class for J2534 library behavior.

    This class manages global settings that control how the J2534 library
    operates. It uses the singleton pattern to ensure only one configuration
    instance exists throughout the application lifetime.

    The configuration provides two main behavior switches:

    1. Debug Mode (debug_enabled):
       Controls whether detailed debug information is logged during
       J2534 operations. Useful for diagnosing communication issues.

    2. Exception Mode (raise_exceptions):
       Controls error handling behavior. When enabled, functions raise
       descriptive exceptions on errors. When disabled, functions return
       False or None on errors.

    Attributes:
        debug_enabled (bool): Read-only property indicating if debug
            output is enabled. Use enable_debug() and disable_debug()
            to change this setting.
        raise_exceptions (bool): Read-only property indicating if
            exception-based error handling is enabled. Use
            enable_exceptions() and disable_exceptions() to change.
        logger (logging.Logger): The logger instance used for debug
            output. Can be customized if needed.

    Example:
        >>> from J2534.config import j2534_config
        >>>
        >>> # Enable debug mode for troubleshooting
        >>> j2534_config.enable_debug()
        >>> print(f"Debug enabled: {j2534_config.debug_enabled}")
        Debug enabled: True
        >>>
        >>> # Switch to exception-based error handling
        >>> j2534_config.enable_exceptions()
        >>> print(f"Exceptions enabled: {j2534_config.raise_exceptions}")
        Exceptions enabled: True

    Note:
        The singleton instance is automatically created when this module
        is imported. Access it via the module-level `j2534_config` variable.
    """

    # Class-level variable to hold the singleton instance
    _instance: Optional['J2534Configuration'] = None

    def __new__(cls) -> 'J2534Configuration':
        """
        Create or return the singleton configuration instance.

        This method ensures only one J2534Configuration instance exists.
        Subsequent calls to J2534Configuration() return the same instance.

        Returns:
            J2534Configuration: The singleton configuration instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Initialize the configuration with default values.

        This method is called only once when the singleton is first created.
        It sets up the default configuration state:
        - Debug output disabled
        - Exception-based error handling disabled (return False on errors)
        - Logger configured for the J2534 namespace

        Note:
            This is a private method called automatically during singleton
            creation. Do not call it directly.
        """
        # Debug mode: when True, detailed logging is enabled
        self._debug_enabled: bool = False

        # Exception mode: when True, errors raise exceptions instead of returning False
        self._raise_exceptions: bool = False

        # Logger for debug output - uses the J2534 namespace for filtering
        self._logger: logging.Logger = logging.getLogger('J2534')

        # Set up a default handler if none exists
        # This prevents "No handler found" warnings
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        # Default to WARNING level (debug messages hidden until enabled)
        self._logger.setLevel(logging.WARNING)

    # =========================================================================
    # Debug Mode Control
    # =========================================================================

    @property
    def debug_enabled(self) -> bool:
        """
        Check if debug mode is currently enabled.

        When debug mode is enabled, the library logs detailed information
        about J2534 operations including:
        - Function calls with parameters
        - Return values and status codes
        - Timing information
        - Raw message data in hex format

        Returns:
            bool: True if debug mode is enabled, False otherwise.

        Example:
            >>> if j2534_config.debug_enabled:
            ...     print("Debug logging is active")
        """
        return self._debug_enabled

    def enable_debug(self) -> None:
        """
        Enable debug mode for detailed logging output.

        When debug mode is enabled:
        - All J2534 function calls are logged with their parameters
        - Return values and error codes are logged
        - Message data is displayed in hex format
        - Timing information may be included

        Debug output is written to the J2534 logger, which by default
        outputs to stderr. You can customize the logger by accessing
        j2534_config.logger.

        Example:
            >>> from J2534.config import j2534_config
            >>> j2534_config.enable_debug()
            >>> # Now all J2534 operations will be logged
            >>> device_id = pt_open()  # This will log the operation

        See Also:
            disable_debug: Turn off debug logging
            logger: Access the logger for customization
        """
        self._debug_enabled = True
        self._logger.setLevel(logging.DEBUG)

    def disable_debug(self) -> None:
        """
        Disable debug mode to suppress detailed logging.

        When debug mode is disabled (the default), only warnings and
        errors are logged. This is recommended for production use to
        reduce log noise and improve performance.

        Example:
            >>> from J2534.config import j2534_config
            >>> j2534_config.disable_debug()
            >>> # Now only warnings and errors are logged

        See Also:
            enable_debug: Turn on debug logging
        """
        self._debug_enabled = False
        self._logger.setLevel(logging.WARNING)

    # =========================================================================
    # Exception Mode Control
    # =========================================================================

    @property
    def raise_exceptions(self) -> bool:
        """
        Check if exception-based error handling is enabled.

        When exception mode is enabled, J2534 functions raise specific
        exception classes (from J2534.exceptions) when errors occur.
        This allows for detailed error information and stack traces.

        When exception mode is disabled (the default), functions return
        False or None on errors. This allows for simpler error checking
        in scripts but provides less detail about what went wrong.

        Returns:
            bool: True if exceptions are raised on errors, False if
                functions return False/None on errors.

        Example:
            >>> if j2534_config.raise_exceptions:
            ...     try:
            ...         device_id = pt_open()
            ...     except J2534OpenError as e:
            ...         print(f"Open failed: {e}")
            ... else:
            ...     device_id = pt_open()
            ...     if device_id is False:
            ...         print("Open failed")
        """
        return self._raise_exceptions

    def enable_exceptions(self) -> None:
        """
        Enable exception-based error handling.

        When exceptions are enabled, J2534 functions will raise specific
        exception classes when errors occur. This provides:
        - Detailed error messages
        - J2534 error codes
        - Stack traces for debugging
        - Ability to catch specific error types

        Exception classes (from J2534.exceptions):
        - J2534OpenError: Device open failed
        - J2534CloseError: Device close failed
        - J2534ConnectError: Channel connection failed
        - J2534DisconnectError: Channel disconnect failed
        - J2534ReadError: Message read failed
        - J2534WriteError: Message write failed
        - J2534FilterError: Filter operation failed
        - J2534IoctlError: IOCTL operation failed

        Example:
            >>> from J2534.config import j2534_config
            >>> from J2534.exceptions import J2534OpenError
            >>>
            >>> j2534_config.enable_exceptions()
            >>>
            >>> try:
            ...     device_id = pt_open()
            ... except J2534OpenError as error:
            ...     print(f"Failed to open device: {error}")
            ...     print(f"Error code: {error.error_code}")

        See Also:
            disable_exceptions: Switch to return-value error handling
            J2534.exceptions: Module containing all exception classes
        """
        self._raise_exceptions = True

    def disable_exceptions(self) -> None:
        """
        Disable exception-based error handling (use return values).

        When exceptions are disabled (the default), J2534 functions
        return False or None when errors occur instead of raising
        exceptions. This simplifies error checking in scripts:

        - Functions that return IDs (device_id, channel_id, filter_id)
          return False on error
        - Functions that return data return None on error
        - Functions that return status codes return the error code

        This mode is useful for:
        - Simple scripts where detailed errors aren't needed
        - Compatibility with existing code
        - Avoiding try/except blocks for every call

        Example:
            >>> from J2534.config import j2534_config
            >>>
            >>> j2534_config.disable_exceptions()
            >>>
            >>> device_id = pt_open()
            >>> if device_id is False:
            ...     error_message = pt_get_last_error()
            ...     print(f"Open failed: {error_message}")

        See Also:
            enable_exceptions: Switch to exception-based error handling
        """
        self._raise_exceptions = False

    # =========================================================================
    # Logger Access
    # =========================================================================

    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger instance used for J2534 debug output.

        You can use this property to customize logging behavior:
        - Add additional handlers (file output, network logging)
        - Change the log format
        - Filter log messages

        Returns:
            logging.Logger: The logger instance for the J2534 namespace.

        Example:
            >>> import logging
            >>> from J2534.config import j2534_config
            >>>
            >>> # Add file handler for persistent logs
            >>> file_handler = logging.FileHandler('j2534_debug.log')
            >>> j2534_config.logger.addHandler(file_handler)
            >>>
            >>> # Change log format
            >>> formatter = logging.Formatter('%(levelname)s: %(message)s')
            >>> for handler in j2534_config.logger.handlers:
            ...     handler.setFormatter(formatter)
        """
        return self._logger

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def reset_to_defaults(self) -> None:
        """
        Reset all configuration options to their default values.

        This method restores the configuration to its initial state:
        - Debug mode disabled
        - Exception mode disabled
        - Logger level set to WARNING

        Useful for testing or when you need to ensure a known state.

        Example:
            >>> from J2534.config import j2534_config
            >>>
            >>> # Make some changes
            >>> j2534_config.enable_debug()
            >>> j2534_config.enable_exceptions()
            >>>
            >>> # Reset everything
            >>> j2534_config.reset_to_defaults()
            >>> print(j2534_config.debug_enabled)  # False
            >>> print(j2534_config.raise_exceptions)  # False
        """
        self._debug_enabled = False
        self._raise_exceptions = False
        self._logger.setLevel(logging.WARNING)

    def __repr__(self) -> str:
        """
        Return a string representation of the current configuration.

        Returns:
            str: A human-readable description of the configuration state.

        Example:
            >>> print(j2534_config)
            J2534Configuration(debug_enabled=False, raise_exceptions=False)
        """
        return (
            f"J2534Configuration("
            f"debug_enabled={self._debug_enabled}, "
            f"raise_exceptions={self._raise_exceptions})"
        )


# =============================================================================
# Module-Level Singleton Instance
# =============================================================================

# Create the global configuration instance
# This is the primary way to access configuration throughout the library
j2534_config: J2534Configuration = J2534Configuration()
"""
Global J2534 configuration instance.

This singleton instance provides access to all J2534 library configuration
options. Import and use it directly:

    from J2534.config import j2534_config

    j2534_config.enable_debug()
    j2534_config.enable_exceptions()

See J2534Configuration class documentation for available options.
"""
