#!/usr/bin/env python3
import cloudgenix
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
from pprint import pprint as pp
import sys
import cmd
import cgxEasyAPI
import logging
import re
import db

log = None
cgxapi = None
class cgxcmd(cmd.Cmd):
    SET_COMMANDS = ["interface_security_zone", "snmpv3_agent", ]
    ADD_COMMANDS = ["dhcp_pool_option", "interface_tag", "interface_dhcp_relay"]
    DELETE_COMMANDS = ['dhcp_pool_option', "dhcp_pool"]
    def do_exit(self, line):
        return True
    def do_EOF(self, line):
        return True
    def do_set(self, line):
        """change a property of an object
        set interface_security_zone element <element_name> interface <interface_name> zone <zone_name>
        set interface_security_zone element_file <element_file_name> interface <interface_name> zone <zone_name>
        """
        
        # remove spaces
        clean_line = " ".join(line.split())
        print(clean_line)
        m = re.search(r'interface_security_zone element \"(.*)\" interface \"(.*)\" zone \"(.*)\"', clean_line)
        if m:
            element_re, interface, zone = m.groups()
            elements = db.get_re("name2element", element_re)
            for element in elements:
                res, err = cgxapi.set_interface_zone(element['name'], interface, zone)
                if not res:
                    log.error(err)

    def complete_set(self, text, line, begidx, endidx):
        #print(f"\n\ntext {text}\nbegindx {begidx} endidx {endidx}")
        # remove spaces
        # clean_line = " ".join(line.split())
        # words = clean_line.split(" ")
        # if clean_line == "set interface_security_zone":
        #     completions = ['elements', 'element_file']
        # if len(words) == 2 and words[1] == "interface_security_zone":
        #     if not text:
        #         completions = ['element_file', 'elements'][:]
        #     else:
        #         completions = [
        #             f for f in ['element_file', 'elements']
        #             if f.startswith(text)
        #         ]
        if not text:
            completions = self.SET_COMMANDS[:]
        else:
            completions = [
                f for f in self.SET_COMMANDS
                if f.startswith(text)
            ]
        return completions

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

    # init cgxEasyAPI
    cgxapi = cgxEasyAPI.cgxEasyAPI(sdk)
    cgxcmd().cmdloop()

