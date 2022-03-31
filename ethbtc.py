from binance.client import Client
from binance.enums import *
import time
from datetime import datetime
import math
from config import *


def round_decimals_down(number, decimals=2):
    if not isinstance(decimals, int):
        raise TypeError("Not int value to round down")
    elif decimals < 0:
        raise ValueError("Decimal places negative")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor


def sell(amount, symbol):
    quantity = round_decimals_down(amount, 3)
    order = client.create_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=quantity
    )

    print(order)
    time.sleep(5)
    new_amount = float(client.get_asset_balance(asset=base)["free"])
    return new_amount


def buy(amount, symbol):
    quantity = round_decimals_down(amount / curr_price, 3)
    order = client.create_order(
        symbol=symbol,
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=quantity
    )

    print(order)
    time.sleep(5)
    new_amount = float(client.get_asset_balance(asset=target)["free"])
    return new_amount


def get_transaction_price():
    try:
        f = open('transaction_price.txt')
        line = f.readline()
        f.close()
    except IOError:
        line = client.get_avg_price(symbol=pair)['price']
        set_transaction_price(str(line))
    return float(line)


def set_transaction_price(price):
    f = open('transaction_price.txt', 'w')
    f.write(str(price))
    f.close()


client = Client(api_key, api_secret, {"verify": True, "timeout": 20})

pair = target + base
curr_price = last_price = float(client.get_avg_price(symbol=pair)['price'])
mode = "none"
trend = "none"

while 1:
    transaction_price = get_transaction_price()

    my_target_amount = float(client.get_asset_balance(asset=target)["free"])
    my_base_amount = float(client.get_asset_balance(asset=base)["free"])

    if my_target_amount * last_price > my_base_amount:
        mode = "sell"
    if my_target_amount * last_price < my_base_amount:
        mode = "buy"

    last_price = curr_price

    curr_price = float(client.get_avg_price(symbol=pair)['price'])
    if last_price < curr_price:
        trend = "up"
    if last_price > curr_price:
        trend = "down"
    percentage = curr_price / transaction_price * 100
    to_print = f"\n" \
               f"{datetime.now()}\n" \
               f"Transaction price={transaction_price}\n" \
               f"Current={curr_price}\n" \
               f"Percentage={percentage}%\n" \
               f"Trend={trend}\n" \
               f"Mode={mode}\n" \
               f"{my_base_amount}{base}   {my_target_amount}{target}"

    with open('status.log', 'w') as the_file:
        the_file.write(to_print)

    if percentage <= buy_percentage and trend == "up" and mode == "buy":
        time.sleep(360)
        curr_price = float(client.get_avg_price(symbol=pair)['price'])
        if last_price < curr_price:
            trend = "up"
        if last_price > curr_price:
            trend = "down"

        percentage = curr_price / transaction_price * 100
        if percentage <= buy_percentage and trend == "up" and mode == "buy":
            my_target_amount = buy(my_base_amount, pair)
            my_base_amount = 0.0
            transaction_price = curr_price
            set_transaction_price(transaction_price)
            to_print = f"\n" \
                       f"{datetime.now()}\n" \
                       f"BUY - now we have{my_target_amount}{target}\n"

            with open(f'{base}{target}.log', 'a') as the_file:
                the_file.write(to_print)

    if percentage >= sell_percentage and trend == "down" and mode == "sell":
        time.sleep(360)
        curr_price = float(client.get_avg_price(symbol=pair)['price'])
        if last_price < curr_price:
            trend = "up"
        if last_price > curr_price:
            trend = "down"
        percentage = curr_price / transaction_price * 100
        if percentage >= sell_percentage and trend == "down" and mode == "sell":
            my_base_amount = sell(my_target_amount, pair)
            my_target_amount = 0.0
            transaction_price = curr_price
            set_transaction_price(transaction_price)
            to_print = f"\n{datetime.now()}\n" \
                       f"SELL - now we have{my_base_amount}{base}\n"

            with open(f'{base}{target}.log', 'a') as the_file:
                the_file.write(to_print)

    if percentage >= buy_again and trend == "up" and mode == "buy":
        to_print = f"\n{datetime.now()} Reload the threshold: " \
                   f"Transaction price={transaction_price} " \
                   f"Current={curr_price} " \
                   f"Percentage={percentage}% " \
                   f"Trend={trend} " \
                   f"Mode={mode}\n"

        with open(f'{base}{target}.log', 'a') as the_file:
            the_file.write(to_print)
        transaction_price = curr_price
        set_transaction_price(transaction_price)

    time.sleep(sleeptime)
