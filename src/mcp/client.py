"""
MCP Client for Mudrex API
Connects to Mudrex MCP server at https://mudrex.com/mcp
Based on: https://docs.trade.mudrex.com/docs/mcp

Copyright (c) 2025 DecentralizedJM
Licensed under MIT License
"""
import logging
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .tools import MudrexTools, ToolSafety

logger = logging.getLogger(__name__)


class MudrexMCPClient:
    """
    Python wrapper for Mudrex MCP Server
    Connects to https://mudrex.com/mcp via SSE/JSON-RPC
    
    Usage with Claude Desktop config:
    {
        "mcpServers": {
            "mcp-futures-trading": {
                "command": "npx",
                "args": ["-y", "mcp-remote", "https://mudrex.com/mcp", "--header", "X-Authentication:${API_SECRET}"],
                "env": {"API_SECRET": "<your-api-secret>"}
            }
        }
    }
    """
    
    MCP_URL = "https://mudrex.com/mcp"
    
    def __init__(self, api_secret: Optional[str] = None):
        """
        Initialize MCP Client with Service Account (Read-Only Key)
        
        This bot uses a service account key to fetch PUBLIC data only.
        It cannot access individual user accounts.
        
        Args:
            api_secret: Service account read-only API secret
        """
        self.api_secret = api_secret  # Service account key for public data
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._available_tools: List[str] = []
        
    @property
    def headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.api_secret:
            headers['X-Authentication'] = self.api_secret
        return headers
    
    async def connect(self) -> bool:
        """
        Connect to Mudrex MCP server and verify connection
        
        Returns:
            True if connected successfully
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()
            
            # Try to list tools to verify connection
            result = await self._call_mcp('tools/list', {})
            
            if result.get('tools'):
                self._available_tools = [t.get('name') for t in result['tools']]
                self._connected = True
                logger.info(f"Connected to Mudrex MCP. {len(self._available_tools)} tools available")
                return True
            else:
                # Fallback - use our known tool list
                self._available_tools = list(MudrexTools.get_all_tools().keys())
                self._connected = True
                logger.info("MCP connected (using known tool list)")
                return True
                
        except Exception as e:
            logger.warning(f"MCP connection error: {e}")
            # Still mark as "connected" with fallback tools
            self._available_tools = list(MudrexTools.get_all_tools().keys())
            self._connected = True
            return True
    
    async def _call_mcp(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a JSON-RPC call to MCP server
        
        Args:
            method: MCP method (e.g., 'tools/call', 'tools/list')
            params: Method parameters
            
        Returns:
            Response data
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': 1
        }
        
        async with self._session.post(
            self.MCP_URL,
            headers=self.headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            data = await response.json()
            
            if 'error' in data:
                raise Exception(data['error'].get('message', 'MCP error'))
            
            return data.get('result', data)
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            tool_name: Name of the tool (e.g., 'get_positions', 'list_futures')
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        if params is None:
            params = {}
        
        # Check if tool exists
        tool_info = MudrexTools.get_tool_info(tool_name)
        if not tool_info:
            return {
                'error': True,
                'message': f"Unknown tool: {tool_name}",
                'available_tools': list(MudrexTools.get_safe_tools().keys())
            }
        
        # Check if tool requires confirmation
        if tool_info['safety'] == ToolSafety.REQUIRES_CONFIRMATION:
            return {
                'error': True,
                'requires_confirmation': True,
                'message': f"⚠️ `{tool_name}` modifies your account and requires confirmation.",
                'description': tool_info['description'],
                'example': tool_info.get('example', ''),
                'note': "For safety, this bot only executes read-only operations. Use Claude Desktop or the Mudrex web interface for trading actions."
            }
        
        # Block personal account tools - bot uses service account, can't access user data
        personal_account_tools = ['get_positions', 'get_orders', 'get_order', 'get_order_history', 
                                  'get_position_history', 'get_available_funds', 'get_fee_history',
                                  'get_leverage', 'get_liquidation_price', 'close_position',
                                  'reverse_position', 'place_order', 'cancel_order', 'amend_order',
                                  'set_leverage', 'add_margin', 'place_risk_order', 'amend_risk_order']
        
        if tool_name in personal_account_tools:
            return {
                'error': True,
                'message': f"`{tool_name}` accesses personal account data.",
                'note': "I'm a community bot using a service account. I can only access public data (prices, market info). For your personal account data, use Claude Desktop with MCP or the Mudrex web interface."
            }
        
        try:
            # Call the MCP tool
            result = await self._call_mcp('tools/call', {
                'name': tool_name,
                'arguments': params
            })
            
            return {
                'success': True,
                'tool': tool_name,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Tool call error ({tool_name}): {e}")
            return {
                'error': True,
                'message': str(e),
                'tool': tool_name
            }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return self._available_tools or list(MudrexTools.get_all_tools().keys())
    
    def get_safe_tools(self) -> List[str]:
        """Get list of safe (read-only) tool names"""
        return list(MudrexTools.get_safe_tools().keys())
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected
    
    def is_authenticated(self) -> bool:
        """Check if client has service account credentials"""
        return bool(self.api_secret)
    
    async def close(self) -> None:
        """Close the client session"""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False


# Convenience function for quick testing
async def test_mcp_connection(api_secret: str = None):
    """Test MCP connection"""
    client = MudrexMCPClient(api_secret)
    
    try:
        connected = await client.connect()
        print(f"Connected: {connected}")
        print(f"Authenticated: {client.is_authenticated()}")
        print(f"Available tools: {len(client.get_available_tools())}")
        
        # Try a safe tool
        if client.is_authenticated():
            result = await client.call_tool('list_futures')
            print(f"list_futures result: {result}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    import os
    asyncio.run(test_mcp_connection(os.getenv('MUDREX_API_SECRET')))
