from pm4py.algo.discovery.dfg.adapters.pandas import df_statistics
from pm4py.algo.filtering.common.filtering_constants import CASE_CONCEPT_NAME
from pm4py.algo.filtering.pandas.auto_filter import auto_filter
from pm4py.objects.heuristics_net.net import HeuristicsNet
from pm4py.objects.log.util import xes
from pm4py.visualization.common.utils import get_base64_from_file
from pm4py.visualization.heuristics_net import factory as heu_vis_factory
from pm4py.algo.filtering.pandas.attributes import attributes_filter
from pm4py.algo.filtering.pandas.start_activities import start_activities_filter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.util import constants as pm4_constants
from pm4py.algo.filtering.common.filtering_constants import CASE_CONCEPT_NAME
import base64

from pm4pyws.util import constants as ws_constants


def apply(dataframe, parameters=None):
    """
    Gets the frequency HNet

    Parameters
    ------------
    dataframe
        Dataframe
    parameters
        Parameters of the algorithm

    Returns
    ------------
    base64
        Base64 of an SVG representing the model
    model
        Text representation of the model
    format
        Format of the model
    """
    if parameters is None:
        parameters = {}

    activity_key = parameters[pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY
    timestamp_key = parameters[pm4_constants.PARAMETER_CONSTANT_TIMESTAMP_KEY] if pm4_constants.PARAMETER_CONSTANT_TIMESTAMP_KEY in parameters else xes.DEFAULT_TIMESTAMP_KEY
    case_id_glue = parameters[pm4_constants.PARAMETER_CONSTANT_CASEID_KEY] if pm4_constants.PARAMETER_CONSTANT_CASEID_KEY in parameters else CASE_CONCEPT_NAME

    dataframe = attributes_filter.filter_df_keeping_spno_activities(dataframe, activity_key=activity_key,
                                                                    max_no_activities=ws_constants.MAX_NO_ACTIVITIES)
    dataframe = auto_filter.apply_auto_filter(dataframe, parameters=parameters)

    activities_count = attributes_filter.get_attribute_values(dataframe, activity_key)
    start_activities_count = start_activities_filter.get_start_activities(dataframe, parameters=parameters)
    end_activities_count = end_activities_filter.get_end_activities(dataframe, parameters=parameters)
    activities = list(activities_count.keys())
    start_activities = list(start_activities_count.keys())
    end_activities = list(end_activities_count.keys())

    if timestamp_key in dataframe.columns:
        dfg_frequency = df_statistics.get_dfg_graph(dataframe, case_id_glue=case_id_glue,
                                                    activity_key=activity_key, timestamp_key=timestamp_key, sort_caseid_required=False, sort_timestamp_along_case_id=False)
        heu_net = HeuristicsNet(dfg_frequency, activities=activities, start_activities=start_activities, end_activities=end_activities, activities_occurrences=activities_count)
    else:
        dfg = df_statistics.get_dfg_graph(dataframe, case_id_glue=case_id_glue,
                                          activity_key=activity_key, sort_caseid_required=False, sort_timestamp_along_case_id=False)
        heu_net = HeuristicsNet(dfg, activities=activities, start_activities=start_activities, end_activities=end_activities, activities_occurrences=activities_count)
    heu_net.calculate()

    vis = heu_vis_factory.apply(heu_net, parameters={"format": "svg"})

    gviz_base64 = base64.b64encode("".encode('utf-8'))

    return get_base64_from_file(vis.name), None, "", "parquet", activities, start_activities, end_activities, gviz_base64, []
