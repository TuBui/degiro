import os
import json
import matplotlib
# matplotlib.use('Agg')  # headless run
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from yahoo_fin import stock_info as si


def pretty_json(data):
    return json.dumps(data, indent=4, sort_keys=True)


def dict2dataframe(dictionary, col='info'):
    """convert a dict to pandas dataframe where each key, val is one row"""
    df = pd.DataFrame(index=dictionary.keys(), columns=[col])
    df[col] = dictionary.values()
    return df 


def plot_historic_price(x, y, t, prod, outdir='logs'):
    """
    plot price curve between two dates
    Args:
        x   x-axis data
        y   y-axis data (price)
        t   tuple (start_date, end_date)
        prod Product object, containing basic info about the stock such as symbol, name, currency etc.
        outdir output dir to save the plot
    Return:
        no return
    """
    n = len(x)
    x = [x_ - min(x) for x_ in x]
    y_min, y_max = min(y), max(y)
    x_min, x_max = x[y.index(y_min)], x[y.index(y_max)]  # corresponding x position of y_min and y_max
    plt.plot(x,y,'b', linewidth=2)
    plt.plot(x_min, y_min, 'ro', markersize=5)
    plt.text(0, y_min, str(y_min), color='r')
    plt.plot(x, [y_min]*n, 'r')
    plt.plot(x_max, y_max, 'go', markersize=5)
    plt.text(0, y_max, str(y_max), color='g')
    plt.plot(x, [y_max]*n, 'g')

    # get tick labels for x axis
    y_t = pd.date_range(t[0], t[1], periods=max(x)+1).to_pydatetime()
    y_t = [y_t[x_] for x_ in x]  # corresponding timestamps of x
    gap = max(n//10,1)
    x_t = x[::gap]  # x ticks
    y_t = y_t[::gap]
    interval = t[1] - t[0]
    if interval.days*3600*24 + interval.seconds <= 3600*24:  # a day or less
        y_t = [t.strftime('%H:%M:%S') for t in y_t]
    elif interval.days <= 31:  # month or less
        y_t = [t.strftime('%m-%d') for t in y_t]
    else:
        y_t = [t.strftime('%Y-%m-%d') for t in y_t]
    plt.xticks(x_t, y_t, rotation=90)

    plt.grid(which='major', linestyle='dotted')
    plt.title(f'{prod._name} {prod._symbol}', fontsize=16)
    plt.ylabel(f'{prod._currency}', fontsize=14)
    plt.savefig(os.path.join(outdir, f'{prod._name}.jpg'), dpi=200, bbox_inches = 'tight')
    plt.show()


def get_yahoo_fin(prod, outdir):
    """
    Query exhaustive information of a stock on Yahoo finance and output to a worksheet
    Args:
        prod    Product object, containing basic info about the stock such as symbol, name, currency etc.
        start_date  start date string such as '1/1/2018' or '2018-1-1T00:00:00'
        end_date    end date string such as '30/12/2018' ...
        outdir  output dir to save the plot
    Return:
        no return
    """
    ticker = prod._symbol
    out_path = os.path.join(outdir, f'{prod._name}.xlsx')
    print(f'Retrieving data for {prod._name} ...')
    writer = pd.ExcelWriter(out_path,engine='xlsxwriter')  # Creating Excel Writer Object from Pandas  

    # summary, quote table, stats
    print('\tQuerying summary/quote table/stats ...')
    row_count = 0
    summ = {'name': prod._name, 'id': prod._id, 'symbol': prod._symbol, 
            'close price': prod._closeprice,
            'close date': prod._closedate, 
            'current price': si.get_live_price(ticker),
            'vwdId': prod._vwdId}
    df_summ = dict2dataframe(summ, 'info')
    df_summ.rename_axis('Summary', axis='index', inplace=True)
    df_summ.to_excel(writer, sheet_name='Summary', startrow=row_count, startcol=0)
    row_count = row_count + len(df_summ) + 2

    df_quote = dict2dataframe(si.get_quote_table(ticker))
    df_quote.rename_axis('Quote table', axis='index', inplace=True)
    df_quote.to_excel(writer, sheet_name='Summary', startrow=row_count, startcol=0)
    row_count = row_count + len(df_quote) + 2

    df_stats = si.get_stats(ticker)
    df_stats.rename_axis('Stats', axis='index', inplace=True)
    df_stats.to_excel(writer, sheet_name='Summary', startrow=row_count, startcol=0)
    row_count = row_count + len(df_stats) + 2

    # analyst
    print('\tQuerying analyst ...')
    ana = si.get_analysts_info(ticker)  # this return a dict of pandas dataframes
    row_count = 0
    for key, df in ana.items():
        df.name = key
        df.to_excel(writer, sheet_name='Analyst Info', startrow=row_count, startcol=0)
        row_count = row_count + len(df) + 2

    # balance sheet
    print('\tQuerying balance ...')
    df_bal = si.get_balance_sheet(ticker)
    df_bal.to_excel(writer,sheet_name='Balance', startrow=0 , startcol=0)

    # cash flow
    print('\tQuerying cash flow ...')
    df_cash = si.get_cash_flow(ticker)
    df_cash.to_excel(writer,sheet_name='Cash flow', startrow=0 , startcol=0)

    # data
    print('\tQuerying historic data ...')
    df_data = si.get_data(ticker)
    df_data.sort_index(ascending=False, inplace=True)
    df_data.to_excel(writer,sheet_name='Data', startrow=0 , startcol=0)

    # financial
    print('\tQuerying financial ...')
    fin = si.get_financials(ticker)  # this return a dict of dataframes
    row_count = 0
    for key, df in fin.items():
        df.rename_axis(key, axis='index', inplace=True)
        df.to_excel(writer, sheet_name='Financial', startrow=row_count, startcol=0)
        row_count = row_count + len(df) + 2

    # save
    writer.save()
    print(f'Data saved to {out_path}')