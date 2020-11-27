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

from typing import Optional

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from aioipfabric.client import IPFabricClient
from nauti.source import Source
from nauti.config_models import SourcesModel
from nauti.mappings import create_expander

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from nauti_ipfabric import NAUTI_SOURCE_NAME

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricSource", "IPFabricClient"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricSource(Source):

    name = NAUTI_SOURCE_NAME
    client_class = IPFabricClient

    def __init__(self, config: Optional[SourcesModel] = None, **kwargs):
        super(IPFabricSource, self).__init__()
        initargs = dict()

        self.config = config or {}

        if config:
            initargs.update(
                dict(
                    base_url=config.default.url,
                    token=config.default.credentials.token.get_secret_value(),
                    **config.default.options,
                )
            )
            initargs.update(kwargs)

        if (expands := getattr(self.config, "expands", None)) is not None:
            items = expands.items()
            self.expands = {field: create_expander(mapping) for field, mapping in items}

            self.deflates = {
                field: create_expander(mapping.inv) for field, mapping in items
            }
        else:
            self.expands = {}
            self.deflates = {}

        self.client = IPFabricClient(**(initargs or kwargs))

    async def login(self, *vargs, **kwargs):
        await self.client.login()

    async def logout(self):
        await self.client.logout()

    @property
    def is_connected(self):
        return not self.client.api.is_closed
