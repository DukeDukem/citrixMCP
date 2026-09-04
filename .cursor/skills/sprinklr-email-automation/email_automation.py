"""
Email Automation Script for Sprinklr Console
Monitors the Console tab for new emails, extracts content, queries Cursor AI,
and writes responses back to the email composition area.
"""

import re
import time
import json
import hashlib
import subprocess
import logging
import os
import sys
import requests
import uuid
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

DEBUG_LOG_PATH = _repo_root / "debug-912f41.log"
DEBUG_SESSION_ID = "912f41"
LATEST_RE_REPLY_PATH = _repo_root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json"
LATEST_USER_DIRECTED_REPLY_PATH = _repo_root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_user_directed_reply.json"


def _agent_debug_log(hypothesis_id: str, location: str, message: str, data: Dict):
    """Append one NDJSON debug line for runtime evidence collection."""
    try:
        payload = {
            "sessionId": DEBUG_SESSION_ID,
            "id": f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
            "timestamp": int(time.time() * 1000),
            "runId": "login-debug-1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        try:
            logger.error(f"DEBUG LOG WRITE FAILED at {location}: {e} (path={DEBUG_LOG_PATH})")
        except Exception:
            pass


# region agent log
_agent_debug_log(
    "H0",
    "email_automation.py:module_import",
    "Instrumentation module loaded",
    {"debug_log_path": str(DEBUG_LOG_PATH)},
)
# endregion


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
        self.login_url = config.get(
            'login_url',
            'https://telefonica-germany-app.sprinklr.com/ui/login?returnTo=%2Fui%2Fservice%2Flogin%3Fservice%3Dspr%26returnTo%3Dhttps%253A%252F%252Ftelefonica-germany.sprinklr.com%252Fapp%252Fconsole&service=spr'
        )
        self._stop_after_login = False
        self._login_popup_seen = False
        # When True (e.g. --process-current-only / read-email): never navigate away from email content page
        self._leave_page_unchanged = False
        # Hard anti-repaste guard: allow only one editor write per process run.
        self._reply_write_invoked = False

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
    
    def connect_to_browser(self, cdp_endpoint: Optional[str] = None, leave_page_unchanged: bool = False, stop_after_login: bool = False):
        """
        Connect to an existing Chrome browser instance via CDP (Chrome DevTools Protocol)

        Args:
            cdp_endpoint: CDP endpoint URL (e.g., 'http://localhost:9222')
                         If None, will try to find Chrome's CDP endpoint
            leave_page_unchanged: If True (read-email / process-current-only), do not navigate
                                 away from current page; ensure_console_page() will not leave email content.
        """
        self._leave_page_unchanged = leave_page_unchanged
        self._stop_after_login = stop_after_login
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
        
        # Get the best available page across ALL contexts (not just contexts[0]).
        # Root cause seen in runtime logs: first context/page can be chrome://new-tab-page
        # or unrelated tabs (e.g. forms), which breaks login/read flow.
        contexts = self.browser.contexts
        # region agent log
        _agent_debug_log(
            "H8",
            "email_automation.py:connect_to_browser:contexts",
            "Enumerating CDP contexts",
            {"context_count": len(contexts) if contexts else 0},
        )
        # endregion
        if contexts and len(contexts) > 0:
            all_pages = []
            for ctx in contexts:
                try:
                    for p in (ctx.pages or []):
                        all_pages.append((ctx, p))
                except Exception:
                    continue

            # region agent log
            _agent_debug_log(
                "H8",
                "email_automation.py:connect_to_browser:all_pages",
                "Collected pages across all contexts",
                {
                    "total_pages": len(all_pages),
                    "urls": [((p.url or "")[:180]) for _, p in all_pages[:12]],
                },
            )
            # endregion

            pages = [p for _, p in all_pages]
            # region agent log
            _agent_debug_log(
                "H8",
                "email_automation.py:connect_to_browser:context0_pages",
                "Legacy context0 page list (for comparison)",
                {
                    "page_count": len(pages) if pages else 0,
                    "page_urls": [((p.url or "")[:180]) for p in (pages or [])[:10]],
                },
            )
            # endregion
            if pages and len(pages) > 0:
                # Prefer an already-open case tab first, then any Sprinklr tab.
                # This prevents RE from attaching to the console list tab when a case is open in another tab.
                sprinklr_url_patterns = (
                    "telefonica-germany.sprinklr.com",
                    "telefonica-germany-app.sprinklr.com",
                    "sprinklr.com",
                )
                chosen = None
                case_tab_pattern = re.compile(r"/app/console/c/[a-z0-9]+")

                for p in pages:
                    try:
                        u = (p.url or "").lower()
                        if u.startswith("devtools://"):
                            continue
                        if any(host in u for host in sprinklr_url_patterns) and case_tab_pattern.search(u):
                            chosen = p
                            break
                    except Exception:
                        continue

                if chosen is not None:
                    logger.info("Selected open-case Sprinklr tab for process_current_only/read-email flow")

                for p in pages:
                    if chosen is not None:
                        break
                    try:
                        u = (p.url or "").lower()
                        if u.startswith("devtools://"):
                            continue
                        if any(host in u for host in sprinklr_url_patterns):
                            chosen = p
                            break
                    except Exception:
                        continue
                # If still nothing Sprinklr-like, prefer first non-devtools/non-chrome:// tab.
                if chosen is None:
                    for p in pages:
                        try:
                            u = (p.url or "").lower()
                            if u.startswith("devtools://") or u.startswith("chrome://"):
                                continue
                            chosen = p
                            break
                        except Exception:
                            continue
                if chosen is None:
                    chosen = pages[0]
                    if (chosen.url or "").lower().startswith("devtools://"):
                        logger.warning("Active tab is DevTools; no Sprinklr tab found.")
                        print("[ERROR] The active browser tab is DevTools (devtools://), not Sprinklr.")
                        print("[INFO] The script only reads the Sprinklr tab and does not switch tabs automatically.")
                        print("[INFO] Open or switch to the Sprinklr tab (Telefonica Germany / Console), then run again.")
                        raise Exception(
                            "No Sprinklr tab found. Current tab is DevTools. "
                            "Open the Sprinklr Console tab (telefonica-germany.sprinklr.com) and run again."
                        )
                self.page = chosen
                # region agent log
                _agent_debug_log(
                    "H9",
                    "email_automation.py:connect_to_browser:chosen_page",
                    "Chosen page in first-context strategy",
                    {"chosen_url": ((self.page.url or "")[:220])},
                )
                # endregion
                try:
                    self.page.bring_to_front()
                    logger.info("Brought chosen browser tab to front")
                except Exception as e:
                    logger.debug(f"Could not bring chosen tab to front: {e}")
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
                msg = (dialog.message or "")
                logger.info(f"Dialog appeared: {dialog.type} - {msg[:80]}")
                print(f"[POPUP] Accepting dialog: {dialog.type}")
                # In login-only mode, treat post-submit popup (e.g. missing audio) as login completion signal.
                if self._stop_after_login:
                    lowered = msg.lower()
                    if "audio" in lowered or "mikro" in lowered or "ton" in lowered or "missing" in lowered:
                        self._login_popup_seen = True
                        print("[LOGIN] Login popup signal detected; login-only flow will stop.")
                dialog.accept()
            self.page.on("dialog", _on_dialog)
            logger.info("Dialog listener added: dialogs will be accepted automatically")
        except Exception as e:
            logger.debug(f"Could not add dialog listener: {e}")
        
        # Detect current page state using smart detection
        current_state = self._detect_page_state()
        print(f"[PAGE STATE] Current page state: {current_state}")
        logger.info(f"Detected page state: {current_state}")
        
        # HARD LOGIN GATE - must be authenticated before any further actions.
        # For read-email/write-reply modes (leave_page_unchanged), never trigger login navigation/new tabs.
        logger.info("Running login verification gate...")
        print("[INFO] Verifying authenticated login before proceeding...")
        if leave_page_unchanged:
            # RE/PR modes must operate strictly on the current visible tab.
            # Do not run login heuristics here because they can be overly strict and block valid open-case tabs.
            if current_state in ['email_content', 'console']:
                pass
            else:
                raise Exception(
                    "Current tab is not a readable Sprinklr case/console page. "
                    "RE/write mode does not open new tabs or run login automatically. "
                    "Open the intended Sprinklr case tab and rerun."
                )
        else:
            self._ensure_logged_in_or_fail()
        
        if stop_after_login:
            logger.info("Stop-after-login mode enabled: skipping console/status/email checks")
            print("[INFO] Login-only mode: stopping immediately after successful login.")
        elif leave_page_unchanged:
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
            current_url_lower = current_url.lower()
            # region agent log
            _agent_debug_log(
                "H1",
                "email_automation.py:_check_login_status:url",
                "Checking login status URL",
                {"current_url": current_url[:400]},
            )
            # endregion
            
            # Check if we're on login page
            if 'login' in current_url_lower or 'ui/login' in current_url_lower:
                logger.info("On login page - not logged in")
                print("[LOGIN CHECK] On login page - not logged in")
                return False
            
            # Must be on Sprinklr domain and not on login URL.
            if 'sprinklr.com' not in current_url_lower:
                logger.info("Not on Sprinklr domain - not logged in for this automation context")
                print("[LOGIN CHECK] Not on Sprinklr domain")
                return False

            # Check if we're already logged in by looking for common logged-in elements
            logged_in_indicators = [
                '[data-testid*="case"]',
                '[data-testid="collapsed-case-item"]',  # Email cases
                '[aria-label*="Console"]',
                'h2:has-text("Fall #")',  # Case header
                '[data-testid="html-message-content"]',  # Email content
            ]
            
            for indicator in logged_in_indicators:
                try:
                    elem = self.page.locator(indicator).first
                    if elem.is_visible(timeout=2000):
                        # region agent log
                        _agent_debug_log(
                            "H2",
                            "email_automation.py:_check_login_status:indicator",
                            "Logged-in indicator visible",
                            {"indicator": indicator},
                        )
                        # endregion
                        logger.info("Already logged in - found logged-in indicator")
                        print(f"[LOGIN CHECK] Already logged in (found: {indicator})")
                        return True
                except:
                    continue

            # Fallback authenticated-state heuristic:
            # If we're on Sprinklr domain, not on login URL, and no visible login form fields,
            # treat as logged in. This prevents false negatives on pages that are authenticated
            # but don't render the case/console indicators yet.
            login_form_selectors = [
                'input[name="uid"]',
                'input[name="username"]',
                'input[autocomplete="username"]',
                'input[type="email"]',
                'input[name="pass"]',
                'input[name="password"]',
                'input[autocomplete="current-password"]',
                'input[type="password"]',
                'button[type="submit"]',
                'input[type="submit"]',
            ]
            login_form_visible = False
            for selector in login_form_selectors:
                try:
                    if self.page.locator(selector).first.is_visible(timeout=300):
                        login_form_visible = True
                        break
                except Exception:
                    continue

            if not login_form_visible:
                # region agent log
                _agent_debug_log(
                    "H3",
                    "email_automation.py:_check_login_status:fallback_auth",
                    "Auth inferred by fallback (no visible login form)",
                    {"current_url": current_url[:400]},
                )
                # endregion
                logger.info("No login form visible on Sprinklr non-login URL; treating session as authenticated")
                print("[LOGIN CHECK] Authenticated session inferred (non-login Sprinklr page, no login form)")
                return True
            
            logger.info("Could not find logged-in indicators")
            print("[LOGIN CHECK] Could not determine login status")
            # region agent log
            _agent_debug_log(
                "H4",
                "email_automation.py:_check_login_status:unverified",
                "Login status unresolved",
                {"current_url": current_url[:400], "login_form_visible": login_form_visible},
            )
            # endregion
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
            current_url_lower = current_url.lower()
            
            # Navigate to login page if not already there OR current tab is not Sprinklr.
            if ('login' not in current_url_lower and 'ui/login' not in current_url_lower) or ('sprinklr.com' not in current_url_lower):
                logger.info("Not on login page, navigating...")
                print("[LOGIN] Navigating to login page...")
                self.page.goto(self.login_url, wait_until='domcontentloaded', timeout=15000)
                try:
                    self.page.bring_to_front()
                except Exception:
                    pass
                time.sleep(0.2)
            
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
                'input[name="username"]',
                'input[autocomplete="username"]',
                'input[aria-label*="Enter Email"]',
                'input[aria-label*="Email"]',
                'input[type="email"][aria-label*="Email"]',
                'input[placeholder*="Email"]',
                'input[type="email"]',
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = self.page.locator(selector).first
                    if email_input.is_visible(timeout=1200):
                        email_input.click()
                        email_input.fill('')  # Clear existing value
                        email_input.fill(self.login_email)
                        email_filled = True
                        logger.info("Email filled")
                        break
                except:
                    continue
            
            if not email_filled:
                logger.warning("Could not find email input field on current tab. Trying fresh login tab fallback...")
                print("[LOGIN] Email field not found. Opening fresh login tab...")
                # region agent log
                _agent_debug_log(
                    "H5",
                    "email_automation.py:_perform_login:email_not_found",
                    "Email field not found on current tab",
                    {"current_url": (self.page.url or "")[:400]},
                )
                # endregion
                try:
                    fresh_page = self.page.context.new_page()
                    fresh_page.goto(self.login_url, wait_until='domcontentloaded', timeout=15000)
                    self.page = fresh_page
                    try:
                        self.page.bring_to_front()
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"Fresh login tab fallback failed: {e}")
                    return False

                for selector in email_selectors:
                    try:
                        email_input = self.page.locator(selector).first
                        if email_input.is_visible(timeout=1800):
                            email_input.click()
                            email_input.fill('')
                            email_input.fill(self.login_email)
                            email_filled = True
                            logger.info("Email filled (fresh tab fallback)")
                            break
                    except Exception:
                        continue

                if not email_filled:
                    logger.error(f"Could not find email input field. Current URL: {self.page.url}")
                    # region agent log
                    _agent_debug_log(
                        "H5",
                        "email_automation.py:_perform_login:email_not_found_fallback",
                        "Email field not found even after fresh tab fallback",
                        {"current_url": (self.page.url or "")[:400]},
                    )
                    # endregion
                    return False
            
            # Fill password
            password_selectors = [
                'input[name="pass"]',
                'input[name="password"]',
                'input[autocomplete="current-password"]',
                'input[aria-label*="Enter Password"]',
                'input[type="password"][aria-label*="Password"]',
                'input[placeholder*="Password"]',
                'input[type="password"]',
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = self.page.locator(selector).first
                    if password_input.is_visible(timeout=1200):
                        password_input.click()
                        password_input.fill('')
                        password_input.fill(self.login_password)
                        password_filled = True
                        logger.info("Password filled")
                        break
                except:
                    continue
            
            if not password_filled:
                logger.error("Could not find password input field")
                # region agent log
                _agent_debug_log(
                    "H6",
                    "email_automation.py:_perform_login:password_not_found",
                    "Password field not found",
                    {"current_url": (self.page.url or "")[:400]},
                )
                # endregion
                return False
            
            # Submit the form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Anmelden")',
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = self.page.locator(selector).first
                    if submit_button.is_visible(timeout=1200):
                        submit_button.click()
                        logger.info("Login form submitted")
                        submitted = True
                        break
                except:
                    continue
            if not submitted:
                # Fast fallback: press Enter in password field.
                try:
                    self.page.keyboard.press("Enter")
                    submitted = True
                    logger.info("Login submitted via Enter key fallback")
                except Exception:
                    pass
            
            # Wait for navigation after login
            logger.info("Waiting for login to complete...")
            # Wait for URL to change or for login to complete
            max_wait = 8
            waited = 0
            while waited < max_wait:
                current_url = self.page.url
                if 'login' not in current_url.lower() and 'sprinklr.com' in current_url:
                    logger.info("Login appears to have completed")
                    break
                time.sleep(0.5)
                waited += 0.5
            
            if self._stop_after_login:
                logger.info("Stop-after-login mode: ending login flow immediately after submit.")
                # region agent log
                _agent_debug_log(
                    "H7",
                    "email_automation.py:_perform_login:stop_after_login",
                    "Stop-after-login branch taken",
                    {"current_url": (self.page.url or "")[:400], "popup_seen": bool(self._login_popup_seen)},
                )
                # endregion
                return True

            # Navigate to console URL if needed
            if self.url not in self.page.url:
                logger.info(f"Navigating to console URL: {self.url}")
                try:
                    self.page.goto(self.url, wait_until='domcontentloaded', timeout=15000)
                    time.sleep(0.4)
                except Exception as e:
                    logger.warning(f"Navigation timeout, but continuing: {e}")
                    time.sleep(0.3)
            
            logger.info("Login process completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False

    def _ensure_logged_in_or_fail(self):
        """
        Hard login gate: verify authenticated state before proceeding.
        Retries login once, then fails fast if still not authenticated.
        """
        if self._check_login_status():
            return True

        print("[LOGIN] Login not verified. Starting login flow...")
        first_attempt = self._check_and_login()
        time.sleep(0.3)
        if self._stop_after_login and first_attempt:
            # Login-only strict stop: once submit flow completes (or popup signal appears), stop immediately.
            print("[LOGIN] Login-only mode: login submit flow completed. Stopping without further retries.")
            return True
        if first_attempt and self._check_login_status():
            print("[LOGIN] Login verified after first attempt.")
            return True

        print("[LOGIN] First login attempt failed/unverified. Retrying once...")
        second_attempt = self._check_and_login()
        time.sleep(0.3)
        if self._stop_after_login and second_attempt:
            print("[LOGIN] Login-only mode: stopping after retry submit flow.")
            return True
        if second_attempt and self._check_login_status():
            print("[LOGIN] Login verified after retry.")
            return True

        raise Exception("ERROR: LOGIN NOT VERIFIED. STOPPING AUTOMATION.")
    
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
            # Console list = .../app/console/c (no case id). Case page = .../app/console/c/<id> (e.g. 699d1e46...).
            # So: only treat as "case page" when there is a non-empty id segment after /c/.
            url_is_case_page = bool(re.search(r'/app/console/c/[a-z0-9]+', current_url)) or (
                '/console/c/' in current_url and re.search(r'/console/c/[a-z0-9]+', current_url)
            )
            
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
            
            # Check if URL suggests console page (even if elements not visible yet).
            # Do NOT return 'console' when URL is a case-open page (url_is_case_page) so we don't
            # mis-detect the email content page as console and re-navigate away.
            if url_has_console and not url_is_case_page:
                logger.info("Detected: Console page (URL pattern)")
                print("[PAGE DETECTION] Console page detected via URL pattern")
                return 'console'
            if url_has_console and url_is_case_page:
                # Could be email content view with case open; indicators may still be loading
                logger.info("URL is case page (/console/c/...), not assuming console")
                print("[PAGE DETECTION] URL suggests case page - not assuming console")
            
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
                            # and URL has console (and is not a case-open page), assume console
                            if url_has_console and not url_is_case_page:
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

    def _is_console_list_url(self) -> bool:
        """True when URL is the console list (e.g. .../app/console/c) with no case id after /c."""
        try:
            u = (self.page.url or "").lower().split("?")[0].rstrip("/")
            # Must end with /app/console/c (no id segment after c; /c/699d... would not match)
            return u.endswith("/app/console/c")
        except Exception:
            return False

    def _has_collapsed_case_item(self) -> bool:
        """True when at least one collapsed-case-item is visible (new case ready to be read)."""
        try:
            loc = self.page.locator("[data-testid=\"collapsed-case-item\"]").first
            return loc.is_visible(timeout=800)
        except Exception:
            return False

    # In-page script: runs inside Chrome to watch for new cases on console/c and open the first one.
    _AUTO_OPEN_NEW_CASE_SCRIPT = r"""
    (function() {
      var pathname = window.location.pathname || '';
      if (!/\/app\/console\/c$/.test(pathname.replace(/\/$/, ''))) return;
      if (window.__sprinklrAutoOpenActive) return;
      window.__sprinklrAutoOpenActive = true;
      var root = document.querySelector('[data-entityid="CollapsedPreviewsList"]') || document.body;
      function clickFirstCollapsed() {
        var items = document.querySelectorAll('[data-testid="collapsed-case-item"]');
        for (var i = 0; i < items.length; i++) {
          var el = items[i];
          if (el.offsetParent !== null && el.getBoundingClientRect().width > 0) {
            el.click();
            if (window.__sprinklrAutoOpenObserver) {
              window.__sprinklrAutoOpenObserver.disconnect();
              window.__sprinklrAutoOpenObserver = null;
            }
            window.__sprinklrAutoOpenActive = false;
            return true;
          }
        }
        return false;
      }
      var observer = new MutationObserver(function() {
        if (window.location.pathname && !/\/app\/console\/c$/.test(window.location.pathname.replace(/\/$/, ''))) return;
        if (clickFirstCollapsed()) return;
      });
      observer.observe(root, { childList: true, subtree: true });
      window.__sprinklrAutoOpenObserver = observer;
      setTimeout(function() { clickFirstCollapsed(); }, 800);
      return true;
    })();
    """

    def _inject_auto_open_new_case_script(self) -> bool:
        """
        Inject script into the page so Chrome itself watches for new cases on console/c
        and opens the first one. Only runs when we're on the list URL.
        """
        if not self._is_console_list_url():
            return False
        try:
            self.page.evaluate(self._AUTO_OPEN_NEW_CASE_SCRIPT)
            logger.info("Injected in-page auto-open script (Chrome will open first new case on list)")
            return True
        except Exception as e:
            logger.debug("Could not inject auto-open script: %s", e)
            return False

    def _ensure_console_list_url(self) -> bool:
        """
        When we need to monitor and open new emails, we must be on the list URL (console/c), NOT console/c/<id>.
        If we're on console but URL is not .../app/console/c, navigate to the list URL so new cases are visible.
        When on list URL, injects in-page script so Chrome itself auto-opens the first new case.
        """
        if self._is_console_list_url():
            self._inject_auto_open_new_case_script()
            return True
        try:
            current_url = (self.page.url or "").lower()
            # Only navigate if we're on some console path but not the list (e.g. /app/console without /c)
            if "/console" not in current_url and "/app/console" not in current_url:
                return False
            if re.search(r'/app/console/c/[a-z0-9]+', current_url):
                # We're on a case page (console/c/<id>), not the list - go to list
                list_url = self.url.rstrip("/")
                if not list_url.endswith("/c"):
                    list_url = list_url + "/c"
                logger.info("Navigating to console list URL (console/c) to monitor for new emails")
                print("[INFO] Navigating to console list (console/c) to monitor and open new email...")
                self.page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                if self._is_console_list_url():
                    self._inject_auto_open_new_case_script()
                    return True
                return False
            # We're on /app/console without /c - go to /app/console/c
            list_url = self.url.rstrip("/") + ("/c" if not self.url.rstrip("/").endswith("/c") else "")
            logger.info("Navigating to console list URL (console/c) to monitor for new emails")
            print("[INFO] Navigating to console list (console/c) to monitor and open new email...")
            self.page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            if self._is_console_list_url():
                self._inject_auto_open_new_case_script()
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not ensure console list URL: {e}")
            return False

    def ensure_console_page(self):
        """Ensure we're on the console page, navigate if needed - AVOID UNNECESSARY RELOADS"""
        current_state = self._detect_page_state()
        
        # When in read-email / process-current-only mode: never navigate away from email content.
        # Stay on the email page so we only "navigate to email" once (user already has it open).
        if getattr(self, '_leave_page_unchanged', False) and current_state == 'email_content':
            logger.info("Leave-page-unchanged: already on email content page, not navigating to console")
            return True
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

        # Fallback for mis-detection: if reply editor is visible, treat page as email content.
        try:
            editor_section = self.page.locator('section[aria-label="Nachricht verfassen"]').first
            if editor_section.count() > 0 and editor_section.is_visible(timeout=1200):
                logger.info("Email content fallback: reply editor is visible, proceeding.")
                print("[INFO] Email-content fallback active: reply editor detected.")
                return True
        except Exception:
            pass
        
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
        Extract case ID from text (format: # followed by at least 6 numbers,
        or "Fall Nr. 12345678" / "Fall #12345678").
        """
        if not text:
            return None
        pattern = r'#(\d{6,})'
        match = re.search(pattern, text)
        if match:
            return f"#{match.group(1)}"
        # Sidebar collapsed-case-item aria-label: "Fall Nr. 55411928 von …"
        match2 = re.search(r'(?i)Fall\s*(?:Nr\.?|#)?\s*(\d{6,})', text)
        if match2:
            return f"#{match2.group(1)}"
        return None

    @staticmethod
    def _fall_digits(case_id: Optional[str]) -> Optional[str]:
        """Normalize Fall id to digit string only (e.g. '#55411928' → '55411928')."""
        if not case_id:
            return None
        m = re.search(r'(\d{6,})', str(case_id))
        return m.group(1) if m else None

    # Canonical case ID element: <h2>Fall <span data-testid="box" ...>#36556980</span></h2> (always use this, never body/URL)
    _CASE_ID_HEADER_SELECTOR = "h2:has-text('Fall') span:has-text('#'), h1:has-text('Fall') span:has-text('#')"
    _CASE_ID_HEADER_FALLBACK = "h2:has-text('Fall'), h1:has-text('Fall')"

    def _get_case_id_from_page_header(self) -> Optional[str]:
        """
        Get the case ID from the canonical page element only:
        <h2>Fall <span data-testid="box" ...>#36556980</span></h2>
        This is the only source for case ID; do not use page body or URL to avoid Kundennummer etc.
        """
        try:
            # First: span inside h2 that contains # (the exact element the user specified)
            span = self.page.locator(self._CASE_ID_HEADER_SELECTOR).first
            if span.count() and span.is_visible(timeout=1200):
                text = span.inner_text()
                cid = self.extract_case_id(text.strip())
                if cid:
                    return cid
            # Fallback: full h2 text if span not found
            header = self.page.locator(self._CASE_ID_HEADER_FALLBACK).first
            if header.is_visible(timeout=500):
                return self.extract_case_id(header.inner_text())
        except Exception:
            pass
        return None
    
    def get_new_emails(self) -> List[Dict]:
        """
        Get list of new emails from the Console tab.
        ALWAYS when the user is on console/c (list URL, NOT console/c/<id>), we monitor and open the new email.
        """
        new_emails = []
        
        # Ensure we're on the console page
        if not self.ensure_console_page():
            logger.warning("Cannot get emails - not on console page")
            print("[EMAIL DETECTION] Cannot get emails - not on console page")
            return new_emails
        
        # ALWAYS when monitoring for new emails we must be on the list URL (console/c), never console/c/<id>
        if not self._ensure_console_list_url():
            logger.warning("Could not ensure console list URL (console/c)")
            print("[EMAIL DETECTION] Could not reach console list (console/c).")
            return new_emails
        
        # New case ready to be read = BOTH: console list URL (/app/console/c) AND collapsed-case-item present
        on_list_url = self._is_console_list_url()
        has_item = self._has_collapsed_case_item()
        if not on_list_url or not has_item:
            logger.info("New case requires both: console list URL and collapsed-case-item. URL=%s, item=%s", on_list_url, has_item)
            print("[EMAIL DETECTION] New case requires both: URL = .../app/console/c (list) and item = collapsed-case-item visible.")
            return new_emails
        
        try:
            print("[EMAIL DETECTION] Console list URL + collapsed-case-item present - scanning for new case(s)...")
            # On /app/console/c (list page, not /c/<id>), presence of collapsed-case-item = new case ready to be read
            # Find collapsed-case-item entries (both URL and item conditions already satisfied above)
            email_selectors = [
                'button[data-testid="collapsed-case-item"]',  # Case stream: new case ready to be read on /app/console/c
                '[data-testid="collapsed-case-item"]',  # Same without tag (in case structure varies)
                '[data-entityid="CollapsedPreviewsList"] button[data-testid="collapsed-case-item"]',  # Collapsed preview in sidebar
                '[data-testid="case-item-root"] div.cardItem',  # Console stream case cards (SLA, name, subject, preview)
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
            
            # Case ID is always from the canonical element (h2 > span #36556980); never from page body
            real_case_id = self._get_case_id_from_page_header()
            if not real_case_id:
                real_case_id = self.extract_case_id(self.page.url)
            if not real_case_id:
                try:
                    real_case_id = self.extract_case_id(self.page.title())
                except Exception:
                    pass
            page_content = self.page.content()  # keep for ConversationId fallback below
            
            # Method 5: Try to extract from ConversationId in email content (as fallback identifier)
            if not real_case_id:
                try:
                    # Look for ConversationId pattern: %%[ConversationId: ...]%%
                    conv_id_match = re.search(r'%%\[ConversationId:\s*([a-f0-9]+)\]%%', page_content, re.IGNORECASE)
                    if conv_id_match:
                        conv_id = conv_id_match.group(1)
                        # Use first 8 chars as a case identifier if no real case ID found
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
            
            # If we still have a temp/conv id, try page header again for the real case ID
            if email_content['case_id'].startswith('#TEMP') or email_content['case_id'].startswith('#CONV'):
                extracted_case_id = self._get_case_id_from_page_header()
                if extracted_case_id:
                    email_content['case_id'] = extracted_case_id
                    logger.info(f"Updated case ID from header: {extracted_case_id}")
            
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

STEP 3 - GENERATE RESPONSE IN THIS EXACT ORDER (MANDATORY OUTPUT STRUCTURE):
You MUST output the following sections in this order. Use these exact section headers so the script can parse your response.

---
## 1. CUSTOMER CASE SUMMARY
Concise summary in English: case ID, subject, from; who wrote what (customer vs. brand), in order; main request and current status. No long prose.

---
## 2. VERIFICATION
Customer verified: Yes or No. If Yes, list verified key data (name, Kundennummer, last 4 IBAN, address, Geburtsdatum, etc.) in English. Never ask for PKK.

---
## 3. TRANSFER ELIGIBILITY
Query KnowledgeBase/TransferMatrix.md. Identify Thema and Fall; state Ziel-Kontakt.
Transfer eligible: Yes (case goes to another team/queue/email) or No (we handle directly or Kein Transfer).

---
## 4a. TRANSFER GOAL (if transferable)
If Transfer eligible = Yes: state Transfer goal (queue/team name or email) and action (e.g. "Transfer in Sprinklr" or "Forward to email").
If Transfer eligible = No, write "Not applicable - case not transferable".

---
## 4b. IF NOT TRANSFERABLE
If Transfer eligible = No: briefly state that KB was queried for handling. (Skip 4a.)

---
## 5. INSTRUCTIONS ON HANDLING CASE
KB-based + agent steps in one section: which path, ticket type/Themen-ID, inbox, Buchungsgrund, or "direct customer to X"; what to do in Sprinklr/systems. Cite KB where relevant. Numbered or bulleted.

---
## 6. YOUR RESPONSE TO CUSTOMER
Full suggested email reply in German (copyable block). ONLY IF Transfer eligible = No. If Transfer eligible = Yes, write "NOT APPLICABLE - Case is transferable, no customer email will be sent".
Use the exact template (salutation, body, survey line, signature block) specified below. Do not truncate.

---
## 7. SUMMARY OF RESPONSE
One short paragraph in English: what the reply says and what the agent/customer should do next.
---

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

2. Show specific sympathy for the customer's case and circumstance. Add an apology only when contextually necessary (clear inconvenience, error, delay, or misinformation caused by us). If context does not warrant an apology, do not include one.

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
        
        # Try to extract sections from the response (supports both 7-step structure and legacy format)
        # Look for customer case summary / communication thread summary first
        thread_summary_match = re.search(
            r'(?:##\s*1\.\s*CUSTOMER CASE SUMMARY|COMMUNICATION THREAD SUMMARY)[:\s]*\n(.*?)(?=\n\n---|\n\n##\s*2\.|\n\nTRANSFER|TRANSFER ELIGIBILITY|$)', response_text, re.DOTALL | re.IGNORECASE
        )
        if thread_summary_match:
            parsed['thread_summary'] = thread_summary_match.group(1).strip()
            logger.info("Extracted customer case summary / thread summary")
        else:
            thread_summary_patterns = [
                r'Thread Summary[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)',
                r'Communication Summary[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)',
                r'Summary of Communications[:\s]*\n(.*?)(?=\n\n===|\n\nTRANSFER|$)'
            ]
            for pattern in thread_summary_patterns:
                match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                if match:
                    parsed['thread_summary'] = match.group(1).strip()
                    logger.info("Extracted thread summary (alternative pattern)")
                    break
        
        # Look for transfer eligibility
        transfer_match = re.search(r'Transfer Eligible[:\s]*([YN]O|YES|NO)', response_text, re.IGNORECASE)
        if transfer_match:
            parsed['transfer_eligible'] = transfer_match.group(1).upper() in ['YES', 'Y']
        
        # Look for transfer reasoning
        reasoning_match = re.search(r'Reasoning:?\s*\n(.*?)(?=\n\n|\nSuggested|$)', response_text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            parsed['transfer_reasoning'] = reasoning_match.group(1).strip()
        
        # Look for suggested transfer goal (4a. TRANSFER GOAL or legacy)
        goal_match = re.search(
            r'(?:##\s*4a\.\s*TRANSFER GOAL|Suggested Transfer Goal)[:\s]*\n(.*?)(?=\n\n---|\n\n##\s*[45]\.|\n\nCUSTOMER|CUSTOMER EMAIL|YOUR RESPONSE|$)', response_text, re.DOTALL | re.IGNORECASE
        )
        if goal_match:
            raw = goal_match.group(1).strip()
            if raw and 'not applicable' not in raw.lower() and 'not transferable' not in raw.lower():
                parsed['suggested_transfer_goal'] = raw
        
        # Look for handling instructions (5. INSTRUCTIONS ON HANDLING CASE or legacy)
        instructions_match = re.search(
            r'(?:##\s*5\.\s*INSTRUCTIONS ON HANDLING CASE|DETAILED HANDLING INSTRUCTIONS|Step \d+:|Handling Instructions)[:\s]*\n(.*?)(?=\n\n---|\n\n##\s*6\.|\n\nCUSTOMER EMAIL RESPONSE|CUSTOMER EMAIL|YOUR RESPONSE TO CUSTOMER|$)', response_text, re.DOTALL | re.IGNORECASE
        )
        if instructions_match:
            parsed['handling_instructions'] = instructions_match.group(2).strip()
        else:
            parts = re.split(r'CUSTOMER EMAIL RESPONSE|Customer Email Response|YOUR RESPONSE TO CUSTOMER', response_text, flags=re.IGNORECASE)
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
            # Pattern 1: Look for "## 6. YOUR RESPONSE TO CUSTOMER" (7-step structure)
            customer_match = re.search(r'##\s*6\.\s*YOUR RESPONSE TO CUSTOMER[:\s]*\n(.*?)(?=\n\n---|\n\n##\s*7\.|$)', response_text, re.DOTALL | re.IGNORECASE)
            if customer_match:
                customer_response = customer_match.group(1).strip()
                if 'NOT APPLICABLE' in customer_response.upper():
                    customer_response = None
            # Pattern 2: Look for "CUSTOMER EMAIL RESPONSE" section (legacy)
            if not customer_response:
                customer_match = re.search(r'CUSTOMER EMAIL RESPONSE[:\s]*\n(.*?)(?=\n\n===|\n\nFULL CURSOR|$)', response_text, re.DOTALL | re.IGNORECASE)
                if customer_match:
                    customer_response = customer_match.group(1).strip()
            # Pattern 3: Look for "3. CUSTOMER EMAIL RESPONSE" (numbered section)
            if not customer_response:
                customer_match = re.search(r'3\.\s*CUSTOMER EMAIL RESPONSE[:\s]*\n(.*?)(?=\n\n===|\n\nFULL CURSOR|$)', response_text, re.DOTALL | re.IGNORECASE)
                if customer_match:
                    customer_response = customer_match.group(1).strip()
            
            # Pattern 4: Look for German email content (starts with "Guten Tag" or similar)
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
            
            # Pattern 5: Fallback - try to find German text at the end (likely the customer response)
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

            # Hard anti-fusion sanitizer: keep only one bounded customer reply block.
            customer_response = self._sanitize_single_customer_reply_block(customer_response)

            # Final hard block for merged responses.
            sal_count = len(re.findall(r'(?im)^\s*guten tag\b', customer_response))
            sig_count = len(re.findall(r'(?im)^\s*freundliche grüße\b', customer_response))
            survey_count = len(re.findall(r'(?i)zur verbesserung unseres kundenservices', customer_response))
            if sal_count > 1 or sig_count > 1 or survey_count > 1:
                logger.error(
                    "CRITICAL: Parsed customer response still appears merged "
                    f"(salutations={sal_count}, signatures={sig_count}, survey={survey_count}). Blocking paste content."
                )
                parsed['customer_response'] = ''
                return parsed

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

    def _sanitize_single_customer_reply_block(self, text: str) -> str:
        """
        Reduce parsed text to one customer reply block to prevent merged multi-case output.
        """
        t = (text or "").strip()
        if not t:
            return t

        # Start at first salutation if present.
        sal_matches = list(re.finditer(r'(?im)^\s*guten tag\b', t))
        if sal_matches:
            t = t[sal_matches[0].start():].strip()
            sal_matches = list(re.finditer(r'(?im)^\s*guten tag\b', t))
            if len(sal_matches) > 1:
                t = t[:sal_matches[1].start()].strip()

        # Keep only first survey block occurrence.
        survey_matches = list(re.finditer(r'(?i)zur verbesserung unseres kundenservices', t))
        if len(survey_matches) > 1:
            t = t[:survey_matches[1].start()].strip()

        # Keep only first signature block occurrence.
        sig_matches = list(re.finditer(r'(?im)^\s*freundliche grüße\b', t))
        if len(sig_matches) > 1:
            t = t[:sig_matches[1].start()].strip()

        # If fixed footer exists, cut at first footer end to avoid trailing appended blocks.
        foot = re.search(r'(?i)\* gemäß tarif für anrufe in das dt\. fest- bzw\. mobilfunknetz', t)
        if foot:
            t = t[:foot.end()].strip()

        return t
    
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

    def _write_latest_re_reply_record(self, case_id: str, customer_response: str) -> None:
        """
        Persist the exact response shown in RE so PR can paste the same text for the same case.
        """
        try:
            text = (customer_response or "").strip()
            if not text:
                return
            payload = {
                "case_id": (case_id or "").strip(),
                "response_text": text,
                "saved_at": int(time.time()),
            }
            LATEST_RE_REPLY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LATEST_RE_REPLY_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved latest RE reply record for case {case_id} at {LATEST_RE_REPLY_PATH}")
        except Exception as e:
            logger.warning(f"Could not save latest RE reply record: {e}")

    def _write_latest_user_directed_reply_record(self, case_id: str, customer_response: str) -> None:
        """
        Persist explicit user-directed override reply for the same visible case.
        """
        try:
            text = (customer_response or "").strip()
            if not text:
                return
            payload = {
                "case_id": (case_id or "").strip(),
                "response_text": text,
                "saved_at": int(time.time()),
            }
            LATEST_USER_DIRECTED_REPLY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LATEST_USER_DIRECTED_REPLY_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved latest user-directed reply record for case {case_id} at {LATEST_USER_DIRECTED_REPLY_PATH}")
        except Exception as e:
            logger.warning(f"Could not save latest user-directed reply record: {e}")
    
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

    def _normalize_text(self, text: str) -> str:
        """Normalize text for reliable comparisons."""
        if not text:
            return ""
        out = text.replace('\r\n', '\n').replace('\r', '\n')
        out = re.sub(r'[ \t]+', ' ', out)
        out = re.sub(r'\n{3,}', '\n\n', out)
        return out.strip()

    def _validate_single_reply_text(self, text: str) -> List[str]:
        """
        Validate that reply text is a single response block and not merged.
        Returns a list of validation errors (empty if valid).
        """
        errors: List[str] = []
        raw = text or ""
        lowered = raw.lower()
        salutation_count = len(re.findall(r'(?im)^\s*guten tag\b', raw))
        survey_count = lowered.count("zur verbesserung unseres kundenservices")
        signature_count = lowered.count("freundliche grüße")
        agent_name_count = lowered.count("ihr o2 kundenbetreuer")

        if salutation_count != 1:
            errors.append(f"Expected exactly 1 salutation, found {salutation_count}")
        if survey_count != 1:
            errors.append(f"Expected exactly 1 survey line, found {survey_count}")
        if signature_count != 1:
            errors.append(f"Expected exactly 1 signature header, found {signature_count}")
        if agent_name_count != 1:
            errors.append(f"Expected exactly 1 agent signature marker, found {agent_name_count}")

        # Detect duplicated paragraph blocks (very common when previous case reply is concatenated)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', raw) if p.strip()]
        seen = set()
        for p in paragraphs:
            key = re.sub(r'\s+', ' ', p.lower())
            if len(key) < 30:
                continue
            if key in seen:
                errors.append("Detected duplicated paragraph block")
                break
            seen.add(key)
        return errors

    def _get_editor_plain_text(self) -> str:
        """Read current TinyMCE editor text from the visible reply section (same editor as write)."""
        try:
            text = self.page.evaluate(
                """() => {
                    const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
                    if (!section) return '';
                    const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
                    const iframe = base.querySelector('iframe[id$="_ifr"]')
                        || base.querySelector('iframe')
                        || section.querySelector('iframe[id$="_ifr"]')
                        || section.querySelector('iframe');

                    // Prefer the TinyMCE instance bound to the reply iframe (never editors[0]).
                    try {
                        if (window.tinymce && iframe) {
                            const rawId = (iframe.id || '').replace(/_ifr$/, '');
                            let editor = (rawId && window.tinymce.get) ? window.tinymce.get(rawId) : null;
                            if (!editor && window.tinymce.editors) {
                                for (const ed of window.tinymce.editors) {
                                    try {
                                        const el = ed.getElement && ed.getElement();
                                        const edIframe = ed.iframeElement || (el && el.querySelector && el.querySelector('iframe'));
                                        if (edIframe === iframe || (ed.id && iframe.id && iframe.id.indexOf(ed.id) === 0)) {
                                            editor = ed;
                                            break;
                                        }
                                    } catch (e) {}
                                }
                            }
                            if (editor) {
                                return (editor.getContent({ format: 'text' }) || '').trim();
                            }
                        }
                    } catch (e) {}

                    if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
                        return (iframe.contentDocument.body.innerText || '').trim();
                    }
                    return '';
                }"""
            )
            return self._normalize_text(text or "")
        except Exception:
            return ""

    def _get_visible_sender_text(self) -> str:
        """Read visible sender text ('Von:') from current open case."""
        try:
            txt = self.page.evaluate(
                """() => {
                    const inbound = document.querySelector('[data-testid="inboundChatConversationItemFanMessage"]:last-child')
                        || document.querySelector('[data-testid="inboundChatConversationItemFanMessage"]');
                    if (!inbound) return '';
                    const labels = inbound.querySelectorAll('span[data-testid="label"]');
                    let vonParent = null;
                    for (const l of labels) {
                        const t = (l.innerText || '').trim().toLowerCase();
                        if (t === 'von:' || t === 'von') { vonParent = l.parentElement; break; }
                    }
                    if (!vonParent) return '';
                    const value = vonParent.querySelector('span[data-spaceweb="typography-l2"]');
                    return value ? (value.innerText || '').trim() : '';
                }"""
            )
            return (txt or "").strip()
        except Exception:
            return ""

    def _has_verifiable_visible_customer_name(self) -> bool:
        """
        Conservative check: only return True when a plausible person name is visible.
        If uncertain, returns False (fail-safe).
        """
        sender = self._get_visible_sender_text()
        if not sender:
            return False
        s = re.sub(r'<[^>]*>', ' ', sender).strip()
        if '@' in s:
            return False
        if re.search(r'\d', s):
            return False
        tokens = [t for t in re.split(r'[\s,;:/]+', s) if t]
        alpha_tokens = [t for t in tokens if re.search(r'[A-Za-zÄÖÜäöüß]', t)]
        return len(alpha_tokens) >= 2

    def _force_neutral_salutation_if_name_unverified(self, text: str) -> str:
        """
        If visible case does not show a verifiable customer name, force 'Guten Tag,'.
        Prevents leaking stale names from prior cases.
        """
        if self._has_verifiable_visible_customer_name():
            return text
        normalized = text or ""
        out = re.sub(r'(?im)^\s*Guten Tag\s+[^,\n]+,\s*$', 'Guten Tag,', normalized, count=1)
        if out != normalized:
            logger.warning("Named salutation replaced with neutral salutation (no visible customer name).")
            print("[EDITOR] WARNING: No visible customer name verified. Forced salutation to 'Guten Tag,'.")
        return out

    def _clear_editor_hard(self) -> None:
        """Hard-clear TinyMCE/editor content using multiple DOM paths."""
        self.page.evaluate(
            """() => {
                try {
                    if (window.tinymce && window.tinymce.editors) {
                        for (const ed of window.tinymce.editors) {
                            try { ed.setContent(''); ed.fire('input'); ed.fire('change'); } catch (e) {}
                        }
                    }
                } catch (e) {}
                const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
                if (section) {
                    const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
                    const iframe = base.querySelector('iframe[id$="_ifr"]') || base.querySelector('iframe') || section.querySelector('iframe[id$="_ifr"]') || section.querySelector('iframe');
                    if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
                        iframe.contentDocument.body.innerHTML = '';
                        iframe.contentDocument.body.innerText = '';
                    }
                }
            }"""
        )

    def _editor_is_effectively_empty(self) -> bool:
        """Treat whitespace-only editor as empty."""
        actual = self._normalize_text(self._get_editor_plain_text() or "")
        return len(actual.strip()) == 0

    def _check_and_record_pr_write_lock(self, case_id: str, response_text: str) -> bool:
        """
        Cross-process guard: prevent near-immediate duplicate write invocations
        that can stack content from repeated PR triggers.
        """
        try:
            lock_dir = Path(".cursor") / "tmp"
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_file = lock_dir / "last_pr_write_lock.json"
            digest = hashlib.sha256((response_text or "").encode("utf-8", errors="replace")).hexdigest()
            now = time.time()
            payload = {
                "case_id": (case_id or "").strip(),
                "digest": digest,
                "ts": now,
            }
            if lock_file.exists():
                prev = json.loads(lock_file.read_text(encoding="utf-8"))
                prev_case = str(prev.get("case_id", "")).strip()
                prev_digest = str(prev.get("digest", "")).strip()
                prev_ts = float(prev.get("ts", 0) or 0)
                if prev_case == payload["case_id"] and prev_digest == digest and (now - prev_ts) < 60:
                    logger.error("Cross-process duplicate PR write blocked by lock file")
                    print("[EDITOR] ERROR: Duplicate PR invocation blocked (same case/reply in <60s).")
                    return False
            lock_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"PR write lock check failed open: {e}")
            return True

    def _assert_editor_content(self, expected_text: str) -> bool:
        """
        Post-write guard:
        - ensure editor has a single reply structure
        - ensure expected body (not just salutation) made it into the visible reply editor
        - reject Sprinklr placeholder stubs like [Antwort]
        """
        actual = self._get_editor_plain_text()
        expected = self._normalize_text(expected_text)
        if not actual:
            logger.error("Editor readback is empty after write")
            return False

        actual_l = actual.lower()
        expected_lines = [ln.strip() for ln in expected.split("\n") if ln.strip()]
        # Prefer a distinctive body line (skip salutation / short lines).
        body_probes = [
            ln for ln in expected_lines
            if len(ln) >= 40 and not ln.lower().startswith("guten tag")
        ]
        probes = body_probes[:3] if body_probes else expected_lines[:2]
        if not probes:
            logger.error("No expected probe lines available for editor readback")
            return False
        matched = sum(1 for p in probes if p in actual)

        # Stub check: only fail when placeholder remains AND expected body is missing.
        # (Avoid treating legitimate German word "Antwort" or partial UI chrome as a hard fail
        # when the drafted reply body is clearly present.)
        has_stub = ("[antwort]" in actual_l) or ("%%[author_user_name" in actual_l)
        if has_stub and matched < 1:
            logger.error("Editor still contains placeholder stub ([Antwort] / author template)")
            print("[EDITOR] ERROR: Editor still shows [Antwort] stub — write targeted wrong/empty editor.")
            return False

        validation_errors = self._validate_single_reply_text(actual)
        if validation_errors:
            logger.error(f"Editor content validation failed: {validation_errors}")
            return False

        if matched < 1:
            logger.error("Editor readback does not include expected body content")
            print("[EDITOR] ERROR: Visible editor content does not match drafted reply body.")
            return False

        # Length sanity: stub replies are ~800 chars; real replies are usually longer.
        if len(expected) > 900 and len(actual) < max(500, int(len(expected) * 0.45)):
            logger.error(
                f"Editor readback too short ({len(actual)} chars) vs expected ({len(expected)} chars)"
            )
            print("[EDITOR] ERROR: Editor content length mismatch after paste.")
            return False
        return True

    def _write_via_reply_section_tinymce(self, html_content: str) -> dict:
        """
        Write HTML into the TinyMCE instance bound to section 'Nachricht verfassen'.
        Avoids tinymce.editors[0], which can be a hidden/non-reply editor.
        """
        return self.page.evaluate(
            """(content) => {
                const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
                if (!section) return { success: false, error: 'reply section not found' };
                const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
                const iframe = base.querySelector('iframe[id$="_ifr"]')
                    || base.querySelector('iframe')
                    || section.querySelector('iframe[id$="_ifr"]')
                    || section.querySelector('iframe');
                if (!iframe) return { success: false, error: 'reply iframe not found' };

                let editor = null;
                try {
                    if (window.tinymce) {
                        const rawId = (iframe.id || '').replace(/_ifr$/, '');
                        if (rawId && window.tinymce.get) editor = window.tinymce.get(rawId);
                        if (!editor && window.tinymce.editors) {
                            for (const ed of window.tinymce.editors) {
                                try {
                                    const el = ed.getElement && ed.getElement();
                                    const edIframe = ed.iframeElement || (el && el.querySelector && el.querySelector('iframe'));
                                    if (edIframe === iframe || (ed.id && iframe.id && iframe.id.indexOf(ed.id) === 0)) {
                                        editor = ed;
                                        break;
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                } catch (e) {}

                try {
                    if (editor) {
                        editor.focus();
                        editor.setContent('');
                        editor.setContent(content);
                        try { editor.undoManager && editor.undoManager.clear && editor.undoManager.clear(); } catch (e) {}
                        try { editor.fire('input'); editor.fire('change'); editor.fire('keyup'); } catch (e) {}
                        // Keep iframe DOM in sync for readback paths that use contentDocument.
                        try {
                            const doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
                            if (doc && doc.body) {
                                doc.body.innerHTML = editor.getContent({ format: 'html' }) || content;
                            }
                        } catch (e) {}
                        const text = (editor.getContent({ format: 'text' }) || '').trim();
                        if (!text || text.length < 20 || /\\[Antwort\\]/i.test(text)) {
                            return { success: false, error: 'tinymce setContent did not stick (stub/empty)' };
                        }
                        return { success: true, method: 'tinymce_reply_section', editorId: editor.id || '', textLen: text.length, textProbe: text.slice(0, 80) };
                    }
                } catch (e) {
                    return { success: false, error: 'tinymce setContent failed: ' + e.message };
                }

                // Fallback: write directly into iframe body and sync if possible
                try {
                    const doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
                    if (!doc || !doc.body) return { success: false, error: 'iframe document unavailable' };
                    doc.body.innerHTML = content;
                    doc.body.dispatchEvent(new Event('input', { bubbles: true }));
                    doc.body.dispatchEvent(new Event('change', { bubbles: true }));
                    const text = (doc.body.innerText || '').trim();
                    return { success: true, method: 'iframe_body_fallback', editorId: iframe.id || '', textLen: text.length, textProbe: text.slice(0, 80) };
                } catch (e) {
                    return { success: false, error: 'iframe body write failed: ' + e.message };
                }
            }""",
            html_content,
        )
    
    def write_response_to_editor(self, response_text: str, expected_case_id: str = ""):
        """
        Write the response text to the TinyMCE email composition editor
        Clears existing content before writing new content
        
        Args:
            response_text: The response text to write (should be clean German email body only)
        """
        logger.info("Writing response to email editor...")
        print("[EDITOR] Writing response to TinyMCE editor...")

        # Absolute one-shot guard against duplicate pastes within same script execution.
        if self._reply_write_invoked:
            logger.error("Second write attempt blocked by one-shot guard.")
            print("[EDITOR] ERROR: Second paste attempt blocked. Script is single-shot and will not repaste.")
            return
        self._reply_write_invoked = True
        
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

        # Sanitize here as well (write path may receive contaminated multi-reply text from file/chat).
        sanitized = self._sanitize_single_customer_reply_block(response_text)
        if sanitized != response_text:
            logger.warning(
                f"Write-time sanitizer trimmed reply from {len(response_text)} to {len(sanitized)} chars"
            )
            print("[EDITOR] WARNING: Detected merged content in draft; auto-trimmed to first single reply block.")
        response_text = sanitized
        response_text = self._force_neutral_salutation_if_name_unverified(response_text)

        # Pre-write validation: fail closed on any multi-reply/merged signal.
        pre_write_errors = self._validate_single_reply_text(response_text)
        if pre_write_errors:
            logger.error(f"Single-response validation failed before write: {pre_write_errors}")
            print("[EDITOR] ERROR: Reply failed strict single-response checks. Paste blocked to prevent data leak.")
            for err in pre_write_errors:
                print(f"[EDITOR] - {err}")
            return

        # Cross-process duplicate invocation guard (same case + same body in short window).
        if not self._check_and_record_pr_write_lock(expected_case_id, response_text):
            return
        
        logger.info(f"Writing cleaned response to editor ({len(response_text)} chars)")
        print(f"[EDITOR] Writing cleaned German email body ({len(response_text)} characters) to editor...")
        
        # Ensure we're on email content page (where the editor is)
        if not self.ensure_email_content_page():
            logger.error("Cannot write response - not on email content page")
            print("[EDITOR] ERROR: Not on email content page")
            return

        # Hard pre-clear and verify editor is truly empty before writing.
        try:
            self._clear_editor_hard()
            time.sleep(0.25)
            if not self._editor_is_effectively_empty():
                self._clear_editor_hard()
                time.sleep(0.25)
                if not self._editor_is_effectively_empty():
                    logger.error("Editor is not empty after hard clear. Blocking write to prevent fusion.")
                    print("[EDITOR] ERROR: Editor clear failed (content remains). Blocking paste to prevent data fusion.")
                    return
        except Exception as e:
            logger.debug(f"Pre-clear before write failed: {e}")
        
        # Wait for the reply section and editor to be in DOM (TinyMCE may have visibility:hidden initially)
        time.sleep(1)
        
        try:
            editor_found = False
            html_content = self._text_to_html(response_text)

            # Make reply TinyMCE visible if Sprinklr hid it
            try:
                self.page.evaluate('''() => {
                    const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
                    if (section) {
                        const tox = section.querySelector('.tox-tinymce');
                        if (tox && tox.style) tox.style.visibility = 'visible';
                        try { section.scrollIntoView({ block: 'center' }); } catch (e) {}
                        const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
                        const iframe = base.querySelector('iframe[id$="_ifr"]') || base.querySelector('iframe');
                        if (iframe) {
                            try { iframe.click(); } catch (e) {}
                        }
                    }
                }''')
                time.sleep(0.3)
            except Exception:
                pass

            # Method 0 (preferred): TinyMCE bound to section "Nachricht verfassen" — never editors[0]
            try:
                logger.info("Attempting reply-section TinyMCE write...")
                result = self._write_via_reply_section_tinymce(html_content)
                if result and result.get("success"):
                    editor_found = True
                    logger.info(
                        f"Response written via {result.get('method')} id={result.get('editorId')} len={result.get('textLen')}"
                    )
                    print(
                        f"[EDITOR] Successfully wrote response (reply-section TinyMCE / {result.get('method')})"
                    )
                else:
                    err = (result or {}).get("error", "unknown")
                    logger.warning(f"Reply-section TinyMCE write failed: {err}")
                    print(f"[EDITOR] Reply-section TinyMCE write failed: {err}")
            except Exception as e:
                logger.debug(f"Reply-section TinyMCE method failed: {e}")
                print(f"[EDITOR] Reply section method: {e}")
            
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
                return

            # Post-write readback assertion to prevent silent wrong-editor / stub paste.
            time.sleep(0.5)
            if not self._assert_editor_content(response_text):
                logger.error("Post-write verification failed after single paste. Blocking further automation.")
                print("[EDITOR] ERROR: Verification failed after single paste. No auto-repaste will be attempted.")
                try:
                    self._clear_editor_hard()
                    print("[EDITOR] Editor cleared after failed verification.")
                except Exception as clear_err:
                    logger.warning(f"Post-fail clear failed: {clear_err}")
                return
                
        except Exception as e:
            logger.error(f"Error writing response to editor: {e}")
            print(f"[EDITOR] ERROR: {e}")
            import traceback
            traceback.print_exc()

    def _case_tracker_module(self):
        """Lazy-load Roberta Case Tracker helpers from fill-microsoft-form skill."""
        import importlib.util
        path = _script_dir.parent / "fill-microsoft-form" / "fill_case_tracker.py"
        spec = importlib.util.spec_from_file_location("fill_case_tracker", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load Case Tracker module from {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def open_case_tracker_tab(self) -> None:
        """
        Open Roberta Case Tracker in a new tab from the current Sprinklr context.
        Reuses an existing tracker tab when present. Returns focus to Sprinklr.
        """
        ct = self._case_tracker_module()
        ctx = self.page.context
        tracker = ct.open_or_reuse_case_tracker_tab(
            ctx, self.config, bring_sprinklr_back=self.page
        )
        logger.info(f"Case Tracker tab ready: {tracker.url}")
        print(f"[CASE TRACKER] Tab ready: {tracker.url}")

    def fill_case_tracker_form(self, case_id: str) -> None:
        """
        Open Roberta Case Tracker, fill Case # + E-Mail Care + defaults,
        and leave Speichern to the agent unless auto-submit is added later.
        """
        try:
            ct = self._case_tracker_module()
            ctx = self.page.context
            salcus = ""
            transfer_flag = None
            transfer_target = None
            try:
                case_info = ct.extract_case_info_from_sprinklr(self.page)
                salcus = ct.extract_salcus_from_sprinklr(self.page, case_info)
                transfer_flag, transfer_target = ct.resolve_transfer(case_info)
            except Exception as e:
                logger.debug(f"Case tracker field extraction skipped: {e}")
            tracker = ct.open_or_reuse_case_tracker_tab(
                ctx, self.config, bring_sprinklr_back=None
            )
            ct.fill_case_tracker_fields(
                tracker,
                case_id,
                salcus=salcus,
                transfer=transfer_flag,
                transfer_target=transfer_target,
                submit=False,
            )
            try:
                self.page.bring_to_front()
            except Exception:
                pass
            logger.info("Case tracker form filled (not submitted)")
            print("[FORM] Case tracker filled in Roberta tab. Click Speichern after sending the email.")
        except Exception as e:
            logger.warning(f"Case tracker form fill failed: {e}")
            print(f"[FORM] Could not fill case tracker form: {e}", file=sys.stderr)

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
                self._write_latest_re_reply_record(case_id, cursor_response.get('customer_response', ''))
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
                self._write_latest_re_reply_record(case_id, cursor_response['customer_response'])
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
                
                self.write_response_to_editor(cursor_response['customer_response'], expected_case_id=case_id)
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
    
    # Selectors for "Case abschließen" + "Anwenden" flow (close case → trigger next-email detection)
    _SELECTOR_CASE_ABSCHLIESSEN = 'button[data-entityid="@sprinklr/action/ApplyMacroWithId"]:has-text("Case abschließen"), button:has-text("Case abschließen")'
    _SELECTOR_ANWENDEN = 'button[data-action-id="validateMacro"]:has-text("Anwenden"), button[data-action-id="validateMacro"], button:has-text("Anwenden")'
    # Universal Case macro Apply (Anwenden) — click-gated auto-RE
    _SELECTOR_ANWENDEN_UNIVERSAL = (
        'button[data-action-id="validateMacro"]'
        '[data-tracker-event-id="@macro/editableMacroBox/UNIVERSAL_CASE"]'
    )
    _COLLAPSED_CASE_ITEM_SELECTOR = 'button[data-testid="collapsed-case-item"]'
    _ANWENDEN_RE_WAIT_SECONDS = 4
    _WAIT_ANWENDEN_CLICK_JS = """
() => {
  if (window.__anwendenReArmed) return true;
  const cleanup = () => {
    if (window.__anwendenReClickHandler) {
      document.removeEventListener('mousedown', window.__anwendenReClickHandler, true);
      document.removeEventListener('click', window.__anwendenReClickHandler, true);
      window.__anwendenReClickHandler = null;
    }
  };
  const handler = (e) => {
    if (typeof e.button === 'number' && e.button !== 0) return;
    const btn = e.target.closest('button[data-action-id="validateMacro"]');
    if (!btn) return;
    const tracker = btn.getAttribute('data-tracker-event-id') || '';
    const text = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
    const isUniversal = tracker.indexOf('UNIVERSAL_CASE') !== -1;
    const isAnwenden = /Anwenden/i.test(text);
    if (!isUniversal && !isAnwenden) return;
    window.__anwendenReClickInfo = { tracker: tracker, text: text, isUniversal: isUniversal, at: Date.now() };
    cleanup();
  };
  window.__anwendenReClickHandler = handler;
  window.__anwendenReClickInfo = null;
  window.__anwendenReArmed = true;
  document.addEventListener('mousedown', handler, true);
  document.addEventListener('click', handler, true);
  return true;
}
"""
    _POLL_ANWENDEN_CLICK_JS = """
() => {
  const info = window.__anwendenReClickInfo;
  if (!info) return null;
  window.__anwendenReClickInfo = null;
  window.__anwendenReArmed = false;
  return info;
}
"""
    _REMOVE_ANWENDEN_CLICK_JS = """
() => {
  if (window.__anwendenReClickHandler) {
    document.removeEventListener('mousedown', window.__anwendenReClickHandler, true);
    document.removeEventListener('click', window.__anwendenReClickHandler, true);
    window.__anwendenReClickHandler = null;
  }
  window.__anwendenReArmed = false;
  window.__anwendenReClickInfo = null;
}
"""
    # Transfer workflow FINAL confirm only: exact label "Weiter" (step 4/4).
    # Do NOT match Weiterleiten / Weiteleiten (steps 2–3) — those fire too early.
    _WAIT_WEITER_CLICK_JS = """
() => {
  if (window.__weiterReArmed) return true;
  const cleanup = () => {
    if (window.__weiterReClickHandler) {
      document.removeEventListener('mousedown', window.__weiterReClickHandler, true);
      document.removeEventListener('click', window.__weiterReClickHandler, true);
      window.__weiterReClickHandler = null;
    }
  };
  const handler = (e) => {
    if (typeof e.button === 'number' && e.button !== 0) return;
    const btn = e.target.closest(
      'button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]'
    );
    if (!btn) return;
    const tracker = btn.getAttribute('data-tracker-event-id') || '';
    const text = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
    // Exact final step only: "Weiter" — NOT Weiterleiten / Weiteleiten
    if (!/^Weiter$/i.test(text)) return;
    window.__weiterReClickInfo = { tracker: tracker, text: text, at: Date.now() };
    cleanup();
  };
  window.__weiterReClickHandler = handler;
  window.__weiterReClickInfo = null;
  window.__weiterReArmed = true;
  document.addEventListener('mousedown', handler, true);
  document.addEventListener('click', handler, true);
  return true;
}
"""
    _POLL_WEITER_CLICK_JS = """
() => {
  const info = window.__weiterReClickInfo;
  if (!info) return null;
  window.__weiterReClickInfo = null;
  window.__weiterReArmed = false;
  return info;
}
"""
    _REMOVE_WEITER_CLICK_JS = """
() => {
  if (window.__weiterReClickHandler) {
    document.removeEventListener('mousedown', window.__weiterReClickHandler, true);
    document.removeEventListener('click', window.__weiterReClickHandler, true);
    window.__weiterReClickHandler = null;
  }
  window.__weiterReArmed = false;
  window.__weiterReClickInfo = null;
}
"""
    # External email transfer FINAL confirm: exact label "Weiterleiten" (step 2/3).
    # Do NOT match exact "Weiter" (internal path) or "Weiteleiten" (internal typo step).
    _WAIT_EXTERN_WEITERLEITEN_CLICK_JS = """
() => {
  if (window.__externReArmed) return true;
  const cleanup = () => {
    if (window.__externReClickHandler) {
      document.removeEventListener('mousedown', window.__externReClickHandler, true);
      document.removeEventListener('click', window.__externReClickHandler, true);
      window.__externReClickHandler = null;
    }
  };
  const handler = (e) => {
    if (typeof e.button === 'number' && e.button !== 0) return;
    const btn = e.target.closest(
      'button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]'
    );
    if (!btn) return;
    const tracker = btn.getAttribute('data-tracker-event-id') || '';
    const text = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
    // Exact extern confirm only: "Weiterleiten" — NOT Weiter / Weiteleiten
    if (!/^Weiterleiten$/i.test(text)) return;
    window.__externReClickInfo = { tracker: tracker, text: text, at: Date.now() };
    cleanup();
  };
  window.__externReClickHandler = handler;
  window.__externReClickInfo = null;
  window.__externReArmed = true;
  document.addEventListener('mousedown', handler, true);
  document.addEventListener('click', handler, true);
  return true;
}
"""
    _POLL_EXTERN_WEITERLEITEN_CLICK_JS = """
() => {
  const info = window.__externReClickInfo;
  if (!info) return null;
  window.__externReClickInfo = null;
  window.__externReArmed = false;
  return info;
}
"""
    _REMOVE_EXTERN_WEITERLEITEN_CLICK_JS = """
() => {
  if (window.__externReClickHandler) {
    document.removeEventListener('mousedown', window.__externReClickHandler, true);
    document.removeEventListener('click', window.__externReClickHandler, true);
    window.__externReClickHandler = null;
  }
  window.__externReArmed = false;
  window.__externReClickInfo = null;
}
"""
    # Externer Transfer -> Weiterleiten (transfer case → user taken to console/c)
    _SELECTOR_EXTERNER_TRANSFER = 'button[data-entityid="@sprinklr/action/GuidedAction"]:has-text("Externer Transfer"), button:has-text("Externer Transfer")'
    _SELECTOR_WEITERLEITEN = 'button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]:has-text("Weiterleiten"), button:has-text("Weiterleiten")'
    # Internal Transfer -> Weiterleiten -> Weiteleiten (second confirm; typo in UI) → user taken to console/c
    _SELECTOR_WEITELEITEN = 'button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]:has-text("Weiteleiten"), button:has-text("Weiteleiten")'

    def _anwenden_button_visible(self) -> bool:
        """True if the 'Anwenden' button (macro apply) is visible (user has opened Case abschließen dialog)."""
        try:
            btn = self.page.locator(self._SELECTOR_ANWENDEN).first
            return btn.is_visible(timeout=500)
        except Exception:
            return False

    def _case_abschliessen_button_visible(self) -> bool:
        """True if the 'Case abschließen' button is visible."""
        try:
            btn = self.page.locator(self._SELECTOR_CASE_ABSCHLIESSEN).first
            return btn.is_visible(timeout=500)
        except Exception:
            return False

    def _weiterleiten_button_visible(self) -> bool:
        """True if the 'Weiterleiten' button (transfer confirm) is visible (Externer Transfer or internal Transfer flow)."""
        try:
            btn = self.page.locator(self._SELECTOR_WEITERLEITEN).first
            return btn.is_visible(timeout=500)
        except Exception:
            return False

    def _weiteleiten_button_visible(self) -> bool:
        """True if the 'Weiteleiten' button (second confirm in internal Transfer flow) is visible."""
        try:
            btn = self.page.locator(self._SELECTOR_WEITELEITEN).first
            return btn.is_visible(timeout=500)
        except Exception:
            return False

    def wait_for_email_sent(self, case_id: str, max_wait_time: int = 300):
        """
        Wait for the user to send the email or finish the case by monitoring:
        - return to console page (console/c), or
        - page state change away from email content, or
        - user clicks "Case abschließen" then "Anwenden" (close case), or
        - user clicks "Externer Transfer" then "Weiterleiten" (external transfer → console/c), or
        - user clicks "Transfer" then "Weiterleiten" then "Weiteleiten" (internal transfer → console/c).
        
        Args:
            case_id: The case ID of the email being sent
            max_wait_time: Maximum time to wait in seconds (default 5 minutes)
        """
        logger.info(f"Waiting for user to send email with case ID: {case_id}")
        print(f"\n[WAITING] Monitoring for email send / case done... (will wait up to {max_wait_time} seconds)")
        print("[WAITING] Detects: return to console, 'Case abschließen' + 'Anwenden', 'Externer Transfer' + 'Weiterleiten', or 'Transfer' + 'Weiterleiten' + 'Weiteleiten'.")
        
        start_time = time.time()
        check_interval = 2  # Check every 2 seconds
        saw_anwenden_visible = False  # User opened macro dialog (Anwenden was visible)
        saw_weiterleiten_visible = False  # User opened transfer flow (Weiterleiten was visible)
        saw_weiteleiten_visible = False  # User in internal transfer flow (Weiteleiten second confirm)
        
        while time.time() - start_time < max_wait_time:
            try:
                current_state = self._detect_page_state()
                
                # If we're back on console page, the email was sent or case was transferred
                if current_state == 'console':
                    logger.info("Detected return to console page - email sent or case transferred")
                    print("[INFO] Detected return to console page - email sent or case done!")
                    time.sleep(1)  # Give it a moment to ensure we're really on console
                    return True
                
                # Also check if we can still see the email content page
                if current_state != 'email_content':
                    logger.info(f"Page state changed to: {current_state} - email sent or case done")
                    print(f"[INFO] Page state changed - email sent or case done!")
                    time.sleep(1)
                    return True
                
                # Detect "Case abschließen" -> "Anwenden" flow: once Anwenden was visible and then disappears, case is closed
                anwenden_now = self._anwenden_button_visible()
                if anwenden_now:
                    saw_anwenden_visible = True
                if saw_anwenden_visible and not anwenden_now:
                    logger.info("Detected 'Case abschließen' + 'Anwenden' - case closed, triggering next-email detection")
                    print("[INFO] Detected 'Case abschließen' + 'Anwenden' - case closed!")
                    time.sleep(1)
                    return True
                
                # Detect transfer flows: Externer Transfer -> Weiterleiten, or Transfer -> Weiterleiten -> Weiteleiten
                # Once any transfer confirm (Weiterleiten or Weiteleiten) was visible and both are now gone, case was transferred
                weiterleiten_now = self._weiterleiten_button_visible()
                weiteleiten_now = self._weiteleiten_button_visible()
                if weiterleiten_now:
                    saw_weiterleiten_visible = True
                if weiteleiten_now:
                    saw_weiteleiten_visible = True
                if (saw_weiterleiten_visible or saw_weiteleiten_visible) and not weiterleiten_now and not weiteleiten_now:
                    logger.info("Detected transfer flow (Externer or internal Transfer + Weiterleiten/Weiteleiten) - case transferred")
                    print("[INFO] Detected transfer (Externer or Transfer + Weiterleiten/Weiteleiten) - case transferred!")
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

    def _reattach_sprinklr_page_no_steal(self) -> None:
        """Keep self.page on a Sprinklr tab without bring_to_front (do not steal focus)."""
        if not self.browser:
            return
        sprinklr_hosts = (
            "telefonica-germany.sprinklr.com",
            "telefonica-germany-app.sprinklr.com",
            "sprinklr.com",
        )
        pages: list = []
        for ctx in self.browser.contexts:
            try:
                pages.extend(ctx.pages or [])
            except Exception:
                continue
        chosen = None
        for p in pages:
            try:
                u = (p.url or "").lower()
                if u.startswith("devtools://"):
                    continue
                if any(h in u for h in sprinklr_hosts):
                    chosen = p
                    break
            except Exception:
                continue
        if chosen is not None:
            self.page = chosen

    def _wait_for_anwenden_click(self, poll_seconds: float = 0.5) -> Optional[dict]:
        """Arm Anwenden click listener and poll until left-click (survives navigation better than blocking Promise)."""
        self._reattach_sprinklr_page_no_steal()
        try:
            self.page.evaluate(self._REMOVE_ANWENDEN_CLICK_JS)
        except Exception:
            pass
        try:
            self.page.evaluate(self._WAIT_ANWENDEN_CLICK_JS)
        except Exception as e:
            logger.error(f"Could not arm Anwenden click listener: {e}")
            print(f"[ERROR] Could not arm Anwenden click listener: {e}")
            return None

        last_heartbeat = 0.0
        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                # Re-arm if page navigated and lost the listener
                try:
                    armed = self.page.evaluate("() => !!window.__anwendenReArmed")
                    if not armed:
                        self.page.evaluate(self._WAIT_ANWENDEN_CLICK_JS)
                except Exception:
                    time.sleep(poll_seconds)
                    continue
                info = self.page.evaluate(self._POLL_ANWENDEN_CLICK_JS)
                if isinstance(info, dict):
                    return info
                # Also treat Anwenden button disappearing after it was visible as a click signal
                # (macro apply often navigates before our mousedown handler resolves)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.debug(f"Anwenden poll tick: {e}")

            now = time.time()
            if now - last_heartbeat >= 5:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Still waiting for Anwenden left-click… (open case → click Anwenden)")
                last_heartbeat = now
            time.sleep(poll_seconds)

    def _click_first_collapsed_case_item(
        self,
        exclude_fall_digits: Optional[str] = None,
        settle_timeout_s: float = 25.0,
        poll_s: float = 0.75,
    ) -> bool:
        """
        Click the next sidebar collapsed-case-item after Anwenden/Weiter/Extern.

        Skips items whose aria-label still shows the just-closed/transferred Fall #
        (common after Extern Weiterleiten — stale first item is the same case).
        Polls until a different item appears or timeout.
        """
        exclude = self._fall_digits(exclude_fall_digits) if exclude_fall_digits else None
        if exclude is None and exclude_fall_digits:
            exclude = self._fall_digits(str(exclude_fall_digits))
        deadline = time.time() + max(5.0, float(settle_timeout_s))
        last_log = 0.0

        while time.time() < deadline:
            self._reattach_sprinklr_page_no_steal()
            try:
                locs = self.page.locator(self._COLLAPSED_CASE_ITEM_SELECTOR)
                n = locs.count()
            except Exception as e:
                logger.debug(f"collapsed-case-item count: {e}")
                n = 0

            for i in range(n):
                try:
                    loc = locs.nth(i)
                    if not loc.is_visible(timeout=800):
                        continue
                    aria = ""
                    try:
                        aria = loc.get_attribute("aria-label") or ""
                    except Exception:
                        pass
                    item_digits = self._fall_digits(self.extract_case_id(aria) or aria)
                    if exclude and item_digits and item_digits == exclude:
                        now = time.time()
                        if now - last_log >= 3.0:
                            print(
                                f"[INFO] Skipping closed Fall #{exclude} in sidebar "
                                f"(aria-label={aria!r}) — waiting for a different case…",
                                flush=True,
                            )
                            last_log = now
                        continue
                    loc.click(timeout=8000)
                    print("CASE_ITEM_AUTO_CLICKED", flush=True)
                    if aria:
                        print(f"aria-label: {aria}", flush=True)
                    if exclude:
                        print(f"excluded_closed_fall: #{exclude}", flush=True)
                    return True
                except Exception as e:
                    logger.debug(f"collapsed-case-item nth({i}) click try: {e}")
                    continue

            now = time.time()
            if now - last_log >= 3.0:
                print(
                    f"[INFO] Waiting for next collapsed-case-item"
                    + (f" (not Fall #{exclude})" if exclude else "")
                    + "…",
                    flush=True,
                )
                last_log = now
            time.sleep(poll_s)

        print(
            "[ERROR] No next-case collapsed-case-item found"
            + (f" (still only Fall #{exclude}?)" if exclude else "")
            + f" within {settle_timeout_s:.0f}s.",
            flush=True,
        )
        print("ERROR: NEXT CASE NOT OPEN — run run.py --once", flush=True)
        return False

    def _open_next_case_and_extract(
        self,
        *,
        closed_fall: Optional[str],
        delay_s: float,
        mode_label: str,
        extract_done_marker: str,
    ) -> bool:
        """
        Shared post-trigger path: wait → click next case (skip closed Fall) → extract.
        Returns True on successful extract. On failure prints recovery and returns False
        (caller should stop re-arming the same transfer click).
        """
        closed_digits = self._fall_digits(closed_fall)
        print(f"Waiting {delay_s}s before looking for next case...", flush=True)
        if closed_digits:
            print(f"Will skip closed/transferred Fall #{closed_digits} in sidebar.", flush=True)
        time.sleep(delay_s)

        # Extra settle: poll for a different case item (not just first .first)
        if not self._click_first_collapsed_case_item(
            exclude_fall_digits=closed_digits,
            settle_timeout_s=25.0,
        ):
            print(
                f"[ERROR] {mode_label}: next-case click failed. "
                "Do not wait for another transfer click — use run.py --once if case is open.",
                flush=True,
            )
            print("ERROR: NEXT CASE NOT OPEN — run run.py --once", flush=True)
            return False

        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        time.sleep(1.5)

        for attempt in range(1, 4):
            try:
                state = self._detect_page_state()
            except Exception:
                state = "unknown"
            try:
                opened = self._fall_digits(self._get_case_id_from_page_header())
            except Exception:
                opened = None

            if state == "console" or not opened:
                print(
                    f"[WARN] After click: state={state} opened_fall={opened or 'none'} "
                    f"(attempt {attempt}/3) — retrying next-case click…",
                    flush=True,
                )
            elif closed_digits and opened == closed_digits:
                print(
                    f"[WARN] Still on closed Fall #{closed_digits} (attempt {attempt}/3) — "
                    "retrying next-case click…",
                    flush=True,
                )
            else:
                ok = self.process_current_page_once(
                    chat_only=False, extract_only=True, cue_on_extract_start=True
                )
                if ok:
                    # Final guard if header flipped back to closed Fall
                    try:
                        again = self._fall_digits(self._get_case_id_from_page_header())
                    except Exception:
                        again = opened
                    if closed_digits and again and again == closed_digits:
                        print(
                            f"[WARN] Extracted closed Fall #{closed_digits} — not accepting.",
                            flush=True,
                        )
                    else:
                        print(extract_done_marker, flush=True)
                        return True
                print(
                    f"[WARN] Extract after {mode_label} failed (attempt {attempt}/3).",
                    flush=True,
                )

            if attempt < 3:
                time.sleep(2.0)
                self._click_first_collapsed_case_item(
                    exclude_fall_digits=closed_digits,
                    settle_timeout_s=15.0,
                )
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    pass
                time.sleep(1.5)

        print(
            f"[ERROR] Extract after {mode_label} failed. "
            "Stopping arm watch — run run.py --once on the visible case.",
            flush=True,
        )
        print("ERROR: NEXT CASE NOT OPEN — run run.py --once", flush=True)
        return False

    def _cue_armed_re_start_sound(self) -> None:
        """Play Prowler only after armed extract fully finished (CUSTOMER EMAIL + RE_PENDING_SOUND)."""
        try:
            from re_complete_sound import play_re_complete_sound

            if play_re_complete_sound():
                print("ARMED_RE_START_SOUND", flush=True)
        except Exception as e:
            logger.debug(f"Armed RE start sound failed: {e}")
            print(f"[WARN] Armed RE start sound failed: {e}", flush=True)

    def monitor_anwenden_then_open_case_for_re(self, wait_seconds: int | None = None) -> bool:
        """
        Click-gated auto-RE:
        1. Wait for user left-click on Anwenden (validateMacro / UNIVERSAL_CASE)
        2. Wait wait_seconds (default 3)
        3. Click first visible collapsed-case-item
        4. Extract current case (extract-only) for 7-step RE
        """
        delay = self._ANWENDEN_RE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
        logger.info("Starting Anwenden-gated auto-RE (wait=%ss after click)", delay)
        print("\n" + "=" * 80, flush=True)
        print("ANWENDEN -> AUTO-RE ARMED", flush=True)
        print("1. Left-click Anwenden on Sprinklr:", flush=True)
        print('     button[data-action-id="validateMacro"]', flush=True)
        print('     data-tracker-event-id="@macro/editableMacroBox/UNIVERSAL_CASE"', flush=True)
        print(f"2. Script waits {delay}s, then clicks:", flush=True)
        print(f'     {self._COLLAPSED_CASE_ITEM_SELECTOR}', flush=True)
        print("3. Extract email -> agent runs 7-step RE", flush=True)
        print("Ctrl+C to cancel. Manual extract: run.py --once", flush=True)
        print("=" * 80 + "\n", flush=True)
        print("ANWENDEN_RE_ARMED", flush=True)
        closed_fall_remembered: Optional[str] = None

        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                # Remember open Fall while still on case (before Anwenden navigates away)
                try:
                    live = self._get_case_id_from_page_header()
                    if live:
                        closed_fall_remembered = live
                except Exception:
                    pass
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Waiting for Anwenden left-click...", flush=True)
                click_info = self._wait_for_anwenden_click()
                if not click_info:
                    print("[WARN] Anwenden listener could not be armed — retrying in 2s…", flush=True)
                    time.sleep(2)
                    continue

                print("\n" + "=" * 80, flush=True)
                print("ANWENDEN_CLICK_DETECTED", flush=True)
                if click_info.get("tracker"):
                    print(f"tracker: {click_info.get('tracker')}", flush=True)
                if click_info.get("text"):
                    print(f"button text: {click_info.get('text')}", flush=True)
                if closed_fall_remembered:
                    print(f"closed_fall: {closed_fall_remembered}", flush=True)
                print("=" * 80 + "\n", flush=True)

                if self._open_next_case_and_extract(
                    closed_fall=closed_fall_remembered,
                    delay_s=delay,
                    mode_label="Anwenden",
                    extract_done_marker="ANWENDEN_RE_EXTRACT_DONE",
                ):
                    return True
                return False
            except KeyboardInterrupt:
                print("\n[INFO] Anwenden auto-RE stopped by user (Ctrl+C)")
                raise
            except Exception as e:
                logger.error(f"Anwenden auto-RE loop error: {e}")
                print(f"[ERROR] Anwenden auto-RE: {e}", flush=True)
                time.sleep(2)

    def _wait_for_weiter_click(self, poll_seconds: float = 0.5) -> Optional[dict]:
        """Arm Weiter (guidedWorkflow screenButton) click listener and poll until left-click."""
        self._reattach_sprinklr_page_no_steal()
        try:
            self.page.evaluate(self._REMOVE_WEITER_CLICK_JS)
        except Exception:
            pass
        try:
            self.page.evaluate(self._WAIT_WEITER_CLICK_JS)
        except Exception as e:
            logger.error(f"Could not arm Weiter click listener: {e}")
            print(f"[ERROR] Could not arm Weiter click listener: {e}")
            return None

        last_heartbeat = 0.0
        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                try:
                    armed = self.page.evaluate("() => !!window.__weiterReArmed")
                    if not armed:
                        self.page.evaluate(self._WAIT_WEITER_CLICK_JS)
                except Exception:
                    time.sleep(poll_seconds)
                    continue
                info = self.page.evaluate(self._POLL_WEITER_CLICK_JS)
                if isinstance(info, dict):
                    return info
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.debug(f"Weiter poll tick: {e}")

            now = time.time()
            if now - last_heartbeat >= 5:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Still waiting for final Weiter left-click (step 4/4; ignore Weiterleiten/Weiteleiten)...")
                last_heartbeat = now
            time.sleep(poll_seconds)

    def monitor_weiter_then_open_case_for_re(self, wait_seconds: int | None = None) -> bool:
        """
        Transfer-gated auto-RE (LF TR):
        User completes transfer UI clicks 1–3 manually; script reacts only to final "Weiter" (4/4).
        1. Wait for user left-click on exact label Weiter (guidedWorkflow/runner/screenButton)
        2. Wait wait_seconds (default 3)
        3. Click first visible collapsed-case-item
        4. Extract current case (extract-only) for 7-step RE
        """
        delay = self._ANWENDEN_RE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
        logger.info("Starting Weiter-gated auto-RE (wait=%ss after final Weiter)", delay)
        print("\n" + "=" * 80, flush=True)
        print("WEITER -> AUTO-RE ARMED (transfer / LF TR)", flush=True)
        print("You click the transfer path yourself (script ignores steps 1-3):", flush=True)
        print("  1/4 Transfer   (GuidedAction)", flush=True)
        print("  2/4 Weiterleiten", flush=True)
        print("  3/4 Weiteleiten  (UI typo)", flush=True)
        print("  4/4 Weiter       <-- ONLY this click arms the next-case extract", flush=True)
        print("Trigger button:", flush=True)
        print('     button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]', flush=True)
        print('     exact label: Weiter  (NOT Weiterleiten / Weiteleiten)', flush=True)
        print(f"After final Weiter: wait {delay}s, then click:", flush=True)
        print(f'     {self._COLLAPSED_CASE_ITEM_SELECTOR}', flush=True)
        print("Then extract email -> agent runs 7-step RE", flush=True)
        print("Ctrl+C to cancel. Manual extract: run.py --once", flush=True)
        print("=" * 80 + "\n", flush=True)
        print("WEITER_RE_ARMED", flush=True)
        closed_fall_remembered: Optional[str] = None

        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                try:
                    live = self._get_case_id_from_page_header()
                    if live:
                        closed_fall_remembered = live
                except Exception:
                    pass
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Waiting for Weiter left-click...", flush=True)
                click_info = self._wait_for_weiter_click()
                if not click_info:
                    print("[WARN] Weiter listener could not be armed — retrying in 2s…", flush=True)
                    time.sleep(2)
                    continue

                print("\n" + "=" * 80, flush=True)
                print("WEITER_CLICK_DETECTED", flush=True)
                if click_info.get("tracker"):
                    print(f"tracker: {click_info.get('tracker')}", flush=True)
                if click_info.get("text"):
                    print(f"button text: {click_info.get('text')}", flush=True)
                if closed_fall_remembered:
                    print(f"closed_fall: {closed_fall_remembered}", flush=True)
                print("=" * 80 + "\n", flush=True)

                if self._open_next_case_and_extract(
                    closed_fall=closed_fall_remembered,
                    delay_s=delay,
                    mode_label="Weiter",
                    extract_done_marker="WEITER_RE_EXTRACT_DONE",
                ):
                    return True
                return False
            except KeyboardInterrupt:
                print("\n[INFO] Weiter auto-RE stopped by user (Ctrl+C)")
                raise
            except Exception as e:
                logger.error(f"Weiter auto-RE loop error: {e}")
                print(f"[ERROR] Weiter auto-RE: {e}", flush=True)
                time.sleep(2)

    def _wait_for_extern_weiterleiten_click(self, poll_seconds: float = 0.5) -> Optional[dict]:
        """Arm Externer Transfer final Weiterleiten click listener and poll until left-click."""
        self._reattach_sprinklr_page_no_steal()
        try:
            self.page.evaluate(self._REMOVE_EXTERN_WEITERLEITEN_CLICK_JS)
        except Exception:
            pass
        try:
            self.page.evaluate(self._WAIT_EXTERN_WEITERLEITEN_CLICK_JS)
        except Exception as e:
            logger.error(f"Could not arm Extern Weiterleiten click listener: {e}")
            print(f"[ERROR] Could not arm Extern Weiterleiten click listener: {e}")
            return None

        last_heartbeat = 0.0
        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                try:
                    armed = self.page.evaluate("() => !!window.__externReArmed")
                    if not armed:
                        self.page.evaluate(self._WAIT_EXTERN_WEITERLEITEN_CLICK_JS)
                except Exception:
                    time.sleep(poll_seconds)
                    continue
                info = self.page.evaluate(self._POLL_EXTERN_WEITERLEITEN_CLICK_JS)
                if isinstance(info, dict):
                    return info
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.debug(f"Extern Weiterleiten poll tick: {e}")

            now = time.time()
            if now - last_heartbeat >= 5:
                ts = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[{ts}] Still waiting for Extern Weiterleiten left-click "
                    "(step 2/3; ignore Externer Transfer)..."
                )
                last_heartbeat = now
            time.sleep(poll_seconds)

    def monitor_extern_then_open_case_for_re(self, wait_seconds: int | None = None) -> bool:
        """
        External-email transfer-gated auto-RE (LF TR with email target):
        User clicks Externer Transfer manually; script reacts only to final "Weiterleiten" (2/3).
        1. Wait for user left-click on exact label Weiterleiten (guidedWorkflow/runner/screenButton)
        2. Wait wait_seconds (default 3)
        3. Click first visible collapsed-case-item → extract
        """
        delay = self._ANWENDEN_RE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
        logger.info("Starting Extern-gated auto-RE (wait=%ss after Weiterleiten)", delay)
        print("\n" + "=" * 80, flush=True)
        print("EXTERN -> AUTO-RE ARMED (email transfer / LF TR)", flush=True)
        print("You click the external transfer path yourself (script ignores step 1):", flush=True)
        print("  1/3 Externer Transfer   (GuidedAction) — IGNORE", flush=True)
        print("  2/3 Weiterleiten        <-- ONLY this click arms the next-case extract", flush=True)
        print("  3/3 script: wait → collapsed-case-item → extract", flush=True)
        print("Trigger button:", flush=True)
        print('     button[data-tracker-event-id="@guidedWorkflow/runner/screenButton"]', flush=True)
        print('     exact label: Weiterleiten  (NOT Weiter / Weiteleiten)', flush=True)
        print(f"After Weiterleiten: wait {delay}s, then click:", flush=True)
        print(f'     {self._COLLAPSED_CASE_ITEM_SELECTOR}', flush=True)
        print("Then extract email -> agent runs 7-step RE", flush=True)
        print("Ctrl+C to cancel. Manual extract: run.py --once", flush=True)
        print("=" * 80 + "\n", flush=True)
        print("EXTERN_RE_ARMED", flush=True)
        closed_fall_remembered: Optional[str] = None

        while True:
            try:
                self._reattach_sprinklr_page_no_steal()
                # Capture Fall # while case is still open (before Externer Transfer UI)
                try:
                    live = self._get_case_id_from_page_header()
                    if live:
                        closed_fall_remembered = live
                except Exception:
                    pass
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Waiting for Extern Weiterleiten left-click...", flush=True)
                click_info = self._wait_for_extern_weiterleiten_click()
                if not click_info:
                    print("[WARN] Extern listener could not be armed — retrying in 2s…", flush=True)
                    time.sleep(2)
                    continue

                print("\n" + "=" * 80, flush=True)
                print("EXTERN_WEITERLEITEN_CLICK_DETECTED", flush=True)
                if click_info.get("tracker"):
                    print(f"tracker: {click_info.get('tracker')}", flush=True)
                if click_info.get("text"):
                    print(f"button text: {click_info.get('text')}", flush=True)
                if closed_fall_remembered:
                    print(f"closed_fall: {closed_fall_remembered}", flush=True)
                print("=" * 80 + "\n", flush=True)

                if self._open_next_case_and_extract(
                    closed_fall=closed_fall_remembered,
                    delay_s=delay,
                    mode_label="Extern",
                    extract_done_marker="EXTERN_RE_EXTRACT_DONE",
                ):
                    return True
                return False
            except KeyboardInterrupt:
                print("\n[INFO] Extern auto-RE stopped by user (Ctrl+C)")
                raise
            except Exception as e:
                logger.error(f"Extern auto-RE loop error: {e}")
                print(f"[ERROR] Extern auto-RE: {e}", flush=True)
                time.sleep(2)

    def process_current_page_once(
        self,
        chat_only: bool = False,
        extract_only: bool = False,
        cue_on_extract_start: bool = False,
    ) -> bool:
        """
        Process the current page once: if on email content page, extract and optionally reply; if on console, process first visible email. Then exit (no monitoring).
        When extract_only=True: only print the customer email to stdout and exit (no AI, no KB, no suggested reply in script). Cursor then queries KB and writes reply in chat.
        When chat_only=True: extract, query AI, print summary + suggested reply to stdout; do not write to editor.
        When cue_on_extract_start=True (armed Anwenden/Weiter/Extern): play Prowler only after CUSTOMER EMAIL extract is fully printed (not after the 4s wait).
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
        # Fallback: if state detection is wrong but a case header is visible, treat as email content.
        try:
            visible_case_id = self._get_case_id_from_page_header()
            if visible_case_id and current_state != 'email_content':
                logger.info(f"Case header detected ({visible_case_id}) despite state={current_state}; forcing email_content mode.")
                print(f"[INFO] Visible case header detected ({visible_case_id}) — proceeding as open case.")
                current_state = 'email_content'
        except Exception:
            pass
        if current_state == 'email_content':
            try:
                # Case ID is always from the canonical element: h2 > span with #36556980 (never from body/URL)
                case_id = self._get_case_id_from_page_header()
                if not case_id:
                    case_id = self.extract_case_id(self.page.url)
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
                    self._print_customer_email_and_exit(
                        case_id, email_content, cue_on_extract_start=cue_on_extract_start
                    )
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
        # Extract-only on console: strict no-navigation mode.
        # Do NOT open/click any case from the list; require user-visible open case tab.
        if extract_only and current_state == 'console':
            print("[INFO] RE extract-only does not open cases from console list.")
            print("[INFO] Open the intended case (Fall #...) so it is visible, then run RE again.")
            return False
        print("[INFO] Please open an email case (Fall #...) in the browser, then run this skill again.")
        return False

    def _print_customer_email_and_exit(
        self,
        case_id: str,
        email_content: dict,
        cue_on_extract_start: bool = False,
    ) -> None:
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
        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        def _safe_print(s: str) -> str:
            if not isinstance(s, str):
                s = str(s)
            try:
                s.encode(enc)
                return s
            except UnicodeEncodeError:
                return s.encode(enc, errors='replace').decode(enc)
        print("Subject:", _safe_print(email_content.get('subject', 'N/A')))
        print("From:", _safe_print(email_content.get('from', 'N/A')))
        print("-"*40)
        print("Body:")
        body_text = email_content.get('body', '') or ''
        if not isinstance(body_text, str):
            body_text = str(body_text)
        body_text = body_text.strip()
        try:
            print(body_text)
        except UnicodeEncodeError:
            print(_safe_print(body_text))
        print("="*80)
        print("[INFO] Script finished. Cursor: query KnowledgeBase and write the suggested reply in the chat window.")
        print("="*80 + "\n")
        try:
            if str(_script_dir) not in sys.path:
                sys.path.insert(0, str(_script_dir))
            from re_pending_sound import set_re_pending_sound

            set_re_pending_sound(case_id=case_id)
            print("RE_PENDING_SOUND")
        except Exception as e:
            logger.debug(f"RE pending sound flag failed: {e}")

        # Armed auto-RE: cue AFTER extract is fully printed + pending flag set
        # (not after the 4s wait — that was too early when the next case was already visible).
        if cue_on_extract_start:
            self._cue_armed_re_start_sound()
            print("ARMED_EXTRACT_DONE_SOUND", flush=True)

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

                # ALWAYS when on console/c (list URL, not console/c/<id>): monitor and open the new email
                self._ensure_console_list_url()
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
                            # Case ID only from canonical header (h2 > span #36556980)
                            case_id = self._get_case_id_from_page_header() or self.extract_case_id(self.page.url)
                            
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

                    # ALWAYS when on console/c (list URL, NOT console/c/<id>): monitor and open the new email
                    self._ensure_console_list_url()
                    # Get new emails (we're on console list page)
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
    login_then_monitor = '--login-then-monitor' in sys.argv
    if login_then_monitor:
        login_only = True  # do login/status, then fall through to monitor
    process_current_only = '--process-current-only' in sys.argv
    chat_only = '--chat-only' in sys.argv
    extract_only = '--extract-only' in sys.argv
    write_reply_only = '--write-reply-only' in sys.argv
    wait_next_extract_only = '--wait-next-extract-only' in sys.argv
    no_fill_case_tracker = '--no-fill-case-tracker' in sys.argv
    watch_anwenden_re = '--watch-anwenden-re' in sys.argv
    watch_weiter_re = '--watch-weiter-re' in sys.argv
    watch_extern_re = '--watch-extern-re' in sys.argv
    reply_file = _get_arg_value('--reply-file')
    if watch_anwenden_re:
        print("\n" + "=" * 80)
        print("MODE: --watch-anwenden-re (Anwenden click → 4s → open case → extract)")
        print("=" * 80 + "\n")
    if watch_weiter_re:
        print("\n" + "=" * 80)
        print("MODE: --watch-weiter-re (Weiter click → 4s → open case → extract)")
        print("=" * 80 + "\n")
    if watch_extern_re:
        print("\n" + "=" * 80)
        print("MODE: --watch-extern-re (Extern Weiterleiten click → 4s → open case → extract)")
        print("=" * 80 + "\n")
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
        # Anwenden/Weiter/Extern-gated RE also must leave the open case tab alone.
        stop_after_login = bool(login_only and not login_then_monitor)
        automation.connect_to_browser(
            CDP_ENDPOINT,
            leave_page_unchanged=(
                process_current_only
                or write_reply_only
                or watch_anwenden_re
                or watch_weiter_re
                or watch_extern_re
            ),
            stop_after_login=stop_after_login
        )
        
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
            # Case ID only from canonical header element (h2 > span #36556980)
            current_case_id = automation._get_case_id_from_page_header() or automation.extract_case_id(automation.page.url) or ''
            with open(reply_file, 'r', encoding='utf-8') as f:
                reply_text = f.read()

            # Authoritative RE->PR sync (hard gate):
            # PR may paste ONLY the exact latest RE response for the currently visible case.
            try:
                if not current_case_id:
                    print("[ERROR] Could not determine currently visible case ID. PR blocked.", file=sys.stderr)
                    automation.cleanup()
                    sys.exit(1)
                if not LATEST_RE_REPLY_PATH.exists():
                    print("[ERROR] No latest RE reply record found. Run RE for the visible case, then PR.", file=sys.stderr)
                    automation.cleanup()
                    sys.exit(1)

                with open(LATEST_RE_REPLY_PATH, "r", encoding="utf-8") as rf:
                    rec = json.load(rf)
                rec_case_id = str(rec.get("case_id", "")).strip()
                rec_text = str(rec.get("response_text", "")).strip()

                if not rec_case_id or not rec_text:
                    print("[ERROR] Latest RE reply record is incomplete. Run RE again for the visible case.", file=sys.stderr)
                    automation.cleanup()
                    sys.exit(1)

                # Allowed PR payload sources for current visible case:
                # 1) exact latest RE 7-step reply, OR
                # 2) explicit user-directed override already recorded for same case.
                file_text = (reply_text or "").strip()
                user_override_ok = False
                if LATEST_USER_DIRECTED_REPLY_PATH.exists():
                    try:
                        with open(LATEST_USER_DIRECTED_REPLY_PATH, "r", encoding="utf-8") as uf:
                            urec = json.load(uf)
                        u_case_id = str(urec.get("case_id", "")).strip()
                        u_text = str(urec.get("response_text", "")).strip()
                        user_override_ok = (
                            u_case_id == current_case_id and bool(u_text) and file_text == u_text
                        )
                    except Exception:
                        user_override_ok = False

                if rec_case_id != current_case_id and not user_override_ok:
                    print(
                        f"[ERROR] CASE ID MISMATCH: visible case {current_case_id} vs latest RE case {rec_case_id}. "
                        "PR blocked. Run RE for the currently visible case, then PR.",
                        file=sys.stderr,
                    )
                    automation.cleanup()
                    sys.exit(1)
                if file_text == rec_text:
                    print("[INFO] PR source: exact latest RE response for current visible case.")
                    reply_text = rec_text
                elif file_text:
                    # Differing payload is only allowed if it matches a previously recorded
                    # user-directed override for this exact case.
                    try:
                        if not LATEST_USER_DIRECTED_REPLY_PATH.exists():
                            print(
                                "[ERROR] Reply differs from latest RE response and no recorded user-directed override exists for this case. "
                                "PR blocked.",
                                file=sys.stderr,
                            )
                            automation.cleanup()
                            sys.exit(1)
                        with open(LATEST_USER_DIRECTED_REPLY_PATH, "r", encoding="utf-8") as uf:
                            urec = json.load(uf)
                        u_case_id = str(urec.get("case_id", "")).strip()
                        u_text = str(urec.get("response_text", "")).strip()
                        if u_case_id != current_case_id or not u_text or file_text != u_text:
                            print(
                                "[ERROR] Reply differs from latest RE response and does not match the recorded user-directed override "
                                "for the visible case. PR blocked.",
                                file=sys.stderr,
                            )
                            automation.cleanup()
                            sys.exit(1)
                        print("[INFO] PR source: recorded user-directed override for current visible case.")
                        reply_text = u_text
                    except SystemExit:
                        raise
                    except Exception as ue:
                        print(f"[ERROR] Could not validate user-directed override: {ue}", file=sys.stderr)
                        automation.cleanup()
                        sys.exit(1)
                else:
                    print("[ERROR] Empty reply payload. PR blocked.", file=sys.stderr)
                    automation.cleanup()
                    sys.exit(1)
            except Exception as e:
                logger.warning(f"Could not apply latest RE->PR sync record: {e}")
                print(f"[ERROR] Could not apply RE->PR sync: {e}", file=sys.stderr)
                automation.cleanup()
                sys.exit(1)

            automation.write_response_to_editor(reply_text, expected_case_id=current_case_id)
            print("[INFO] Reply written to editor.")

            # NOTE: Do NOT auto-fill the case tracker form or auto-monitor for next email.
            # The user must explicitly request those actions (LF for form, RE for next email).
            # This prevents unwanted automation loops.

            print("[INFO] Reply written to editor. You can now:")
            print("  - Send the email manually in Sprinklr")
            print("  - When ready, use 'LF' to fill the case tracker form")
            print("  - Use 'RE' to read the next email when it arrives")
            automation.cleanup()
            return

        # Wait-next-extract-only (standalone): monitor for the next new email, open it, print email + thread, then exit.
        # This is used after case-tracker form submission (manual by default) to immediately pick up the next case.
        if wait_next_extract_only:
            try:
                automation.ensure_console_page()
                automation.monitor_next_email_extract_only(check_interval=CHECK_INTERVAL)
            finally:
                automation.cleanup()
            return

        # Anwenden-gated auto-RE: wait for Anwenden click → wait 4s → click case item → extract
        # Must run BEFORE any monitor_emails / get_new_emails path.
        if watch_anwenden_re:
            try:
                automation.monitor_anwenden_then_open_case_for_re(wait_seconds=4)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Anwenden-gated RE failed: {e}")
                print(f"\n[ERROR] Anwenden-gated RE failed: {e}")
                print("[INFO] Tip: open the case, show Anwenden, rerun RE — or use: run.py --once")
            finally:
                automation.cleanup()
            return

        # Weiter-gated auto-RE (LF TR internal queue transfer close-out)
        if watch_weiter_re:
            try:
                automation.monitor_weiter_then_open_case_for_re(wait_seconds=4)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Weiter-gated RE failed: {e}")
                print(f"\n[ERROR] Weiter-gated RE failed: {e}")
                print("[INFO] Tip: complete transfer UI, show Weiter, rerun --arm-weiter — or use: run.py --once")
            finally:
                automation.cleanup()
            return

        # Extern-gated auto-RE (LF TR external email transfer close-out)
        if watch_extern_re:
            try:
                automation.monitor_extern_then_open_case_for_re(wait_seconds=4)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Extern-gated RE failed: {e}")
                print(f"\n[ERROR] Extern-gated RE failed: {e}")
                print(
                    "[INFO] Tip: complete Externer Transfer → Weiterleiten, "
                    "rerun --arm-extern — or use: run.py --once"
                )
            finally:
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
        # Go to console list (console/c) and inject in-page script so Chrome auto-opens new cases
        automation._ensure_console_list_url()
        
        login_then_monitor = '--login-then-monitor' in sys.argv
        if login_only and not login_then_monitor:
            logger.info("Login-only mode: exiting after login and status set.")
            print("[INFO] Login and status complete. Exiting (--login-only).")
            try:
                automation.open_case_tracker_tab()
                print("[INFO] Roberta Case Tracker opened in a new tab (Sprinklr tab remains active).")
            except Exception as e:
                logger.warning(f"Could not open Case Tracker tab after login: {e}")
                print(f"[WARN] Case Tracker tab not opened: {e}")
            try:
                if str(_script_dir) not in sys.path:
                    sys.path.insert(0, str(_script_dir))
                from first_re_once import set_first_re_once

                set_first_re_once(source="login")
                print("FIRST_RE_ONCE_PENDING")
                print("[INFO] Next RE will extract the open case (--once), not arm Anwenden.")
            except Exception as e:
                logger.warning(f"Could not set first-RE-once flag: {e}")
                print(f"[WARN] Could not set first-RE-once flag: {e}")
            print("[INFO] Browser is on the console list; in-page script will auto-open new emails when they appear.")
            automation.cleanup()
            return
        
        if login_then_monitor:
            print("[INFO] Login and status complete. Starting email monitoring (Ctrl+C to stop)...")
        # Start monitoring (runs until Ctrl+C)
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
        # Never fall back into continuous monitor_emails for Anwenden-RE / extract-only modes
        if (
            watch_anwenden_re
            or watch_weiter_re
            or watch_extern_re
            or process_current_only
            or write_reply_only
            or extract_only
        ):
            print("[INFO] Stopping (no monitor fallback for RE/extract modes).")
            try:
                automation.cleanup()
            except Exception:
                pass
            sys.exit(1)
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

