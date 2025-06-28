#!/usr/bin/env python3
"""
Extended MCP Atlassian Server with More Tools
Based on the working cookie server but with additional tools
"""

import json
import sys
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
import requests
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

class ExtendedJiraManager:
    """Extended Jira manager with more tools"""
    
    def __init__(self):
        self.session = requests.Session()
        self.jira_url = None
        self.cookies_loaded = False
        self.config_loaded = False
        
        # Extended tool definitions
        self.tools = [
            # Basic tools
            {
                "name": "jira_search",
                "description": "Search Jira issues using JQL query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "jql": {"type": "string", "description": "JQL query"},
                        "max_results": {"type": "integer", "description": "Max results", "default": 50}
                    },
                    "required": ["jql"]
                }
            },
            {
                "name": "jira_get_issue",
                "description": "Get details of a specific Jira issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key (e.g., PROJ-123)"}
                    },
                    "required": ["issue_key"]
                }
            },
            {
                "name": "jira_get_user_profile",
                "description": "Get current user profile",
                "inputSchema": {"type": "object", "properties": {}}
            },
            
            # Comments
            {
                "name": "jira_add_comment",
                "description": "Add a comment to a Jira issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "comment": {"type": "string", "description": "Comment text"}
                    },
                    "required": ["issue_key", "comment"]
                }
            },
            {
                "name": "jira_get_comments",
                "description": "Get all comments for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            
            # Projects
            {
                "name": "jira_get_projects",
                "description": "Get all accessible projects",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "jira_get_project",
                "description": "Get details of a specific project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"}
                    },
                    "required": ["project_key"]
                }
            },
            {
                "name": "jira_get_project_issues",
                "description": "Get issues for a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"},
                        "max_results": {"type": "integer", "description": "Max results", "default": 50}
                    },
                    "required": ["project_key"]
                }
            },
            
            # Transitions
            {
                "name": "jira_get_transitions",
                "description": "Get available transitions for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            {
                "name": "jira_transition_issue",
                "description": "Transition an issue to a new status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "transition_name": {"type": "string", "description": "Transition name (e.g., 'In Progress', 'Done')"}
                    },
                    "required": ["issue_key", "transition_name"]
                }
            },
            
            # Worklog
            {
                "name": "jira_get_worklog",
                "description": "Get work logs for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            {
                "name": "jira_add_worklog",
                "description": "Add work log to an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "time_spent": {"type": "string", "description": "Time spent (e.g., '2h', '30m')"},
                        "comment": {"type": "string", "description": "Work description"}
                    },
                    "required": ["issue_key", "time_spent"]
                }
            },
            
            # Issue Creation/Updates
            {
                "name": "jira_create_issue",
                "description": "Create a new Jira issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"},
                        "summary": {"type": "string", "description": "Issue summary"},
                        "description": {"type": "string", "description": "Issue description"},
                        "issue_type": {"type": "string", "description": "Issue type", "default": "Task"}
                    },
                    "required": ["project_key", "summary"]
                }
            },
            {
                "name": "jira_update_issue",
                "description": "Update an existing issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "summary": {"type": "string", "description": "New summary"},
                        "description": {"type": "string", "description": "New description"}
                    },
                    "required": ["issue_key"]
                }
            },
            
            # Boards & Sprints
            {
                "name": "jira_get_boards",
                "description": "Get all agile boards",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "jira_get_board_issues",
                "description": "Get issues from a board",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "board_id": {"type": "integer", "description": "Board ID"}
                    },
                    "required": ["board_id"]
                }
            },
            
            # Fields
            {
                "name": "jira_get_fields",
                "description": "Get all available fields",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "jira_search_fields",
                "description": "Search for specific fields by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Field search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "jira_get_custom_fields",
                "description": "Get all custom fields",
                "inputSchema": {"type": "object", "properties": {}}
            },
            
            # Epic Management
            {
                "name": "jira_link_to_epic",
                "description": "Link an issue to an epic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key to link"},
                        "epic_key": {"type": "string", "description": "Epic key"}
                    },
                    "required": ["issue_key", "epic_key"]
                }
            },
            {
                "name": "jira_get_epic_issues",
                "description": "Get all issues in an epic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "epic_key": {"type": "string", "description": "Epic key"}
                    },
                    "required": ["epic_key"]
                }
            },
            
            # Issue Links
            {
                "name": "jira_create_issue_link",
                "description": "Create a link between two issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "inward_issue": {"type": "string", "description": "Source issue key"},
                        "outward_issue": {"type": "string", "description": "Target issue key"},
                        "link_type": {"type": "string", "description": "Link type (e.g., 'Blocks', 'Relates')", "default": "Relates"}
                    },
                    "required": ["inward_issue", "outward_issue"]
                }
            },
            {
                "name": "jira_get_issue_link_types",
                "description": "Get all available issue link types",
                "inputSchema": {"type": "object", "properties": {}}
            },
            
            # Sprints
            {
                "name": "jira_create_sprint",
                "description": "Create a new sprint",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "board_id": {"type": "integer", "description": "Board ID"},
                        "name": {"type": "string", "description": "Sprint name"},
                        "goal": {"type": "string", "description": "Sprint goal"}
                    },
                    "required": ["board_id", "name"]
                }
            },
            {
                "name": "jira_get_sprint_issues",
                "description": "Get issues in a sprint",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sprint_id": {"type": "integer", "description": "Sprint ID"}
                    },
                    "required": ["sprint_id"]
                }
            },
            {
                "name": "jira_get_all_sprints_from_board",
                "description": "Get all sprints from a board",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "board_id": {"type": "integer", "description": "Board ID"}
                    },
                    "required": ["board_id"]
                }
            },
            
            # Project Versions
            {
                "name": "jira_get_project_versions",
                "description": "Get all versions for a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"}
                    },
                    "required": ["project_key"]
                }
            },
            {
                "name": "jira_create_version",
                "description": "Create a new project version",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"},
                        "name": {"type": "string", "description": "Version name"},
                        "description": {"type": "string", "description": "Version description"}
                    },
                    "required": ["project_key", "name"]
                }
            },
            
            # Advanced Issue Operations
            {
                "name": "jira_delete_issue",
                "description": "Delete a Jira issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key to delete"}
                    },
                    "required": ["issue_key"]
                }
            },
            
            # User Management
            {
                "name": "jira_get_user_by_username",
                "description": "Get user profile by username",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Username to lookup"}
                    },
                    "required": ["username"]
                }
            },
            
            # Attachments
            {
                "name": "jira_get_attachments",
                "description": "Get all attachments for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            {
                "name": "jira_download_attachment",
                "description": "Download an attachment from an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "attachment_id": {"type": "string", "description": "Attachment ID"},
                        "filename": {"type": "string", "description": "Filename to save as"}
                    },
                    "required": ["attachment_id"]
                }
            },
            {
                "name": "jira_delete_attachment",
                "description": "Delete an attachment from an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "attachment_id": {"type": "string", "description": "Attachment ID to delete"}
                    },
                    "required": ["attachment_id"]
                }
            },
            
            # Advanced Comments
            {
                "name": "jira_update_comment",
                "description": "Update an existing comment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "comment_id": {"type": "string", "description": "Comment ID"},
                        "comment": {"type": "string", "description": "Updated comment text"}
                    },
                    "required": ["issue_key", "comment_id", "comment"]
                }
            },
            {
                "name": "jira_delete_comment",
                "description": "Delete a comment from an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "comment_id": {"type": "string", "description": "Comment ID to delete"}
                    },
                    "required": ["issue_key", "comment_id"]
                }
            },
            
            # Watchers
            {
                "name": "jira_get_watchers",
                "description": "Get all watchers for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            {
                "name": "jira_add_watcher",
                "description": "Add a watcher to an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "username": {"type": "string", "description": "Username to add as watcher"}
                    },
                    "required": ["issue_key", "username"]
                }
            },
            {
                "name": "jira_remove_watcher",
                "description": "Remove a watcher from an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "username": {"type": "string", "description": "Username to remove as watcher"}
                    },
                    "required": ["issue_key", "username"]
                }
            },
            
            # Advanced Issue Operations
            {
                "name": "jira_clone_issue",
                "description": "Clone/duplicate an existing issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key to clone"},
                        "summary": {"type": "string", "description": "Summary for cloned issue"},
                        "project_key": {"type": "string", "description": "Target project key (optional)"}
                    },
                    "required": ["issue_key", "summary"]
                }
            },
            {
                "name": "jira_assign_issue",
                "description": "Assign an issue to a user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "assignee": {"type": "string", "description": "Username to assign to"}
                    },
                    "required": ["issue_key", "assignee"]
                }
            },
            {
                "name": "jira_unassign_issue",
                "description": "Remove assignee from an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"}
                    },
                    "required": ["issue_key"]
                }
            },
            
            # Advanced Sprint Management
            {
                "name": "jira_update_sprint",
                "description": "Update sprint details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sprint_id": {"type": "integer", "description": "Sprint ID"},
                        "name": {"type": "string", "description": "Sprint name"},
                        "goal": {"type": "string", "description": "Sprint goal"}
                    },
                    "required": ["sprint_id"]
                }
            },
            {
                "name": "jira_start_sprint",
                "description": "Start a sprint",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sprint_id": {"type": "integer", "description": "Sprint ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                    },
                    "required": ["sprint_id"]
                }
            },
            {
                "name": "jira_complete_sprint",
                "description": "Complete/close a sprint",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sprint_id": {"type": "integer", "description": "Sprint ID"}
                    },
                    "required": ["sprint_id"]
                }
            },
            
            # Advanced Worklog
            {
                "name": "jira_update_worklog",
                "description": "Update an existing worklog entry",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "worklog_id": {"type": "string", "description": "Worklog ID"},
                        "time_spent": {"type": "string", "description": "Time spent (e.g., '2h', '30m')"},
                        "comment": {"type": "string", "description": "Work description"}
                    },
                    "required": ["issue_key", "worklog_id"]
                }
            },
            {
                "name": "jira_delete_worklog",
                "description": "Delete a worklog entry",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "worklog_id": {"type": "string", "description": "Worklog ID to delete"}
                    },
                    "required": ["issue_key", "worklog_id"]
                }
            },
            
            # Missing Original Tools
            {
                "name": "jira_batch_create_issues",
                "description": "Create multiple issues at once",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issues": {
                            "type": "array",
                            "description": "Array of issue objects to create",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "project_key": {"type": "string", "description": "Project key"},
                                    "summary": {"type": "string", "description": "Issue summary"},
                                    "description": {"type": "string", "description": "Issue description"},
                                    "issue_type": {"type": "string", "description": "Issue type", "default": "Task"}
                                },
                                "required": ["project_key", "summary"]
                            }
                        }
                    },
                    "required": ["issues"]
                }
            },
            {
                "name": "jira_batch_create_versions",
                "description": "Create multiple project versions at once",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "Project key"},
                        "versions": {
                            "type": "array",
                            "description": "Array of version objects to create",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Version name"},
                                    "description": {"type": "string", "description": "Version description"}
                                },
                                "required": ["name"]
                            }
                        }
                    },
                    "required": ["project_key", "versions"]
                }
            },
            {
                "name": "jira_batch_get_changelogs",
                "description": "Get changelogs for multiple issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_keys": {
                            "type": "array",
                            "description": "Array of issue keys",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["issue_keys"]
                }
            },
            {
                "name": "jira_create_remote_issue_link",
                "description": "Create a remote/web link for an issue",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "Issue key"},
                        "url": {"type": "string", "description": "Remote URL"},
                        "title": {"type": "string", "description": "Link title"},
                        "summary": {"type": "string", "description": "Link summary/description"}
                    },
                    "required": ["issue_key", "url", "title"]
                }
            },
            {
                "name": "jira_remove_issue_link",
                "description": "Remove a link between two issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "link_id": {"type": "string", "description": "Issue link ID to remove"}
                    },
                    "required": ["link_id"]
                }
            }
        ]
    
    def load_config(self, config_file: str) -> bool:
        """Load Jira configuration"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.jira_url = config.get('jira_url')
            if not self.jira_url:
                logger.error("No jira_url in config")
                return False
            
            # Apply headers from config
            if 'headers' in config:
                self.session.headers.update(config['headers'])
            
            logger.info(f"✅ Config loaded from: {config_file}")
            self.config_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def load_cookies(self, cookie_file: str) -> bool:
        """Load cookies from file"""
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            cookies = cookie_data.get('cookies', {})
            if not cookies:
                logger.error("No cookies found in file")
                return False
            
            # Apply cookies to session
            for name, value in cookies.items():
                self.session.cookies.set(name, value)
            
            # Apply enhanced browser-like headers to fool rate limiting
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'X-Atlassian-Token': 'no-check',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Referer': f"{self.jira_url}/secure/Dashboard.jspa" if self.jira_url else ''
            })
            
            logger.info(f"✅ Loaded {len(cookies)} cookies")
            logger.info(f"🌐 Applied enhanced browser-like headers")
            self.cookies_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False
    
    def _make_browser_request(self, method: str, url: str, **kwargs):
        """Make a request with browser-like timing to avoid rate limiting"""
        import time
        import random
        
        # Add small random delay to mimic human behavior
        delay = random.uniform(0.1, 0.3)
        time.sleep(delay)
        
        # Make the request
        response = self.session.request(method, url, **kwargs)
        
        # Small delay after request
        time.sleep(random.uniform(0.05, 0.1))
        
        return response
    
    def is_ready(self) -> bool:
        """Check if manager is ready"""
        return self.config_loaded and self.cookies_loaded and self.jira_url
    
    # Tool implementations
    def jira_search(self, jql: str = "", max_results: int = 50) -> Dict:
        """Search Jira issues using JQL"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,assignee,reporter,created,updated,description,issuetype,priority"
            }
            
            response = self._make_browser_request('GET', url, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e)}
    
    def jira_get_issue(self, issue_key: str) -> Dict:
        """Get details of a specific Jira issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Get issue failed: {e}")
            return {"error": str(e)}
    
    def jira_get_user_profile(self) -> Dict:
        """Get current user profile"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/myself"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Get user profile failed: {e}")
            return {"error": str(e)}
    
    def jira_add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add comment to issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment"
            data = {"body": comment}
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Add comment failed: {e}")
            return {"error": str(e)}
    
    def jira_get_comments(self, issue_key: str) -> Dict:
        """Get comments for issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Get comments failed: {e}")
            return {"error": str(e)}
    
    def jira_get_projects(self) -> Dict:
        """Get all projects"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/project"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            return {"projects": response.json()}
            
        except Exception as e:
            logger.error(f"Get projects failed: {e}")
            return {"error": str(e)}
    
    def jira_get_project(self, project_key: str) -> Dict:
        """Get details of a specific project"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/project/{project_key}"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get project failed: {e}")
            return {"error": str(e)}
    
    def jira_get_project_issues(self, project_key: str, max_results: int = 50) -> Dict:
        """Get issues for a project"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            jql = f"project = {project_key}"
            return self.jira_search(jql, max_results)
            
        except Exception as e:
            logger.error(f"Get project issues failed: {e}")
            return {"error": str(e)}
    
    def jira_transition_issue(self, issue_key: str, transition_name: str) -> Dict:
        """Transition an issue to a new status"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            # First get available transitions
            transitions_response = self.jira_get_transitions(issue_key)
            if "error" in transitions_response:
                return transitions_response
            
            # Find the transition ID
            transition_id = None
            for transition in transitions_response.get("transitions", []):
                if transition.get("name", "").lower() == transition_name.lower():
                    transition_id = transition.get("id")
                    break
            
            if not transition_id:
                return {"error": f"Transition '{transition_name}' not found"}
            
            # Execute the transition
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/transitions"
            data = {"transition": {"id": transition_id}}
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Transitioned {issue_key} to {transition_name}"}
            
        except Exception as e:
            logger.error(f"Transition issue failed: {e}")
            return {"error": str(e)}
    
    def jira_get_worklog(self, issue_key: str) -> Dict:
        """Get work logs for an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/worklog"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get worklog failed: {e}")
            return {"error": str(e)}
    
    def jira_add_worklog(self, issue_key: str, time_spent: str, comment: str = "") -> Dict:
        """Add work log to an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/worklog"
            data = {
                "timeSpent": time_spent,
                "comment": comment
            }
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Added {time_spent} worklog to {issue_key}"}
            
        except Exception as e:
            logger.error(f"Add worklog failed: {e}")
            return {"error": str(e)}
    
    def jira_create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> Dict:
        """Create a new Jira issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue"
            data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            }
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            new_issue = response.json()
            return {"success": f"Created issue {new_issue.get('key')}", "issue": new_issue}
            
        except Exception as e:
            logger.error(f"Create issue failed: {e}")
            return {"error": str(e)}
    
    def jira_update_issue(self, issue_key: str, summary: str = None, description: str = None) -> Dict:
        """Update an existing issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}"
            fields = {}
            if summary:
                fields["summary"] = summary
            if description:
                fields["description"] = description
            
            data = {"fields": fields}
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Updated issue {issue_key}"}
            
        except Exception as e:
            logger.error(f"Update issue failed: {e}")
            return {"error": str(e)}
    
    def jira_delete_issue(self, issue_key: str) -> Dict:
        """Delete a Jira issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Deleted issue {issue_key}"}
            
        except Exception as e:
            logger.error(f"Delete issue failed: {e}")
            return {"error": str(e)}
    
    def jira_get_boards(self) -> Dict:
        """Get all agile boards"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/board"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get boards failed: {e}")
            return {"error": str(e)}
    
    def jira_get_board_issues(self, board_id: int) -> Dict:
        """Get issues from a board"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/board/{board_id}/issue"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get board issues failed: {e}")
            return {"error": str(e)}
    
    def jira_get_project_versions(self, project_key: str) -> Dict:
        """Get all versions for a project"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/project/{project_key}/versions"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return {"versions": response.json()}
            
        except Exception as e:
            logger.error(f"Get project versions failed: {e}")
            return {"error": str(e)}
    
    def jira_create_version(self, project_key: str, name: str, description: str = "") -> Dict:
        """Create a new project version"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/version"
            data = {
                "name": name,
                "description": description,
                "project": project_key
            }
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            new_version = response.json()
            return {"success": f"Created version {name}", "version": new_version}
            
        except Exception as e:
            logger.error(f"Create version failed: {e}")
            return {"error": str(e)}
    
    def jira_get_user_by_username(self, username: str) -> Dict:
        """Get user profile by username"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/user?username={username}"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get user by username failed: {e}")
            return {"error": str(e)}
    
    def jira_get_transitions(self, issue_key: str) -> Dict:
        """Get available transitions for issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/transitions"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Get transitions failed: {e}")
            return {"error": str(e)}
    
    def jira_search_fields(self, query: str) -> Dict:
        """Search for fields by name"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/field"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            fields = response.json()
            # Filter fields by query
            matching_fields = [f for f in fields if query.lower() in f.get('name', '').lower()]
            return {"fields": matching_fields}
            
        except Exception as e:
            logger.error(f"Search fields failed: {e}")
            return {"error": str(e)}
    
    def jira_get_fields(self) -> Dict:
        """Get all available fields"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/field"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            fields = response.json()
            return {"fields": fields}
            
        except Exception as e:
            logger.error(f"Get fields failed: {e}")
            return {"error": str(e)}
    
    def jira_get_custom_fields(self) -> Dict:
        """Get all custom fields"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/field"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            fields = response.json()
            # Filter only custom fields
            custom_fields = [f for f in fields if f.get('custom', False)]
            return {"custom_fields": custom_fields}
            
        except Exception as e:
            logger.error(f"Get custom fields failed: {e}")
            return {"error": str(e)}
    
    def jira_link_to_epic(self, issue_key: str, epic_key: str) -> Dict:
        """Link an issue to an epic"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            # First get the epic link field ID
            fields_response = self._make_browser_request('GET', f"{self.jira_url}/rest/api/2/field")
            fields_response.raise_for_status()
            fields = fields_response.json()
            
            epic_link_field = None
            for field in fields:
                if field.get('name') == 'Epic Link':
                    epic_link_field = field['id']
                    break
            
            if not epic_link_field:
                return {"error": "Epic Link field not found"}
            
            # Update the issue with epic link
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}"
            data = {
                "fields": {
                    epic_link_field: epic_key
                }
            }
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Linked {issue_key} to epic {epic_key}"}
            
        except Exception as e:
            logger.error(f"Link to epic failed: {e}")
            return {"error": str(e)}
    
    def jira_get_epic_issues(self, epic_key: str) -> Dict:
        """Get all issues in an epic"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            # Search for issues with this epic
            jql = f'"Epic Link" = {epic_key}'
            return self.jira_search(jql, 100)
            
        except Exception as e:
            logger.error(f"Get epic issues failed: {e}")
            return {"error": str(e)}
    
    def jira_create_issue_link(self, inward_issue: str, outward_issue: str, link_type: str = "Relates") -> Dict:
        """Create a link between two issues"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issueLink"
            data = {
                "type": {"name": link_type},
                "inwardIssue": {"key": inward_issue},
                "outwardIssue": {"key": outward_issue}
            }
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Created {link_type} link between {inward_issue} and {outward_issue}"}
            
        except Exception as e:
            logger.error(f"Create issue link failed: {e}")
            return {"error": str(e)}
    
    def jira_get_issue_link_types(self) -> Dict:
        """Get all available issue link types"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issueLinkType"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get issue link types failed: {e}")
            return {"error": str(e)}
    
    def jira_create_sprint(self, board_id: int, name: str, goal: str = "") -> Dict:
        """Create a new sprint"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint"
            data = {
                "name": name,
                "originBoardId": board_id,
                "goal": goal
            }
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Create sprint failed: {e}")
            return {"error": str(e)}
    
    def jira_get_sprint_issues(self, sprint_id: int) -> Dict:
        """Get issues in a sprint"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get sprint issues failed: {e}")
            return {"error": str(e)}
    
    def jira_get_all_sprints_from_board(self, board_id: int) -> Dict:
        """Get all sprints from a board"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/board/{board_id}/sprint"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get sprints from board failed: {e}")
            return {"error": str(e)}
    
    # New attachment methods
    def jira_get_attachments(self, issue_key: str) -> Dict:
        """Get all attachments for an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}?fields=attachment"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            issue_data = response.json()
            attachments = issue_data.get('fields', {}).get('attachment', [])
            
            return {"attachments": attachments}
            
        except Exception as e:
            logger.error(f"Get attachments failed: {e}")
            return {"error": str(e)}
    
    def jira_download_attachment(self, attachment_id: str, filename: str = None) -> Dict:
        """Download an attachment"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/attachment/{attachment_id}"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            # For now, just return attachment info
            # In a full implementation, you'd save the file
            return {"success": f"Attachment {attachment_id} info retrieved", "size": len(response.content)}
            
        except Exception as e:
            logger.error(f"Download attachment failed: {e}")
            return {"error": str(e)}
    
    def jira_delete_attachment(self, attachment_id: str) -> Dict:
        """Delete an attachment"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/attachment/{attachment_id}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Attachment {attachment_id} deleted"}
            
        except Exception as e:
            logger.error(f"Delete attachment failed: {e}")
            return {"error": str(e)}
    
    # Advanced comment methods
    def jira_update_comment(self, issue_key: str, comment_id: str, comment: str) -> Dict:
        """Update an existing comment"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment/{comment_id}"
            data = {"body": comment}
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Comment {comment_id} updated"}
            
        except Exception as e:
            logger.error(f"Update comment failed: {e}")
            return {"error": str(e)}
    
    def jira_delete_comment(self, issue_key: str, comment_id: str) -> Dict:
        """Delete a comment"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment/{comment_id}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Comment {comment_id} deleted"}
            
        except Exception as e:
            logger.error(f"Delete comment failed: {e}")
            return {"error": str(e)}
    
    # Watcher methods
    def jira_get_watchers(self, issue_key: str) -> Dict:
        """Get all watchers for an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/watchers"
            response = self._make_browser_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get watchers failed: {e}")
            return {"error": str(e)}
    
    def jira_add_watcher(self, issue_key: str, username: str) -> Dict:
        """Add a watcher to an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/watchers"
            response = self._make_browser_request('POST', url, json=username)
            response.raise_for_status()
            
            return {"success": f"Added {username} as watcher to {issue_key}"}
            
        except Exception as e:
            logger.error(f"Add watcher failed: {e}")
            return {"error": str(e)}
    
    def jira_remove_watcher(self, issue_key: str, username: str) -> Dict:
        """Remove a watcher from an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/watchers?username={username}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Removed {username} as watcher from {issue_key}"}
            
        except Exception as e:
            logger.error(f"Remove watcher failed: {e}")
            return {"error": str(e)}
    
    # Advanced issue operations
    def jira_clone_issue(self, issue_key: str, summary: str, project_key: str = None) -> Dict:
        """Clone an existing issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            # First get the original issue
            original = self.jira_get_issue(issue_key)
            if "error" in original:
                return original
            
            # Extract fields from original issue
            fields = original.get("fields", {})
            target_project = project_key or fields.get("project", {}).get("key")
            
            # Create new issue with cloned data
            clone_data = {
                "fields": {
                    "project": {"key": target_project},
                    "summary": summary,
                    "description": fields.get("description", ""),
                    "issuetype": fields.get("issuetype", {"name": "Task"}),
                    "priority": fields.get("priority", {"name": "Medium"})
                }
            }
            
            url = f"{self.jira_url}/rest/api/2/issue"
            response = self._make_browser_request('POST', url, json=clone_data)
            response.raise_for_status()
            
            new_issue = response.json()
            return {"success": f"Cloned {issue_key} as {new_issue.get('key')}", "new_issue": new_issue}
            
        except Exception as e:
            logger.error(f"Clone issue failed: {e}")
            return {"error": str(e)}
    
    def jira_assign_issue(self, issue_key: str, assignee: str) -> Dict:
        """Assign an issue to a user"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/assignee"
            data = {"name": assignee}
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Assigned {issue_key} to {assignee}"}
            
        except Exception as e:
            logger.error(f"Assign issue failed: {e}")
            return {"error": str(e)}
    
    def jira_unassign_issue(self, issue_key: str) -> Dict:
        """Remove assignee from an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/assignee"
            data = {"name": None}
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Unassigned {issue_key}"}
            
        except Exception as e:
            logger.error(f"Unassign issue failed: {e}")
            return {"error": str(e)}
    
    # Advanced sprint methods
    def jira_update_sprint(self, sprint_id: int, name: str = None, goal: str = None) -> Dict:
        """Update sprint details"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}"
            data = {}
            if name:
                data["name"] = name
            if goal:
                data["goal"] = goal
            
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Updated sprint {sprint_id}"}
            
        except Exception as e:
            logger.error(f"Update sprint failed: {e}")
            return {"error": str(e)}
    
    def jira_start_sprint(self, sprint_id: int, start_date: str = None, end_date: str = None) -> Dict:
        """Start a sprint"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}"
            data = {"state": "active"}
            if start_date:
                data["startDate"] = start_date
            if end_date:
                data["endDate"] = end_date
            
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Started sprint {sprint_id}"}
            
        except Exception as e:
            logger.error(f"Start sprint failed: {e}")
            return {"error": str(e)}
    
    def jira_complete_sprint(self, sprint_id: int) -> Dict:
        """Complete a sprint"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}"
            data = {"state": "closed"}
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Completed sprint {sprint_id}"}
            
        except Exception as e:
            logger.error(f"Complete sprint failed: {e}")
            return {"error": str(e)}
    
    # Advanced worklog methods
    def jira_update_worklog(self, issue_key: str, worklog_id: str, time_spent: str = None, comment: str = None) -> Dict:
        """Update an existing worklog entry"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/worklog/{worklog_id}"
            data = {}
            if time_spent:
                data["timeSpent"] = time_spent
            if comment:
                data["comment"] = comment
            
            response = self._make_browser_request('PUT', url, json=data)
            response.raise_for_status()
            
            return {"success": f"Updated worklog {worklog_id}"}
            
        except Exception as e:
            logger.error(f"Update worklog failed: {e}")
            return {"error": str(e)}
    
    def jira_delete_worklog(self, issue_key: str, worklog_id: str) -> Dict:
        """Delete a worklog entry"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/worklog/{worklog_id}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Deleted worklog {worklog_id}"}
            
        except Exception as e:
            logger.error(f"Delete worklog failed: {e}")
            return {"error": str(e)}
    
    # Missing Original Tools Implementation
    def jira_batch_create_issues(self, issues: list) -> Dict:
        """Create multiple issues at once"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/bulk"
            issue_updates = []
            
            for issue in issues:
                issue_data = {
                    "fields": {
                        "project": {"key": issue.get("project_key")},
                        "summary": issue.get("summary"),
                        "description": issue.get("description", ""),
                        "issuetype": {"name": issue.get("issue_type", "Task")}
                    }
                }
                issue_updates.append(issue_data)
            
            data = {"issueUpdates": issue_updates}
            response = self._make_browser_request('POST', url, json=data)
            response.raise_for_status()
            
            result = response.json()
            return {"success": f"Created {len(result.get('issues', []))} issues", "issues": result}
            
        except Exception as e:
            logger.error(f"Batch create issues failed: {e}")
            return {"error": str(e)}
    
    def jira_batch_create_versions(self, project_key: str, versions: list) -> Dict:
        """Create multiple project versions at once"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            created_versions = []
            errors = []
            
            for version in versions:
                try:
                    result = self.jira_create_version(
                        project_key, 
                        version.get("name"), 
                        version.get("description", "")
                    )
                    if "error" in result:
                        errors.append(f"Version '{version.get('name')}': {result['error']}")
                    else:
                        created_versions.append(result)
                except Exception as e:
                    errors.append(f"Version '{version.get('name')}': {str(e)}")
            
            return {
                "success": f"Created {len(created_versions)} versions",
                "created": created_versions,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Batch create versions failed: {e}")
            return {"error": str(e)}
    
    def jira_batch_get_changelogs(self, issue_keys: list) -> Dict:
        """Get changelogs for multiple issues"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            changelogs = {}
            errors = []
            
            for issue_key in issue_keys:
                try:
                    url = f"{self.jira_url}/rest/api/2/issue/{issue_key}?expand=changelog"
                    response = self._make_browser_request('GET', url)
                    response.raise_for_status()
                    
                    issue_data = response.json()
                    changelogs[issue_key] = issue_data.get("changelog", {})
                    
                except Exception as e:
                    errors.append(f"Issue {issue_key}: {str(e)}")
            
            return {
                "changelogs": changelogs,
                "errors": errors,
                "success": f"Retrieved changelogs for {len(changelogs)} issues"
            }
            
        except Exception as e:
            logger.error(f"Batch get changelogs failed: {e}")
            return {"error": str(e)}
    
    def jira_create_remote_issue_link(self, issue_key: str, url: str, title: str, summary: str = "") -> Dict:
        """Create a remote/web link for an issue"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            api_url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/remotelink"
            data = {
                "object": {
                    "url": url,
                    "title": title,
                    "summary": summary
                }
            }
            response = self._make_browser_request('POST', api_url, json=data)
            response.raise_for_status()
            
            return {"success": f"Created remote link '{title}' for {issue_key}"}
            
        except Exception as e:
            logger.error(f"Create remote issue link failed: {e}")
            return {"error": str(e)}
    
    def jira_remove_issue_link(self, link_id: str) -> Dict:
        """Remove a link between two issues"""
        if not self.is_ready():
            return {"error": "Manager not initialized"}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issueLink/{link_id}"
            response = self._make_browser_request('DELETE', url)
            response.raise_for_status()
            
            return {"success": f"Removed issue link {link_id}"}
            
        except Exception as e:
            logger.error(f"Remove issue link failed: {e}")
            return {"error": str(e)}
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name"""
        if tool_name == "jira_search":
            jql = arguments.get("jql", "")
            max_results = arguments.get("max_results", 50)
            return self.jira_search(jql, max_results)
            
        elif tool_name == "jira_get_issue":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_issue(issue_key)
            
        elif tool_name == "jira_get_user_profile":
            return self.jira_get_user_profile()
            
        elif tool_name == "jira_add_comment":
            issue_key = arguments.get("issue_key", "")
            comment = arguments.get("comment", "")
            return self.jira_add_comment(issue_key, comment)
            
        elif tool_name == "jira_get_comments":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_comments(issue_key)
            
        elif tool_name == "jira_get_projects":
            return self.jira_get_projects()
            
        elif tool_name == "jira_get_project":
            project_key = arguments.get("project_key", "")
            return self.jira_get_project(project_key)
            
        elif tool_name == "jira_get_transitions":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_transitions(issue_key)
            
        elif tool_name == "jira_get_fields":
            return self.jira_get_fields()
            
        elif tool_name == "jira_search_fields":
            query = arguments.get("query", "")
            return self.jira_search_fields(query)
            
        elif tool_name == "jira_get_custom_fields":
            return self.jira_get_custom_fields()
            
        elif tool_name == "jira_get_project_issues":
            project_key = arguments.get("project_key", "")
            max_results = arguments.get("max_results", 50)
            return self.jira_get_project_issues(project_key, max_results)
            
        elif tool_name == "jira_transition_issue":
            issue_key = arguments.get("issue_key", "")
            transition_name = arguments.get("transition_name", "")
            return self.jira_transition_issue(issue_key, transition_name)
            
        elif tool_name == "jira_get_worklog":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_worklog(issue_key)
            
        elif tool_name == "jira_add_worklog":
            issue_key = arguments.get("issue_key", "")
            time_spent = arguments.get("time_spent", "")
            comment = arguments.get("comment", "")
            return self.jira_add_worklog(issue_key, time_spent, comment)
            
        elif tool_name == "jira_create_issue":
            project_key = arguments.get("project_key", "")
            summary = arguments.get("summary", "")
            description = arguments.get("description", "")
            issue_type = arguments.get("issue_type", "Task")
            return self.jira_create_issue(project_key, summary, description, issue_type)
            
        elif tool_name == "jira_update_issue":
            issue_key = arguments.get("issue_key", "")
            summary = arguments.get("summary")
            description = arguments.get("description")
            return self.jira_update_issue(issue_key, summary, description)
            
        elif tool_name == "jira_delete_issue":
            issue_key = arguments.get("issue_key", "")
            return self.jira_delete_issue(issue_key)
            
        elif tool_name == "jira_get_boards":
            return self.jira_get_boards()
            
        elif tool_name == "jira_get_board_issues":
            board_id = arguments.get("board_id", 0)
            return self.jira_get_board_issues(board_id)
            
        elif tool_name == "jira_get_project_versions":
            project_key = arguments.get("project_key", "")
            return self.jira_get_project_versions(project_key)
            
        elif tool_name == "jira_create_version":
            project_key = arguments.get("project_key", "")
            name = arguments.get("name", "")
            description = arguments.get("description", "")
            return self.jira_create_version(project_key, name, description)
            
        elif tool_name == "jira_get_user_by_username":
            username = arguments.get("username", "")
            return self.jira_get_user_by_username(username)
            
        elif tool_name == "jira_link_to_epic":
            issue_key = arguments.get("issue_key", "")
            epic_key = arguments.get("epic_key", "")
            return self.jira_link_to_epic(issue_key, epic_key)
            
        elif tool_name == "jira_get_epic_issues":
            epic_key = arguments.get("epic_key", "")
            return self.jira_get_epic_issues(epic_key)
            
        elif tool_name == "jira_create_issue_link":
            inward_issue = arguments.get("inward_issue", "")
            outward_issue = arguments.get("outward_issue", "")
            link_type = arguments.get("link_type", "Relates")
            return self.jira_create_issue_link(inward_issue, outward_issue, link_type)
            
        elif tool_name == "jira_get_issue_link_types":
            return self.jira_get_issue_link_types()
            
        elif tool_name == "jira_create_sprint":
            board_id = arguments.get("board_id", 0)
            name = arguments.get("name", "")
            goal = arguments.get("goal", "")
            return self.jira_create_sprint(board_id, name, goal)
            
        elif tool_name == "jira_get_sprint_issues":
            sprint_id = arguments.get("sprint_id", 0)
            return self.jira_get_sprint_issues(sprint_id)
            
        elif tool_name == "jira_get_all_sprints_from_board":
            board_id = arguments.get("board_id", 0)
            return self.jira_get_all_sprints_from_board(board_id)
            
        # Attachment tools
        elif tool_name == "jira_get_attachments":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_attachments(issue_key)
            
        elif tool_name == "jira_download_attachment":
            attachment_id = arguments.get("attachment_id", "")
            filename = arguments.get("filename")
            return self.jira_download_attachment(attachment_id, filename)
            
        elif tool_name == "jira_delete_attachment":
            attachment_id = arguments.get("attachment_id", "")
            return self.jira_delete_attachment(attachment_id)
            
        # Advanced comment tools
        elif tool_name == "jira_update_comment":
            issue_key = arguments.get("issue_key", "")
            comment_id = arguments.get("comment_id", "")
            comment = arguments.get("comment", "")
            return self.jira_update_comment(issue_key, comment_id, comment)
            
        elif tool_name == "jira_delete_comment":
            issue_key = arguments.get("issue_key", "")
            comment_id = arguments.get("comment_id", "")
            return self.jira_delete_comment(issue_key, comment_id)
            
        # Watcher tools
        elif tool_name == "jira_get_watchers":
            issue_key = arguments.get("issue_key", "")
            return self.jira_get_watchers(issue_key)
            
        elif tool_name == "jira_add_watcher":
            issue_key = arguments.get("issue_key", "")
            username = arguments.get("username", "")
            return self.jira_add_watcher(issue_key, username)
            
        elif tool_name == "jira_remove_watcher":
            issue_key = arguments.get("issue_key", "")
            username = arguments.get("username", "")
            return self.jira_remove_watcher(issue_key, username)
            
        # Advanced issue operations
        elif tool_name == "jira_clone_issue":
            issue_key = arguments.get("issue_key", "")
            summary = arguments.get("summary", "")
            project_key = arguments.get("project_key")
            return self.jira_clone_issue(issue_key, summary, project_key)
            
        elif tool_name == "jira_assign_issue":
            issue_key = arguments.get("issue_key", "")
            assignee = arguments.get("assignee", "")
            return self.jira_assign_issue(issue_key, assignee)
            
        elif tool_name == "jira_unassign_issue":
            issue_key = arguments.get("issue_key", "")
            return self.jira_unassign_issue(issue_key)
            
        # Advanced sprint tools
        elif tool_name == "jira_update_sprint":
            sprint_id = arguments.get("sprint_id", 0)
            name = arguments.get("name")
            goal = arguments.get("goal")
            return self.jira_update_sprint(sprint_id, name, goal)
            
        elif tool_name == "jira_start_sprint":
            sprint_id = arguments.get("sprint_id", 0)
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            return self.jira_start_sprint(sprint_id, start_date, end_date)
            
        elif tool_name == "jira_complete_sprint":
            sprint_id = arguments.get("sprint_id", 0)
            return self.jira_complete_sprint(sprint_id)
            
        # Advanced worklog tools
        elif tool_name == "jira_update_worklog":
            issue_key = arguments.get("issue_key", "")
            worklog_id = arguments.get("worklog_id", "")
            time_spent = arguments.get("time_spent")
            comment = arguments.get("comment")
            return self.jira_update_worklog(issue_key, worklog_id, time_spent, comment)
            
        elif tool_name == "jira_delete_worklog":
            issue_key = arguments.get("issue_key", "")
            worklog_id = arguments.get("worklog_id", "")
            return self.jira_delete_worklog(issue_key, worklog_id)
            
        # Missing Original Tools
        elif tool_name == "jira_batch_create_issues":
            issues = arguments.get("issues", [])
            return self.jira_batch_create_issues(issues)
            
        elif tool_name == "jira_batch_create_versions":
            project_key = arguments.get("project_key", "")
            versions = arguments.get("versions", [])
            return self.jira_batch_create_versions(project_key, versions)
            
        elif tool_name == "jira_batch_get_changelogs":
            issue_keys = arguments.get("issue_keys", [])
            return self.jira_batch_get_changelogs(issue_keys)
            
        elif tool_name == "jira_create_remote_issue_link":
            issue_key = arguments.get("issue_key", "")
            url = arguments.get("url", "")
            title = arguments.get("title", "")
            summary = arguments.get("summary", "")
            return self.jira_create_remote_issue_link(issue_key, url, title, summary)
            
        elif tool_name == "jira_remove_issue_link":
            link_id = arguments.get("link_id", "")
            return self.jira_remove_issue_link(link_id)
            
        else:
            return {"error": f"Tool not implemented: {tool_name}"}

class ExtendedMCPServer:
    """Extended MCP Server with more tools"""
    
    def __init__(self):
        self.manager = ExtendedJiraManager()
        self.initialized = False
    
    def initialize_manager(self) -> bool:
        """Initialize the Jira manager"""
        try:
            script_dir = Path(__file__).parent
            
            cookie_file = os.getenv('JIRA_COOKIE_FILE', str(script_dir / 'config' / 'production_cookies.json'))
            config_file = os.getenv('JIRA_CONFIG_FILE', str(script_dir / 'config' / 'jira_config.json'))
            
            logger.info(f"Initializing with cookie file: {cookie_file}")
            logger.info(f"Using config file: {config_file}")
            
            # Load configuration
            if not self.manager.load_config(config_file):
                return False
            
            # Load cookies
            if not self.manager.load_cookies(cookie_file):
                return False
            
            # Test connection
            user_profile = self.manager.jira_get_user_profile()
            if 'error' not in user_profile:
                logger.info(f"✅ Connected as: {user_profile.get('displayName', 'Unknown')}")
                logger.info("✅ Cookie-based connection established")
                return True
            else:
                logger.error("❌ Cookie-based connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def handle_initialize(self, request):
        """Handle MCP initialize request"""
        request_id = request.get("id", 1)
        success = self.initialize_manager()
        self.initialized = success
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "mcp-atlassian-extended",
                    "version": "1.5.0"
                }
            }
        }
    
    def handle_list_tools(self, request):
        """Handle tools/list request"""
        request_id = request.get("id", 1)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": self.manager.tools}
        }
    
    def handle_call_tool(self, request):
        """Handle tools/call request"""
        request_id = request.get("id", 1)
        
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -1, "message": "Server not initialized"}
            }
        
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            result = self.manager.execute_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }]
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -1, "message": f"Error: {str(e)}"}
            }
    
    def handle_list_resources(self, request):
        """Handle resources/list request"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": {"resources": []}
        }
    
    def handle_list_prompts(self, request):
        """Handle prompts/list request"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": {"prompts": []}
        }
    
    def handle_request(self, request):
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        request_id = request.get("id", 1)
        
        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "tools/list":
            return self.handle_list_tools(request)
        elif method == "tools/call":
            return self.handle_call_tool(request)
        elif method == "resources/list":
            return self.handle_list_resources(request)
        elif method == "prompts/list":
            return self.handle_list_prompts(request)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
    
    def run(self):
        """Run the extended MCP server"""
        logger.info("🚀 Starting Extended MCP Atlassian Server")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Server stopped")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point"""
    server = ExtendedMCPServer()
    server.run()

if __name__ == "__main__":
    main()
