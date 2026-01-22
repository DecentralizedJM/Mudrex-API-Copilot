"""
MCP Tools definitions for Mudrex API
Based on official Mudrex MCP documentation: https://docs.trade.mudrex.com/docs/mcp

Copyright (c) 2025 DecentralizedJM
Licensed under MIT License
"""
from typing import Dict, Any, List
from enum import Enum


class ToolSafety(Enum):
    """Tool safety classification"""
    SAFE = "safe"  # Read-only, no confirmation needed
    REQUIRES_CONFIRMATION = "confirmation"  # Modifies account, needs user confirmation


class MudrexTools:
    """
    Defines available Mudrex MCP tools
    Source: https://docs.trade.mudrex.com/docs/mcp
    """
    
    # ==================== SAFE TOOLS (Read-Only) ====================
    # These can be called freely by the bot
    
    SAFE_TOOLS = {
        # Orders (read)
        'get_orders': {
            'description': 'List all open orders on your account',
            'parameters': {},
            'example': 'Show all my open orders'
        },
        'get_order': {
            'description': 'Fetch a specific order by order_id',
            'parameters': {'order_id': 'string'},
            'example': 'Get details for order #12345'
        },
        'get_order_history': {
            'description': 'Get historical orders',
            'parameters': {},
            'example': 'Show my order history for the last 30 days'
        },
        
        # Positions (read)
        'get_positions': {
            'description': 'List all open positions on your account',
            'parameters': {},
            'example': 'Show all my open positions on Mudrex'
        },
        'get_position_history': {
            'description': 'Get historical positions',
            'parameters': {},
            'example': 'Show my closed positions history'
        },
        
        # Risk Management (read)
        'get_liquidation_price': {
            'description': 'Compute liquidation price for a position',
            'parameters': {'symbol': 'string'},
            'example': 'What is the liquidation price for my ETH/USDT position?'
        },
        
        # Leverage (read)
        'get_leverage': {
            'description': 'Get current leverage for a contract',
            'parameters': {'symbol': 'string'},
            'example': 'What is my current leverage on ETH/USDT?'
        },
        
        # Markets & Account
        'list_futures': {
            'description': 'List all available futures contracts on Mudrex',
            'parameters': {},
            'example': 'List all available futures contracts on Mudrex'
        },
        'get_future': {
            'description': 'Get details for a specific contract (by id or symbol)',
            'parameters': {'symbol': 'string'},
            'example': 'Get details for the BTC/USDT futures contract'
        },
        'get_available_funds': {
            'description': 'Get available funds for trading',
            'parameters': {},
            'example': 'How much available balance do I have for futures trading?'
        },
        'get_fee_history': {
            'description': 'Get trading fee history',
            'parameters': {},
            'example': 'Show my trading fee history'
        },
    }
    
    # ==================== CONFIRMATION REQUIRED TOOLS ====================
    # These modify the account and need explicit user confirmation
    
    CONFIRMATION_TOOLS = {
        # Orders (write)
        'place_order': {
            'description': 'Place LONG/SHORT order (optionally attach SL/TP)',
            'parameters': {
                'symbol': 'string (e.g., ETH/USDT)',
                'side': 'LONG or SHORT',
                'amount': 'USDT amount',
                'leverage': 'integer (e.g., 5)',
                'stop_loss': 'optional percentage',
                'take_profit': 'optional percentage'
            },
            'example': 'Place a LONG order on ETH/USDT for 200 USDT with 5x leverage'
        },
        'amend_order': {
            'description': 'Amend an existing order (price / SL / TP)',
            'parameters': {'order_id': 'string', 'changes': 'object'},
            'example': 'Amend my XRP/USDT order to move stop loss to 1.5% above entry'
        },
        'cancel_order': {
            'description': 'Cancel an order',
            'parameters': {'order_id': 'string'},
            'example': 'Cancel my open XRP/USDT order'
        },
        
        # Positions (write)
        'close_position': {
            'description': 'Close a position at market price',
            'parameters': {'symbol': 'string'},
            'example': 'Close my BTC/USDT position at market price'
        },
        'reverse_position': {
            'description': 'Reverse a position (flip long to short or vice versa)',
            'parameters': {'symbol': 'string'},
            'example': 'Reverse my ETH/USDT position'
        },
        
        # Risk Management (write)
        'place_risk_order': {
            'description': 'Place stop-loss / take-profit on a position',
            'parameters': {
                'symbol': 'string',
                'stop_loss': 'percentage',
                'take_profit': 'percentage'
            },
            'example': 'Add a stop loss at 2% and take profit at 5% to my XRP/USDT position'
        },
        'amend_risk_order': {
            'description': 'Amend stop-loss / take-profit on a position',
            'parameters': {'symbol': 'string', 'changes': 'object'},
            'example': 'Move my ETH/USDT take profit to 6%'
        },
        
        # Leverage & Margin (write)
        'set_leverage': {
            'description': 'Set leverage for a contract',
            'parameters': {'symbol': 'string', 'leverage': 'integer'},
            'example': 'Set leverage to 10x for ETH/USDT'
        },
        'add_margin': {
            'description': 'Add margin to a position',
            'parameters': {'symbol': 'string', 'amount': 'USDT'},
            'example': 'Add 100 USDT margin to my ETH/USDT position'
        },
    }
    
    @classmethod
    def get_safe_tools(cls) -> Dict[str, Dict]:
        """Get all safe (read-only) tools"""
        return cls.SAFE_TOOLS
    
    @classmethod
    def get_confirmation_tools(cls) -> Dict[str, Dict]:
        """Get all tools that require confirmation"""
        return cls.CONFIRMATION_TOOLS
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, Dict]:
        """Get all tools"""
        all_tools = {}
        all_tools.update(cls.SAFE_TOOLS)
        all_tools.update(cls.CONFIRMATION_TOOLS)
        return all_tools
    
    @classmethod
    def is_safe_tool(cls, name: str) -> bool:
        """Check if a tool is safe (read-only)"""
        return name in cls.SAFE_TOOLS
    
    @classmethod
    def requires_confirmation(cls, name: str) -> bool:
        """Check if a tool requires user confirmation"""
        return name in cls.CONFIRMATION_TOOLS
    
    @classmethod
    def get_tool_info(cls, name: str) -> Dict[str, Any] | None:
        """Get info for a specific tool"""
        if name in cls.SAFE_TOOLS:
            return {**cls.SAFE_TOOLS[name], 'safety': ToolSafety.SAFE}
        if name in cls.CONFIRMATION_TOOLS:
            return {**cls.CONFIRMATION_TOOLS[name], 'safety': ToolSafety.REQUIRES_CONFIRMATION}
        return None
    
    @classmethod
    def get_tools_summary(cls) -> str:
        """Get a formatted summary of all tools for display"""
        lines = ["*Mudrex MCP Tools*\n"]
        
        lines.append("*Safe Tools (Read-Only):*")
        for name, info in cls.SAFE_TOOLS.items():
            lines.append(f"• `{name}` - {info['description']}")
        
        lines.append("\n*Confirmation Required:*")
        for name, info in cls.CONFIRMATION_TOOLS.items():
            lines.append(f"• `{name}` - {info['description']}")
        
        return "\n".join(lines)
    
    @classmethod
    def get_safe_tools_summary(cls) -> str:
        """Get summary of safe tools only"""
        lines = ["*Available Tools (Read-Only):*\n"]
        
        categories = {
            'Orders': ['get_orders', 'get_order', 'get_order_history'],
            'Positions': ['get_positions', 'get_position_history', 'get_liquidation_price'],
            'Markets': ['list_futures', 'get_future', 'get_leverage'],
            'Account': ['get_available_funds', 'get_fee_history'],
        }
        
        for category, tools in categories.items():
            lines.append(f"*{category}:*")
            for tool in tools:
                if tool in cls.SAFE_TOOLS:
                    lines.append(f"• `{tool}` - {cls.SAFE_TOOLS[tool]['description']}")
            lines.append("")
        
        return "\n".join(lines)
