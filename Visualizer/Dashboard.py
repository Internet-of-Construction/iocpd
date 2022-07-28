#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_daq as daq
import plotly.express as px
import datetime
import pandas
import plotly.graph_objects as go
from pm4py.objects.petri_net.importer import importer as pnml_importer
import graphviz
import plotly.figure_factory as pff
from dash.dependencies import Input, Output


#------------------------------------------------------------------------------
# Main Project Variables
#------------------------------------------------------------------------------
project_name = 'Betonieren'
project_path = 'testing/project/'
cost_plan_path = 'testing/project2/predicted_costs.csv'
actual_costs_path = 'testing/project2/actual_costs.csv'

curr_date = datetime.datetime(2022, 2, 10, 9, 0) #datetime.datetime.now()

# for cost diplay: use costs.sum(axis=1)


#------------------------------------------------------------------------------
# Initiate Dash App
#------------------------------------------------------------------------------
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(external_stylesheets=external_stylesheets, title='Projektübersicht')

for f in [f for f in os.listdir(app.config.assets_folder)]:
    os.remove(os.path.join(app.config.assets_folder, f))
    
#------------------------------------------------------------------------------
# Content
#------------------------------------------------------------------------------
app.layout = html.Div([
     dbc.Row([
         html.H1('Projektübersicht - ' + project_name, style={
             "paddingBottom": "10px"
             })
         ]),
     dbc.Row([
         dbc.Col([
             html.H2(f'Stand {curr_date.strftime("%Y-%m-%d %H:%M:%S")}', style={
                 'color': 'gray',
                 "paddingBottom": "20px"
                 })
             ],
             width=6
             ),
         dbc.Col([
             html.H3(['Projektübersicht'], style={'float': 'right'})
             ], width=2),
         dbc.Col([
             daq.ToggleSwitch(id='main-switch', value=True)
             ], width=1),
         dbc.Col([
             html.H3(['Wirtschaftlichkeitsanalyse'])
             ], width=3)
         ]),
        
        html.Div(['content loading...'], id='main-content')
    ],
    style={
        "padding": "50px",
        "fontFamily": "Arial",
        "fontSize": "0.9em"
        }
    )



# Main Callback: Show Project view or economic analysis
#------------------------------------------------------------------------------
@app.callback(Output('main-content', 'children'),
              Input('main-switch', 'value'))
def render_main_content(value):
    if not value: # Projektübersicht
        return [
            dbc.Row([
                dbc.Col([
                    dcc.Tabs(id="tabs-progress", value='tab-petri', children=[
                        dcc.Tab(label='Petri Net', value='tab-petri'),
                        dcc.Tab(label='Gantt Chart', value='tab-gantt'),
                        ]),
                    html.Div(id='tabs-progress-content', style={'border':'2px black solid', 'padding': '0px'}),
                    ],
                    width=8),
                 dbc.Col([
                     html.H2('Event Log'),
                     get_event_log()
                     ],
                     width=4,
                     style={
                         "paddingLeft": "10px",
                         "fontSize": "18px"})
                 ],
                 style={
                     "paddingBottom": "30px"
                     }),
             dbc.Row([
                 dbc.Col([
                     html.H2('Letzte Tätigkeiten', style={'paddingBottom': '20px'}),
                     get_last_activities()
                     ],style={"fontSize": "18px"}, width=3),
                 dbc.Col([
                     html.H2('Nächste Tätigkeiten', style={'paddingBottom': '20px'}),
                     get_next_activities()
                     ],style={"fontSize": "18px"}, width=5),
                 dbc.Col([
                     html.H2('Restliche Projektdauer', style={'paddingBottom': '20px'}),
                     get_remaining_duration()
                     ],style={"fontSize": "18px"}, width=4),
                 ])
            ]
    else: # Wirtschaftlichkeitsanalyse
        return [
            dbc.Row([
                dbc.Col([
                    html.H2(['Soll-Ist Vergleich der Projektkosten über die Zeit']),
                    get_cost_over_time()
                    ],
                    width=8),
                 dbc.Col([
                     html.H2('Projektkosten'),
                     '' #TODO: get_costs
                     ],
                     style={
                         "paddingLeft": "10px",
                         "fontSize": "18px"})
                 ],
                 style={
                     "paddingBottom": "30px"
                     }),
             dbc.Row([
                 dbc.Col([
                     html.H2('Kosten nach Partnern', style={'paddingBottom': '20px'}),
                     'Partnerkosten' #TODO: get_cost_by_partners
                     ],style={"fontSize": "18px"}, width=4),
                 dbc.Col([
                     html.H2('Kosten nach Kostenarten', style={'paddingBottom': '20px'}),
                     'Kostenartenkosten' #TODO: get_cost_by_kind
                     ],style={"fontSize": "18px"}, width=4),
                 dbc.Col([
                     html.H2('Restliche Projektkosten', style={'paddingBottom': '20px'}),
                     get_remaining_costs()
                     ],style={"fontSize": "18px"}, width=4),
                 ])
            ]


#------------------------------------------------------------------------------
# Page project view
#------------------------------------------------------------------------------

# Petri Net and Gantt Chart View
#------------------------------------------------------------------------------
@app.callback(Output('tabs-progress-content', 'children'),
              Input('tabs-progress', 'value'))
def render_progress(tab):
    if tab == 'tab-petri':
        return [html.Div('petri net is loading...', id='petri-net'),
                get_petri_filtering()]
    elif tab == 'tab-gantt':
        return get_gantt()


@app.callback(Output('petri-net', 'children'),
              Input('petri-filtering', 'value'))
def update_petri(petri_filter):
    generate_petri(petri_filter)
    
    fig = go.Figure()
    fig.add_layout_image(
            dict(
                source=app.get_asset_url('progress' + str(hash(str(petri_filter))) + '.gv.svg'),
                xref="x",
                yref="y",
                x=-5,
                y=0.5,
                sizex=10,
                sizey=4,
                sizing='contain',
                layer='below'
            )
    )
    fig.update_layout(xaxis={'range':[-4, 4], 'visible': False},
                      yaxis={'range':[-2, 2], 'visible': False},
                      margin={'pad': 0, 'l': 0, 't': 0, 'r': 0, 'b': 0},
                      dragmode='pan',
                      clickmode='none',
                      plot_bgcolor='#ffffff',
                      autosize=True)
    
    return dcc.Graph(figure=fig,
                     config = {'scrollZoom': True, 'displayModeBar': False})

def generate_petri(petri_filter):
    net, im, fm = pnml_importer.apply(project_path + 'temp/petri_net.pnml')
    
    if not os.path.exists(project_path + 'processes.csv'):
        print("WARNING: Couldn't find processes for coloring completed activities")
    
    if not os.path.exists(project_path + 'next_activities.csv'):
        print("WARNING: Couldn't find next activities for coloring")
    
    df = pandas.read_csv(project_path + 'processes.csv')
    next_activities = pandas.read_csv(project_path + 'next_activities.csv')
    completed = df[df['isfinished'] == True]
    res = get_ressources()
    
    nodes = {}
    arcs = []
    
    for node in net.transitions:
        nodes[node.name] = node.label
    
    for place in net.places:
        in_arcs = list(place.in_arcs)
        out_arcs = list(place.out_arcs)
        
        if len(in_arcs) == 1 and len(out_arcs) == 1:
            arcs.append([in_arcs[0].source.name, out_arcs[0].target.name])
        elif len(in_arcs) == 0 and len(out_arcs) == 1:
            arcs.append([place.name, out_arcs[0].target.name])
            nodes[place.name] = 'Start'
        elif len(in_arcs) == 1 and len(out_arcs) == 0:
            arcs.append([in_arcs[0].source.name, place.name])
            nodes[place.name] = 'End'
        else:
            print(f'WARNING: MORE THAN 1 ARCS IN PLACE {place.name}')
    
    
    dot = graphviz.Digraph('progress' + str(hash(str(petri_filter))), graph_attr={'rankdir':'LR'})
    
    for name in nodes.keys():
        if not nodes[name] == None:
            process = df[df['processname'] == nodes[name]]
            
            # determine colors
            if nodes[name] in list(completed['processname']):
                color = 'green'
            elif nodes[name] in list(next_activities['activity']):
                
                if process['isstarted'].iloc[0]:
                    color = 'limegreen'
                else:
                    if datetime.datetime.strptime(process['starttime'].iloc[0], '%d.%m.%Y %H:%M:%S') < curr_date:
                        color = 'red'
                    else:
                        color = 'orange'
            else:
                color = 'black'
            
            if not nodes[name] in ['Start', 'End']:
                if not petri_filter == res:
                    filter_true = False
                    for f in petri_filter:
                        print(f)
                        if f in process['resdescription'].iloc[0]:
                            print(f"[{f} is in {process['resdescription']}")
                            filter_true = True
                            
                    if filter_true:
                        fontcolor = 'navy'    
                    else:
                        fontcolor = 'gray40'
                else:
                    fontcolor = 'black'
            else:
                fontcolor = 'black'
                        
            dot.node(name, nodes[name], shape='box', color=color, fontcolor=fontcolor)
        else:
            dot.node(name, '', shape='circle')
    
    for arc in arcs:
        if not arc[0] in nodes.keys():
            dot.node(arc[0], '', shape='circle')
        if not arc[1] in nodes.keys():
            dot.node(arc[1], '', shape='circle')
        
        dot.edge(arc[0], arc[1])
    
    dot.format= 'svg'
    dot.render(directory=app.config.assets_folder)

def get_petri_filtering(petri_filter='all'):
    res = get_ressources()
    if petri_filter == 'all':
        selection = res
    else:
        selection = petri_filter
    
    return dcc.Checklist(res, selection, id='petri-filtering', inputStyle={'margin-left': '20px', 'margin-right': '5px'})

def get_gantt():
    df = pandas.read_csv(project_path + 'processes.csv', usecols=['processname', 'starttime', 'endtime', 'isfinished'])#.sort_values('endtime', ascending=True)
    df['starttime'] = pandas.to_datetime(df['starttime'], dayfirst=True)
    df['endtime'] = pandas.to_datetime(df['endtime'], dayfirst=True)
    df = df.rename({'starttime': 'Start', 'endtime': 'Finish', 'processname': 'Task'}, axis=1)
    fig = pff.create_gantt(df)
    fig.update_yaxes(autorange="reversed")
    return dcc.Graph(figure=fig,
                     config = {'scrollZoom': True, 'displayModeBar': False})

# Upper Right: Event Log
#------------------------------------------------------------------------------
def get_event_log(max_rows=8):
    if not os.path.exists(project_path + 'event_log.csv'):
        return html.P("couldn't load event log, file is not existing")

    df = pandas.read_csv(project_path + 'event_log.csv').sort_values('timestamp', ascending=False).rename({'process': 'Tätigkeit', 'key': 'Faktor', 'from': 'Von', 'to': 'zu', 'timestamp': 'Zeitstempel'}, axis=1)
    return generate_table(df, 8)


# Bottom Left: Completed Activities
#------------------------------------------------------------------------------
def get_last_activities():
    if not os.path.exists(project_path + 'processes.csv'):
        return html.P("couldn't load last activites, processes are not existing")
    
    df = pandas.read_csv(project_path + 'processes.csv', usecols=['processname', 'endtime', 'isfinished']).sort_values('endtime', ascending=False).rename({'processname': 'Tätigkeit', 'endtime': 'Erledigt am'}, axis=1)
    completed = df[df['isfinished'] == True]
    completed = completed.drop(['isfinished'], axis=1)
    return generate_table(completed, 5)

# Bottom Middle: Next Activities with relevance
#------------------------------------------------------------------------------
def get_next_activities(max_rows=5):
    if not os.path.exists(project_path + 'next_activities.csv'):
        return html.P("couldn't load next activities, file is not existing")
    
    df = pandas.read_csv(project_path + 'next_activities.csv').sort_values('until', ascending=False).rename({'activity': 'Tätigkeit', 'until': 'Erledigen bis', 'relevance': 'Dringlichkeit', 'starttime': 'Startdatum'}, axis=1)
    colors = []
    
    for index, row in df.iterrows():
        color = 'black'

        if row['started']:
            color = 'green'
        
        colors.append(color)
    
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col, style={'padding': '10px'}) for col in df.columns if col in ['Tätigkeit', 'Erledigen bis', 'Dringlichkeit', 'Startdatum']])
        ),
        html.Tbody([
            html.Tr([
                html.Td(df.iloc[i][col], style={'paddingLeft': '10px', 'paddingRight': '10px'}) for col in df.columns if col in ['Tätigkeit', 'Erledigen bis', 'Dringlichkeit','Startdatum']
            ], style={'color': colors[i]}) for i in range(min(len(df), max_rows))
        ])
    ])


# Bottom Right: Remaining Duration
#------------------------------------------------------------------------------
def get_remaining_duration():
    if not os.path.exists(project_path + 'temp/duration.csv'):
        return html.P("couldn't load remaining duration, file is not existing")
    
    try:
        with open(project_path + 'temp/duration.csv', 'r') as f:
            durs = [float(l) for l in f.readlines()]
    except:
        return html.P("couldn't load remaining duration, file is not accessible, retrying...")
    
    fig = px.histogram(durs)
    fig.update_layout({'xaxis': {'title': {'text': 'Restdauer (in h)'}},
                       'yaxis': {'title': {'text': 'Häufigkeit'}},
                       'showlegend': False})
    return dcc.Graph(figure=fig, config = {'displayModeBar': False})


#------------------------------------------------------------------------------
# Page economic analysis
#------------------------------------------------------------------------------

# Main Cost over Time
#------------------------------------------------------------------------------
def get_cost_over_time():
    if not os.path.exists(project_path + 'processes.csv'):
        return html.P("couldn't load processes, file is not existing")
    try:
        proc = pandas.read_csv(project_path + 'processes.csv')
    except:
        return html.P("couldn't load processes, file is not accessible, retrying...")
    
    if not os.path.exists(cost_plan_path):
        return html.P("couldn't load cost plan, file is not existing")
    try:
        planned_costs = pandas.read_csv(cost_plan_path)
    except:
        return html.P("couldn't load cost plan, file is not accessible, retrying...")
    
    if not os.path.exists(actual_costs_path):
        return html.P("couldn't load actaul costs, file is not existing")
    try:
        actual_costs = pandas.read_csv(actual_costs_path)
    except:
        return html.P("couldn't load actaul costs, file is not accessible, retrying...")
    
    
    df = pandas.merge(proc, planned_costs, on='processname').sort_values('endtime')
    df['total_planned_costs'] = df['personal'] + df['material'] + df['transport'] + df['vertrieb'] + df['equipment']
    df['accumulated_planned_costs'] = df['total_planned_costs'].cumsum()
    df = df.drop(['personal', 'material', 'transport', 'vertrieb', 'equipment', 'total_planned_costs'], axis=1)
    
    df = pandas.merge(df, actual_costs, on='processname')
    df['total_actual_costs'] = df['personal'] + df['material'] + df['transport'] + df['vertrieb'] + df['equipment']
    df['accumulated_actual_costs'] = df['total_actual_costs'].cumsum()
    df = df.drop(['personal', 'material', 'transport', 'vertrieb', 'equipment', 'total_actual_costs'], axis=1)
    
    graph_df = df[['endtime', 'accumulated_planned_costs', 'accumulated_actual_costs']]
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=graph_df['endtime'], y=graph_df['accumulated_planned_costs'], mode='lines'))
    fig.add_trace(go.Scatter(x=graph_df['endtime'], y=graph_df['accumulated_actual_costs'], mode='lines'))
    
    #fig.update_layout({'xaxis': {'title': {'text': 'Verbleibende Kosten (in EUR)'}},
    #                   'yaxis': {'title': {'text': 'Häufigkeit'}},
    #                   'showlegend': False})
    return dcc.Graph(figure=fig, config = {'displayModeBar': False})




def get_remaining_costs():
    if not os.path.exists(project_path + 'temp/costs.csv'):
        return html.P("couldn't load remaining duration, file is not existing")
    try:
        df = pandas.read_csv(project_path + 'temp/costs.csv')    
    except:
        return html.P("couldn't load remaining duration, file is not accessible, retrying...")
    
    total_costs = df.sum(axis=1).to_list()
    
    fig = px.histogram(total_costs)
    fig.update_layout({'xaxis': {'title': {'text': 'Verbleibende Kosten (in EUR)'}},
                       'yaxis': {'title': {'text': 'Häufigkeit'}},
                       'showlegend': False})
    return dcc.Graph(figure=fig, config = {'displayModeBar': False})



#------------------------------------------------------------------------------
# Helper Functions
#------------------------------------------------------------------------------
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col, style={'padding': '10px'}) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col], style={'paddingLeft': '10px', 'paddingRight': '10px'}) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


def get_ressources():
    df = pandas.read_csv(project_path + 'processes.csv')
    ressources = df['resdescription'].unique()
    res = []
    for r in ressources:
        r = r.replace('[', '').replace(']', '')
        while '|' in r:
            res.append(r[:r.index('|')].lstrip().rstrip().lstrip("'").rstrip("'"))
            r = r[r.index('|') + 1:]
        res.append(r.lstrip().rstrip().lstrip("'").rstrip("'"))
    return list(dict.fromkeys(res))






if __name__ == '__main__':
    app.run_server(debug=True)#, dev_tools_hot_reload=False)