import platform
import subprocess
import logging
import asyncio

from pingu.plugin import Checker, Events

log = logging.getLogger('Ping')

class Ping(Checker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.num_packets = kwargs.get('num_packets', 4)
        self.timeout = kwargs.get('timeout', 1)
        self.interval = kwargs.get('interval', 1)

    async def check(self):
        command = 'ping'
        command += ' -W ' + str(self.timeout)
        if platform.system().lower()=='windows':
            command += '-n ' + str(self.num_packets*1000)
        else:
            command += ' -c ' + str(self.num_packets)
            command += ' -i ' + str(self.interval)
        command += ' ' + self.host

        log.debug(f'Pinging {self.host}')
        log.debug(f'EXEC: {command}')

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        if stdout:
            log.debug(f'[stdout]\n{stdout.decode()}')
        if stderr:
            log.error(f'[stderr]\n{stderr.decode()}')

        if proc.returncode == 0:
            log.debug("ping success")
            return {
                "name": self.name,
                "host": self.host,
                "type": type(self).__name__,
                "state": Events.ONLINE,
            }
        else:
            log.debug("ping fail")
            return {
                "name": self.name,
                "host": self.host,
                "type": type(self).__name__,
                "state": Events.OFFLINE,
            }