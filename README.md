# cgxEasyAPI
Expressive API for CGX

## Authentication

Rename file `cloudgenix_settings.py.changeme` to `cloudgenix_settings.py`. Inside that file replace `token here` with an auth token.

## API usage

### To init the API:

```python
import cgxEastAPI
import cloudgenix_settings 

cgxapi = cgxEasyAPI.cgxEasyAPI(cloudgenix_settings.CLOUDGENIX_AUTH_TOKEN)
```

### To use the API

All API functions are returning status (boolean) and error message (string). A typical call looks like the following:

```python
res,err = easy.net_policy_add_global_prefix("new2", ['1.1.1.1/32'])
if not res:
    print(err)
    sys.exit()
```