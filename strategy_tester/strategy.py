import numpy as np

# TO DO: create several built-in strategies
# TO DO: edit this class to be a generic super class
# TO DO: use a decorator to simplify methods?
class Strategy:
    """Open, modify, and close orders. By modification, we could keep a 
    number of variables, in order to track its performance and make decisions."""
    def __init__(self,RiskManagement,id=None,name=None):
        self.RiskManagement = RiskManagement
        self.id = id
        self.name = name
        self.on = []
    
    def __include_identifiers(self,args):
        args['strategy_id'] = self.id
        args['strategy_name'] = self.name
        return args
    
    def __random_decision(self,p=0.01):
        return np.random.uniform(0,1,1)[0] < p
    
    def check_registered_assets(self):
        if len(self.on) == 0:
            raise AttributeError('No asset is registered. Set a target instrument to `on` to use this strategy.')
    
    # TO DO: bring preprocessing back to life
    def preprocess(self,spot_price,timestamp,Account,RiskManagement,exog=None):
        return exog
    
    def postprocess(self,decision,args):
        "Last checks and corrections."
        args = self.__include_identifiers(args)
        return decision, args

    def __long_open(self,spot_price,timestamp,Account,exog=None):
        args = {
        'type':'market',
        'size':self.RiskManagement.order_size(Account),
        'strike_price':spot_price,
        'stop_loss':0.001,
        'take_profit':0.001
        }
        return self.__random_decision(), args

    def __short_open(self,spot_price,timestamp,Account,exog=None):
        args = {
        'type':'market',
        'size':self.RiskManagement.order_size(Account),
        'strike_price':spot_price,
        'stop_loss':0.001,
        'take_profit':0.001
        }
        return self.__random_decision(), args
    
    # TO DO: check exog variable usage later
    def long_open(self,spot_price,timestamp,Account,exog=None):
        decision, args = self.__long_open(spot_price=spot_price,
                                          timestamp=timestamp,
                                          Account=Account,
                                          exog=exog)
        return self.postprocess(decision, args)
    
    def short_open(self,spot_price,timestamp,Account,exog=None):
        if exog is not None:
            exog = self.preprocess() # TO DO: supply correct function arguments
        decision, args = self.__short_open(spot_price=spot_price,
                                           Account=Account,
                                           timestamp=timestamp,
                                           exog=exog)
        return self.postprocess(decision, args)
    
    def long_modify(self,order,spot_price,Account,exog=None):
        "Set attributes, and check order's state to track the performance."
        return order
    
    def short_modify(self,order,spot_price,Account,exog=None):
        return order
    
    def long_close(self,order,spot_price,Account,exog=None):
        if order.position != 'long':
            ValueError(f'Position is expected to be long, got {order.position}')
        return self.__random_decision()

    def short_close(self,order,spot_price,Account,exog=None):
        if order.position != 'short':
            ValueError(f'Position is expected to be short, got {order.position}')
        return self.__random_decision()