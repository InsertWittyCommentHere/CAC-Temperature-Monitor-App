#  Author : Riyan
#  Description:
#  First release:

try:
    from smbus2 import SMBus
    from mlx90614 import MLX90614
    import RPi.GPIO as GPIO
except ImportError:
    print("Module not found!!")

from flask import Flask, request, render_template, session
from datetime import datetime
import time
import pandas as pd
import json
import plotly
import plotly.express as px

app = Flask(__name__)

try:
    bus = SMBus(1)
    sensor = MLX90614(bus, address=0x5A)
except Exception as e:
    print("SMbus or MLX not available. Read Exception", e)
channels = [5, 6, 26]

# time to keep the GPIO pin HIGH
TIME = 2

try:
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channels, GPIO.OUT)
except Exception as e:
    print("GPIO is not defined. Read Exception", e)

def fwrite(data):
    f = open("readings.txt", "a")
    f.write(data)
    f.close()



def green_led():
    try:
        GPIO.output(6, GPIO.HIGH)
        time.sleep(TIME)
        GPIO.output(6, GPIO.LOW)
    except Exception as e:
        print("GPIO is not defined. Read Exception", e)

def red_led():
    try:
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(TIME)
        GPIO.output(5, GPIO.LOW)
        GPIO.output(26, GPIO.LOW)
    except Exception as e:
        print("GPIO is not defined. Read Exception", e)

def c2f(c):
    f_read = "{:.2f}".format((c * 9/5) + 32)
    return str(f_read)




def getstats(d):
    stats = [0, 0]
    for i in d['status']:
        if i == "Normal":
            stats[0] += 1
        else:
            stats[1] += 1
    return stats


@app.route('/read1', methods=['POST', 'GET'])
def read2():
    return render_template('index2.html')

@app.route('/read2', methods=['POST', 'GET'])
def getTemp():
    if request.method == 'GET':
        print("inside get-temp GET try")
        try:
            a_temp_c = sensor.get_ambient()
            o_temp_c_raw = sensor.get_object_1()
            o_temp_c = "{:.2f}".format(o_temp_c_raw)
            print(o_temp_c)
            #return str(a_temp_c), str(o_temp_c)
            str = c2f(float(o_temp_c) + 4.5)
            session['temp'] = str
            if float(str) >= 99.5:
                red_led()
                return render_template("redindex3.html", temperature=str)

            if float(str) < 99.5:
                green_led()
                GPIO.output(6, GPIO.HIGH)
                time.sleep(3)
                GPIO.output(6, GPIO.LOW)
                return render_template('index3.html', temperature=str)
        except OSError as error :
            print(error)
            print("It looks like MLX sensor have trouble connecting. Try running i2cdetect command!")
            return render_template('error.html')
        except Exception as e:
            print("Something went wrong")
            print("Likely something is not defined")
            return render_template('error.html')

    if request.method == 'POST':
        try:
            print("inside POST try")
            barcode_read = request.form['barcode']
            print(barcode_read, session.get('temp'))

            # dd/mm/YY H:M:S
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            if temp < 99.5:
                color = 'green'
            else:
                color = 'red'
            fwrite(dt_string + " , " + barcode_read + " , " + session.get('temp') + " , " + color + "\n")
            return render_template('index2.html')
        except Exception as e:
            print(e)
            print("something wrong happened")
            return render_template('error.html')



@app.route('/', methods=['POST', 'GET'])
def index2():
    return render_template('login.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    return render_template('login.html')



@app.route('/graphs', methods=['POST', 'GET'])
def plotgraphs():
    tmp_list = []
    allrecords = []
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []


    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    # create dataframes by date
    df_20211016 = df_all[df_all['date'] == '2021-10-16']
    df_20211017 = df_all[df_all['date'] == '2021-10-17']
    df_20211018 = df_all[df_all['date'] == '2021-10-18']
    df_20211019 = df_all[df_all['date'] == '2021-10-19']
    df_20211020 = df_all[df_all['date'] == '2021-10-20']
    df_20211021 = df_all[df_all['date'] == '2021-10-21']

    df = df_all
    # Line Chart
    fig = px.line(df, x='date', y='temp', color='name', title='Line Plot')
    graphJSON_line = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Bar chart
    fig = px.bar(df, x='date', y='temp', color='temp', title='Bar Plot', barmode='group')
    graphJSON_bar = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211016_stats = []
    df_20211017_stats = []
    df_20211018_stats = []
    df_20211019_stats = []
    df_20211020_stats = []
    df_20211021_stats = []

    df_20211016_stats = getstats(df_20211016)
    df_20211017_stats = getstats(df_20211017)
    df_20211018_stats = getstats(df_20211018)
    df_20211019_stats = getstats(df_20211019)
    df_20211020_stats = getstats(df_20211020)
    df_20211021_stats = getstats(df_20211021)

    print("---")
    print(df_20211016_stats)
    print(df_20211017_stats)
    print(df_20211018_stats)
    print(df_20211019_stats)
    print(df_20211020_stats)
    print(df_20211021_stats)

    # print(df)
    # print(df.dtypes)
    return render_template('plots.html',
                           tables=[df.to_html(classes='data')],
                           titles=df.columns.values,
                           graphJSON_line=graphJSON_line,
                           graphJSON_bar=graphJSON_bar,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211016_stats=df_20211016_stats,
                           df_20211017_stats=df_20211017_stats,
                           df_20211018_stats=df_20211018_stats,
                           df_20211019_stats=df_20211019_stats,
                           df_20211020_stats=df_20211020_stats,
                           df_20211021_stats=df_20211021_stats)


@app.route('/plot16', methods=['POST', 'GET'])
def plot16():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211016 = df_all[df_all['date'] == '2021-10-16']
    df = df_20211016

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-16')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211016_stats = getstats(df_20211016)
    df = df.sort_values('status')

    return render_template('plots16.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211016_stats=df_20211016_stats)

@app.route('/plot17', methods=['POST', 'GET'])
def plot17():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211017 = df_all[df_all['date'] == '2021-10-17']
    df = df_20211017

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-17')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211017_stats = getstats(df_20211017)
    df = df.sort_values('status')

    return render_template('plots17.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211017_stats=df_20211017_stats)

@app.route('/plot18', methods=['POST', 'GET'])
def plot18():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211018 = df_all[df_all['date'] == '2021-10-18']
    df = df_20211018

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-18')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211018_stats = getstats(df_20211018)
    df = df.sort_values('status')

    return render_template('plots18.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211018_stats=df_20211018_stats)

@app.route('/plot19', methods=['POST', 'GET'])
def plot19():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211019 = df_all[df_all['date'] == '2021-10-19']
    df = df_20211019

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-19')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211019_stats = getstats(df_20211019)
    df = df.sort_values('status')

    return render_template('plots19.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211019_stats=df_20211019_stats)

@app.route('/plot20', methods=['POST', 'GET'])
def plot20():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211020 = df_all[df_all['date'] == '2021-10-20']
    df = df_20211020

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-20')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211020_stats = getstats(df_20211020)
    df = df.sort_values('status')

    return render_template('plots20.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211020_stats=df_20211020_stats)

@app.route('/plot21', methods=['POST', 'GET'])
def plot21():
    tmp_list = []
    allrecords = []
    # fr = open("readings-full.txt", "r")
    fr = open("out.csv", "r")
    records = fr.readlines()
    for i in records:
        tmp_list = i.strip().split(',')
        allrecords.append(tmp_list)
        tmp_list = []
    print(allrecords)

    df_all = pd.DataFrame(allrecords, columns=['date', 'name', 'temp', 'status', 'phone', 'email'])
    df_all['temp'] = df_all['temp'].astype(float)

    df_20211021 = df_all[df_all['date'] == '2021-10-21']
    df = df_20211021

    # Scatter chart
    fig = px.scatter(df, x='name', y='temp', color='status', title='Scatter Plot 2021-10-21')
    graphJSON_scatter = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    df_20211021_stats = getstats(df_20211021)
    df = df.sort_values('status')

    return render_template('plots21.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           graphJSON_scatter=graphJSON_scatter,
                           df_20211021_stats=df_20211021_stats)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True, host='0.0.0.0')
