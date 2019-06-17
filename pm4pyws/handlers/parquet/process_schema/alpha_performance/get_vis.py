from pm4py.algo.discovery.dfg.adapters.pandas import df_statistics
from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.algo.filtering.pandas.auto_filter import auto_filter
from pm4py.objects.log.util import xes
from pm4py.visualization.common.utils import get_base64_from_gviz
from pm4py.visualization.petrinet import factory as pn_vis_factory
from pm4py.visualization.petrinet.util.vis_trans_shortest_paths import get_decorations_from_dfg_spaths_acticount
from pm4py.visualization.petrinet.util.vis_trans_shortest_paths import get_shortest_paths
from pm4py.objects.petri.exporter.pnml import export_petri_as_string
from pm4pyws.util import constants
from pm4py.algo.filtering.pandas.attributes import attributes_filter
from pm4py.algo.filtering.pandas.start_activities import start_activities_filter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4pyws.util import get_graph
from pm4py.util import constants as pm4_constants
from pm4py.algo.filtering.common.filtering_constants import CASE_CONCEPT_NAME
import base64


def apply(dataframe, parameters=None):
    """
    Gets the Petri net through Alpha Miner, decorated by performance metric

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
                                                                    max_no_activities=constants.MAX_NO_ACTIVITIES)
    dataframe = auto_filter.apply_auto_filter(dataframe, parameters=parameters)
    dfg = df_statistics.get_dfg_graph(dataframe, activity_key=activity_key, timestamp_key=timestamp_key, case_id_glue=case_id_glue, sort_caseid_required=False, sort_timestamp_along_case_id=False)
    activities_count = attributes_filter.get_attribute_values(dataframe, activity_key)
    activities = list(activities_count.keys())
    start_activities = list(start_activities_filter.get_start_activities(dataframe, parameters=parameters).keys())
    end_activities = list(end_activities_filter.get_end_activities(dataframe, parameters=parameters).keys())
    net, im, fm = alpha_miner.apply_dfg(dfg, parameters=parameters)
    spaths = get_shortest_paths(net)
    aggregated_statistics = get_decorations_from_dfg_spaths_acticount(net, dfg, spaths,
                                                                      activities_count,
                                                                      variant="performance")
    gviz = pn_vis_factory.apply(net, im, fm, parameters={"format": "svg"}, variant="performance",
                                aggregated_statistics=aggregated_statistics)

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))

    ret_graph = get_graph.get_graph_from_petri(net, im, fm)

    return get_base64_from_gviz(gviz), export_petri_as_string(net, im, fm), ".pnml", "parquet", activities, start_activities, end_activities, gviz_base64, ret_graph
