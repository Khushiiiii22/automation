#!/usr/bin/env python3
# Quick script to add debugging to _continue_booking_after_login

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the location to insert debugging
old_code = '''            self.take_screenshot('03_booking_page.png')
            current_url = self.driver.current_url
            self.log_status(f"📍 Current URL: {current_url}")'''

new_code = '''            self.take_screenshot('03_booking_page.png')
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.log_status(f"📍 Current URL: {current_url}")
            self.log_status(f"📄 Page Title: {page_title}")
            
            # Debug: Log all elements on the page
            self.log_status("🔍 DEBUG: Analyzing page structure...")
            try:
                # Check for all buttons
                all_buttons = self.driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit'] | //a[contains(@class, 'btn')]")
                self.log_status(f"🔍 Found {len(all_buttons)} buttons/button-like elements")
                for i, btn in enumerate(all_buttons[:10]):  # Show first 10
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
                for i, sel in enumerate(all_selects[:10]):  # Show first 10
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
                for i, inp in enumerate(visible_inputs[:15]):  # Show first 15 visible ones
                    try:
                        inp_type = inp.get_attribute('type') or 'text'
                        inp_name = inp.get_attribute('name') or 'No name'
                        inp_id = inp.get_attribute('id') or 'No ID'
                        inp_placeholder = inp.get_attribute('placeholder') or 'No placeholder'
                        self.log_status(f"  Input {i+1}: type='{inp_type}' | name='{inp_name}' | id='{inp_id}' | placeholder='{inp_placeholder[:30]}'")
                    except:
                        pass
                
                # Check for all links
                all_links = self.driver.find_elements(By.XPATH, "//a")
                visible_links = [link for link in all_links if link.is_displayed() and link.text.strip()]
                self.log_status(f"🔍 Found {len(visible_links)} visible links with text")
                for i, link in enumerate(visible_links[:10]):  # Show first 10
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
                self.log_status(f"🔍 Debug analysis failed: {str(e)[:100]}", "warning")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Debugging code added successfully!")
else:
    print("❌ Could not find the code to replace")
