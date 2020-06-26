# Dependencies
import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import plotly.figure_factory as ff
import plotly.graph_objs as go
import configparser
import cx_Oracle

###########################
# Helpers
###########################

def printf (format,*args):
  sys.stdout.write (format % args)

def printException (exception):
  error, = exception.args
  printf ("Error code = %s\n",error.code);
  printf ("Error message = %s\n",error.message);

###########################
# Database
###########################

class mydb(object):   
    # def __init__(self):
        # printf ('Oracle __init__\n')

    def connect(self, username, password, hostname, port, servicename):
        # printf ('%s,%s,%s,%s,%s\n',username, password, hostname, port, servicename)
        try:
            dsn_tns = cx_Oracle.makedsn(hostname,port,servicename)
            self.conn = cx_Oracle.connect(user=username, password=password, dsn=dsn_tns)

        except cx_Oracle.DatabaseError as e:
            raise
        
        self.cursor = self.conn.cursor()
        # Alter session is optional
        self.cursor.execute('''ALTER SESSION SET NLS_DATE_FORMAT = 'MM/DD/SYYYY HH24:MI:SS' ''')
        self.cursor.execute('''ALTER SESSION SET NLS_TIMESTAMP_TZ_FORMAT = 'MM/DD/SYYYY HH24:MI:SS.FF TZH:TZM' ''')
        self.cursor.execute('''ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'MM/DD/SYYYY HH24:MI:SS.FF' ''')
        self.cursor.execute('''ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,' ''')
        self.cursor.execute('''ALTER SESSION SET NLS_NCHAR_CONV_EXCP = FALSE ''')
        self.cursor.execute('''ALTER SESSION SET TIME_ZONE = '-04:00' ''')


    def fetch_data(self, thisql):

        result = pd.read_sql(
            sql=thisql,
            con=self.conn
        )
        return result

    def disconnect(self):

        try:
            self.cursor.disconnect()
            self.conn.close()
        except cx_Oracle.DatabaseError:
            pass

###########################
# Data Manipulation / Model
###########################

def get_divisions():
    '''Returns the list of divisions that are stored in the database'''

    # printf ('get_seasons division_query\n')
    division_query = (
        f'''
        SELECT DISTINCT division
        FROM results order by division
        '''
    )
    divisions = []
    for index, row in p1.fetch_data(division_query).iterrows():
        divisions.append (row['DIVISION'] )  
    return divisions

def get_seasons(division):
    '''Returns the seasons of the datbase store'''

    # printf ('get_seasons seasons_query for Division = %s\n',division)
    seasons_query = (
        f'''
        SELECT DISTINCT season
        FROM results
        WHERE division='{division}' order by season
        '''
    )
    seasons = []
    for index, row in p1.fetch_data(seasons_query).iterrows():
        seasons.append (row['SEASON'] )  
    return seasons


def get_teams(division, season):
    '''Returns all teams playing in the division in the season'''

    # printf ('get_teams teams_query for Division/Season = %s,%s\n',division,season)
    teams_query = (
        f'''
        SELECT DISTINCT team
        FROM results
        WHERE division='{division}'
        AND season='{season}' order by team
        '''
    )
    teams = []
    for index, row in p1.fetch_data(teams_query).iterrows():
        teams.append (row['TEAM'] )  
    return teams


def get_match_results(division, season, team):
    '''Returns match results for the selected prompts'''

    # printf ('get_match_results for Division/Season/Team = %s,%s,%s\n',division,season,team)
    results_query = (
        f'''
        SELECT dateg, team, opponent, goals, goals_opp, result, points
        FROM results
        WHERE division='{division}'
        AND season='{season}'
        AND team='{team}'
        ORDER BY dateg ASC
        '''
    )
    match_results = p1.fetch_data(results_query)
    return match_results


def calculate_season_summary(results):
    record = results.groupby(by=['RESULT'])['TEAM'].count()
    summary = pd.DataFrame(
        data={
            'W': record['W'],
            'L': record['L'],
            'D': record['D'],
            'Points': results['POINTS'].sum()
        },
        columns=['W', 'D', 'L', 'Points'],
        index=results['TEAM'].unique(),
    )
    return summary


def draw_season_points_graph(results):
    dates = results['DATEG']
    points = results['POINTS'].cumsum()

    figure = go.Figure(
        data=[
            go.Scatter(x=dates, y=points, mode='lines+markers')
        ],
        layout=go.Layout(
            title='Points Accumulation',
            showlegend=False
        )
    )

    return figure

#########################
# Dashboard Layout / View
#########################

def generate_table(dataframe, max_rows=10):
    '''Given dataframe, return template generated using Dash components
    '''
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def onLoad_division_options():
    '''Actions to perform upon initial page load'''

    list = (
        [{'label': division, 'value': division}
            for division in get_divisions() ]
    )
    return list

# Set up Dashboard and create layout
app = dash.Dash()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

# If you want to use external css file
#app.css.append_css({
#    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
#})

config = configparser.ConfigParser()
config.read('assets/config.ini')

p1 = mydb()
p1.connect(config['football']['user'],
           config['football']['pass'],
           config['football']['host'],
           config['football']['port'],
           config['football']['db']
           )

app.layout = html.Div([

    # Using local copy of css
    html.Link(
        rel='stylesheet',
        href='/assets/bWLwgP.css'
    ),

    # Page Header
    html.Div([
        html.H1('Soccer Results Viewer')
    ]),

    # Dropdown Grid
    html.Div([
        html.Div([
            # Select Division Dropdown
            html.Div([
                html.Div('Select Division', className='three columns'),
                html.Div(dcc.Dropdown(id='division-selector',
                                      options=onLoad_division_options()),
                         className='nine columns')
            ]),

            # Select Season Dropdown
            html.Div([
                html.Div('Select Season', className='three columns'),
                html.Div(dcc.Dropdown(id='season-selector'),
                         className='nine columns')
            ]),

            # Select Team Dropdown
            html.Div([
                html.Div('Select Team', className='three columns'),
                html.Div(dcc.Dropdown(id='team-selector'),
                         className='nine columns'),
                html.Button('Submit', id='submit-val', n_clicks=0),
                html.Div(id='container-button-basic')
        ])
        ], className='six columns'),

        # Empty
        html.Div(className='six columns'),
    ], className='twleve columns'),

    # Match Results Grid
    html.Div([

        # Match Results Table
        html.Div(
            html.Table(id='match-results'),
            className='six columns'
        ),

        # Season Summary Table and Graph
        html.Div([
            # summary table
            dcc.Graph(id='season-summary'),

            # graph
            dcc.Graph(id='season-graph')
            # style={},

        ], className='six columns')
    ]),

    # json dataframe-cache-storage
    html.Div(id='df-cache-storage', style={'display': 'none'}),

])

#############################################
# Interaction Between Components / Controller
#############################################

# Load Seasons in Dropdown
@app.callback(
    Output(component_id='season-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value')
    ]
)
def populate_season_selector(division):
    if division == None:
        raise PreventUpdate
    seasons = get_seasons(division)
    return [
        {'label': season, 'value': season}
        for season in seasons
    ]


# Load Teams into dropdown
@app.callback(
    Output(component_id='team-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value')
    ]
)
def populate_team_selector(division, season):
    if division == None or season == None:
        raise PreventUpdate
    teams = get_teams(division, season)
    return [
        {'label': team, 'value': team}
        for team in teams
    ]

# Load Cache
@app.callback(
    dash.dependencies.Output('df-cache-storage', 'children'),
    [
        dash.dependencies.Input('submit-val', 'n_clicks')
    ],
    [
        dash.dependencies.State(component_id='division-selector', component_property='value'),
        dash.dependencies.State(component_id='season-selector', component_property='value'),
        dash.dependencies.State(component_id='team-selector', component_property='value'),
    ]    
)
def load_cache(n_clicks, division, season, team):
    if n_clicks < 1:
        return dash.no_update
    if division == None or season == None or team == None:
        raise PreventUpdate   
    # printf ('load_cache = %s,%s,%s\n',division,season,team) 
    results = get_match_results(division, season, team)
    return results.to_json(date_format='iso', orient='split')

# Load Match results
@app.callback(
    Output(component_id='match-results', component_property='children'),
    [
            Input('df-cache-storage', 'children')
    ],
    [
        dash.dependencies.State(component_id='division-selector', component_property='value'),
        dash.dependencies.State(component_id='season-selector', component_property='value'),
        dash.dependencies.State(component_id='team-selector', component_property='value'),
    ] 
)
def load_match_results(results, division, season, team):
    # printf ('load_match_results\n')     
    if division == None or season == None or team == None:
        raise PreventUpdate 
    results = pd.read_json(results, orient='split')
    return generate_table(results, max_rows=50)


# Update Season Summary Table
@app.callback(
    Output(component_id='season-summary', component_property='figure'),
    [
            Input('df-cache-storage', 'children')
    ],
    [
        dash.dependencies.State(component_id='division-selector', component_property='value'),
        dash.dependencies.State(component_id='season-selector', component_property='value'),
        dash.dependencies.State(component_id='team-selector', component_property='value'),
    ] 
)
def load_season_summary(results, division, season, team):
    # printf ('load_season_summary\n')    
    if division == None or season == None or team == None:
        raise PreventUpdate 
    table = []
    if len(results) > 0:
        summary = calculate_season_summary(pd.read_json(results, orient='split'))
        table = ff.create_table(summary)

    return table


# Update Season Point Graph
@app.callback(
    Output(component_id='season-graph', component_property='figure'),
    [
            Input('df-cache-storage', 'children')
    ],
    [
        dash.dependencies.State(component_id='division-selector', component_property='value'),
        dash.dependencies.State(component_id='season-selector', component_property='value'),
        dash.dependencies.State(component_id='team-selector', component_property='value'),
    ] 
)
def load_season_points_graph(results, division, season, team):
    # printf ('load_season_points_graph\n')    
    if division == None or season == None or team == None:
        raise PreventUpdate 
    figure = []
    if len(results) > 0:
        figure = draw_season_points_graph(pd.read_json(results, orient='split'))

    return figure


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050,
        threaded=False
    )
