"""Subscription-related MCP tools"""

from typing import Dict, Any, Optional, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register subscription-related tools with the MCP server"""
    
    @mcp.tool
    async def subscriptions_list_channel_subscriptions(
        channel_id: Annotated[str, Field(description="The YouTube channel ID to get subscriptions for")],
        max_results: Annotated[Union[int, str], Field(
            default=50,
            description="Maximum number of results to return"
        )] = 50,
        for_channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter subscriptions to only this channel ID"
        )] = None
    ) -> Dict[str, Any]:
        """List subscriptions for a specific channel"""
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=50)
            
            subscriptions = await youtube_client.list_subscriptions(
                channel_id=channel_id,
                max_results=max_results_int,
                for_channel_id=for_channel_id
            )
            
            return {
                "channelId": channel_id,
                "subscriptionCount": len(subscriptions),
                "subscriptions": subscriptions
            }
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }
    
    @mcp.tool
    async def subscriptions_list_my_subscriptions(
        max_results: Annotated[Union[int, str], Field(
            default=50,
            description="Maximum number of results to return"
        )] = 50,
        for_channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter subscriptions to only this channel ID"
        )] = None
    ) -> Dict[str, Any]:
        """List subscriptions for the authenticated user (requires OAuth)"""
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=50)
            
            subscriptions = await youtube_client.list_subscriptions(
                mine=True,
                max_results=max_results_int,
                for_channel_id=for_channel_id
            )
            
            return {
                "subscriptionCount": len(subscriptions),
                "subscriptions": subscriptions
            }
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }
    
    @mcp.tool
    async def subscriptions_list_my_recent_subscribers(
        max_results: Annotated[Union[int, str], Field(
            default=50,
            description="Maximum number of results to return"
        )] = 50
    ) -> Dict[str, Any]:
        """List recent subscribers to the authenticated user's channel (requires OAuth)"""
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=50)
            
            subscribers = await youtube_client.list_recent_subscribers(
                max_results=max_results_int
            )
            
            return {
                "subscriberCount": len(subscribers),
                "subscribers": subscribers
            }
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }
    
    @mcp.tool
    async def subscriptions_insert(
        channel_id: Annotated[str, Field(description="The YouTube channel ID to subscribe to")]
    ) -> Dict[str, Any]:
        """Subscribe to a YouTube channel (requires OAuth authentication)"""
        try:
            result = await youtube_client.insert_subscription(channel_id)
            return result
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }
    
    @mcp.tool
    async def subscriptions_delete(
        subscription_id: Annotated[str, Field(description="The YouTube subscription ID to delete")]
    ) -> Dict[str, Any]:
        """Delete a YouTube subscription (requires OAuth authentication)"""
        try:
            result = await youtube_client.delete_subscription(subscription_id)
            return result
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }