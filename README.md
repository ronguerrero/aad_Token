# Overview

This program will retrieve an AAD access token that can be used against Azure services like Azure Databricks.  
Access tokens have a short lifespan and must be renewed periodically using a refresh token.    
Refresh tokens have a much longer lifespan than access tokens.

The process flow is a follows:
 * retrieve an authorization code (which will allows us to request an access token). It will launch a browser via the Selenium python module.
 * retrieve the access token and refresh token from AAD
 * the refresh token will be persisted to a local file - .refresh_token
 * the refresh token will be used to get renewed access token without having to retrieve and authorization code (logging into AAD).
 *
 * future runs of the program will leverage .refresh_token file, using it's contents to get an updated access token

# Getting Started  

Included is a conda environment yaml file.  Ensure conda is installed and run the following to create the environment:
```
conda env create -f environment.yml
conda activate aad-token
```

Refer to this link for more information: https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/aad/app-aad-token  
* Fill out the detail in config.ini.  
    * tenant = your azure tenant id
    * clientID = per the link above, it's the registered application ID
    * redirect_uri = per the link, whatever redirect URI that was specified
    * app_key = per the link, the associated key for the registered application
 * Run the program:   
    ``` python get_token.py ```
    
    
 # Troubleshooting
 * ensure you have the proper information in the config.ini file
 * the validity of the refresh token is not checked.  you can remove the .refresh_token file and re-run the program to get a newer refresh token.
 a
