import dash_table
import dash_core_components as dcc
import dash_html_components as html

from view.plots import generate_alarm_pie_chart,generate_test_locations_plot,generate_device_map_plot


def generate_device_map_layout(device_location_data):


    layout = html.Div(
        children = [html.Div(children = [html.H5("Location Map",
                                                 style = {'text-align':'center',
                                                          'color':"#2C404C"})],className = 'row'),
                    dcc.Loading(
                             id = 'device-loading',
                             type = "default",
                             children = [
                                 dcc.Dropdown(id = "dropdown-device-location",
                                              options = [{"label":type,"value":type} for type in
                                                         set(device_location_data['product_code'])],
                                              # value = control_objects[0],
                                              clearable = False),
                                 html.Div(
                                     children = [
                                         # dcc.Graph(figure=generate_device_map_plot(device_location_data),
                                         #           config={'displayLogo': False,
                                         #                    "displayModeBar": False}),
                                     ],
                                     style = {"max-width":"100%",
                                              "height":"100%",
                                              # "margin":"auto"
                                              },
                                     id = 'device-chart', className = 'row'
                                 ),
                             ]
                         )
                     ],

        style = {"max-width":"100%",
                 "height": "100%",
                 #"margin":"auto"
                 },
        id = "device-info-container",
        className = "row"
    )




    return layout