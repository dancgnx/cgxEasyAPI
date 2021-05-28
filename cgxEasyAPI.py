import cloudgenix
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
import logging
import db
from pprint import pprint as pp

#init logging
log = logging.getLogger('cgxEasyAPI').addHandler(logging.NullHandler())

# init db

class cgxEasyAPI:
    def __init__(self, sdk, debug=0):
        self.sdk = sdk
        self.debug = debug
    
    def dhcp_pool_delete(self, site_name, subnet):
        """Delete DHCP pool
        :param site_name: the site name from where to delete the DHCP pool
        :type site_name: str
        :param subnet: the network for which the dhcp pool is for. Exmample: "192.168.1.0/24"
        :type subnet: str 
        :return: Success, ErrMSG
        :rtype Success: Boolean
        :rtype ErrMSG: String
        """
        # shortcut
        sdk = self.sdk

        # get site info
        site = db.fetch("name2site", site_name)
        if not site:
            return False, "Site not found"

        # find the dhcp scoped
        for dhcpserver in sdk.get.dhcpservers(site['id']).cgx_content['items']:
            if dhcpserver['subnet'] == subnet:
                break 
        else:
            return False, "DHCP subnet not found"
        
        # delete DHCP scope
        log.info(f"Deleting DHCP scope of subnet {subnet} at site {site_name}")
        res = sdk.delete.dhcpservers(site['id'], dhcpserver['id'])
        if not res:
            err = f"--- Can't delete scope: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err

        return True, ""

    def interface_dhcprelay_add(self, ION_name, interface_name, dhcprelay):
        # shortcut
        sdk = self.sdk

        # get ION



if __name__ == "__main__":
    # init logging
    cloudgenix.api_logger.setLevel(logging.WARN)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("cgxEasyAPI").setLevel(logging.INFO)
    log = logging.getLogger("TEST")

    # init API
    sdk = cloudgenix.API()
    res = sdk.interactive.use_token(cloudgenix_settings.CLOUDGENIX_AUTH_TOKEN)
    if not res:
        log.critical("Can't Login. Check authtoken")
        jd_detailed(res)
        sys.exit()
    
    #init db
    db.init(sdk)

    #delete dhcp 
    easy = cgxEasyAPI(sdk)
    res, err= easy.dhcp_pool_delete("CA-1025","192.168.0.0/24")
    print(res, err)
