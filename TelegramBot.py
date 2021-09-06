from Helper import BaseClass
import re
import hashlib
import ast
from datetime import datetime

class TelegramBot(BaseClass):
    
    def initialize(self):

        self._commanddict = {"/hi": {"desc": "greetings", "method": self.greet_user_if_new_conversation},
                             "/toggle_light": {"desc": "Turn on light", "method": self.toggle_steigerlamp},
                             "/keyboard": {"desc": "display keyboard", "method": self.keyb}}
        
        self._textdict = {"Steigerlamp": {"desc":"empty", "method":self.toggle_steigerlamp},
                          "Schouw": {"desc":"empty", "method":self.toggle_schouwlamp},
                          "Slaapkamer plafondlamp": {"desc":"empty", "method":self.toggle_bedroomlamp},
                          "Vakkenkast": {"desc":"empty", "method":self.vakkenkast_lamp},
                          "Plafondlamp keuken": {"desc":"empty", "method":self.plafondlamp_keuken},
                          "Living Room": {"desc":"empty", "method":self.keyb_livingroom}, 
                          "Dining Room": {"desc":"empty", "method":self.keyb_diningroom},
                          "Kitchen": {"desc":"empty", "method":self.keyb_kitchen}, 
                          "Bedroom": {"desc":"empty", "method":self.keyb_bedroom},
                          "Back --> General": {"desc":"empty", "method":self.keyb}
        }
    
        self.listen_event(self._receive_telegram_command, 'telegram_command')
        self.listen_event(self._receive_telegram_callback, 'telegram_callback')
        self.listen_event(self._receive_telegram_text, 'telegram_text')
        self._entityid_hash_dict = dict()
        self._hash_entityid_dict = dict()
        self._version=1.1
        
        self._log_debug(self.args)

        #handle extend
        self._extend_system = None
        if self.args["extend_system"] is not None and self.args["extend_system"]!="":
            self._extend_system=self.args["extend_system"].split(',')
        self._log_debug(f"extend_system: {self._extend_system}")

        self._filter_blacklist = None
        if self.args.get("filter_blacklist", None) is not None and self.args.get("filter_blacklist")!="":
            self._filter_blacklist=self.args.get("filter_blacklist")
        self._log_debug(self._filter_blacklist)
        self._log_debug(f"filter_blacklist: {self._filter_blacklist}")
        
        self._filter_whitelist = None
        if self.args.get("filter_whitelist", None) is not None and self.args.get("filter_whitelist")!="":
            self._filter_whitelist=self.args.get("filter_whitelist")
        self._log_debug(f"filter_whitelist: {self._filter_whitelist}")

        self._routing = self.args.get("routing", None)
        self._log_debug(f"routing: {self._routing}")

        self._hass = self.args.get("hass", None)
        self._log_debug(f"hass: {self._hass}")

    def _receive_telegram_command(self, event_id, payload_event, *args):
        user_id = payload_event['user_id']
        chat_id = payload_event['chat_id']
        command = payload_event['command'].lower()

        self._log_debug(f"Telegram Command: user_id: {user_id}, chat_id: {chat_id}, command: {command}")
        self._log_debug(f"Paylod_event: {payload_event}")

        if command in self._commanddict:
            method = self._commanddict.get(command).get('method')
            method(user_id)
        else:
            msg = f"Unkown command {command}. Use /help to get a list of all available commands."
            self.call_service(
                'telegram_bot/send_message',
                target=user_id,
                message=self._escape_markdown(msg))
    
    def _receive_telegram_text(self, event_id, payload_event, *args):
        user_id = payload_event['user_id']
        chat_id = payload_event['chat_id']
        text = payload_event.get('text')
        
        if text in self._textdict:
            method = self._textdict.get(text).get('method')
            method(user_id)

        self._log_debug(f"Telegram Command: user_id: {user_id}, chat_id: {chat_id}, text: {text}")
        self._log_debug(f"Paylod_event: {payload_event}")

        #check if location was sent
        if isinstance(text, dict) and text.get('location',None) is not None:
            location = text.get('location',dict())
            longitude = location.get('longitude',None)
            latitude = location.get('latitude',None)
            self._compute_travel_time(user_id, longitude, latitude)

    def _receive_telegram_callback(self, event_id, payload_event, *args):
        data_callback = payload_event['data'].lower()
        callback_id = payload_event['id']

        self._log_debug(f"Telegram Callback: data_callback: {data_callback}, callback_id: {callback_id}")
        self._log_debug(f"Paylod_event: {payload_event}")

        if "?" in data_callback:
            callback, params = data_callback.split("?")
        else:
            callback = data_callback
            params = None
        if params is not None:
            params = dict(item.split("=") for item in params.split(";"))
        if callback in self._callbackdict:
            method = self._callbackdict.get(callback).get('method')
            method(target_id=callback_id, paramdict=params)
        if callback in self._commanddict:
            method = self._commanddict.get(callback).get('method')
            method(target_id=callback_id)
            #https://python-telegram-bot.readthedocs.io/en/stable/telegram.callbackquery.html
            #After the user presses an inline button, Telegram clients will display a progress 
            #bar until you call answer. It is, therefore, necessary to react by calling 
            #telegram.Bot.answer_callback_query even if no notification to the user is needed 
            #(e.g., without specifying any of the optional parameters).
            self.call_service(
                'telegram_bot/answer_callback_query',
                message="",
                callback_query_id=callback_id)

    def greet_user_if_new_conversation(self, target_id):
        msg = 'Hi Karel'
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)

                              
    def toggle_steigerlamp(self, target_id): 
        msg = "Toggeling the Stijgerhoutlamp"
        self.call_service("light/toggle", entity_id="light.steigerhout_lamp")
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)
    
    def toggle_schouwlamp(self, target_id): 
        msg = "Toggeling the lamp on the schouw"
        self.call_service("light/toggle", entity_id="light.antique_sta_lamp")
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)
                             
    def toggle_bedroomlamp(self, target_id): 
        msg = "Toggeling the plafondlamp in de slaapkamer"
        self.call_service("light/toggle", entity_id="light.plafondlamp_bed")
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)
    
    def vakkenkast_lamp(self, target_id): 
        msg = "Toggeling the lamp in de vakkenkast"
        self.call_service("light/toggle", entity_id="light.vakkenkast_lamp")
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)
    
    def plafondlamp_keuken(self, target_id): 
        msg = "Toggeling the plafondlamp in de keuken"
        self.call_service("light/toggle", entity_id="light.plafondlamp_keuken")
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg)
                             
    def keyb(self, target_id): #general keyboard
        msg = "Make a choice you ..."
        keyboard_list = ["Living Room", "Dining Room", "Kitchen", "Bedroom"]
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg, keyboard=keyboard_list)
    
                              
    def keyb_livingroom(self, target_id): #specific for livingroom
        msg = "Make a choice to toggle"
        keyboard_list = ["Steigerlamp", "Schouw", "Back --> General"]
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg, keyboard=keyboard_list)
    
    def keyb_bedroom(self, target_id): #specific for bedroom
        msg = "Make a choice to toggle"
        keyboard_list = ["Slaapkamer plafondlamp", "Back --> General"]
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg, keyboard=keyboard_list)
    
    def keyb_diningroom(self, target_id): #specific for diningroom
        msg = "Make a choice to toggle"
        keyboard_list = ["Vakkenkast", "Back --> General"]
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg, keyboard=keyboard_list)
    
    def keyb_kitchen(self, target_id): #specific for kitchen
        msg = "Make a choice to toggle"
        keyboard_list = ["Plafondlamp keuken", "Back --> General"]
        self.call_service('telegram_bot/send_message',
                              target=target_id,
                              message=msg, keyboard=keyboard_list)