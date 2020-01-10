import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

from view.plots import generate_alarm_pie_chart, generate_test_locations_plot
from utils import make_dash_table


def generate_overview_layout(econet_data, mac_addresses):
    latest_sw_version = econet_data.get_latest_sw_version(mac_addresses)
    alarm_counts = econet_data.get_alarm_count_by_code()

    df_locations = pd.DataFrame(econet_data.config['field_test_user_info']).set_index('mac_address')

    device_configuration = html.Div(children=[html.Div(children=[html.H5("Device Configuration")], className='row'),
                                              html.Div(children=[html.Div(
                                                  children=make_dash_table(latest_sw_version),
                                                  className="table-bordered", style={"font-size": "12px"}
                                              )], className='row')],
                                    className='three columns')

    alarm_configuration = html.Div(children=[html.Div(children=[html.H5("Alarm Breakdown",
                                                                        style={'text-align': 'center',
                                                                               'color':"#2C404C"})], className='row'),
                                             html.Div(children=[html.Div(
                                                 children=dcc.Graph(figure=generate_alarm_pie_chart(alarm_counts),
                                                                    config={'displayLogo': False,
                                                                            "displayModeBar": False}),
                                             )], className='row')],
                                   className='four columns')

    device_locations = html.Div(children=[dcc.Graph(figure=generate_test_locations_plot(df_locations), id='location_map')], className='four columns')

    overview_layout = \
        html.Div(children=
            [device_configuration, alarm_configuration, device_locations],
            id="info-container",
            className="row"
        )
    return overview_layout
