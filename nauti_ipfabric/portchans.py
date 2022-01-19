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
import asyncio
from typing import Dict, Optional

from aioipfabric.filters import parse_filter
from aioipfabric.mixins.portchan import IPFPortChannelsMixin

from nauti.collection import Collection, CollectionCallback, get_collection
from nauti.collections.portchans import PortChannelCollection
from nauti_ipfabric.source import IPFabricSource, IPFabricClient

from nauti.mappings import normalize_hostname


# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricPortChannelCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricPortChannelCollection(Collection, PortChannelCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        # going to fetch the associated devices and store them into the
        # collection cache so that these items/values can be used for filtering
        # purposes.  For example, the User may want to filter out port-channels
        # based on device model/family.

        dev_col = self.cache["devices"] = get_collection(
            source=self.source, name="devices"
        )

        await dev_col.fetch(**params)
        dev_col.make_keys("hostname")

        api: IPFabricClient() = self.source.client
        api.mixin(IPFPortChannelsMixin)

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        records = await api.fetch_portchannels(**params)
        api.xf_portchannel_members(records)

        # invert these records to a flat list of fields.
        xf_records = list()

        for rec in records:
            for member in rec["members"]:
                hostname = rec["hostname"]
                pchan_name = rec["intName"]
                member_name = member["intName"]

                iface_pchan, iface_member = await asyncio.gather(
                    self.source.client.fetch_table(
                        url="/tables/inventory/interfaces",
                        columns=["hostname", "intName", "nameOriginal"],
                        filters=parse_filter(
                            f"and(hostname={hostname}, intName={pchan_name})"
                        ),
                    ),
                    self.source.client.fetch_table(
                        url="/tables/inventory/interfaces",
                        columns=["hostname", "intName", "nameOriginal"],
                        filters=parse_filter(
                            f"and(hostname={hostname}, intName={member_name})"
                        ),
                    ),
                )

                xf_records.append(
                    dict(
                        hostname=rec["hostname"],
                        intName=iface_member[0]["nameOriginal"],
                        portchan=iface_pchan[0]["nameOriginal"],
                    )
                )

        self.source_records.extend(xf_records)

    async def fetch_items(self, items: Dict):
        raise NotImplementedError()

    def itemize(self, rec: Dict) -> Dict:
        return dict(
            hostname=normalize_hostname(rec["hostname"]),
            interface=rec["intName"],
            portchan=rec["portchan"],
        )

    async def add_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        pass

    async def update_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        pass

    async def delete_items(
        self, items: Dict, callback: Optional[CollectionCallback] = None
    ):
        pass
