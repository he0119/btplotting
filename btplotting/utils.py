import logging

import backtrader as bt

import itertools


_logger = logging.getLogger(__name__)


def paramval2str(name, value):
    if value is None:  # catch None value early here!
        return str(value)
    elif name == "timeframe":
        return bt.TimeFrame.getname(value, 1)
    elif isinstance(value, float):
        return f"{value:.2f}"
    elif isinstance(value, (list, tuple)):
        return ','.join(value)
    elif isinstance(value, type):
        return value.__name__
    else:
        return str(value)


def get_nondefault_params(params: object):
    return {key: params._get(key)
            for key in params._getkeys()
            if not params.isdefault(key)}


def get_params(params):
    return {key: params._get(key) for key in params._getkeys()}


def get_params_str(params):
    user_params = get_nondefault_params(params)
    plabs = [f"{x}: {paramval2str(x, y)}" for x, y in user_params.items()]
    plabs = '/'.join(plabs)
    return plabs


def find_by_plotid(strategy, plotid):
    '''
    Returns a object by its plotid.
    '''

    objs = itertools.chain(
        strategy.datas,
        strategy.getindicators(),
        strategy.getobservers())
    founds = []
    for obj in objs:
        if getattr(obj.plotinfo, 'plotid', None) == plotid:
            founds.append(obj)

    num_results = len(founds)
    if num_results == 0:
        return None
    elif num_results == 1:
        return founds[0]
    else:
        raise RuntimeError(f'Found multiple objects with plotid "{plotid}"')


def get_indicator_data(indicator):
    '''
    The indicator might have been created using a specific line
    (like SMA(data.lines.close)). In this case a LineSeriesStub
    has been created for which we have to resolve the original
    data.
    '''

    data = indicator.data
    if isinstance(data, bt.LineSeriesStub):
        return data._owner.data
    else:
        return data


def filter_by_datadomain(obj, datadomain):
    '''
    Returns if the given object should be included in datadomain.
    True if it should be included, False if not
    '''

    if datadomain is False:
        return True

    if isinstance(datadomain, str):
        datadomain = [datadomain]

    obj_lg = get_datadomain(obj)
    return obj_lg is False or obj_lg in datadomain


def get_datadomain(obj):
    '''
    Returns the datadomain for given object. A datadomain
    is basically the name of a data feed.
    If there is no datadomain -> False will be returned.
    '''

    if isinstance(obj, bt.Strategy):
        # strategy will have no datadomain
        return False
    elif isinstance(obj, bt.AbstractDataBase):
        # data feeds are end points
        return obj._name
    elif isinstance(obj, (bt.IndicatorBase, bt.ObserverBase)):
        # to get the datadomain for ind and obs, use clock
        return get_datadomain(obj._clock)
    else:
        # try to find a clock as last ressort
        return get_datadomain(get_clock_obj(obj))


def get_clock_obj(obj):
    '''
    Returns a clock object to use for building data
    '''

    if isinstance(obj, bt.LinesOperation):
        # indicators can be created to run on a line
        # (instead of e.g. a data object) in that case grab
        # the owner of that line to find the corresponding clock
        # also check for line actions like "macd > data[0]"
        return get_clock_obj(obj._clock)
    elif isinstance(obj, bt.LineSingle):
        # if we have a line, return its owners clock
        return get_clock_obj(obj._owner)
    elif isinstance(obj, bt.LineSeriesStub):
        # if its a LineSeriesStub object, take the first line
        # and get the clock from it
        return get_clock_obj(obj.lines[0])
    elif isinstance(obj, bt.StrategyBase):
        clk = obj
    elif isinstance(obj, bt.AbstractDataBase):
        clk = obj
    elif isinstance(obj, (bt.IndicatorBase, bt.ObserverBase)):
        clk = obj
    else:
        raise Exception(f'Unsupported object type passed: {obj.__class__}')
    return clk


def get_clock_line(obj):
    '''
    Find the corresponding clock for an object.
    A clock is a datetime line that holds timestamps for the line in question.
    '''

    clk = get_clock_obj(obj)
    return clk.lines.datetime


def get_source_id(source):
    '''
    Returns a unique source id for given source.
    This is used for unique column names.
    '''

    return str(id(source))
