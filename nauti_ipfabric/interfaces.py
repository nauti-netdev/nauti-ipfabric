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

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from aioipfabric.filters import parse_filter

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from nauti.collection import Collection, CollectionCallback
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


class IPFabricInterfaceCollection(Collection, InterfaceCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        records = await self.source.client.fetch_table(
            url="/tables/inventory/interfaces",
            columns=["hostname", "intName", "dscr", "siteName", "l1"],
            **params,
        )

        self.source_records.extend(records)

    async def fetch_items(self, items: Dict):
        raise NotImplementedError()

    def itemize(self, rec: Dict) -> Dict:
        return {
            "interface": self.source.expands["interface"](rec["intName"]),  # noqa
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
