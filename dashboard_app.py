import plotly.graph_objects as go 
import pandas as pd
import os
import dash
from dash import dcc,html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime

data = pd.read_csv('query-results.txt',sep = '\t', on_bad_lines = 'skip')

data.loc[data['state'] == 'Sport Utility 4D']
data.drop(12433,axis = 0,inplace= True)
data.reset_index(inplace=True)
data['location'] = data['location'].str.title()

data['make'] = data['make'].str.title()

data.loc[data['location'] == 'Kpr','location'] = 'Tri-Cities'

data = data[data['predicted_price'] > 0]
columns_to_drop = ['index','latitude','longitude','title_text']

data['time_posted'] = pd.to_datetime(data['time_posted'],unit = 's')
data['time_posted'] = data['time_posted'].apply(lambda x: x.strftime("%Y-%m-%d"))
unique_states = data.drop_duplicates(subset = ['state'])['state']
unique_cities = data.drop_duplicates(subset= ['location'])['location']
state_options = [{'label': f"{state}", 'value': f"{state}"} for state in unique_states.values]

state_options.insert(0, {'label': 'All States', 'value': 'All'})
cities_options =  data.drop_duplicates(subset=['location', 'state'])[['location', 'state']]

car_options = data.drop_duplicates(subset='make')
car_options.insert(0,{'label':'All Makes','value':'All'})

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.H1(children='PNW Car Search Dashboard'),
            dcc.Dropdown(id = 'state-dropdown',
                       options = state_options,
                       value = ['All'],
                       multi = True),
            dcc.Dropdown(id = 'city-dropdown',
                         options = [],
                         value = ['All'],
                         multi = True),
 
               dcc.Dropdown(
        id='sort-dropdown',
        options=[
            {'label': 'Price: Low to High', 'value': 'ascending'},
            {'label': 'Price: High to Low', 'value': 'descending'}
        ],
        value='ascending', 
    ),
                dcc.Dropdown(
                    id = 'time-dropdown',
                    options = [
                        {'label':'Newest','value':'descending'},
                        {'label':'Oldest', 'value': 'ascending'}
                    ],
                    value = 'descending'
                ),

                dcc.Dropdown(id = 'make-dropdown',
                    options = [{'label':make,'value':make}for make in car_options['make']],
                    value = ['All'],
                    multi = True),

                dcc.Slider(id = 'price-slider',
                    min = data['price'].min(),
                    max = data['price'].max(),
                    step = 500,
                    value = data['price'].max(),
                    marks = {i:f"{i}" for i in range(int(data['price'].min()),int(data['price'].max()),10000)},
                    tooltip={'placement':'bottom','always_visible': True}),
                

    dbc.Tabs([
        dbc.Tab(label='Car Listings Table', tab_id='tab-table'),
        dbc.Tab(label='Map of Car Listings', tab_id='tab-map'),
        dbc.Tab(label='Median Car Price', tab_id='tab-median')
    ], id='tabs', active_tab='tab-table'),


    html.Div(id='tab-content')
])


@app.callback(
    Output(component_id='city-dropdown', component_property='options'),
    Input(component_id='state-dropdown', component_property='value')
)
def update_city_dropdown(selected_states):
    if 'All' in selected_states:
        # If "All" is selected, show all locations
        filtered_locations = cities_options
    else:
        # Filter unique locations based on the selected states
        filtered_locations = cities_options[cities_options['state'].isin(selected_states)]
    
    city_options = [{'label': loc, 'value': loc} for loc in filtered_locations['location'].unique()]
    city_options.insert(0, {'label': 'All Locations', 'value': 'All'})
    
    return city_options

@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('state-dropdown', 'value'),
     Input('city-dropdown', 'value'),
     Input('price-slider', 'value'),
     Input('sort-dropdown', 'value'),
     Input('time-dropdown','value'),
     Input('make-dropdown','value')]
)

def update_tab_content(active_tab, selected_states, selected_cities, selected_price, sort_order,time_order,selected_makes):
    # Filter the data based on selected state, city, and price range
    
    if 'All' in selected_states:
        filtered_cars = data[data['price'] <= selected_price]
    else:
        filtered_cars = data[(data['state'].isin(selected_states)) & (data['price'] <= selected_price)]
    
    if 'All' not in selected_cities and selected_cities:
        filtered_cars = filtered_cars[filtered_cars['location'].isin(selected_cities)]

    if 'All' not in selected_makes and selected_makes:
        filtered_cars = filtered_cars[filtered_cars['make'].isin(selected_makes)]
    # Sort the data based on the selected sort order
    if sort_order == 'ascending':
        filtered_cars = filtered_cars.sort_values(by='price', ascending=True)
    else:
        filtered_cars = filtered_cars.sort_values(by='price', ascending=False)

    #sort data base on time_posted
    if time_order == 'descending':
        filtered_cars = filtered_cars.sort_values(by='time_posted', ascending=False)
    else:
        filtered_cars = filtered_cars.sort_values(by='time_posted', ascending=True)

    if active_tab == 'tab-table':
        # Create a table of car listings
        filtered_cars = filtered_cars.drop(columns_to_drop,axis =1)
        return dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in filtered_cars.columns],
            data=filtered_cars.to_dict('records'),
            style_table={'overflowX': 'auto'}
        )
    
    elif active_tab == 'tab-map':
        # Create a map of car listings using Plotly Scattermapbox
        map_fig = go.Figure(go.Scattermapbox(
            lat=filtered_cars['latitude'],
            lon=filtered_cars['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=9, opacity= .4,color = 'blue'),
            text=filtered_cars['make']
        ))
        map_fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=go.layout.mapbox.Center(
                    lat=filtered_cars['latitude'].mean(),
                    lon=filtered_cars['longitude'].mean()
                ),
                zoom=5
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return dcc.Graph(id = 'car-map',figure=map_fig)

    elif active_tab == 'tab-median':
        # Calculate and display median price
        median_price = filtered_cars['price'].median()
        median_fig = go.Figure(go.Indicator(
            mode="number",
            value=median_price,
            title={"text": f"Median Car Price in Selected Area"}
        ))
        return dcc.Graph(figure=median_fig)

    return None

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run_server(host='0.0.0.0', port=port, debug=False)
