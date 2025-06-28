#!/usr/bin/env python3
"""
Advanced Cookie Reader - Handles multiple JSON formats
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

class CookieJSONReader:
    """Advanced cookie reader supporting multiple JSON formats"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = None
        self.cookies = {}
        self.format_type = None
    
    def read_file(self) -> bool:
        """Read and parse JSON file"""
        
        if not self.file_path.exists():
            print(f"❌ File not found: {self.file_path}")
            return False
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            print(f"✅ Successfully loaded: {self.file_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    
    def detect_format(self) -> str:
        """Detect the JSON format type"""
        
        if not self.data:
            return "unknown"
        
        # Format 1: Our cookie manager format
        if isinstance(self.data, dict) and 'cookies' in self.data:
            self.format_type = "cookie_manager"
            return "cookie_manager"
        
        # Format 2: Direct cookie dictionary
        if isinstance(self.data, dict) and all(isinstance(v, str) for v in self.data.values()):
            self.format_type = "direct_cookies"
            return "direct_cookies"
        
        # Format 3: Browser export format (array of cookie objects)
        if isinstance(self.data, list) and len(self.data) > 0:
            if isinstance(self.data[0], dict) and 'name' in self.data[0] and 'value' in self.data[0]:
                self.format_type = "browser_export"
                return "browser_export"
        
        # Format 4: HAR file format
        if isinstance(self.data, dict) and 'log' in self.data:
            self.format_type = "har_file"
            return "har_file"
        
        # Format 5: Nested cookie structure
        if isinstance(self.data, dict):
            for key, value in self.data.items():
                if isinstance(value, dict) and 'cookies' in value:
                    self.format_type = "nested_cookies"
                    return "nested_cookies"
        
        self.format_type = "unknown"
        return "unknown"
    
    def extract_cookies(self) -> Dict[str, str]:
        """Extract cookies based on detected format"""
        
        format_type = self.detect_format()
        
        if format_type == "cookie_manager":
            return self._extract_cookie_manager_format()
        elif format_type == "direct_cookies":
            return self._extract_direct_cookies_format()
        elif format_type == "browser_export":
            return self._extract_browser_export_format()
        elif format_type == "har_file":
            return self._extract_har_format()
        elif format_type == "nested_cookies":
            return self._extract_nested_format()
        else:
            print(f"⚠️  Unknown format, attempting generic extraction")
            return self._extract_generic_format()
    
    def _extract_cookie_manager_format(self) -> Dict[str, str]:
        """Extract from our cookie manager format"""
        
        print("📋 Format: Cookie Manager")
        cookies = self.data.get('cookies', {})
        
        # Display metadata
        if 'domain' in self.data:
            print(f"🌐 Domain: {self.data['domain']}")
        if 'timestamp' in self.data:
            import time
            age_hours = (time.time() - self.data['timestamp']) / 3600
            print(f"⏰ Age: {age_hours:.1f} hours")
        
        return cookies
    
    def _extract_direct_cookies_format(self) -> Dict[str, str]:
        """Extract from direct cookie dictionary"""
        
        print("📋 Format: Direct Cookies")
        return self.data
    
    def _extract_browser_export_format(self) -> Dict[str, str]:
        """Extract from browser export format"""
        
        print("📋 Format: Browser Export")
        cookies = {}
        
        for cookie_obj in self.data:
            if isinstance(cookie_obj, dict):
                name = cookie_obj.get('name')
                value = cookie_obj.get('value')
                domain = cookie_obj.get('domain', '')
                
                if name and value:
                    cookies[name] = value
                    
                    # Show additional info if available
                    if domain:
                        print(f"   🌐 {name}: {domain}")
        
        return cookies
    
    def _extract_har_format(self) -> Dict[str, str]:
        """Extract cookies from HAR file"""
        
        print("📋 Format: HAR File")
        cookies = {}
        
        try:
            entries = self.data.get('log', {}).get('entries', [])
            
            for entry in entries:
                request = entry.get('request', {})
                response = entry.get('response', {})
                
                # Extract from request cookies
                for cookie in request.get('cookies', []):
                    name = cookie.get('name')
                    value = cookie.get('value')
                    if name and value:
                        cookies[name] = value
                
                # Extract from response set-cookie headers
                for header in response.get('headers', []):
                    if header.get('name', '').lower() == 'set-cookie':
                        cookie_str = header.get('value', '')
                        # Parse set-cookie header
                        if '=' in cookie_str:
                            parts = cookie_str.split(';')[0]  # Get first part before attributes
                            if '=' in parts:
                                name, value = parts.split('=', 1)
                                cookies[name.strip()] = value.strip()
        
        except Exception as e:
            print(f"⚠️  Error parsing HAR: {e}")
        
        return cookies
    
    def _extract_nested_format(self) -> Dict[str, str]:
        """Extract from nested cookie structure"""
        
        print("📋 Format: Nested Structure")
        cookies = {}
        
        def find_cookies_recursive(obj, path=""):
            if isinstance(obj, dict):
                if 'cookies' in obj:
                    found_cookies = obj['cookies']
                    if isinstance(found_cookies, dict):
                        cookies.update(found_cookies)
                        print(f"   📁 Found cookies at: {path}")
                
                for key, value in obj.items():
                    find_cookies_recursive(value, f"{path}.{key}" if path else key)
        
        find_cookies_recursive(self.data)
        return cookies
    
    def _extract_generic_format(self) -> Dict[str, str]:
        """Generic extraction attempt"""
        
        print("📋 Format: Generic/Unknown")
        cookies = {}
        
        def search_for_cookies(obj, depth=0):
            if depth > 5:  # Prevent infinite recursion
                return
            
            if isinstance(obj, dict):
                # Look for cookie-like patterns
                for key, value in obj.items():
                    if isinstance(value, str) and len(value) > 10:
                        # Looks like a cookie value
                        if any(keyword in key.lower() for keyword in ['session', 'token', 'auth', 'cookie']):
                            cookies[key] = value
                    elif isinstance(value, (dict, list)):
                        search_for_cookies(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    search_for_cookies(item, depth + 1)
        
        search_for_cookies(self.data)
        return cookies
    
    def display_cookies(self, cookies: Dict[str, str]):
        """Display cookies in a formatted way"""
        
        if not cookies:
            print("❌ No cookies found")
            return
        
        print(f"\n🍪 Extracted {len(cookies)} cookies:")
        print("=" * 50)
        
        # Sort cookies by importance
        important_first = ['JIRASESSIONID', 'atlassian.xsrf.token', 'AWSALBAPP-0']
        sorted_cookies = []
        
        # Add important cookies first
        for important in important_first:
            if important in cookies:
                sorted_cookies.append((important, cookies[important]))
        
        # Add remaining cookies
        for name, value in cookies.items():
            if name not in important_first:
                sorted_cookies.append((name, value))
        
        for name, value in sorted_cookies:
            # Determine importance
            if name in important_first:
                icon = "🔑"
            elif 'session' in name.lower() or 'auth' in name.lower():
                icon = "🛡️"
            elif name.startswith('_ga'):
                icon = "📊"
            else:
                icon = "🍪"
            
            # Mask long values
            if len(value) > 30:
                display_value = f"{value[:10]}...{value[-10:]}"
            else:
                display_value = f"{value[:15]}..." if len(value) > 15 else value
            
            print(f"{icon} {name}")
            print(f"   📏 Length: {len(value)} chars")
            print(f"   🔤 Value: {display_value}")
            print()
    
    def save_as_cookie_manager_format(self, output_file: str, cookies: Dict[str, str]):
        """Save cookies in our cookie manager format"""
        
        import time
        
        cookie_data = {
            "cookies": cookies,
            "timestamp": time.time(),
            "domain": "extracted_from_json",
            "last_refresh": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_file": str(self.file_path),
            "format_detected": self.format_type
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(cookie_data, f, indent=2)
            
            print(f"✅ Cookies saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving cookies: {e}")
            return False

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 advanced_cookie_reader.py <json_file> [output_file]")
        print("\nExample:")
        print("  python3 advanced_cookie_reader.py cookies.json")
        print("  python3 advanced_cookie_reader.py har_file.json converted_cookies.json")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🔍 Advanced Cookie JSON Reader")
    print("=" * 50)
    
    # Create reader
    reader = CookieJSONReader(input_file)
    
    # Read file
    if not reader.read_file():
        return
    
    # Extract cookies
    cookies = reader.extract_cookies()
    
    # Display results
    reader.display_cookies(cookies)
    
    # Save if output file specified
    if output_file and cookies:
        reader.save_as_cookie_manager_format(output_file, cookies)
    
    # Show usage examples
    if cookies:
        print("\n🐍 Python Usage Example:")
        print("-" * 30)
        print("from cookie_manager import AutoRefreshJiraAuth")
        print(f"auth = AutoRefreshJiraAuth('https://jira.domain.com', '{output_file or 'cookies.json'}')")
        print("response = auth.get('rest/api/2/myself')")

if __name__ == "__main__":
    main()
