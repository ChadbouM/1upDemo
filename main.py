# Imports 
import os
import requests
import configparser
import logging
from datetime import datetime
# Setup Config & Logging
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read( config_path )
log_levels = {
    'DEBUG' : logging.DEBUG,
    'INFO' : logging.INFO,
    'WARNING' : logging.WARNING,
    'ERROR' : logging.ERROR,
    'CRITICAL' : logging.CRITICAL
}
logging.basicConfig(level=log_levels[config['DEFAULT']['LogLevel'].upper()])

auth_token = ''
refresh_token = ''
user_code  = ''
results = {
    'page_size_passed' : 0,
    'page_size_total'  : 0,
    'no_duplicates_passed' : 0,
    'no_duplicates_total'  : 0,
    'next_link_passed' : 0,
    'next_link_total'  : 0,
    'expected' : 0,
    'actual'   : 0,
    'failure_pages' : []
}

#############
# FUNCTIONS #
#############

# HTTPS Request Wrapper for POST
def myPost(url, data):
    try:
        r = requests.post(url, data=data)
    except Exception as e:
        raise Exception("Encountered a problem while sending POST request to %s" % url, e)
    if r.status_code >= 400:
        if len(url) > 60: url = url[:60] + '...'
        raise Exception("POST to %s returned a status code of %i" % (url, r.status_code))
    return r

# HTTPS Request Wrapper for GET
def myGet(url, token):
    try:
        r = requests.get(url, headers={
        'Authorization' : 'Bearer %s' % token
    })
    except Exception as e:
        raise Exception("Encountered a problem while sending GET request to %s" % url, e)
    if r.status_code >= 400:
        if len(url) > 60: url = url[:60] + '...'
        raise Exception("GET to %s returned a status code of %i" % (url, r.status_code))
    return r

# HTTPS meta wrapper
def call(method, url, data={}):
    method = method.upper()
    if method == 'POST': return myPost(url, data)
    elif method == 'GET': return myGet(url, auth_token)
    else: raise Exception("The 'call' function only accepts POST and GET, it was passed %s" % method)

# Function for grabbing the "next" link
def getLink(relation, content):
    try:
        for link in content['link']:
            if link['relation'] == relation: return link['url']
    except KeyError: pass
    return 0

# Duplication Test
def testDuplication(content):
    result = True
    logging.debug('Testing for Duplicates')
    log = []
    no_dups = True
    results['no_duplicates_total'] += 1
    for entry in content['entry']:
        if entry['fullUrl'] in log: no_dups = False
        log += [entry['fullUrl']]
    if no_dups: results['no_duplicates_passed'] += 1
    else: result = False
    return result

#################    
# Runtime Logic #
#################
def run(a, b):
    global auth_token
    logging.debug('Starting Up')
    # Get Authorization for User
    if 'code' not in config['CLIENT'].keys(): 
        logging.debug('Generating Authorization Code')
        r = call('POST', 'https://api.1up.health/user-management/v1/user/auth-code?'
            + 'app_user_id=%s'    % config['DEFAULT']['Username']
            + '&client_id=%s'     % config['CLIENT']['id']
            + '&client_secret=%s' % config['CLIENT']['secret']
        )
        # Extract User Code
        config['CLIENT']['code'] = r.json()['code']

    # Get Auth Token using Code
    logging.debug('Generating Authorization Token')
    r = call('POST', 'https://auth.1up.health/oauth2/token', {
        'client_id' :     config['CLIENT']['id'],
        'client_secret' : config['CLIENT']['secret'],
        'code' :          config['CLIENT']['code'],
        'grant_type' : 'authorization_code'
    })
    content = r.json()
    # Extract and update tokens
    auth_token    = content['access_token']
    # Call the test endpoint.
    logging.debug('Starting Test Sequence')

    # SETUP While Loop:
    r = call('GET', 'https://api.1up.health/fhir/dstu2/Observation')
    content = r.json()
    page_number = 1
    results['expected'] = content['total']
    next_page = getLink('next', content)
    # While loop for each page in pagination
    while next_page != 0:
        result = True
        # Length Test
        logging.debug('Testing Page Length')
        item_count = len(content['entry'])
        results['actual'] += item_count
        results['page_size_total'] += 1
        if item_count == 10: results['page_size_passed'] += 1
        else: result = False
        # Duplicate Test
        if not testDuplication(content): result = False
        #There is a next link so Next-Link test passes IF expected > actual
        logging.debug('Confirming that "Next" link should exist')
        results['next_link_total'] += 1
        if results['actual'] < results['expected']: results['next_link_passed'] += 1
        else: result = False
        # SETUP the next interation of while-loop
        r = call('GET', next_page)
        content = r.json()
        # Capture page if any tests failed
        if not result: 
            results['failure_pages'] += [page_number]
            logging.debug(content)
        page_number += 1
        next_page = getLink('next', content)   

    # Final Page Testing:
    result = True
    results['actual'] += len(content['entry'])
    # Duplicate Test
    if not testDuplication(content): result = False
    # There is no next-link. So Next-Link test passes IF expected == actual
    results['next_link_total'] += 1
    if results['actual'] == results['expected']: results['next_link_passed'] += 1
    else: result = False
    # Capture page if any tests failed
    if not result: 
        results['failure_pages'] += [page_number]
        logging.debug(content)

    # Print Results
    print("RESULTS:")
    print("* - Entries per Page Test:      %i / %i passed"%(results['page_size_passed'],results['page_size_total']))
    print("* - No Duplicates Test:         %i / %i passed"%(results['no_duplicates_passed'],results['no_duplicates_total']))
    print("* - Next Link Test:             %i / %i passed"%(results['next_link_passed'],results['next_link_total']))
    print("* - Results / Expected Results: %i / %i"%(results['actual'],results['expected']))
    print("** Pages with failures: " + str(results['failure_pages']))

if __name__ == '__main__':
    run('','')