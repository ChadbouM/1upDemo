# Imports 
import os
import requests
import configparser
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read( config_path )
# Static  Config
log_levels = {
    'DEBUG' : logging.DEBUG,
    'INFO' : logging.INFO,
    'WARNING' : logging.WARNING,
    'ERROR' : logging.ERROR,
    'CRITICAL' : logging.CRITICAL
}
logging.basicConfig(level=log_levels[config['DEFAULT']['LogLevel'].upper()])
# - #
username = config['DEFAULT']['Username']
# Dynamic Config
client_id = config['CLIENT']['id']
client_sc = config['CLIENT']['secret']

# Request Convenience Function
def queryPost(uri, query):
    qs = '?'
    for key in query:
        qs += '%s=%s&'%(key, query[key]) 
    # print( baseURL + uri + qs[:-1] )
    return requests.post(uri + qs[:-1])
    
# Runtime Logic
## - Get Authorization for User
r = queryPost('https://api.1up.health/user-management/v1/user/auth-code', {
    'app_user_id'   : username,
    'client_id'     : client_id,
    'client_secret' : client_sc
})
# Extract User Code
user_code = r.json()['code']
# Get Auth Token using Code
r = requests.post('https://auth.1up.health/oauth2/token', data = {
    'client_id' : client_id,
    'client_secret' : client_sc,
    'code' : user_code,
    'grant_type' : 'authorization_code'
})
auth_token    = r.json()['access_token']
refresh_token = r.json()['refresh_token']

driver = webdriver.Chrome()
driver.implicitly_wait(30)
driver.get('https://api.1up.health/connect/system/clinical/4707?client_id=' + client_id + '&access_token=' + auth_token)

user_field = driver.find_element_by_name('login_username')
pass_field = driver.find_element_by_name('login_password')

user_field.send_keys("wilmasmart")
pass_field.send_keys("Cerner01")
pass_field.send_keys(Keys.RETURN)

allow_button = driver.find_element_by_id("allowButton")
allow_button.click()