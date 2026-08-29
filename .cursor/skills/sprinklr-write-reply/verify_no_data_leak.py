"""
Data Leak Detection Script for Sprinklr Reply Verification

This script runs AFTER the reply has been written to Sprinklr.
It checks the reply box for signs of data leaks:
- Multiple customer names (salutations)
- Multiple signature blocks
- Mixed case IDs / case numbers
- Signs of merged responses

Usage:
  python verify_no_data_leak.py

Requires:
- Chrome with CDP running (port 9222)
- Must be called AFTER reply is written to Sprinklr reply box
"""
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Playwright not installed. Install with: pip install playwright", file=sys.stderr)
    sys.exit(1)


def scan_reply_for_leaks(reply_text: str) -> tuple[bool, list[str]]:
    """
    Scan reply text for signs of data leaks.
    Returns (is_clean, list_of_issues).
    """
    issues = []
    
    # Count salutations (Guten Tag)
    salutation_count = reply_text.count("Guten Tag")
    if salutation_count > 1:
        issues.append("[WARN] Multiple salutations detected ({0}x 'Guten Tag') - possible merged responses".format(salutation_count))
    
    # Count signature blocks
    signature_count = reply_text.count("Freundliche Grüße")
    if signature_count > 1:
        issues.append("[WARN] Multiple signature blocks detected ({0}x 'Freundliche Grüße') - possible merged responses".format(signature_count))
    
    # Count "Ihr o2 Kundenbetreuer"
    betreuer_count = reply_text.count("Ihr o2 Kundenbetreuer")
    if betreuer_count > 1:
        issues.append("[WARN] Multiple agent signatures detected ({0}x) - possible merged responses".format(betreuer_count))
    
    # Count survey lines (Zur Verbesserung unseres Kundenservices)
    survey_count = reply_text.count("Zur Verbesserung unseres Kundenservices")
    if survey_count > 1:
        issues.append("[WARN] Multiple survey lines detected ({0}x) - possible merged responses".format(survey_count))
    
    # Check for Fall # mentions (should not be in customer-facing reply)
    fall_count = reply_text.count("Fall #")
    if fall_count > 0:
        issues.append("[WARN] Case number (Fall #) mentioned in reply - should not expose Fall # to customer")
    
    # Check for multiple "Lukasz Kowalski" names
    lukasz_count = reply_text.count("Lukasz Kowalski")
    if lukasz_count > 1:
        issues.append("[WARN] Multiple agent names detected ({0}x 'Lukasz Kowalski') - possible merged responses".format(lukasz_count))
    
    # Count customer names (rough heuristic - look for multiple "Guten Tag [Name]" patterns)
    # This is harder without full parsing, but we check if there are two different salutation patterns
    lines_with_guten = [line.strip() for line in reply_text.split('\n') if 'Guten Tag' in line]
    if len(lines_with_guten) > 1:
        # Check if they have different names
        names = set()
        for line in lines_with_guten:
            # Extract name after "Guten Tag"
            if "Guten Tag" in line:
                parts = line.split("Guten Tag", 1)
                if len(parts) > 1:
                    name = parts[1].strip().rstrip(',').rstrip('.').strip()
                    if name:
                        names.add(name)
        if len(names) > 1:
            issues.append("[ERROR] Multiple customer names detected: {0} - DATA LEAK DETECTED".format(names))
    
    is_clean = len(issues) == 0
    return is_clean, issues


def main() -> int:
    """
    Connect to Sprinklr via CDP, read the reply box content, scan for leaks.
    """
    CDP_ENDPOINT = "http://127.0.0.1:9222"
    
    print("\n" + "="*80)
    print("[VERIFICATION] DATA LEAK CHECK - Scanning Sprinklr reply box")
    print("="*80 + "\n")
    
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
            except Exception as e:
                print("[ERROR] Cannot connect to Chrome at {0}".format(CDP_ENDPOINT), file=sys.stderr)
                print("[ERROR] Make sure Chrome is running with: chrome --remote-debugging-port=9222", file=sys.stderr)
                return 1
            
            try:
                # Get the Sprinklr tab (first tab that looks like Sprinklr)
                sprinklr_page = None
                for page in browser.contexts[0].pages if browser.contexts else []:
                    url = page.url or ""
                    if "sprinklr" in url.lower():
                        sprinklr_page = page
                        break
                
                if not sprinklr_page:
                    print("[ERROR] Could not find Sprinklr tab in browser", file=sys.stderr)
                    return 1
                
                # Wait for reply box to exist
                print("[SCAN] Waiting for reply box to be visible...")
                reply_box = sprinklr_page.locator("section[aria-label='Nachricht verfassen']").first
                reply_box.wait_for(state="visible", timeout=10000)
                print("[SCAN] Reply box found - OK")
                
                # Try to read the text from TinyMCE editor
                print("[SCAN] Reading reply content from editor...")
                editor_body = sprinklr_page.locator("[data-testid='baseEditorContainer'] iframe").first
                
                reply_text = ""
                try:
                    # Access the iframe content
                    frame = editor_body.content_frame
                    if frame:
                        body_text = frame.locator("body#tinymce").inner_text(timeout=5000)
                        reply_text = body_text
                        print("[SCAN] Read {0} characters from editor - OK".format(len(reply_text)))
                except Exception as e:
                    print("[WARN] Could not read from iframe: {0}".format(e))
                    # Fallback: try to get text from the section itself
                    try:
                        reply_text = reply_box.inner_text(timeout=5000)
                        print("[SCAN] Read {0} characters from section (fallback) - OK".format(len(reply_text)))
                    except Exception as e2:
                        print("[ERROR] Could not read reply box content: {0}".format(e2), file=sys.stderr)
                        return 1
                
                if not reply_text.strip():
                    print("[WARN] Reply box is empty or no text was read", file=sys.stderr)
                    return 1
                
                # Scan for data leaks
                print("\n[LEAK CHECK] Scanning reply for data leaks...\n")
                is_clean, issues = scan_reply_for_leaks(reply_text)
                
                if is_clean:
                    print("[RESULT] CLEAN - No data leaks detected!")
                    print("[RESULT] Reply box contains content for ONE customer only")
                    print("[RESULT] No merged responses detected")
                    print("[RESULT] Safe to proceed")
                    print("\n" + "="*80 + "\n")
                    return 0
                else:
                    print("[RESULT] POTENTIAL DATA LEAK DETECTED:")
                    for issue in issues:
                        print("[RESULT] {0}".format(issue))
                    print("\n[ACTION REQUIRED]")
                    print("[ACTION] 1. DO NOT SEND THIS REPLY")
                    print("[ACTION] 2. Clear the reply box and check which customer this should go to")
                    print("[ACTION] 3. Paste the correct reply for ONE customer only")
                    print("[ACTION] 4. Run this verification script again")
                    print("\n" + "="*80 + "\n")
                    return 1
            
            except Exception as e:
                print("[ERROR] Error during verification: {0}".format(e), file=sys.stderr)
                import traceback
                traceback.print_exc()
                return 1
    
    except Exception as e:
        print("[FATAL] {0}".format(e), file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
