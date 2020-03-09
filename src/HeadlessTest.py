from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.headless = True
driver = webdriver.Firefox(options=options, executable_path=r'/bin/geckodriver')
driver.get("http://quibids.com/en/auction-798156855US-C1771183-150-amazon-gift-card")
print ("Headless Firefox Initialized")
driver.quit()

