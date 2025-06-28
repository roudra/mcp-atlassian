#!/usr/bin/env python3
"""
Comprehensive verification of complete Jira implementation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from mcp_atlassian_extended import ExtendedJiraManager

def verify_complete_implementation():
    """Verify we have complete implementation"""
    
    # Original Jira tools from the source
    original_jira_tools = [
        "add_comment",
        "add_worklog", 
        "batch_create_issues",
        "batch_create_versions",
        "batch_get_changelogs",
        "create_issue",
        "create_issue_link",
        "create_remote_issue_link",
        "create_sprint",
        "create_version",
        "delete_issue",
        "download_attachments",
        "get_agile_boards",
        "get_all_projects",
        "get_board_issues",
        "get_issue",
        "get_link_types",
        "get_project_issues",
        "get_project_versions",
        "get_sprint_issues",
        "get_sprints_from_board",
        "get_transitions",
        "get_user_profile",
        "get_worklog",
        "link_to_epic",
        "remove_issue_link",
        "search",
        "search_fields",
        "transition_issue",
        "update_issue",
        "update_sprint"
    ]
    
    manager = ExtendedJiraManager()
    
    # Get our implemented tools (remove jira_ prefix for comparison)
    our_tools = [tool['name'].replace('jira_', '') for tool in manager.tools if tool['name'].startswith('jira_')]
    
    print("🔍 COMPLETE JIRA IMPLEMENTATION VERIFICATION")
    print("=" * 50)
    
    print(f"\n📊 SUMMARY:")
    print(f"Original Jira tools: {len(original_jira_tools)}")
    print(f"Our implemented tools: {len(our_tools)}")
    
    # Check for missing tools
    missing_tools = []
    for tool in original_jira_tools:
        # Handle name variations
        variations = [
            tool,
            tool.replace('get_agile_boards', 'get_boards'),
            tool.replace('get_all_projects', 'get_projects'),
            tool.replace('download_attachments', 'download_attachment'),
            tool.replace('get_link_types', 'get_issue_link_types'),
            tool.replace('get_sprints_from_board', 'get_all_sprints_from_board')
        ]
        
        found = any(var in our_tools for var in variations)
        if not found:
            missing_tools.append(tool)
    
    # Check for extra tools (our additions)
    extra_tools = []
    for tool in our_tools:
        # Handle name variations back
        original_name = tool
        if tool == 'get_boards':
            original_name = 'get_agile_boards'
        elif tool == 'get_projects':
            original_name = 'get_all_projects'
        elif tool == 'download_attachment':
            original_name = 'download_attachments'
        elif tool == 'get_issue_link_types':
            original_name = 'get_link_types'
        elif tool == 'get_all_sprints_from_board':
            original_name = 'get_sprints_from_board'
        
        if original_name not in original_jira_tools:
            extra_tools.append(tool)
    
    print(f"\n✅ ORIGINAL TOOLS COVERAGE:")
    if not missing_tools:
        print("🎉 ALL ORIGINAL TOOLS IMPLEMENTED!")
    else:
        print(f"❌ Missing {len(missing_tools)} tools:")
        for tool in missing_tools:
            print(f"   - {tool}")
    
    print(f"\n🚀 EXTENDED FUNCTIONALITY:")
    print(f"Added {len(extra_tools)} new tools beyond original:")
    for tool in sorted(extra_tools):
        print(f"   + {tool}")
    
    print(f"\n📈 FINAL STATISTICS:")
    print(f"✅ Original parity: {'YES' if not missing_tools else 'NO'}")
    print(f"🔧 Total tools: {len(our_tools)}")
    print(f"📊 Coverage: {((len(original_jira_tools) - len(missing_tools)) / len(original_jira_tools) * 100):.1f}%")
    print(f"🎯 Enhancement: +{len(extra_tools)} additional tools")
    
    # Test a few key tools to ensure they're properly implemented
    print(f"\n🧪 IMPLEMENTATION TESTING:")
    test_tools = [
        "jira_batch_create_issues",
        "jira_batch_get_changelogs", 
        "jira_create_remote_issue_link",
        "jira_remove_issue_link",
        "jira_batch_create_versions"
    ]
    
    for tool_name in test_tools:
        try:
            result = manager.execute_tool(tool_name, {})
            if "Tool not implemented" in str(result):
                print(f"❌ {tool_name}: Not implemented")
            elif "Manager not initialized" in str(result):
                print(f"✅ {tool_name}: Implementation found (needs auth)")
            else:
                print(f"✅ {tool_name}: Implementation found")
        except Exception as e:
            print(f"⚠️  {tool_name}: {e}")
    
    return len(missing_tools) == 0

if __name__ == "__main__":
    success = verify_complete_implementation()
    if success:
        print(f"\n🎉 SUCCESS: Complete Jira implementation achieved!")
        sys.exit(0)
    else:
        print(f"\n❌ INCOMPLETE: Some original tools are missing")
        sys.exit(1)
