from adal import AuthenticationContext
from selenium import webdriver
from urllib import parse

import requests
import configparser
import os

with open("config.ini") as f:
    config = configparser.ConfigParser(allow_no_value=False)
    config.read("config.ini")
    user_parameters = {
        "tenant": config['default']['tenant'],
        "clientId": config['default']['clientId'],
        "redirect_uri": config['default']['redirect_uri'],
        "app_key": config['default']['app_key'],
        "test_workspace": config['default']['test_workspace']
    }

# these parameters should be constant
authority_host_url = "https://login.microsoftonline.com/"
databricks_resource_id = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

TEMPLATE_AUTHZ_URL = ('https://login.windows.net/{}/oauth2/authorize?' +
                      'response_type=code&client_id={}&redirect_uri={}&' +
                      'state={}&resource={}')

# the auth_state can be a random number or can encoded some info
# about the user. It is used for preventing cross-site request
# forgery attacks [MS_doc]
auth_state = 12345

# build the URL to request the authorization code
authorization_url = TEMPLATE_AUTHZ_URL.format(
    user_parameters['tenant'],
    user_parameters['clientId'],
    user_parameters['redirect_uri'],
    auth_state,
    databricks_resource_id)


def get_authorization_code():
    # retrieves an authorization code from Azure so that we can make a subsequent request for an access token
    # Authorization Code ~= kerberos ticket
    # this logic assumes 2FA, a browser (Chrome) will be opened by Selenium for credential input

    # open a browser, here assume we use Chrome
    dr = webdriver.Chrome()
    # load the user login page
    dr.get(authorization_url)
    # wait until the user login or kill the process
    code_received = False

    code = ''
    while not code_received:
        cur_url = dr.current_url
        if cur_url.startswith(user_parameters['redirect_uri']):
            parsed = parse.urlparse(cur_url)
            query = parse.parse_qs(parsed.query)
            code = query['code'][0]
            state = query['state'][0]
            # throw exception if the state does not match
            if state != str(auth_state):
                raise ValueError('state does not match')
            code_received = True
            dr.close()

    if not code_received:
        print('Error in requesting authorization code')
        dr.close()

    # authorization code is returned. If not successful,
    # then an empty code is returned
    return code


def get_refresh_and_access_token():
    # using a retrieved authorization code, get the access token and the refresh token
    # access tokens have a limited lifespan,  you will need to use the refresh token to renew it

    # configure AuthenticationContext
    # authority URL and tenant ID are used
    authority_url = authority_host_url + user_parameters['tenant']
    context = AuthenticationContext(authority_url)

    # Obtain the authorization code in by a HTTP request in the browser
    # then copy it here or, call the function above to get the authorization code
    authz_code = get_authorization_code()

    # API call to get the token, the response is a
    # key-value dict
    token_response = context.acquire_token_with_authorization_code(
        authz_code,
        user_parameters['redirect_uri'],
        databricks_resource_id,
        user_parameters['clientId'],
        user_parameters['app_key'])

    # you can print all the fields in the token_response
    for key in token_response.keys():
        print(str(key) + ': ' + str(token_response[key]))

    # the tokens can be returned as a pair (or you can return the full
    # token_response)
    return token_response['accessToken'], token_response['refreshToken']


def refresh_access_token(refresh_token):
    # configure AuthenticationContext
    # authority URL and tenant ID are used
    authority_url = authority_host_url + user_parameters['tenant']
    context = AuthenticationContext(authority_url)

    # API call to get the token, the response is a
    # key-value dict
    token_response = context.acquire_token_with_refresh_token(
        refresh_token,
        user_parameters['clientId'],
        databricks_resource_id,
        user_parameters['app_key'])

    # you can print all the fields in the token_response
    for key in token_response.keys():
        print(str(key) + ': ' + str(token_response[key]))

    # the tokens can be returned as a pair (or you can return the full
    # token_response)
    return token_response['accessToken']


def connection_test(access_token):
    # simple test to make sure the access token is valid
    base_url = 'https://%s/api/2.0/workspace/get-status/' % user_parameters['test_workspace']

    # request header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # the /Shared folder should always exist and is accessible by anyone
    payload = {'path': '/Shared'}

    response = requests.get(
        base_url,
        headers=headers,
        params=payload
    )

    print('response header: ' + str(response.headers))

refresh_token_file = ".refresh_token"
if not os.path.exists(refresh_token_file):
    (access_token, refresh_token) = get_refresh_and_access_token()
    with open(refresh_token_file, 'w') as a_writer:
        a_writer.write(refresh_token)
else:
    with open(refresh_token_file, 'r') as a_reader:
        refresh_token = a_reader.readline()
        print(refresh_token)
        access_token = refresh_access_token(refresh_token)

connection_test(access_token)

print("\n\n\n\n\n\n\n\nAccess token: " + access_token)
