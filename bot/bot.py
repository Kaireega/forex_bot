import json
import time
from bot.candle_manager import CandleManager
from bot.technicals_manager import get_trade_decision
from bot.trade_manager import place_trade

from infrastructure.log_wrapper import LogWrapper
from models.trade_settings import TradeSettings
from api.oanda_api import OandaApi
import constants.defs as defs
from dateutil import parser
import pandas as pd
import os


class Bot:
    ERROR_LOG = "error"
    MAIN_LOG = "main"
    GRANULARITY = "M15"
    SLEEP = 10

    def __init__(self):
        self.load_settings()
        self.setup_logs()

        self.api = OandaApi()
        self.candle_manager = CandleManager(self.api, self.trade_settings, self.log_message, Bot.GRANULARITY)

        self.last_logged_positions = {}  # Cache for tracking last logged positions

        self.log_to_main("Bot started")
        self.log_to_error("Bot started")

    def load_settings(self):
        with open("./bot/settings.json", "r") as f:
            data = json.loads(f.read())
            self.trade_settings = {k: TradeSettings(v, k) for k, v in data['pairs'].items()}
            self.trade_risk = data['trade_risk']

    def setup_logs(self):
        self.logs = {}
        for k in self.trade_settings.keys():
            self.logs[k] = LogWrapper(k)
            self.log_message(f"{self.trade_settings[k]}", k)
        self.logs[Bot.ERROR_LOG] = LogWrapper(Bot.ERROR_LOG)
        self.logs[Bot.MAIN_LOG] = LogWrapper(Bot.MAIN_LOG)
        self.log_to_main(f"Bot started with {TradeSettings.settings_to_str(self.trade_settings)}")

    def log_message(self, msg, key):
        self.logs[key].logger.debug(msg)

    def log_to_main(self, msg):
        self.log_message(msg, Bot.MAIN_LOG)

    def log_to_error(self, msg):
        self.log_message(msg, Bot.ERROR_LOG)

    def process_candles(self, triggered):
        if len(triggered) > 0:
            self.log_message(f"process_candles triggered:{triggered}", Bot.MAIN_LOG)
            for p in triggered:
                last_time = self.candle_manager.timings[p].last_time
                trade_decision = get_trade_decision(last_time, p, Bot.GRANULARITY, self.api,
                                                    self.trade_settings[p], self.log_message)
                if trade_decision is not None and trade_decision.signal != defs.NONE:
                    self.log_message(f"Place Trade: {trade_decision}", p)
                    self.log_to_main(f"Place Trade: {trade_decision}")
                    place_trade(trade_decision, self.api, self.log_message, self.log_to_error, self.trade_risk)

    def positions_have_changed(self, new_positions):
        """
        Check if the new positions differ from the last logged positions.
        """
        new_positions_dict = {p["instrument"]: p for p in new_positions}
        if new_positions_dict != self.last_logged_positions:
            return True
        return False

    def log_positions_to_excel(self, positions, filename="./logs/position_tracking.xlsx"):
        """
        Save position details to an Excel sheet.
        """
        if not positions:
            self.log_to_main("No positions to log. Skipping Excel update.")
            return

        df = pd.DataFrame(positions)

        # Check if the file exists
        file_exists = os.path.exists(filename)

        try:
            if file_exists:
                with pd.ExcelWriter(filename, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
                    df.to_excel(writer, index=False, sheet_name="Positions")
            else:
                with pd.ExcelWriter(filename, mode="w", engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Positions")
        except Exception as e:
            self.log_to_error(f"Failed to log positions to Excel: {e}")

    def fetch_and_log_positions(self):
        """
        Fetch positions, check for changes, and log them if necessary.
        """
        try:
            positions = self.api.get_positions()
        except Exception as e:
            self.log_to_error(f"Failed to fetch positions: {e}")
            return

        if positions:
            if self.positions_have_changed(positions):
                self.log_to_main(f"Positions have changed. Logging new positions.")
                self.log_positions_to_excel(positions)
                # Update the cached positions
                self.last_logged_positions = {p["instrument"]: p for p in positions}
           

    def run(self):
        while True:
            time.sleep(Bot.SLEEP)
            try:
                self.process_candles(self.candle_manager.update_timings())
                self.fetch_and_log_positions()  # Log positions regularly
            except Exception as error:
                self.log_to_error(f"CRASH: {error}")
                break

