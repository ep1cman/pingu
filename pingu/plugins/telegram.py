
import asyncio
import logging

from aiogram import Bot, types
from aiogram.utils import exceptions

from pingu.plugin import Notifier, Events

log = logging.getLogger('Telegram')

class Telegram(Notifier):
    name = 'telegram'

    def __init__(self, **kwargs):
        self.api_token = kwargs['api_token']
        self.chat_id = kwargs['chat_id']
        self._bot = Bot(token=self.api_token, parse_mode=types.ParseMode.HTML)

        self.online_message = kwargs.get('online_message', "<b>PINGU:</b>\nDevice: {name} ({host}) has come ONLINE")
        self.offline_message = kwargs.get('offline_message', "<b>PINGU:</b>\nDevice: {name} ({host}) has gone OFFLINE")
        
    async def notify(self, result):
        if result['state'] == Events.ONLINE:
            message = self.online_message.format(**result)
        elif result['state'] == Events.OFFLINE:
            message = self.offline_message.format(**result)
        else:
            return
        await self.send_message(message)
    
    async def send_message(self, text):        
        try:
            await self._bot.send_message(self.chat_id, text)
        except exceptions.BotBlocked:
            log.error(f'Target [ID:{self.chat_id}]: blocked by user')
        except exceptions.ChatNotFound:
            log.error(f'Target [ID:{self.chat_id}]: invalid user ID')
        except exceptions.RetryAfter as e:
            log.error(f'Target [ID:{self.chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.')
            await asyncio.sleep(e.timeout)
            return await self.send_message(text)  # Recursive call
        except exceptions.UserDeactivated:
            log.error(f'Target [ID:{self.chat_id}]: user is deactivated')
        except exceptions.TelegramAPIError:
            log.exception(f'Target [ID:{self.chat_id}]: failed')
        else:
            log.info(f'Target [ID:{self.chat_id}]: success')

 