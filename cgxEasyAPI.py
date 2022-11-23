import cloudgenix
import ipcalc
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
    def __init__(self, auth_token, debug=0, ssl_verify=True):
        """ constrat easyAPI object
        """
        # init logging
        cloudgenix.api_logger.setLevel(logging.WARN)
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("requests").setLevel(logging.WARN)
        logging.getLogger("urllib3").setLevel(logging.WARN)
        logging.getLogger("cgxEasyAPI").setLevel(logging.INFO)
        global log
        log = logging.getLogger("cgxEasyAPI")

        # init API
        sdk = cloudgenix.API(ssl_verify=ssl_verify)
        res = sdk.interactive.use_token(auth_token)
        if not res:
            log.critical("Can't Login. Check authtoken")
            jd_detailed(res)
            sys.exit()

        self.sdk = sdk
        self.debug = debug
        self.interfaces = {} # interface cache
        db.init(sdk)
    
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

    def dhcp_pool_del_option(self, site_name, subnet, opt_def_name):
        """Add dhcp pool option
        :param site_name: The site to add the option to.
        :param type: str
        :param subnet: IPv4 subnet. This will be used to indetify
        :param type: str - 10.0.0.0/24
        :param opt_def_name: Option defenition. In the following option "option my_43 code 43 = text" the definiton name is "my_43"   
        :param type: str - my_43
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
        
        # find the options
        for option in dhcpserver['custom_options']:
            if f"option {opt_def_name} code" in option['option_definition']:
                break
        else:
            return False, "Option not found"

        # remove the option
        dhcpserver['custom_options'].remove(option)
        res = sdk.put.dhcpservers(site['id'], dhcpserver['id'], dhcpserver)
        if not res:
            err = f"--- Can't remove DHCP option: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err

        return True, ""

    def dhcp_pool_add_option(self, site_name, subnet, opt_vci, opt_def, opt_val):
        """Add dhcp pool option
        :param site_name: The site to add the option to.
        :param type: str
        :param subnet: IPv4 subnet. This will be used to indetify
        :param type: str - 10.0.0.0/24
        :param opt_vci: vendor class indetifier
        :param type: str
        :param opt_def: Option defenition
        :param type: str - option my_43 code 43 = text
        :param opt_val: Option value
        :param type: str - option my_43 "as"
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
        
        # if not options alread configure, create an empty list
        if not dhcpserver['custom_options']:
            dhcpserver['custom_options'] = []
        
        # add option 
        dhcpserver['custom_options'].append(
            {
                "vendor_class_identifier" : opt_vci,
                "option_definition": opt_def,
                "option_value": opt_val
            }
        )

        res = sdk.put.dhcpservers(site['id'], dhcpserver['id'], dhcpserver)
        if not res:
            err = f"--- Can't add DHCP option: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err

        return True, ""
        
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

    def interface_tag_add(self, element_name, interface_name, tag):
        """Add tag to an interface
        :param element_name: The name of the ION device
        :type element_name: str
        :param interface_name: The name of the interface to add DHCP relay to
        :type interafce_name: str
        :param tag: tag to add
        :type tag: str - "prisma_region:us-west1:1"
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
        
        if interface['tags'] == None:
            interface['tags'] = []

        if tag in interface['tags']:
            return False, "tag already exists"
        
        interface['tags'].append(tag)
        res = sdk.put.interfaces(element['site_id'], element['id'], interface['id'], interface)
        if not res:
            err = f"--- Can't add tag: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err

        # refresh interfaces for the elemnt as we changed an attribute
        self.build_interfaces_cache(element['site_id'], element['id'])

        return True, ""

    def set_interface_zone(self, element_name, interface_name, zone_name):
        """ Place an interface into a zone. 
        If an interface is already in a zone, th escript will pull it out of that zone
        :param element_name: The name of the ION device
        :type element_name: str
        :param interface_name: The name of the interface to add DHCP relay to
        :type interafce_name: str
        :param zone_name: The name of the zone to attach the interface to
        :type zone_name: str
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

        # create a security zone database
        securityzones = sdk.get.securityzones().cgx_content['items']
        name2zone = {}
        zone2name = {}
        for securityzone in securityzones:
            name2zone[securityzone['name']] = securityzone
            zone2name[securityzone['id']] = securityzone
        
        if zone_name not in name2zone:
            return False, f"Can't find zone {zone_name}"
        else:
            zone = name2zone[zone_name]
        
        # check if interface already assign into a zone
        zone_bindings  = sdk.get.elementsecurityzones(element['site_id'], element['id']).cgx_content['items']
        for zone_binding in zone_bindings:
            if zone_binding['zone_id'] == zone['id']:
                continue
            if zone_binding['interface_ids'] and interface['id'] in zone_binding['interface_ids']:
                log.info(f"--- Interface found in zone {zone2name[zone_binding['zone_id']]['name']}")
                # remove the interface and update the zone binding
                zone_binding['interface_ids'].remove(interface['id'])
                if zone_binding['interface_ids'] == []:
                    zone_binding['interface_ids'] = None
                # scan through all the bindings for the zone, if all are empty then delete otherwise update
                if zone_binding['interface_ids'] == None and \
                    zone_binding['lannetwork_ids'] == None and\
                    zone_binding['waninterface_ids'] == None and\
                    zone_binding['wanoverlay_ids'] == None:
                    # delete zone_binding
                    log.info(f"--- After removing interface from zone {zone2name[zone_binding['zone_id']]['name']} there are no binding left. Deleting the binding")
                    res = sdk.delete.elementsecurityzones(element['site_id'], element['id'], zone_binding['id'])
                    if not res:
                        err = f"--- Can't delete zone binding {zone2name[zone_binding['zone_id']]['name']}: {sdk.pull_content_error(res)}"
                        log.error(err)
                        if self.debug:
                            jd_detailed(res)
                        return False, err
                else:
                    # update the zone_binding
                    log.info(f"--- Removing interface from zone {zone2name[zone_binding['zone_id']]['name']}")
                    res = sdk.put.elementsecurityzones(element['site_id'], element['id'], zone_binding['id'], zone_binding)
                    if not res:
                        err = f"--- Can't update zone binding for {zone2name[zone_binding['zone_id']]['name']}: {sdk.pull_content_error(res)}"
                        log.error(err)
                        if self.debug:
                            jd_detailed(res)
                        return False, err

        # find existing zone bindings. If found, just add the interface and update, else create a new zone binding
        for zone_binding in zone_bindings:
            if zone['id'] == zone_binding['zone_id']:
                # create a list of noze bindings is not there
                if not zone_binding['interface_ids']:
                    zone_binding['interface_ids'] = [interface['id']]
                else:
                    # check if interface already there
                    if interface['id'] in zone_binding['interface_ids']:
                        log.info(f"--- Interface {interface['name']} already bound to zone {zone_name}")
                        return True, "interface already bound"
                    zone = zone_binding['interface_ids'].append(interface['id'])
                # update the zone_binding
                log.info(f"--- Adding interface {interface['name']} to zone {zone_name}")
                res = sdk.put.elementsecurityzones(element['site_id'], element['id'], zone_binding['id'], zone_binding)
                if not res:
                    err = f"--- Can't update zone binding for {zone_name}: {sdk.pull_content_error(res)}"
                    log.error(err)
                    if self.debug:
                        jd_detailed(res)
                    return False, err
                break
        else:
            # create a new zone binding and post
            log.info(f"--- Creating zone binding with interface {interface['name']} bound to zone {zone_name}")
            zone_binding = {
                "zone_id": zone['id'],
                "lannetwork_ids": [],
                "interface_ids": [interface['id']],
                "wanoverlay_ids": [],"waninterface_ids": []
            }
            res = sdk.post.elementsecurityzones(element['site_id'], element['id'], zone_binding)
            if not res:
                err = f"--- Can't create zone bindings for {zone_name}: {sdk.pull_content_error(res)}"
                log.error(err)
                if self.debug:
                    jd_detailed(res)
                return False, err

        return True, ""

    def interface_dhcprelay_add(self, element_name, interface_name, dhcprelay_ip, source_interface_name=None):
        """Add DHCP relay server to an interface
        :param element_name: The name of the ION device
        :type element_name: str
        :param interface_name: The name of the interface to add DHCP relay to
        :type interafce_name: str
        :param dhcprelay_ip: DHCP server IP address to add
        :type dcprelay_ip: str in IP address format, without mask
        :param source_interface_name: The name of the interface to source the DHCP requests. If None, the source interface would be the interface itself.
        :type source_interafce_name: str
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
        
        # find source_interface
        if source_interface_name:
            for source_interface in interfaces:
                if source_interface['name'] == source_interface_name:
                    break
            else:
                return False, "Can't find source interface name"
        else:
            source_interface = None

        
        # if DHCP server list is empty, create new entry if not, add the server to the list
        if interface['dhcp_relay']:
            interface['dhcp_relay']['server_ips'] = list(set(interface['dhcp_relay']['server_ips']+[dhcprelay_ip]))
        else:
            source_interface_id = interface['id'] if not source_interface else source_interface['id']
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
                "source_interface": source_interface_id
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
        log.info("DHCP relay added")
        return True, ""

    def set_snmpv3_agent(self, element_name, user_name, security_level, engine_id, auth_phrase, auth_type, enc_phrase, enc_type):
        """ update or create SNMPv3 agent
        :param element_name: the device to set snmpv3 agent for
        :ptype element_name: str
        :param user_name: SNMPv3 username. This will be the primary key for searchign for existing configuration
        :ptype element_name: str
        :param security_level: What security level for SNMPv3. can be 'noauth', 'auth' or 'private'
        :ptype security_level: str
        :param engine_id: SNMP engine ID. Must be even number of hex digits
        :ptype engine_id: hex string
        :param auth_phrase: auth password
        :ptype auth_phrase: str
        :param auth_type: Authentication type. Can be "md5" or "sha" or "none"
        :ptype auth_type: str
        :param enc_phrase: necryption password
        :ptype enc_phrase: str
        :param enc_type: encryption type. Can be "des" or "aes" or "none
        :ptype enc_type: str
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
        
        # get existing SNMP configuration
        snmpagents = sdk.get.snmpagents(element['site_id'], element['id']).cgx_content['items']

        # if no configuration found, create a new one
        if snmpagents == []:
            log.info("--- No SNMP agents found. Creating a new one")
            snmpagent = {
                "tags": None,
                "description": None,
                "v2_config": {
                    "enabled": False,
                    "community": None
                },
                "v3_config": {
                    "enabled": True,
                    "users_access": [{
                        "user_name": user_name, 
                        "engine_id": engine_id,
                        "security_level": security_level,
                        "auth_type": auth_type,
                        "auth_phrase": auth_phrase,
                        "enc_type": enc_type,
                        "enc_phrase": enc_phrase
                    }]
                }
            }

            res = sdk.post.snmpagents(element['site_id'], element['id'],snmpagent)
            if not res:
                err = f"--- Can't create SNMP agent: {sdk.pull_content_error(res)}"
                log.error(err)
                if self.debug:
                    jd_detailed(res)
                return False, err
            return True, ""
        
        snmpagent = snmpagents[0]
        # check if there are any entries 
        if not snmpagent['v3_config']:
            log.info("--- Creating SNMPv3")
            snmpagent['v3_config'] = {
                "enabled": True,
                "users_access": [
                    {
                        "user_name": user_name, 
                        "engine_id": engine_id,
                        "security_level": security_level,
                        "auth_type": auth_type,
                        "auth_phrase": auth_phrase,
                        "enc_type": enc_type,
                        "enc_phrase": enc_phrase
                    }
                ]
            }
        else:
            # search if username already configured
            for user in snmpagent['v3_config']['users_access']:
                if user['user_name'] == user_name:
                    log.info("--- Username found. Updating existing user")
                    user["engine_id"]= engine_id
                    user["security_level"]= security_level
                    user["auth_type"]= auth_type
                    user["auth_phrase"]= auth_phrase
                    user["enc_type"]= enc_type
                    user["enc_phrase"]= enc_phrase
                    break
            else:
                # user not found. add it to the list
                log.info("--- Username not found. Creating new entry")
                snmpagent['v3_config']['users_access'].append({
                        "user_name": user_name, 
                        "engine_id": engine_id,
                        "security_level": security_level,
                        "auth_type": auth_type,
                        "auth_phrase": auth_phrase,
                        "enc_type": enc_type,
                        "enc_phrase": enc_phrase
                })
        
        # update SNMP agent 
        res = sdk.put.snmpagents(element['site_id'], element['id'],snmpagent['id'], snmpagent)
        if not res:
            err = f"--- Can't update SNMP agent: {sdk.pull_content_error(res)}"
            log.error(err)
            if self.debug:
                jd_detailed(res)
            return False, err

        return True, ""
    def net_policy_add_global_prefix(self, prefix_name, prefixes, description=None, tags=[]):
        """ add prefixes to network policy global prefixlist
        :param prefix_name: The name of the prefix filter to add prefixes to, or to create if doesn't exists
        :type prefix_name: str
        :param prefixes: Prefixes in the form of ip/net_len. Example "10.2.3.0/8" or "13.6.8.5/32"
        :type prefixes: list
        :return: Success, ErrMSG
        :rtype Success: Boolean
        :rtype ErrMSG: String
        """
        # shortcut
        sdk = self.sdk

        # get a list of existing prefixlists. Maybe its alread exists
        for prefix in sdk.get.networkpolicyglobalprefixes().cgx_content['items']:
            if prefix['name'] == prefix_name:
                # prefix found, add prefixes to the list
                prefixes.extend(prefix['ipv4_prefixes'])
                prefix['ipv4_prefixes'] = list(set(prefixes))
                res = sdk.put.networkpolicyglobalprefixes(prefix['id'], prefix)
                if not res:
                    err = f"--- Failed to update global prefixlist: {sdk.pull_content_error(res)}"
                    if self.debug:
                        log.error(err)
                        jd_detailed(res)
                    return False, err
                break
        else:
            # prefix not found, we need to create a new one
            prefix = {
                "name":prefix_name,
                "tags":tags,
                "ipv4_prefixes":prefixes,
                "description": description
            }
            res = sdk.post.networkpolicyglobalprefixes(prefix)
            if not res:
                err = f"--- Failed to create global prefixlist: {sdk.pull_content_error(res)}"
                if self.debug:
                    log.error(err)
                    jd_detailed(res)
                return False, err
        return True, ""
    def interface_add_subinterface(self, element_name, parent_interface_name, vlan, IP_Address, scope, description="", native_vlan=False, used_for="lan", type="static"):
        """Add sub interface
        :param element_name: The name of the ION device
        :type element_name: str
        :param parent_interface_name: The name of the parent interface where the subinterface is added to
        :type interafce_name: str
        :param vlan: VLAN ID
        :type vlan: integer 1-4095
        :param IP_Address: Sub interface IP address
        :type str: ip/bit length notation
        :param scope: is the scope global or local 
        :type str: global/local
        :param native_vlan: Is the subinterface is untagged. Default: false
        :type boolean:
        :param description: a short description of the port
        :type str:
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
            if interface['name'] == parent_interface_name:
                break
        else:
            return False, "Can't find interface"
        
        # check if sub interface exists
        for sub_interface in interfaces:
            if sub_interface['name'] == f"{parent_interface_name}.{vlan}":
                return False, "Sub interface already exists"

        # create the sub interface
        new_interface = {
            "type":"subinterface",
            "attached_lan_networks":None,"site_wan_interface_ids":None,"name":None,
            "description":description,
            "tags":None,"mac_address":None,"mtu":0,
            "ethernet_port":{"full_duplex":False,"speed":0},"admin_up":True,"nat_address":None,"nat_port":0,"nat_zone_id":None,"nat_pools":None,
            "used_for":used_for,
            "bypass_pair":None,"bound_interfaces":None,
            "sub_interface":{"vlan_id":vlan,"native_vlan":native_vlan},
            "pppoe_config":None,"secondary_ip_configs":None,"static_arp_configs":None,"dhcp_relay":None,
            "parent": interface['id'],
            "network_context_id":None,"ipfixcollectorcontext_id":None,"ipfixfiltercontext_id":None,"service_link_config":None,
            "scope":scope,
            "devicemgmt_policysetstack_id":None,"directed_broadcast":False
        }

        if type == "static":
            new_interface["ipv4_config"]={"dhcp_config":None,"dns_v4_config":None,"routes":None,"static_config":{"address":IP_Address},"type":"static"},
        else:
            new_interface["ipv4_config"]={"dhcp_config":None,"dns_v4_config":None,"routes":None,"static_config":None,"type":"dhcp"},

        
        res = sdk.post.interfaces(element['site_id'], element['id'], new_interface)
        if not res:
            err = f"--- Can't add sub interface: {sdk.pull_content_error(res)}"
            if self.debug:
                log.error(err)
                jd_detailed(res)
            return False, err

        # refresh interfaces for the elemnt as we changed an attribute
        self.build_interfaces_cache(element['site_id'], element['id'])

        return True, ""
    def sec_policy_add_local_prefix(self, prefix_name, site_name, prefixes, description=None, tags=[]):
        """ add prefixes to security policy local prefixlist
        :param prefix_name: The name of the prefix filter to add prefixes to, or to create if doesn't exists
        :type prefix_name: str
        :param site_name: The name of the site to add prefix to, o create it if doesn't exists
        :type prefix_name: str
        :param prefixes: Prefixes in the form of ip/net_len. Example "10.2.3.0/8" or "13.6.8.5/32"
        :type prefixes: list
        :return: Success, ErrMSG
        :rtype Success: Boolean
        :rtype ErrMSG: String
        """
        # shortcut
        sdk = self.sdk

        # check if tags is a list
        if not type(tags) is list:
            return False, "tag paramter should be a list of strings"

        # check if prefixes are valid
        for prefix in prefixes:
            try:
                ipcalc.IP(prefix)
            except ValueError:
                return False,f"{prefix} is not a valid"

        # get site info
        site = db.fetch("name2site", site_name)
        if not site:
            return False, "Site not found"

        # get a list of existing prefixlists. Maybe its alread exists
        for prefix in sdk.get.ngfwsecuritypolicylocalprefixes().cgx_content['items']:
            if prefix['name'] == prefix_name:
                # prefix found, add prefixes to the list
                break
        else:
            # prefix not found, we need to create a new one
            prefix = {
                "name":prefix_name,
                "tags":tags,
                "description": description
            }
            res = sdk.post.ngfwsecuritypolicylocalprefixes(prefix)
            if not res:
                err = f"--- Failed to local security prefixlist: {sdk.pull_content_error(res)}"
                if self.debug:
                    log.error(err)
                    jd_detailed(res)
                return False, err
            prefix = res.cgx_content

        prefix_id = prefix['id']

        # get a list of site local prefixes. Maybe it already exists
        for site_prefix in sdk.get.site_ngfwsecuritypolicylocalprefixes(site['id']).cgx_content['items']:
            if site_prefix['prefix_id'] == prefix_id:
                # local prefix found, add prefixes to the list
                prefixes.extend(site_prefix['ipv4_prefixes'])
                site_prefix['ipv4_prefixes'] = list(set(prefixes))
                res = sdk.put.site_ngfwsecuritypolicylocalprefixes(site['id'], site_prefix['id'], site_prefix)
                if not res:
                    err = f"--- Failed to update local security prefixlist: {sdk.pull_content_error(res)}"
                    if self.debug:
                        log.error(err)
                        jd_detailed(res)
                    return False, err
                break
        else:
            # local prefix not found, lets create one
            local_prefix = {
                    "ipv4_prefixes": prefixes,
                    "prefix_id": prefix_id,
                    "tags": tags
                        
                    }
            res = sdk.post.site_ngfwsecuritypolicylocalprefixes(site['id'], local_prefix)
            if not res:
                err = f"--- Failed to create local security prefixlist: {sdk.pull_content_error(res)}"
                if self.debug:
                    log.error(err)
                    jd_detailed(res)
                return False, err
        return True, ""
    
    def secure_fabric_add_tunnels(self, site1_name, site2_name):
        """ create site to site tunnels across all avialble paths
        :param site1_name: Site name 1
        :type prefix_name: str
        :param site2_name: Site name 2
        :type prefix_name: str
        :return: Success, ErrMSG
        :rtype Success: Boolean
        :rtype ErrMSG: String
        """
        # shortcut
        sdk = self.sdk

        # get siter1 info
        site1 = db.fetch("name2site", site1_name)
        if not site1:
            return False, "Site1 not found"
        # get siter2 info
        site2 = db.fetch("name2site", site2_name)
        if not site1:
            return False, "Site1 not found"
        
        # get circuit labels for both sites
        site1_waninterfaces = sdk.get.waninterfaces(site1['id']).cgx_content['items']
        site2_waninterfaces = sdk.get.waninterfaces(site2['id']).cgx_content['items']

        # create anynet links
        for s1_waninterface in site1_waninterfaces:
            for s2_waninterface in site2_waninterfaces:
                # skip if trying to bring up private to public
                if s1_waninterface['type'] != s2_waninterface['type']:
                    continue
                data = {
                        "name":None, "description":None, "tags":None,
                        "ep1_site_id":site1['id'],"ep1_wan_if_id":s1_waninterface['id'],
                        "ep2_site_id":site2['id'],"ep2_wan_if_id":s2_waninterface['id'],
                        "admin_up":True,"forced":True,"type":None,"vpnlink_configuration":None}
                res = sdk.post.tenant_anynetlinks(data)
                if not res:
                    if res.status_code == 400:
                        # link alraedy there
                        if 'DUP_ANYNET' in res.text:
                            if self.debug:
                                log.info(f"VPN between {site1_name} {s1_waninterface['name']} and {site2_name} {s2_waninterface['name']} already exists. Continuing")
                            continue
                        else:
                            pp(res.json())
                            pp(s1_waninterface)
                            pp(s2_waninterface)
                        

        return True, ""

if __name__ == "__main__":
    # init logging
    cloudgenix.api_logger.setLevel(logging.WARN)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("cgxEasyAPI").setLevel(logging.INFO)
    log = logging.getLogger("TEST")

    #delete dhcp 
    easy = cgxEasyAPI(cloudgenix_settings.CLOUDGENIX_AUTH_TOKEN, debug=1)
    res, err = False, "Test"
    #res, err= easy.interface_dhcprelay_add("Dan 2k", "3", "10.2.3.4", source_interface_name = "2")
    #res, err = easy.dhcp_pool_add_option("Dan Home", "1.2.3.0/24", "", "option my_44 code 44 = text", 'option my_44 "as"')
    #res, err = easy.dhcp_pool_del_option("Dan Home", "1.2.3.0/24", "my_44")
    #res, err = easy.set_snmpv3_agent("Dan 2k", "dantest", "auth", "12423423423422", "kokoloko", "sha", None, "none")
    #res, err = easy.set_snmpv3_agent("Dan 2k", "dantest", "auth", "12423423423422", "kokoroko", "sha", None, "none")
    #res, err = easy.set_snmpv3_agent("Ansh-Hub", "uSNMP", "auth", "12423423423422", "kokoroko", "sha", None, "none")
    #res,err = easy.sec_policy_add_local_prefix("easy2", "Dan Home",['172.16.0.0/12', '192.168.0.0/16', '10.0.0.0/8'])
    #print(res, err)
    #res,err = easy.sec_policy_add_local_prefix("easy2","Dan Home",['172.16.0.0/12'])
    #print(res, err)
    res,err = easy.secure_fabric_add_tunnels("PanDan - Branch", "1Dmitry-Branch-Rancho")
    print(res,err)
