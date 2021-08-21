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

    def clean_input(self, line):
        """ Clean any leading traling spaces. Also conver \" to ♞ to be later replaced by "
        """
        line = " ".join(line.split()).replace('\\"',"\u265E")
        return line
    def replace_knight(self, *args):
        """ Replace the ♞ sign with "
        """
        return [
            arg.replace("\u265E",'"')
            for arg in args
        ]
    def do_loko(self, line):
        line = self.clean_input(line)
        print(line)
        print(self.replace_knight(*line.split()))
    def read_file(self, file_name):
        """Read file and return list of lines or error message
        """
        try:
            with open(file_name) as f:
                return f.readlines(), None
        except FileNotFoundError:
            return False, f"File {file_name} not found"
        except PermissionError:
            return False, f"No permission to read {file_name}"

    def do_exit(self, line):
        return True
    def do_EOF(self, line):
        return True
    def do_show(self, line):
        """ Show stuff
        show elements "regualr expression"
        """
        # remove spaces
        clean_line = " ".join(line.split())
        m = re.search(r'elements \"(.*)\"', clean_line)
        if m:
            element_re = m.groups(1)[0]
            elements = db.get_re("name2element", element_re)
            for element in elements:
                print(element['name'])

    def do_add(self, line):
        """ Add somethign to an object 
        add dhcp_pool_option site "<site name>" subnet "<subnet/mask>" opt_vci "<vci>" opt_def "<def>" opt_val "<value>"
        add interface_dhcp_relay element "<element name>" interface "<interface name>" server_ip "<ip address>"
        add interface_dhcp_relay element "<element name>" interface "<interface name>" server_ip "<ip address> source_interface <interface name>"
        add interface_dhcp_relay element_file "<element file name>" interface "<interface name>" server_ip <ip address>"
        add interface_dhcp_relay element_file "<element file name>" interface "<interface name>" server_ip <ip address>" source_interface <interface name>"
        add dhcp_pool_option site "<site name>" subnet "<subnet with /mask>" opt_vci "<vendor class id, can be empty>" opt_def "<opt definition>" opt_val "<opt value>"
        add interface_tag element "<element name>" interface "<interface name>" tag "<tag>"
        add interface_tag element_file "<element file name>" interface "<interface name>" tag "<tag>"
        """

        # clean any white spaces and turn \" to a knight
        clean_line = self.clean_input(line)
        m = re.search(r'interface_dhcp_relay element \"([^\"]+)\" interface \"([^\"]+)\" server_ip \"([^\"]+)\"$', clean_line)
        if m:
            element_re, interface, server_ip = m.groups()
            elements = db.get_re("name2element", element_re)
            for element in elements:
                log.info(f"Working on element {element['name']}")
                res, err = cgxapi.interface_dhcprelay_add(element['name'], interface, server_ip)
                if not res:
                    log.error(err)
            return

        m = re.search(r'interface_dhcp_relay element \"([^\"]+)\" interface \"([^\"]+)\" server_ip \"([^\"]+)\" source_interface \"([^\"]+)\"$', clean_line)
        if m:
            element_re, interface, server_ip, source_interface = m.groups()
            elements = db.get_re("name2element", element_re)
            for element in elements:
                log.info(f"Working on element {element['name']}")
                res, err = cgxapi.interface_dhcprelay_add(element['name'], interface, server_ip, source_interface)
                if not res:
                    log.error(err)
            return

        m = re.search(r'interface_dhcp_relay element_file \"([^\"]+)\" interface \"([^\"]+)\" server_ip \"([^\"]+)\"$', clean_line)
        if m:
            element_file, interface, server_ip = m.groups()
            elements, err = self.read_file(element_file)
            if elements == False:
                log.error(err)
                return
            for element in elements:
                log.info(f"Working on element {element.strip()}")
                res, err = cgxapi.interface_dhcprelay_add(element.strip(), interface, server_ip)
                if not res:
                    log.error(err)
            return

        m = re.search(r'interface_dhcp_relay element_file \"([^\"]+)\" interface \"([^\"]+)\" server_ip \"([^\"]+)\" source_interface \"([^\"]+)\"$', clean_line)
        if m:
            element_file, interface, server_ip, source_interface = m.groups()
            elements, err = self.read_file(element_file)
            if elements == False:
                log.error(err)
                return
            for element in elements:
                log.info(f"Working on element {element.strip()}")
                res, err = cgxapi.interface_dhcprelay_add(element.strip(), interface, server_ip, source_interface)
                if not res:
                    log.error(err)
            return

        m = re.search(r'dhcp_pool_option site \"([^\"]+)\" subnet \"([^\"]+)\" opt_vci \"([^\"]*)\" opt_def \"([^\"]+)\" opt_val \"([^\"]+)\"$', clean_line)
        if m:
            site, subnet, opt_vci, opt_def, opt_val = self.replace_knight(*m.groups())
            res, err = cgxapi.dhcp_pool_add_option(site, subnet, opt_vci, opt_def, opt_val)
            if not res:
                log.error(err)
            return

        m = re.search(r'interface_tag element \"([^\"]+)\" interface \"([^\"]+)\" tag \"([^\"]+)\"$', clean_line)
        if m:
            element_re, interface, tag = self.replace_knight(*m.groups())
            elements = db.get_re("name2element", element_re)
            for element in elements:
                log.info(f"Working on element {element['name']}")
                res, err = cgxapi.interface_tag_add['name'], interface, tag)
                if not res:
                    log.error(err)
            return

        m = re.search(r'interface_tag element_file \"([^\"]+)\" interface \"([^\"]+)\" tag \"([^\"]+)\"$', clean_line)
        if m:
            element_file, interface, tag = self.replace_knight(*m.groups())
            elements, err = self.read_file(element_file)
            if elements == False:
                log.error(err)
                return
            for element in elements:
                log.info(f"Working on element {element.strip()}")
                res, err = cgxapi.interface_tag_add(element.strip(), interface, tag)
                if not res:
                    log.error(err)
            return
        return log.error("Command not found")
        
    def do_delete(self, line):
        """Delete object
        delete dhcp_pool_option site "<site name>" subnet "<pool subnet>" opt_def "<option name>"
        """
        # remove spaces
        clean_line = self.clean_input(line)
        
        m = re.search(r'dhcp_pool_option site \"([^\"]+)\" subnet \"([^\"]+)\" opt_def \"([^\"]+)\"$', clean_line)
        if m:
            site_name, subnet, opt_def_name = self.replace_knight(*m.groups())
            res, err = cgxapi.dhcp_pool_del_option(site_name, subnet, opt_def_name)
            if not res:
                log.error(err)
            return
        return log.error("Command not found")

    def do_set(self, line):
        """change a property of an object
        set interface_security_zone element "<element_name>" interface "<interface_name>" zone "<zone_name>"
        set interface_security_zone element_file "<element_file_name>" interface "<interface_name>" zone "<zone_name>"
        set snmpv3_agent element "<element name>" user_name "<user name>" security_level "<security level>" engine_id  "<engine id>" auth_phrase "<auth phrase>" auth_type "<auth type>" enc_phrase "<encryption phrase>" enc_type "<encryption type>"
        """
        
        # remove spaces
        clean_line = " ".join(line.split())

        m = re.search(r'interface_security_zone element \"(.*)\" interface \"(.*)\" zone \"(.*)\"', clean_line)
        if m:
            element_re, interface, zone = m.groups()
            elements = db.get_re("name2element", element_re)
            for element in elements:
                log.info(f"Working on element {element['name']}")
                res, err = cgxapi.set_interface_zone(element['name'], interface, zone)
                if not res:
                    log.error(err)
            return
        m = re.search(r'interface_security_zone element_file \"(.*)\" interface \"(.*)\" zone \"(.*)\"', clean_line)
        if m:
            element_file, interface, zone = m.groups()
            elements, err = self.read_file(element_file)
            if elements == False:
                log.error(err)
                return
            for element in elements:
                log.info(f"Working on element {element.strip()}")
                res, err = cgxapi.set_interface_zone(element.strip(), interface, zone)
                if not res:
                    log.error(err)
            return

        m = re.search(r'snmpv3_agent element \"([^\"]+)\" user_name \"([^\"]+)\" security_level \"([^\"]+)\" engine_id \"([^\"]*)\" auth_phrase \"([^\"]*)\" auth_type \"([^\"]*)\" enc_phrase \"([^\"]*)\" enc_type \"([^\"]*)\"', clean_line)
        if m:
            element_re, user_name, security_level, engine_id, auth_phrase , auth_type, enc_phrase, enc_type= self.replace_knight(*m.groups())
            elements = db.get_re("name2element", element_re)
            for element in elements:
                log.info(f"Working on element {element['name']}")
                res, err = cgxapi.set_snmpv3_agent(element['name'], user_name, security_level, engine_id, auth_phrase , auth_type, enc_phrase, enc_type)
                if not res:
                    log.error(err)
            return
        m = re.search(r'snmpv3_agent element_file \"([^\"]+)\" user_name \"([^\"]+)\" security_level \"([^\"]+)\" engine_id \"([^\"]*)\" auth_phrase \"([^\"]*)\" auth_type \"([^\"]*)\" enc_phrase \"([^\"]*)\" enc_type \"([^\"]*)\"', clean_line)
        if m:
            element_file, user_name, security_level, engine_id, auth_phrase , auth_type, enc_phrase, enc_type= self.replace_knight(*m.groups())
            elements, err = self.read_file(element_file)
            if elements == False:
                log.error(err)
                return
            for element in elements:
                log.info(f"Working on element {element.strip()}")
                res, err = cgxapi.set_snmpv3_agent(element['name'], user_name, security_level, engine_id, auth_phrase , auth_type, enc_phrase, enc_type)
                if not res:
                    log.error(err)
            return
        return log.error("Command not found")

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

