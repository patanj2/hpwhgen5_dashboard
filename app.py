# -*- coding: utf-8 -*-
# external library imports
import dash
import dash_table
import configparser
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# local imports
from view.plots import *
from view.layouts import *
from data.data_access import EcoNetHistory
from view.layouts.tabs import get_tabs_layout
from view.layouts.device_table import get_device_tab_layout

# TODO: Change to get these items from the configuration
config = configparser.ConfigParser()
config.read("./config.ini")

mac_addresses = ["80-91-33-8A-6D-92", "80-91-33-8A-6D-A6", "80-91-33-8A-75-31",
                 "80-91-33-8A-80-99", "80-91-33-8A-80-9F", "80-91-33-8A-80-A6"]

econet_data = EcoNetHistory()
mac_addresses = [entry['mac_address'] for entry in econet_data.config['field_test_user_info']]

powerbi_src = "https://app.powerbi.com/reportEmbed?reportId=544f9410-4673-4e7b-9e8c-548a7227175e&autoAuth=" \
              "true&ctid=c9f9d6eb-ac24-4f8d-ba12-8aca79668852&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly93YWJpLXVz" \
              "LXdlc3QyLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0LyJ9"

# ================ Main Dash Application ===================#

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = config.get('Basic', 'App_title')

latest_sw_version = econet_data.get_latest_sw_version(mac_addresses)
alarm_counts = econet_data.get_alarm_count_by_code()
df_locations = pd.DataFrame(econet_data.config['field_test_user_info']).set_index('mac_address')

overview_layout = generate_overview_layout(latest_sw_version, alarm_counts, df_locations)
device_tab_layout = get_device_tab_layout(mac_addresses)

tabs_layout = get_tabs_layout(overview_layout, device_tab_layout, powerbi_src)
banner_layout = get_banner_layout(app)

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

    plot_data = econet_data.get_device_accumulators(mac_address, accumulators)

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


# Update pie chart while user select data on location map
@app.callback(
    Output('alarm-chart', 'children'),
    [Input('location_map', 'selectedData')])
def update_chart(selectedData):
    mac_addresses_list = []
    if selectedData and selectedData['points']:
        for e in selectedData['points']:
            mac_addresses_list.append(e['text'].split('</br>')[1])
    alarm_counts = econet_data.get_alarm_count_by_code(filter=mac_addresses_list)
    return html.Div(
        [
            dcc.Graph(figure=generate_alarm_pie_chart(alarm_counts),
                      config={'displayLogo': False,
                              "displayModeBar": False}),
        ]
    )


# Update device table while user select data on location map
@app.callback(
    Output('device-table', 'children'),
    [Input('location_map', 'selectedData')])
def update_table(selectedData):
    ans = []
    if selectedData and selectedData['points']:
        for e in selectedData['points']:
            ans.append(e['text'].split('</br>'))
    df = pd.DataFrame(ans)
    df.columns = ["mac address", "Software Version"]
    return html.Div(
        [
            dash_table.DataTable(columns=[{"name": i, "id": i} for i in df.columns],
                                 data=df.to_dict('records'),
                                 style_table={
                                     'maxHeight': '300px',
                                     'overflowY': 'scroll',
                                     'border': 'thin lightgrey solid'
                                 },
                                 )
        ]
    )


if __name__ == '__main__':
    # TODO: Update to not use built in web server
    app.run_server(debug=False, host='0.0.0.0')
