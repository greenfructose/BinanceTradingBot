import websocket, json, pprint, talib, numpy, pandas, threading
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'ETHUSD'
TRADE_QUANTITY = 0.05

test_cash = 1000.0
eth_owned = 0.0
closes = []
ticks = 0
in_position = False

client = Client(config.API_KEY, config.API_SECRET, tld='us')


def get_ema(series, period):
    series = numpy.array(series)
    return pandas.ewma(series, span=period)[-1]


def test_order(side, close):
    global test_cash, eth_owned
    if side == 'buy':
        if test_cash > 0:
            eth_owned = eth_owned + test_cash / close
            print(f"ETH is oversold, bought {test_cash / close} at {close}")
            test_cash = 0
        else:
            print("ETH is oversold, but we don't have any money to buy")
    if side == 'sell':
        if eth_owned > 0:
            test_cash = test_cash + eth_owned * close
            print(f"ETH is overbought, sold {eth_owned} for {close}")
            eth_owned = 0
        else:
            print("ETH is overbought, but we don't have any to sell")


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True


def on_open(ws):
    print('opened connection')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global closes, in_position, ticks, eth_owned, test_cash
    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message['k']['x'])

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    print(f'Period: {len(closes)}')
    print(f'Tick: {ticks}')
    ticks = ticks + 1
    if is_candle_closed:
        ticks = 0
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print(f'Current Cash Balance: ${test_cash}')
        print(f'Current ETH Balance: {eth_owned} ETH')
        print(f'Current Portfolio Cash Value: ${test_cash + eth_owned * closes[-1]}')
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all rsis calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print(f'The current rsi is {last_rsi}')
            if last_rsi > RSI_OVERBOUGHT:
                threading.Thread(target=test_order, args=('sell', close)).start()

                # if in_position:
                #     print("Overbought! Sell! Sell! Sell!")
                #     # put binance sell logic here
                #     order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                #     if order_succeeded:
                #         in_position = False
                # else:
                #     print("It is overbought, but we don't own any. Nothing to do.")
            if last_rsi < RSI_OVERSOLD:
                threading.Thread(target=test_order, args=('buy', close)).start()
                # if in_position:
                #     print("It is oversold, but you already own it, nothing to do.")
                # else:
                #     print("Oversold! Buy! Buy! Buy!")
                #     # put binance buy order logic here
                #     order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                #     if order_succeeded:
                #         in_position = True


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
