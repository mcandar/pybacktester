import numpy as np
from strategy_tester.utils import dict_product
from strategy_tester.simulate import BackTest


class ParamSearch:
    def __init__(self,account,strategy,paramset):
        self.account = account
        self._strategy = strategy
        self._paramset = paramset
        self.output = []
        self._sid = 0

    @property
    def strategy(self):
        return self._strategy

    @property
    def paramset(self):
        return self._paramset

    def _run(self,params,*args,**kwargs):
        "Run for one set of hyperparameters."
        self.account.reset()
        sname = f'strategy_{self._sid}'
        strategy = self._strategy(id=self._sid,name=sname,**params)
        result = BackTest(self.account,strategy).run(*args,**kwargs)
        self.output.append(result)
        self._sid += 1
    

class Grid(ParamSearch):
    def run(self,*args,**kwargs):
        params = dict_product(self._paramset)
        list(map(lambda s: self._run(s,*args,**kwargs),params))
        return self


# TODO: check whether we should create the variable params at the initialization
# TODO: simplify the code
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