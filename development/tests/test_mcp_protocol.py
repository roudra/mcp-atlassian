#!/usr/bin/env python3
"""
Test MCP protocol directly
"""

import json
import subprocess
import sys
import os

def test_mcp_server():
    """Test the MCP server directly"""
    
    server_path = "/Users/arduor/Project/mcp-atlassian/consolidated/mcp_atlassian_extended.py"
    
    print("🧪 Testing MCP Server Protocol...")
    
    # Test 1: Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    try:
        process = subprocess.Popen(
            ["python3", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send initialize request
        stdout, stderr = process.communicate(
            input=json.dumps(init_request) + "\n",
            timeout=10
        )
        
        print("📤 Sent initialize request")
        print("📥 Response:", stdout[:200] + "..." if len(stdout) > 200 else stdout)
        
        if stderr:
            print("⚠️  Stderr:", stderr[:200] + "..." if len(stderr) > 200 else stderr)
        
        # Check if response is valid JSON
        try:
            response = json.loads(stdout.strip())
            if "result" in response:
                print("✅ Server initialized successfully!")
                
                # Check tools
                if "capabilities" in response["result"]:
                    caps = response["result"]["capabilities"]
                    if "tools" in caps:
                        print(f"🔧 Server reports tools capability")
                    else:
                        print("⚠️  No tools capability reported")
                else:
                    print("⚠️  No capabilities in response")
            else:
                print("❌ No result in response")
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            
    except subprocess.TimeoutExpired:
        print("❌ Server timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error: {e}")

def test_tools_list():
    """Test tools/list endpoint"""
    
    server_path = "/Users/arduor/Project/mcp-atlassian/consolidated/mcp_atlassian_extended.py"
    
    print("\n🔧 Testing Tools List...")
    
    # Test tools/list
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        process = subprocess.Popen(
            ["python3", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send tools/list request
        stdout, stderr = process.communicate(
            input=json.dumps(tools_request) + "\n",
            timeout=10
        )
        
        print("📤 Sent tools/list request")
        
        if stderr:
            print("⚠️  Stderr:", stderr[:200] + "..." if len(stderr) > 200 else stderr)
        
        # Check if response contains tools
        try:
            response = json.loads(stdout.strip())
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                print(f"✅ Found {len(tools)} tools!")
                
                # Show first few tools
                for i, tool in enumerate(tools[:5]):
                    print(f"  {i+1}. {tool.get('name', 'Unknown')}")
                
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more tools")
                    
            else:
                print("❌ No tools found in response")
                print("Response:", stdout[:300])
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print("Raw output:", stdout[:300])
            
    except subprocess.TimeoutExpired:
        print("❌ Server timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mcp_server()
    test_tools_list()
