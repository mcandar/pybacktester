import numpy as np

# TODO: change the name to a more appropriate one (e.g. order sizing, lot optimization, etc.?)


class RiskManagement:
    "Apply risk management and order sizing methods."

    def __init__(self, size_min=0.01, size_max=50, digits=2):
        self.size_min = size_min
        self.size_max = size_max
        self.digits = digits

    def _order_size(self, Account, exog=None):
        return np.random.uniform(0, Account.balance / 1000, 1)[0]

    def postprocess(self, size):
        if size > self.size_max:
            size = self.size_max
        elif size < self.size_min:
            size = self.size_min
        return round(size, self.digits)

    def order_size(self, Account, exog=None, *args, **kwargs):
        size = self._order_size(Account=Account, exog=exog, *args, **kwargs)
        return self.postprocess(size)


class KellyCriterion(RiskManagement):
    def __init__(self, n=10, default_lots=0.01, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = n
        self.default_lots = default_lots

    def _order_size(self, Account, exog=None):
        if Account.n_inactive_orders < self.n:
            return self.default_lots
        else:
            last_n_orders = list(Account.inactive_orders.values())[-self.n :]
            stats = np.array(
                [[order.profit, order.size] for order in last_n_orders]
            )
            p_lose = np.sum(stats[:, 0] < 0) / self.n
            p_win = 1 - p_lose
            ave_size = np.mean(stats[:, 1])
            ave_profit = np.mean(stats[:, 0])
            return p_win - (p_lose / (ave_profit - ave_size))


class ConstantLots(RiskManagement):
    def __init__(self, lots=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lots = lots

    def _order_size(self, Account, exog=None):
        return self.lots


class ConstantRate(RiskManagement):
    def __init__(self, rate=0.1, on="balance", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate = rate
        self.on = on

    def _order_size(self, Account, exog=None):
        return self.rate * getattr(Account, self.on)


class AccountVarianceBased(RiskManagement):
    def __init__(
        self,
        n=20,
        on="balances",
        default_lots=0.01,
        multiplier=1,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.n = n
        self.on = on
        self.default_lots = default_lots
        self.multiplier = multiplier

    def _order_size(self, Account, exog=None):
        if Account.n_inactive_orders < self.n:
            return self.default_lots
        else:
            var = np.var(getattr(Account, self.on)[-self.n :])
            return self.multiplier / var


class VolatilityBased(RiskManagement):
    def __init__(self):
        pass


class ConsecutiveResult(RiskManagement):
    def __init__(self):
        pass


class EqualWeight(RiskManagement):
    def _order_size(self, Account, exog=None, n=None, price=None):
        if Account.n_active_orders == 0:
            self.investable_capital = Account.balance

        return np.floor(self.investable_capital / (n * price)).astype(int)