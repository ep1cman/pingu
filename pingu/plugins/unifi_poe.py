import asyncio
import asyncssh
import logging

from pingu.plugin import Notifier, Events

log = logging.getLogger('UnifiPoe')

class UnifiPoe(Notifier):

    COMMAND = (
        '('
            'echo "enable" ;'
            'echo "configure" ;'
            'echo "interface {}" ;'
            'echo "poe opmode shutdown" ;'
            'echo  "poe opmode auto" ;'
            'echo "exit" ;'
            'echo "exit" ;'
            'echo "exit"'
        ') | telnet localhost 23 ; exit;'
    )

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.ssh_username = kwargs['ssh_username']
        self.ssh_password = kwargs['ssh_password']
        self.ssh_host = kwargs['ssh_host']
        self.delay = kwargs.get('delay', 60)
        self.interfaces = kwargs['interfaces']

        self._tasks = {}

    async def power_cycle_port(self, interface):
        await asyncio.sleep(self.delay)
        async with asyncssh.connect(self.ssh_host, username=self.ssh_username, password=self.ssh_password) as conn:
            log.info(f'Power cycling interface {interface} on {self.ssh_host}')
            command = self.COMMAND.format(interface)
            log.debug(command)
            result = await conn.run(command, check=True)
            log.info(result.stdout, end='')
        del self._tasks[interface]

    async def notify(self, result):
        if result['host'] not in self.interfaces:
            return  # There is no POE port associated with this host
        interface = self.interfaces[result['host']]

        if result['state'] == Events.ONLINE:
            if interface in self._tasks:
                self._tasks[interface].cancel()
                log.debug(f'Cancelled power cycle of interface {interface} on {self.ssh_host}')
        else:
            log.debug(f'Scheduling power cycle of interface {interface} on {self.ssh_host}')
            self._tasks[interface] = asyncio.ensure_future(self.power_cycle_port(interface))
