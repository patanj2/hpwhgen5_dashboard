import json
import os

import dash_core_components as dcc

# TODO: Move to read from assets
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, os.pardir, 'resources', 'appconfig.json')) as f:
    config = json.load(f)

control_objects = config['controlObjects']
# TODO: Change to read from configuration
numeric_objects = ['WHTRSETP', 'SUCTIONT', 'DISCTEMP', 'I_RMSVAL', 'SECCOUNT', 'HOTWATER', 'AMBIENTT',
                   'EVAPTEMP', 'EXACTUAL', 'LOHTRTMP', 'UPHTRTMP', 'POWRWATT', 'TOTALKWH', 'ANODEA2D',
                   'HRSLOHTR', 'ANODESTS']


def generate_control_dropdown():
    control = dcc.Dropdown(id="dropdown-controls",
                           options=[{"label": econet_object, "value": econet_object} for econet_object in
                                    control_objects + numeric_objects],
                           value=control_objects[0], clearable=False)
    return control


def generate_mac_address_dropdown(html_id, mac_addresses):
    """
    Creates a dropdown containing options for all of the mac addresses

    :param html_id: id for the html element
    :param mac_addresses (list)  All mac addresses that should show up as options

    :returns dash_core_components.Dropdown object
    """
    control = dcc.Dropdown(id=html_id,
                           options=[
                               {"label": mac_address, "value": mac_address}
                               for
                               mac_address in mac_addresses],
                           value=mac_addresses[0],
                           clearable=False
                           )
    return control

def generate_date_range_control():
    return dcc.DatePickerRange()

