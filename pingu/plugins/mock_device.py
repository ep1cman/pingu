import logging
import asyncio

from pingu.plugin import Checker, Events

log = logging.getLogger('Mock')

class Mock(Checker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.online_duration = kwargs.get('num_packets', 5)
        self.offline_duration = kwargs.get('num_packets', 5)
        self._online = True
        self._timer_task = asyncio.ensure_future(self.timer())

    async def timer(self):
        while True:
            await asyncio.sleep(self.online_duration)
            self._online = False
            log.debug(f'Going offline (Host: {self.host}, name: {self.name})')
            await asyncio.sleep(self.offline_duration)
            self._online = True
            log.debug(f'Going online (Host: {self.host}, name: {self.name})')


    async def check(self):
        if self._online:
            return {
                "name": self.name,
                "host": self.host,
                "type": type(self).__name__,
                "state": Events.ONLINE,
            }
        else:
            return {
                "name": self.name,
                "host": self.host,
                "type": type(self).__name__,
                "state": Events.OFFLINE,
            }

