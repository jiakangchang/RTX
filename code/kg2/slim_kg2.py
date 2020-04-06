#!/usr/bin/env python3
''' slim_kg2.py: reduce graph in KG2 JSON format to only bare-bones node and edge properties.
    Usage: slim_kg2.py <inputFile>
                         --outputFile <outputFile
'''
__author__ = 'Lindsey Kvarfordt'
__copyright__ = 'Oregon State University'
__credits__ = ['Lindsey Kvarfordt']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = ''
__email__ = ''
__status__ = 'Prototype'

import json
import argparse
import kg2_util


def make_arg_parser():
    arg_parser = argparse.ArgumentParser(description=" slim_kg2.py: reduce graph in KG2 JSON format to only bare-bones node and edge properties.")
    arg_parser.add_argument("inputFilepath", type=str)
    arg_parser.add_argument("--outputFile", type=str, default="./slim_kg2.json")
    return arg_parser


if __name__ == "__main__":
    node_set = set(["name", "id", "full name", "category label"])
    edge_set = set(["simplified relation curie", "subject", "object", "simplified edge label", "provided by"])

    args = make_arg_parser().parse_args()
    pretty = False
    if "test" in args.inputFilepath:
        pretty = True
    reduced = {"nodes": [], "edges": []}
    with open(args.inputFilepath, "r") as fp:
        all_data = json.load(fp)
        for node in all_data["nodes"]:
            temp_node = {}
            for key, val in node.items():
                if key in node_set:
                    temp_node[key] = val
            reduced["nodes"].append(temp_node)

        for edge in all_data["edges"]:
            temp_edge = {}
            for key, val in edge.items():
                if key in edge_set:
                    temp_edge[key] = val
            reduced["edges"].append(temp_edge)

    kg2_util.save_json(reduced, args.outputFile, pretty)
