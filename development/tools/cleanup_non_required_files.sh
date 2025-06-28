#!/bin/bash
# 🧹 MCP Atlassian Cleanup Script
# Removes non-required files for the comprehensive 51-tool MCP server

cd /Users/arduor/Project/mcp-atlassian

echo "🧹 Starting MCP Atlassian cleanup..."
echo "📍 Working directory: $(pwd)"

# Confirm before proceeding
read -p "⚠️  This will delete non-essential files. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

echo "🗑️  Removing non-required files..."

# Remove entire original source (causes Python 3.9 errors)
echo "   Removing src/ directory (Python 3.10+ syntax issues)..."
rm -rf src/

# Remove redundant MCP servers
echo "   Removing redundant MCP server versions..."
rm -f consolidated/mcp_atlassian_enhanced.py
rm -f consolidated/mcp_atlassian_cookie.py  
rm -f consolidated/mcp_atlassian_full_jira.py

# Remove development test files
echo "   Removing development test files..."
rm -f test_cookie_auth.py
rm -f advanced_cookie_reader.py
rm -f convention_based_manager.py
rm -f test_search_rouroy.py
rm -f simple_cookie_test.py
rm -f consolidated/test_*.py
rm -f consolidated/verify_complete_implementation.py

# Remove duplicate configuration files
echo "   Removing duplicate configuration files..."
rm -f claude_desktop_config_*.json
rm -f claude_config_final.json
rm -f production_cookies.json
rm -f jira_config.json
rm -f consolidated/claude_config_full_jira.json
rm -f consolidated/config/claude_desktop_config.json
rm -f consolidated/config/amazonq_config.json
rm -f consolidated/config/claude_desktop_config_convention.json

# Remove analysis/planning documents
echo "   Removing analysis and planning documents..."
rm -f consolidated/comprehensive_tools_plan.md
rm -f consolidated/COMPREHENSIVE_TOOLS_PROGRESS.md
rm -f consolidated/MISSING_TOOLS_ANALYSIS.md
rm -f consolidated/FULL_JIRA_IMPLEMENTATION_SUMMARY.md
rm -f consolidated/CONSOLIDATION_SUMMARY.md
rm -f consolidated/GET_TOOLS_TEST_REPORT.md
rm -f COOKIE_INTEGRATION_SUMMARY.md

# Remove consolidated extras
echo "   Removing consolidated extras..."
rm -rf consolidated/core/
rm -rf consolidated/docs/
rm -f consolidated/README.md

# Remove mysterious file
echo "   Removing unknown files..."
rm -f ..json

# Optional: Remove development infrastructure (uncomment if desired)
echo "   Skipping development infrastructure (tests/, .devcontainer/, etc.)"
echo "   Uncomment lines in script to remove these as well."
# rm -rf tests/
# rm -rf .devcontainer/
# rm -rf scripts/
# rm -rf .github/
# rm -f pyproject.toml
# rm -f uv.lock

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "🎯 Essential files remaining:"
echo "   ✅ consolidated/mcp_atlassian_extended.py (51-tool server)"
echo "   ✅ consolidated/config/production_cookies.json (authentication)"
echo "   ✅ consolidated/config/jira_config.json (configuration)"
echo "   ✅ .vscode/settings.json (VS Code MCP config)"
echo "   ✅ .vscode/launch.json (debug config)"
echo "   ✅ Documentation and setup guides"
echo ""
echo "🚀 Your comprehensive MCP server is ready!"
echo "📊 Estimated space saved: ~3MB+"
