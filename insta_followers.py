import time
import getpass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    options.add_argument("--disable-notifications")
    # options.add_argument("--headless")  # Comment this out to see the browser UI
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def login(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.NAME, "username")))
    
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/{username}/')]")))
    print("✅ Logged in successfully.")

def close_popups(driver):
    wait = WebDriverWait(driver, 5)
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")))
        btn.click()
        print("Closed a popup.")
    except:
        pass

def scroll_dialog(driver, dialog):
    last_height = driver.execute_script("return arguments[0].scrollHeight", dialog)
    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", dialog)
        time.sleep(2)
        new_height = driver.execute_script("return arguments[0].scrollHeight", dialog)
        if new_height == last_height:
            break
        last_height = new_height

def get_usernames_from_dialog(driver, link_xpath):
    wait = WebDriverWait(driver, 10)
    driver.find_element(By.XPATH, link_xpath).click()
    
    dialog = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//ul")))
    scroll_dialog(driver, dialog)
    
    links = dialog.find_elements(By.TAG_NAME, "a")
    users = [link.text.strip().lower() for link in links if link.text.strip() != ""]
    
    close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button[contains(text(),'Close')]")))
    close_btn.click()
    
    return set(users)

def highlight_nonfollowers(driver, followers, following):
    wait = WebDriverWait(driver, 10)
    
    # Open following dialog
    driver.find_element(By.XPATH, "//a[contains(@href, '/following/')]").click()
    dialog = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//ul")))
    scroll_dialog(driver, dialog)
    
    # Highlight users who do NOT follow back
    items = dialog.find_elements(By.TAG_NAME, "li")
    for item in items:
        try:
            username_elem = item.find_element(By.TAG_NAME, "a")
            username = username_elem.text.strip().lower()
            if username and username not in followers:
                # Change background color to highlight
                driver.execute_script("arguments[0].style.backgroundColor = '#ffcccc';", item)
        except:
            pass
    
    print(f"Highlighted {len(following - followers)} users not following back. Please check the browser window.")

def main():
    username = input("Enter your Instagram username: ").strip()
    password = getpass.getpass("Enter your Instagram password: ").strip()
    
    driver = setup_driver()
    try:
        login(driver, username, password)
        close_popups(driver)
        
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3)
        
        followers = get_usernames_from_dialog(driver, "//a[contains(@href, '/followers/')]")
        following = get_usernames_from_dialog(driver, "//a[contains(@href, '/following/')]")
        
        highlight_nonfollowers(driver, followers, following)
        
        print("You can now manually unfollow users highlighted in red in the 'Following' dialog.")
        print("Script will keep browser open for 10 minutes...")
        time.sleep(600)  # Keep browser open so you can work manually
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
