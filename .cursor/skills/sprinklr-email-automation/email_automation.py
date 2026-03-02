"""
Email Automation Script for Sprinklr Console
Monitors the Console tab for new emails, extracts content, queries Cursor AI,
and writes responses back to the email composition area.
"""

import re
import time
import json
import subprocess
import logging
import os
import sys
import requests
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)

# Resolve paths: script may live under .cursor/skills/sprinklr-email-automation/
_script_dir = Path(__file__).resolve().parent


def _find_repo_root() -> Path:
    d = _script_dir
    for _ in range(10):
        if (d / "config.json").exists() or (d / ".cursor").is_dir():
            return d
        if d.parent == d:
            break
        d = d.parent
    return Path.cwd()


_repo_root = _find_repo_root()
_log_file = _script_dir / "email_automation.log"
_log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailAutomation:
    """Main class for email automation"""
    
    def __init__(self, url: str, cursor_cli_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the email automation system
        
        Args:
            url: The Sprinklr console URL
            cursor_cli_path: Path to Cursor CLI (optional, will try to find it)
            config: Optional configuration dictionary
        """
        self.url = url
        self.config = config or {}
        self.cursor_cli_path = cursor_cli_path or self.config.get('cursor_cli_path') or self._find_cursor_cli()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.selectors = self.config.get('selectors', {})
        self.case_ids_file = Path('processed_case_ids.json')
        self.processed_case_ids = self._load_processed_case_ids()
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        # Cursor/OpenAI API configuration
        self.openai_api_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        self.cursor_api_key = config.get('cursor_api_key')  # Legacy support
        # Try local Cursor API first (if running locally), then fallback to OpenAI API
        self.cursor_api_url = config.get('cursor_api_url', 'http://localhost:3000/api/chat')  # Local Cursor API
        
        # Login credentials
        self.login_email = config.get('login_email', 'harun.husic.external@telefonica.com')
        self.login_password = config.get('login_password', 'Avalon!1_1')
        self.login_url = config.get('login_url', 'https://telefonica-germany-app.sprinklr.com/ui/login')
        
    def _load_processed_case_ids(self) -> set:
        """Load previously processed case IDs from file"""
        try:
            if self.case_ids_file.exists():
                with open(self.case_ids_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('case_ids', []))
        except Exception as e:
            logger.warning(f"Could not load processed case IDs: {e}")
        return set()
    
    def _save_processed_case_ids(self):
        """Save processed case IDs to file"""
        try:
            with open(self.case_ids_file, 'w', encoding='utf-8') as f:
                json.dump({'case_ids': list(self.processed_case_ids)}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not save processed case IDs: {e}")
    
    def _find_cursor_cli(self) -> Optional[str]:
        """Try to find Cursor CLI or IDE in common locations"""
        import shutil
        
        # First try cursor-agent CLI in PATH
        cursor_agent = shutil.which('cursor-agent')
        if cursor_agent:
            logger.info(f"Found cursor-agent CLI: {cursor_agent}")
            return cursor_agent
        
        # Try WSL directly first (most reliable for Windows)
        try:
            result = subprocess.run(
                ['wsl', 'bash', '-c', 'test -f ~/.local/bin/cursor-agent && echo found'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and 'found' in result.stdout:
                logger.info("Found cursor-agent in WSL, will use WSL directly")
                # Return a special marker that we'll handle in the query method
                return 'wsl://cursor-agent'
        except:
            pass
        
        # Try wrapper scripts in current directory (for WSL) as fallback
        wrapper_bat = Path('cursor-agent-wrapper.bat')
        wrapper_ps1 = Path('cursor-agent-wrapper.ps1')
        if wrapper_bat.exists():
            logger.info(f"Found cursor-agent wrapper: {wrapper_bat.absolute()}")
            return str(wrapper_bat.absolute())
        elif wrapper_ps1.exists():
            logger.info(f"Found cursor-agent wrapper: {wrapper_ps1.absolute()}")
            return f'powershell.exe -File "{wrapper_ps1.absolute()}"'
        
        # Try cursor CLI
        cursor_path = shutil.which('cursor')
        if cursor_path:
            logger.info(f"Found cursor CLI: {cursor_path}")
            return cursor_path
        
        # Common Windows paths for Cursor IDE
        username = os.getenv('USERNAME') or Path.home().name
        common_paths = [
            rf"C:\Users\{username}\AppData\Local\Programs\cursor\Cursor.exe",
            r"C:\Program Files\Cursor\Cursor.exe",
            r"C:\Program Files (x86)\Cursor\Cursor.exe",
            rf"{Path.home()}\AppData\Local\Programs\cursor\Cursor.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                logger.info(f"Found Cursor IDE: {path}")
                return path
        
        logger.warning("Cursor CLI (cursor-agent) not found!")
        logger.info("To use Cursor programmatically, please install cursor-agent CLI:")
        logger.info("Visit: https://docs.cursor.com/en/cli/installation")
        logger.info("Or run: python setup_cursor_cli.py")
        return None
    
    def _find_cursor_workspace(self) -> Optional[Path]:
        """Find Cursor workspace directory (current project)"""
        # Check for .cursorrules file (indicates Cursor workspace)
        current_dir = Path.cwd()
        if (current_dir / '.cursorrules').exists():
            return current_dir
        
        # Check parent directories
        for parent in current_dir.parents:
            if (parent / '.cursorrules').exists():
                return parent
        
        return None
    
    def _load_cursor_rules(self) -> str:
        """Load .cursorrules file if it exists"""
        workspace = self._find_cursor_workspace()
        if workspace:
            cursorrules_file = workspace / '.cursorrules'
            if cursorrules_file.exists():
                try:
                    with open(cursorrules_file, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.debug(f"Could not load .cursorrules: {e}")
        return ""
    
    def connect_to_browser(self, cdp_endpoint: Optional[str] = None, leave_page_unchanged: bool = False):
        """
        Connect to an existing Chrome browser instance via CDP (Chrome DevTools Protocol)
        
        Args:
            cdp_endpoint: CDP endpoint URL (e.g., 'http://localhost:9222')
                         If None, will try to find Chrome's CDP endpoint
        """
        logger.info("Connecting to existing Chrome browser instance...")
        self.playwright = sync_playwright().start()
        
        if cdp_endpoint:
            endpoint = cdp_endpoint
        else:
            # Try to find Chrome's CDP endpoint
            # Chrome typically uses port 9222 when launched with --remote-debugging-port
            endpoint = self._find_cdp_endpoint()
        
        # Try to connect to existing Chrome first, if endpoint found
        if endpoint:
            logger.info(f"Connecting to CDP endpoint: {endpoint}")
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(endpoint)
                logger.info("Successfully connected to existing Chrome instance")
                print("[INFO] Connected to existing Chrome instance")
            except Exception as e:
                logger.error(f"Failed to connect to CDP endpoint: {e}")
                raise Exception(
                    f"Could not connect to existing browser instance at {endpoint}.\n"
                    "Please ensure Chrome/Edge is running with --remote-debugging-port=9222"
                )
        else:
            logger.error("No CDP endpoint found.")
            raise Exception(
                "No browser instance found with remote debugging enabled.\n"
                "Please launch Chrome/Edge with --remote-debugging-port=9222 first."
            )
        
        # REMOVED: Browser launch code - only connect to existing instance
        if False:  # This block will never execute, kept for reference
            try:
                # Try to find Chrome executable path
                chrome_paths = [
                    f"{os.environ.get('LOCALAPPDATA', '')}\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                ]
                chrome_executable = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_executable = path
                        logger.info(f"Found Chrome at: {chrome_executable}")
                        break
                
                # Launch Chrome explicitly using the executable path
                # Configure Chrome to always allow sound/audio without prompts
                chrome_args = [
                    '--remote-debugging-port=9222',
                    '--autoplay-policy=no-user-gesture-required',  # Allow autoplay
                    '--disable-features=BlockInsecurePrivateNetworkRequests',  # Allow permissions
                    '--use-fake-ui-for-media-stream',  # Auto-grant media permissions (no popup)
                    '--use-fake-device-for-media-stream',  # Use fake devices to avoid permission prompts
                ]
                
                launch_options = {
                    'headless': False,
                    'args': chrome_args
                }
                if chrome_executable:
                    launch_options['executable_path'] = chrome_executable
                    logger.info(f"Launching Chrome from: {chrome_executable}")
                    print(f"[INFO] Launching Chrome from: {chrome_executable}")
                else:
                    logger.info("Chrome executable not found, using Playwright's Chromium")
                    print("[INFO] Using Playwright's Chromium (Chrome executable not found)")
                
                self.browser = self.playwright.chromium.launch(**launch_options)
                logger.info("Launched Chrome browser with Playwright")
                print("[INFO] Launched Chrome browser with Playwright")
            except Exception as e:
                raise Exception(
                    f"Failed to launch Chrome with Playwright: {e}\n"
                    "Make sure Chrome is installed or run: playwright install chromium"
                )
        
        # Get the first available page - USE EXISTING PAGE, don't create new one
        contexts = self.browser.contexts
        if contexts and len(contexts) > 0:
            context = contexts[0]
            pages = context.pages
            if pages and len(pages) > 0:
                # Use the first existing page (existing tab)
                self.page = pages[0]
                logger.info("Connected to existing page/tab")
                print(f"[INFO] Using existing page/tab: {self.page.url}")
            else:
                # No pages exist - wait a moment for pages to load, then try again
                logger.warning("No pages found in context, waiting for pages to load...")
                time.sleep(1)
                pages = context.pages
                if pages and len(pages) > 0:
                    self.page = pages[0]
                    logger.info("Connected to existing page after wait")
                    print(f"[INFO] Using existing page: {self.page.url}")
                else:
                    raise Exception(
                        "No existing pages/tabs found in browser.\n"
                        "Please ensure you have at least one tab open in the browser instance."
                    )
        else:
            raise Exception(
                "No browser contexts found.\n"
                "Please ensure the browser instance has at least one tab open."
            )
        
        # Grant sound/audio permissions for Sprinklr domains - CRITICAL: Do this BEFORE any navigation
        try:
            sprinklr_origins = [
                "https://telefonica-germany.sprinklr.com",
                "https://telefonica-germany-app.sprinklr.com",
                "https://sprinklr.com",
            ]
            for origin in sprinklr_origins:
                try:
                    # Grant both microphone and notifications (sound requires these)
                    context.grant_permissions(['microphone', 'notifications'], origin=origin)
                    logger.info(f"Granted microphone and notifications permissions for {origin}")
                    print(f"[PERMISSIONS] Granted sound/audio permissions for {origin} - NO POPUPS")
                except Exception as e:
                    logger.debug(f"Could not grant permissions for {origin}: {e}")
        except Exception as e:
            logger.debug(f"Error granting permissions: {e}")
        
        # Set up automatic audio permission granting via JavaScript - runs on EVERY page load
        try:
            self.page.add_init_script("""
                // Override permission query to always return 'granted' for audio
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = function(parameters) {
                    if (parameters.name === 'microphone' || parameters.name === 'notifications') {
                        return Promise.resolve({ state: 'granted', onchange: null });
                    }
                    return originalQuery.apply(this, arguments);
                };
                
                // Auto-grant audio permissions immediately when page loads - NO POPUPS
                (async function() {
                    try {
                        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            stream.getTracks().forEach(track => track.stop());
                            console.log('[AUTO-PERMISSION] Audio permission auto-granted - NO POPUP');
                        }
                    } catch (e) {
                        console.log('[AUTO-PERMISSION] Audio permission setup:', e.message);
                    }
                })();
            """)
            logger.info("Added init script to auto-grant audio permissions (no popups)")
            print("[PERMISSIONS] Added script to auto-grant audio permissions - NO POPUPS")
        except Exception as e:
            logger.debug(f"Could not add init script: {e}")
        
        # Wait a moment for connection to stabilize
        time.sleep(1)
        
        # Grant permissions for current page origin (if needed)
        try:
            current_origin = self.page.url.split('/ui/')[0] if '/ui/' in self.page.url else self.page.url.split('/app/')[0] if '/app/' in self.page.url else self.page.url
            context = self.page.context
            # Grant both microphone and notifications for sound
            context.grant_permissions(['microphone', 'notifications'], origin=current_origin)
            logger.info(f"Granted microphone and notifications permissions for current page: {current_origin}")
            print(f"[PERMISSIONS] Granted sound/audio permissions for current page - NO POPUPS")
        except Exception as e:
            logger.debug(f"Could not grant permissions: {e}")
        
        # Conditional popup/dialog resolution (per debugg (2).md): accept any JS/browser dialogs so they don't block
        try:
            def _on_dialog(dialog):
                logger.info(f"Dialog appeared: {dialog.type} - {(dialog.message or '')[:80]}")
                print(f"[POPUP] Accepting dialog: {dialog.type}")
                dialog.accept()
            self.page.on("dialog", _on_dialog)
            logger.info("Dialog listener added: dialogs will be accepted automatically")
        except Exception as e:
            logger.debug(f"Could not add dialog listener: {e}")
        
        # Detect current page state using smart detection
        current_state = self._detect_page_state()
        print(f"[PAGE STATE] Current page state: {current_state}")
        logger.info(f"Detected page state: {current_state}")
        
        # SMART LOGIN DETECTION - Only login if not already logged in
        logger.info("Checking login status with smart detection...")
        print("[INFO] Using smart detection to check if login is needed...")
        self._check_and_login()
        
        if leave_page_unchanged:
            # Process-current-only / extract-only: do NOT navigate; leave email content page as-is
            logger.info("Leave-page-unchanged: skipping ensure_console_page and status/email checks")
            print("[INFO] Leaving current page unchanged (read-email skill will use it as-is).")
        else:
            # Use smart detection to ensure console page (only navigates if needed)
            self.ensure_console_page()
            # Re-detect state after ensuring console page
            current_state = self._detect_page_state()
            print(f"[PAGE STATE] After navigation check: {current_state}")
            # Set status to "Verfügbar" if needed (smart detection - skips if already set)
            if current_state in ['console', 'unknown']:
                self._set_available_status()
            # Check for already visible emails
            self._check_visible_emails()
    
    def _check_login_status(self) -> bool:
        """
        Check if already logged in
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")
            
            # Check if we're on login page
            if 'login' in current_url.lower() or 'ui/login' in current_url:
                logger.info("On login page - not logged in")
                print("[LOGIN CHECK] On login page - not logged in")
                return False
            
            # Check if we're already logged in by looking for common logged-in elements
            logged_in_indicators = [
                '[data-testid*="case"]',
                '[data-testid="collapsed-case-item"]',  # Email cases
                'text="Console"',
                '[aria-label*="Console"]',
                'h2:has-text("Fall #")',  # Case header
                '[data-testid="html-message-content"]',  # Email content
            ]
            
            for indicator in logged_in_indicators:
                try:
                    elem = self.page.locator(indicator).first
                    if elem.is_visible(timeout=2000):
                        logger.info("Already logged in - found logged-in indicator")
                        print(f"[LOGIN CHECK] Already logged in (found: {indicator})")
                        return True
                except:
                    continue
            
            logger.info("Could not find logged-in indicators")
            print("[LOGIN CHECK] Could not determine login status")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            print(f"[LOGIN CHECK] Error: {e}")
            return False
    
    def _check_and_login(self):
        """Check if login is needed and perform login if necessary"""
        try:
            print("\n[LOGIN] Checking login status...")
            
            # Check if already logged in
            if self._check_login_status():
                logger.info("Already logged in, skipping login")
                print("[LOGIN] Already logged in - skipping")
                return True
            
            # Check current URL
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")
            
            # Navigate to login page if not already there
            if 'login' not in current_url.lower() and 'ui/login' not in current_url:
                logger.info("Not on login page, navigating...")
                print("[LOGIN] Navigating to login page...")
                self.page.goto(self.login_url, wait_until='networkidle')
                time.sleep(1)
            
            logger.info("Attempting to login...")
            print("[LOGIN] Attempting to login...")
            return self._perform_login()
                    
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            print(f"[LOGIN] Error: {e}")
            return False
    
    def _perform_login(self):
        """Perform the login process"""
        try:
            logger.info("Filling in login credentials...")
            
            # Wait for email input field
            email_selectors = [
                'input[name="uid"]',
                'input[type="email"][aria-label*="Email"]',
                'input[placeholder*="Email"]',
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = self.page.locator(selector).first
                    if email_input.is_visible(timeout=3000):
                        email_input.click()
                        time.sleep(0.5)
                        email_input.fill('')  # Clear existing value
                        email_input.type(self.login_email, delay=50)
                        email_filled = True
                        logger.info("Email filled")
                        break
                except:
                    continue
            
            if not email_filled:
                logger.error("Could not find email input field")
                return False
            
            time.sleep(0.5)
            
            # Fill password
            password_selectors = [
                'input[name="pass"]',
                'input[type="password"][aria-label*="Password"]',
                'input[placeholder*="Password"]',
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = self.page.locator(selector).first
                    if password_input.is_visible(timeout=2000):
                        password_input.click()
                        time.sleep(0.5)
                        password_input.fill('')
                        password_input.type(self.login_password, delay=50)
                        password_filled = True
                        logger.info("Password filled")
                        break
                except:
                    continue
            
            if not password_filled:
                logger.error("Could not find password input field")
                return False
            
            time.sleep(1)
            
            # Submit the form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Anmelden")',
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.page.locator(selector).first
                    if submit_button.is_visible(timeout=2000):
                        submit_button.click()
                        logger.info("Login form submitted")
                        break
                except:
                    continue
            
            # Wait for navigation after login
            logger.info("Waiting for login to complete...")
            # Wait for URL to change or for login to complete
            max_wait = 15
            waited = 0
            while waited < max_wait:
                current_url = self.page.url
                if 'login' not in current_url.lower() and 'sprinklr.com' in current_url:
                    logger.info("Login appears to have completed")
                    break
                time.sleep(1)
                waited += 1
            
            time.sleep(1)  # Brief wait for page to stabilize
            
            # Navigate to console URL if needed
            if self.url not in self.page.url:
                logger.info(f"Navigating to console URL: {self.url}")
                try:
                    self.page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                    time.sleep(1.5)
                except Exception as e:
                    logger.warning(f"Navigation timeout, but continuing: {e}")
                    # Try to wait a bit more and check if we're on the right page
                    time.sleep(1)
            
            logger.info("Login process completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def _close_popups(self):
        """Popup handling disabled - user has resolved popup issue"""
        # Popup handling removed per user request
        pass
    
    def _check_visible_emails(self):
        """Check if there are already visible emails on the console page"""
        try:
            print("\n[INITIAL CHECK] Checking for already visible emails...")
            
            # Look for collapsed-case-item buttons
            visible_emails = self.page.locator('[data-testid="collapsed-case-item"]').all()
            
            if visible_emails:
                print(f"[INITIAL CHECK] Found {len(visible_emails)} visible email(s) on console page")
                logger.info(f"Found {len(visible_emails)} visible email(s) on console page")
                
                # Check if any are new (not processed)
                new_count = 0
                for email_elem in visible_emails:
                    try:
                        text_content = email_elem.inner_text(timeout=1000)
                        case_id = self.extract_case_id(text_content)
                        if case_id and case_id not in self.processed_case_ids:
                            new_count += 1
                            print(f"[INITIAL CHECK] New email detected: {case_id}")
                    except:
                        continue
                
                if new_count > 0:
                    print(f"[INITIAL CHECK] {new_count} new email(s) ready to process")
                else:
                    print(f"[INITIAL CHECK] All visible emails have been processed")
            else:
                print("[INITIAL CHECK] No visible emails on console page")
                logger.info("No visible emails on console page")
                
        except Exception as e:
            logger.error(f"Error checking visible emails: {e}")
            print(f"[INITIAL CHECK] Error checking visible emails: {e}")
    
    def _check_status(self) -> str:
        """
        Check current status
        
        Returns:
            'verfügbar' if already set to Verfügbar, 'other' if different status, 'unknown' if can't determine
        """
        try:
            # Look for status indicators that show "Verfügbar" is already set
            verfügbar_indicators = [
                'span:has-text("Verfügbar")',
                '[data-spaceweb="tag"]:has-text("Verfügbar")',
                'div:has-text("Verfügbar")',
            ]
            
            for selector in verfügbar_indicators:
                try:
                    elem = self.page.locator(selector).first
                    if elem.is_visible(timeout=2000):
                        # Check if it's the active status (usually has green background or is highlighted)
                        parent = elem.locator('..')
                        parent_classes = parent.get_attribute('class') or ''
                        # Check for green background indicator
                        try:
                            # Look for green circle indicator
                            green_indicator = parent.locator('div[style*="rgb(0, 128, 0)"]').first
                            if green_indicator.is_visible(timeout=500):
                                logger.info("Status is already set to 'Verfügbar'")
                                print("[STATUS CHECK] Already set to 'Verfügbar'")
                                return 'verfügbar'
                        except:
                            pass
                        
                        # Also check if the text is in the status button (not just dropdown)
                        text = elem.inner_text()
                        if 'Verfügbar' in text and len(text) < 50:  # Short text means it's the button, not dropdown item
                            logger.info("Status is already set to 'Verfügbar'")
                            print("[STATUS CHECK] Already set to 'Verfügbar'")
                            return 'verfügbar'
                except:
                    continue
            
            # Check for other status indicators
            other_status_indicators = [
                'span:has-text("Nicht verfügbar")',
                'span:has-text("Pause")',
                'span:has-text("Vorbereitungszeit")',
            ]
            
            for selector in other_status_indicators:
                try:
                    elem = self.page.locator(selector).first
                    if elem.is_visible(timeout=1000):
                        status_text = elem.inner_text()
                        logger.info(f"Current status: {status_text}")
                        print(f"[STATUS CHECK] Current status: {status_text}")
                        return 'other'
                except:
                    continue
            
            logger.warning("Could not determine current status")
            print("[STATUS CHECK] Could not determine current status")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            return 'unknown'
    
    def _set_available_status(self):
        """Set status to 'Verfügbar' (Available) if not already set"""
        try:
            logger.info("Checking current status...")
            print("\n[STATUS] Checking current status...")
            
            # First check if already set to Verfügbar
            current_status = self._check_status()
            if current_status == 'verfügbar':
                logger.info("Status is already 'Verfügbar', no need to change")
                print("[STATUS] Already set to 'Verfügbar' - skipping")
                return True
            
            logger.info("Status is not 'Verfügbar', attempting to set it...")
            print("[STATUS] Setting status to 'Verfügbar'...")
            
            # Look for the status dropdown button - try to find the status tag
            # Based on HTML: span[data-spaceweb="tag"] with text like "008_Vorbereitungszeit"
            status_button_selectors = [
                'span[data-spaceweb="tag"]:has-text("Vorbereitungszeit")',
                'span[data-spaceweb="tag"]:has-text("Verfügbar")',
                'span[data-spaceweb="tag"]',
                'button:has-text("Vorbereitungszeit")',
                'button:has-text("Verfügbar")',
            ]
            
            status_button = None
            for selector in status_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        status_button = btn
                        logger.info("Found status button")
                        print(f"[STATUS] Found status button with selector: {selector}")
                        break
                except:
                    continue
            
            if not status_button:
                logger.warning("Could not find status button - may already be set or not visible")
                print("[STATUS] Could not find status button")
                return False
            
            # Click to open dropdown
            status_button.click()
            time.sleep(1)
            print("[STATUS] Opened status dropdown")
            
            # Look for "Verfügbar" option in dropdown
            verfügbar_selectors = [
                'li:has-text("Verfügbar")',
                '[data-spaceweb="list-item"]:has-text("Verfügbar")',
                'li[role="option"]:has-text("Verfügbar")',
            ]
            
            for selector in verfügbar_selectors:
                try:
                    verfügbar_option = self.page.locator(selector).first
                    if verfügbar_option.is_visible(timeout=2000):
                        verfügbar_option.click()
                        logger.info("Status set to 'Verfügbar'")
                        print("[STATUS] Successfully set to 'Verfügbar'")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            logger.warning("Could not find 'Verfügbar' option in dropdown")
            print("[STATUS] Could not find 'Verfügbar' option in dropdown")
            return False
            
        except Exception as e:
            logger.error(f"Error setting status: {e}")
            print(f"[STATUS] Error: {e}")
            return False
    
    def _find_cdp_endpoint(self) -> Optional[str]:
        """Try to find Chrome's CDP endpoint"""
        import socket
        # Common CDP ports
        ports = [9222, 9223, 9224]
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    return f"http://localhost:{port}"
            except:
                continue
        return None
    
    def _detect_page_state(self) -> str:
        """
        Detect which page we're currently on
        
        Returns:
            'console' if on console page, 'email_content' if on email content page, 'unknown' otherwise
        """
        try:
            # First, check URL patterns as a quick indicator
            current_url = self.page.url.lower()
            url_has_console = '/console' in current_url or '/app/console' in current_url
            url_has_email = '/case/' in current_url or '/email/' in current_url or 'fall' in current_url
            
            # Check for email content page indicators (highest priority)
            email_content_indicators = [
                'h2:has-text("Fall #")',  # Case header
                '[data-testid="html-message-content"]',  # Email body
                'section[aria-label="Nachricht verfassen"]',  # Email editor
                '[data-testid="inboundChatConversationItemFanMessage"]',  # Inbound message container
            ]
            
            for indicator in email_content_indicators:
                try:
                    elem = self.page.locator(indicator).first
                    if elem.is_visible(timeout=1000):
                        logger.info(f"Detected: Email content page (indicator: {indicator})")
                        print(f"[PAGE DETECTION] Email content page detected via: {indicator}")
                        return 'email_content'
                except:
                    continue
            
            # If URL suggests email content but no indicators found, still return email_content
            if url_has_email and not url_has_console:
                logger.info("Detected: Email content page (URL pattern)")
                print("[PAGE DETECTION] Email content page detected via URL pattern")
                return 'email_content'
            
            # Check for console page indicators (more comprehensive)
            console_indicators = [
                '[data-testid*="console"]',  # Console test IDs
                'text="Console"',  # Console text
                '[data-testid="collapsed-case-item"]',  # Email items in console (even if empty list)
                '[aria-label*="Console"]',  # Console aria labels
                'button:has-text("Console")',  # Console button
                # Check for console page structure elements
                '[data-testid*="case-item"]',  # Case items
                '[class*="console"]',  # Console classes (as fallback)
            ]
            
            for indicator in console_indicators:
                try:
                    elem = self.page.locator(indicator).first
                    if elem.is_visible(timeout=1000):
                        logger.info(f"Detected: Console page (indicator: {indicator})")
                        print(f"[PAGE DETECTION] Console page detected via: {indicator}")
                        return 'console'
                except:
                    continue
            
            # Check if URL suggests console page (even if elements not visible yet)
            if url_has_console:
                logger.info("Detected: Console page (URL pattern)")
                print("[PAGE DETECTION] Console page detected via URL pattern")
                return 'console'
            
            # Check for login page
            if 'login' in current_url or 'ui/login' in current_url:
                logger.info("Detected: Login page")
                print("[PAGE DETECTION] Login page detected")
                return 'login'
            
            # Last resort: check if we can find any Sprinklr-specific elements
            try:
                # Check for any Sprinklr page structure
                sprinklr_indicators = [
                    '[data-spaceweb]',  # Spaceweb components
                    '[data-testid]',  # Any test IDs
                    'html[lang="de"]',  # German HTML (Sprinklr uses this)
                ]
                for indicator in sprinklr_indicators:
                    try:
                        elem = self.page.locator(indicator).first
                        if elem.is_visible(timeout=500):
                            # If we find Sprinklr elements but can't determine exact page,
                            # and URL has console, assume console
                            if url_has_console:
                                logger.info("Detected: Console page (Sprinklr elements + URL)")
                                print("[PAGE DETECTION] Console page detected (Sprinklr elements + URL)")
                                return 'console'
                            break
                    except:
                        continue
            except:
                pass
            
            logger.warning("Could not determine page state - assuming unknown")
            print("[PAGE DETECTION] Could not determine page state - returning 'unknown'")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error detecting page state: {e}")
            print(f"[PAGE DETECTION] Error: {e}")
            return 'unknown'
    
    def ensure_console_page(self):
        """Ensure we're on the console page, navigate if needed - AVOID UNNECESSARY RELOADS"""
        current_state = self._detect_page_state()
        
        # If already on console, return immediately (no navigation needed)
        if current_state == 'console':
            logger.debug("Already on console page - no navigation needed")
            return True
        
        # Check URL first - if we're already on console URL, don't reload
        current_url = self.page.url.lower()
        url_has_console = '/console' in current_url or '/app/console' in current_url
        
        if url_has_console and current_state == 'unknown':
            # We're on console URL but detection failed - might be loading
            # Wait a bit and check again instead of reloading
            logger.info("On console URL but state unknown - waiting for page to load...")
            time.sleep(1)
            current_state = self._detect_page_state()
            if current_state == 'console':
                return True
            # If still unknown but URL is correct, assume we're on console
            logger.info("Still unknown but URL is console - assuming console page")
            return True
        
        if current_state == 'email_content':
            logger.info("On email content page, navigating back to console...")
            # Try to go back first (doesn't reload, just history navigation)
            try:
                self.page.go_back()
                time.sleep(1)  # Wait for navigation
                new_state = self._detect_page_state()
                if new_state == 'console':
                    return True
            except Exception as e:
                logger.debug(f"go_back() failed: {e}")
            
            # Try to find and click console tab/navigation (no reload, just click)
            console_selectors = self.selectors.get('console_tab', [
                'text="Console"',
                '[aria-label*="Console"]',
                '[data-testid*="console"]',
            ])
            
            for selector in console_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if elem.is_visible(timeout=2000):
                        elem.click()
                        time.sleep(1)
                        new_state = self._detect_page_state()
                        if new_state == 'console':
                            return True
                except:
                    continue
            
            logger.warning("Could not navigate to console page via navigation")
            return False
        
        # Only navigate to URL if we're NOT already on console URL
        # This prevents unnecessary reloads
        if not url_has_console:
            logger.info("Not on console URL, navigating to console URL...")
            try:
                self.page.goto(self.url, wait_until='domcontentloaded', timeout=60000)  # Use domcontentloaded instead of networkidle to be faster
                time.sleep(1)  # Wait for page load
                self._open_console_tab()
                return self._detect_page_state() == 'console'
            except Exception as e:
                logger.error(f"Error navigating to console: {e}")
                return False
        else:
            # We're on console URL but detection says unknown - might be a loading state
            logger.info("On console URL but state unknown - assuming console page")
            return True
    
    def ensure_email_content_page(self):
        """Ensure we're on the email content page"""
        current_state = self._detect_page_state()
        
        if current_state == 'email_content':
            logger.debug("Already on email content page")
            return True
        
        logger.warning("Not on email content page - cannot extract email content")
        return False
    
    def _open_console_tab(self):
        """Open the Console tab from the sidebar"""
        logger.info("Opening Console tab...")
        try:
            # Wait for sidebar to be available
            time.sleep(1)
            
            # Look for the Console tab/icon in the sidebar
            console_selectors = self.selectors.get('console_tab', [
                'text="Console"',
                '[aria-label*="Console"]',
                '[data-testid*="console"]',
                'button:has-text("Console")',
            ])
            
            for selector in console_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        element.click()
                        logger.info("Console tab opened")
                        time.sleep(1)
                        return
                except:
                    continue
            
            logger.warning("Could not find Console tab automatically. Please open it manually.")
        except Exception as e:
            logger.error(f"Error opening Console tab: {e}")
    
    def extract_case_id(self, text: str) -> Optional[str]:
        """
        Extract case ID from text (format: # followed by at least 6 numbers)
        
        Args:
            text: Text to search for case ID
            
        Returns:
            Case ID if found, None otherwise
        """
        pattern = r'#(\d{6,})'
        match = re.search(pattern, text)
        if match:
            case_id = f"#{match.group(1)}"
            return case_id
        return None
    
    def get_new_emails(self) -> List[Dict]:
        """
        Get list of new emails from the Console tab
        
        Returns:
            List of email dictionaries with case_id, content, etc.
        """
        new_emails = []
        
        # Ensure we're on the console page
        if not self.ensure_console_page():
            logger.warning("Cannot get emails - not on console page")
            print("[EMAIL DETECTION] Cannot get emails - not on console page")
            return new_emails
        
        try:
            print("[EMAIL DETECTION] Scanning for new emails...")
            # Find all email entries in the Console
            # Priority 1: collapsed preview buttons in the sidebar (newest emails)
            # Priority 2: case list cards in the console stream
            email_selectors = [
                '[data-entityid="CollapsedPreviewsList"] button[data-testid="collapsed-case-item"]',  # Collapsed preview for new emails
                '[data-testid="case-item-root"] div.cardItem',  # Console stream case cards (including SLA, name, subject, preview)
            ] + self.selectors.get('email_item', [
                '[data-testid*="email"]',
                '[data-testid*="message"]',
                '.email-item',
                '[class*="email"]',
            ])
            
            email_elements = []
            for selector in email_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    if elements:
                        email_elements = elements
                        break
                except:
                    continue
            
            if not email_elements:
                logger.debug("No email elements found")
                print("[EMAIL DETECTION] No email elements found")
                return new_emails
            
            print(f"[EMAIL DETECTION] Found {len(email_elements)} email element(s) to check")
            
            for element in email_elements:
                try:
                    # Get text content
                    text_content = element.inner_text(timeout=1000)
                    
                    # Extract case ID from text or from data attributes
                    case_id = self.extract_case_id(text_content)
                    
                    # If no case ID in text, try to get it from the element's data attributes or parent
                    if not case_id:
                        try:
                            # Try to find case ID in nearby elements
                            parent = element.locator('..')
                            parent_text = parent.inner_text(timeout=500)
                            case_id = self.extract_case_id(parent_text)
                        except:
                            pass
                    
                    # For collapsed-case-item, we might need to click first to get the case ID
                    # But we'll process it anyway if it's a new element
                    if not case_id:
                        # Generate a temporary ID based on element position or content hash
                        # This will be updated when we click and see the actual case ID
                        element_hash = hash(text_content[:50]) % 1000000
                        case_id = f"#TEMP{element_hash}"
                        logger.debug(f"Temporary case ID assigned: {case_id}")
                    
                    if case_id and case_id not in self.processed_case_ids:
                        # This is a new email
                        email_data = {
                            'case_id': case_id,
                            'element': element,
                            'text_content': text_content,
                            'timestamp': datetime.now().isoformat(),
                            'is_temp_id': case_id.startswith('#TEMP')
                        }
                        new_emails.append(email_data)
                        logger.info(f"Found new email with case ID: {case_id}")
                        # Print for testing
                        print("\n" + "="*80)
                        print(f"NEW EMAIL DETECTED - Case ID: {case_id}")
                        print("="*80)
                        print(f"Text Content Preview:")
                        print(text_content[:500] + ("..." if len(text_content) > 500 else ""))
                        print("="*80 + "\n")
                        
                except Exception as e:
                    logger.debug(f"Error processing email element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error getting new emails: {e}")
        
        return new_emails
    
    def extract_email_content(self) -> Dict:
        """
        Extract email content from the current page (when already on email content page)
        
        Returns:
            Dictionary with full email content including body, subject, attachments
        """
        # Verify we're on email content page
        if not self.ensure_email_content_page():
            logger.warning("Not on email content page, cannot extract content")
            return {'case_id': '', 'subject': '', 'from': '', 'body': '', 'attachments': []}
        
        # Create email_data dict for compatibility with click_email_and_extract_content
        # The function will skip clicking since already_on_content_page is True
        email_data = {
            'case_id': '',  # Will be extracted
            'already_on_content_page': True,
            'element': None  # Not needed since we're already on the page
        }
        
        # Use the same extraction logic by calling click_email_and_extract_content
        # It will skip the click and go straight to extraction
        return self.click_email_and_extract_content(email_data)
    
    def click_email_and_extract_content(self, email_data: Dict) -> Dict:
        """
        Click on an email and extract its full content
        
        Args:
            email_data: Dictionary containing email information
            
        Returns:
            Dictionary with full email content including body, subject, attachments
        """
        logger.info(f"Processing email with case ID: {email_data['case_id']}")
        
        # Check if we're already on the email content page
        if email_data.get('already_on_content_page', False):
            logger.info("Already on email content page, skipping click")
            print("[INFO] Already on email content page, extracting content directly...")
        else:
            # Ensure we're on console page before clicking
            if not self.ensure_console_page():
                logger.error("Cannot click email - not on console page")
                return {'case_id': email_data['case_id'], 'subject': '', 'from': '', 'body': '', 'attachments': []}
            
            try:
                # Click on the email (collapsed-case-item button)
                if email_data.get('element'):
                    email_data['element'].click()
                    time.sleep(1.5)  # Wait for content page to load
                else:
                    logger.warning("No element to click, but not marked as already on content page")
                    return {'case_id': email_data['case_id'], 'subject': '', 'from': '', 'body': '', 'attachments': []}
            except Exception as e:
                logger.error(f"Error clicking email: {e}")
                return {'case_id': email_data['case_id'], 'subject': '', 'from': '', 'body': '', 'attachments': []}
        
        try:
            
            # Verify we're now on email content page
            if not self.ensure_email_content_page():
                logger.warning("After clicking email, not on email content page. Waiting...")
                time.sleep(1)
                # Try one more time
                if not self.ensure_email_content_page():
                    logger.error("Failed to navigate to email content page")
                    return {'case_id': email_data['case_id'], 'subject': '', 'from': '', 'body': '', 'attachments': []}
            
            # Always try to extract the real case ID from multiple sources
            # PRIORITY: h2 header is the AUTHORITATIVE source for case ID
            real_case_id = None
            
            # Method 1 (HIGHEST PRIORITY): Extract from h2 header "Fall #XXXXXXXX"
            try:
                case_header = self.page.locator('h2:has-text("Fall #")').first
                if case_header.is_visible(timeout=2000):
                    header_text = case_header.inner_text()
                    fall_match = re.search(r'Fall\s*#(\d+)', header_text)
                    if fall_match:
                        real_case_id = f"#{fall_match.group(1)}"
                        logger.info(f"Case ID from h2 header (authoritative): {real_case_id}")
            except:
                pass
            
            # Method 2: Try h1 or other header elements
            if not real_case_id:
                try:
                    case_header = self.page.locator('h1:has-text("Fall #"), [data-testid*="case"]:has-text("Fall #")').first
                    if case_header.is_visible(timeout=1200):
                        header_text = case_header.inner_text()
                        fall_match = re.search(r'Fall\s*#(\d+)', header_text)
                        if fall_match:
                            real_case_id = f"#{fall_match.group(1)}"
                except:
                    pass
            
            # Method 3: Try to extract from URL
            if not real_case_id:
                current_url = self.page.url
                real_case_id = self.extract_case_id(current_url)
            
            # Method 4: Try to extract from page title
            if not real_case_id:
                try:
                    page_title = self.page.title()
                    real_case_id = self.extract_case_id(page_title)
                except:
                    pass
            
            # Method 5 (LAST RESORT): Extract from page content
            if not real_case_id:
                page_content = self.page.content()
                fall_match = re.search(r'Fall\s*#(\d+)', page_content)
                if fall_match:
                    real_case_id = f"#{fall_match.group(1)}"
                else:
                    real_case_id = self.extract_case_id(page_content)
            
            # Method 6: ConversationId fallback
            if not real_case_id:
                try:
                    if not page_content:
                        page_content = self.page.content()
                    conv_id_match = re.search(r'%%\[ConversationId:\s*([a-f0-9]+)\]%%', page_content, re.IGNORECASE)
                    if conv_id_match:
                        conv_id = conv_id_match.group(1)
                        real_case_id = f"#CONV{conv_id[:8].upper()}"
                        logger.info(f"Using ConversationId as case identifier: {real_case_id}")
                except:
                    pass
            
            # Update case ID if we found a real one
            if real_case_id:
                if email_data.get('is_temp_id', False):
                    logger.info(f"Found real case ID: {real_case_id} (was {email_data['case_id']})")
                else:
                    logger.info(f"Extracted case ID: {real_case_id}")
                email_data['case_id'] = real_case_id
            
            time.sleep(0.5)
            
            # Extract email content from the content page
            email_content = {
                'case_id': email_data['case_id'],
                'subject': '',
                'from': '',
                'body': '',
                'attachments': []
            }
            
            # Try to extract case ID from the page header one more time (Fall #30091006 format)
            if email_content['case_id'].startswith('#TEMP') or email_content['case_id'].startswith('#CONV'):
                try:
                    case_header = self.page.locator('h2:has-text("Fall #"), h1:has-text("Fall #"), [data-testid*="case"]:has-text("#")').first
                    if case_header.is_visible(timeout=1200):
                        header_text = case_header.inner_text()
                        extracted_case_id = self.extract_case_id(header_text)
                        if extracted_case_id:
                            email_content['case_id'] = extracted_case_id
                            logger.info(f"Updated case ID from header: {extracted_case_id}")
                except:
                    pass
            
            # Extract subject/from/body from the NEWEST inbound message (last in DOM = most recent)
            subject_extracted = False
            try:
                inbound_message = self.page.locator('[data-testid="inboundChatConversationItemFanMessage"]').last
                inbound_message.wait_for(state='attached', timeout=1500)
                subject_label = inbound_message.locator('span[data-testid="label"]:has-text("Betreff:")').first
                if subject_label.count():
                    parent = subject_label.locator('..')
                    subject_spans = parent.locator('span[data-spaceweb="typography-bs2"]').all()
                    if len(subject_spans) >= 2:
                        subject_text = subject_spans[1]
                        email_content['subject'] = subject_text.inner_text().strip()
                        subject_extracted = True
                        logger.info(f"Extracted subject from inbound: {email_content['subject']}")
                        print(f"[EXTRACTION] Subject: {email_content['subject']}")
            except Exception as e:
                logger.debug(f"Subject extraction from inbound failed: {e}")
            
            # Fallback: try general selectors
            if not subject_extracted:
                subject_selectors = [
                    'span[data-testid="label"]:has-text("Betreff:")',
                    'span:has-text("Betreff:")',
                ]
                for selector in subject_selectors:
                    try:
                        label_elem = self.page.locator(selector).first
                        if label_elem.is_visible(timeout=1200):
                            parent = label_elem.locator('..')
                            subject_spans = parent.locator('span[data-spaceweb="typography-bs2"]').all()
                            if len(subject_spans) >= 2:
                                subject_text = subject_spans[1]
                                if subject_text.is_visible(timeout=400):
                                    email_content['subject'] = subject_text.inner_text().strip()
                                    subject_extracted = True
                                    logger.info(f"Extracted subject: {email_content['subject']}")
                                    print(f"[EXTRACTION] Subject: {email_content['subject']}")
                                    break
                    except:
                        continue
            
            # Extract from/sender - use NEWEST inbound message (same as subject/body)
            from_extracted = False
            try:
                inbound_message = self.page.locator('[data-testid="inboundChatConversationItemFanMessage"]').last
                if inbound_message.count():
                    from_label = inbound_message.locator('span[data-testid="label"]:has-text("Von:")').first
                    if from_label.count():
                        parent = from_label.locator('..')
                        email_elem = parent.locator('span[data-spaceweb="typography-l2"]').first
                        if email_elem.count():
                            email_content['from'] = email_elem.inner_text().strip()
                            from_extracted = True
                            logger.info(f"Extracted from inbound: {email_content['from']}")
                            print(f"[EXTRACTION] From: {email_content['from']}")
            except Exception as e:
                logger.debug(f"From extraction from inbound failed: {e}")
            
            # Fallback: try general selectors
            if not from_extracted:
                from_selectors = [
                    'span[data-testid="label"]:has-text("Von:")',
                    'span:has-text("Von:")',
                ]
                for selector in from_selectors:
                    try:
                        label_elem = self.page.locator(selector).first
                        if label_elem.is_visible(timeout=1200):
                            parent = label_elem.locator('..')
                            email_elem = parent.locator('span[data-spaceweb="typography-l2"]').first
                            if email_elem.is_visible(timeout=400):
                                email_content['from'] = email_elem.inner_text().strip()
                                from_extracted = True
                                logger.info(f"Extracted from: {email_content['from']}")
                                print(f"[EXTRACTION] From: {email_content['from']}")
                                break
                    except:
                        continue
            
            # Extract email body - use NEWEST inbound message (last in DOM)
            body_extracted = False
            try:
                inbound_message = self.page.locator('[data-testid="inboundChatConversationItemFanMessage"]').last
                if inbound_message.count():
                    body_elem = inbound_message.locator('[data-testid="html-message-content"]').first
                    if body_elem.count():
                        email_content['body'] = body_elem.inner_text()
                        try:
                            email_content['body_html'] = body_elem.inner_html()
                        except Exception:
                            pass
                        body_extracted = True
                        logger.info("Extracted body from newest inbound message")
                        print(f"[EXTRACTION] Body extracted from newest inbound - length: {len(email_content['body'])} characters")
            except Exception as e:
                logger.debug(f"Could not extract from inbound message: {e}")
            
            # Fallback: get first html-message-content element
            if not body_extracted:
                body_selectors = [
                    '[data-testid="html-message-content"]',
                    'div[data-testid="html-message-content"] > div',
                ]
                
                for selector in body_selectors:
                    try:
                        body_elem = self.page.locator(selector).first
                        if body_elem.is_visible(timeout=1200):
                            email_content['body'] = body_elem.inner_text()
                            try:
                                email_content['body_html'] = body_elem.inner_html()
                            except:
                                pass
                            body_extracted = True
                            logger.info(f"Extracted body using selector: {selector}")
                            print(f"[EXTRACTION] Body length: {len(email_content['body'])} characters")
                            break
                    except Exception as e:
                        logger.debug(f"Body extraction failed with {selector}: {e}")
                        continue
            
            # If body not found, try to get from the inner div
            if not body_extracted:
                try:
                    # Try the inner div that contains the actual text
                    inner_div = self.page.locator('[data-testid="html-message-content"] > div > div').first
                    if inner_div.is_visible(timeout=700):
                        email_content['body'] = inner_div.inner_text()
                        try:
                            email_content['body_html'] = inner_div.inner_html()
                        except:
                            pass
                        body_extracted = True
                        logger.info("Extracted body from inner div")
                        print(f"[EXTRACTION] Body length: {len(email_content['body'])} characters")
                except:
                    pass
            
            # Last resort: get all text from the email message container
            if not body_extracted:
                try:
                    message_container = self.page.locator('[data-element-type="email-message-container"]').first
                    if message_container.is_visible(timeout=700):
                        email_content['body'] = message_container.inner_text()
                        try:
                            email_content['body_html'] = message_container.inner_html()
                        except:
                            pass
                        body_extracted = True
                        logger.info("Extracted body from message container")
                        print(f"[EXTRACTION] Body length: {len(email_content['body'])} characters")
                except:
                    pass
            
            if not body_extracted:
                logger.warning("Could not extract email body")
                print("[EXTRACTION] WARNING: Could not extract email body")
            
            # Extract attachments info - look for "Anhang" text
            try:
                attachment_elem = self.page.locator('p[data-spaceweb="typography-bs2"]:has-text("Anhang")').first
                if attachment_elem.is_visible(timeout=700):
                    attachment_text = attachment_elem.inner_text()
                    email_content['attachments'] = [attachment_text]
                    # Try to find attachment file names
                    try:
                        attachment_sections = self.page.locator('section[data-index]').all()
                        for section in attachment_sections:
                            # Extract file name if available
                            file_name = section.get_attribute('title') or section.inner_text()
                            if file_name and file_name not in email_content['attachments']:
                                email_content['attachments'].append(file_name)
                    except:
                        pass
            except:
                pass
            
            logger.info(f"Extracted content for case {email_content['case_id']}")
            
            # Extract FULL conversation thread from the main container
            print("\n" + "="*80)
            print("="*80)
            print(f"EXTRACTING FULL CONVERSATION THREAD - Case ID: {email_content['case_id']}")
            print("="*80)
            print("="*80)
            
            # Find the main conversation container
            conversation_messages = []
            try:
                # Find all message items in the conversation (both inbound and outbound)
                inbound_messages = self.page.locator('[data-testid="inboundChatConversationItemFanMessage"]').all()
                outbound_messages = self.page.locator('[data-testid="inboundChatConversationItemBrandMessage"]').all()
                
                logger.info(f"Found {len(inbound_messages)} inbound message(s) and {len(outbound_messages)} outbound message(s)")
                print(f"\n[CONVERSATION] Found {len(inbound_messages)} inbound message(s) and {len(outbound_messages)} outbound message(s)")
                
                # Extract all inbound messages (customer emails)
                for i, msg in enumerate(inbound_messages, 1):
                    try:
                        if msg.is_visible(timeout=1200):
                            msg_data = {}
                            
                            # Extract subject
                            try:
                                subject_label = msg.locator('span[data-testid="label"]:has-text("Betreff:")').first
                                if subject_label.is_visible(timeout=400):
                                    parent = subject_label.locator('..')
                                    subject_spans = parent.locator('span[data-spaceweb="typography-bs2"]').all()
                                    if len(subject_spans) >= 2:
                                        msg_data['subject'] = subject_spans[1].inner_text().strip()
                            except:
                                pass
                            
                            # Extract from
                            try:
                                from_label = msg.locator('span[data-testid="label"]:has-text("Von:")').first
                                if from_label.is_visible(timeout=400):
                                    parent = from_label.locator('..')
                                    email_elem = parent.locator('span[data-spaceweb="typography-l2"]').first
                                    if email_elem.is_visible(timeout=400):
                                        msg_data['from'] = email_elem.inner_text().strip()
                            except:
                                pass
                            
                            # Extract timestamp
                            try:
                                timestamp_elem = msg.locator('span[data-spaceweb="typography-l2"]').last
                                if timestamp_elem.is_visible(timeout=400):
                                    msg_data['timestamp'] = timestamp_elem.inner_text().strip()
                            except:
                                pass
                            
                            # Extract body
                            try:
                                body_elem = msg.locator('[data-testid="html-message-content"]').first
                                if body_elem.is_visible(timeout=700):
                                    msg_data['body'] = body_elem.inner_text()
                                    msg_data['body_html'] = body_elem.inner_html()
                            except:
                                pass
                            
                            msg_data['type'] = 'INBOUND'
                            msg_data['index'] = i
                            conversation_messages.append(msg_data)
                    except Exception as e:
                        logger.debug(f"Error extracting inbound message {i}: {e}")
                        continue
                
                # Extract all outbound messages (brand/agent responses)
                for i, msg in enumerate(outbound_messages, 1):
                    try:
                        if msg.is_visible(timeout=1200):
                            msg_data = {}
                            
                            # Extract subject
                            try:
                                subject_label = msg.locator('span[data-testid="label"]:has-text("Betreff:")').first
                                if subject_label.is_visible(timeout=400):
                                    parent = subject_label.locator('..')
                                    subject_spans = parent.locator('span[data-spaceweb="typography-bs2"]').all()
                                    if len(subject_spans) >= 2:
                                        msg_data['subject'] = subject_spans[1].inner_text().strip()
                            except:
                                pass
                            
                            # Extract to
                            try:
                                to_label = msg.locator('span[data-testid="label"]:has-text("An:")').first
                                if to_label.is_visible(timeout=400):
                                    parent = to_label.locator('..')
                                    email_elem = parent.locator('span[data-spaceweb="typography-l2"]').first
                                    if email_elem.is_visible(timeout=400):
                                        msg_data['to'] = email_elem.inner_text().strip()
                            except:
                                pass
                            
                            # Extract timestamp
                            try:
                                timestamp_elem = msg.locator('span[data-spaceweb="typography-l2"]').last
                                if timestamp_elem.is_visible(timeout=400):
                                    msg_data['timestamp'] = timestamp_elem.inner_text().strip()
                            except:
                                pass
                            
                            # Extract body
                            try:
                                body_elem = msg.locator('[data-testid="html-message-content"]').first
                                if body_elem.is_visible(timeout=700):
                                    msg_data['body'] = body_elem.inner_text()
                                    msg_data['body_html'] = body_elem.inner_html()
                            except:
                                pass
                            
                            msg_data['type'] = 'OUTBOUND'
                            msg_data['index'] = i
                            conversation_messages.append(msg_data)
                    except Exception as e:
                        logger.debug(f"Error extracting outbound message {i}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error extracting conversation thread: {e}")
                print(f"[ERROR] Could not extract conversation thread: {e}")
            
            # Print the full conversation thread
            print("\n" + "="*80)
            print("="*80)
            print(f"COMPLETE CONVERSATION THREAD - Case ID: {email_content['case_id']}")
            print("="*80)
            print("="*80)
            
            if conversation_messages:
                print(f"\nTotal messages in thread: {len(conversation_messages)}\n")
                
                # Print messages in reverse order (oldest first, newest last)
                for msg_idx, msg in enumerate(reversed(conversation_messages), 1):
                    msg_type = msg.get('type', 'UNKNOWN')
                    print("\n" + "-"*80)
                    print(f"MESSAGE {msg_idx} - {msg_type}")
                    print("-"*80)
                    
                    if msg.get('subject'):
                        print(f"SUBJECT: {msg['subject']}")
                    
                    if msg.get('from'):
                        print(f"FROM: {msg['from']}")
                    
                    if msg.get('to'):
                        print(f"TO: {msg['to']}")
                    
                    if msg.get('timestamp'):
                        print(f"TIMESTAMP: {msg['timestamp']}")
                    
                    if msg.get('body'):
                        print(f"\nBODY:")
                        print("-" * 80)
                        try:
                            print(msg['body'])
                        except UnicodeEncodeError:
                            enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
                            print(msg['body'].encode(enc, errors='replace').decode(enc))
                        print("-" * 80)
                    else:
                        print("\nBODY: (No body text extracted)")
                    
                    print()
            else:
                print("\n[WARNING] No messages found in conversation thread")
                # Fallback to single message extraction
                print(f"\nSUBJECT: {email_content.get('subject', 'N/A')}")
                print(f"FROM: {email_content.get('from', 'N/A')}")
                print(f"\nBODY:")
                print("-" * 80)
                body_full = email_content.get('body', 'N/A')
                if body_full and body_full != 'N/A':
                    try:
                        print(body_full)
                    except UnicodeEncodeError:
                        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
                        print(body_full.encode(enc, errors='replace').decode(enc))
                else:
                    print("   (No body text extracted)")
                print("-" * 80)
            
            print("\n" + "="*80)
            print("="*80)
            print(f"END OF CONVERSATION THREAD - Case ID: {email_content['case_id']}")
            print("="*80)
            print("="*80 + "\n")
            
            # Store conversation messages in email_content for potential use
            email_content['conversation_thread'] = conversation_messages
            
            return email_content
            
        except Exception as e:
            logger.error(f"Error extracting email content: {e}")
            return email_content
    
    def query_cursor_ai(self, email_content: Dict) -> Dict:
        """
        Query Cursor AI with the email content using the prompt from prompt.md
        
        Args:
            email_content: Dictionary containing email information including conversation thread
            
        Returns:
            Dictionary containing parsed response with transfer info, instructions, and customer response
        """
        logger.info(f"Querying Cursor AI for case {email_content['case_id']}")
        
        # Load prompt template from prompt.md
        prompt_file = Path('KnowledgeBase/prompt.md')
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        else:
            logger.warning("prompt.md not found, using default prompt")
            prompt_template = """You are an AI advisor for Telefonica O2 customer support. 
Analyze the following email case and provide detailed handling instructions.

Case ID: {case_id}
Subject: {subject}
From: {from_email}

Full Conversation Thread:
{conversation_thread}

Please provide:
1. Transfer eligibility assessment
2. Detailed handling instructions
3. Customer email response in German"""
        
        # Build conversation thread text
        conversation_text = ""
        if email_content.get('conversation_thread'):
            for msg in reversed(email_content['conversation_thread']):
                msg_type = msg.get('type', 'UNKNOWN')
                conversation_text += f"\n\n--- {msg_type} MESSAGE ---\n"
                if msg.get('subject'):
                    conversation_text += f"Subject: {msg['subject']}\n"
                if msg.get('from'):
                    conversation_text += f"From: {msg['from']}\n"
                if msg.get('to'):
                    conversation_text += f"To: {msg['to']}\n"
                if msg.get('timestamp'):
                    conversation_text += f"Timestamp: {msg['timestamp']}\n"
                if msg.get('body'):
                    conversation_text += f"\nBody:\n{msg['body']}\n"
        else:
            # Fallback to single message
            conversation_text = f"""
Subject: {email_content.get('subject', 'N/A')}
From: {email_content.get('from', 'N/A')}
Body:
{email_content.get('body', 'N/A')}
"""
        
        # Reference knowledge base files instead of loading full content
        # cursor-agent can access the files directly from KnowledgeBase/ directory
        knowledge_base_reference = self._get_knowledge_base_reference()
        
        # Build the full prompt with clear instructions
        # ANNOTATE WITH FALL # AT THE BEGINNING
        case_id = email_content.get('case_id', 'N/A')
        formatted_case_id = case_id
        if case_id and case_id.startswith('#'):
            # Format as "Fall #XXXXXXXX" (8 digits)
            numeric_part = re.sub(r'\D', '', case_id)
            if numeric_part:
                if len(numeric_part) < 8:
                    numeric_part = numeric_part.zfill(8)
                elif len(numeric_part) > 8:
                    numeric_part = numeric_part[:8]
                formatted_case_id = f"Fall #{numeric_part}"
        
        full_prompt = f"""================================================================================
FALL # ANNOTATION: {formatted_case_id}
================================================================================
This is the case identifier visible in the top left of the browser window.
All analysis and responses below are for this specific case.

{prompt_template}

{knowledge_base_reference}

================================================================================
CASE INFORMATION:
================================================================================
Case ID: {case_id}
Subject: {email_content.get('subject', 'N/A')}
From: {email_content.get('from', 'N/A')}
Attachments: {', '.join(email_content.get('attachments', [])) or 'None'}

================================================================================
FULL CONVERSATION THREAD:
================================================================================
{conversation_text}

================================================================================
INSTRUCTIONS:
================================================================================
CRITICAL: YOU MUST READ THE KNOWLEDGE BASE FILES BEFORE GENERATING YOUR RESPONSE!

STEP 1 - READ KNOWLEDGE BASE FILES FIRST:
1. MANDATORY: Read KnowledgeBase/TransferMatrix_KnowledgeBase.md to determine transfer eligibility
2. MANDATORY: Read KnowledgeBase/KnowledgeBase_Complete.md for specific procedures and Ticket IDs related to this case
3. Search the knowledge base for information relevant to the customer's specific inquiry (subject, issue type, etc.)

STEP 2 - ANALYZE THE CASE:
- Analyze the customer's email content carefully
- Identify the specific issue(s) mentioned in the email
- Determine what type of inquiry this is (billing, contract, technical, etc.)
- Note any specific details mentioned (amounts, dates, phone numbers, etc.)
- Create a concise summary of the entire communication thread for quick understanding

STEP 3 - GENERATE RESPONSE:
Provide your response in the EXACT format specified in the prompt template above with these sections:
   - COMMUNICATION THREAD SUMMARY (concise, time-efficient summary of all customer communications)
   - TRANSFER ELIGIBILITY ASSESSMENT (based on TransferMatrix_KnowledgeBase.md)
   - DETAILED HANDLING INSTRUCTIONS FOR AGENT (based on KnowledgeBase_Complete.md)
   - CUSTOMER EMAIL RESPONSE (ONLY IF Transfer Eligible = NO, otherwise leave empty or write "NOT APPLICABLE - Case is transferable")

COMMUNICATION THREAD SUMMARY REQUIREMENTS:
- Provide a concise, time-efficient summary of the entire communication thread
- Focus on key points: what the customer asked, when, and what has been discussed
- Use bullet points for clarity
- Keep it brief but comprehensive enough to bring the agent up to speed quickly
- Include: customer's main concern, any previous responses, current status

CRITICAL RULE FOR CUSTOMER EMAIL RESPONSE:
- IF Transfer Eligible = YES: DO NOT generate any customer email response. Write "NOT APPLICABLE - Case is transferable, no customer email will be sent" or leave the section empty.
- IF Transfer Eligible = NO: Generate the customer email response in German following the template below.

CRITICAL: The customer email response MUST be specific to the customer's inquiry. DO NOT use generic placeholder text. Address their specific issue, mention their specific concern, and provide relevant information based on what they asked about.

ABSOLUTELY FORBIDDEN PLACEHOLDER TEXT - DO NOT USE THESE UNDER ANY CIRCUMSTANCES:
- "Sehr geehrte Damen und Herren" (WRONG - use "Guten Tag" instead)
- "vielen Dank für Ihre Nachricht bezüglich Fall #[CASE_ID]" (WRONG - NEVER mention case ID in thank you)
- "vielen Dank für Ihre Nachricht bezüglich Fall #212123" (WRONG - this exact phrase is FORBIDDEN)
- "vielen Dank für Ihre Nachricht bezüglich Fall" (WRONG - any mention of "Fall #" is FORBIDDEN)
- "Wir werden Ihre Anfrage bearbeiten" (WRONG - be specific about what you will do, this is placeholder text)
- "Mit freundlichen Grüßen\nIhr Team" (WRONG - use the standard closing template below)

IF YOU USE ANY OF THESE FORBIDDEN PHRASES, YOUR ENTIRE RESPONSE WILL BE REJECTED AND YOU MUST REGENERATE IT.
YOU MUST generate a case-specific response that addresses the customer's actual inquiry - NEVER use placeholder text.

IMPORTANT FOR CUSTOMER EMAIL RESPONSE - USE THIS EXACT TEMPLATE:

Salutation:
- We always mirror what the contact uses as their signature.
- Ideally, "Guten Tag [First Name Last Name]," (NO "Herr" or "Frau").
- IF NO NAME IS KNOWN, OR ONLY THE LAST NAME IS GIVEN WITHOUT THE (abbreviated) FIRST NAME, WE REPLY WITH "Guten Tag," (without name).

Body Structure:
1. Followed by a case-specific thank you to the customer in the form: "vielen Dank für Ihre E-Mail bezüglich [customer case explanation/summary/parroting back to them]". 
   - ABSOLUTELY FORBIDDEN: "vielen Dank für Ihre Nachricht bezüglich Fall #[CASE_ID]" or "vielen Dank für Ihre Nachricht bezüglich Fall #212123"
   - ABSOLUTELY FORBIDDEN: Any mention of "Fall #" or case ID in the thank you line
   - DO NOT mention the case ID or case number anywhere in the email
   - Instead, summarize or paraphrase their specific inquiry/issue
   - Examples (CORRECT): 
     * "vielen Dank für Ihre E-Mail bezüglich Ihrer Anfrage zur Namensänderung"
     * "vielen Dank für Ihre E-Mail bezüglich Ihrer Rechnungsreklamation"
     * "vielen Dank für Ihre E-Mail bezüglich Ihrer Anfrage zu den Vertragsverlängerungen und der Vertragsübernahme"
     * "vielen Dank für Ihre E-Mail bezüglich Ihrer Anfrage zur Zahlungsaufschub"

2. Apologise and show specific sympathy for the customer's case and circumstance. Reference their specific situation (e.g., if they mention a problem with a contract extension, acknowledge that specific problem).

3. Address the customer's concern directly and provide clear information or next steps. This MUST be specific to what they asked about. If they asked about a billing issue, address the billing issue. If they asked about missing documents, address the missing documents. DO NOT use generic text like "wir werden Ihre Anfrage bearbeiten" - be specific about what you will do or what information you are providing.

Standard Closing (MUST BE INCLUDED EXACTLY AS SHOWN WITH PROPER SPACING):
Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer

Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz

FORMATTING REQUIREMENTS:
- Use single blank lines between paragraphs (one empty line between each paragraph)
- Use single blank line before the survey text/closing section
- Use single blank line between "Freundliche Grüße," and "Ihr o2 Kundenbetreuer"
- Use single blank line between "Ihr o2 Kundenbetreuer" and "Lukasz Kowalski"
- Use single blank line between "Lukasz Kowalski" and company address
- Use single blank line between each line of the legal disclaimers
- Write ONLY the email body in German
- Do NOT include any instructions, explanations, or English text
- The response should be formatted as plain text with proper line breaks
- The entire response should be ready to copy-paste directly into an email editor

MANDATORY: You MUST read the knowledge base files from the KnowledgeBase/ directory BEFORE generating your response. Do not generate a generic placeholder response. The response must be specific to the customer's inquiry based on the knowledge base information.

To read the files, use the file system access available to cursor-agent. The files are located at:
- KnowledgeBase/TransferMatrix_KnowledgeBase.md
- KnowledgeBase/KnowledgeBase_Complete.md

Read these files first, then generate a case-specific response based on the customer's actual inquiry.

FINAL VALIDATION CHECKLIST - Your response MUST:
✅ IF Transfer Eligible = YES: Customer Email Response section must be EMPTY or say "NOT APPLICABLE - Case is transferable"
✅ IF Transfer Eligible = NO: Customer Email Response must:
   ✅ Start with "Guten Tag" (NOT "Sehr geehrte Damen und Herren")
   ✅ Thank customer by summarizing their specific inquiry (NOT mentioning case ID)
   ✅ NEVER use "vielen Dank für Ihre Nachricht bezüglich Fall #" - this is ABSOLUTELY FORBIDDEN
   ✅ Address their specific concern with concrete information
   ✅ Include the complete standard closing template
   ✅ NOT contain "wir werden Ihre Anfrage bearbeiten" or similar generic text
   ✅ NOT mention "Fall #" or case ID anywhere in the entire email
   ✅ Be specific to what the customer actually asked about

ABSOLUTE RULES - VIOLATION WILL CAUSE REJECTION:
❌ NEVER generate customer email for transferable cases (Transfer Eligible = YES)
❌ NEVER use "vielen Dank für Ihre Nachricht bezüglich Fall #[CASE_ID]" - this exact phrase is FORBIDDEN
❌ NEVER use placeholder text like "wir werden Ihre Anfrage bearbeiten"
❌ NEVER mention case ID anywhere in customer-facing email

If your response fails any of these checks, it will be REJECTED and you must regenerate it."""
        
        # Print the prompt for testing
        print("\n" + "="*80)
        print("PROMPT SENT TO CURSOR AI:")
        print("="*80)
        print(full_prompt[:2000] + "..." if len(full_prompt) > 2000 else full_prompt)
        print("="*80 + "\n")
        
        # Try to query Cursor programmatically
        # ONLY USE CURSOR-AGENT CLI (WSL) - NO API FALLBACKS
        response_text = None
        try:
            # ONLY METHOD: Cursor CLI (cursor-agent) via WSL
            if self.cursor_cli_path:
                logger.info("Attempting to use Cursor CLI (cursor-agent) via WSL...")
                response_text = self._query_cursor_via_subprocess(full_prompt)
                if response_text:
                    logger.info("Successfully used Cursor CLI")
                else:
                    logger.error("Cursor CLI (cursor-agent) returned no response")
            else:
                logger.error("Cursor CLI path not found. Cannot proceed without cursor-agent.")
                
        except Exception as e:
            logger.error(f"Error querying Cursor: {e}")
            import traceback
            logger.error(traceback.format_exc())
            response_text = None
        
        if not response_text:
            logger.error("="*80)
            logger.error("CRITICAL: Could not query cursor-agent CLI!")
            logger.error("="*80)
            logger.error("The script ONLY uses cursor-agent CLI in WSL. No API fallbacks.")
            logger.error("Please ensure cursor-agent is properly configured and working.")
            logger.error("")
            logger.error("Troubleshooting steps:")
            logger.error("1. Verify cursor-agent is installed in WSL: wsl bash -c '~/.local/bin/cursor-agent --version'")
            logger.error("2. Verify API key is set in config.json")
            logger.error("3. Test cursor-agent manually: wsl bash -c 'export CURSOR_API_KEY=... && echo \"test\" | ~/.local/bin/cursor-agent -p'")
            logger.error("4. Check email_automation.log for detailed error messages")
            logger.error("="*80)
            logger.error("ABORTING: Cannot proceed without cursor-agent. Please fix the setup.")
            raise Exception("cursor-agent CLI failed - cannot generate case-specific response. Please fix cursor-agent setup.")
        
        # Check if response looks like a placeholder
        if response_text and len(response_text.strip()) < 100:
            logger.warning(f"Response seems too short ({len(response_text)} chars), may be incomplete")
        
        # Check for placeholder text in response (generic text that should not appear)
        placeholder_indicators = [
            "wir werden Ihre Anfrage bearbeiten",
            "Wir werden Ihre Anfrage bearbeiten",
            "mit freundlichen Grüßen\nIhr Team",
            "Mit freundlichen Grüßen\nIhr Team"
        ]
        if any(indicator in response_text.lower() for indicator in [p.lower() for p in placeholder_indicators]):
            if "vielen Dank für Ihre Nachricht bezüglich Fall" in response_text and "Wir werden Ihre Anfrage bearbeiten" in response_text:
                logger.error("CRITICAL: Response contains placeholder-like text!")
                logger.error("This indicates cursor-agent did not generate a case-specific response.")
                logger.error("Please verify cursor-agent can access KnowledgeBase/ directory and read the files.")
                logger.error("This response should NOT be used - it violates the no-placeholder policy.")
        
        # Check for case ID mentions in response (should not be in customer email)
        case_id_pattern = r'\b(Fall|Case|Fallnummer|Case-ID)[\s:]*#?\d+'
        if re.search(case_id_pattern, response_text, re.IGNORECASE):
            logger.warning("Response contains case ID mention - this should be removed from customer email")
            logger.warning("Case IDs should NOT appear in customer-facing emails")
        
        # Parse the response
        parsed_response = self._parse_cursor_response(response_text, email_content)
        
        # Store email content in parsed response for potential fallback thread summary generation
        parsed_response['_email_content_for_summary'] = email_content
        
        print("\n" + "="*80)
        print("CURSOR AI RESPONSE:")
        print("="*80)
        print(response_text[:2000] + "..." if len(response_text) > 2000 else response_text)
        print("="*80 + "\n")
        
        return parsed_response
    
    def _query_cursor_api_local(self, prompt: str) -> Optional[str]:
        """Try to query Cursor IDE via local API (if Cursor IDE is running)"""
        try:
            # Cursor IDE might expose a local API when running
            # Try common endpoints that Cursor might use
            api_key = self.cursor_api_key or self.config.get('cursor_api_key', '')
            
            endpoints = [
                'http://localhost:3000/api/chat',
                'http://127.0.0.1:3000/api/chat',
                'http://localhost:8080/api/chat',
                'http://127.0.0.1:8080/api/chat',
            ]
            
            for endpoint in endpoints:
                try:
                    headers = {'Content-Type': 'application/json'}
                    if api_key:
                        headers['Authorization'] = f'Bearer {api_key}'
                    
                    response = requests.post(
                        endpoint,
                        json={
                            'messages': [
                                {'role': 'user', 'content': prompt}
                            ],
                            'model': 'gpt-4',
                        },
                        headers=headers,
                        timeout=10  # Short timeout for local API check
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        if content:
                            logger.info(f"Successfully queried Cursor IDE local API at {endpoint}")
                            return content
                except requests.exceptions.RequestException:
                    continue
                except Exception as e:
                    logger.debug(f"Local API endpoint {endpoint} failed: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Local API query failed: {e}")
        
        return None
    
    def _query_openai_api(self, prompt: str) -> Optional[str]:
        """Try to query OpenAI API (Cursor uses OpenAI models)"""
        try:
            # Try to import OpenAI
            try:
                from openai import OpenAI
            except ImportError:
                logger.warning("OpenAI library not installed. Install with: pip install openai")
                return None
            
            # Get API key from config or environment
            # Note: cursor_api_key might not work with OpenAI API directly
            api_key = self.openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable or add 'openai_api_key' to config.json")
                logger.info("Note: cursor_api_key cannot be used with OpenAI API - you need a separate OpenAI API key")
                return None
            
            logger.info(f"Using OpenAI API with key: {api_key[:10]}...")
            client = OpenAI(api_key=api_key)
            
            # Read knowledge base files for context
            logger.info("Loading knowledge base context...")
            knowledge_base_context = self._load_knowledge_base_context()
            cursor_rules = self._load_cursor_rules()
            
            logger.info(f"Knowledge base loaded: {len(knowledge_base_context)} chars, Cursor rules: {len(cursor_rules) if cursor_rules else 0} chars")
            
            # Build messages with system prompt and user prompt
            messages = []
            system_content = 'You are an AI advisor for Telefonica O2 customer support. You must analyze customer emails and provide detailed handling instructions based on the knowledge base provided.'
            
            # Add Cursor rules if available
            if cursor_rules:
                system_content += f'\n\nCURSOR WORKSPACE RULES:\n{cursor_rules[:2000]}'
            
            # Add knowledge base context - use more context for better results
            if knowledge_base_context:
                # Use more context - up to 15000 chars for better analysis
                kb_preview = knowledge_base_context[:15000] if len(knowledge_base_context) > 15000 else knowledge_base_context
                system_content += f'\n\nKNOWLEDGE BASE CONTEXT:\n{kb_preview}'
                logger.info(f"Using {len(kb_preview)} chars of knowledge base context")
            
            messages.append({
                'role': 'system',
                'content': system_content
            })
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Call OpenAI API
            logger.info("Calling OpenAI API (this may take a moment)...")
            response = client.chat.completions.create(
                model='gpt-4',
                messages=messages,
                temperature=0.7,
                max_tokens=4000  # Increased for longer responses
            )
            
            if response.choices and len(response.choices) > 0:
                output = response.choices[0].message.content
                # Fix any encoding issues
                if output:
                    output = self._fix_encoding(output)
                    logger.info(f"OpenAI API returned response ({len(output)} chars)")
                return output
            else:
                logger.warning("OpenAI API returned no choices")
                return None
            
        except Exception as e:
            logger.debug(f"OpenAI API query failed: {e}")
        
        return None
    
    def _load_knowledge_base_context(self) -> str:
        """Load knowledge base files for context (full content)"""
        context_parts = []
        knowledge_base_dir = Path('KnowledgeBase')
        
        if knowledge_base_dir.exists():
            # Load TransferMatrix_KnowledgeBase.md (important for transfer decisions)
            transfer_matrix_file = knowledge_base_dir / 'TransferMatrix_KnowledgeBase.md'
            if transfer_matrix_file.exists():
                try:
                    with open(transfer_matrix_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_parts.append(f"=== TRANSFER MATRIX KNOWLEDGE BASE ===\n{content}\n=== END TRANSFER MATRIX ===\n")
                        logger.info(f"Loaded TransferMatrix_KnowledgeBase.md ({len(content)} chars)")
                except Exception as e:
                    logger.warning(f"Could not load TransferMatrix_KnowledgeBase.md: {e}")
            
            # Load KnowledgeBase_Complete.md (main knowledge base)
            complete_kb_file = knowledge_base_dir / 'KnowledgeBase_Complete.md'
            if complete_kb_file.exists():
                try:
                    with open(complete_kb_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_parts.append(f"=== COMPLETE KNOWLEDGE BASE ===\n{content}\n=== END COMPLETE KNOWLEDGE BASE ===\n")
                        logger.info(f"Loaded KnowledgeBase_Complete.md ({len(content)} chars)")
                except Exception as e:
                    logger.warning(f"Could not load KnowledgeBase_Complete.md: {e}")
        
        result = '\n\n'.join(context_parts)
        if result:
            logger.info(f"Total knowledge base context loaded: {len(result)} characters")
        return result
    
    def _get_knowledge_base_reference(self) -> str:
        """Get knowledge base file references for cursor-agent to access directly"""
        knowledge_base_dir = Path('KnowledgeBase')
        references = []
        
        if knowledge_base_dir.exists():
            # Check which files exist and provide references
            transfer_matrix_file = knowledge_base_dir / 'TransferMatrix_KnowledgeBase.md'
            complete_kb_file = knowledge_base_dir / 'KnowledgeBase_Complete.md'
            prompt_file = knowledge_base_dir / 'prompt.md'
            
            file_info = []
            
            if transfer_matrix_file.exists():
                size = transfer_matrix_file.stat().st_size
                file_info.append(f"- KnowledgeBase/TransferMatrix_KnowledgeBase.md ({size:,} bytes) - Use this for transfer routing decisions")
                logger.info(f"Transfer Matrix available: {size:,} bytes")
            
            if complete_kb_file.exists():
                size = complete_kb_file.stat().st_size
                file_info.append(f"- KnowledgeBase/KnowledgeBase_Complete.md ({size:,} bytes) - Use this for detailed procedures, Ticket IDs, and system instructions")
                logger.info(f"Complete KB available: {size:,} bytes")
            
            if prompt_file.exists():
                file_info.append(f"- KnowledgeBase/prompt.md - This is the prompt template you should follow")
            
            if file_info:
                references.append("""MANDATORY - KNOWLEDGE BASE ACCESS - READ THESE FILES FIRST:

The following knowledge base files are available in the KnowledgeBase/ directory. 
YOU MUST READ THESE FILES BEFORE GENERATING YOUR RESPONSE. DO NOT USE PLACEHOLDER OR GENERIC TEXT.

""")
                references.append('\n'.join(file_info))
                references.append("""

CRITICAL INSTRUCTIONS FOR USING KNOWLEDGE BASE:
1. BEFORE generating any response, you MUST read: KnowledgeBase/TransferMatrix_KnowledgeBase.md to determine transfer eligibility
2. BEFORE generating any response, you MUST read relevant sections from: KnowledgeBase/KnowledgeBase_Complete.md for specific procedures, Ticket IDs, and system instructions related to this case
3. Search the knowledge base for information that matches the customer's specific inquiry (check the subject, email body, and conversation thread)
4. Use the information from the knowledge base to generate a SPECIFIC response that addresses the customer's actual issue
5. DO NOT generate generic placeholder text like "wir werden Ihre Anfrage bearbeiten" - use specific information from the knowledge base
6. Always cite which file and section you're referencing in your response

The files are in the same directory where cursor-agent is running, so you can access them directly using file system operations.
Use cursor-agent's file reading capabilities to read these files before generating your response.
""")
        
        result = '\n'.join(references) if references else ""
        if result:
            logger.info("Knowledge base files referenced (cursor-agent will access them directly)")
        return result
    
    def _query_cursor_via_subprocess(self, prompt: str) -> Optional[str]:
        """Query Cursor programmatically using cursor-agent CLI"""
        if not self.cursor_cli_path:
            return None
        
        # Check if we need to use WSL
        use_wsl = str(self.cursor_cli_path).startswith('wsl://')
        is_wrapper = str(self.cursor_cli_path).endswith('.bat') or str(self.cursor_cli_path).endswith('.ps1')
        
        try:
            logger.info(f"Running cursor-agent with prompt (length: {len(prompt)} chars)...")
            
            # Escape prompt for shell (especially for WSL)
            # For long prompts, write to temp file and reference it
            temp_file = Path('temp_cursor_prompt.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            if use_wsl:
                # Use WSL directly with API key - pass prompt via stdin (simplest and most reliable)
                import shlex
                api_key = self.cursor_api_key or self.config.get('cursor_api_key', '')
                
                # Get current working directory in WSL format
                current_dir = Path.cwd()
                wsl_dir = str(current_dir).replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
                
                # Write prompt to temp file in WSL accessible location
                # Use the temp file we already created
                wsl_temp_path = f"{wsl_dir}/temp_cursor_prompt.txt"
                
                # Build the command with proper escaping
                # Use -p flag for non-interactive print mode
                if api_key:
                    api_key_escaped = shlex.quote(api_key)
                    # Use cursor-agent with API key via environment variable and -p for script mode
                    # Change to the project directory first
                    cmd_str = f'cd {shlex.quote(wsl_dir)} && export CURSOR_API_KEY={api_key_escaped} && ~/.local/bin/cursor-agent -p'
                else:
                    # Try without API key (may use default config)
                    cmd_str = f'cd {shlex.quote(wsl_dir)} && ~/.local/bin/cursor-agent -p'
                
                cmd = ['wsl', 'bash', '-c', cmd_str]
                
                # Pass prompt via stdin (this is what worked in our test)
                logger.info(f"Calling cursor-agent via WSL with prompt ({len(prompt)} chars)...")
                logger.info(f"WSL directory: {wsl_dir}")
                logger.info(f"Command: {' '.join(cmd[:2])} ...")
                
                try:
                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',  # Replace encoding errors instead of failing
                        timeout=300,  # Increased timeout for AI processing
                        cwd=Path.cwd(),
                        env=dict(os.environ, **{'PYTHONIOENCODING': 'utf-8'})  # Ensure UTF-8 for subprocess
                    )
                    
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()
                    
                    if result.returncode == 0:
                        output = result.stdout.strip()
                        if output:
                            # Ensure output is properly decoded as UTF-8
                            if isinstance(output, bytes):
                                output = output.decode('utf-8', errors='replace')
                            # Fix any encoding issues (double-encoding)
                            output = self._fix_encoding(output)
                            logger.info(f"Successfully queried Cursor via cursor-agent CLI (WSL) - Response length: {len(output)} chars")
                            logger.debug(f"Response preview (first 500 chars): {output[:500]}")
                            
                            # Check if response looks valid (not just an error message)
                            if len(output) < 50:
                                logger.warning(f"Response seems very short ({len(output)} chars), may be incomplete")
                            elif "error" in output.lower()[:200] or "failed" in output.lower()[:200]:
                                logger.warning("Response may contain error message, checking...")
                                logger.debug(f"Full response: {output}")
                            
                            return output
                        else:
                            logger.warning("cursor-agent returned empty output")
                            if result.stderr:
                                logger.warning(f"cursor-agent stderr: {result.stderr[:1000]}")
                            logger.debug(f"Full stdout: {result.stdout}")
                            logger.debug(f"Full stderr: {result.stderr}")
                    else:
                        logger.error(f"cursor-agent exited with code {result.returncode}")
                        if result.stderr:
                            logger.error(f"cursor-agent error: {result.stderr[:2000]}")
                        if result.stdout:
                            logger.info(f"cursor-agent output: {result.stdout[:1000]}")
                        logger.debug(f"Full command that failed: {' '.join(cmd)}")
                        # Don't return None yet - let it try other methods
                        
                except subprocess.TimeoutExpired:
                    logger.warning("cursor-agent via WSL timed out")
                except Exception as e:
                    logger.error(f"Error calling cursor-agent via WSL: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                # Continue to try other methods if WSL failed
                logger.info("WSL cursor-agent failed, will try other methods...")
            elif is_wrapper:
                # Use wrapper script
                if str(self.cursor_cli_path).endswith('.bat'):
                    cmd = [str(self.cursor_cli_path), '-p', prompt]
                else:  # .ps1
                    cmd = ['powershell.exe', '-File', str(self.cursor_cli_path), '-p', prompt]
            else:
                # Direct cursor-agent call
                cursor_exe = Path(self.cursor_cli_path)
                cmd = [str(cursor_exe), '-p', prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace encoding errors instead of failing
                timeout=180,  # Increased timeout for AI processing
                cwd=Path.cwd(),
                env=dict(os.environ, **{'PYTHONIOENCODING': 'utf-8'})  # Ensure UTF-8 for subprocess
            )
                
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    # Ensure output is properly decoded as UTF-8
                    if isinstance(output, bytes):
                        output = output.decode('utf-8', errors='replace')
                    # Fix any encoding issues (double-encoding)
                    output = self._fix_encoding(output)
                    logger.info("Successfully queried Cursor via cursor-agent CLI")
                    return output
                else:
                    logger.debug("cursor-agent returned empty output")
                    if result.stderr:
                        logger.debug(f"cursor-agent stderr: {result.stderr[:500]}")
            else:
                logger.warning(f"cursor-agent exited with code {result.returncode}")
                if result.stderr:
                    logger.debug(f"cursor-agent error: {result.stderr[:500]}")
                if result.stdout:
                    logger.debug(f"cursor-agent output: {result.stdout[:500]}")
                
        except FileNotFoundError:
            logger.warning(f"Cursor CLI not found at: {self.cursor_cli_path}")
            logger.info("Please install cursor-agent CLI or set cursor_cli_path in config.json")
        except subprocess.TimeoutExpired:
            logger.warning("Cursor CLI query timed out (this may take a while for AI processing)")
        except Exception as e:
            logger.error(f"Error querying Cursor CLI: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return None
    
    def _query_cursor_with_context(self, prompt: str) -> Optional[str]:
        """Query using Cursor's context and knowledge base via OpenAI API"""
        # This method uses OpenAI API but with Cursor's workspace context
        # Load Cursor rules and knowledge base
        cursor_rules = self._load_cursor_rules()
        knowledge_base = self._load_knowledge_base_context()
        
        # Build enhanced prompt with Cursor context
        enhanced_prompt = prompt
        if cursor_rules:
            enhanced_prompt = f"CURSOR WORKSPACE RULES:\n{cursor_rules}\n\n{enhanced_prompt}"
        
        # Use OpenAI API with Cursor's context
        return self._query_openai_api_with_context(enhanced_prompt, knowledge_base)
    
    def _query_openai_api_with_context(self, prompt: str, additional_context: str = "") -> Optional[str]:
        """Query OpenAI API with additional context (used by Cursor integration)"""
        try:
            from openai import OpenAI
            
            api_key = self.openai_api_key or self.cursor_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                return None
            
            client = OpenAI(api_key=api_key)
            
            messages = []
            
            # Add system message with context
            system_content = 'You are an AI advisor for Telefonica O2 customer support using Cursor IDE context.'
            if additional_context:
                # Limit context size to avoid token limits
                context_preview = additional_context[:6000] if len(additional_context) > 6000 else additional_context
                system_content += f'\n\nKNOWLEDGE BASE CONTEXT:\n{context_preview}'
            
            messages.append({
                'role': 'system',
                'content': system_content
            })
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            response = client.chat.completions.create(
                model='gpt-4',
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            if response.choices and len(response.choices) > 0:
                logger.info("Successfully queried via OpenAI API with Cursor context")
                return response.choices[0].message.content
                
        except Exception as e:
            logger.debug(f"OpenAI API query with Cursor context failed: {e}")
        
        return None
    
    def _parse_cursor_response(self, response_text: str, email_content: Dict) -> Dict:
        """Parse the Cursor AI response into structured format"""
        # Fix any encoding issues in the response text first
        response_text = self._fix_encoding(response_text)
        
        parsed = {
            'transfer_eligible': False,
            'transfer_reasoning': '',
            'suggested_transfer_goal': '',
            'handling_instructions': '',
            'customer_response': '',
            'thread_summary': '',
            'full_response': response_text
        }
        
        # Try to extract sections from the response
        # Look for communication thread summary first
        thread_summary_match = re.search(r'COMMUNICATION THREAD SUMMARY[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|TRANSFER ELIGIBILITY|$)', response_text, re.DOTALL | re.IGNORECASE)
        if thread_summary_match:
            parsed['thread_summary'] = thread_summary_match.group(1).strip()
            logger.info("Extracted communication thread summary")
        else:
            # Try alternative patterns
            thread_summary_patterns = [
                r'Thread Summary[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)', 
                r'Communication Summary[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)',
                r'Summary of Communications[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)'
            ]
            for pattern in thread_summary_patterns:
                match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                if match:
                    parsed['thread_summary'] = match.group(1).strip()
                    logger.info("Extracted communication thread summary (alternative pattern)")
                    break
        
        # Look for transfer eligibility
        transfer_match = re.search(r'Transfer Eligible[:\s]*([YN]O|YES|NO)', response_text, re.IGNORECASE)
        if transfer_match:
            parsed['transfer_eligible'] = transfer_match.group(1).upper() in ['YES', 'Y']
        
        # Look for transfer reasoning
        reasoning_match = re.search(r'Reasoning:?\s*\n(.*?)(?=\n\n|\nSuggested|$)', response_text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            parsed['transfer_reasoning'] = reasoning_match.group(1).strip()
        
        # Look for suggested transfer goal
        goal_match = re.search(r'Suggested Transfer Goal[:\s]*\n(.*?)(?=\n\n|\n\d+\.|$)', response_text, re.DOTALL | re.IGNORECASE)
        if goal_match:
            parsed['suggested_transfer_goal'] = goal_match.group(1).strip()
        
        # Look for handling instructions (usually after "DETAILED HANDLING INSTRUCTIONS" or step numbers)
        instructions_match = re.search(r'(DETAILED HANDLING INSTRUCTIONS|Step \d+:|Handling Instructions)[:\s]*\n(.*?)(?=\n\nCUSTOMER|CUSTOMER EMAIL|$)', response_text, re.DOTALL | re.IGNORECASE)
        if instructions_match:
            parsed['handling_instructions'] = instructions_match.group(2).strip()
        else:
            # Fallback: get everything before customer response
            parts = re.split(r'CUSTOMER EMAIL RESPONSE|Customer Email Response', response_text, flags=re.IGNORECASE)
            if len(parts) > 1:
                parsed['handling_instructions'] = parts[0].strip()
        
        # Look for customer email response - multiple patterns
        # BUT FIRST: Check if case is transferable - if so, DO NOT extract customer response
        customer_response = None
        
        # If transfer eligible, check if there's a customer response (shouldn't be one)
        if parsed.get('transfer_eligible'):
            # Check if response says "NOT APPLICABLE" or is empty
            if 'NOT APPLICABLE' in response_text.upper() or 'not applicable' in response_text.lower():
                logger.info("Case is transferable - customer response correctly marked as NOT APPLICABLE")
                parsed['customer_response'] = ''
                return parsed
            # Even if there's text, for transferable cases we should not use it
            logger.warning("Case is transferable but customer response section found - will be ignored")
        
        # Only extract customer response if case is NOT transferable
        if not parsed.get('transfer_eligible'):
            # Pattern 1: Look for "CUSTOMER EMAIL RESPONSE" section
            customer_match = re.search(r'CUSTOMER EMAIL RESPONSE[:\s]*\n(.*?)(?=\n\n===|\n\nFULL CURSOR|$)', response_text, re.DOTALL | re.IGNORECASE)
            if customer_match:
                customer_response = customer_match.group(1).strip()
            
            # Pattern 2: Look for "3. CUSTOMER EMAIL RESPONSE" (numbered section)
            if not customer_response:
                customer_match = re.search(r'3\.\s*CUSTOMER EMAIL RESPONSE[:\s]*\n(.*?)(?=\n\n===|\n\nFULL CURSOR|$)', response_text, re.DOTALL | re.IGNORECASE)
                if customer_match:
                    customer_response = customer_match.group(1).strip()
            
            # Pattern 3: Look for German email content (starts with "Guten Tag" or similar)
            if not customer_response:
                german_starters = ['Guten Tag', 'Sehr geehrte', 'Hallo', 'Liebe', 'Lieber']
                for starter in german_starters:
                    pattern = rf'({starter}.*?)(?=\n\n===|\n\nFULL CURSOR|$)'
                    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        # Check if it contains German email closings (likely a complete email)
                        text = match.group(1).strip()
                        german_closings = ['Mit freundlichen Grüßen', 'Freundliche Grüße', 'Ihr o2 Team', 'Ihre o2 Kundenbetreuung', 'Ihr o2 Kundenbetreuer']
                        if any(closing in text for closing in german_closings):
                            customer_response = text
                            break
            
            # Pattern 4: Fallback - try to find German text at the end (likely the customer response)
            if not customer_response:
                german_closings = ['Mit freundlichen Grüßen', 'Freundliche Grüße', 'Ihr o2 Team', 'Ihre o2 Kundenbetreuung', 'Ihr o2 Kundenbetreuer']
                for closing in german_closings:
                    if closing in response_text:
                        # Find the last occurrence and get text from there to the end
                        idx = response_text.rfind(closing)
                        # Look backwards to find the start of the email (usually "Guten Tag" or similar)
                        text_before = response_text[:idx]
                        german_starters = ['Guten Tag', 'Sehr geehrte', 'Hallo', 'Liebe', 'Lieber']
                        start_idx = 0
                        for starter in german_starters:
                            last_starter = text_before.rfind(starter)
                            if last_starter > start_idx:
                                start_idx = last_starter
                        if start_idx > 0:
                            customer_response = response_text[start_idx:].strip()
                        else:
                            customer_response = response_text[idx:].strip()
                        break
        else:
            # Case is transferable - ensure customer_response is empty
            customer_response = None
            parsed['customer_response'] = ''
            logger.info("Case is transferable - customer response set to empty")
        
        # Clean up the customer response - remove markdown formatting, extra whitespace, and case ID mentions
        if customer_response:
            # Remove markdown code blocks
            customer_response = re.sub(r'```[a-z]*\n?', '', customer_response)
            # Remove markdown bold/italic
            customer_response = re.sub(r'\*\*([^*]+)\*\*', r'\1', customer_response)
            customer_response = re.sub(r'\*([^*]+)\*', r'\1', customer_response)
            # Remove case ID mentions (Fall #123456, Case #123456, etc.)
            customer_response = re.sub(r'\b(Fall|Case|Fallnummer|Case-ID)[\s:]*#?\d+\b', '', customer_response, flags=re.IGNORECASE)
            # Remove extra blank lines (more than 2 consecutive)
            customer_response = re.sub(r'\n{3,}', '\n\n', customer_response)
            # Remove leading/trailing whitespace
            customer_response = customer_response.strip()
            parsed['customer_response'] = customer_response
            logger.info(f"Extracted customer response ({len(customer_response)} chars)")
            print(f"[PARSING] Extracted customer email response ({len(customer_response)} characters)")
        else:
            # If customer response not found, DO NOT use placeholder
            # This should not happen if cursor-agent is working correctly
            logger.error("CRITICAL: Could not extract customer response from Cursor output!")
            logger.error("This indicates cursor-agent did not generate a proper response.")
            logger.error("DO NOT using placeholder - this would violate the no-placeholder policy.")
            print("[PARSING] ERROR: Could not extract customer response from Cursor output")
            print("[PARSING] This should not happen. cursor-agent should always generate a customer response.")
            # Set empty response - will be handled by transfer check logic
            parsed['customer_response'] = ''
        
        # Smart recognition: Check if transfer goal is an actual transfer target
        # vs just instructions for the agent
        if parsed.get('transfer_eligible') and parsed.get('suggested_transfer_goal'):
            transfer_goal = parsed['suggested_transfer_goal']
            # Check if it's an actual transfer target (starts with known prefixes)
            transfer_target_patterns = [
                r'^CBC_',  # Customer Backoffice Care teams
                r'^CL_',   # Collections teams
                r'^CS_',   # Customer Service teams
                r'^AS_',   # Agent Support teams
                r'^DS_',   # Data Service teams
                r'^.*@.*\.com',  # Email addresses
                r'^Kein Transfer',  # Explicit no transfer
            ]
            is_actual_transfer_target = any(re.match(pattern, transfer_goal, re.IGNORECASE) 
                                          for pattern in transfer_target_patterns)
            
            if not is_actual_transfer_target:
                # It's instructions, not a transfer target
                logger.info(f"Transfer goal '{transfer_goal}' is instructions, not a transfer target")
                logger.info("Case should be handled by agent, not transferred")
                parsed['transfer_eligible'] = False
                # Keep the instructions in handling_instructions, not as transfer goal
                if not parsed.get('handling_instructions'):
                    parsed['handling_instructions'] = f"Transfer instructions: {transfer_goal}"
                parsed['suggested_transfer_goal'] = ''
        
        return parsed
    
    def _generate_placeholder_analysis(self, email_content: Dict) -> Dict:
        """Generate placeholder analysis when Cursor is not available"""
        return {
            'transfer_eligible': False,
            'transfer_reasoning': 'Could not analyze case - Cursor AI not available. Please review manually.',
            'suggested_transfer_goal': '',
            'handling_instructions': 'Please review the case manually and determine appropriate handling steps.',
            'customer_response': self._generate_placeholder_response(email_content),
            'full_response': 'Cursor AI not available - placeholder response generated'
        }
    
    def _generate_placeholder_response(self, email_content: Dict) -> str:
        """
        DEPRECATED: This method should NOT be used.
        Placeholder responses are NOT allowed - all responses must be case-specific from cursor-agent.
        This method is kept only for backward compatibility but should never be called.
        """
        logger.error("CRITICAL: _generate_placeholder_response() was called - this should NEVER happen!")
        logger.error("All responses must be case-specific from cursor-agent. No placeholders allowed.")
        raise Exception("Placeholder responses are not allowed. cursor-agent must generate case-specific responses.")
    
    def create_output_file(self, case_id: str, cursor_response: Dict):
        """
        Create output file with case analysis and instructions
        
        Args:
            case_id: The case ID
            cursor_response: Parsed response from Cursor AI
        """
        # Extract just the numeric part of case ID for filename
        # Case IDs are typically like #30091006, #TEMP123456, or #CONV123456
        # Extract all digits from the case ID
        numeric_part = re.sub(r'\D', '', case_id)  # Remove all non-digits
        if not numeric_part:
            # Fallback: if no digits found, use cleaned version
            numeric_part = re.sub(r'[^\w-]', '_', case_id.replace('#', ''))
        output_file = self.output_dir / f"{numeric_part}.txt"
        
        logger.info(f"Creating output file: {output_file}")
        
        # Format case ID as "Fall #XXXXXXXX" (8 digits)
        # Extract numeric part and pad to 8 digits if needed
        numeric_part = re.sub(r'\D', '', case_id)  # Remove all non-digits
        if numeric_part:
            # Pad to 8 digits if shorter, truncate to 8 if longer
            if len(numeric_part) < 8:
                numeric_part = numeric_part.zfill(8)
            elif len(numeric_part) > 8:
                numeric_part = numeric_part[:8]
            formatted_case_id = f"Fall #{numeric_part}"
        else:
            # Fallback: use original case_id if no digits found
            formatted_case_id = case_id
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"CASE ANALYSIS - {formatted_case_id}\n")
            f.write("="*80 + "\n\n")
            
            # Communication Thread Summary (if available)
            thread_summary = cursor_response.get('thread_summary', '')
            if not thread_summary:
                # Fallback: Generate a basic summary from email content if cursor-agent didn't provide one
                email_content_for_summary = cursor_response.get('_email_content_for_summary', {})
                if email_content_for_summary:
                    subject = email_content_for_summary.get('subject', 'N/A')
                    from_email = email_content_for_summary.get('from', 'N/A')
                    conversation_count = len(email_content_for_summary.get('conversation_thread', []))
                    thread_summary = f"- Current inquiry: {subject}\n- From: {from_email}\n- Conversation thread: {conversation_count} message(s)\n- Review full conversation thread below for details"
            
            if thread_summary:
                f.write("COMMUNICATION THREAD SUMMARY:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{thread_summary}\n\n")
            
            # Transfer Eligibility
            f.write("TRANSFER ELIGIBILITY:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Transfer Eligible: {'YES' if cursor_response.get('transfer_eligible') else 'NO'}\n\n")
            
            if cursor_response.get('transfer_reasoning'):
                f.write("Reasoning:\n")
                f.write(f"{cursor_response['transfer_reasoning']}\n\n")
            
            if cursor_response.get('suggested_transfer_goal'):
                f.write("Suggested Transfer Goal:\n")
                f.write(f"{cursor_response['suggested_transfer_goal']}\n\n")
            elif not cursor_response.get('transfer_eligible'):
                f.write("Suggested Transfer Goal:\n")
                f.write("(Not applicable - case not transferable)\n\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("DETAILED HANDLING INSTRUCTIONS FOR AGENT\n")
            f.write("="*80 + "\n\n")
            
            if cursor_response.get('handling_instructions'):
                f.write(cursor_response['handling_instructions'])
            else:
                f.write("No specific instructions provided. Please review case manually.\n")
            
            f.write("\n\n" + "="*80 + "\n")
            f.write("CUSTOMER EMAIL RESPONSE\n")
            f.write("="*80 + "\n\n")
            
            # Check if case is transferable - if so, note that no email will be sent
            if cursor_response.get('transfer_eligible'):
                suggested_transfer = cursor_response.get('suggested_transfer_goal', '').strip()
                # Verify it's an actual transfer target
                if suggested_transfer:
                    transfer_target_patterns = [
                        r'^CBC_', r'^CL_', r'^CS_', r'^AS_', r'^DS_', r'^.*@.*\.com'
                    ]
                    is_actual_transfer_target = any(re.match(pattern, suggested_transfer, re.IGNORECASE) 
                                                  for pattern in transfer_target_patterns)
                    
                    if is_actual_transfer_target:
                        f.write("⚠️  IMPORTANT: This case is TRANSFERABLE.\n")
                        f.write("Per policy: NO email will be sent to the customer for transferable cases.\n")
                        f.write("Please proceed with the transfer process as outlined in the handling instructions above.\n\n")
                        f.write(f"Transfer to: {suggested_transfer}\n\n")
                    else:
                        # It's instructions, not a transfer - case should be handled by agent
                        f.write("ℹ️  NOTE: This case has handling instructions but is NOT transferable.\n")
                        f.write("The case should be handled by the agent (you) following the instructions above.\n")
                        f.write("A customer email response will be generated.\n\n")
                else:
                    f.write("⚠️  IMPORTANT: This case is TRANSFERABLE.\n")
                    f.write("Per policy: NO email will be sent to the customer for transferable cases.\n")
                    f.write("Please proceed with the transfer process as outlined in the handling instructions above.\n\n")
            elif cursor_response.get('customer_response'):
                f.write(cursor_response['customer_response'])
            else:
                f.write("No customer response generated.\n")
            
            # Removed "FULL CURSOR AI RESPONSE" section to declutter output file
            # Only essential information is kept for maximum ease of reading
        
        print(f"\n[OUTPUT] Created output file: {output_file}")
        logger.info(f"Output file created: {output_file}")
    
    def _fix_encoding(self, text: str) -> str:
        """
        Fix encoding issues where UTF-8 characters are double-encoded
        (e.g., "Rückmeldung" becomes "RĂĽckmeldung")
        
        Args:
            text: Text that may have encoding issues
            
        Returns:
            Text with encoding issues fixed
        """
        if not text:
            return text
        
        try:
            # Check if text contains common double-encoding patterns
            # These patterns indicate UTF-8 bytes interpreted as Latin-1/Windows-1252
            double_encoding_patterns = [
                ('ĂĽ', 'ü'),  # ü double-encoded
                ('Ă¤', 'ä'),  # ä double-encoded
                ('Ă¶', 'ö'),  # ö double-encoded
                ('Ăź', 'ß'),  # ß double-encoded
                ('Ă„', 'Ä'),  # Ä double-encoded
                ('Ăś', 'Ü'),  # Ü double-encoded
                ('Ă–', 'Ö'),  # Ö double-encoded
            ]
            
            # Try to fix double-encoding
            fixed_text = text
            for pattern, replacement in double_encoding_patterns:
                if pattern in fixed_text:
                    fixed_text = fixed_text.replace(pattern, replacement)
            
            # If we found and fixed patterns, return the fixed text
            if fixed_text != text:
                logger.info("Fixed encoding issues in text (double-encoded UTF-8)")
                return fixed_text
            
            # Try to decode if it's actually bytes
            if isinstance(text, bytes):
                try:
                    # Try UTF-8 first
                    return text.decode('utf-8')
                except UnicodeDecodeError:
                    # If that fails, try to fix by interpreting as Latin-1 then decoding as UTF-8
                    try:
                        return text.decode('latin-1').encode('latin-1').decode('utf-8')
                    except:
                        return text.decode('utf-8', errors='replace')
            
            # If text appears to be double-encoded, try to fix it
            # This happens when UTF-8 bytes are interpreted as Latin-1
            try:
                # Try encoding as Latin-1 then decoding as UTF-8 (reverse of double-encoding)
                if any(pattern in text for pattern, _ in double_encoding_patterns):
                    # Text is likely double-encoded, try to fix
                    encoded = text.encode('latin-1', errors='ignore')
                    decoded = encoded.decode('utf-8', errors='replace')
                    if decoded != text and len(decoded) > 0:
                        logger.info("Fixed double-encoded UTF-8 text")
                        return decoded
            except:
                pass
            
            return text
            
        except Exception as e:
            logger.debug(f"Error fixing encoding: {e}")
            return text
    
    def _text_to_html(self, text: str) -> str:
        """
        Convert plain text to HTML format suitable for TinyMCE editor
        Preserves paragraphs and line breaks
        
        Args:
            text: Plain text to convert
            
        Returns:
            HTML formatted string
        """
        if not text:
            return "<p></p>"
        
        # Replace double newlines with paragraph breaks
        # Single newlines become <br>
        html = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split by double newlines to get paragraphs
        paragraphs = html.split('\n\n')
        
        # Convert each paragraph
        html_paragraphs = []
        for para in paragraphs:
            if para.strip():
                # Replace single newlines within paragraph with <br>
                para_html = para.strip().replace('\n', '<br>')
                html_paragraphs.append(f'<p>{para_html}</p>')
        
        if not html_paragraphs:
            # If no paragraphs, just wrap the text
            html_text = text.replace('\n', '<br>')
            return f'<p>{html_text}</p>'
        
        return ''.join(html_paragraphs)
    
    def _preformat_reply(self, text: str) -> str:
        """
        Preformat the reply text before pasting into the editor.
        Normalizes line endings, trims lines, and enforces consistent paragraph spacing
        so the email displays correctly in TinyMCE (salutation, body, survey line, signature).
        """
        if not text:
            return ""
        # Normalize line endings
        out = text.replace('\r\n', '\n').replace('\r', '\n')
        # Trim each line (no trailing/leading spaces per line)
        lines = [line.rstrip() for line in out.split('\n')]
        # Rebuild: drop leading/trailing blank lines, collapse 3+ blank lines to 2
        rebuilt = []
        prev_blank = False
        blank_count = 0
        for line in lines:
            is_blank = (line.strip() == '')
            if is_blank:
                blank_count += 1
                # Allow at most one blank line in a row (one empty line between paragraphs)
                if blank_count <= 1:
                    rebuilt.append('')
                prev_blank = True
            else:
                blank_count = 0
                rebuilt.append(line)
                prev_blank = False
        # Strip leading and trailing blank lines
        while rebuilt and rebuilt[0].strip() == '':
            rebuilt.pop(0)
        while rebuilt and rebuilt[-1].strip() == '':
            rebuilt.pop()
        return '\n'.join(rebuilt)
    
    def write_response_to_editor(self, response_text: str):
        """
        Write the response text to the TinyMCE email composition editor
        Clears existing content before writing new content
        
        Args:
            response_text: The response text to write (should be clean German email body only)
        """
        logger.info("Writing response to email editor...")
        print("[EDITOR] Writing response to TinyMCE editor...")
        
        # Preformat: normalize line endings, trim lines, consistent paragraph spacing
        response_text = self._preformat_reply(response_text)
        
        # Clean the response text - remove any markdown, extra formatting, or instructions
        # This should already be clean from parsing, but do a final cleanup
        cleaned_text = response_text.strip()
        
        # Remove any remaining markdown formatting
        cleaned_text = re.sub(r'```[a-z]*\n?', '', cleaned_text)
        cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\*([^*]+)\*', r'\1', cleaned_text)
        cleaned_text = re.sub(r'#{1,6}\s+', '', cleaned_text)  # Remove markdown headers
        cleaned_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned_text)  # Remove markdown links
        
        # Remove any English instructions that might have been included
        # Look for common instruction patterns and remove them
        instruction_patterns = [
            r'CUSTOMER EMAIL RESPONSE[:\s]*\n',
            r'IMPORTANT[:\s]*\n',
            r'NOTE[:\s]*\n',
            r'Please note[:\s]*\n',
            r'Remember[:\s]*\n',
        ]
        for pattern in instruction_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove extra blank lines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        # Use cleaned text
        response_text = cleaned_text
        
        logger.info(f"Writing cleaned response to editor ({len(response_text)} chars)")
        print(f"[EDITOR] Writing cleaned German email body ({len(response_text)} characters) to editor...")
        
        # Ensure we're on email content page (where the editor is)
        if not self.ensure_email_content_page():
            logger.error("Cannot write response - not on email content page")
            print("[EDITOR] ERROR: Not on email content page")
            return
        
        # Wait for the reply section and editor to be in DOM (TinyMCE may have visibility:hidden initially)
        time.sleep(1)
        
        try:
            editor_found = False
            
            # Method 0: Scope to section "Nachricht verfassen" and find iframe inside baseEditorContainer (Sprinklr structure)
            try:
                logger.info("Attempting to find editor in section Nachricht verfassen...")
                section = self.page.locator('section[aria-label="Nachricht verfassen"]').first
                section.wait_for(state='attached', timeout=2500)
                base_container = section.locator('[data-testid="baseEditorContainer"]').first
                base_container.wait_for(state='attached', timeout=2500)
                iframe = base_container.locator('iframe[id$="_ifr"]').first
                if iframe.count() == 0:
                    iframe = base_container.locator('iframe').first
                iframe.wait_for(state='attached', timeout=2500)
                frame = iframe.content_frame()
                if frame:
                    body = frame.locator('body#tinymce').first
                    body.wait_for(state='attached', timeout=2500)
                    # TinyMCE wrapper can be visibility:hidden; make it visible so focus/setContent work
                    self.page.evaluate('''() => {
                        const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
                        if (section) {
                            const tox = section.querySelector('.tox-tinymce');
                            if (tox && tox.style) tox.style.visibility = 'visible';
                        }
                    }''')
                    time.sleep(0.5)
                    html_content = self._text_to_html(response_text)
                    body.evaluate('el => { el.innerHTML = ""; el.innerText = ""; }')
                    time.sleep(0.2)
                    body.evaluate(f'el => {{ el.innerHTML = {json.dumps(html_content)}; }}')
                    time.sleep(0.2)
                    body.evaluate('''
                        el => {
                            el.dispatchEvent(new Event("input", { bubbles: true }));
                            el.dispatchEvent(new Event("change", { bubbles: true }));
                            if (window.parent && window.parent.tinymce && window.parent.tinymce.editors && window.parent.tinymce.editors.length > 0) {
                                try { window.parent.tinymce.editors[0].fire("input"); window.parent.tinymce.editors[0].fire("change"); } catch (e) {}
                            }
                        }
                    ''')
                    editor_found = True
                    logger.info("Response written to editor (Nachricht verfassen + baseEditorContainer)")
                    print("[EDITOR] Successfully wrote response (reply section)")
            except Exception as e:
                logger.debug(f"Nachricht verfassen method failed: {e}")
                print(f"[EDITOR] Reply section method: {e}")
            
            # Method 1: Use TinyMCE API via parent window (most reliable)
            try:
                logger.info("Attempting to use TinyMCE API...")
                result = self.page.evaluate('''
                    () => {
                        try {
                            // Check if TinyMCE is available
                            if (window.tinymce && window.tinymce.editors && window.tinymce.editors.length > 0) {
                                const editor = window.tinymce.editors[0];
                                return { success: true, editorId: editor.id, method: 'tinymce_api' };
                            }
                            return { success: false, error: 'TinyMCE not found' };
                        } catch (e) {
                            return { success: false, error: e.message };
                        }
                    }
                ''')
                
                if result.get('success'):
                    editor_id = result.get('editorId')
                    logger.info(f"Found TinyMCE editor with ID: {editor_id}")
                    
                    # Convert text to HTML format
                    html_content = self._text_to_html(response_text)
                    
                    # Clear existing content first, then set new content (Skill 2: editor must start empty)
                    set_content_result = self.page.evaluate(f'''
                        (content) => {{
                            try {{
                                const editor = window.tinymce.editors[0];
                                editor.setContent('');
                                editor.setContent(content);
                                editor.fire('input');
                                editor.fire('change');
                                return {{ success: true }};
                            }} catch (e) {{
                                return {{ success: false, error: e.message }};
                            }}
                        }}
                    ''', html_content)
                    
                    if set_content_result.get('success'):
                        editor_found = True
                        logger.info("Response written to TinyMCE editor via API")
                        print("[EDITOR] Successfully wrote response using TinyMCE API")
            except Exception as e:
                logger.debug(f"TinyMCE API method failed: {e}")
            
            # Method 2: Find iframe and write directly to body#tinymce (container may have visibility:hidden)
            if not editor_found:
                try:
                    logger.info("Attempting to find TinyMCE iframe...")
                    # Wait for TinyMCE editor container (attached is enough; may be visibility:hidden)
                    tiny_mce_container = self.page.locator('section[aria-label="Nachricht verfassen"] [data-testid="tinyMCEEditor"], [data-testid="tinyMCEEditor"]').first
                    tiny_mce_container.wait_for(state='attached', timeout=2500)
                    logger.info("Found TinyMCE container")
                    # Find the iframe - it has an ID ending with "_ifr" (container may be visibility:hidden)
                    iframe = tiny_mce_container.locator('iframe[id$="_ifr"]').first
                    if iframe.count() == 0:
                        iframe = tiny_mce_container.locator('iframe').first
                    iframe.wait_for(state='attached', timeout=2500)
                    if iframe.count() > 0:
                        logger.info("Found TinyMCE iframe")
                        frame = iframe.content_frame()
                        if frame:
                            body = frame.locator('body#tinymce').first
                            body.wait_for(state='attached', timeout=2500)
                            if body.count() > 0:
                                logger.info("Found TinyMCE body element")
                                body.first.click()
                                time.sleep(0.5)
                                html_content = self._text_to_html(response_text)
                                body.first.evaluate('el => { el.innerHTML = ""; el.innerText = ""; }')
                                time.sleep(0.3)
                                body.first.evaluate(f'el => {{ el.innerHTML = {json.dumps(html_content)}; }}')
                                time.sleep(0.3)
                                body.first.evaluate('''
                                    el => {
                                        el.dispatchEvent(new Event("input", { bubbles: true }));
                                        el.dispatchEvent(new Event("change", { bubbles: true }));
                                        if (window.parent && window.parent.tinymce && window.parent.tinymce.editors && window.parent.tinymce.editors.length > 0) {
                                            try { window.parent.tinymce.editors[0].setContent(el.innerHTML); } catch (e) {}
                                        }
                                    }
                                ''')
                                editor_found = True
                                logger.info("Response written to TinyMCE editor (iframe method)")
                                print("[EDITOR] Successfully wrote response to TinyMCE editor")
                except Exception as e:
                    logger.debug(f"TinyMCE iframe method failed: {e}")
                    print(f"[EDITOR] Iframe method error: {e}")
            
            # Method 3: Try finding iframe by ID pattern (contains UUID ending with _ifr)
            if not editor_found:
                try:
                    logger.info("Attempting to find iframe by ID pattern...")
                    # Look for iframe with id ending with "_ifr"
                    iframes = self.page.locator('iframe[id$="_ifr"]').all()
                    if not iframes:
                        # Fallback: any iframe
                        iframes = self.page.locator('iframe').all()
                    
                    for iframe in iframes:
                        try:
                            if iframe.is_visible(timeout=2000):
                                frame = iframe.content_frame()
                                if frame:
                                    body = frame.locator('body#tinymce')
                                    if body.count() > 0:
                                        logger.info("Found TinyMCE body via iframe ID pattern")
                                        body.first.click()
                                        time.sleep(0.5)
                                        
                                        # Convert text to HTML
                                        html_content = self._text_to_html(response_text)
                                        
                                        # Clear and set content
                                        body.first.evaluate('el => { el.innerHTML = ""; el.innerText = ""; }')
                                        time.sleep(0.3)
                                        body.first.evaluate(f'el => {{ el.innerHTML = {json.dumps(html_content)}; }}')
                                        time.sleep(0.3)
                                        
                                        # Trigger events
                                        body.first.evaluate('''
                                            el => {
                                                el.dispatchEvent(new Event("input", { bubbles: true }));
                                                el.dispatchEvent(new Event("change", { bubbles: true }));
                                            }
                                        ''')
                                        
                                        editor_found = True
                                        logger.info("Response written to editor (iframe by ID pattern)")
                                        print("[EDITOR] Successfully wrote response (iframe by ID pattern)")
                                        break
                        except Exception as e:
                            logger.debug(f"Error with iframe: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Iframe by ID pattern method failed: {e}")
            
            # Method 4: Fallback - try via baseEditorContainer
            if not editor_found:
                try:
                    logger.info("Attempting baseEditorContainer method...")
                    base_container = self.page.locator('[data-testid="baseEditorContainer"]').first
                    if base_container.is_visible(timeout=3000):
                        iframe = base_container.locator('iframe').first
                        if iframe.is_visible(timeout=2000):
                            frame = iframe.content_frame()
                            if frame:
                                body = frame.locator('body#tinymce').first
                                if body.is_visible(timeout=2000):
                                    body.click()
                                    time.sleep(0.5)
                                    
                                    html_content = self._text_to_html(response_text)
                                    body.evaluate('el => { el.innerHTML = ""; }')
                                    time.sleep(0.3)
                                    body.evaluate(f'el => {{ el.innerHTML = {json.dumps(html_content)}; }}')
                                    body.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
                                    editor_found = True
                                    logger.info("Response written to editor (baseEditorContainer method)")
                                    print("[EDITOR] Successfully wrote response (baseEditorContainer method)")
                except Exception as e:
                    logger.debug(f"BaseEditorContainer method failed: {e}")
            
            if not editor_found:
                logger.error("Could not find email editor. Please check selectors.")
                print("[EDITOR] ERROR: Could not find email editor")
                
        except Exception as e:
            logger.error(f"Error writing response to editor: {e}")
            print(f"[EDITOR] ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def process_new_email(self, email_data: Dict, chat_only: bool = False):
        """
        Process a single new email: extract content, query Cursor AI, create output file, optionally write response.
        
        Args:
            email_data: Dictionary containing email information
            chat_only: If True, only print summary and suggested reply to stdout (for chat); do not write to editor.
        """
        case_id = email_data['case_id']
        
        # Format case ID as "Fall #XXXXXXXX" for annotation
        formatted_case_id = case_id
        if case_id and case_id.startswith('#'):
            numeric_part = re.sub(r'\D', '', case_id)
            if numeric_part:
                if len(numeric_part) < 8:
                    numeric_part = numeric_part.zfill(8)
                elif len(numeric_part) > 8:
                    numeric_part = numeric_part[:8]
                formatted_case_id = f"Fall #{numeric_part}"
        
        logger.info(f"Processing email with case ID: {case_id} (Fall #: {formatted_case_id})")
        
        print("\n" + "="*80)
        print(f"FALL #: {formatted_case_id}")
        print("="*80)
        print(f"PROCESSING EMAIL - Case ID: {case_id}")
        print("="*80 + "\n")
        
        # Extract full email content including conversation thread
        # This may update the case_id if a real one is found
        email_content = self.click_email_and_extract_content(email_data)
        
        # Use the case_id from email_content (may have been updated during extraction)
        final_case_id = email_content.get('case_id', case_id)
        
        # If case ID was updated, update email_data and processed_case_ids
        if final_case_id != case_id:
            logger.info(f"Case ID updated during extraction: {case_id} -> {final_case_id}")
            print(f"[CASE ID] Updated: {case_id} -> {final_case_id}")
            # Remove old case_id from processed set if it was a temp ID
            if case_id.startswith('#TEMP') or case_id.startswith('#CONV'):
                self.processed_case_ids.discard(case_id)
            case_id = final_case_id
        
        # Mark as processed with final case ID
        self.processed_case_ids.add(case_id)
        self._save_processed_case_ids()
        
        # Query Cursor AI
        # Format case ID for display
        display_case_id = final_case_id
        if final_case_id and final_case_id.startswith('#'):
            numeric_part = re.sub(r'\D', '', final_case_id)
            if numeric_part:
                if len(numeric_part) < 8:
                    numeric_part = numeric_part.zfill(8)
                elif len(numeric_part) > 8:
                    numeric_part = numeric_part[:8]
                display_case_id = f"Fall #{numeric_part}"
        
        print("\n" + "="*80)
        print(f"FALL #: {display_case_id}")
        print("="*80)
        print("QUERYING CURSOR AI...")
        print("="*80 + "\n")
        cursor_response = self.query_cursor_ai(email_content)
        
        # Create output file with final case ID
        print("\n" + "="*80)
        print("CREATING OUTPUT FILE...")
        print("="*80 + "\n")
        self.create_output_file(case_id, cursor_response)
        
        # Chat-only mode: print customer email (so Cursor can read it), then summary and suggested reply
        if chat_only:
            # First: print the actual customer email so Cursor can see/read what the customer sent
            print("\n" + "="*80)
            print("CUSTOMER EMAIL (what the customer sent - for Cursor to read):")
            print("="*80)
            print("Subject:", email_content.get('subject', 'N/A'))
            print("From:", email_content.get('from', 'N/A'))
            print("-"*40)
            print("Body:")
            body_text = email_content.get('body', '') or ''
            if isinstance(body_text, str):
                print(body_text.strip())
            else:
                print(str(body_text).strip())
            print("="*80 + "\n")
            print("COMMUNICATION THREAD SUMMARY (paste to chat):")
            print("="*80)
            thread_summary = cursor_response.get('thread_summary', '')
            if isinstance(thread_summary, str) and thread_summary:
                print(thread_summary)
            else:
                ec = cursor_response.get('_email_content_for_summary', {})
                if isinstance(ec, dict):
                    print(f"Subject: {ec.get('subject', 'N/A')}")
                    print(f"From: {ec.get('from', 'N/A')}")
                    print(f"Messages in thread: {len(ec.get('conversation_thread', []))}")
                else:
                    print(str(thread_summary or ec or 'N/A'))
            print("="*80 + "\n")
            print("PROPOSED EMAIL REPLY (paste to chat):")
            print("="*80)
            if cursor_response.get('transfer_eligible'):
                print("NOT APPLICABLE - Case is transferable; no customer email will be sent.")
            else:
                print(cursor_response.get('customer_response', ''))
            print("="*80 + "\n")
            print("[INFO] Chat-only mode: reply was NOT written to the browser. Use the 'sprinklr-write-reply' skill to write it when you say 'reply with ...'.")
            return
        
        # Check if case is transferable - if so, DO NOT send email to customer
        # Smart recognition: Only truly transferable if there's an actual transfer target
        is_transferable = cursor_response.get('transfer_eligible', False)
        suggested_transfer = cursor_response.get('suggested_transfer_goal', '').strip()
        
        # Verify it's an actual transfer target (not just instructions)
        if is_transferable and suggested_transfer:
            transfer_target_patterns = [
                r'^CBC_',  # Customer Backoffice Care teams
                r'^CL_',   # Collections teams
                r'^CS_',   # Customer Service teams
                r'^AS_',   # Agent Support teams
                r'^DS_',   # Data Service teams
                r'^.*@.*\.com',  # Email addresses
            ]
            is_actual_transfer_target = any(re.match(pattern, suggested_transfer, re.IGNORECASE) 
                                          for pattern in transfer_target_patterns)
            
            if not is_actual_transfer_target:
                # It's instructions for the agent, not a transfer target
                logger.info(f"Case marked as transferable but '{suggested_transfer}' is instructions, not a transfer target")
                logger.info("Case will be handled by agent - email will be sent to customer")
                is_transferable = False
        
        if is_transferable:
            print("\n" + "="*80)
            print("TRANSFERABLE CASE - NO EMAIL TO CUSTOMER")
            print("="*80 + "\n")
            suggested_transfer = cursor_response.get('suggested_transfer_goal', 'Unknown')
            print(f"[INFO] Case {case_id} is transferable to: {suggested_transfer}")
            print("[INFO] Per policy: No email will be sent to customer for transferable cases.")
            print("[INFO] Please proceed with the transfer process as outlined in the output file.")
            logger.info(f"Case {case_id} is transferable to {suggested_transfer} - skipping customer email per policy")
            # Clear customer response to ensure it's not used
            cursor_response['customer_response'] = ''
        elif cursor_response.get('customer_response') and cursor_response['customer_response'].strip():
            # Only write to editor if case is NOT transferable AND response exists
            
            # Final validation: Check for case ID mentions and remove them
            customer_response = cursor_response['customer_response']
            case_id_pattern = r'\b(Fall|Case|Fallnummer|Case-ID)[\s:]*#?\d+'
            if re.search(case_id_pattern, customer_response, re.IGNORECASE):
                logger.warning("Removing case ID mentions from customer response...")
                customer_response = re.sub(case_id_pattern, '', customer_response, flags=re.IGNORECASE)
                # Clean up extra spaces
                customer_response = re.sub(r'\s+', ' ', customer_response)
                customer_response = re.sub(r'\n\s*\n\s*\n', '\n\n', customer_response)
                cursor_response['customer_response'] = customer_response.strip()
            
            # Check for placeholder indicators - STRICT VALIDATION
            placeholder_indicators = [
                "wir werden Ihre Anfrage bearbeiten",
                "Wir werden Ihre Anfrage bearbeiten",
                "sehr geehrte damen und herren",
                "Sehr geehrte Damen und Herren",
                "mit freundlichen grüßen\nihr team",
                "Mit freundlichen Grüßen\nIhr Team"
            ]
            
            # Check for case ID mentions - STRICT CHECK
            case_id_patterns = [
                r'\b(Fall|Case|Fallnummer)[\s:]*#?\d+',  # "Fall #123" or "Case #123"
                r'vielen Dank für Ihre Nachricht bezüglich Fall',  # The forbidden phrase
                r'bezüglich Fall\s*#',  # "bezüglich Fall #"
            ]
            case_id_in_response = None
            for pattern in case_id_patterns:
                match = re.search(pattern, customer_response, re.IGNORECASE)
                if match:
                    case_id_in_response = match
                    break
            
            # Check for missing standard closing (should contain "Ihr o2 Kundenbetreuer" and "Lukasz Kowalski")
            has_standard_closing = "Ihr o2 Kundenbetreuer" in customer_response and "Lukasz Kowalski" in customer_response
            
            # Check if starts with wrong salutation
            wrong_salutation = customer_response.strip().startswith("Sehr geehrte")
            
            validation_errors = []
            if any(indicator in customer_response.lower() for indicator in [p.lower() for p in placeholder_indicators]):
                validation_errors.append("Contains forbidden placeholder text (e.g., 'wir werden Ihre Anfrage bearbeiten')")
            if case_id_in_response:
                validation_errors.append(f"CRITICAL: Contains FORBIDDEN case ID mention: '{case_id_in_response.group()}' - The phrase 'vielen Dank für Ihre Nachricht bezüglich Fall #' is ABSOLUTELY FORBIDDEN")
            if wrong_salutation:
                validation_errors.append("Starts with 'Sehr geehrte' instead of 'Guten Tag'")
            if not has_standard_closing:
                validation_errors.append("Missing standard closing template (should include 'Ihr o2 Kundenbetreuer' and 'Lukasz Kowalski')")
            
            # Check for the specific forbidden phrase
            if "vielen Dank für Ihre Nachricht bezüglich Fall" in customer_response:
                validation_errors.append("CRITICAL: Contains the ABSOLUTELY FORBIDDEN phrase 'vielen Dank für Ihre Nachricht bezüglich Fall' - This must NEVER be used")
            
            if validation_errors:
                logger.error("CRITICAL: Customer response FAILED validation!")
                for error in validation_errors:
                    logger.error(f"  - {error}")
                logger.error("This violates the no-placeholder policy. Response will NOT be written to editor.")
                print("\n[ERROR] Customer response FAILED validation - NOT writing to editor")
                print("[ERROR] Validation errors:")
                for error in validation_errors:
                    print(f"  - {error}")
                print("[ERROR] cursor-agent must generate a case-specific response that passes all validation checks")
                print("[ERROR] Response preview:")
                print(customer_response[:500])
            else:
                # Only write to editor if case is NOT transferable
                # Print proposed reply to stdout so it appears in chat/terminal when skill 2 is run
                print("\n" + "="*80)
                print("PROPOSED EMAIL REPLY (also shown in chat):")
                print("="*80)
                print(cursor_response['customer_response'])
                print("="*80 + "\n")
                print("WRITING RESPONSE TO EDITOR...")
                print("="*80 + "\n")
                
                # Ensure we're still on email content page before writing
                time.sleep(1)  # Wait for page to be stable and editor to be ready
                if not self.ensure_email_content_page():
                    logger.warning("Not on email content page, attempting to navigate back...")
                    # Try to navigate back to the email by clicking it again
                    # This is a fallback - ideally we should still be on the page
                    print("[WARNING] Had to navigate back to email content page")
                    time.sleep(1)  # Wait after navigation
                
                self.write_response_to_editor(cursor_response['customer_response'])
                print("\n[INFO] Response written to editor. Please review before sending.")
                print("[INFO] Waiting for you to click 'Send' in the console...")
                
                # Wait for user to send the email
                self.wait_for_email_sent(case_id)
        else:
            if is_transferable:
                print("\n[INFO] No customer response needed - case is transferable")
            else:
                print("\n[WARNING] No customer response generated. Please create response manually.")
                logger.warning("No customer response available - cursor-agent may not have generated one")
        
        print("\n" + "="*80)
        print(f"EMAIL PROCESSING COMPLETE - Case ID: {case_id}")
        print("="*80 + "\n")
    
    def wait_for_email_sent(self, case_id: str, max_wait_time: int = 300):
        """
        Wait for the user to send the email by monitoring if we return to console page
        or if the email disappears from the list
        
        Args:
            case_id: The case ID of the email being sent
            max_wait_time: Maximum time to wait in seconds (default 5 minutes)
        """
        logger.info(f"Waiting for user to send email with case ID: {case_id}")
        print(f"\n[WAITING] Monitoring for email send... (will wait up to {max_wait_time} seconds)")
        
        start_time = time.time()
        check_interval = 2  # Check every 2 seconds
        
        while time.time() - start_time < max_wait_time:
            try:
                current_state = self._detect_page_state()
                
                # If we're back on console page, the email was likely sent
                if current_state == 'console':
                    logger.info("Detected return to console page - email likely sent")
                    print("[INFO] Detected return to console page - email sent!")
                    time.sleep(1)  # Give it a moment to ensure we're really on console
                    return True
                
                # Also check if we can still see the email content page
                # If it's gone or changed, email might have been sent
                if current_state != 'email_content':
                    logger.info(f"Page state changed to: {current_state} - email likely sent")
                    print(f"[INFO] Page state changed - email sent!")
                    time.sleep(1)
                    return True
                
                # Small delay before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Error while waiting for email send: {e}")
                time.sleep(check_interval)
        
        # If we've waited too long, assume user is still working on it
        logger.warning(f"Timeout waiting for email send (case ID: {case_id})")
        print(f"[WARNING] Timeout waiting for email send. Continuing monitoring anyway...")
        return False
    
    def process_current_page_once(self, chat_only: bool = False, extract_only: bool = False) -> bool:
        """
        Process the current page once: if on email content page, extract and optionally reply; if on console, process first visible email. Then exit (no monitoring).
        When extract_only=True: only print the customer email to stdout and exit (no AI, no KB, no suggested reply in script). Cursor then queries KB and writes reply in chat.
        When chat_only=True: extract, query AI, print summary + suggested reply to stdout; do not write to editor.
        Returns True if an email was processed, False otherwise.
        """
        logger.info("Process-current-only: detecting page state (no navigation)...")
        print("[INFO] Process-current-only: reading current page (do not navigate)...")
        if extract_only:
            print("[INFO] Extract-only: will print the customer email and exit. Cursor will query KnowledgeBase and write the suggested reply in chat.")
        elif chat_only:
            print("[INFO] Chat-only mode: will output summary and suggested reply to chat (no browser write).")
        current_state = self._detect_page_state()
        logger.info(f"Current page state: {current_state}")
        print(f"[INFO] Current page state: {current_state}")
        if current_state == 'email_content':
            try:
                page_content = self.page.content()
                case_id = self.extract_case_id(page_content)
                if not case_id:
                    case_id = self.extract_case_id(self.page.url)
                if not case_id:
                    try:
                        case_header = self.page.locator('h2:has-text("Fall #"), h1:has-text("Fall #")').first
                        if case_header.is_visible(timeout=1200):
                            case_id = self.extract_case_id(case_header.inner_text())
                    except Exception:
                        pass
                if not case_id:
                    print("[WARN] Could not extract case ID from page. Ensure the case (Fall #...) is open.")
                    return False
                if case_id in self.processed_case_ids and not chat_only and not extract_only:
                    print(f"[INFO] Case {case_id} already processed. Writing reply anyway (will update editor).")
                # Wait for page and email content to be loaded (no fixed sleep)
                try:
                    self.page.wait_for_load_state('domcontentloaded', timeout=8000)
                    inbound = self.page.locator('[data-testid="inboundChatConversationItemFanMessage"]').last
                    inbound.wait_for(state='attached', timeout=8000)
                    body_in_last = inbound.locator('[data-testid="html-message-content"]').first
                    body_in_last.wait_for(state='visible', timeout=6000)
                except Exception as e:
                    logger.debug(f"Wait for email DOM: {e}")
                email_content = self.extract_email_content()
                if not email_content:
                    email_content = {'body': '', 'subject': '', 'from': ''}
                # Extract-only: print the email and exit; Cursor will do KB + suggested reply in chat
                if extract_only:
                    self._print_customer_email_and_exit(case_id, email_content)
                    return True
                email_data = {
                    'case_id': case_id,
                    'element': None,
                    'text_content': email_content.get('body', ''),
                    'timestamp': datetime.now().isoformat(),
                    'is_temp_id': False,
                    'already_on_content_page': True
                }
                self.process_new_email(email_data, chat_only=chat_only)
                return True
            except Exception as e:
                logger.error(f"Error processing current email: {e}")
                import traceback
                traceback.print_exc()
                print(f"[ERROR] {e}")
                return False
        if current_state == 'console' and not extract_only:
            new_emails = self.get_new_emails()
            if new_emails:
                self.process_new_email(new_emails[0], chat_only=chat_only)
                return True
            print("[INFO] On console but no unprocessed email in list. Open a case (Fall #...) then run again.")
            return False
        if extract_only and current_state == 'console':
            # Auto-open first visible email so Cursor can get content without user opening a case manually
            new_emails = self.get_new_emails()
            if new_emails:
                email_data = new_emails[0]
                case_id = email_data.get('case_id', '') or ''
                logger.info(f"Extract-only on console: opening first email (case {case_id}) then printing for Cursor.")
                print("[INFO] On console: opening first visible email, then extracting for Cursor...")
                email_content = self.click_email_and_extract_content(email_data)
                if not email_content:
                    email_content = {'body': '', 'subject': '', 'from': '', 'case_id': case_id}
                extracted_case_id = email_content.get('case_id') or case_id
                self._print_customer_email_and_exit(extracted_case_id, email_content)
                return True
            print("[INFO] Extract-only requires an open email. No emails in list. Open a case (Fall #...) in the browser, then run this skill again.")
            return False
        print("[INFO] Please open an email case (Fall #...) in the browser, then run this skill again.")
        return False

    def _print_customer_email_and_exit(self, case_id: str, email_content: dict) -> None:
        """Print the customer email to stdout so Cursor can read it; then script is done. Cursor queries KB and writes suggested reply in chat."""
        display_case_id = case_id
        if case_id and case_id.startswith('#'):
            numeric_part = re.sub(r'\D', '', case_id)
            if numeric_part:
                if len(numeric_part) < 8:
                    numeric_part = numeric_part.zfill(8)
                elif len(numeric_part) > 8:
                    numeric_part = numeric_part[:8]
                display_case_id = f"Fall #{numeric_part}"
        print("\n" + "="*80)
        print("CUSTOMER EMAIL (for Cursor to read — then query KnowledgeBase and write suggested reply in chat):")
        print("="*80)
        print("Case ID:", display_case_id)
        print("Subject:", email_content.get('subject', 'N/A'))
        print("From:", email_content.get('from', 'N/A'))
        print("-"*40)
        print("Body:")
        body_text = email_content.get('body', '') or ''
        if not isinstance(body_text, str):
            body_text = str(body_text)
        body_text = body_text.strip()
        # Avoid UnicodeEncodeError on Windows (e.g. \u202f) when printing to console
        try:
            print(body_text)
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
            print(body_text.encode(enc, errors='replace').decode(enc))
        print("="*80)
        print("[INFO] Script finished. Cursor: query KnowledgeBase and write the suggested reply in the chat window.")
        print("="*80 + "\n")

    def monitor_next_email_extract_only(self, check_interval: int = 5) -> None:
        """
        Wait for the next new email on the console, then open it and print the
        customer email + full thread in extract-only mode (for Skill 2).

        This is used after a reply was written and sent: it monitors until a new
        case appears, opens that case once, prints the email for Cursor, then exits.
        """
        logger.info(f"Waiting for next new email (extract-only, checking every {check_interval} seconds)...")
        print("\n" + "="*80)
        print("WAITING FOR NEXT NEW EMAIL (extract-only mode)")
        print(f"Checking for next email every {check_interval} seconds...")
        print("="*80 + "\n")

        while True:
            try:
                # Ensure we're on console page before scanning
                current_state = self._detect_page_state()
                if current_state != 'console':
                    if not self.ensure_console_page():
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Could not navigate to console page (waiting before next check)...")
                        time.sleep(check_interval)
                        continue

                # Look for new/unprocessed emails using the same detection logic as get_new_emails
                new_emails = self.get_new_emails()
                if not new_emails:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No new emails found yet (waiting)...")
                    time.sleep(check_interval)
                    continue

                # Take the first new email
                email_data = new_emails[0]
                case_id = email_data.get('case_id', '') or ''
                logger.info(f"Next new email detected for extract-only processing: {case_id}")
                print("\n" + "="*80)
                print(f"[NEXT EMAIL] Detected new email - Case ID: {case_id}")
                print("="*80 + "\n")

                # Click it and extract full content
                email_content = self.click_email_and_extract_content(email_data)
                if not email_content:
                    email_content = {'body': '', 'subject': '', 'from': '', 'case_id': case_id}

                # Prefer the case ID from extracted content if available
                extracted_case_id = email_content.get('case_id') or case_id
                if extracted_case_id and isinstance(extracted_case_id, str):
                    self.processed_case_ids.add(extracted_case_id)
                    self._save_processed_case_ids()

                # Print customer email + info for Cursor, then stop (no further monitoring)
                self._print_customer_email_and_exit(extracted_case_id or case_id, email_content)
                return

            except KeyboardInterrupt:
                logger.info("monitor_next_email_extract_only stopped by user")
                print("\n[INFO] Stopped waiting for next email (Ctrl+C).")
                return
            except Exception as e:
                logger.error(f"Error while waiting for next email (extract-only): {e}")
                import traceback
                traceback.print_exc()
                print(f"\n[ERROR] Error while waiting for next email: {e}")
                print("[INFO] Will continue waiting after a short delay...")
                time.sleep(check_interval)

    def monitor_emails(self, check_interval: int = 5):
        """
        Continuously monitor for new emails
        
        Args:
            check_interval: Seconds between checks for new emails
        """
        logger.info(f"Starting email monitoring (checking every {check_interval} seconds)...")
        print("\n" + "="*80)
        print("EMAIL MONITORING STARTED")
        print(f"Checking for new emails every {check_interval} seconds...")
        print("="*80 + "\n")
        
        try:
            while True:
                try:
                    # Detect current page state
                    current_state = self._detect_page_state()
                    logger.debug(f"Current page state: {current_state}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for new emails... (Current state: {current_state})")
                    
                    # If we're on email content page, check if there's an unprocessed case
                    if current_state == 'email_content':
                        logger.debug("On email content page, checking if case needs processing...")
                        print("  -> On email content page, checking for unprocessed case...")
                        try:
                            # Try to extract case ID from current page
                            page_content = self.page.content()
                            case_id = self.extract_case_id(page_content)
                            
                            # Also try URL
                            if not case_id:
                                current_url = self.page.url
                                case_id = self.extract_case_id(current_url)
                            
                            # If we found a case ID and it's not processed, process it
                            if case_id and case_id not in self.processed_case_ids:
                                logger.info(f"Found unprocessed case on email content page: {case_id}")
                                print(f"  -> Found unprocessed case: {case_id}, processing...")
                                
                                # Extract email content from current page
                                email_content = self.extract_email_content()
                                if email_content:
                                    email_data = {
                                        'case_id': case_id,
                                        'element': None,  # Already on content page
                                        'text_content': email_content.get('body', ''),
                                        'timestamp': datetime.now().isoformat(),
                                        'is_temp_id': False,
                                        'already_on_content_page': True
                                    }
                                    self.process_new_email(email_data)
                                    time.sleep(1)
                                    continue
                            elif case_id and case_id in self.processed_case_ids:
                                logger.debug(f"Case {case_id} already processed, waiting...")
                                print(f"  -> Case {case_id} already processed, waiting...")
                                time.sleep(check_interval)
                                continue
                            else:
                                # No case ID found or already processed, wait
                                logger.debug("On email content page but no unprocessed case found")
                                time.sleep(check_interval)
                                continue
                        except Exception as e:
                            logger.warning(f"Error checking email content page: {e}")
                            time.sleep(check_interval)
                            continue
                    
                    # Detect current page state first (without navigation)
                    current_state = self._detect_page_state()
                    
                    # Only ensure console page if we're NOT already on it (avoids unnecessary navigation)
                    if current_state != 'console':
                        # Ensure we're on console page to check for new emails
                        if not self.ensure_console_page():
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Could not navigate to console page")
                            time.sleep(check_interval)
                            continue
                    
                    # Get new emails (we're already on console page)
                    new_emails = self.get_new_emails()
                    
                    if new_emails:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(new_emails)} new email(s)!")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No new emails found")
                    
                    # Process each new email
                    for email_data in new_emails:
                        try:
                            self.process_new_email(email_data)
                            
                            # After processing and waiting for send, return to console page for next check
                            # The wait_for_email_sent should have already handled navigation back to console
                            # But ensure we're on console before continuing
                            time.sleep(1)  # Small delay after email processing
                            if self._detect_page_state() != 'console':
                                self.ensure_console_page()
                        except Exception as e:
                            logger.error(f"Error processing email: {e}")
                            import traceback
                            traceback.print_exc()
                            print(f"[ERROR] Error processing email: {e}")
                            print("[INFO] Continuing to next email...")
                            # Try to get back to console page
                            try:
                                if self._detect_page_state() != 'console':
                                    self.ensure_console_page()
                            except:
                                pass
                            time.sleep(1)  # Small delay before continuing
                    
                    # Wait before next check
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    raise  # Re-raise KeyboardInterrupt to be caught by outer handler
                except Exception as e:
                    logger.error(f"Error in monitoring iteration: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"\n[ERROR] Error in monitoring iteration: {e}")
                    print("[INFO] Continuing monitoring after error...")
                    # Don't cleanup - just wait and continue the loop
                    time.sleep(check_interval)
                    continue
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            print("\n[INFO] Monitoring stopped by user (Ctrl+C)")
            print("[INFO] Closing browser...")
            self.cleanup()
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n[ERROR] Fatal error in monitoring loop: {e}")
            print("[INFO] Attempting to continue...")
            # Wait a bit and try to restart the loop
            time.sleep(check_interval * 2)
            try:
                # Try to continue monitoring
                self.monitor_emails(check_interval=check_interval)
            except:
                logger.error("Could not recover from fatal error")
                print("[ERROR] Could not recover. Script will exit.")
                # Only cleanup on truly fatal errors
                self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Cleanup complete")


def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file (searches script dir, then repo root)."""
    try:
        candidates = [Path(config_path), _script_dir / config_path, _repo_root / config_path]
        for p in candidates:
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
        raise FileNotFoundError(config_path)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return {}


def _get_arg_value(flag: str) -> Optional[str]:
    """Get value for --flag=value from argv."""
    for arg in sys.argv[1:]:
        if arg.startswith(flag + '='):
            return arg.split('=', 1)[1].strip().strip('"\'')
    return None


def main():
    """Main entry point"""
    login_only = '--login-only' in sys.argv
    process_current_only = '--process-current-only' in sys.argv
    chat_only = '--chat-only' in sys.argv
    extract_only = '--extract-only' in sys.argv
    write_reply_only = '--write-reply-only' in sys.argv
    wait_next_extract_only = '--wait-next-extract-only' in sys.argv
    reply_file = _get_arg_value('--reply-file')
    # Load configuration
    config = load_config()
    
    # Get configuration values with defaults (env overrides config)
    URL = config.get('url', "https://telefonica-germany.sprinklr.com/app/console")
    CURSOR_CLI_PATH = config.get('cursor_cli_path')
    CHECK_INTERVAL = config.get('check_interval_seconds', 5)
    CDP_ENDPOINT = os.environ.get('SPRINKLR_CDP_ENDPOINT') or config.get('cdp_endpoint')  # e.g., "http://localhost:9222"
    
    # Create automation instance
    automation = EmailAutomation(URL, CURSOR_CLI_PATH, config)
    
    try:
        # Connect without navigating: Skill 2 (read email) and write-reply must not reload or change URL
        automation.connect_to_browser(CDP_ENDPOINT, leave_page_unchanged=(process_current_only or write_reply_only))
        
        # Verify connection and page state
        logger.info("Browser connected successfully")
        current_state = automation._detect_page_state()
        logger.info(f"Initial page state: {current_state}")
        
        # Write-reply-only: clear editor and write reply from file (Skill "reply with ...").
        # When --wait-next-extract-only is ALSO set, wait for send + monitor for next email in extract-only mode.
        if write_reply_only:
            if not reply_file or not Path(reply_file).exists():
                print(f"[ERROR] --write-reply-only requires --reply-file=<path> to an existing file.", file=sys.stderr)
                automation.cleanup()
                sys.exit(1)
            automation.ensure_email_content_page()
            # Best-effort extraction of current case ID (for nicer logging in wait_for_email_sent)
            current_case_id = ''
            try:
                page_content = automation.page.content()
                current_case_id = automation.extract_case_id(page_content) or automation.extract_case_id(automation.page.url) or ''
            except Exception:
                current_case_id = ''
            with open(reply_file, 'r', encoding='utf-8') as f:
                reply_text = f.read()
            automation.write_response_to_editor(reply_text)
            print("[INFO] Reply written to editor.")

            # Optional: after writing, wait for send and then auto-read the next incoming email (extract-only)
            if wait_next_extract_only:
                try:
                    # Wait until the user sends this email (return to console or page change)
                    automation.wait_for_email_sent(current_case_id or '')
                    # After send, ensure console page and monitor for the next new email once (extract-only)
                    automation.ensure_console_page()
                    automation.monitor_next_email_extract_only(check_interval=CHECK_INTERVAL)
                finally:
                    automation.cleanup()
                return

            print("[INFO] Reply written to editor. Execution stopped.")
            automation.cleanup()
            return
        
        # Skill 2: process current page once then exit
        if process_current_only:
            logger.info("Process-current-only: processing current page once, then exiting.")
            automation.process_current_page_once(chat_only=chat_only, extract_only=extract_only)
            automation.cleanup()
            return
        
        # Ensure we start on console page (login + set status to Verfügbar)
        automation.ensure_console_page()
        
        if login_only:
            logger.info("Login-only mode: exiting after login and status set.")
            print("[INFO] Login and status complete. Exiting (--login-only).")
            automation.cleanup()
            return
        
        # Start monitoring
        automation.monitor_emails(check_interval=CHECK_INTERVAL)
        
    except KeyboardInterrupt:
        logger.info("Script stopped by user")
        print("\n[INFO] Script stopped by user (Ctrl+C)")
        automation.cleanup()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] Fatal error: {e}")
        if automation.page is not None:
            print("[INFO] Attempting to continue...")
            try:
                automation.monitor_emails(check_interval=CHECK_INTERVAL)
            except Exception:
                logger.error("Could not recover from fatal error")
                print("[ERROR] Could not recover. Script will exit.")
                automation.cleanup()
        else:
            print("[INFO] Cannot continue without browser connection. Start Chrome with --remote-debugging-port=9222 first.")
            sys.exit(1)


if __name__ == "__main__":
    main()

