import dash_table
import dash_core_components as dcc
import dash_html_components as html

from view.plots import generate_alarm_pie_chart, generate_test_locations_plot


def generate_overview_layout(latest_sw_version, alarm_counts, df_locations):
    device_configuration = html.Div(
        children=[html.Div(children=[html.H5("Device Configuration")], className='row'),
                  html.Div(
                      children=
                      [
                          dash_table.DataTable(
                              columns=[{"name": i, "id": i} for i in latest_sw_version.columns],
                              data=latest_sw_version.to_dict('records'),
                              style_table={
                                  'maxHeight': '300px',
                                  'overflowY': 'scroll',
                                  'border': 'thin lightgrey solid'
                              },
                          )
                      ],
                      id='device-table'
                  )
                  ],
        className='three columns')

    alarm_configuration = html.Div(
        children=[html.Div(children=[html.H5("Alarm Breakdown",
                                             style={'text-align': 'center',
                                                    'color': "#2C404C"})], className='row'),
                  html.Div(
                      children=[
                          dcc.Graph(figure=generate_alarm_pie_chart(alarm_counts),
                                    config={'displayLogo': False,
                                            "displayModeBar": False}),
                      ], id='alarm-chart', className='row')],
        className='four columns')

    device_locations = html.Div(
        children=[dcc.Graph(figure=generate_test_locations_plot(df_locations), id='location_map')],
        className='four columns')

    overview_layout = html.Div (children=
         [device_configuration, alarm_configuration, device_locations],
         id="info-container",
         className="row"
         )
    return overview_layout
