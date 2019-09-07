import matplotlib.pyplot as plt
from functools import reduce
import pandas as pd
import scipy.spatial
import scipy.cluster
import numpy as np
import json
from functools import reduce
from scipy.cluster.hierarchy import dendrogram, linkage, cophenet, to_tree
from scipy.spatial.distance import squareform
from trace_cluster import filter_subsets
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.log.log import EventLog
from pm4py.util import constants
from trace_cluster.evaluation import fake_log_eval
from trace_cluster.merge_log import merge_log
from pm4py.visualization.common.utils import get_base64_from_file
from pm4py.visualization.graphs import factory as graphs_factory
from pm4py.algo.filtering.log.attributes import attributes_filter
import base64


def get_dendrogram_svg(log, parameters=None):
    if parameters is None:
        parameters = {}

    percent = 1
    alpha = 0.5

    list_of_vals = []
    list = []
    list_of_vals_dict = attributes_filter.get_trace_attribute_values(log, 'concept:name')
    # print(list_of_vals_dict.keys())
    list_of_vals_keys = sorted(list_of_vals_dict.keys())
    for i in range(len(list_of_vals_keys)):
        list_of_vals.append(list_of_vals_keys[i])

    for i in range(len(list_of_vals)):
        logsample = merge_log.log2sublog(log, list_of_vals[i])
        list.append(logsample)


    y = fake_log_eval.eval_avg_leven(list, percent, alpha)
    Z = linkage(y, method='average')


    # Create dictionary for labeling nodes by their IDs

    id2name = dict(zip(range(len(list_of_vals)), list_of_vals))

    T = to_tree(Z, rd=False)
    d3Dendro = dict(children=[], name="Root1")
    merge_log.add_node(T, d3Dendro)

    merge_log.label_tree(d3Dendro["children"][0],id2name)
    d3Dendro = d3Dendro["children"][0]
    d3Dendro["name"] = 'root'
    ret = d3Dendro
    print(ret)

    gviz = 'C:\\Users\\yukun\\PycharmProjects\\pm4py-source\\trace_cluster\\evaluation\\cluster.svg'

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))


    return get_base64_from_file(gviz), gviz_base64, ret


if __name__ == "__main__":
    log = xes_importer.apply("C:\\Users\\yukun\\PycharmProjects\\pm4py-ws\\logs\\mergedlog_1EKQ.xes")
    get_dendrogram_svg(log)
