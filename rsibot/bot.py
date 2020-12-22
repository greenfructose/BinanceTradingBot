import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_SIGNAL = 9
MACD_OVERBOUGHT = 0
MACD_OVERSOLD = 0
TRADE_SYMBOL = 'ETHUSD'
TRADE_QUANTITY = 0.05

ema_list = []
closes = []
ticks = 0
in_position = False

client = Client(config.API_KEY, config.API_SECRET, tld='us')


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
    global closes, in_position, ticks, ema_list
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
        print("closes")
        print(closes)
        if len(closes) > 26:
            np_closes = numpy.array(closes)
            short_ema = talib.EMA(closes, 12)
            long_ema = talib.EMA(closes, 26)
            macd_prev = long_ema - short_ema
            ema_list.append(macd_prev)
            if len(ema_list) > 8:
                macd = talib.EMA(ema_list, 9)
                print(f'MACD: {macd}')
                rsi = talib.RSI(np_closes, RSI_PERIOD)
                print("all rsis calculated so far")
                print(rsi)
                last_rsi = rsi[-1]
                print("the current rsi is {}".format(last_rsi))

                if last_rsi > RSI_OVERBOUGHT:
                    if in_position:
                        print("Overbought! Sell! Sell! Sell!")
                        # put binance sell logic here
                        order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = False
                    else:
                        print("It is overbought, but we don't own any. Nothing to do.")

                if last_rsi < RSI_OVERSOLD:
                    if in_position:
                        print("It is oversold, but you already own it, nothing to do.")
                    else:
                        print("Oversold! Buy! Buy! Buy!")
                        # put binance buy order logic here
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = True


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
