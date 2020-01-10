import dash_html_components as html


def make_dash_table(df):
    """ Return a dash definition of an HTML table for a Pandas dataframe
    :param df (pandas DataFrame that contains a mac address and software version column
    """
    table = []
    table_header = html.Tr(children=[html.Th("mac address"),
                                     html.Th("Software Version")])
    table.append(table_header)

    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table
