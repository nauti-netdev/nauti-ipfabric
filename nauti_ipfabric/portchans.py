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

from typing import Dict, Optional

from aioipfabric.filters import parse_filter
from aioipfabric.mixins.portchan import IPFPortChannels

from nauti.collection import Collection, CollectionCallback
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

        api: IPFabricClient(IPFPortChannels) = self.source.client
        api.mixin(IPFPortChannels)

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        records = await api.fetch_portchannels(**params)
        api.xf_portchannel_members(records)

        # invert these records to a flat list of fields.

        xf_records = [
            dict(
                hostname=rec["hostname"],
                intName=member["intName"],
                portchan=rec["intName"],
            )
            for rec in records
            for member in rec["members"]
        ]

        self.source_records.extend(xf_records)

    async def fetch_items(self, items: Dict):
        raise NotImplementedError()

    def itemize(self, rec: Dict) -> Dict:
        exp_ifn = self.source.expands["interface"]  # noqa

        return dict(
            hostname=normalize_hostname(rec["hostname"]),
            interface=exp_ifn(rec["intName"]),
            portchan=exp_ifn(rec["portchan"]),
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
