import dash_table
import dash_core_components as dcc
import dash_html_components as html

from view.plots import generate_alarm_pie_chart, generate_test_locations_plot


def generate_overview_layout(latest_sw_version, alarm_counts, df_locations):
    aggregate_configuration = html.Div(
        [
            html.Div(
                [html.H4(id="devicesText"), html.P("No. of Devices")],
                id="totalDevices",
                className="mini_container",
            ),
            html.Div(
                [html.H4(id="alertsText"), html.P("No. Of Alerts")],
                id="totalAlerts",
                className="mini_container",
            ),
            html.Div(
                [html.H4(id="hoursText"), html.P("Total Hours")],
                id="totalHours",
                className="mini_container",
            ),
        ],
        id="aggregate-container",
        className="row container-display",
    )

    device_configuration = html.Div(
        children=[html.Div(children=[html.H5("Device Configuration")], className='row'),
                  html.Div(
                      # place holder for table updating in the future
                      id='device-table'
                  )
                  ],
        className='three columns')

    alarm_configuration = html.Div(
        children=[html.Div(children=[html.H5("Alarm Breakdown",
                                             style={'text-align': 'center',
                                                    'color': "#2C404C"})], className='row'),
                  dcc.Loading(
                      id='alarm-loading',
                      type="default",
                      children=[
                          html.Div(
                              children=[],
                              id='alarm-chart', className='row'
                          ),
                      ]
                  )
                  ],
        className='four columns')

    device_locations = html.Div(
        children=[
            dcc.Graph(
                figure=generate_test_locations_plot(df_locations),
                config={
                    'editable': True,
                    'modeBarButtonsToRemove':
                        [
                            'toImage',
                            'lasso2d',
                            'toggleHover',
                            'hoverClosestGeo',
                            'hoverClosestGl2d',
                            'hoverClosestPie',
                            'hoverClosest3d',
                            'hoverCompareCartesian',
                            'hoverClosestCartesian'
                        ]
                },
                id='location_map'
            )
        ],
        className='four columns')

    overview_layout = html.Div(children=
                               [aggregate_configuration,
                                device_configuration,
                                alarm_configuration,
                                device_locations],
                               id="info-container",
                               className="row"
                               )
    return overview_layout
