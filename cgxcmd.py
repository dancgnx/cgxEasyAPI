#!/usr/bin/env python3
import cloudgenix
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
from pprint import pprint as pp
import sys
import cmd
import cgxEasyAPI
import logging


if __name__ == "__main__":
    # init logging
    cloudgenix.api_logger.setLevel(logging.WARN)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("cgxEasyAPI").setLevel(logging.INFO)
    log = logging.getLogger("cgxcmd")

    # init API
    sdk = cloudgenix.API()
    res = sdk.interactive.use_token(cloudgenix_settings.CLOUDGENIX_AUTH_TOKEN)
    if not res:
        log.critical("Can't Login. Check authtoken")
        jd_detailed(res)
        sys.exit()

