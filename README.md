# 1upDemo

This is a Demo of a testing application capable of running a small array of tests against the 'https://api.1up.health/fhir/dstu2/Observation' endpoint.
It is pre-configured in a way which allows it to be deployed to AWS Lambda.

# Configuration (Windows)

1. Create an application in the 1up dev portal
	1. https://developer.1up.health/
	1. The OAuth2 Redirect URL can be set to any value. It is not used by this demo.
	1. Keep track of the OAuth2 Client Id and Secret
1. Pull down the git repo:
	* git clone https://github.com/ChadbouM/1upDemo.git
1. edit config.ini
	1. Add the client_id and client_secret from your 1up-app to the corresponding lines of the config file
1. Open a cmd-prompt in the new folder and run the following command
	1. python config.py
	1. This should generate a new user and link the 'wilmasmart' user-data to the user you created
1. Wait until the browser has been redirected to the Redirect URL, (in the case of http://localhost:8000 this will be an error screen)
1. Close the browser window

# Running Manually

1. python main.py