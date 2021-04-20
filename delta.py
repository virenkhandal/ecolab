### Imports and Initializations
from numpy import place
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import plotly.express as px
import plotly.graph_objects as go
import boto3
import dash
import json
from urllib.request import urlopen
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

from flask_caching import Cache

import warnings
warnings.filterwarnings('ignore')
app = dash.Dash(__name__)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
server = app.server
TIMEOUT = 60
def load_counties():
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
        return counties

@cache.memoize(timeout=TIMEOUT)
def load_data():
    client = boto3.client('s3')
    

    ### Data: Use old ipynb from ecl
    county_geo = pd.read_csv('tl_2017_us_county.csv')
    county_geo = county_geo[['GEOID']]
    county_geo_org = county_geo.sort_values(by='GEOID')
    county_geo_org['GEOID'] = county_geo_org['GEOID'].astype('str')

    county_geo_org = county_geo_org.drop([1248, 1460, 81])


    path = "s3://ecodatalab/data/"
    ten = pd.read_csv( path + 'counties5year2010clean.csv'); ten.insert(0, 'year', 2010)
    eleven = pd.read_csv(path + 'counties5year2011clean.csv'); eleven.insert(0, 'year', 2011)
    twelve = pd.read_csv(path + 'counties5year2012clean.csv'); twelve.insert(0, 'year', 2012)
    thirteen = pd.read_csv(path + 'counties5year2013clean.csv'); thirteen.insert(0, 'year', 2013)
    fourteen = pd.read_csv(path + 'counties5year2014clean.csv'); fourteen.insert(0, 'year', 2014)
    fifteen = pd.read_csv(path + 'counties5year2015clean.csv'); fifteen.insert(0, 'year', 2015)
    sixteen = pd.read_csv(path + 'counties5year2016clean.csv'); sixteen.insert(0, 'year', 2016)
    seventeen = pd.read_csv(path + 'counties5year2017clean.csv'); seventeen.insert(0, 'year', 2017)
    frames = [ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen, seventeen]
    # newdf = pd.read_csv(path + 'carbon_data_county.csv')



    newdf = pd.concat(frames)

    newdf = newdf.rename(columns={"year": "YEAR", "Geo_NAME":"County Name", "DEGREE":"DEGREE", "MEDINCOME":"MEDINCOME", "AVGINCOME":"AVGINCOME", "OWN":"OWN", "SIZE":"SIZE", "ROOMS":"ROOMS", "VEHICLES":"VEHICLES", "Geo_FIPS":"GEOID"})
    newdf['GEOID'] = newdf['GEOID'].astype(str)

    finaldf = county_geo_org.merge(newdf, on=['GEOID'])

    finaldf['GEOID'] = finaldf['GEOID'].replace("46102", "46113")

    finaldf['GEOID'] = finaldf['GEOID'].replace("2158", "2270")
    return finaldf

app.layout = html.Div([

    html.H1("EcoDataLab Maps", style={'text-align': 'center', 'margin-bottom': 10}),

    dcc.Slider(
        id='my_slider',
        min=2010,
        max=2017,
        step=1,
        value=2014,
        marks={
        2010: '2010',
        2011: '2011',
        2012: '2012',
        2013: '2013',
        2014: '2014',
        2015: '2015',
        2016: '2016',
        2017: '2017'
        },
        included=False
    ),

    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Degree', 'value': 'DEGREE'},
            # {'label': 'Average Income', 'value': 'AVGINCOME'},
            # {'label': 'Median Income', 'value': 'MEDINCOME'},
            {'label': 'Rooms per Household', 'value': 'ROOMS'},
            {'label': 'Home Ownership', 'value': 'OWN'},
            {'label': 'Vehicle Ownership', 'value': 'VEHICLES'}
        ],
        value='DEGREE',
        placeholder="Select a variable to display on the map"
    ),

    html.Div(id='output_container', children=[]),
    html.Div(id='output_container_two', children=[]),
    html.Br(),

    dcc.Graph(id='map', figure={}, style={'height': '100vh'})

])


### Callback
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='output_container_two', component_property='children'),
     Output(component_id='map', component_property='figure')],
    [Input(component_id='my_slider', component_property='value'),
     Input(component_id='dropdown', component_property='value')]
)

def map_value(my_slider, dropdown):
    container = "You are currently viewing the map for : {}".format(my_slider)
    container_two = "You are currently mapping : {}".format(dropdown)
    year = my_slider
    variable = dropdown
    finaldf = load_data()
    counties = load_counties()
    currdf = finaldf[finaldf['YEAR'] == year]
    placeholder = finaldf[finaldf['YEAR'] == 2010]
    currdf[variable] = currdf[variable].values / placeholder[variable].values
    # print(currdf[variable])
    currdf['GEOID'] = currdf['GEOID'].str.zfill(5)
    min_value = currdf[variable].min()
    max_value = currdf[variable].max()
    fig = px.choropleth(
        data_frame=currdf,
        geojson=counties,
        locations=currdf["GEOID"],
        scope="usa",
        color=variable,
        hover_data=['County Name', 'YEAR', variable],
        color_continuous_scale="RdYlGn",
        labels={str(variable): variable},
        range_color = [min_value, max_value]
    )
    fig.update_layout(geo=dict(bgcolor= 'rgba(189, 222, 240, 1)', lakecolor='#BDDEF0'))
    fig.update_traces(marker_line_width=0)
    fig.update_geos(
        visible=False, resolution=110, scope="usa"
    )   
    return container, container_two, fig


### Run
if __name__ == '__main__':
    app.run_server(debug=True)