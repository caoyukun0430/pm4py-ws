from pm4py.objects.log.importer.xes import factory as xes_importer
from trace_cluster.merge_log import merge_log
from trace_cluster.evaluation import factory
from pm4py.visualization.common.utils import get_base64_from_file
from pm4py.visualization.graphs import factory as graphs_factory
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.algo.discovery.inductive import factory as inductive_miner
from pm4py.visualization.petrinet import factory as pn_vis_factory
import base64


# get the triple group of nodes
def bfs(tree):
    queue = []
    output = []
    queue.append(tree)
    while queue:
        # element in queue is waiting to become root and splited into child
        # root is the first ele of queue
        root = queue.pop(0)
        if len(root['children']) > 0:
            name = [root['name']]
            for child in root['children']:
                queue.append(child)
                name.append(child['name'])
            output.append(name)

    return output


def get_dendrogram_svg(log, variant='VARIANT_DMM_LEVEN', parameters=None):
    if parameters is None:
        parameters = {}

    selectedNode = parameters["selectedNode"] if "selectedNode" in parameters else 'root'

    ATTR_NAME = 'responsible'

    (ret, leafname) = factory.apply(log, variant=variant, parameters=parameters)
    print("variant", variant)

    trilist = bfs(ret)
    # replace root with actual element
    # trilist[0][0] = trilist[0][1] + '-' + trilist[0][2]

    rootlist = []
    for ele in trilist:
        rootlist.append(ele[0])

    print("selectednode", selectedNode)
    print('rootlist', rootlist)

    if selectedNode == 'root':

        # slice_num = 2
        # index_list = []
        # length = int(len(leafname) / slice_num)
        #
        # slice_val = []
        # # slice list_of_vals 2 groups here, then 0:4 and 4:8
        # for i in range(slice_num):
        #     slice_val.append(leafname[i * length:(i + 1) * length])
        # # print(slice_val)
        select_index = rootlist.index(selectedNode)
        root_triple = trilist[select_index]
        root_triple[0] = root_triple[1] + '-' + root_triple[2]
        slice_val = []
        for ele in root_triple:
            slice_val.append(ele.split('-'))
        # print("slice_val", slice_val)
        gviz_list = []
        for i in range(len(slice_val)):
            logsample = merge_log.logslice(log, slice_val[i],ATTR_NAME)
            net, initial_marking, final_marking = inductive_miner.apply(logsample)
            parameters = {"format": "svg"}
            gviz = pn_vis_factory.apply(net, initial_marking, final_marking, parameters={"format": "svg"})
            filenname = "pn" + str(i + 1) + ".svg"
            pn_vis_factory.save(gviz, filenname)
            gviz_list.append(filenname)
    elif selectedNode in rootlist:
        select_index = rootlist.index(selectedNode)
        # get the triple-- one parent and two children
        show_triple = trilist[select_index]

        gviz_list = []

        # modify data structure
        slice_val = []
        for ele in show_triple:
            slice_val.append(ele.split('-'))

        for i in range(len(slice_val)):
            logsample = merge_log.logslice(log, slice_val[i],ATTR_NAME)
            net, initial_marking, final_marking = inductive_miner.apply(logsample)
            parameters = {"format": "svg"}
            gviz = pn_vis_factory.apply(net, initial_marking, final_marking, parameters={"format": "svg"})
            filenname = "pn" + str(i + 1) + ".svg"
            pn_vis_factory.save(gviz, filenname)
            gviz_list.append(filenname)


    base64_list = []
    gviz_base64_list = []

    for gviz in gviz_list:
        base64_list.append(get_base64_from_file(gviz))
        gviz_base64_list.append(base64.b64encode(str(gviz).encode('utf-8')))

    # gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))
    #
    #
    # return get_base64_from_file(gviz), gviz_base64, ret
    return base64_list, gviz_base64_list, ret


if __name__ == "__main__":
    log = xes_importer.apply("C:\\Users\\yukun\\PycharmProjects\\pm4py-ws\\logs\\mergedlog_all_1MEF.xes")
    get_dendrogram_svg(log)
