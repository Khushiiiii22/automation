"""
Professional Appointment Booking Automation System
Web-based interface for easy configuration and execution
"""

from flask import Flask, render_template, request, jsonify, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import secrets
from datetime import datetime
import os
import socket


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
    """Professional booking automation handler"""
    
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
    
    def setup_driver(self):
        """Initialize WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
            self.log_status("✅ Browser initialized successfully")
            return True
        except Exception as e:
            self.log_status(f"❌ Failed to initialize browser: {str(e)}", "error")
            return False
    
    def navigate_to_website(self, url):
        """Navigate to target website"""
        try:
            self.log_status(f"🌐 Navigating to {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Check if page loaded successfully
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            if page_title:
                self.log_status(f"✅ Page loaded: {page_title}")
                return True
            else:
                self.log_status(f"⚠️ Page loaded but may be empty", "warning")
                return True
                
        except Exception as e:
            error_msg = str(e)
            
            # Provide user-friendly error messages
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
        
        # Try by ID first
        for pattern in patterns[field_type]:
            try:
                element = self.driver.find_element(By.ID, pattern)
                if element:
                    return element
            except:
                pass
        
        # Try by name
        for pattern in patterns[field_type]:
            try:
                element = self.driver.find_element(By.NAME, pattern)
                if element:
                    return element
            except:
                pass
        
        # Try by placeholder or label text for input fields
        if field_type not in ['login_button', 'submit_button']:
            try:
                # Try finding by placeholder
                element = self.driver.find_element(By.XPATH, f"//input[contains(@placeholder, '{field_type}')]")
                if element:
                    return element
            except:
                pass
        
        return None
    
    def smart_find_button(self, button_texts, timeout=10):
        """Find button by text or common patterns"""
        # Try finding by visible text
        for text in button_texts:
            try:
                element = self.driver.find_element(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")
                if element:
                    return element
            except:
                pass
            
            try:
                element = self.driver.find_element(By.XPATH, f"//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")
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
                element.clear()
                element.send_keys(value)
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
                element.click()
                self.log_status(f"✅ Clicked: {identifier}")
                time.sleep(1)
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
    
    def execute_booking(self, booking_data):
        """Execute the booking process"""
        try:
            self.log_status("🚀 Starting booking automation")
            
            # VPN Check Message
            self.log_status("🔐 IMPORTANT: Make sure you're connected to a Korean VPN!")
            self.log_status("⏸️ Waiting 10 seconds for you to connect to VPN...")
            time.sleep(10)
            
            # Check internet connectivity first
            if not self.check_internet_connection(booking_data['website_url']):
                return False, "No internet connection. Please check your network and VPN."
            
            # Navigate to website
            self.log_status("� Attempting to load website...")
            if not self.navigate_to_website(booking_data['website_url']):
                return False, "Failed to load website. Check your connection!"
            
            # Wait longer for page to fully load
            self.log_status("⏳ Waiting for page to load completely...")
            time.sleep(5)  # Give JavaScript time to render
            
            # Check if it's a real error page by looking at title
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            # IMPROVED: Check for actual 404 error page (not just "404" in text)
            is_error_page = False
            if "404 Error Page" in page_title or "에러페이지" in page_title:
                is_error_page = True
            elif "404 Error Page" in page_source and len(page_source) < 50000:
                # Short page with "404 Error Page" is likely actual error
                is_error_page = True
            
            if is_error_page:
                self.log_status("❌ Website showing 404 error page!", "error")
                self.take_screenshot('error_404_page.png')
                return False, "❌ Website shows 404 error! Make sure you're connected to Korean VPN. Try: 1) Connect VPN to Korea 2) Restart automation"
            
            # Take screenshot of login page
            self.take_screenshot('login_page.png')
            self.log_status(f"✅ Page loaded: {page_title}")
            
            # Step 1: Login
            self.log_status("🔐 Logging in...")
            
            # Find and fill login ID
            login_field = self.smart_find_field('login_id')
            if login_field:
                login_field.clear()
                time.sleep(0.5)
                login_field.send_keys(booking_data['login_id'])
                self.log_status(f"✅ Filled login ID: {booking_data['login_id']}")
                time.sleep(1)
            else:
                self.log_status("⚠️ Login ID field not found - trying alternative methods...", "warning")
                # Try finding by placeholder text
                try:
                    login_field = self.driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
                    if login_field:
                        login_field.clear()
                        login_field.send_keys(booking_data['login_id'])
                        self.log_status(f"✅ Filled login ID using alternative method")
                        time.sleep(1)
                except:
                    self.log_status("❌ Could not find login ID field", "error")
            
            # Find and fill password
            password_field = self.smart_find_field('password')
            if password_field:
                password_field.clear()
                time.sleep(0.5)
                password_field.send_keys(booking_data['password'])
                self.log_status(f"✅ Filled password")
                time.sleep(1)
            else:
                self.log_status("⚠️ Password field not found - trying alternative methods...", "warning")
                # Try finding by type='password'
                try:
                    password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                    if password_field:
                        password_field.clear()
                        password_field.send_keys(booking_data['password'])
                        self.log_status(f"✅ Filled password using alternative method")
                        time.sleep(1)
                except:
                    self.log_status("❌ Could not find password field", "error")
            
            # Take screenshot before clicking login
            self.take_screenshot('before_login.png')
            
            # Find and click login button
            self.log_status("🔘 Looking for login button...")
            login_button = self.smart_find_button(['login', 'sign in', 'submit', '로그인', 'log in'])
            if not login_button:
                login_button = self.smart_find_field('login_button')
            
            if not login_button:
                # Try finding any button or submit input
                self.log_status("⚠️ Trying to find submit button...", "warning")
                try:
                    login_button = self.driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
                except:
                    try:
                        login_button = self.driver.find_element(By.XPATH, "//button | //input[@type='button']")
                    except:
                        pass
            
            if login_button:
                login_button.click()
                self.log_status("✅ Clicked login button")
                time.sleep(5)  # Wait for login to process
                self.take_screenshot('after_login.png')
            else:
                self.log_status("❌ Login button not found - Please check the screenshot", "error")
                self.take_screenshot('login_button_not_found.png')
            
            # Step 2: Auto-select Embassy
            embassy_field = self.smart_find_field('embassy')
            if embassy_field and booking_data.get('embassy'):
                self.log_status(f"🏛️ Selecting embassy: {booking_data['embassy']}")
                try:
                    select = Select(embassy_field)
                    select.select_by_visible_text(booking_data['embassy'])
                    self.log_status("✅ Embassy selected")
                    time.sleep(2)
                except Exception as e:
                    self.log_status(f"⚠️ Embassy selection: {str(e)}", "warning")
            
            # Step 3: Select Document Authentication service
            service_field = self.smart_find_field('service')
            if service_field:
                self.log_status("📄 Selecting service type...")
                service_text = booking_data.get('service_type', 'Document Authentication')
                try:
                    select = Select(service_field)
                    # Try different selection methods
                    try:
                        select.select_by_visible_text(service_text)
                    except:
                        try:
                            select.select_by_value(service_text.lower().replace(' ', '_'))
                        except:
                            select.select_by_index(1)
                    self.log_status(f"✅ Selected service: {service_text}")
                    time.sleep(2)
                except Exception as e:
                    self.log_status(f"⚠️ Service selection: {str(e)}", "warning")
            
            # Step 4: Select Date and Time
            date_field = self.smart_find_field('date')
            if date_field and booking_data.get('date'):
                self.log_status("📅 Selecting appointment date...")
                date_field.clear()
                date_field.send_keys(booking_data['date'])
                self.log_status("✅ Date entered")
            
            time_field = self.smart_find_field('time')
            if time_field and booking_data.get('time'):
                self.log_status("🕐 Selecting appointment time...")
                time_field.clear()
                time_field.send_keys(booking_data['time'])
                self.log_status("✅ Time entered")
            
            # Step 5: Enter passport number
            passport_field = self.smart_find_field('passport')
            if passport_field and booking_data.get('passport_number'):
                self.log_status("🛂 Entering passport number...")
                passport_field.clear()
                passport_field.send_keys(booking_data['passport_number'])
                self.log_status("✅ Passport number entered")
            
            # Step 6: CAPTCHA handling
            self.log_status("🔐 Please complete CAPTCHA if present...")
            self.log_status("⏸️ Waiting 60 seconds for manual CAPTCHA completion...")
            time.sleep(60)
            
            # Step 7: Select notification preferences
            self.log_status("📧 Setting notification preferences...")
            
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
                        email_checkbox.click()
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
                        sms_checkbox.click()
                        self.log_status("✅ SMS notification enabled")
                except Exception as e:
                    self.log_status(f"⚠️ SMS notification: {str(e)}", "warning")
            
            # Take pre-submit screenshot
            self.take_screenshot('pre_submit.png')
            
            # Step 8: Final submit
            self.log_status("🎯 Submitting booking confirmation...")
            
            submit_button = self.smart_find_button(['submit', 'confirm', 'book', 'reserve', '제출', '확인'])
            if not submit_button:
                submit_button = self.smart_find_field('submit_button')
            
            if submit_button:
                submit_button.click()
                self.log_status("✅ Submit button clicked")
                time.sleep(5)
                self.take_screenshot('post_submit.png')
                self.log_status("✅ Booking submitted successfully!")
                self.log_status("📧 Check your email/SMS for confirmation")
                return True, "Booking completed successfully! Check your email/SMS for confirmation."
            else:
                self.log_status("❌ Submit button not found", "error")
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
            from urllib.parse import urlparse
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
        
        # Setup browser
        if not automation.setup_driver():
            return jsonify({
                'success': False,
                'message': 'Failed to initialize browser',
                'status': automation.status_updates
            })
        
        # Execute booking
        success, message = automation.execute_booking(data)
        
        # Keep browser open briefly
        time.sleep(3)
        
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
