"""Member-related MCP tools implementing YouTube Members API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register member-related tools with the MCP server"""
    
    @mcp.tool
    async def members_list(
        part: Annotated[List[str], Field(
            description="Member resource properties to include (snippet)"
        )],
        mode: Annotated[Optional[Literal["all_current", "updates"]], Field(
            default="all_current",
            description="List mode: all_current or updates"
        )] = "all_current",
        max_results: Annotated[Union[int, str], Field(
            default=20,
            description="Maximum number of items to return"
        )] = 20,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for specific results page"
        )] = None,
        filter_by_member_channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter by specific member's channel ID"
        )] = None,
        has_access_to_level: Annotated[Optional[str], Field(
            default=None,
            description="Filter by members with access to specific level ID"
        )] = None
    ) -> Dict[str, Any]:
        """
        List channel members (channel memberships).
        
        Requires OAuth authentication by the channel owner.
        Note: Access to this API requires approval from YouTube.
        Contact your YouTube representative for access.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=20)
            
            # Build request parameters
            params = {
                "part": ",".join(part),
                "mode": mode,
                "maxResults": max_results_int
            }
            
            # Add optional parameters
            if page_token:
                params["pageToken"] = page_token
            if filter_by_member_channel_id:
                params["filterByMemberChannelId"] = filter_by_member_channel_id
            if has_access_to_level:
                params["hasAccessToLevel"] = has_access_to_level
            
            # Make the API call
            response = await youtube_client.members_list(**params)
            
            return {
                "items": response.get("items", []),
                "nextPageToken": response.get("nextPageToken"),
                "pageInfo": response.get("pageInfo", {}),
                "totalResults": response.get("pageInfo", {}).get("totalResults", len(response.get("items", [])))
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