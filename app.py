"""
Appointment Booking Automation System
Web interface for booking appointments
"""

from flask import Flask, render_template, request, jsonify, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time
import random
import logging
import secrets
from datetime import datetime
import os
import socket
from urllib.parse import urlparse


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('booking_automation.log'),
        logging.StreamHandler()
    ]
)


class BookingAutomation:
    """Booking automation handler"""
    
    def __init__(self, headless=False):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.status_updates = []
    
    def log_status(self, message, level="info"):
        """Log status update"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_updates.append({"time": timestamp, "message": message, "level": level})
        if level == "error":
            logging.error(message)
        else:
            logging.info(message)
    
    def random_delay(self, min_seconds, max_seconds):
        """Random delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_type(self, element, text):
        """Type text character by character with random delays to simulate human typing"""
        try:
            # Scroll element into view first
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self.random_delay(0.2, 0.4)
            
            # Wait for element to be visible and enabled
            WebDriverWait(self.driver, 5).until(EC.visibility_of(element))
            
            # Clear the field
            element.clear()
            self.random_delay(0.1, 0.2)
            
            # Type character by character
            for char in text:
                element.send_keys(char)
                # Random delay between keystrokes (0.05-0.3 seconds)
                time.sleep(random.uniform(0.05, 0.3))
        except Exception as e:
            # Fallback: try JavaScript to set value if send_keys fails
            try:
                self.driver.execute_script("arguments[0].value = arguments[1];", element, text)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
            except Exception:
                self.log_status(f"⚠️ Typing failed: {str(e)[:100]}", "warning")
    
    def human_click(self, element):
        """Click element with mouse movement to simulate human behavior"""
        try:
            # First, scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self.random_delay(0.2, 0.5)
            
            # Wait for element to be clickable
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(element))
            
            # Try ActionChains click first
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).pause(random.uniform(0.1, 0.3)).click().perform()
                return True
            except Exception:
                # Try regular click
                try:
                    element.click()
                    return True
                except Exception:
                    # Fallback to JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
        except Exception as e:
            # Last resort: JavaScript click
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", element)
                return True
            except Exception:
                self.log_status(f"⚠️ Click failed: {str(e)[:100]}", "warning")
                return False
    
    def setup_driver(self, use_stealth=True):
        """Initialize WebDriver - can use regular Chrome or undetected-chromedriver
        
        Args:
            use_stealth: If False, uses regular ChromeDriver (more stable for manual login)
        """
        try:
            self.log_status("🔧 Initializing browser (this may take a moment)...")
            
            if not use_stealth:
                # Use regular ChromeDriver for manual login (more stable)
                self.log_status("🔧 Using standard ChromeDriver (stable mode)...")
                from selenium.webdriver.chrome.service import Service as ChromeService
                from webdriver_manager.chrome import ChromeDriverManager
                import os
                
                options = webdriver.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                
                # Essential arguments with better stealth
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--start-maximized')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-web-security')
                options.add_argument('--allow-running-insecure-content')
                options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
                
                # Experimental options to avoid detection
                options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Initialize regular ChromeDriver with proper path
                driver_path = ChromeDriverManager().install()
                self.log_status(f"🔍 Initial driver path: {driver_path}")
                
                # Fix path - webdriver-manager sometimes returns wrong file
                if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
                    self.log_status("⚠️ Incorrect path detected, fixing...")
                    driver_dir = os.path.dirname(driver_path)
                    correct_path = os.path.join(driver_dir, 'chromedriver')
                    if os.path.isfile(correct_path):
                        driver_path = correct_path
                        self.log_status(f"✅ Found correct driver: {driver_path}")
                    else:
                        self.log_status(f"❌ Could not find chromedriver in {driver_dir}", "error")
                
                # Make sure it's executable
                if os.path.isfile(driver_path):
                    try:
                        os.chmod(driver_path, 0o755)
                        self.log_status(f"✅ Set executable permissions")
                    except Exception as e:
                        self.log_status(f"⚠️ Could not set permissions: {e}", "warning")
                
                self.log_status(f"🔧 Using ChromeDriver at: {driver_path}")
                service = ChromeService(driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
                
                # Set page load timeout
                self.driver.set_page_load_timeout(30)
                
                # Execute stealth scripts to avoid detection
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
                })
                self.driver.execute_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en', 'ko']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                """)
                
                self.wait = WebDriverWait(self.driver, 20)
                self.log_status("✅ Browser initialized successfully (standard mode)")
                return True
            
            else:
                # Use undetected-chromedriver for full automation with maximum stealth
                self.log_status("🔧 Using undetected ChromeDriver (maximum stealth mode)...")
                self.log_status("🛡️ Configuring advanced anti-detection measures...")
                
                options = uc.ChromeOptions()
                
                # Essential stealth arguments
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--start-maximized')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-browser-side-navigation')
                options.add_argument('--disable-features=VizDisplayCompositor')
                
                # Stealth user agent
                options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
                
                # Preferences to avoid detection
                prefs = {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                    "profile.default_content_setting_values.notifications": 2,
                }
                options.add_experimental_option("prefs", prefs)
                
                # Initialize undetected-chromedriver (it handles most anti-detection automatically)
                self.log_status("🔄 Launching browser with anti-bot protection...")
                self.driver = uc.Chrome(
                    options=options,
                    version_main=None,
                    use_subprocess=True,
                    headless=self.headless
                )
                
                # Wait for browser to fully load
                self.log_status("⏳ Waiting for browser initialization...")
                time.sleep(6)
                
                # Apply additional JavaScript-based stealth
                self.log_status("🔐 Applying stealth scripts...")
                try:
                    # Comprehensive stealth script to hide automation
                    stealth_js = """
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Mock plugins
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        // Mock languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en', 'ko-KR', 'ko']
                        });
                        
                        // Add chrome object
                        window.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };
                        
                        // Mock permissions
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                        
                        // Hide automation in iframe checks
                        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                            get: function() {
                                return window;
                            }
                        });
                        
                        // Mock battery API
                        Object.defineProperty(navigator, 'getBattery', {
                            value: () => Promise.resolve({
                                charging: true,
                                chargingTime: 0,
                                dischargingTime: Infinity,
                                level: 1
                            })
                        });
                        
                        // Override toString to hide proxy
                        const oldToString = Function.prototype.toString;
                        Function.prototype.toString = function() {
                            if (this === window.navigator.permissions.query) {
                                return 'function query() { [native code] }';
                            }
                            return oldToString.call(this);
                        };
                    """
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': stealth_js
                    })
                    self.log_status("✅ Stealth scripts applied successfully")
                except Exception as e:
                    self.log_status(f"⚠️ Some stealth scripts failed: {str(e)[:50]}", "warning")
                
                # Set timeouts
                try:
                    self.driver.set_page_load_timeout(45)
                    self.driver.implicitly_wait(5)
                except:
                    pass
                
                self.wait = WebDriverWait(self.driver, 20)
                self.log_status("✅ Browser ready with maximum stealth protection")
                self.log_status("🛡️ Bot detection bypass active")
                return True
                
        except Exception as e:
            self.log_status(f"❌ Failed to initialize browser: {str(e)}", "error")
            return False
            return True
        except Exception as e:
            self.log_status(f"❌ Failed to initialize browser: {str(e)}", "error")
            return False
    
    def navigate_to_website(self, url):
        """Navigate to website with human-like behavior to avoid bot detection"""
        try:
            self.log_status(f"🌐 Navigating to {url}")
            self.log_status("🤖 Using human-like navigation to bypass bot detection...")
            
            # First, navigate to a neutral page (Google) to establish a normal browsing session
            self.log_status("🔄 Step 1: Establishing normal browsing session...")
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Perform some human-like actions
            try:
                # Move mouse randomly
                self.driver.execute_script("""
                    window.scrollTo(0, 100);
                """)
                time.sleep(1)
            except:
                pass
            
            # Now navigate to the actual target URL
            self.log_status(f"🔄 Step 2: Navigating to target website...")
            self.driver.get(url)
            
            # Wait longer for page to fully load and for any bot detection to complete
            self.log_status("⏳ Waiting for page to fully load (this may take a moment)...")
            time.sleep(8)  # Longer wait for bot detection to pass
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # Check if we got blocked by bot manager
            if "botmanager.stclab.com" in current_url or "404 Error Page" in page_title:
                self.log_status("⚠️ Bot detection triggered! Attempting recovery...", "warning")
                self.log_status("🔄 Refreshing page to retry...")
                time.sleep(3)
                self.driver.refresh()
                time.sleep(8)
                
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                if "botmanager.stclab.com" in current_url or "404 Error Page" in page_title:
                    self.log_status("⚠️ Still blocked. Trying direct navigation...", "warning")
                    # Try clearing cookies and navigating again
                    self.driver.delete_all_cookies()
                    time.sleep(2)
                    self.driver.get(url)
                    time.sleep(10)
                    
                    current_url = self.driver.current_url
                    page_title = self.driver.title
            
            if page_title:
                self.log_status(f"✅ Page loaded: {page_title}")
                self.log_status(f"📍 Final URL: {current_url}")
                
                if "botmanager.stclab.com" in current_url:
                    self.log_status("❌ Unable to bypass bot detection", "error")
                    self.log_status("💡 The website has strong anti-bot protection", "warning")
                    self.log_status("💡 You may need to manually navigate to the login page", "warning")
                    # Don't return False, let user try manually
                    return True
                
                return True
            else:
                self.log_status(f"⚠️ Page loaded but may be empty", "warning")
                return True
                
        except Exception as e:
            error_msg = str(e)
            
            if "ERR_INTERNET_DISCONNECTED" in error_msg:
                self.log_status(f"❌ No internet connection. Please check your network and try again.", "error")
            elif "ERR_NAME_NOT_RESOLVED" in error_msg:
                self.log_status(f"❌ Cannot find website. Please check the URL is correct.", "error")
            elif "ERR_CONNECTION_REFUSED" in error_msg:
                self.log_status(f"❌ Website refused connection. The site may be down.", "error")
            elif "ERR_CONNECTION_TIMED_OUT" in error_msg:
                self.log_status(f"❌ Connection timed out. Website may be slow or unreachable.", "error")
            else:
                self.log_status(f"❌ Navigation failed: {error_msg[:200]}", "error")
            
            return False
    
    def find_element(self, identifier, by_method="id", timeout=10):
        """Find element with flexible locator strategy"""
        try:
            by_map = {
                "id": By.ID,
                "name": By.NAME,
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "class": By.CLASS_NAME
            }
            
            by = by_map.get(by_method.lower(), By.ID)
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, identifier))
            )
            return element
        except TimeoutException:
            self.log_status(f"⚠️ Element not found: {identifier}", "warning")
            return None
    
    def smart_find_field(self, field_type, timeout=10):
        """Smart field detection - tries multiple common patterns"""
        patterns = {
            'login_id': ['userId', 'username', 'user_id', 'loginId', 'email', 'userid', 'user'],
            'password': ['userPw', 'password', 'passwd', 'pwd', 'pass'],
            'name': ['name', 'fullName', 'userName', 'fullname', 'studentName'],
            'email': ['email', 'emailAddress', 'mail', 'userEmail'],
            'phone': ['phone', 'phoneNumber', 'mobile', 'tel', 'telephone'],
            'passport': ['passportNo', 'passport', 'passportNumber', 'idNumber'],
            'date': ['appointmentDate', 'date', 'bookingDate', 'reservationDate'],
            'time': ['appointmentTime', 'time', 'bookingTime', 'reservationTime'],
            'embassy': ['embassy', 'embassySelect', 'location', 'office'],
            'service': ['serviceType', 'service', 'appointmentType', 'type'],
            'login_button': ['loginBtn', 'login', 'signin', 'submit', 'btnLogin'],
            'submit_button': ['submitBtn', 'submit', 'confirm', 'book', 'btnSubmit', 'reserve']
        }
        
        if field_type not in patterns:
            return None
        
        is_button = field_type in ['login_button', 'submit_button']
        
        # Try by ID first
        for pattern in patterns[field_type]:
            try:
                if is_button:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.ID, pattern))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.ID, pattern))
                    )
                if element:
                    return element
            except:
                pass
        
        # Try by name
        for pattern in patterns[field_type]:
            try:
                if is_button:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.NAME, pattern))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.NAME, pattern))
                    )
                if element:
                    return element
            except:
                pass
        
        # Try by placeholder or label text for input fields
        if not is_button:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, f"//input[contains(@placeholder, '{field_type}')]"))
                )
                if element:
                    return element
            except:
                pass
        
        return None
    
    def smart_find_button(self, button_texts, timeout=10):
        """Find button by text or common patterns"""
        for text in button_texts:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
                )
                if element:
                    return element
            except:
                pass
            
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, f"//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
                )
                if element:
                    return element
            except:
                pass
        
        return None
    
    def fill_field(self, identifier, value, by_method="id"):
        """Fill form field"""
        try:
            element = self.find_element(identifier, by_method)
            if element:
                self.human_type(element, value)
                self.log_status(f"✅ Filled field: {identifier}")
                return True
            return False
        except Exception as e:
            self.log_status(f"❌ Failed to fill {identifier}: {str(e)}", "error")
            return False
    
    def click_element(self, identifier, by_method="id"):
        """Click element"""
        try:
            element = self.find_element(identifier, by_method)
            if element:
                self.human_click(element)
                self.log_status(f"✅ Clicked: {identifier}")
                self.random_delay(0.5, 1.5)
                return True
            return False
        except Exception as e:
            self.log_status(f"❌ Failed to click {identifier}: {str(e)}", "error")
            return False
    
    def select_dropdown(self, identifier, option_text, by_method="id"):
        """Select dropdown option"""
        try:
            element = self.find_element(identifier, by_method)
            if element:
                select = Select(element)
                select.select_by_visible_text(option_text)
                self.log_status(f"✅ Selected '{option_text}' from dropdown")
                return True
            return False
        except Exception as e:
            self.log_status(f"❌ Failed to select from dropdown: {str(e)}", "error")
            return False
    
    def take_screenshot(self, filename=None):
        """Capture screenshot"""
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            filepath = os.path.join('static', 'screenshots', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.driver.save_screenshot(filepath)
            self.log_status(f"📸 Screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.log_status(f"❌ Screenshot failed: {str(e)}", "error")
            return None
    
    def execute_manual_login_booking(self, booking_data):
        """Execute booking with manual login - user logs in, then automation continues"""
        try:
            self.log_status("🚀 Starting booking automation with MANUAL LOGIN")
            self.log_status("="*60)
            
            # Use undetected-chromedriver to bypass bot detection on initial page load
            self.log_status("🔧 Initializing browser for manual login (anti-bot mode)...")
            self.log_status("💡 Using undetected-chromedriver to bypass STCLab Bot Manager...")
            if not self.setup_driver(use_stealth=True):
                return False, "Failed to initialize browser"
            
            if not self.check_internet_connection(booking_data['website_url']):
                return False, "No internet connection. Please check your network."
            
            # Navigate to login page
            self.log_status("🌐 Opening login page...")
            if not self.navigate_to_website(booking_data['website_url']):
                return False, "Failed to load website. Check your connection!"
            
            self.take_screenshot('01_login_page.png')
            self.log_status("✅ Login page loaded")
            
            # WAIT FOR MANUAL LOGIN
            self.log_status("="*60)
            self.log_status("⏸️  MANUAL LOGIN REQUIRED")
            self.log_status("="*60)
            self.log_status("👤 Please LOGIN MANUALLY in the browser window:")
            self.log_status("   1. Enter your username")
            self.log_status("   2. Enter your password")
            self.log_status("   3. Complete any CAPTCHA if present")
            self.log_status("   4. Click the LOGIN button")
            self.log_status("")
            self.log_status("⏳ Waiting 60 seconds for you to complete login...")
            self.log_status("   (The automation will continue automatically)")
            self.log_status("="*60)
            
            # Show browser notification
            notification_script = '''
            // Remove any existing notification
            const existing = document.getElementById('manual-login-notification');
            if (existing) existing.remove();
            
            // Create notification overlay
            const overlay = document.createElement('div');
            overlay.id = 'manual-login-notification';
            overlay.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                z-index: 999999;
                max-width: 400px;
                animation: slideIn 0.5s ease-out;
            `;
            
            overlay.innerHTML = `
                <div style="font-size: 40px; margin-bottom: 15px; text-align: center;">🔐</div>
                <h2 style="margin: 0 0 15px 0; font-size: 24px; text-align: center;">Manual Login Required</h2>
                <div style="font-size: 16px; line-height: 1.6; margin-bottom: 15px;">
                    <p style="margin: 5px 0;">✅ 1. Enter your username</p>
                    <p style="margin: 5px 0;">✅ 2. Enter your password</p>
                    <p style="margin: 5px 0;">✅ 3. Complete CAPTCHA (if any)</p>
                    <p style="margin: 5px 0;">✅ 4. Click LOGIN</p>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 8px; text-align: center; font-size: 14px;">
                    ⏳ Automation will continue in 60s
                </div>
            `;
            
            document.body.appendChild(overlay);
            
            // Add animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(400px); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
            
            // Auto-remove after 60 seconds
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.style.animation = 'slideIn 0.5s ease-out reverse';
                    setTimeout(() => overlay.remove(), 500);
                }
            }, 60000);
            '''
            
            try:
                self.driver.execute_script(notification_script)
            except:
                pass
            
            # Wait for manual login (60 seconds)
            initial_url = self.driver.current_url
            login_complete = False
            
            for i in range(12):  # Check every 5 seconds for 60 seconds
                self.random_delay(4, 6)
                current_url = self.driver.current_url
                
                # Check if URL changed (indicates successful login)
                if current_url != initial_url and 'login' not in current_url.lower():
                    self.log_status("✅ Login detected! URL changed - continuing automation...")
                    login_complete = True
                    break
                
                # Check if page title changed
                try:
                    page_title = self.driver.title
                    if 'login' not in page_title.lower() and page_title:
                        self.log_status("✅ Login detected! Page changed - continuing automation...")
                        login_complete = True
                        break
                except:
                    pass
                
                remaining = 60 - ((i + 1) * 5)
                if remaining > 0:
                    self.log_status(f"⏳ Waiting for login... ({remaining}s remaining)")
            
            # Remove notification
            try:
                self.driver.execute_script('''
                    const overlay = document.getElementById('manual-login-notification');
                    if (overlay) overlay.remove();
                ''')
            except:
                pass
            
            if not login_complete:
                current_url = self.driver.current_url
                if 'login' not in current_url.lower():
                    self.log_status("✅ Assuming login complete - continuing...")
                    login_complete = True
            
            self.take_screenshot('02_after_manual_login.png')
            self.log_status(f"📍 Current URL after login wait: {self.driver.current_url}")
            
            if not login_complete:
                self.log_status("⚠️ Could not confirm login, but continuing anyway...", "warning")
            
            self.log_status("="*60)
            self.log_status("🤖 Starting AUTOMATIC BOOKING...")
            self.log_status("="*60)
            
            # Now continue with automated booking
            return self._continue_booking_after_login(booking_data)
            
        except Exception as e:
            self.log_status(f"❌ Booking failed: {str(e)}", "error")
            self.take_screenshot('error.png')
            return False, str(e)
    
    def _continue_booking_after_login(self, booking_data):
        """Continue booking process after manual login"""
        try:
            self.random_delay(2, 3)
            
            # Take screenshot of current page
            self.take_screenshot('03_booking_page.png')
            current_url = self.driver.current_url
            self.log_status(f"� Current URL: {current_url}")
            page_title = self.driver.title
            self.log_status(f"📄 Page Title: {page_title}")
            
            # Debug: Log all elements on the page
            self.log_status("🔍 DEBUG: Analyzing page structure...")
            try:
                # Check for all buttons
                all_buttons = self.driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit'] | //a[contains(@class, 'btn')]")
                self.log_status(f"🔍 Found {len(all_buttons)} buttons/button-like elements")
                for i, btn in enumerate(all_buttons[:10]):
                    try:
                        btn_text = btn.text or btn.get_attribute('value') or btn.get_attribute('title') or 'No text'
                        btn_id = btn.get_attribute('id') or 'No ID'
                        is_visible = btn.is_displayed()
                        self.log_status(f"  Button {i+1}: '{btn_text[:50]}' | id='{btn_id}' | visible={is_visible}")
                    except:
                        pass
                
                # Check for all select dropdowns
                all_selects = self.driver.find_elements(By.XPATH, "//select")
                self.log_status(f"🔍 Found {len(all_selects)} select dropdowns")
                for i, sel in enumerate(all_selects[:10]):
                    try:
                        sel_name = sel.get_attribute('name') or 'No name'
                        sel_id = sel.get_attribute('id') or 'No ID'
                        is_visible = sel.is_displayed()
                        options_count = len(sel.find_elements(By.TAG_NAME, "option"))
                        self.log_status(f"  Select {i+1}: name='{sel_name}' | id='{sel_id}' | options={options_count} | visible={is_visible}")
                    except:
                        pass
                
                # Check for all input fields
                all_inputs = self.driver.find_elements(By.XPATH, "//input")
                self.log_status(f"🔍 Found {len(all_inputs)} input fields")
                visible_inputs = [inp for inp in all_inputs if inp.is_displayed()]
                self.log_status(f"🔍 {len(visible_inputs)} input fields are visible")
                for i, inp in enumerate(visible_inputs[:15]):
                    try:
                        inp_type = inp.get_attribute('type') or 'text'
                        inp_name = inp.get_attribute('name') or 'No name'
                        inp_id = inp.get_attribute('id') or 'No ID'
                        inp_placeholder = inp.get_attribute('placeholder') or 'No placeholder'
                        self.log_status(f"  Input {i+1}: type='{inp_type}' | name='{inp_name}' | id='{inp_id}' | placeholder='{inp_placeholder[:30]}'")
                    except:
                        pass
                
                # Check for all links with clickable actions
                all_links = self.driver.find_elements(By.XPATH, "//a")
                visible_links = [link for link in all_links if link.is_displayed() and link.text.strip()]
                self.log_status(f"🔍 Found {len(visible_links)} visible links with text")
                for i, link in enumerate(visible_links[:10]):
                    try:
                        link_text = link.text[:50]
                        link_href = link.get_attribute('href') or 'No href'
                        self.log_status(f"  Link {i+1}: '{link_text}' -> {link_href[:60]}")
                    except:
                        pass
                
                # Check for iframes
                iframes = self.driver.find_elements(By.XPATH, "//iframe")
                self.log_status(f"🔍 Found {len(iframes)} iframes on page")
                
            except Exception as e:
                self.log_status(f"🔍 Debug analysis failed: {str(e)[:100]}", "warning")
            
            # Check if we're on the booking page (selectCIPH0801Deng.do)
            if "selectCIPH0801Deng.do" not in current_url:
                self.log_status("⚠️ Not on booking page yet, navigating...")
                self.driver.get("https://www.g4k.go.kr/ciph/0800/selectCIPH0801Deng.do")
                self.random_delay(3, 4)
                self.take_screenshot('04_navigated_booking.png')
                
                # Debug the navigated page too
                current_url = self.driver.current_url
                page_title = self.driver.title
                self.log_status(f"📍 After navigation URL: {current_url}")
                self.log_status(f"📄 After navigation Title: {page_title}")
                
                # Check if we got redirected or blocked
                if "selectCIPH0801Deng.do" not in current_url:
                    self.log_status("⚠️ Navigation may have been blocked or redirected!", "warning")
                    self.log_status("💡 Trying to find booking link on main page instead...")
                    
                    # Try to find and click a booking link on the main page
                    booking_links = [
                        "//a[contains(text(), '예약') or contains(text(), '신청')]",
                        "//a[contains(@href, 'CIPH0801') or contains(@href, 'ciph/0800')]",
                        "//a[contains(text(), 'Civil complaint application')]"
                    ]
                    
                    for link_xpath in booking_links:
                        try:
                            links = self.driver.find_elements(By.XPATH, link_xpath)
                            self.log_status(f"🔍 Found {len(links)} links matching pattern")
                            for link in links:
                                if link.is_displayed():
                                    link_text = link.text[:50]
                                    link_href = link.get_attribute('href') or 'No href'
                                    self.log_status(f"  Found link: '{link_text}' -> {link_href}")
                                    self.log_status(f"🖱️ Clicking link: {link_text}")
                                    link.click()
                                    self.random_delay(2, 3)
                                    self.take_screenshot('05_after_link_click.png')
                                    break
                            if "selectCIPH0801Deng.do" in self.driver.current_url:
                                break
                        except Exception as e:
                            self.log_status(f"🔍 Link search failed: {str(e)[:50]}", "info")
                
                # Debug again after potential link click
                self.log_status("🔍 DEBUG: Analyzing page after navigation/click...")
                try:
                    all_buttons = self.driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']")
                    self.log_status(f"🔍 Found {len(all_buttons)} buttons after navigation")
                    for i, btn in enumerate(all_buttons[:10]):
                        try:
                            btn_text = btn.text or btn.get_attribute('value') or 'No text'
                            is_visible = btn.is_displayed()
                            self.log_status(f"  Button {i+1}: '{btn_text[:50]}' | visible={is_visible}")
                        except:
                            pass
                    
                    all_selects = self.driver.find_elements(By.XPATH, "//select")
                    self.log_status(f"🔍 Found {len(all_selects)} select dropdowns after navigation")
                    for i, sel in enumerate(all_selects[:10]):
                        try:
                            sel_name = sel.get_attribute('name') or 'No name'
                            is_visible = sel.is_displayed()
                            self.log_status(f"  Select {i+1}: name='{sel_name}' | visible={is_visible}")
                        except:
                            pass
                    
                    visible_inputs = [inp for inp in self.driver.find_elements(By.XPATH, "//input") if inp.is_displayed()]
                    self.log_status(f"🔍 Found {len(visible_inputs)} visible inputs after navigation")
                    
                except Exception as e:
                    self.log_status(f"🔍 Post-navigation debug failed: {str(e)[:100]}", "warning")
            
            self.log_status("📋 Starting to fill booking form...")
            self.log_status(f"🏛️ Embassy to select: {booking_data.get('embassy', 'Not specified')}")
            
            # Step 1: Select Diplomatic Mission/Embassy
            self.log_status("🔍 Step 1: Looking for embassy/mission selection...")
            embassy_field = None
            
            # Try multiple selectors for embassy field
            embassy_selectors = [
                ("//select[@name='smMissionCd']", "name='smMissionCd'"),
                ("//select[@id='smMissionCd']", "id='smMissionCd'"),
                ("//select[contains(@name, 'mission')]", "name contains 'mission'"),
                ("//select[contains(@id, 'mission')]", "id contains 'mission'"),
                ("//select[contains(@name, 'embassy')]", "name contains 'embassy'"),
                ("//select", "any select element")
            ]
            
            for selector, description in embassy_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.log_status(f"🔍 Trying {description}: found {len(elements)} elements")
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            embassy_field = elem
                            self.log_status(f"✅ Found embassy field using: {description}")
                            break
                    if embassy_field:
                        break
                except Exception as e:
                    self.log_status(f"🔍 {description} failed: {str(e)[:50]}", "info")
            
            if embassy_field and booking_data.get('embassy'):
                try:
                    select = Select(embassy_field)
                    # Get all options to help user select
                    options = [opt.text for opt in select.options if opt.text.strip()]
                    self.log_status(f"📋 Available embassies: {', '.join(options[:5])}...")
                    
                    # Try to select the embassy
                    select.select_by_visible_text(booking_data['embassy'])
                    self.log_status(f"✅ Embassy '{booking_data['embassy']}' selected successfully")
                    self.random_delay(1.5, 2.5)
                    self.take_screenshot('05_embassy_selected.png')
                except Exception as e:
                    self.log_status(f"⚠️ Embassy selection failed: {str(e)}", "warning")
                    self.log_status("💡 Please select the embassy manually in the browser")
            else:
                self.log_status("⚠️ Embassy field not found - may need manual selection", "warning")
            
            # Step 2: Look for date/time selection
            self.log_status("🔍 Step 2: Looking for date/time selection...")
            self.random_delay(1, 2)
            
            # Try to find date picker or calendar
            date_field = None
            date_selectors = [
                ("//input[@type='date']", "date input"),
                ("//input[contains(@id, 'date')]", "id contains 'date'"),
                ("//input[contains(@name, 'date')]", "name contains 'date'"),
                ("//input[contains(@class, 'datepicker')]", "class contains 'datepicker'"),
                ("//input[contains(@placeholder, '날짜')]", "Korean date placeholder")
            ]
            
            for selector, description in date_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            date_field = elem
                            self.log_status(f"✅ Found date field using: {description}")
                            break
                    if date_field:
                        break
                except Exception as e:
                    pass
            
            if date_field and booking_data.get('appointment_date'):
                try:
                    date_field.click()
                    self.random_delay(0.5, 1)
                    date_field.clear()
                    date_field.send_keys(booking_data['appointment_date'])
                    self.log_status(f"✅ Date entered: {booking_data['appointment_date']}")
                    self.random_delay(1, 2)
                    self.take_screenshot('06_date_selected.png')
                except Exception as e:
                    self.log_status(f"⚠️ Date entry failed: {str(e)}", "warning")
            else:
                self.log_status("💡 Date field not found or date not provided - manual selection may be needed", "info")
            
            # Step 3: Look for time selection
            time_field = None
            time_selectors = [
                ("//select[contains(@name, 'time')]", "name contains 'time'"),
                ("//select[contains(@id, 'time')]", "id contains 'time'"),
                ("//input[@type='time']", "time input"),
                ("//input[contains(@placeholder, '시간')]", "Korean time placeholder")
            ]
            
            for selector, description in time_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            time_field = elem
                            self.log_status(f"✅ Found time field using: {description}")
                            break
                    if time_field:
                        break
                except Exception as e:
                    pass
            
            if time_field and booking_data.get('appointment_time'):
                try:
                    if time_field.tag_name == 'select':
                        select = Select(time_field)
                        select.select_by_visible_text(booking_data['appointment_time'])
                    else:
                        time_field.send_keys(booking_data['appointment_time'])
                    self.log_status(f"✅ Time entered: {booking_data['appointment_time']}")
                    self.random_delay(1, 2)
                    self.take_screenshot('07_time_selected.png')
                except Exception as e:
                    self.log_status(f"⚠️ Time entry failed: {str(e)}", "warning")
            
            # Step 4: Look for submit/confirm/next button
            self.log_status("🔍 Step 4: Looking for submit/confirmation button...")
            submit_button = None
            submit_selectors = [
                ("//button[contains(text(), '신청') or contains(text(), '예약') or contains(text(), '확인')]", "Korean submit button"),
                ("//button[contains(text(), 'Submit') or contains(text(), 'Confirm') or contains(text(), 'Next')]", "English submit button"),
                ("//input[@type='submit']", "submit input"),
                ("//button[@type='submit']", "submit button"),
                ("//a[contains(@class, 'btn') and (contains(text(), '신청') or contains(text(), '예약'))]", "submit link")
            ]
            
            for selector, description in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            submit_button = elem
                            self.log_status(f"✅ Found submit button using: {description}")
                            break
                    if submit_button:
                        break
                except Exception as e:
                    pass
            
            if submit_button:
                try:
                    self.log_status("🖱️ Clicking submit button...")
                    submit_button.click()
                    self.random_delay(2, 3)
                    self.take_screenshot('08_after_submit.png')
                    self.log_status("✅ Submit button clicked successfully")
                except Exception as e:
                    self.log_status(f"⚠️ Submit click failed: {str(e)}", "warning")
            else:
                self.log_status("💡 Submit button not found - please complete submission manually", "info")
            
            # Final message
            self.log_status("✅ Booking automation completed!")
            self.log_status("📧 Please verify the booking in the browser and check your email for confirmation")
            self.log_status("🌐 Browser will remain open for your verification")
            
            return True, "Booking process completed! Please verify in the browser window and check your email."
            
        except Exception as e:
            error_msg = f"Booking continuation failed: {str(e)}"
            self.log_status(f"❌ {error_msg}", "error")
            self.take_screenshot('error_booking.png')
            return False, error_msg
    
    def execute_booking(self, booking_data):
        """Execute the booking process"""
        try:
            self.log_status("🚀 Starting booking automation")
            
            self.log_status("🔐 IMPORTANT: Please wait...")
            self.log_status("⏸️ Initializing...")
            self.random_delay(8, 12)
            
            if not self.check_internet_connection(booking_data['website_url']):
                return False, "No internet connection. Please check your network."
            
            self.log_status("🌐 Attempting to load website...")
            if not self.navigate_to_website(booking_data['website_url']):
                return False, "Failed to load website. Check your connection!"
            
            self.log_status("⏳ Waiting for page to load completely...")
            
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            is_error_page = False
            if "404 Error Page" in page_title or "에러페이지" in page_title:
                is_error_page = True
            elif "404 Error Page" in page_source and len(page_source) < 50000:
                is_error_page = True
            
            if is_error_page:
                self.log_status("❌ Website showing 404 error page!", "error")
                self.take_screenshot('error_404_page.png')
                return False, "❌ Website shows 404 error! Please check your connection and try again"
            
            self.take_screenshot('login_page.png')
            self.log_status(f"✅ Page loaded: {page_title}")
            self.log_status(f"📍 Current URL: {self.driver.current_url}")
            
            self.log_status("🔐 Step: Starting login process...")
            
            self.log_status("🔍 Looking for login ID field...")
            
            # First, log all input fields for debugging
            try:
                all_inputs = self.driver.find_elements(By.XPATH, "//input")
                self.log_status(f"🔍 Debug: Found {len(all_inputs)} total input fields on page")
                visible_count = sum(1 for inp in all_inputs if inp.is_displayed())
                self.log_status(f"🔍 Debug: {visible_count} input fields are visible")
            except Exception as e:
                self.log_status(f"🔍 Debug check failed: {str(e)[:50]}", "info")
            
            login_field = self.smart_find_field('login_id')
            if login_field:
                self.log_status(f"✅ Login ID field found, filling with: {booking_data['login_id']}")
                login_field.clear()
                self.random_delay(0.3, 0.8)
                self.human_type(login_field, booking_data['login_id'])
                self.log_status(f"✅ Login ID filled successfully")
                self.random_delay(0.5, 1.0)
            else:
                self.log_status("⚠️ Login ID field not found - trying alternative methods...", "warning")
                login_found = False
                
                # Try multiple methods to find login field
                try:
                    # Method 1: Look for first visible text input
                    text_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or not(@type)]")
                    for inp in text_inputs:
                        if inp.is_displayed():
                            login_field = inp
                            login_found = True
                            self.log_status(f"✅ Found login field (first visible text input), filling...")
                            break
                    
                    if login_found and login_field:
                        login_field.clear()
                        self.human_type(login_field, booking_data['login_id'])
                        self.log_status(f"✅ Login ID filled using alternative method")
                        self.random_delay(0.5, 1.0)
                    else:
                        self.log_status(f"❌ Could not find login ID field", "error")
                except Exception as e:
                    self.log_status(f"❌ Could not find login ID field: {str(e)[:100]}", "error")
            
            # Enhanced password field detection with detailed logging
            self.log_status("� Looking for password field...")
            password_field = None
            password_found = False
            
            # First, try smart_find_field
            try:
                password_field = self.smart_find_field('password')
                if password_field and password_field.is_displayed():
                    password_found = True
                    self.log_status("🔑 Found password field using smart_find_field")
            except Exception as e:
                self.log_status(f"🔍 smart_find_field: {str(e)[:50]}", "info")
            
            # Method 1: Try finding by type='password' 
            if not password_found:
                self.log_status("⚠️ Trying Method 1: type='password'...", "warning")
                try:
                    password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
                    self.log_status(f"🔍 Found {len(password_fields)} password-type fields")
                    if password_fields:
                        for idx, pf in enumerate(password_fields):
                            try:
                                is_displayed = pf.is_displayed()
                                is_enabled = pf.is_enabled()
                                field_id = pf.get_attribute('id') or 'N/A'
                                field_name = pf.get_attribute('name') or 'N/A'
                                self.log_status(f"  Field {idx+1}: id='{field_id}', name='{field_name}', visible={is_displayed}, enabled={is_enabled}")
                                if is_displayed and is_enabled:
                                    password_field = pf
                                    password_found = True
                                    self.log_status("🔑 Found password field using type='password'!")
                                    break
                            except:
                                continue
                except Exception as e:
                    self.log_status(f"🔍 Method 1 failed: {str(e)[:50]}", "info")
                
                # Method 2: Try finding by common Korean/English names
                if not password_found:
                    self.log_status("⚠️ Trying Method 2: name/id patterns...", "warning")
                    try:
                        password_patterns = [
                            ("//input[contains(@id, 'Pw')]", "id contains 'Pw'"),
                            ("//input[contains(@id, 'pw')]", "id contains 'pw'"),
                            ("//input[contains(@name, 'Pw')]", "name contains 'Pw'"),
                            ("//input[contains(@name, 'pw')]", "name contains 'pw'"),
                            ("//input[contains(@name, 'pass')]", "name contains 'pass'"),
                            ("//input[contains(@id, 'pass')]", "id contains 'pass'"),
                            ("//input[contains(@placeholder, '비밀번호')]", "placeholder='비밀번호'"),
                            ("//input[contains(@placeholder, 'password')]", "placeholder='password'"),
                            ("//input[contains(@placeholder, 'Password')]", "placeholder='Password'")
                        ]
                        for pattern, desc in password_patterns:
                            try:
                                password_fields = self.driver.find_elements(By.XPATH, pattern)
                                self.log_status(f"🔍 Pattern '{desc}': found {len(password_fields)} fields")
                                for pf in password_fields:
                                    if pf.is_displayed() and pf.is_enabled():
                                        password_field = pf
                                        password_found = True
                                        self.log_status(f"🔑 Found password field using: {desc}")
                                        break
                                if password_found:
                                    break
                            except:
                                continue
                    except Exception as e:
                        self.log_status(f"🔍 Method 2 failed: {str(e)[:50]}", "info")
                
                # Method 3: Find second input field after username (common pattern)
                if not password_found:
                    self.log_status("⚠️ Trying Method 3: second visible input field...", "warning")
                    try:
                        # Find all input fields that could be text or password
                        all_inputs = self.driver.find_elements(By.XPATH, "//input")
                        visible_inputs = []
                        for inp in all_inputs:
                            try:
                                if inp.is_displayed() and inp.is_enabled():
                                    input_type = inp.get_attribute('type') or 'text'
                                    # Include text, password, and inputs without type
                                    if input_type.lower() in ['text', 'password', '']:
                                        visible_inputs.append(inp)
                                        field_id = inp.get_attribute('id') or 'N/A'
                                        field_name = inp.get_attribute('name') or 'N/A'
                                        field_type = inp.get_attribute('type') or 'text'
                                        self.log_status(f"  Visible input: type='{field_type}', id='{field_id}', name='{field_name}'")
                            except:
                                continue
                        
                        self.log_status(f"🔍 Found {len(visible_inputs)} visible input fields")
                        
                        if len(visible_inputs) >= 2:
                            password_field = visible_inputs[1]  # Second field is usually password
                            password_found = True
                            self.log_status("🔑 Found password field as second visible input field")
                    except Exception as e:
                        self.log_status(f"🔍 Method 3 failed: {str(e)[:50]}", "info")
                
                # Method 4: Wait and retry (field might load dynamically)
                if not password_found:
                    self.log_status("⚠️ Trying Method 4: waiting for dynamic load...", "warning")
                    try:
                        self.random_delay(2, 3)
                        password_field = self.wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
                        )
                        if password_field and password_field.is_displayed():
                            password_found = True
                            self.log_status("🔑 Found password field after waiting")
                    except Exception as e:
                        self.log_status(f"🔍 Method 4 failed: {str(e)[:50]}", "info")
                
                # Fill the password field if found
                if password_found and password_field:
                    try:
                        self.log_status("🔑 Filling password field...")
                        password_field.clear()
                        self.random_delay(0.3, 0.8)
                        self.human_type(password_field, booking_data['password'])
                        self.log_status(f"✅ Password filled successfully")
                        self.random_delay(0.5, 1.0)
                    except Exception as e:
                        self.log_status(f"❌ Failed to fill password: {str(e)[:100]}", "error")
                else:
                    self.log_status("❌ Could not find password field with any method", "error")
                    self.take_screenshot('password_field_not_found.png')
                    self.log_status("📸 Screenshot saved for debugging")
                    # Print available input fields for debugging
                    try:
                        all_inputs = self.driver.find_elements(By.XPATH, "//input")
                        self.log_status(f"🔍 DEBUG: Found {len(all_inputs)} total input fields on page")
                        for idx, inp in enumerate(all_inputs[:15]):  # Show first 15
                            try:
                                input_type = inp.get_attribute('type') or 'text'
                                input_name = inp.get_attribute('name') or 'N/A'
                                input_id = inp.get_attribute('id') or 'N/A'
                                input_placeholder = inp.get_attribute('placeholder') or 'N/A'
                                is_visible = inp.is_displayed()
                                self.log_status(f"  Input {idx+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}', visible={is_visible}")
                            except Exception as e:
                                self.log_status(f"  Input {idx+1}: Could not read - {str(e)[:30]}")
                    except Exception as e:
                        self.log_status(f"🔍 Could not list input fields: {str(e)[:100]}", "info")
            
            self.log_status("📸 Taking screenshot before login attempt...")
            self.take_screenshot('before_login.png')
            
            # Check for and handle CAPTCHA field (before login button)
            self.log_status("🔍 Checking for CAPTCHA field...")
            captcha_field = None
            captcha_patterns = [
                ("Korean placeholder", "//input[contains(@placeholder, '보안문자')]"),
                ("Security placeholder", "//input[contains(@placeholder, 'security')]"),
                ("Captcha placeholder", "//input[contains(@placeholder, 'captcha')]"),
                ("CAPTCHA placeholder", "//input[contains(@placeholder, 'CAPTCHA')]"),
                ("Captcha name/id", "//input[@name='captcha' or @id='captcha' or @name='captchaCode' or @id='captchaCode']"),
                ("Captcha class", "//input[contains(@class, 'captcha')]"),
                ("Any input near captcha image", "//img[contains(@src, 'captcha') or contains(@alt, 'captcha')]/following-sibling::input | //img[contains(@src, 'captcha') or contains(@alt, 'captcha')]/../input"),
                ("Input after captcha label", "//label[contains(text(), '보안문자') or contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]/following-sibling::input"),
            ]
            
            for pattern_name, pattern in captcha_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element and element.is_displayed():
                            captcha_field = element
                            self.log_status(f"✅ CAPTCHA field found using: {pattern_name}")
                            break
                    if captcha_field:
                        break
                except Exception as e:
                    self.log_status(f"🔍 Tried {pattern_name}: not found", "info")
                    pass
            
            # Also try to find by looking for input fields near captcha images
            if not captcha_field:
                try:
                    self.log_status("🔍 Trying to find CAPTCHA by image proximity...")
                    captcha_images = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'captcha') or contains(@alt, 'captcha') or contains(@id, 'captcha') or contains(@class, 'captcha')]")
                    for img in captcha_images:
                        if img.is_displayed():
                            # Look for input fields near this image
                            parent = img.find_element(By.XPATH, "./..")
                            nearby_inputs = parent.find_elements(By.XPATH, ".//input[@type='text']")
                            for inp in nearby_inputs:
                                if inp.is_displayed() and inp.get_attribute('placeholder') and ('보안문자' in inp.get_attribute('placeholder') or 'captcha' in inp.get_attribute('placeholder').lower()):
                                    captcha_field = inp
                                    self.log_status("✅ CAPTCHA field found near captcha image")
                                    break
                            if captcha_field:
                                break
                except Exception as e:
                    self.log_status(f"🔍 Image proximity search: {str(e)[:100]}", "info")
            
            if captcha_field and captcha_field.is_displayed():
                captcha_value = captcha_field.get_attribute('value') or ''
                self.log_status(f"🔐 CAPTCHA field detected! Current value: '{captcha_value}'")
                
                if not captcha_value or len(captcha_value.strip()) == 0:
                    self.log_status("⚠️ CAPTCHA field is EMPTY - manual completion required!")
                    self.log_status("⏸️ Please manually complete the CAPTCHA in the browser window...")
                    self.log_status("⏳ Waiting 60 seconds for manual CAPTCHA completion...")
                    self.take_screenshot('captcha_detected.png')
                    
                    # Get CAPTCHA field selector for auto-removal
                    captcha_field_id = captcha_field.get_attribute('id') or ''
                    captcha_field_name = captcha_field.get_attribute('name') or ''
                    
                    # Inject visible notification overlay in the browser
                    notification_script = f'''
                    // Remove any existing notification
                    const existing = document.getElementById('captcha-notification-overlay');
                    if (existing) existing.remove();
                    
                    // Create notification overlay
                    const overlay = document.createElement('div');
                    overlay.id = 'captcha-notification-overlay';
                    overlay.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0, 0, 0, 0.5);
                        z-index: 999999;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        animation: fadeIn 0.3s ease-in;
                    `;
                    
                    const notificationBox = document.createElement('div');
                    notificationBox.style.cssText = `
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px 50px;
                        border-radius: 15px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        color: white;
                        text-align: center;
                        max-width: 500px;
                        animation: pulse 2s infinite;
                    `;
                    
                    notificationBox.innerHTML = `
                        <div style="font-size: 60px; margin-bottom: 20px;">🔐</div>
                        <h2 style="margin: 0 0 15px 0; font-size: 28px; font-weight: bold;">CAPTCHA Required!</h2>
                        <p style="margin: 0 0 20px 0; font-size: 18px; opacity: 0.95;">
                            Please complete the CAPTCHA below<br>
                            The script will continue automatically in 60 seconds
                        </p>
                        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; font-size: 14px; opacity: 0.9;">
                            ⏳ Waiting for manual completion...
                        </div>
                    `;
                    
                    overlay.appendChild(notificationBox);
                    document.body.appendChild(overlay);
                    
                    // Add CSS animations
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes fadeIn {{
                            from {{ opacity: 0; }}
                            to {{ opacity: 1; }}
                        }}
                        @keyframes fadeOut {{
                            from {{ opacity: 1; }}
                            to {{ opacity: 0; }}
                        }}
                        @keyframes pulse {{
                            0%, 100% {{ transform: scale(1); }}
                            50% {{ transform: scale(1.02); }}
                        }}
                        #captcha-notification-overlay {{
                            animation: fadeIn 0.3s ease-in;
                        }}
                        #captcha-notification-overlay > div {{
                            animation: pulse 2s infinite;
                        }}
                    `;
                    document.head.appendChild(style);
                    
                    // Remove notification when CAPTCHA field has a value
                    const captchaSelectors = [
                        'input[placeholder*="보안문자"]',
                        'input[placeholder*="security"]',
                        'input[placeholder*="captcha"]',
                        'input[name="captcha"]',
                        'input[id="captcha"]',
                        'input[name="captchaCode"]',
                        'input[id="captchaCode"]'
                    ''' + (f', \'input[id="{captcha_field_id}"]\'' if captcha_field_id else '') + (f', \'input[name="{captcha_field_name}"]\'' if captcha_field_name else '') + '''];
                    
                    let captchaInput = null;
                    for (const selector of captchaSelectors) {
                        captchaInput = document.querySelector(selector);
                        if (captchaInput) break;
                    }
                    
                    if (captchaInput) {
                        const checkCaptcha = setInterval(() => {
                            if (captchaInput.value && captchaInput.value.length > 0) {
                                const overlayEl = document.getElementById('captcha-notification-overlay');
                                if (overlayEl) {
                                    overlayEl.style.animation = 'fadeOut 0.3s ease-out';
                                    setTimeout(() => overlayEl.remove(), 300);
                                }
                                clearInterval(checkCaptcha);
                            }
                        }, 1000);
                    }
                    '''
                    
                    # Scroll to CAPTCHA field and highlight it
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", captcha_field)
                    self.driver.execute_script("""
                        const field = arguments[0];
                        const originalStyle = field.style.cssText;
                        field.style.cssText += 'border: 3px solid #ff6b6b !important; box-shadow: 0 0 20px rgba(255, 107, 107, 0.6) !important; animation: blink 1s infinite;';
                        setTimeout(() => {
                            field.style.cssText = originalStyle + 'border: 2px solid #4ecdc4 !important; box-shadow: 0 0 15px rgba(78, 205, 196, 0.4) !important;';
                        }, 3000);
                    """, captcha_field)
                    
                    # Inject notification overlay
                    self.driver.execute_script(notification_script)
                    
                    # Add blinking animation for CAPTCHA field
                    self.driver.execute_script("""
                        const style = document.createElement('style');
                        style.textContent = '@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }';
                        document.head.appendChild(style);
                    """)
                    
                    self.log_status("✅ Visual notification displayed in browser - Please complete CAPTCHA now")
                    
                    # Wait for user to complete CAPTCHA manually, checking periodically
                    self.log_status("⏳ Waiting for CAPTCHA completion (checking every 5 seconds)...")
                    wait_time = 0
                    max_wait = 60
                    check_interval = 5
                    
                    while wait_time < max_wait:
                        self.random_delay(check_interval - 0.5, check_interval + 0.5)
                        wait_time += check_interval
                        
                        try:
                            current_value = captcha_field.get_attribute('value') or ''
                            if current_value and len(current_value.strip()) > 0:
                                self.log_status(f"✅ CAPTCHA field has value: '{current_value}' - continuing!")
                                break
                            else:
                                remaining = max_wait - wait_time
                                self.log_status(f"⏳ CAPTCHA still empty. Waiting... ({remaining} seconds remaining)")
                        except:
                            self.log_status(f"⏳ Checking CAPTCHA status... ({max_wait - wait_time} seconds remaining)")
                    
                    # Remove notification overlay
                    try:
                        self.driver.execute_script("""
                            const overlay = document.getElementById('captcha-notification-overlay');
                            if (overlay) overlay.remove();
                        """)
                    except:
                        pass
                    
                    final_value = captcha_field.get_attribute('value') or ''
                    if final_value and len(final_value.strip()) > 0:
                        self.log_status(f"✅ CAPTCHA completed with value: '{final_value}' - proceeding with login")
                    else:
                        self.log_status("⚠️ CAPTCHA field still empty after wait period - proceeding anyway (may fail)")
                else:
                    self.log_status(f"✅ CAPTCHA field already has value: '{captcha_value}' - proceeding")
            else:
                self.log_status("ℹ️ No CAPTCHA field detected - proceeding with login")
            
            # Find and click login button
            self.log_status("🔘 Step: Looking for login button...")
            login_button = self.smart_find_button(['login', 'sign in', 'submit', '로그인', 'log in'])
            if login_button:
                self.log_status("✅ Login button found using smart_find_button")
            else:
                self.log_status("🔍 Login button not found, trying smart_find_field...")
                login_button = self.smart_find_field('login_button')
            
            if not login_button:
                # Try finding any button or submit input
                self.log_status("⚠️ Trying alternative methods to find submit button...", "warning")
                try:
                    login_button = self.driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
                    self.log_status("✅ Found submit button using type='submit'")
                except:
                    try:
                        login_button = self.driver.find_element(By.XPATH, "//button | //input[@type='button']")
                        self.log_status("✅ Found button using generic button selector")
                    except:
                        self.log_status("❌ Could not find any button element", "error")
                        pass
            
            if login_button:
                self.log_status("🖱️ Attempting to click login button...")
                click_success = self.human_click(login_button)
                if click_success:
                    self.log_status("✅ Login button clicked successfully")
                else:
                    self.log_status("⚠️ Login button click may have failed", "warning")
                self.log_status("⏳ Waiting for login to process (4-6 seconds)...")
                self.random_delay(4, 6)  # Wait for login to process
                self.log_status("📸 Taking screenshot after login attempt...")
                self.take_screenshot('after_login.png')
                self.log_status(f"✅ Screenshot saved. Current URL: {self.driver.current_url}")
            else:
                self.log_status("❌ Login button not found - Please check the screenshot", "error")
                self.take_screenshot('login_button_not_found.png')
            
            self.log_status("📋 Step: Filling booking form fields...")
            
            embassy_field = self.smart_find_field('embassy')
            if embassy_field and booking_data.get('embassy'):
                self.log_status(f"🏛️ Found embassy field, selecting: {booking_data['embassy']}")
                try:
                    select = Select(embassy_field)
                    select.select_by_visible_text(booking_data['embassy'])
                    self.log_status("✅ Embassy selected successfully")
                    self.random_delay(1.5, 2.5)
                except Exception as e:
                    self.log_status(f"⚠️ Embassy selection failed: {str(e)}", "warning")
            else:
                if not embassy_field:
                    self.log_status("ℹ️ Embassy field not found (may not be required)")
                else:
                    self.log_status("ℹ️ Embassy not provided in booking data")
            
            service_field = self.smart_find_field('service')
            if service_field:
                service_text = booking_data.get('service_type', 'Document Authentication')
                self.log_status(f"📄 Found service field, selecting: {service_text}")
                try:
                    select = Select(service_field)
                    # Try different selection methods
                    try:
                        select.select_by_visible_text(service_text)
                        self.log_status(f"✅ Service selected by visible text: {service_text}")
                    except:
                        try:
                            select.select_by_value(service_text.lower().replace(' ', '_'))
                            self.log_status(f"✅ Service selected by value")
                        except:
                            select.select_by_index(1)
                            self.log_status(f"✅ Service selected by index (fallback)")
                    self.random_delay(1.5, 2.5)
                except Exception as e:
                    self.log_status(f"⚠️ Service selection failed: {str(e)}", "warning")
            else:
                self.log_status("ℹ️ Service field not found (may not be required)")
            
            date_field = self.smart_find_field('date')
            if date_field and booking_data.get('date'):
                self.log_status(f"📅 Found date field, entering: {booking_data['date']}")
                date_field.clear()
                self.human_type(date_field, booking_data['date'])
                self.log_status("✅ Date entered successfully")
            else:
                if not date_field:
                    self.log_status("ℹ️ Date field not found (may not be required)")
                else:
                    self.log_status("ℹ️ Date not provided in booking data")
            
            time_field = self.smart_find_field('time')
            if time_field and booking_data.get('time'):
                self.log_status(f"🕐 Found time field, entering: {booking_data['time']}")
                time_field.clear()
                self.human_type(time_field, booking_data['time'])
                self.log_status("✅ Time entered successfully")
            else:
                if not time_field:
                    self.log_status("ℹ️ Time field not found (may not be required)")
                else:
                    self.log_status("ℹ️ Time not provided in booking data")
            
            passport_field = self.smart_find_field('passport')
            if passport_field and booking_data.get('passport_number'):
                self.log_status("🛂 Found passport field, entering passport number...")
                passport_field.clear()
                self.human_type(passport_field, booking_data['passport_number'])
                self.log_status("✅ Passport number entered successfully")
            else:
                if not passport_field:
                    self.log_status("ℹ️ Passport field not found (may not be required)")
                else:
                    self.log_status("ℹ️ Passport number not provided in booking data")
            
            self.log_status("📧 Step: Setting notification preferences...")
            
            if booking_data.get('notify_email'):
                try:
                    # Try multiple patterns for email notification
                    email_checkbox = None
                    for pattern in ['notifyEmail', 'emailNotif', 'email_notification', 'chkEmail']:
                        try:
                            email_checkbox = self.driver.find_element(By.ID, pattern)
                            break
                        except:
                            try:
                                email_checkbox = self.driver.find_element(By.NAME, pattern)
                                break
                            except:
                                pass
                    
                    if email_checkbox and not email_checkbox.is_selected():
                        self.human_click(email_checkbox)
                        self.log_status("✅ Email notification enabled")
                except Exception as e:
                    self.log_status(f"⚠️ Email notification: {str(e)}", "warning")
            
            if booking_data.get('notify_sms'):
                try:
                    sms_checkbox = None
                    for pattern in ['notifySms', 'smsNotif', 'sms_notification', 'chkSms']:
                        try:
                            sms_checkbox = self.driver.find_element(By.ID, pattern)
                            break
                        except:
                            try:
                                sms_checkbox = self.driver.find_element(By.NAME, pattern)
                                break
                            except:
                                pass
                    
                    if sms_checkbox and not sms_checkbox.is_selected():
                        self.human_click(sms_checkbox)
                        self.log_status("✅ SMS notification enabled")
                except Exception as e:
                    self.log_status(f"⚠️ SMS notification: {str(e)}", "warning")
            
            # Take pre-submit screenshot
            self.log_status("📸 Taking pre-submit screenshot...")
            self.take_screenshot('pre_submit.png')
            self.log_status(f"✅ Pre-submit screenshot saved. Current URL: {self.driver.current_url}")
            
            self.log_status("🎯 Step: Submitting booking confirmation...")
            
            submit_button = self.smart_find_button(['submit', 'confirm', 'book', 'reserve', '제출', '확인'])
            if submit_button:
                self.log_status("✅ Submit button found using smart_find_button")
            else:
                self.log_status("🔍 Submit button not found, trying smart_find_field...")
                submit_button = self.smart_find_field('submit_button')
            
            if submit_button:
                self.log_status("🖱️ Attempting to click submit button...")
                click_success = self.human_click(submit_button)
                if click_success:
                    self.log_status("✅ Submit button clicked successfully")
                else:
                    self.log_status("⚠️ Submit button click may have failed", "warning")
                self.log_status("⏳ Waiting for submission to process (4-6 seconds)...")
                self.random_delay(4, 6)
                self.log_status("📸 Taking post-submit screenshot...")
                self.take_screenshot('post_submit.png')
                self.log_status(f"✅ Post-submit screenshot saved. Current URL: {self.driver.current_url}")
                self.log_status("✅ Booking submitted successfully!")
                self.log_status("📧 Check your email/SMS for confirmation")
                return True, "Booking completed successfully! Check your email/SMS for confirmation."
            else:
                self.log_status("❌ Submit button not found", "error")
                self.log_status(f"⚠️ Current page URL: {self.driver.current_url}")
                self.log_status(f"⚠️ Current page title: {self.driver.title}")
                self.take_screenshot('submit_not_found.png')
                return False, "Submit button not found. Please check the screenshots to see what page was loaded."
            
        except Exception as e:
            self.log_status(f"❌ Booking failed: {str(e)}", "error")
            self.take_screenshot('error.png')
            return False, str(e)
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.log_status("🔒 Browser closed")
    
    def check_internet_connection(self, url):
        """Check if internet connection is available"""
        try:
            # Extract domain from URL
            domain = urlparse(url).netloc or url
            
            # Try to resolve DNS
            socket.gethostbyname(domain)
            self.log_status("✅ Internet connection verified")
            return True
        except socket.gaierror:
            self.log_status("❌ Cannot resolve website. Check internet connection.", "error")
            return False
        except Exception as e:
            self.log_status(f"⚠️ Connection check warning: {str(e)}", "warning")
            return True  # Continue anyway if check fails


# Global automation instance
automation = None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/start_booking', methods=['POST'])
def start_booking():
    """Start the booking process"""
    global automation
    
    try:
        data = request.json
        
        # Create automation instance
        automation = BookingAutomation(headless=False)
        
        # Setup browser with stealth mode for full automation
        if not automation.setup_driver(use_stealth=True):
            return jsonify({
                'success': False,
                'message': 'Failed to initialize browser',
                'status': automation.status_updates
            })
        
        # Execute booking
        success, message = automation.execute_booking(data)
        
        # Keep browser open briefly
        automation.random_delay(2, 4)
        
        return jsonify({
            'success': success,
            'message': message,
            'status': automation.status_updates
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status': automation.status_updates if automation else []
        })
    finally:
        if automation:
            automation.close()


@app.route('/start_manual_login', methods=['POST'])
def start_manual_login():
    """Start booking with manual login - user logs in, then automation continues"""
    global automation
    
    try:
        data = request.json
        
        # Create automation instance
        automation = BookingAutomation(headless=False)
        
        # Execute booking with manual login (setup_driver is called inside with use_stealth=False)
        success, message = automation.execute_manual_login_booking(data)
        
        # Keep browser open for user to verify
        automation.random_delay(5, 10)
        
        return jsonify({
            'success': success,
            'message': message,
            'status': automation.status_updates
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status': automation.status_updates if automation else []
        })
    finally:
        if automation:
            automation.close()


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'running', 'timestamp': datetime.now().isoformat()})


@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204  # No content, prevents 404 errors


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/screenshots', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 Appointment Booking Automation System")
    print("="*60)
    print("\n📱 Web Interface: http://localhost:5001")
    print("📖 Open the URL above in your browser\n")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
