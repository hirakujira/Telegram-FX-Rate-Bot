import telebot
import requests
import json
import re
from datetime import datetime

global bot

class FXRateConfig:
    def __init__(self, bot_token, channels):
        global bot
        bot = telebot.TeleBot(bot_token)
        self.channels = channels


def load_config():
    with open('config.json') as f:
        j = json.load(f)
        return FXRateConfig(j['bot_token'], j['channels'])

def get_currency_list():
    url = "https://api.fxratesapi.com/currencies?format=json"
    try:
        response = requests.get(url)
        data = response.json()

        currency_list = [data[currency]['code'] for currency in data]
        return currency_list
    except Exception as e:
        print(e)
        return None

def get_exchange_rate(amount, from_currency, to_currency):
    url = f"https://api.fxratesapi.com/convert?from={from_currency}&to={to_currency}&amount={amount}&format=json"
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        print(e)
        return None

config = load_config()
currency_list = get_currency_list()

def parse_currency_input(text):
    pattern = r'^(\d+(\.\d+)?\s*)?([A-Z]{3,4})(\s+[A-Z]{3,4})?$'
    match = re.match(pattern, text.strip().upper())
    
    if match:
        amount = match.group(1)
        from_currency = match.group(3)
        to_currency = match.group(4)

        if from_currency not in currency_list:
            return -1, from_currency, ""
        if to_currency and to_currency.strip() not in currency_list:
            return -1, "", to_currency
        
        amount = float(amount.strip()) if amount else 1
        to_currency = to_currency.strip() if to_currency else 'TWD'
        
        return amount, from_currency, to_currency
    return None

@bot.message_handler(commands=['cur'])
def handle_currency_conversion(message):
    try:
        if len(config.channels) and message.chat.id not in config.channels:
            bot.reply_to(message, "您沒有權限使用此指令。")
            return
        result = parse_currency_input(message.text.replace('/cur ', '').replace('=', '').replace(',', ''))
        if result:
            amount, from_currency, to_currency = result

            if amount == -1:
                if from_currency:
                    bot.reply_to(message, f"找不到幣種: {from_currency}")
                else:
                    bot.reply_to(message, f"找不到幣種: {to_currency}")
                return

            data = get_exchange_rate(amount, from_currency, to_currency)
            if data is None:
                bot.reply_to(message, "無法取得匯率資料。")
                return
            
            converted_amount = data['result']
            timestamp = datetime.fromtimestamp(data['timestamp'])

            if amount.is_integer():
                amount_str = f"{int(amount):,}"
            else:
                amount_str = f"{amount:,.2f}"

            if converted_amount < 0.01:
                response = f"`💰{amount_str} {from_currency} = < 0.01 {to_currency}`"
                response += f"\n\n更新時間: {timestamp.strftime('%Y-%m-%d %H:%M')}"
            else:
                if converted_amount.is_integer():
                    converted_amount_str = f"{int(converted_amount):,}"
                else:
                    converted_amount_str = f"{converted_amount:,.2f}"
                
                response = f"`💰{amount_str} {from_currency} = {converted_amount_str} {to_currency}`"
                response += f"\n\n更新時間: {timestamp.strftime('%Y-%m-%d %H:%M')}"
            
            bot.reply_to(message, response, parse_mode="Markdown")
        else:
            bot.reply_to(message, "格式錯誤。請使用 /cur <金額> <從幣種> <到幣種>")
    except Exception as e:
        print(e)
        bot.reply_to(message, "格式錯誤。請使用 /cur <金額> <從幣種> <到幣種>")

bot.polling()
