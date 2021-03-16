#      Copyright (C) 2020  Jeremy Schulman
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, Optional
import re

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from aioipfabric.filters import parse_filter

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from nauti.collection import Collection, CollectionCallback, get_collection
from nauti.collections.interfaces import InterfaceCollection
from nauti_ipfabric.source import IPFabricSource
from nauti.mappings import normalize_hostname

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricInterfaceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

_exos_port_match = re.compile(r'(\d+):(\d+)').match

class IPFabricInterfaceCollection(Collection, InterfaceCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        # We want to know information about the device, such as os_name, and we
        # will key this collection by the hostname value

        dev_col = self.cache['devices'] = get_collection(source=self.source, name='devices')
        await dev_col.fetch(**params)
        dev_col.make_keys('hostname')

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        records = await self.source.client.fetch_table(
            url="/tables/inventory/interfaces",
            columns=["hostname", "intName", "dscr", "siteName", "l1", "primaryIp"],
            **params,
        )

        self.source_records.extend(records)

    async def fetch_items(self, items: Dict):
        raise NotImplementedError()

    def itemize(self, rec: Dict) -> Dict:
        hostname = normalize_hostname(rec['hostname']).lower()          # hostnames always used in lowercase form.
        orig_if_name = rec['intName']
        os_name = self.cache['devices'].items[hostname]['os_name']

        # TODO: this is a bit of a hack for now, but we'll need to address how we want to
        #       perform mapping and filtering in more of a plugin/config-file mannter.

        if os_name == 'exos':
            # if this is a physical port, it will take the form "<switch_id>:<port_id>"
            if (mo := _exos_port_match(orig_if_name)):
                sw_id, port_id = mo.groups()
                if_name = f'Ethernet{port_id}' if sw_id == '1' else f'Ethernet{sw_id}/{port_id}'

            # otherwise this is a "VLAN" port, and we only want to keep those
            # that have an IP address assigned.  Other "VLAN ports" are just
            # VLANs and do not constitute a port.  EXOS joy.

            else:
                if not rec['primaryIp']:
                    return None

                if_name = orig_if_name

        else:
            if_name = self.source.expands["interface"](orig_if_name)

        return {
            "interface": if_name,
            "hostname": normalize_hostname(rec["hostname"]),
            "description": rec["dscr"] or "",
            "site": rec["siteName"],
        }

    async def add_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        raise NotImplementedError()

    async def update_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        raise NotImplementedError()

    async def delete_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        raise NotImplementedError()
