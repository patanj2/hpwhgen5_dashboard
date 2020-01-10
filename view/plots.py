import copy

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from data_preprocessing import  get_total_alarm_count

MAPBOX_TOKEN = "pk.eyJ1IjoicGF0YW5qMiIsImEiOiJjazU0cmh4OGwwbWx4M25wbjQ5eXJmdmJ6In0.zt0cq1Vw9a9j6uS6hZp1uw"

common_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=20, r=20, t=40, b=20),
    title=dict(
        font=dict(family="Open Sans, sans-serif", size=14, color="#515151"),
    ),
    font=dict(family="Open Sans, sans-serif", size=12, color="#515151"),
    xaxis={"tickmode": "auto", "showgrid": True, "gridwidth": 1, "gridcolor": "lightgray", "title": {"text": ""}},
    yaxis={"tickmode": "auto", "showgrid": True, "gridwidth": 1, "gridcolor": "lightgray", "title": {"text": ""}},
    hovermode="closest"
)


def generate_time_series_chart(object_name, device_mac_address, df):
    """
    Generates a time series line-chart with timestamp on the x-axis and
    single data series on the y axis

    :param object_name: EcoNet Object
    :param device_mac_address: mac address for the Wifi module of the device
    :param df: Pandas dataframe
    """

    title = f"{object_name} for device {device_mac_address}"

    data = [go.Scattergl(x=df.timestamp, y=df[object_name], mode="lines", line=dict(color="#71cde4"))]
    layout = copy.deepcopy(common_layout)

    layout['height'] = 200
    layout['margin'] = dict(l=40, r=20, t=40, b=20)
    layout['title']['text'] = title
    return {"data": data, "layout": layout}


def generate_device_accumulators(df, accumulators):
    """
    :param df Pandas dataframe for an individual device (i.e. already filtered for a specific device)
    :param accumulators list of column names in the dataframe that correspond to the device counters.
    """
    temp = df.melt(value_vars=accumulators,
                   var_name='counter_name',
                   value_name='hours').groupby('counter_name').max().reset_index()

    fig = go.Figure()
    y = temp['counter_name']
    x = temp['hours']
    fig.add_trace(go.Bar(x=x, y=y, orientation='h', marker_color="#60c2f8"))

    layout = copy.deepcopy(common_layout)
    layout['title']['text'] = "Device Accumulators"
    layout['height'] = 200
    layout['hovermode'] = False
    layout['yaxis']['showgrid'] = False

    fig.update_layout(layout)

    return fig


def generate_boxplot(df, column_name):
    """ Generates a horizontal box plot with mac_address on the y-axis
    """
    layout = copy.deepcopy(common_layout)
    title = f"Distribution of {column_name}"

    layout['title']['text'] = column_name
    layout['height'] = 200
    layout['hovermode'] = False

    fig = px.violin(df, y=column_name)
    fig.data[0].marker.color = "#60c2f8"
    fig.update_layout(layout)
    return fig


def generate_alarm_chart(device_mac_address, df, alarm_columns):
    """
    :param device_mac_address mac address of the selected device.
    :param df historical alarm data for the connected device
    :param alarm_columns (list) List of names of columns in dataframe that are the alarms.
    """
    title = f"Alarm counts for device {device_mac_address}"

    # Count the number of alarms per alarm value
    alarm_totals = get_total_alarm_count(df)

    y = alarm_totals.alarm_code
    x = alarm_totals.alarm_text

    data = [go.Bar(name="Alarm Totals", x=x, y=y, orientation='h')]
    layout = copy.deepcopy(common_layout)
    layout['height'] = 200
    layout['margin'] = {"l": 40, "r": 20, "t": 40, "b": 20}
    layout['title']['text'] = title
    return {"data": data, "layout": layout}


def multi_time_series_plot(df, column_names):
    """
    :param df (dataFrame) historical data
    :param column_names list of names of columns in the pandas dataframe
    Generates a generic time series plot with multiple parameters
    """
    traces = []

    for column in column_names:
        traces.append(
            go.Scattergl(x=df.timestamp,
                         y=df[column].values, mode='lines',
                         name=column, opacity=0.75)
        )
    return traces


def make_time_series_subplots(df, temperature_columns, operations_columns, config_columns):
    """
    Creates a group of multiple time series plots with a shared x axis.

    Reference https://plot.ly/python-api-reference/generated/plotly.graph_objects.Figure.html

    :param df (dataFrame) historical object data
    :param temperature_columns (list)
    :param operations_columns (list)
    :param config_columns (list)

    :returns plotly.graph_objects.Figure

    """
    layout = copy.deepcopy(common_layout)

    column_groups = [temperature_columns, operations_columns, config_columns]

    fig = make_subplots(rows=len(column_groups),
                        cols=1,
                        shared_xaxes=True,
                        row_heights=[200, 200, 200])

    for i, column_names in enumerate(column_groups, start=1):
        traces = multi_time_series_plot(df, column_names)
        for trace in traces:
            fig.add_trace(trace, row=i, col=1)

    fig.update_layout(layout)
    fig.update_yaxes(layout['yaxis'])
    fig.update_xaxes(layout['xaxis'])
    fig.update_layout(title_text='Control and Operational Data')

    return fig


def generate_alarm_pie_chart(df):
    """
    DataFrame must contain files alarm code and alarm counts.

    :param df (pandas DataFrame) summarized data frame containing counts by alarm code
    """

    layout = copy.deepcopy(common_layout)

    fig = go.Figure(data=[go.Pie(labels=df.alarm_code, values=df.alarm_count, hole=0.5)])
    fig.update_layout(layout)
    fig['layout']['legend'] = dict(font=dict(color="#2C404C", size=10), orientation="h", bgcolor="rgba(0,0,0,0)")
    return fig


def generate_test_locations_plot(df_locations):
    fig = go.Figure(go.Scattermapbox(
        lat=df_locations.lat,
        lon=df_locations.long,
        text=df_locations.user + "</br>" + df_locations.index,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=6,
            color="red"
        ),
    ))

    fig.update_layout(
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken=MAPBOX_TOKEN,
            bearing=0,
            style='streets',
            center=go.layout.mapbox.Center(
                # Rheem Water Heating Headquarters
                lat=34.065,
                lon=-84.317
            ),
            pitch=0,
            zoom=2.8
        )
    )

    return fig