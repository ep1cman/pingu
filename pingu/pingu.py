#!/usr/bin/env python3

import os
import logging
import argparse
import asyncio
from pprint import pformat

import yaml

from pingu.plugin import PluginLoader, Events, Logger

log = logging.getLogger('Main')


class Runner():
    def __init__(self, args):
        self.checkers = []
        self.notifiers = []
        self.loggers = []

        # Parse config
        log.debug(f'Loading config from: {os.path.abspath(args.config.name)}')
        config = yaml.load(args.config, Loader=yaml.FullLoader) 
        self._config = config['config']
        log.debug('Config:')
        log.debug(pformat(config))

        # Load Plugins
        # TODO: Extra plugin dirs from config
        log.info('Discovering Plug-ins')
        self._loader = PluginLoader()
        built_in_plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        self._loader.discover_plugins(built_in_plugin_dir)

        # Initialise plugins
        log.info('Initialising Plug-ins')
        self.load_checkers(config['devices'])
        self.load_notifiers(config['notifiers'])
        self.load_loggers(config['loggers'])

    def load_checkers(self, config):
        seen_names = set()
        for device_config in config:
            if device_config['type'] not in self._loader.checkers:
                raise Exception(f'Unknown device type: {device_config["type"]}')
            if device_config['name'] in seen_names:
                raise Exception(f'Duplicate device named: {device_config["name"]}')
            seen_names.add(device_config['name'])
            self.checkers.append(self._loader.checkers[device_config['type']](**device_config))
        
    def load_notifiers(self, config):
        for notifier_name, notifier_config in config.items():
            if notifier_name not in self._loader.notifiers:
                raise Exception(f'Unknown notifier type: {notifier_name}')
            self.notifiers.append(self._loader.notifiers[notifier_name](**notifier_config))

    def load_loggers(self, config):
        for logger_name, logger_config in config.items():
            if logger_name not in self._loader.loggers:
                raise Exception(f'Unknown logger type: {logger_name}')
            self.loggers.append(self._loader.loggers[logger_name](**logger_config))

    async def loop(self):
        last_result = {}
        log.info('Starting Pingu')

        while True:
            for checker in self.checkers:
                result = await checker.check()
                if checker.name not in last_result:
                    last_result[checker.name] = result
                
                # State has changed, fire the configured notifiers (if any)
                if last_result[checker.name] != result:
                    if result['state'] in checker.events:
                        asyncio.create_task(self.notify(result))

                last_result[checker.name] = result

                asyncio.create_task(self.log(result))

            await asyncio.sleep(self._config['interval'])

    async def log(self, result):
        for logger in self.loggers:
            await logger._log(result)

    async def notify(self, result):
        for notifier in self.notifiers:
            await notifier.notify(result)


def main():
    # Setup argparse
    parser = argparse.ArgumentParser(description='Checks network device status and generates notifications on changes')
    parser.add_argument('config', type=argparse.FileType('r'), metavar='CONFIG_FILE',
                        help='Path to YAML config file')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debugging messages')
    args = parser.parse_args()
    
    # Setup logger
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    log.debug(f'ARGS: {args}') 

    runner = Runner(args)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.loop())
    pending = asyncio.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))

    log.info('Finished')


if __name__ == '__main__':
    main()


