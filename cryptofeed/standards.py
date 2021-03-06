'''
Copyright (C) 2017-2020  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.


Contains all code to normalize and standardize the differences
between exchanges. These include trading pairs, timestamps, and
data channel names
'''
import logging

import pandas as pd

from cryptofeed.defines import (BINANCE, BINANCE_FUTURES, BINANCE_DELIVERY, BINANCE_US, BITCOINCOM, BITFINEX, BITMAX, BITMEX,
                                BITSTAMP, BITTREX, BLOCKCHAIN, BYBIT, COINBASE, COINBENE, DERIBIT, EXX, FILL_OR_KILL, FTX,
                                FTX_US, FUNDING, GATEIO, GEMINI, HITBTC, HUOBI, HUOBI_DM, HUOBI_SWAP, IMMEDIATE_OR_CANCEL, KRAKEN,
                                KRAKEN_FUTURES, L2_BOOK, L3_BOOK, LIMIT, LIQUIDATIONS,
                                MAKER_OR_CANCEL, MARKET, OKCOIN, OKEX, OPEN_INTEREST, POLONIEX, PROBIT, TICKER,
                                TRADES, UNSUPPORTED, UPBIT, VOLUME, FUTURES_INDEX)
from cryptofeed.exceptions import UnsupportedDataFeed, UnsupportedTradingOption, UnsupportedTradingPair
from cryptofeed.pairs import gen_pairs, _exchange_info

LOG = logging.getLogger('feedhandler')

_std_trading_pairs = {}
_exchange_to_std = {}


def load_exchange_pair_mapping(exchange: str):
    if exchange in {BITMEX, DERIBIT, KRAKEN_FUTURES}:
        return
    mapping = gen_pairs(exchange)
    for std, exch in mapping.items():
        _exchange_to_std[exch] = std
        if std in _std_trading_pairs:
            _std_trading_pairs[std][exchange] = exch
        else:
            _std_trading_pairs[std] = {exchange: exch}


def get_exchange_info(exchange: str):
    mapping = gen_pairs(exchange)
    info = dict(_exchange_info.get(exchange, {}))
    return mapping, info


def pair_std_to_exchange(pair: str, exchange: str):
    # bitmex does its own validation of trading pairs dynamically
    if exchange in {BITMEX, DERIBIT, KRAKEN_FUTURES}:
        return pair
    if pair in _std_trading_pairs:
        try:
            return _std_trading_pairs[pair][exchange]
        except KeyError:
            raise UnsupportedTradingPair(f'{pair} is not supported on {exchange}')
    else:
        # Bitfinex supports funding pairs that are single currencies, prefixed with f
        if exchange == BITFINEX and '-' not in pair:
            return f"f{pair}"
        raise UnsupportedTradingPair(f'{pair} is not supported on {exchange}')


def pair_exchange_to_std(pair):
    if pair in _exchange_to_std:
        return _exchange_to_std[pair]
    # Bitfinex funding currency
    if pair[0] == 'f':
        return pair[1:]
    return None


def timestamp_normalize(exchange, ts):
    if exchange in {BITMEX, COINBASE, HITBTC, OKCOIN, OKEX, FTX, FTX_US, BITCOINCOM, BLOCKCHAIN, PROBIT}:
        return pd.Timestamp(ts).timestamp()
    elif exchange in {HUOBI, HUOBI_DM, HUOBI_SWAP, BITFINEX, BYBIT, COINBENE, DERIBIT, BINANCE, BINANCE_US, BINANCE_FUTURES,
                      BINANCE_DELIVERY, GEMINI, BITTREX, BITMAX, KRAKEN_FUTURES, UPBIT}:
        return ts / 1000.0
    elif exchange in {BITSTAMP}:
        return ts / 1000000.0
    return ts


_feed_to_exchange_map = {
    L2_BOOK: {
        BITFINEX: 'book-P0-F0-100',
        POLONIEX: L2_BOOK,
        HITBTC: 'subscribeOrderbook',
        COINBASE: 'level2',
        BITMEX: 'orderBookL2',
        BITSTAMP: 'diff_order_book',
        KRAKEN: 'book',
        KRAKEN_FUTURES: 'book',
        BINANCE: 'depth@100ms',
        BINANCE_US: 'depth@100ms',
        BINANCE_FUTURES: 'depth@100ms',
        BINANCE_DELIVERY: 'depth@100ms',
        BLOCKCHAIN: 'l2',
        EXX: 'ENTRUST_ADD',
        HUOBI: 'depth.step0',
        HUOBI_DM: 'depth.step0',
        HUOBI_SWAP: 'depth.step0',
        OKCOIN: 'spot/depth_l2_tbt',
        OKEX: '{}/depth_l2_tbt',
        COINBENE: L2_BOOK,
        DERIBIT: 'book',
        BYBIT: 'orderBookL2_25',
        FTX: 'orderbook',
        FTX_US: 'orderbook',
        GEMINI: L2_BOOK,
        BITTREX: 'SubscribeToExchangeDeltas',
        BITCOINCOM: 'subscribeOrderbook',
        BITMAX: L2_BOOK,
        UPBIT: L2_BOOK,
        GATEIO: 'depth.subscribe',
        PROBIT: 'order_books'
    },
    L3_BOOK: {
        BITFINEX: 'book-R0-F0-100',
        BITSTAMP: 'detail_order_book',
        HITBTC: UNSUPPORTED,
        COINBASE: 'full',
        BITMEX: UNSUPPORTED,
        POLONIEX: UNSUPPORTED,  # supported by specifying a trading pair as the channel,
        KRAKEN: UNSUPPORTED,
        KRAKEN_FUTURES: UNSUPPORTED,
        BINANCE: UNSUPPORTED,
        BINANCE_US: UNSUPPORTED,
        BINANCE_FUTURES: UNSUPPORTED,
        BINANCE_DELIVERY: UNSUPPORTED,
        BLOCKCHAIN: 'l3',
        EXX: UNSUPPORTED,
        HUOBI: UNSUPPORTED,
        HUOBI_DM: UNSUPPORTED,
        OKCOIN: UNSUPPORTED,
        OKEX: UNSUPPORTED,
        BYBIT: UNSUPPORTED,
        FTX: UNSUPPORTED,
        FTX_US: UNSUPPORTED,
        GEMINI: UNSUPPORTED,
        BITCOINCOM: UNSUPPORTED,
        BITMAX: UNSUPPORTED,
        UPBIT: UNSUPPORTED,
        PROBIT: UNSUPPORTED
    },
    TRADES: {
        POLONIEX: TRADES,
        HITBTC: 'subscribeTrades',
        BITSTAMP: 'live_trades',
        BITFINEX: 'trades',
        COINBASE: 'matches',
        BITMEX: 'trade',
        KRAKEN: 'trade',
        KRAKEN_FUTURES: 'trade',
        BINANCE: 'aggTrade',
        BINANCE_US: 'aggTrade',
        BINANCE_FUTURES: 'aggTrade',
        BINANCE_DELIVERY: 'aggTrade',
        BLOCKCHAIN: 'trades',
        EXX: 'TRADE',
        HUOBI: 'trade.detail',
        HUOBI_DM: 'trade.detail',
        HUOBI_SWAP: 'trade.detail',
        OKCOIN: 'spot/trade',
        OKEX: '{}/trade',
        COINBENE: TRADES,
        DERIBIT: 'trades',
        BYBIT: 'trade',
        FTX: 'trades',
        FTX_US: 'trades',
        GEMINI: TRADES,
        BITTREX: TRADES,
        BITCOINCOM: 'subscribeTrades',
        BITMAX: TRADES,
        UPBIT: TRADES,
        GATEIO: 'trades.subscribe',
        PROBIT: 'recent_trades'
    },
    TICKER: {
        POLONIEX: 1002,
        HITBTC: 'subscribeTicker',
        BITFINEX: 'ticker',
        BITSTAMP: UNSUPPORTED,
        COINBASE: 'ticker',
        BITMEX: 'quote',
        KRAKEN: TICKER,
        KRAKEN_FUTURES: 'ticker_lite',
        BINANCE: 'ticker',
        BINANCE_US: 'ticker',
        BINANCE_FUTURES: 'ticker',
        BINANCE_DELIVERY: 'ticker',
        BLOCKCHAIN: UNSUPPORTED,
        HUOBI: UNSUPPORTED,
        HUOBI_DM: UNSUPPORTED,
        OKCOIN: '{}/ticker',
        OKEX: '{}/ticker',
        COINBENE: TICKER,
        DERIBIT: "ticker",
        BYBIT: UNSUPPORTED,
        FTX: "ticker",
        FTX_US: "ticker",
        GEMINI: UNSUPPORTED,
        BITTREX: 'SubscribeToSummaryDeltas',
        BITCOINCOM: 'subscribeTicker',
        BITMAX: UNSUPPORTED,
        UPBIT: UNSUPPORTED,
        GATEIO: UNSUPPORTED,
        PROBIT: UNSUPPORTED
    },
    VOLUME: {
        POLONIEX: 1003
    },
    FUNDING: {
        BITMEX: 'funding',
        BITFINEX: 'trades',
        BINANCE_FUTURES: 'markPrice',
        BINANCE_DELIVERY: 'markPrice',
        KRAKEN_FUTURES: 'ticker',
        DERIBIT: 'ticker',
        OKEX: '{}/funding_rate',
        FTX: 'funding',
        HUOBI_SWAP: 'funding'
    },
    OPEN_INTEREST: {
        OKEX: '{}/ticker',
        BITMEX: 'instrument',
        KRAKEN_FUTURES: 'ticker',
        DERIBIT: 'ticker',
        FTX: 'open_interest',
        BINANCE_FUTURES: 'open_interest',
        BINANCE_DELIVERY: 'open_interest',
        BYBIT: 'instrument_info.100ms'
    },
    LIQUIDATIONS: {
        BITMEX: 'liquidation',
        BINANCE_FUTURES: 'forceOrder',
        BINANCE_DELIVERY: 'forceOrder',
        FTX: 'trades',
        DERIBIT: 'trades',
        OKEX: LIQUIDATIONS,
    },
    FUTURES_INDEX: {
        BYBIT: 'instrument_info.100ms'
    }
}

_exchange_options = {
    LIMIT: {
        KRAKEN: 'limit',
        GEMINI: 'exchange limit',
        POLONIEX: 'limit',
        COINBASE: 'limit',
        BLOCKCHAIN: 'limit',
    },
    MARKET: {
        KRAKEN: 'market',
        GEMINI: UNSUPPORTED,
        POLONIEX: UNSUPPORTED,
        COINBASE: 'market',
        BLOCKCHAIN: 'market',
    },
    FILL_OR_KILL: {
        GEMINI: 'fill-or-kill',
        POLONIEX: 'fillOrKill',
        COINBASE: {'time_in_force': 'FOK'},
        KRAKEN: UNSUPPORTED,
        BLOCKCHAIN: 'FOK'
    },
    IMMEDIATE_OR_CANCEL: {
        GEMINI: 'immediate-or-cancel',
        POLONIEX: 'immediateOrCancel',
        COINBASE: {'time_in_force': 'IOC'},
        KRAKEN: UNSUPPORTED,
        BLOCKCHAIN: 'IOC'
    },
    MAKER_OR_CANCEL: {
        GEMINI: 'maker-or-cancel',
        POLONIEX: 'postOnly',
        COINBASE: {'post_only': 1},
        KRAKEN: 'post'
    }
}


def normalize_trading_options(exchange, option):
    if option not in _exchange_options:
        raise UnsupportedTradingOption
    if exchange not in _exchange_options[option]:
        raise UnsupportedTradingOption

    ret = _exchange_options[option][exchange]
    if ret == UNSUPPORTED:
        raise UnsupportedTradingOption
    return ret


def feed_to_exchange(exchange, feed, silent=False):
    def raise_error():
        exception = UnsupportedDataFeed(f"{feed} is not currently supported on {exchange}")
        if not silent:
            LOG.error("Error: %r", exception)
        raise exception

    if exchange == POLONIEX:
        if feed not in _feed_to_exchange_map:
            return pair_std_to_exchange(feed, POLONIEX)
    try:
        ret = _feed_to_exchange_map[feed][exchange]
    except KeyError:
        raise_error()

    if ret == UNSUPPORTED:
        raise_error()
    return ret
