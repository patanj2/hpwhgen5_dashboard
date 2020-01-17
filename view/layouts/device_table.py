import dash_html_components as html
import dash_core_components as dcc
from datetime import datetime, timedelta

from view.controls import generate_control_dropdown, generate_mac_address_dropdown


def get_device_tab_layout(mac_addresses):
    device_tab_layout = html.Div(
        className='row',
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
                                           min_date_allowed=datetime.today() - timedelta(
                                               days=42),
                                           max_date_allowed=datetime.today() + timedelta(
                                               days=1),
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
    return device_tab_layout
