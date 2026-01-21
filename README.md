# 🤖 Appointment Booking Automation System

A web-based automation system for booking appointments with advanced anti-bot detection bypass capabilities.

## 🚀 Quick Start

### 1. Start the server

```bash
python3 app.py
```

Server will run at: **http://localhost:5001**

### 2. Open the web interface

Navigate to http://localhost:5001 in your browser

### 3. Choose booking mode

- **Full Automation**: Complete automation including login
- **Manual Login + Auto Booking**: You log in, automation continues

## � Features

### Anti-Bot Detection Bypass

- Undetected ChromeDriver integration
- Advanced stealth JavaScript injection
- Multi-step navigation strategy
- Human-like delays and interactions

### Dual Mode Operation

1. **Full Automation Mode**
   - Automatic login
   - Form filling
   - Submission

2. **Manual Login Mode**
   - Manual login (60 second window)
   - Automatic form completion after login
   - Handles complex CAPTCHA scenarios

### Enhanced Field Detection

- Smart field pattern matching
- Multiple detection strategies
- Fallback mechanisms
- Korean and English field recognition

### Comprehensive Logging

- Detailed activity logs
- Screenshot capture at each step
- Error tracking and debugging
- Page structure analysis

## 🎯 Usage

### Prepare Information

Required details:
- Website URL
- Login credentials
- Appointment details (embassy, date, time)
- Personal information (name, passport, email, phone)

### Fill the Form

1. Open http://localhost:5001
2. Enter all required information
3. Select automation mode
4. Click start button

### Monitor Progress

The system will:
- Open browser window
- Navigate to target site
- Complete login process
- Fill booking forms
- Submit appointment request
- Capture screenshots

## 🔧 Configuration

### Browser Settings

Located in `setup_driver()` method:
- Headless mode option
- Stealth configurations
- Timeout settings

### Logging

Configured in `booking_automation.log`:
- Activity tracking
- Error messages
- Debug information

## 📸 Screenshots

Automatically saved in `static/screenshots/`:
- `01_login_page.png` - Initial page
- `02_after_manual_login.png` - Post-login
- `03_booking_page.png` - Booking form
- `04_navigated_booking.png` - After navigation
- `error.png` - Error captures

## 🐛 Troubleshooting

### Bot Detection Issues

If blocked by bot manager:
- System automatically retries
- Clears cookies
- Refreshes page
- Allows manual navigation

### Field Detection Failures

Check logs for:
- Available input fields
- Field attributes
- Detection attempts
- Error messages

### Connection Problems

Verify:
- Internet connectivity
- Website availability
- Port 5001 not in use
- ChromeDriver installation

## 🛠️ Technical Stack

- **Backend**: Flask web framework
- **Automation**: Selenium WebDriver
- **Anti-Detection**: undetected-chromedriver
- **Browser**: Google Chrome
- **Language**: Python 3.9+

## 📦 Dependencies

Install via `requirements_web.txt`:
```bash
pip install -r requirements_web.txt
```

Required packages:
- Flask
- Selenium
- undetected-chromedriver
- webdriver-manager

## 🔐 Security Notes

- Credentials handled in-memory only
- No data persistence
- Local execution only
- Session-based authentication

## ⚙️ System Requirements

- Python 3.9 or higher
- Google Chrome browser
- macOS, Linux, or Windows
- Stable internet connection

## 📝 License

This project is provided as-is for educational and automation purposes.
```bash
open static/screenshots/login_page.png
```
See exactly what the automation sees on the login page.

**Solution 3: Manual Inspection**
1. Open your target website in Chrome
2. Right-click on the password field → "Inspect"
3. Note the `id`, `name`, or `type` attributes
4. The improved code should now handle these automatically

### "Failed to load website"

- ✅ Check your internet connection
- ✅ Verify the URL is correct
- ✅ Try opening it in Chrome manually first
- ✅ Check if the website is down

### "404 Error Page"

- ✅ The URL might be incorrect
- ✅ The website structure may have changed
- ✅ Check your network connection

### CAPTCHAs

If CAPTCHA appears:
1. **Don't panic!** The automation will pause automatically
2. You'll see a purple notification in the browser
3. Complete the CAPTCHA manually
4. Wait - automation continues automatically after 60 seconds or when CAPTCHA is filled

## 🎓 Understanding the Automation

### Anti-Detection Features:

1. **Undetected ChromeDriver** - Bypasses STCLab Bot Manager and similar systems
2. **Human-like Typing** - Random delays between keystrokes (50-300ms)
3. **Random Delays** - Waits random amounts between actions
4. **Mouse Movements** - Simulates real mouse behavior
5. **Stealth Scripts** - Removes Selenium detection markers

### Success Indicators:

✅ Green checkmarks in the status log  
✅ Screenshots showing correct pages  
✅ "Booking completed successfully" message  
✅ Email/SMS confirmation from the website  

## 📊 Status Messages Explained

| Message | Meaning |
|---------|---------|
| 🚀 Starting booking automation | Beginning the process |
| 🌐 Navigating to... | Loading the website |
| 🔍 Debug: Found X input fields | Analyzing page structure |
| ✅ Login ID field found | Successfully located username field |
| 🔑 Found password field | Successfully located password field |
| ⚠️ Password field not found | Trying alternative methods |
| 🔐 CAPTCHA field detected | Manual intervention needed |
| ✅ Login button clicked | Login submitted |
| 📸 Screenshot saved | Screenshot captured for verification |
| ✅ Booking submitted successfully | All done! |

## 🔐 Security & Privacy

- **All data stays local** - Nothing sent to external servers
- **Credentials not saved** - Used only during automation
- **Open source** - You can review all the code
- **Browser-based** - You see everything happening

## 📞 Getting Help

### Check These First:

1. **Logs**: `booking_automation.log` - Detailed step-by-step log
2. **Screenshots**: `static/screenshots/` - Visual proof of what happened
3. **Website Inspector**: `python3 inspect_website.py` - Analyze the target website
4. **Guide**: `BOOKING_GUIDE.md` - Comprehensive guide

### Debug Workflow:

```
1. Run automation → Fails
2. Check logs → Find error message  
3. Look at screenshots → See what went wrong
4. Run website inspector → Understand page structure
5. Try again → Should work now!
```

## 🆘 Still Having Issues?

### The password field problem from your logs:

The error you saw:
```
⚠️ Password field not found - trying alternative methods...
❌ Could not find password field
```

**Has been fixed with:**
- 4 different detection methods
- Better error logging showing all input fields
- Screenshot capture for debugging
- Position-based fallback (finds 2nd input field)

### Try Now:

1. Go to http://localhost:5001
2. Fill in your credentials
3. Click "Start Booking Automation"
4. Watch the improved detection work!

The system will now:
- ✅ Log all input fields it finds
- ✅ Show their IDs, names, and types
- ✅ Try multiple methods to find password field
- ✅ Provide better error messages if it fails
- ✅ Save debugging screenshots

## 🎉 Tips for Success

1. **First Time?** Run `python3 inspect_website.py` to understand your target website
2. **Check Connection** Open the website manually first to ensure it's accessible
3. **Watch the Browser** Keep an eye on the automated browser window
4. **Read the Logs** Status updates tell you exactly what's happening
5. **Be Patient** Some websites load slowly - give it time

---

## 🔄 Quick Commands

Start the server (if not already running):
```bash
python3 app.py
```

Inspect a website:
```bash
python3 inspect_website.py
```

View recent screenshots:
```bash
ls -lh static/screenshots/
```

View logs:
```bash
tail -f booking_automation.log
```

Clear old screenshots:
```bash
rm static/screenshots/*.png
```

---

**Ready to book automatically? Visit http://localhost:5001 now! 🚀**
