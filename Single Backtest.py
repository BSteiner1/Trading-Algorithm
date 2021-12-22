import numpy as np
import pandas as pd
import datetime as dt
import time 
from datetime import timedelta
from yahoo_fin import stock_info as si
import matplotlib as mpl
import matplotlib.pyplot as plt

#create user input for stock tickers
stock_ticker = input("Choose a stock ticker: ")
#stock_ticker = input("Select a stock ticker:")
#print("You selected", stock_ticker)
current_price = si.get_live_price(stock_ticker)
#print("The current price is", current_price)

#define start date and end date for required data
current_date = dt.datetime.now()
choose_start_date = current_date - timedelta(365)
#print(choose_start_date)
#choose_start_date = input("Select a start date (yyyy-mm-dd): ")

#create DataFrame of historical stock price
df = si.get_data(stock_ticker, start_date=choose_start_date, end_date=current_date)

#define length of short and long-term exponential moving average in days
shortEmas = [1, 2, 3, 5, 8, 10]
longEmas = [30, 35, 40, 45, 50, 60]
emasUsed = []
for x in shortEmas:
    emasUsed.append(x)
for x in longEmas:
      emasUsed.append(x)
#print(emasUsed)

#create our DataFrame 
for x in emasUsed:
    ema = x
    ema_Value = df.iloc[:,4].ewm(span=ema).mean()    #create our exponential moving averages for all x in emasUsed
    df["ema_" + str(ema)] = round(ema_Value, 3)           #create a new column for each ema length and round to 3dp

#define our initial conditions
position = 0            #0 denotes no position, 1 denotes active position
percent_change = []     #a list to add profit/loss % for all of our completed positions


fast_Ma = []
slow_Ma = []

print(df)

#this step will make our graph less busy so we only plot two lines instead of all 12 MAs
for i in df.index:
    cmax = max(df["ema_1"][i], df["ema_2"][i], df["ema_3"][i], df["ema_5"][i], df["ema_8"][i], df["ema_10"][i])        #min of short term emas
    cmin = min(df["ema_30"][i],df["ema_35"][i],df["ema_40"][i],df["ema_45"][i],df["ema_50"][i],df["ema_60"][i])     #max of long term emas
    fast_Ma.append(cmax)        
    slow_Ma.append(cmin)
    close_price = df['adjclose'][i]

    if cmax > cmin:                 #condition to take a position
        print("Red White Blue")
        if position == 0:
            position = 1
            print("Creating position")
            buy_price = close_price
            print(buy_price)

    elif cmin > cmax:               #condition to exit position
        print("Blue White Red")
        if position == 1:
            position = 0
            print("Exiting position")
            sell_price = close_price
            print(sell_price)
            pc = (sell_price/buy_price - 1)*100
            percent_change.append(pc)

#exit position if currently held
if position ==1:
    print("\nLast buy price was", buy_price)
    print("Current price is", current_price)
    final_sell = ((current_price/buy_price) - 1)*100
    percent_change.append(final_sell)

#print list of all completed trades
print("\nPercentage Changes:", percent_change)

#create a list of ratios to determine overall gains
new_list = []
for x in percent_change:
    new = 1 + x/100
    new_list.append(new)

print("Ratios:", new_list)

#create a new list net gain that accounts for re-investing with a different amount
#This is achieved by letting the ith entry be the product of the first i entreis of percent_change
net_gain = []
for i in range(len(new_list)):
    product = np.prod(new_list[:i])
    net_gain.append(product)

net_gain.append(0)
net_gain[-1] = net_gain[-2]*(percent_change[-1]/100 +1)

print("\nNet Gain: ", net_gain[1:])

#product of all ratios will give us total gains
PnL = net_gain[-1]
print("\nYou currently have", round(PnL, 5), "times what you started with")

#print results of trades
if PnL > 1:
    print("You have made", round((PnL - 1)*100, 5), "percent")
else:
    print("You lost", round((1-PnL)*100, 5), "percent")

#time.sleep(5)

#add new columns to our dataframe
df['Fast Moving Averages'] = fast_Ma
df['Slow Moving Averages'] = slow_Ma

#Create our buy and sell signals
Buy = []
Sell = []
Flag = 0        #0 denotes no position, 1 denotes current position held

#Check whether to buy, sell, or take no action
for i in range(0, len(df)):
    if df['Fast Moving Averages'][i] > df['Slow Moving Averages'][i]:
        Sell.append(np.nan)
        if Flag != 1:
            Flag = 1
            Buy.append(df['adjclose'][i])
        else:
            Buy.append(np.nan)
    elif df['Fast Moving Averages'][i] < df['Slow Moving Averages'][i]:
        Buy.append(np.nan)
        if Flag != 0:
            Flag = 0
            Sell.append(df['adjclose'][i])
        else:
            Sell.append(np.nan)
    else:                             #resolve indexing issues for first entry
        Sell.append(np.nan)     
        Buy.append(np.nan)      

#Add our buy and sell signals to our DataFrame
df['Buy'] = Buy
df['Sell'] = Sell

#create dynamic graph title depneding on earlier input
stock_title_name = "$" + str(stock_ticker).upper() + " stock price graph"

#create our graph to plot
plt.figure(figsize=(10, 4.5))       #define the sie of the graph shown
plt.scatter(df.index, Buy, color = 'green', label = 'Buy', marker = '^', alpha = 1, s=100)      #add our buy signals to our graph
plt.scatter(df.index, Sell, color = 'red', label = 'Sell', marker = 'v', alpha = 1, s=100)      #add our sell signals to our graph
#df.plot(y = ['adjclose', 'Slow Moving Averages', 'Fast Moving Averages'], kind='line', color = ('black', 'blue', 'red'))
plt.plot(df['adjclose'], label='Close', color='black')      #plot adjusted close
plt.plot(df['Fast Moving Averages'], label='Fast EMA', color='red', alpha=0.7)      #plot Fast Moving Averages graph
plt.plot(df['Slow Moving Averages'], label='Slow EMA', color='blue', alpha=0.7)     #plot Fast Moving Averages graph
plt.title(stock_title_name)
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.legend(loc = 'upper left')
plt.show()

#note: it seems to pick winners and lets them run, but also picks up too many single digit losses
#try to reduce the number of position changes it takes
#or dont sell so soon