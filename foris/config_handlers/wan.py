# Foris - web administration interface for OpenWrt based on NETCONF
# Copyright (C) 2017 CZ.NIC, z.s.p.o. <http://www.nic.cz>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .base import BaseConfigHandler
from foris import fapi, validators
from foris.state import current_state
from foris.form import (
    Checkbox,
    Dropdown,
    Textbox,
)

from foris.utils.translators import gettext_dummy as gettext, _


class WanHandler(BaseConfigHandler):
    userfriendly_title = gettext("WAN")

    def __init__(self, *args, **kwargs):
        # Do not display "none" options for WAN protocol if hide_no_wan is True
        self.hide_no_wan = kwargs.pop("hide_no_wan", False)
        super(WanHandler, self).__init__(*args, **kwargs)

    def _convert_backend_data_to_form_data(self, data):
        res = {}

        # WAN
        res["proto"] = data["wan_settings"]["wan_type"]
        if res["proto"] == "dhcp":
            res["hostname"] = data["wan_settings"]["wan_dhcp"].get("hostname", "")
        elif res["proto"] == "static":
            res["ipaddr"] = data["wan_settings"]["wan_static"]["ip"]
            res["netmask"] = data["wan_settings"]["wan_static"]["netmask"]
            res["gateway"] = data["wan_settings"]["wan_static"]["gateway"]
            res["ipv4_dns1"] = data["wan_settings"]["wan_static"].get("dns1", "")
            res["ipv4_dns2"] = data["wan_settings"]["wan_static"].get("dns2", "")
        elif res["proto"] == "pppoe":
            res["username"] = data["wan_settings"]["wan_pppoe"]["username"]
            res["password"] = data["wan_settings"]["wan_pppoe"]["password"]

        # WAN6
        res["wan6_proto"] = data["wan6_settings"]["wan6_type"]
        if res["wan6_proto"] == "static":
            res["ip6addr"] = data["wan6_settings"]["wan6_static"]["ip"]
            res["ip6prefix"] = data["wan6_settings"]["wan6_static"]["network"]
            res["ip6gw"] = data["wan6_settings"]["wan6_static"]["gateway"]
            res["ipv6_dns1"] = data["wan6_settings"]["wan6_static"].get("dns1", "")
            res["ipv6_dns2"] = data["wan6_settings"]["wan6_static"].get("dns2", "")
        elif res["wan6_proto"] == "dhcpv6":
            res["ip6duid"] = data["wan6_settings"]["wan6_dhcpv6"]["duid"]

        # MAC
        res["custom_mac"] = data["mac_settings"]["custom_mac_enabled"]
        res["macaddr"] = data["mac_settings"].get("custom_mac", "")

        return res

    def _convert_form_data_to_backend_data(self, data):
        res = {"wan_settings": {}, "wan6_settings": {}, "mac_settings": {}}

        # WAN
        res["wan_settings"]["wan_type"] = data["proto"]
        if data["proto"] == "dhcp":
            hostname = data.get("hostname", False)
            res["wan_settings"]["wan_dhcp"] = {"hostname": hostname} if hostname else {}
        elif data["proto"] == "static":
            res["wan_settings"]["wan_static"] = {}
            res["wan_settings"]["wan_static"]["ip"] = data["ipaddr"]
            res["wan_settings"]["wan_static"]["netmask"] = data["netmask"]
            res["wan_settings"]["wan_static"]["gateway"] = data["gateway"]
            dns1 = data.get("ipv4_dns1", None)
            dns2 = data.get("ipv4_dns2", None)
            res["wan_settings"]["wan_static"].update(
                {k: v for k, v in {"dns1": dns1, "dns2": dns2}.items() if v})
        elif data["proto"] == "pppoe":
            res["wan_settings"]["wan_pppoe"] = {}
            res["wan_settings"]["wan_pppoe"]["username"] = data["username"]
            res["wan_settings"]["wan_pppoe"]["password"] = data["password"]

        # WAN6
        res["wan6_settings"]["wan6_type"] = data["wan6_proto"]
        if data["wan6_proto"] == "static":
            res["wan6_settings"]["wan6_static"] = {}
            res["wan6_settings"]["wan6_static"]["ip"] = data["ip6addr"]
            res["wan6_settings"]["wan6_static"]["network"] = data["ip6prefix"]
            res["wan6_settings"]["wan6_static"]["gateway"] = data["ip6gw"]
            dns1 = data.get("ipv6_dns1", None)
            dns2 = data.get("ipv6_dns2", None)
            res["wan6_settings"]["wan6_static"].update(
                {k: v for k, v in {"dns1": dns1, "dns2": dns2}.items() if v})
        if data["wan6_proto"] == "dhcpv6":
            res["wan6_settings"]["wan6_dhcpv6"] = {"duid": data.get("ip6duid", "")}

        # MAC
        res["mac_settings"] = {"custom_mac_enabled": True, "custom_mac": data["macaddr"]} \
            if "custom_mac" in data and data["custom_mac"] else {"custom_mac_enabled": False}

        return res

    def get_form(self):
        data = current_state.backend.perform("wan", "get_settings")
        data = self._convert_backend_data_to_form_data(data)

        if self.data:
            # Update from post
            data.update(self.data)

        # WAN
        wan_form = fapi.ForisForm("wan", data)
        wan_main = wan_form.add_section(
            name="set_wan",
            title=_(self.userfriendly_title),
            description=_(
                "Here you specify your WAN port settings. Usually, you can leave this "
                "options untouched unless instructed otherwise by your internet service "
                "provider. Also, in case there is a cable or DSL modem connecting your "
                "router to the network, it is usually not necessary to change this "
                "setting."
            )
        )
        WAN_DHCP = "dhcp"
        WAN_STATIC = "static"
        WAN_PPPOE = "pppoe"
        WAN_OPTIONS = (
            (WAN_DHCP, _("DHCP (automatic configuration)")),
            (WAN_STATIC, _("Static IP address (manual configuration)")),
            (WAN_PPPOE, _("PPPoE (for DSL bridges, Modem Turris, etc.)")),
        )

        WAN6_NONE = "none"
        WAN6_DHCP = "dhcpv6"
        WAN6_STATIC = "static"

        WAN6_OPTIONS = (
            (WAN6_DHCP, _("DHCPv6 (automatic configuration)")),
            (WAN6_STATIC, _("Static IP address (manual configuration)")),
        )

        if not self.hide_no_wan:
            WAN6_OPTIONS = ((WAN6_NONE, _("Disable IPv6")),) + WAN6_OPTIONS

        # protocol
        wan_main.add_field(
            Dropdown, name="proto", label=_("IPv4 protocol"), args=WAN_OPTIONS, default=WAN_DHCP)

        # static ipv4
        wan_main.add_field(
            Textbox, name="ipaddr", label=_("IP address"), required=True,
            validators=validators.IPv4()
        ).requires("proto", WAN_STATIC)
        wan_main.add_field(
            Textbox, name="netmask", label=_("Network mask"), required=True,
            validators=validators.IPv4Netmask()
        ).requires("proto", WAN_STATIC)
        wan_main.add_field(
            Textbox, name="gateway", label=_("Gateway"), required=True,
            validators=validators.IPv4(),
        ).requires("proto", WAN_STATIC)

        wan_main.add_field(
            Textbox, name="hostname", label=_("DHCP hostname"),
            validators=validators.Domain(),
            hint=_(
                "Hostname which will be provided to DHCP server."
            )
        ).requires("proto", WAN_DHCP)

        # DNS servers
        wan_main.add_field(
            Textbox, name="ipv4_dns1", label=_("DNS server 1 (IPv4)"),
            validators=validators.IPv4(),
            hint=_(
                "DNS server address is not required as the built-in "
                "DNS resolver is capable of working without it."
            )
        ).requires("proto", WAN_STATIC)
        wan_main.add_field(
            Textbox, name="ipv4_dns2", label=_("DNS server 2 (IPv4)"),
            validators=validators.IPv4(),
            hint=_(
                "DNS server address is not required as the built-in "
                "DNS resolver is capable of working without it."
            )
        ).requires("proto", WAN_STATIC)

        # xDSL settings
        wan_main.add_field(
            Textbox, name="username", label=_("PAP/CHAP username"),
        ).requires("proto", WAN_PPPOE)
        wan_main.add_field(
            Textbox, name="password", label=_("PAP/CHAP password"),
        ).requires("proto", WAN_PPPOE)

        # IPv6 configuration
        wan_main.add_field(
            Dropdown, name="wan6_proto", label=_("IPv6 protocol"),
            args=WAN6_OPTIONS, default=WAN6_NONE,
        )
        wan_main.add_field(
            Textbox, name="ip6addr", label=_("IPv6 address"),
            validators=validators.IPv6Prefix(), required=True,
            hint=_(
                "IPv6 address and prefix length for WAN interface, "
                "e.g. 2001:db8:be13:37da::1/64"
            ),
        ).requires("wan6_proto", WAN6_STATIC)
        wan_main.add_field(
            Textbox, name="ip6gw", label=_("IPv6 gateway"),
            validators=validators.IPv6(), required=True
        ).requires("wan6_proto", WAN6_STATIC)
        wan_main.add_field(
            Textbox, name="ip6prefix", label=_("IPv6 prefix"),
            validators=validators.IPv6Prefix(),
            hint=_(
                "Address range for local network, "
                "e.g. 2001:db8:be13:37da::/64"
            )
        ).requires("wan6_proto", WAN6_STATIC)
        # DNS servers
        wan_main.add_field(
            Textbox, name="ipv6_dns1", label=_("DNS server 1 (IPv6)"),
            validators=validators.IPv6(),
            hint=_(
                "DNS server address is not required as the built-in "
                "DNS resolver is capable of working without it."
            )
        ).requires("wan6_proto", WAN6_STATIC)
        wan_main.add_field(
            Textbox, name="ipv6_dns2", label=_("DNS server 2 (IPv6)"),
            validators=validators.IPv6(),
            hint=_(
                "DNS server address is not required as the built-in "
                "DNS resolver is capable of working without it."
            )
        ).requires("wan6_proto", WAN6_STATIC)
        wan_main.add_field(
            Textbox, name="ip6duid", label=_("Custom DUID"),
            validators=validators.Duid(),
            hint=_(
                "DUID which will be provided to the dhcpv6 server."
            )
        ).requires("wan6_proto", WAN6_DHCP)

        # custom MAC
        wan_main.add_field(
            Checkbox, name="custom_mac", label=_("Custom MAC address"),
            hint=_(
                "Useful in cases, when a specific MAC address is required by "
                "your internet service provider."
            )
        )

        wan_main.add_field(
            Textbox, name="macaddr", label=_("MAC address"),
            validators=validators.MacAddress(), required=True,
            hint=_("Separator is a colon, for example 00:11:22:33:44:55"),
        ).requires("custom_mac", True)

        def wan_form_cb(data):
            backend_data = self._convert_form_data_to_backend_data(data)
            res = current_state.backend.perform("wan", "update_settings", backend_data)

            return "save_result", res  # store {"result": ...} to be used later...

        wan_form.add_callback(wan_form_cb)

        return wan_form
