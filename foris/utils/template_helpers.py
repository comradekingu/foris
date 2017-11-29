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

import re

from .routing import external_route


def shorten_text(text, max_chars, etc="..."):
    """
        Shortens text. "Very long text" -> "Very long..."
    """
    if len(text) > max_chars:
        return text[:max_chars - len(etc)] + etc
    return text


def external_url(path):
    return external_route(path)


def remove_html_tags(text):
    return re.sub(r'<[^>]*>', '', text)
