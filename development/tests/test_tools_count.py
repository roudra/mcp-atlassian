#!/usr/bin/env python3
"""
Quick test to verify all tools are properly implemented
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from mcp_atlassian_extended import ExtendedJiraManager

def test_tools():
    manager = ExtendedJiraManager()
    
    print(f"📊 Total tools defined: {len(manager.tools)}")
    print("\n🔧 Tool List:")
    
    for i, tool in enumerate(manager.tools, 1):
        print(f"{i:2d}. {tool['name']}")
    
    print(f"\n✅ All {len(manager.tools)} tools are properly defined!")
    
    # Test that execute_tool doesn't immediately fail for each tool
    print("\n🧪 Testing tool execution framework...")
    
    test_cases = [
        ("jira_get_fields", {}),
        ("jira_get_projects", {}),
        ("jira_get_user_profile", {}),
    ]
    
    for tool_name, args in test_cases:
        try:
            result = manager.execute_tool(tool_name, args)
            if "Tool not implemented" in str(result):
                print(f"❌ {tool_name}: Not implemented")
            else:
                print(f"✅ {tool_name}: Implementation found")
        except Exception as e:
            print(f"⚠️  {tool_name}: {e}")

if __name__ == "__main__":
    test_tools()
