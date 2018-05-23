import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
import plotly.plotly as py
from plotly.graph_objs import *
from scipy.stats import rayleigh
from flask import Flask
import numpy as np
import pandas as pd
import os
import sqlite3
import datetime as dt
from AeroSpike_production import AerospikeClient
import time
import ipaddress
import dash_table_experiments as dte
from datetime import timedelta
import flask
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = dash.Dash('streaming-wind-app')


server = app.server
points_per_second = 10
readRange = 300 # history lenght
aero = AerospikeClient()
aero.connect()

app.layout = html.Div([
    html.Link(href='/home/user/Desktop/hrpi/static/style.css', rel='stylesheet'),
    html.Div([
        html.H2("HRPI Anal"),
        html.Img(src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png"),
    ], className='banner'),
    html.Div([
        html.Div([
            html.H3("HRPI Graph")
        ], className='Title'),	 
        html.Div([
            dcc.Graph(id='wind-speed'),
        ], className='twelve columns wind-speed'),
        dcc.Interval(id='wind-speed-update', interval=1000, n_intervals=0),
    ], className='row wind-speed-row'),
        html.Div([
           dcc.Interval(id='iptable-update', interval=1000, n_intervals=0),
           dte.DataTable(
               id='iptable',
               rows='',
               columns=['IP address', 'Request count'],
               max_rows_in_viewport=1000,
               row_height=32,
               resizable=False,
               editable=False,
               row_selectable=False,
               filterable=False,
               sortable=False,
               enable_drag_and_drop=False,
            ),
        ], className='iptable-table'),
         html.Div([
            html.Br(),                   
            html.Div([ 
                      html.Br(),
                      dcc.Input(id='date_input',type='Date',value=dt.date.today())],                  
                      style={'width': '50%'}),
                      html.Label('Select hour to display'),
                      dcc.Dropdown(id='my-dropdown',options=                                         
                        [{'label': '00 h.', 'value': 0},
                        {'label': '01 h.', 'value': 1},
                        {'label': '02 h.', 'value': 2},
                        {'label': '03 h.', 'value': 3},
                        {'label': '04 h.', 'value': 4},
                        {'label': '05 h.', 'value': 5},
                        {'label': '06 h.', 'value': 6},
                        {'label': '07 h.', 'value': 7},
                        {'label': '08 h.', 'value': 8},
                        {'label': '09 h.', 'value': 9},
                        {'label': '10 h.', 'value': 10},
                        {'label': '11 h.', 'value': 11},
                        {'label': '12 h.', 'value': 12},
                        {'label': '13 h.', 'value': 13},
                        {'label': '14 h.', 'value': 14},
                        {'label': '15 h.', 'value': 15},
                        {'label': '16 h.', 'value': 16},
                        {'label': '17 h.', 'value': 17},
                        {'label': '18 h.', 'value': 18},
                        {'label': '19 h.', 'value': 19},
                        {'label': '20 h.', 'value': 20},
                        {'label': '21 h.', 'value': 21},
                        {'label': '22 h.', 'value': 22},
                        {'label': '23 h.', 'value': 23}],
                        value='0'),
                    dcc.Dropdown(id='minute-dropdown',options=
                     [{'label': '00-05 min.', 'value': 0},
                     {'label': '05-10 min.', 'value': 5},
                     {'label': '10-15 min.', 'value': 10},
                     {'label': '15-20 min.', 'value': 15},
                     {'label': '20-25 min.', 'value': 20},
                     {'label': '25-30 min.', 'value': 25},
                     {'label': '30-35 min.', 'value': 30},
                     {'label': '45-50 min.', 'value': 45},
                     {'label': '50-55 min.', 'value': 50},
                     {'label': '55-60 min.', 'value': 55}], value = '0'),
                    html.Br(),
                    html.Div(id='input_container'), 
                     
                
            html.Button('Generate history', id='history_button'),        
            dcc.Graph(id='history-table'),
                         
        ], className='twelve columns history-table'),
        dcc.Interval(id='history-table-update', interval=1000, n_intervals=0),
    ], style={'padding': '0px 10px 15px 10px',
          'marginLeft': 'auto', 'marginRight': 'auto', "width": "900px",
          'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)'})
#------------------------------History-update-----------------------------------------
@app.server.route('/static/<resource>')
def serve_static(resource):
 return flask.send_from_directory(STATIC_PATH, resource)
#------------------------------History-lentele-----------------------------------------
@app.callback(Output('history-table','figure'), [Input('history_button', 'n_clicks'), Input('my-dropdown', 'value'),Input('minute-dropdown', 'value'),Input('date_input', 'value')])
def gen_history_table(interval,valueHours,valueMinutes, valueDate):
    print("----------")
    print(valueHours)
    print(valueDate)
    print("----------")
    #ltime = int(time.time() * points_per_second)
    #dataSpike = aero.getData(timeFrom=ltime - readRange, timeTo=ltime - 10)
    #update_time =  dt.datetime.strptime(valueDate, "%d-%m-%Y").timestamp()
    update_time =  int(time.mktime(dt.datetime.strptime(valueDate, "%Y-%m-%d").timetuple()))
    print("**************")
    print(update_time)
    print("**************")
    timeReadFrom = (update_time + int(valueHours)*3600 + int(valueMinutes) * 60) * 10
    timeReadTo = (update_time + int(valueHours)*3600 +  (int(valueMinutes) + 5) * 60) * 10
    dataSpike = aero.getHistoryData(timeFrom=timeReadFrom, timeTo=timeReadTo)
    hrpi_array = []
    eval_array = []
    stamps_array = []
    for record in dataSpike:
     if (record[1] != None):
       stamps_array.append(int(record[0][2])*100)
       hrpi_array.append(str(record[2].get('data')))
       if (record[2].get('eval') == 0):
            eval_array.append(0)
       else:
            eval_array.append(1 + record[2].get('attack'))

    trace = Scatter(
        x=stamps_array,
        y=hrpi_array,
        line=Line(
            color='#42C4F7'
        ),
        hoverinfo='skip',
        mode='markers+lines',
        visible=True,
        marker=dict(
           size='7',
           cmin=0,
           cmax=2,
           cauto=False,
           color=eval_array,
           showscale=True,
           colorscale=[
                    [0, 'rgb(0,255,0)'],
                    [0.33, 'rgb(0,255,0)'],

                    [0.33, 'rgb(255,255,0)'],
                    [0.66, 'rgb(255,255,0)'],

                    [0.66, 'rgb(255,0,0)'],
                    [1, 'rgb(255,0,0)'],
          ],
          colorbar=dict(
                    tickmode='array',
                    title='Pavojaus Lygis',
                    titleside='top',
                    tickvals=[0.4, 1, 1.6],
                    ticktext=['Saugu', 'Itartina', 'Pavojinga'],
                    dtick=(1)
          )
          
       )
     
        
    )
    layout = dict(
            title='History',
            height=600,
            xaxis=dict(
                constrain='range',
                constraintoward='right',
                #range=[hrpiTime[0], hrpiTime[-1]],
                autorange=True,
                # range=xrange,
                
                rangeslider=dict(
                    autorange=True,
                    #range=[hrpiTime[0], hrpiTime[-1]],
                    yaxis=dict(
                        rangemode='match'
                    )
                ),
                type='date'
            ),
            yaxis=dict(
                fixedrange=True,
                range=list([0, 3]),
                autorange=False,
                nticks=6,
            )
        )
    return Figure(data=[trace], layout=layout)
  
#---------------------------------IP-lentele--------------------------------------
@app.callback(Output('iptable', 'rows'), [Input('iptable-update', 'n_intervals')])
def gen_ip_table(interval):
    ltime = int(time.time() * points_per_second)
    records = aero.getDataIP(timeFrom=ltime-readRange, timeTo=ltime+10)
    ip_requests = {}
    request_sum = 0
    for record in records:
                if (record[1] != None):
                    IPlist = record[2]
                    if IPlist is not None:
                     for IP in IPlist.items():
                        IP_address = (str(ipaddress.IPv4Address(int(IP[0]))))
                        ip_requests[IP_address] = ip_requests.get(IP_address, 0) + IP[1]
                        request_sum += IP[1]
                                      
    ip_count = len(ip_requests)                                 
    ip_table = list()
    for IP, count in ip_requests.items():
       ip_table.append({'IP address': IP, 'Request count' : count})
    ip_table.sort(key=lambda x: -x['Request count'])
    return ip_table


#---------------------------------HRPI grafikas------------------------------------------
@app.callback(Output('wind-speed', 'figure'),[Input('wind-speed-update', 'n_intervals')])
def gen_wind_speed(interval):
    ltime = int(time.time() * points_per_second)
    #print(ltime)
    dataSpike = aero.getData(timeFrom=ltime-readRange, timeTo=ltime+10)
    hrpi_array = []
    eval_array = []
    stamps_array = []
    for record in dataSpike:
     if (record[1] != None):
       stamps_array.append(int(record[0][2])*100)
       hrpi_array.append(str(record[2].get('data')))
       if (record[2].get('eval') == 0):
            eval_array.append(0)
       else:
            eval_array.append(1 + record[2].get('attack'))

    trace = Scatter(
        x=stamps_array,
        y=hrpi_array,
        line=Line(
            color='#42C4F7'
        ),
        hoverinfo='skip',
        mode='markers+lines',
        visible=True,
        marker=dict(
           size='7',
           cmin=0,
           cmax=2,
           cauto=False,
           color=eval_array,
           showscale=True,
           colorscale=[
                    [0, 'rgb(0,255,0)'],
                    [0.33, 'rgb(0,255,0)'],

                    [0.33, 'rgb(255,255,0)'],
                    [0.66, 'rgb(255,255,0)'],

                    [0.66, 'rgb(255,0,0)'],
                    [1, 'rgb(255,0,0)'],
          ],
          colorbar=dict(
                    tickmode='array',
                    title='Pavojaus Lygis',
                    titleside='top',
                    tickvals=[0.4, 1, 1.6],
                    ticktext=['Saugu', 'Itartina', 'Pavojinga'],
                    dtick=(1)
          )
          
       )
     
        
    )
    

    layout = Layout(
        height=450,
       xaxis=dict(
                constrain='range',
                constraintoward='right',
                fixedrange=True,
                rangemode='normal',
                autorange=True,
                #range=[int((ltime-readRange)*100),int((ltime-10)*100)],
                type='date'
            ),
         yaxis=dict(
                constrain='range',
                constraintoward='right',
                fixedrange=True,
                #range=list([0, 3]),
                autorange=True,
                nticks=6,
            )     
    )
    return Figure(data=[trace], layout=layout)




external_css = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "/static/style.css",
                "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
                "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i"
                ]


for css in external_css:
    app.css.append_css({"external_url": css})

if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')

