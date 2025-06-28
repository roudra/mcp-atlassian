#!/usr/bin/env python3
"""
Cookie-Enhanced MCP Server
A simplified MCP server that uses cookie authentication
"""

import json
import sys
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Import the cookie reader and manager
from advanced_cookie_reader import CookieJSONReader
from convention_based_manager import ConventionBasedManager

# Set up logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Simplified MCP Server with cookie authentication"""
    
    def __init__(self):
        self.manager: Optional[ConventionBasedManager] = None
        self.cookie_reader: Optional[CookieJSONReader] = None
        self.initialized = False
        
    def initialize_manager(self):
        """Initialize the cookie-based manager"""
        try:
            # Check for cookie file configuration
            cookie_file = os.getenv('JIRA_COOKIE_FILE', 'production_cookies.json')
            config_file = os.getenv('JIRA_CONFIG_FILE', 'jira_config.json')
            
            logger.info(f"Initializing with cookie file: {cookie_file}")
            logger.info(f"Using config file: {config_file}")
            
            # Initialize cookie reader
            if Path(cookie_file).exists():
                self.cookie_reader = CookieJSONReader(cookie_file)
                if self.cookie_reader.read_file():
                    logger.info("✅ Cookie file loaded successfully")
                else:
                    logger.error("❌ Failed to load cookie file")
                    return False
            else:
                logger.error(f"❌ Cookie file not found: {cookie_file}")
                return False
            
            # Initialize the convention-based manager
            self.manager = ConventionBasedManager()
            
            # Test connection
            if self.manager.test_connection():
                logger.info("✅ Cookie-based connection established")
                self.initialized = True
                return True
            else:
                logger.error("❌ Cookie-based connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize cookie manager: {e}")
            return False
    
    def handle_initialize(self, request):
        """Handle MCP initialize request"""
        success = self.initialize_manager()
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "mcp-atlassian-cookie",
                    "version": "1.0.0"
                }
            }
        }
    
    def handle_list_tools(self, request):
        """Handle tools/list request"""
        if not self.initialized or not self.manager:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": []}
            }
        
        tools = []
        if hasattr(self.manager, 'tools'):
            for tool_name in self.manager.tools:
                tools.append({
                    "name": tool_name,
                    "description": f"Execute {tool_name} with cookie authentication",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True
                    }
                })
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"tools": tools}
        }
    
    def handle_call_tool(self, request):
        """Handle tools/call request"""
        if not self.initialized or not self.manager:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -1,
                    "message": "Server not initialized"
                }
            }
        
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # Use the convention-based manager to execute the tool
            result = self.manager.run_tool(tool_name, arguments)
            
            if isinstance(result, dict):
                result_text = json.dumps(result, indent=2)
            else:
                result_text = str(result)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -1,
                    "message": f"Error executing {tool_name}: {str(e)}"
                }
            }
    
    def handle_request(self, request):
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        
        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "tools/list":
            return self.handle_list_tools(request)
        elif method == "tools/call":
            return self.handle_call_tool(request)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Cookie-Enhanced MCP Server")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    
                    if response:
                        print(json.dumps(response), flush=True)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    
        except KeyboardInterrupt:
            logger.info("👋 Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point"""
    server = SimpleMCPServer()
    server.run()

if __name__ == "__main__":
    main()
