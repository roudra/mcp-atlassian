#!/usr/bin/env python3
"""
Convention-Based Cookie Manager

Uses convention over configuration - automatically finds config files
"""

# Suppress SSL warnings for cleaner output
import warnings
import urllib3
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

class ConventionBasedManager:
    """Cookie manager using convention over configuration"""
    
    def __init__(self):
        self.config = {}
        self.jira_url = None
        self.cookie_file = None
        self.cookies = {}
        self.session = None
        
        # Use conventions to find configuration
        self._discover_config()
        self._setup_session()
    
    def _discover_config(self):
        """Discover configuration using conventions"""
        
        print("🔍 Discovering configuration using conventions...")
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Convention 1: Look for standard config file names in order of preference
        config_candidates = [
            "jira_config.json",           # Primary convention
            "config.json",                # Generic convention
            "atlassian_config.json",      # Product-specific convention
            ".jira_config.json"           # Hidden file convention
        ]
        
        config_file = None
        for candidate in config_candidates:
            # Look in script directory first, then current directory
            for search_dir in [script_dir, Path.cwd()]:
                config_path = search_dir / candidate
                if config_path.exists():
                    config_file = str(config_path)
                    print(f"   ✅ Found config: {config_path}")
                    break
            if config_file:
                break
        
        if not config_file:
            print(f"   🔍 Searched in:")
            print(f"      Script dir: {script_dir}")
            print(f"      Current dir: {Path.cwd()}")
            raise FileNotFoundError(f"No configuration file found. Expected one of: {config_candidates}")
        
        # Load the configuration
        self._load_config(config_file)
        
        # Convention 2: Discover cookie file
        self._discover_cookie_file()
    
    def _load_config(self, config_file: str):
        """Load configuration from discovered file"""
        
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            # Extract Jira URL using conventions
            self.jira_url = (
                self.config.get('jira_url') or 
                self.config.get('url') or 
                self.config.get('base_url') or
                self.config.get('server_url')
            )
            
            if not self.jira_url:
                raise ValueError("No Jira URL found in configuration (expected: jira_url, url, base_url, or server_url)")
            
            self.jira_url = self.jira_url.rstrip('/')
            
            print(f"   🌐 Jira URL: {self.jira_url}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def _discover_cookie_file(self):
        """Discover cookie file using conventions"""
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Convention: Look for cookie files in order of preference
        cookie_candidates = [
            # From config file
            self.config.get('cookie_file'),
            self.config.get('cookies_file'),
            self.config.get('auth_file'),
            
            # Standard conventions
            "production_cookies.json",
            "cookies.json",
            "jira_cookies.json",
            "auth.json",
            ".cookies.json"
        ]
        
        # Remove None values
        cookie_candidates = [c for c in cookie_candidates if c]
        
        for candidate in cookie_candidates:
            # Look in script directory first, then current directory
            for search_dir in [script_dir, Path.cwd()]:
                cookie_path = search_dir / candidate
                if cookie_path.exists():
                    self.cookie_file = str(cookie_path)
                    print(f"   🍪 Found cookies: {cookie_path}")
                    return
        
        print(f"   🔍 Searched in:")
        print(f"      Script dir: {script_dir}")
        print(f"      Current dir: {Path.cwd()}")
        raise FileNotFoundError(f"No cookie file found. Expected one of: {cookie_candidates}")
    
    def _load_cookies(self) -> Dict[str, str]:
        """Load cookies from discovered file"""
        
        try:
            with open(self.cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            # Handle different cookie file formats using conventions
            if 'cookies' in cookie_data:
                cookies = cookie_data['cookies']
            elif 'auth' in cookie_data:
                cookies = cookie_data['auth']
            elif 'session' in cookie_data:
                cookies = cookie_data['session']
            else:
                # Assume direct cookie format
                cookies = cookie_data
            
            # Show metadata if available
            if 'timestamp' in cookie_data:
                age_hours = (time.time() - cookie_data['timestamp']) / 3600
                print(f"   📅 Cookie age: {age_hours:.1f} hours")
            
            print(f"   🍪 Loaded {len(cookies)} cookies")
            
            # Validate critical cookies
            critical_cookies = ['JIRASESSIONID']
            missing_cookies = [cookie for cookie in critical_cookies if cookie not in cookies]
            
            if missing_cookies:
                print(f"   ⚠️  Missing critical cookies: {missing_cookies}")
            else:
                print(f"   ✅ All critical cookies present")
            
            return cookies
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cookie file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading cookies: {e}")
    
    def _setup_session(self):
        """Setup requests session with cookies and headers"""
        
        # Load cookies
        self.cookies = self._load_cookies()
        
        # Create session
        self.session = requests.Session()
        
        # Set cookies
        for name, value in self.cookies.items():
            self.session.cookies.set(name, value)
        
        # Set headers from configuration or use defaults
        headers = self.config.get('headers', {})
        if headers:
            self.session.headers.update(headers)
            print(f"   📋 Applied {len(headers)} custom headers")
        
        # Set conventional default headers
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'X-Atlassian-Token': 'no-check',
            'Referer': f'{self.jira_url}/'
        }
        
        for header, value in default_headers.items():
            if header not in self.session.headers:
                self.session.headers[header] = value
    
    def test_connection(self) -> bool:
        """Test connection to Jira"""
        
        print(f"\n🧪 Testing connection to {self.jira_url}")
        
        try:
            # Get timeout from settings or use default
            timeout = self.config.get('settings', {}).get('timeout_seconds', 30)
            
            response = self.session.get(f"{self.jira_url}/rest/api/2/myself", timeout=timeout)
            
            if response.status_code == 200:
                user_data = response.json()
                display_name = user_data.get('displayName', 'Unknown')
                email = user_data.get('emailAddress', 'Unknown')
                
                print(f"   ✅ Connected successfully!")
                print(f"   👤 User: {display_name}")
                print(f"   📧 Email: {email}")
                return True
                
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed (401)")
                return False
                
            else:
                print(f"   ❌ Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def get(self, endpoint: str, **kwargs):
        """GET request with automatic URL building"""
        url = f"{self.jira_url}/{endpoint.lstrip('/')}"
        return self.session.get(url, **kwargs)
    
    def post(self, endpoint: str, **kwargs):
        """POST request with automatic URL building"""
        url = f"{self.jira_url}/{endpoint.lstrip('/')}"
        return self.session.post(url, **kwargs)
    
    def put(self, endpoint: str, **kwargs):
        """PUT request with automatic URL building"""
        url = f"{self.jira_url}/{endpoint.lstrip('/')}"
        return self.session.put(url, **kwargs)
    
    def delete(self, endpoint: str, **kwargs):
        """DELETE request with automatic URL building"""
        url = f"{self.jira_url}/{endpoint.lstrip('/')}"
        return self.session.delete(url, **kwargs)
    
    def get_discovered_files(self) -> Dict[str, str]:
        """Get information about discovered files"""
        return {
            'config_file': getattr(self, '_config_file', 'Unknown'),
            'cookie_file': self.cookie_file,
            'jira_url': self.jira_url
        }

def test_convention_based_manager():
    """Test the convention-based manager"""
    
    print("🧪 Testing Convention-Based Manager")
    print("=" * 60)
    
    try:
        # Initialize without any arguments - pure convention
        manager = ConventionBasedManager()
        
        # Show discovered configuration
        discovered = manager.get_discovered_files()
        print(f"\n📋 Discovered Configuration:")
        for key, value in discovered.items():
            print(f"   {key}: {value}")
        
        # Test connection
        if manager.test_connection():
            print(f"\n🔍 Testing API calls:")
            
            # Test user profile
            response = manager.get('rest/api/2/myself')
            if response.status_code == 200:
                user = response.json()
                print(f"   ✅ User profile: {user.get('displayName')}")
            
            # Test issue search
            response = manager.get('rest/api/2/search?jql=assignee=currentUser()&maxResults=3')
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Issue search: {data.get('total', 0)} issues")
            
            print(f"\n✅ Convention-based manager working perfectly!")
            
        else:
            print(f"\n❌ Connection test failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_convention_based_manager()
