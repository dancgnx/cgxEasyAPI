import cloudgenix
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
import logging
import db
from pprint import pprint as pp
import sys

#init logging
log = logging.getLogger('cgxEasyAPI').addHandler(logging.NullHandler())

# init db

class cgxEasyAPI:
    def __init__(self, sdk, debug=0):
        self.sdk = sdk
        self.debug = debug
        self.interfaces = {} # interface cache
    
    def build_interfaces_cache(self, site_id, element_id):
        """Build interfaces cache 
        :param site_id: The site ID of the element 
        :param type: str
        :param element_id: The element for which we need the interface list for
        :param type: str
        """
        # shortcut
        interfaces = self.interfaces
        sdk = self.sdk

        # get the list of interfaces for the element
        res = sdk.get.interfaces(site_id, element_id)
        if not res:
            jd_detailed(res)
            sys.exit()
        interfaces[element_id] = res.cgx_content["items"]

    def get_interfaces(self, site_id, element_id):
        """Returns interfaces from the cache. If the cache is empty, the cache will be recreated
        :param site_id: The site ID of the element 
        :param type: str
        :param element_id: The element for which we need the interface list for
        :param type: str
        :return interface list: A list with all the interfaces configured for the element
        :rtype list:
        """
        # shortcut
        interfaces = self.interfaces

        # check if we have a cache entry
        if not element_id in interfaces:
            self.build_interfaces_cache(site_id, element_id)
        
        return interfaces[element_id]
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

    def interface_dhcprelay_add(self, element_name, interface_name, dhcprelay_ip):
        """Add DHCP relay server to an interface
        :param element_name: The name of the ION device
        :type element_name: str
        :param interface_name: The name of the interface to add DHCP relay to
        :type interafce_name: str
        :param dhcprelay_ip: DHCP server IP address to add
        :type dcprelay_ip: str in IP address format, without mask
        :return: Success, ErrMSG
        :rtype Success: Boolean
        :rtype ErrMSG: String
        """
        # shortcut
        sdk = self.sdk

        # get ION from cache and get interface list
        element = db.fetch("name2element", element_name)
        if not element:
            return False, "Can't find element"
        interfaces = self.get_interfaces(element['site_id'], element['id'])

        # find interface name 
        for interface in interfaces:
            if interface['name'] == interface_name:
                break
        else:
            return False, "Can't find interface"
        
        # if DHCP server list is empty, create new entry if not, add the server to the list
        if interface['dhcp_relay']:
            interface['dhcp_relay']['server_ips'] = list(set(interface['dhcp_relay']['server_ips']+[dhcprelay_ip]))
        else:
            interface['dhcp_relay']= {
                "server_ips": [
                    dhcprelay_ip
                ],
                "enabled": True,
                "option_82": {
                    "enabled": False,
                    "circuit_id": None,
                    "remote_id": None,
                    "reforwarding_policy": "replace"
                },
                "source_interface": interface['id']
            }
        
        # update the interface
        res = sdk.put.interfaces(element['site_id'], element['id'], interface['id'], interface)
        if not res:
            err = f"--- Can't update interface: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err
        
        # refresh interfaces for the elemnt as we changed an attribute
        self.build_interfaces_cache(element['site_id'], element['id'])

        return True, ""

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
    easy = cgxEasyAPI(sdk, debug=1)
    res, err= easy.interface_dhcprelay_add("Dan 2k", "3", "10.2.3.4")
    print(res, err)
    res, err= easy.interface_dhcprelay_add("Dan 2k", "3", "10.2.3.5")
    print(res, err)
