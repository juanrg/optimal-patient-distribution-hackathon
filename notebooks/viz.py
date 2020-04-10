import matplotlib.pyplot as plt
from simulationmodel import calc_daily_deaths
import numpy as np

def plot_deaths(deaths, ax=None):
    
    if type(deaths) != dict:
        print('wrong data type, expecting dictionary of arrays')
        print(type(deaths))
        return
    if ax is None:
        ax=plt.gca()
        
    ax.plot(deaths['unattended'].sum(axis=1), label='unattended', c='r')
    ax.plot(deaths['transport'].sum(axis=1), label='transport', c='g')
    ax.plot(deaths['total'].sum(axis=1), label='total', c='k')
#     ax2 = ax.twinx()
#     ax2.plot(deaths['total'].sum(axis=1).cumsum(), label='cumulativesum')
    
    ax.legend()

def plot_scenario_overview(movements, scenario_infos, titles = None):
    """
        movement is a list of array[day, node_from, node_to]
    """
    if type(movements) != list:
        print('wrong data type, excepting a list of movements')
        return
    
    maxcols = 4
    rows = 1+len(movements)//maxcols
    cols = min(len(movements),maxcols)
    
    fig, subps = plt.subplots(rows,cols,sharey='all', figsize=(4*cols,4*rows))
    
    if type(subps) == np.ndarray:
        subps = subps.flatten()
    elif type(subps) != list:
        subps = [subps]
        
    for i, (m, si) in enumerate(zip(movements, scenario_infos)):
        ax = subps[i]
        if titles is None:
            ax.set_title(f'Transport Scenario {i}')
        else:
            ax.set_title(titles[i])
            
        plot_deaths(calc_daily_deaths(movements=m, scenario_info=si), ax=ax)

