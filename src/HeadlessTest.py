from selenium import webdriver
options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome(options=options)

driver.get("http://quibids.com/en/auction-333427488US-C1704-25-amazon-gift-card")