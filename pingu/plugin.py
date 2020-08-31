"""Main applicatoin that demonstrates the functionality of
the dynamic plugins and the PluginCollection class
"""

import pkgutil
import importlib
import inspect
import logging
from enum import Enum

class Events(Enum):
    ONLINE = 1
    OFFLINE = 2

class Plugin():
    name = "OVERRIDE ME"

class Notifier(Plugin):
    pass

class Checker(Plugin):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.host = kwargs["host"]
        events = kwargs.get("events", [Events.OFFLINE.name])
        self.events = [Events[event] for event in events]

    def check(self, **kwargs):
        pass

class Logger(Plugin):
    class Modes(Enum):
        EVERY = 1  # Log every result
        CHANGE = 2  # Log when the resut state changes

    def __init__(self, **kwargs):
        self.mode = Logger.Modes[kwargs.get("mode", Logger.Modes.EVERY.name)]
        self._last_result = {}

    async def _log(self, result):
        if (result["name"] not in self._last_result):
            self._last_result[result["name"]] = result

        if self.mode == Logger.Modes.EVERY:
            await self.log(result)
        elif self.mode == Logger.Modes.CHANGE and result != self._last_result[result["name"]]:
            await self.log(result)
        
        self._last_result[result["name"]] = result
    
    def log(self, result):
        raise NotImplementedError()

class PluginLoader():
    def __init__(self):
        self.loggers = {}
        self.notifiers = {}
        self.checkers = {}

    def discover_plugins(self, path):
        for _, name, _ in pkgutil.iter_modules([path], "pingu.plugins."):
            print (name)
            plugin_module = importlib.import_module(name, ".")
            for (_, member_value) in inspect.getmembers(plugin_module, inspect.isclass):
                if issubclass(member_value, Plugin) and (member_value not in [Plugin, Notifier, Logger, Checker]) :
                    plugin = member_value
                    plugin_name = plugin.__name__
                    if issubclass(member_value, Notifier):
                        logging.debug(f'Found plugin (Notifier): {member_value.__module__}.{member_value.__name__}')
                        self.notifiers[plugin_name] = plugin
                    if issubclass(member_value, Logger):
                        logging.debug(f'Found plugin (Logger): {member_value.__module__}.{member_value.__name__}')
                        self.loggers[plugin_name] = plugin
                    if issubclass(member_value, Checker):
                        logging.debug(f'Found plugin (Checker): {member_value.__module__}.{member_value.__name__}')
                        self.checkers[plugin_name] = plugin


