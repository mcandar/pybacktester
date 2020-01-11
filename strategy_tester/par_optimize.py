import numpy as np
from ray import tune
from strategy_tester.utils import dict_product, generate_data
from strategy_tester.account import Account
from strategy_tester.asset import EURUSD
from strategy_tester.simulate import BackTest
from strategy_tester.risk_management import ConstantRate
from strategy_tester.strategy import Strategy

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

class MACross(Strategy):
    def __init__(self,rate,**args):
        super().__init__(**args)
        self.rate=rate

    def decide_long_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                if exog[0] > exog[1] + exog[1]*self.rate:
                    args = {
                        'type':'market',
                        'size':self.RiskManagement.order_size(Account),
                        'strike_price':spot_price[asset_id]
                    }
                    output[asset_id] = args
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                if exog[0] < exog[1] - exog[1]*self.rate:
                    args = {
                        'type':'market',
                        'size':self.RiskManagement.order_size(Account),
                        'strike_price':spot_price[asset_id]
                    }
                    output[asset_id] = args
        return output
    
    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] < exog[1] - exog[1]*self.rate
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] > exog[1] + exog[1]*self.rate



# asset = EURUSD(generate_data(100000))
# account = Account(initial_balance=1000)
# slow_period = 45
# fast_period = 35
# sma = np.zeros((asset.data.shape[0],2))
# sma[(slow_period-1):,0] = moving_average(asset.data[:,1],slow_period)
# sma[(fast_period-1):,1] = moving_average(asset.data[:,1],fast_period)


def foo(config):
    print('Running...')
    asset = EURUSD(generate_data(100000))
    account = Account(initial_balance=1000)
    slow_period = 45
    fast_period = 35
    sma = np.zeros((asset.data.shape[0],2))
    sma[(slow_period-1):,0] = moving_average(asset.data[:,1],slow_period)
    sma[(fast_period-1):,1] = moving_average(asset.data[:,1],fast_period)
    risk_man = ConstantRate(config['lot_size'],on='free_margin')

    strategy = MACross(RiskManagement=risk_man,rate=config['rate'])
    strategy = asset.register(strategy)
    result = BackTest(account,strategy).run(assets=asset,exog=sma)
    tune.track.log(mean_accuracy=result.Account.balance)


analysis = tune.run(foo,
                    config={'rate':tune.grid_search([0.001, 0.01, 0.1]),
                            'lot_size':tune.grid_search([0.001, 0.01, 0.1])},
                    num_samples=10)

print("Best config: ", analysis.get_best_config(metric="mean_accuracy"))



import torch.optim as optim
from ray import tune
from ray.tune.examples.mnist_pytorch import (
    get_data_loaders, ConvNet, train, test)


def foo(config):
    train_loader, test_loader = get_data_loaders()
    model = ConvNet()
    optimizer = optim.SGD(model.parameters(), lr=config["lr"])
    for i in range(10):
        train(model, optimizer, train_loader)
        acc = test(model, test_loader)
        tune.track.log(mean_accuracy=acc)

analysis = tune.run(
    foo, config={"lr": tune.grid_search([0.001, 0.01, 0.1])})

print("Best config: ", analysis.get_best_config(metric="mean_accuracy"))

df = analysis.dataframe()



class Grid(ParamSearch):
    def run(self,*args,**kwargs):
        params = dict_product(self._paramset)
        list(map(lambda s: self._run(s,*args,**kwargs),params))
        return self


# TO DO: check whether we should create the variable params at the initialization
# TO DO: simplify the code
class Random(ParamSearch):
    def __init__(self,q,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if not 0 < q < 1:
            raise ValueError('q must be in (0,1)')
        self.q = q

    def run(self,*args,**kwargs):
        params = list(dict_product(self._paramset))
        size = len(params)
        self.n = int(size*self.q)

        idxs = np.random.randint(0,size,self.n,dtype=int)
        params = [params[i] for i in idxs]

        list(map(lambda s: self._run(s,*args,**kwargs),params))
        return self


if __name__ == '__main__':
    from strategy_tester.utils import generate_data, dict_product
    from strategy_tester.account import Account
    from strategy_tester.strategy import Strategy
    from strategy_tester.risk_management import ConstantRate

    data     = generate_data(100000)
    account  = Account(balance=1000)
    paramset = {'RiskManagement':[ConstantRate(0.05),ConstantRate(0.1),ConstantRate(0.2)]}
    sim      = Random(0.7,account,Strategy,paramset).run(data.values)
    print(sim.output)