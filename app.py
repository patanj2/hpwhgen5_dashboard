# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

# external library imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# local imports
from view.controls import generate_control_dropdown, generate_mac_address_dropdown
from data.data_access import EcoNetHistory
from view.plots import (generate_time_series_chart, generate_device_accumulators, generate_boxplot,
                        make_time_series_subplots)
from view.layouts import get_banner_layout, generate_overview_layout


# TODO: Change to get these items from the configuration
mac_addresses = ["80-91-33-8A-6D-92", "80-91-33-8A-6D-A6", "80-91-33-8A-75-31",
                 "80-91-33-8A-80-99", "80-91-33-8A-80-9F", "80-91-33-8A-80-A6"]

econet_data = EcoNetHistory()
mac_addresses = [entry['mac_address'] for entry in econet_data.config['field_test_user_info']]
powerbi_src = "https://app.powerbi.com/reportEmbed?reportId=544f9410-4673-4e7b-9e8c-548a7227175e&autoAuth=true&ctid=c9f9d6eb-ac24-4f8d-ba12-8aca79668852&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly93YWJpLXVzLXdlc3QyLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0LyJ9"

# Main Dash Application
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Rheem HPWH Gen V Field Test"  # TODO: Convert to configuration

device_tab_layout = html.Div(className='row',
                             children=[
                                 html.Div(
                                     children=[html.Div(children=[
                                         html.P("Device"),
                                         generate_mac_address_dropdown('dropdown-device', mac_addresses)],
                                         className='two columns'),
                                         html.Div(children=[
                                             html.P("EcoNet Object", ),
                                             generate_control_dropdown(),
                                         ],
                                             className='two columns'),
                                         html.Div(children=[html.P("Date Range"),
                                                            dcc.DatePickerRange(
                                                                min_date_allowed=datetime.today() - timedelta(days=42),
                                                                max_date_allowed=datetime.today() + timedelta(days=1),
                                                                start_date=datetime.today() - timedelta(days=42),
                                                                end_date=datetime.today() + timedelta(days=1),
                                                                updatemode='bothdates',
                                                                id='datepicker-range')
                                                            ], className="five columns")
                                     ], className="row"
                                 ),
                                 html.Div(className='row',
                                          children=[html.Div(children=[
                                              html.Div(dcc.Loading(dcc.Graph(id="econet-controls-graph",
                                                                             config={"displaylogo": False,
                                                                                     "modeBarButtonsToRemove": [
                                                                                         'toImage', 'zoomIn2d',
                                                                                         'zoomOut2d']})),
                                                       className="four columns",
                                                       ),
                                              dcc.Graph(id='horizontal-boxplot',
                                                        className="one column",
                                                        config={"displaylogo": False,
                                                                "displayModeBar": False}
                                                        ),
                                              html.Div(dcc.Loading(dcc.Graph(id='counter-plot',
                                                                             config={"displaylogo": False,
                                                                                     "displayModeBar": False})),
                                                       className='two columns')
                                          ],
                                              className="row"),
                                              html.Div(children=[html.Div(dcc.Loading(dcc.Graph(id='multiplot',
                                                                                                config={
                                                                                                    "displaylogo": False,
                                                                                                    "modeBarButtonsToRemove": [
                                                                                                        'toImage',
                                                                                                        'zoomIn2d',
                                                                                                        'zoomOut2d']})),
                                                                          className='seven columns'),

                                                                 ], className="row")
                                          ])
                             ])

overview_layout = generate_overview_layout(econet_data, mac_addresses)
banner_layout = get_banner_layout(app)

tabs_layout = html.Div(dcc.Tabs(id="tabs-container", value='tabs-container',
                                children=[
                                    dcc.Tab(label='Overview', value='overview-tab',
                                            children=[overview_layout]),
                                    dcc.Tab(label='Device', value='device-tab', children=[device_tab_layout]),
                                    dcc.Tab(label='Reliability Testing', value='power-bi-tab',
                                            children=[html.Div(html.Iframe(src=powerbi_src, id="powerbi_iframe"))]
                                            )
                                ],
                                className="row"))

app.layout = html.Div(children=[html.Div(children=[banner_layout, tabs_layout])], id="mainContainer")

# Callbacks - These update the graphs based on User Input or Other Events
@app.callback(
    Output('multiplot', 'figure'),
    [Input('dropdown-device', 'value'),
     Input('datepicker-range', 'start_date'),
     Input('datepicker-range', 'end_date')]
)
def update_timeseries_charts(device_mac_address, start_date, end_date):
    # TODO pull this from the configuration data

    temperature_columns = ['LOHTRTMP', 'UPHTRTMP', 'AMBIENTT', 'EVAPTEMP', 'SUCTIONT', 'DISCTEMP']
    operations_columns = ['COMP_RLY', 'HEATCTRL', 'FAN_CTRL', 'SHUTOFFV', 'HOTWATER']
    config_columns = ['WHTRCNFG', 'WHTRENAB', 'WHTRMODE']

    df = econet_data.query(4736, device_mac_address, start_date, end_date)

    column_names = ['mac_address', 'timestamp'] + temperature_columns + operations_columns + config_columns
    df = df.loc[:, column_names]

    fig = make_time_series_subplots(df, temperature_columns, operations_columns, config_columns)

    return fig


@app.callback(
    Output('econet-controls-graph', 'figure'),
    [Input('dropdown-controls', 'value'),
     Input('dropdown-device', 'value'),
     Input('datepicker-range', 'start_date'),
     Input('datepicker-range', 'end_date')]
)
def update_time_series(object_select, device_select, start_date, end_date):
    """
    :param object_select Econet object to plot
    :param device_select Device (mac address to plot)
    """
    df = econet_data.query(4736, device_select, start_date, end_date)
    columns = ['timestamp', object_select]
    # TODO Handle
    return generate_time_series_chart(object_select, device_select, df.loc[:, columns])


@app.callback(
    Output('counter-plot', 'figure'),
    [Input('dropdown-device', 'value')]
)
def update_device_counters(mac_address):
    accumulators = ['HRSHIFAN', 'HRSLOFAN', 'HRSLOHTR', 'HRSUPHTR', 'HRS_COMP']

    plot_data= econet_data.get_device_accumulators(mac_address, accumulators)

    return generate_device_accumulators(plot_data, accumulators)


@app.callback(
    Output('horizontal-boxplot', 'figure'),
    [Input('dropdown-controls', 'value'),
     Input('dropdown-device', 'value'),
     Input('datepicker-range', 'start_date'),
     Input('datepicker-range', 'end_date')]
)
def update_boxplot(object_select, device_select, start_date, end_date):
    df = econet_data.query(4736, device_select, start_date, end_date)
    return generate_boxplot(df, object_select)


if __name__ == '__main__':
    # TODO: Update to not use built in web server
    app.run_server(debug=False, host='0.0.0.0')
