import hashlib
from uuid import uuid4

# from strategy_tester.utils import generate_id

# TODO: implement asset-to-account_balance currency conversion (assume USD account convert anything to USD) (write inside GETTER-SETTER?, every asset must have USD counterpart)
# TODO: implement bid-ask spread (instead of using only price and spread)
# TODO: Implement swap costs (both for long and short)


class Ticker:
    def __init__(
        self,
        aid,
        timestamp,
        price,
        spread,
        commissions,
        slippage,
        usd_equivalent,
    ):
        self.aid = aid
        self.timestamp = timestamp
        self.price = price
        self.spread = spread
        self.commissions = commissions
        self.slippage = slippage
        self.usd_equivalent = usd_equivalent

        self.attributes = (
            "aid",
            "timestamp",
            "price",
            "spread",
            "commissions",
            "slippage",
            "usd_equivalent",
        )

    def to_dict(self, attributes=None):
        if attributes is None:
            attributes = self.attributes

        return {attr: getattr(self, attr) for attr in attributes}

    def to_tuple(self, attributes=None):
        if attributes is None:
            attributes = self.attributes

        return (getattr(self, attr) for attr in attributes)


class TickerSet:
    def __init__(self, tickers):
        pass


class Asset:
    "Base financial instrument class that includes all common properties."

    def __init__(
        self,
        price,
        spread=0,
        commissions=0,
        slippage=0,
        lot_units=1,
        type="Main",
        name="Base",
        base="NA",
        quote="NA",
        usd_converter=None,
    ):
        # dynamic
        self.price = price
        self.spread = (
            [spread for _ in range(price.shape[0])]
            if isinstance(spread, (float, int))
            else spread
        )
        self.commissions = (
            [commissions for _ in range(price.shape[0])]
            if isinstance(commissions, (float, int))
            else commissions
        )
        self.slippage = (
            [slippage for _ in range(price.shape[0])]
            if isinstance(slippage, (float, int))
            else slippage
        )
        if quote.upper() != "USD":
            if usd_converter is not None:
                self.usd_equivalent = self.price * usd_converter
            else:
                raise ValueError(
                    "Argument `usd_converter` cannot be None if quote is not USD."
                )
        else:
            self.usd_equivalent = self.price

        # static
        self.base = base
        self.quote = quote
        self.lot_units = lot_units
        self.type = type
        self.name = name
        # self.id = generate_id(prefix=self.name, digits=4, timestamp=False)
        self.id = hashlib.sha1(
            f"{self.base}{self.quote}".encode("utf-8")
        ).hexdigest()
        self.registered = []
        self.n_registered = 0

    def reset(self):
        self.__init__()

    def features(self):
        output = vars(self).copy()
        del (
            output["price"],
            output["spread"],
            output["commissions"],
            output["slippage"],
            output["usd_equivalent"],
        )
        return output

    def register(self, *strategies):
        n = len(strategies)
        self.n_registered += n
        for strategy in strategies:
            strategy.on.append(self.id)
            self.registered.append(strategy.id)
        return strategies if n > 1 else strategies[0]

    def data(self):
        return [
            # {
            #    "timestamp": t[0],
            #    "price": t[1],
            #    "spread": t[2],
            #    "commissions": t[3],
            #    "slippage": t[4],
            #    "usd_equivalent": t[5],
            # }
            Ticker(
                aid=self.id,
                timestamp=t[0],
                price=t[1],
                spread=t[2],
                commissions=t[3],
                slippage=t[4],
                usd_equivalent=t[5],
            )
            for t in zip(
                self.price[:, 1],
                self.price[:, 0],
                self.spread,
                self.commissions,
                self.slippage,
                self.usd_equivalent,
            )
        ]


class Currency(Asset):
    "Currency class."

    def __init__(
        self,
        price,
        base,
        quote,
        spread=1e-4,
        commissions=0,
        swap={"long": 0, "short": 0},
        lot_units=100000,
        type="Currency",
        #        name="Base",
        *args,
        **kwargs,
    ):
        super().__init__(
            price=price,
            spread=spread,
            commissions=commissions,
            lot_units=lot_units,
            type=type,
            base=base,
            quote=quote,
            #            name=name,
            *args,
            **kwargs,
        )
        self.base = base
        self.quote = quote
        self.swap = swap


class Stock(Asset):
    def __init__(
        self,
        price,
        base,
        spread=1e-4,
        commissions=0,
        lot_units=1,
        type="Stock",
        quote="USD",
        *args,
        **kwargs,
    ):
        super().__init__(
            price=price,
            spread=spread,
            commissions=commissions,
            lot_units=lot_units,
            type=type,
            quote=quote,
            *args,
            **kwargs,
        )
        self.short_name = base
        self.base = base


class ETF:
    def __init__(self):
        pass


class Option:
    def __init__(self):
        pass


class Market:
    def __init__(self):
        self._info = "dummy"
