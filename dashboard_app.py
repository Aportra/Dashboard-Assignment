import plotly.graph_objects as go 
import pandas as pd
import os
import dash
from dash import dcc,html, dash_table,no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import numpy as np


#Data cleaning and prep

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

unique_cars = data.drop_duplicates(subset='make')['make']

car_options = [{'label':f'{car}','value':f'{car}'} for car in unique_cars.values]

car_options.insert(0,{'label':'All Makes','value':'All'})



#Building with Dash
app = dash.Dash(__name__,external_stylesheets=[dbc.themes.FLATLY])
app.layout = html.Div([
     dcc.Store(id = 'filtered-cars-store'),
    html.H1(children='PNW Car Search Dashboard'),
            dcc.Dropdown(id = 'state-dropdown',
                       options = state_options,
                       value = ['All'],
                       multi = True),
            dcc.Dropdown(id = 'city-dropdown',
                         options = [],
                         value = [],
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
                    options = car_options,
                    value = ['All'],
                    multi = True),

                dcc.RangeSlider(id = 'price-slider',
                    min = 0,
                    max = data['price'].max(),
                    step = 500,
                    value = [data['price'].min(),data['price'].max()],
                    marks = {i:f"${i}" for i in range(int(0),int(data['price'].max()),5000)},
                    tooltip={'placement':'bottom','always_visible': True},
                    allowCross = False),
                
                dcc.RangeSlider(id = 'odometer-slider',
                    min = 0,
                    max = data['odometer'].max(),
                    step = 1000,
                    value = [data['odometer'].min(),data['odometer'].max()],
                    marks = {i:f"{i}" for i in range(int(0),int(data['odometer'].max()),50000)},
                    tooltip={'placement':'bottom','always_visible': True},
                    allowCross = False),
                
                dcc.RangeSlider(id = 'year-slider',
                    min = data['year'].min(),
                    max = data['year'].max(),
                    step = 1,
                    value = [data['year'].min(),data['year'].max()],
                    marks = {i:f"{i}" for i in range(int(0),int(data['year'].max()),5)},
                    tooltip={'placement':'bottom','always_visible': True},
                    allowCross = False),


    dbc.Tabs([
        dbc.Tab(label='Car Listings Table', tab_id='tab-table'),
        dbc.Tab(label='Map of Car Listings', tab_id='tab-map'),
        dbc.Tab(label='Price Analysis', tab_id='tab-analysis')
    ], id='tabs', active_tab='tab-table'),

    html.Div(id='tab-content'),
])


#Adding filtering for cities; needed to be separate because we are passing in the selected state before returning.

@app.callback(
    Output(component_id='city-dropdown', component_property='options'),
    Input(component_id='state-dropdown', component_property='value')
)
def update_city_dropdown(selected_states):
    if 'All' in selected_states:

        filtered_locations = cities_options
    else:

        filtered_locations = cities_options[cities_options['state'].isin(selected_states)]
    
    city_options = [{'label': loc, 'value': loc} for loc in filtered_locations['location'].unique()]
   
    
    return city_options


#Adding filtering for everything else

@app.callback(
    [Output('tab-content', 'children'), Output('filtered-cars-store', 'data')],
    [Input('tabs', 'active_tab'),
     Input('state-dropdown', 'value'),
     Input('city-dropdown', 'value'),
     Input('price-slider', 'value'),
     Input('sort-dropdown', 'value'),
     Input('time-dropdown', 'value'),
     Input('make-dropdown', 'value'),
     Input('odometer-slider', 'value'),
     Input('year-slider', 'value')]
)
def update_tab_content(active_tab, selected_states, selected_cities, selected_price, sort_order, time_order, selected_makes, odometer_order, year_order):

    min_price, max_price = selected_price
    min_year, max_year = year_order
    min_od, max_od = odometer_order

    filtered_cars = data[(data['price'] >= min_price) & (data['price'] <= max_price)]
    filtered_cars = filtered_cars[(filtered_cars['year'] >= min_year) & (filtered_cars['year'] <= max_year)]
    filtered_cars = filtered_cars[(filtered_cars['odometer'] >= min_od) & (filtered_cars['odometer'] <= max_od)]

    if 'All' not in selected_states:
        filtered_cars = filtered_cars[filtered_cars['state'].isin(selected_states)]
    
    if 'All' not in selected_cities and selected_cities:
        filtered_cars = filtered_cars[filtered_cars['location'].isin(selected_cities)]

    if 'All' not in selected_makes and selected_makes:
        filtered_cars = filtered_cars[filtered_cars['make'].isin(selected_makes)]
    

    filtered_cars = filtered_cars.sort_values(by='price', ascending=(sort_order == 'ascending'))

    filtered_cars = filtered_cars.sort_values(by='time_posted', ascending=(time_order == 'ascending'))
    
    filtered_cars_data = filtered_cars.drop(columns_to_drop, axis=1)

    if active_tab == 'tab-table':
        # Create a table of car listings
        return dash_table.DataTable(
            id='car-table',
            columns=[{"name": col, "id": col} for col in filtered_cars_data.columns],
            data=filtered_cars_data.to_dict('records'),
            style_table={'overflowX': 'scroll', 'width': '100%'},
            style_cell={'minWidth': '80px', 'maxWidth': '200px', 'width': 'auto'},
            style_data={'whiteSpace': 'normal', 'height': 'auto', 'padding': '5px'},
            fixed_columns={'headers': True},
          ), filtered_cars.to_dict('records')

    elif active_tab == 'tab-map':

        map_fig = go.Figure(go.Scattermapbox(
            lat=filtered_cars['latitude'],
            lon=filtered_cars['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=9, opacity=0.4, color='blue'),
            text=[f'City: {location} State: {state} Make: {make} Price: {price} Odometer: {odometer}' for location, state, make, price, odometer in zip(filtered_cars['location'], filtered_cars['state'], filtered_cars['make'], filtered_cars['price'], filtered_cars['odometer'])]
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
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            autosize=True,
            height=1000
        )
        return dcc.Graph(id='car-map', figure=map_fig), filtered_cars.to_dict('records')

    elif active_tab == 'tab-analysis':

        median_price_fig = go.Figure()
        for make in filtered_cars['make'].unique():
            make_data = filtered_cars[filtered_cars['make'] == make]
            median_price_over_time = make_data.groupby('time_posted')['price'].median().reset_index()
            median_price_fig.add_trace(go.Scatter(x=median_price_over_time['time_posted'],
                                                  y=median_price_over_time['price'],
                                                  mode='lines',
                                                  name=f'{make} Median Price'))


        filtered_cars['log_odometer'] = np.log1p(filtered_cars['odometer'])
        price_vs_odometer_fig = go.Figure(go.Scatter(
            x=filtered_cars['log_odometer'],
            y=filtered_cars['price'],
            mode='markers',
            marker=dict(size=6, color='green', opacity=0.5),
            text=[f"Make: {make}, Price: ${price}" for make, price in zip(filtered_cars['make'], filtered_cars['price'])],
        ))
        price_vs_odometer_fig.update_layout(title="Price vs Log(Odometer)",
                                            xaxis_title="Log(Odometer)",
                                            yaxis_title="Price")


        make_counts = filtered_cars['make'].value_counts().reset_index()
        make_counts.columns = ['make', 'count']
        make_count_fig = go.Figure(go.Bar(
            x=make_counts['make'],
            y=make_counts['count'],
            text=make_counts['count'],
            textposition='auto'
        ))
        make_count_fig.update_layout(title="Count of Listings by Make",
                                     xaxis_title="Make",
                                     yaxis_title="Number of Listings")

        return html.Div([
            html.H3(f"Selected State: {', '.join(selected_states)} | Selected City: {', '.join(selected_cities)}"),
            html.Div([dcc.Graph(figure=median_price_fig), dcc.Graph(figure=price_vs_odometer_fig), dcc.Graph(figure=make_count_fig)])
        ]), filtered_cars.to_dict('records')

    return None, filtered_cars.to_dict('records')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run_server(host='0.0.0.0', port=port, debug=False)