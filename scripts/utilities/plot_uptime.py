import pandas as pd
import matplotlib.pyplot as plt
import os

UPTIME_LOG = 'uptime_history.csv'

def plot_uptime():
    if not os.path.exists(UPTIME_LOG):
        print('No uptime log found.')
        return
    df = pd.read_csv(UPTIME_LOG)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    plt.figure(figsize=(10,4))
    plt.plot(df['timestamp'], df['uptime_minutes'], marker='o', label='Uptime (min)')
    plt.scatter(df[df['event']=='CRASH']['timestamp'], df[df['event']=='CRASH']['uptime_minutes'], color='red', label='Crashes')
    plt.title('Bot Uptime & Crash History')
    plt.xlabel('Time')
    plt.ylabel('Uptime (minutes)')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_uptime()
