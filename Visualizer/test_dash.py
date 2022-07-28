#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import datetime
import pandas
import plotly.graph_objects as go
from pm4py.objects.petri_net.importer import importer as pnml_importer
import graphviz
import plotly.figure_factory as pff
from dash.dependencies import Input, Output
import numpy as py



#------------------------------------------------------------------------------
# Initiate Dash App
#------------------------------------------------------------------------------
external_stylesheets = [dbc.themes.BOOTSTRAP]#, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(external_stylesheets=external_stylesheets, title='Projektübersicht', suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Tabs(id="tabs", value='tab1', children=[
        dcc.Tab(label='Tab 1', value='tab1'),
        dcc.Tab(label='Tab 2', value='tab2'),
        ]),
    html.Div(id='tabs-content')
    ])


# Upper Left: Progress View in Petri-Net resp. Gantt Chart
#------------------------------------------------------------------------------
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_tabs(tab):
    if tab == 'tab1':
        return html.Div(children=[
            dcc.Input(id='in1', type='number'),
            html.P(children='This is tab 1', id='out1')
            ])
    elif tab == 'tab2':
        return html.Div(children=[
            html.Div("This is tab 2"),
            dcc.Input(id='in2', type='number'),
            html.P(children='This is tab 2', id='out2')
            ])



@app.callback(
    Output('out2', 'children'),
    Input('in2', 'value')
)
def show_sum(num):
    if num is None:
        return ''
    flag = py.random.randint(1, num)
    return '{} is {} + {}'.format(num, flag, num - flag)



@app.callback(
    Output('out1', 'children'),
    Input('in1', 'value')
)
def show_factors(num):
    if num is None:
        return ''
    factors = prime_factors(num)
    return '{} is {}'.format(num, ' * '.join(str(n) for n in factors))


def prime_factors(num):
    n, i, out = num, 2, []
    while i * i <= n:
        if n % i == 0:
            n = int(n / i)
            out.append(i)
        else:
            i += 1 if i == 2 else 2
    out.append(n)
    return out



if __name__ == '__main__':
    app.run_server(debug=True)#, dev_tools_hot_reload=False)