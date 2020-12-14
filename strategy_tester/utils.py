import itertools, logging, random
from datetime import datetime as dt
import numpy as np
import pandas as pd

# TODO: use time index!!!!
# TODO: write a strategy class checker (keep it simple, only for necessary method and attributes)


def generate_data(n, start_date="2020-01-01 00:00:00", freq="1min", digits=5):
    price = np.round(np.exp(np.cumsum(np.random.laplace(0, 0.02, n))), digits)

    start = pd.to_datetime(start_date)
    # end = start + (pd.Timedelta(freq) * (price.shape[0] - 1))
    ts = pd.date_range(start, periods=n, freq=freq)
    return pd.DataFrame({"timestamp": ts, "price": price}).values


def dict_product(dicts):
    """
    >>> list(dict_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))


## TODO: apply a generic ID convention to all classes
# def generate_id(prefix="", suffix="", digits=6, timestamp=True):
#    ts = f"TS{int(dt.utcnow().timestamp())}" if timestamp else ""
#    return f"{prefix}{random.randint(10**(digits-1),10**digits-1)}{ts}{suffix}"


def ROI(Account):
    return (
        Account.balance - Account.initial_balance
    ) / Account.initial_balance


def sharpe_ratio(Account, risk_free_rate=0.05):
    sigma = Account.balances["balance"].std()
    if sigma == 0:
        return np.nan
    else:
        return (ROI(Account) - risk_free_rate) / sigma


def error_logger(level=logging.WARNING):
    error_log_level = level
    error_log = logging.getLogger("error_logger")
    error_log.setLevel(error_log_level)
    fh = logging.FileHandler("../error.log")
    fh.setLevel(error_log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s: %(module)s - %(funcName)s - %(process)d - %(message)s"
    )
    fh.setFormatter(formatter)
    error_log.addHandler(fh)
    return error_log


def transaction_logger(level=logging.WARNING):
    fh = logging.FileHandler("../transaction.log")
    fh.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)

    TRANSACTION = 20
    logging.addLevelName(TRANSACTION, "TRANSACTION")

    def transaction(self, message, *args, **kws):
        self.log(TRANSACTION, message, *args, **kws)

    logging.Logger.transaction = transaction
    transaction_log = logging.getLogger("transaction_log")
    transaction_log.setLevel(TRANSACTION)
    transaction_log.addHandler(fh)

    return transaction_log