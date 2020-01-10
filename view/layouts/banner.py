import dash_html_components as html

# TODO Get the title of the project from the app configuration

def get_banner_layout(app):
    """
    Generates an html Div containing header information for a dashboard.
    :param app Instance of flask app used to get app resources
    """
    banner_layout = html.Div(className='row', id="banner",
                             children=[html.Div(
                                 html.Img(src=app.get_asset_url("252px-Rheem_logo.svg.png"), style={"width": "30%",
                                                                                                    "vertical-align": "middle"}),
                                 className='two columns'),
                                 html.Div(html.H3("Odin Project: Heat Pump Water Heater Gen V Field Test",
                                                  className='header', id="title", style={"letter-spacing": "-1.6px"}),
                                          className="ten columns")],
                             )
    return banner_layout
