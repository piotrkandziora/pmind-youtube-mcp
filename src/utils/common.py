"""Common utility functions for MCP tools"""

from typing import Union, Optional


def parse_bool_param(value: Union[bool, str, None]) -> Optional[bool]:
    """Parse boolean parameter that might come as string from MCP client
    
    The MCP client sometimes sends boolean values as strings ("true"/"false")
    instead of actual boolean types. This function handles both cases.
    
    Args:
        value: Boolean, string representation of boolean, or None
        
    Returns:
        Parsed boolean value or None
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return None


def parse_int_param(value: Union[int, str, None], default: Optional[int] = None) -> Optional[int]:
    """Parse integer parameter that might come as string from MCP client
    
    The MCP client sometimes sends numeric values as strings ("10", "50")
    instead of actual integer types. This function handles both cases.
    
    Args:
        value: Integer, string representation of integer, or None
        default: Default value to return if value is None
        
    Returns:
        Parsed integer value, default, or None
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default