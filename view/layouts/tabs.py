import dash_html_components as html
import dash_core_components as dcc


def get_tabs_layout(overview_layout, device_tab_layout, powerbi_src):
    """
    Generates an html Div containing tabs information for a dashboard.
    :param powerbi_src:
    :param overview_layout:
    :param device_tab_layout:
    :param app Instance of flask app used to get app resources
    """

    tabs_layout = html.Div(
        dcc.Tabs(id="tabs-container",
                 value='tabs-container',
                 children=[
                     dcc.Tab(label='Overview', value='overview-tab',
                             children=[overview_layout]),
                     dcc.Tab(label='Device', value='device-tab', children=[device_tab_layout]),
                     dcc.Tab(label='Reliability Testing', value='power-bi-tab',
                             children=[html.Div(html.Iframe(src=powerbi_src, id="powerbi_iframe"))]
                             )
                 ],
                 className="row"))

    return tabs_layout
