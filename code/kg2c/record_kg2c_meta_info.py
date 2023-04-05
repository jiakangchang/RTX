#!/bin/env python3
"""
This script creates a 'meta knowledge graph' (per TRAPI) and records node neighbor counts by category (in the
kg2c.sqlite file generated by create_kg2c_files.py). It uses the 'lite' KG2c JSON file to derive this meta info.
Usage: python3 record_kg2c_meta_info.py [--test]
"""
import argparse
import csv
import json
import logging
import os
import pickle
import sqlite3
import sys
import time
from collections import defaultdict
from typing import Dict, Set

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ARAX/BiolinkHelper/")
from biolink_helper import BiolinkHelper


KG2C_DIR = f"{os.path.dirname(os.path.abspath(__file__))}"


def serialize_with_sets(obj: any) -> any:
    # Thank you https://stackoverflow.com/a/60544597
    if isinstance(obj, set):
        return list(obj)
    else:
        return obj

def get_meta_qualifier(qualified_predicate, qualified_object_direction, qualified_object_aspect):
    return [{"qualifier_type_id": "biolink:qualified_predicate", "applicable_values": qualified_predicate},
            {"qualifier_type_id": "biolink:object_direction_qualifier", "applicable_values": qualified_object_direction},
            {"qualifier_type_id":"biolink:object_aspect_qualifier", "applicable_values": qualified_object_aspect}
            ]
def add_edge_to_applicable_values(qualifier_dict, key, value): #Adds the qualifier value to the corresponding applicable values of the list
    if (value != ""):                                          #given the key nad the value is not alreadt present.
        if(key in qualifier_dict):
            if(value not in qualifier_dict[key]):
                qualifier_dict[key].append(value)
        else:
            qualifier_dict[key] = [value]
    else:
        if(key not in qualifier_dict):
            qualifier_dict[key] = []


def build_meta_kg(nodes_by_id: Dict[str, Dict[str, any]], edges_by_id: Dict[str, Dict[str, any]],
                  meta_kg_file_name: str, biolink_helper: BiolinkHelper, is_test: bool):
    logging.info(f"Building meta KG..")
    logging.info(" Gathering all meta triples..")
    meta_triples = set()
    qualified_predicate = {}
    qualified_object_direction = {}
    qualified_object_aspect = {}
    for edge in edges_by_id.values():
        subject_node_id = edge["subject"]
        object_node_id = edge["object"]
        if not is_test or (subject_node_id in nodes_by_id and object_node_id in nodes_by_id):
            subject_node = nodes_by_id[subject_node_id]
            object_node = nodes_by_id[object_node_id]
            subject_categories = biolink_helper.add_conflations(subject_node["all_categories"])
            object_categories = biolink_helper.add_conflations(object_node["all_categories"])
            predicate = edge["predicate"]

            for subject_category in subject_categories:
                for object_category in object_categories:
                    add_edge_to_applicable_values(qualified_predicate, f"{subject_category}-{object_category}", edge["qualified_predicate"]) #Adding the  qualified_predicate of the edge to the corresponding applicable values list for the object_category-subject_category pair
                    add_edge_to_applicable_values(qualified_object_direction, f"{subject_category}-{object_category}", edge["qualified_object_direction"]) #Adding the qualified_object_direction of the edge to the corresponding applicable values list for the object_category-subject_category pair
                    add_edge_to_applicable_values(qualified_object_aspect, f"{subject_category}-{object_category}", edge["qualified_object_aspect"]) #Adding the qualified_object_aspect of the edge to the corresponding applicable values list for the object_category-subject_category pair
                    meta_triples.add((subject_category, predicate, object_category))
    kg2_infores_curie = "infores:rtx-kg2"

    meta_edges = [{"subject": triple[0], 
                   "predicate": triple[1], 
                   "object": triple[2], 
                   "qualifiers": get_meta_qualifier(qualified_predicate[f"{triple[0]}-{triple[2]}"], qualified_object_direction[f"{triple[0]}-{triple[2]}"], qualified_object_aspect[f"{triple[0]}-{triple[2]}"]) }
                  for triple in meta_triples]
    logging.info(f" Created {len(meta_edges)} meta edges")

    logging.info(" Gathering all meta nodes..")
    with open(f"{KG2C_DIR}/equivalent_curies.pickle", "rb") as equiv_curies_file:
        equivalent_curies_dict = pickle.load(equiv_curies_file)
    meta_nodes = defaultdict(lambda: defaultdict(lambda: set()))
    for node_id, node in nodes_by_id.items():
        equivalent_curies = equivalent_curies_dict.get(node_id, [node_id])
        prefixes = {curie.split(":")[0] for curie in equivalent_curies}
        categories = biolink_helper.add_conflations(node["category"])
        for category in categories:
            meta_nodes[category]["id_prefixes"].update(prefixes)
    logging.info(f" Created {len(meta_nodes)} meta nodes")

    logging.info(" Saving meta KG to JSON file..")
    meta_kg = {"nodes": meta_nodes, "edges": meta_edges}
    with open(f"{KG2C_DIR}/{meta_kg_file_name}", "w+") as meta_kg_file:
        json.dump(meta_kg, meta_kg_file, default=serialize_with_sets, indent=2)


def add_neighbor_counts_to_sqlite(nodes_by_id: Dict[str, Dict[str, any]], edges_by_id: Dict[str, Dict[str, any]],
                                  sqlite_file_name: str, label_property_name: str, is_test: bool):
    logging.info("Counting up node neighbors by category..")
    # First gather neighbors of each node by label/category
    neighbors_by_label = defaultdict(lambda: defaultdict(lambda: set()))
    neighbors = defaultdict(set)
    for edge in edges_by_id.values():
        subject_node_id = edge["subject"]
        object_node_id = edge["object"]
        neighbors[subject_node_id].add(object_node_id)  # Used for overall neighbor counts later
        neighbors[object_node_id].add(subject_node_id)  # Used for overall neighbor counts later
        if not is_test or (subject_node_id in nodes_by_id and object_node_id in nodes_by_id):
            subject_node = nodes_by_id[subject_node_id]
            object_node = nodes_by_id[object_node_id]
            for label in object_node[label_property_name]:
                neighbors_by_label[subject_node_id][label].add(object_node_id)
            for label in subject_node[label_property_name]:
                neighbors_by_label[object_node_id][label].add(subject_node_id)

    # Then record only the counts of neighbors per label/category
    neighbor_counts = defaultdict(dict)
    for node_id, neighbors_dict in neighbors_by_label.items():
        for label, neighbor_ids in neighbors_dict.items():
            neighbor_counts[node_id][label] = len(neighbor_ids)

    # Then write these counts to the sqlite file
    logging.info(f" Saving neighbor counts (for {len(neighbor_counts)} nodes) to sqlite..")
    connection = sqlite3.connect(sqlite_file_name)
    connection.execute("DROP TABLE IF EXISTS neighbors")
    connection.execute("CREATE TABLE neighbors (id TEXT, neighbor_counts TEXT)")
    rows = [(node_id, json.dumps(neighbor_counts)) for node_id, neighbor_counts in neighbor_counts.items()]
    connection.executemany(f"INSERT INTO neighbors (id, neighbor_counts) VALUES (?, ?)", rows)
    connection.execute("CREATE UNIQUE INDEX node_neighbor_index ON neighbors (id)")
    connection.commit()
    cursor = connection.execute(f"SELECT COUNT(*) FROM neighbors")
    logging.info(f" Done adding neighbor counts to sqlite; neighbors table contains {cursor.fetchone()[0]} rows")
    cursor.close()
    connection.close()

    # Additionally record top node degrees (used for dev purposes)
    neighbors_tsv_name = "neighbor_counts.tsv"
    logging.info(f"Recording overall neighbor counts in {neighbors_tsv_name}..")
    with open(f"{KG2C_DIR}/{neighbors_tsv_name}", "w+") as neighbors_file:
        writer = csv.writer(neighbors_file, delimiter="\t")
        writer.writerow(["id", "num_neighbors", "name", label_property_name])
        for node_id, neighbor_ids in sorted(neighbors.items(), key=lambda item: len(item[1]), reverse=True)[:1000000]:
            node = nodes_by_id.get(node_id, dict())
            writer.writerow([node_id, len(neighbor_ids), node.get("name"), node.get(label_property_name)])


def add_category_counts_to_sqlite(nodes_by_id: Dict[str, Dict[str, any]], sqlite_file_name: str,
                                  label_property_name: str):
    logging.info("Counting up nodes by category..")
    # Organize node IDs by their categories/labels
    nodes_by_label = defaultdict(set)
    for node_id, node in nodes_by_id.items():
        for category in node[label_property_name]:
            nodes_by_label[category].add(node_id)

    # Then write these counts to the sqlite file
    logging.info(f" Saving category counts (for {len(nodes_by_label)} categories) to sqlite..")
    connection = sqlite3.connect(sqlite_file_name)
    connection.execute("DROP TABLE IF EXISTS category_counts")
    connection.execute("CREATE TABLE category_counts (category TEXT, count INTEGER)")
    rows = [(category, len(node_ids)) for category, node_ids in nodes_by_label.items()]
    connection.executemany(f"INSERT INTO category_counts (category, count) VALUES (?, ?)", rows)
    connection.execute("CREATE UNIQUE INDEX category_index ON category_counts (category)")
    connection.commit()
    cursor = connection.execute(f"SELECT COUNT(*) FROM category_counts")
    logging.info(f" Done adding category counts to sqlite; category_counts table contains "
                 f"{cursor.fetchone()[0]} rows")
    cursor.close()
    connection.close()


def generate_fda_approved_drugs_pickle(edges_by_id: Dict[str, Dict[str, any]], fda_approved_file_name: str):
    # Extract the IDs of FDA-approved drug nodes per DRUGBANK (they're attached to the "fda approved drug" node)
    fda_approved_drug_node = "MI:2099"
    fda_approved_drugs = set()
    for edge_id, edge in edges_by_id.items():
        node_ids = {edge["subject"], edge["object"]}
        if fda_approved_drug_node in node_ids:
            drug_node_id = next(node_id for node_id in node_ids.difference({fda_approved_drug_node}))
            fda_approved_drugs.add(drug_node_id)
    logging.info(f"Saving IDs of {len(fda_approved_drugs)} FDA-approved drugs to {fda_approved_file_name}")
    with open(fda_approved_file_name, "wb") as pickle_file:
        pickle.dump(fda_approved_drugs, pickle_file)


def record_meta_kg_info(is_test: bool):
    kg2c_lite_file_name = f"kg2c_lite{'_test' if is_test else ''}.json"
    meta_kg_file_name = f"kg2c_meta_kg{'_test' if is_test else ''}.json"
    sqlite_file_name = f"kg2c{'_test' if is_test else ''}.sqlite"
    fda_approved_file_name = f"fda_approved_drugs{'_test' if is_test else ''}.pickle"
    # Initiate a BiolinkHelper for the proper Biolink model version
    with open("kg2c_config.json") as config_file:
        config_info = json.load(config_file)
    bh = BiolinkHelper(config_info["biolink_version"])

    start = time.time()
    # Load the 'lite' KG2c file into node/edge dictionaries
    with open(f"{KG2C_DIR}/{kg2c_lite_file_name}", "r") as input_kg_file:
        logging.info(f"Loading {kg2c_lite_file_name} into memory..")
        kg2c_dict = json.load(input_kg_file)
        nodes_by_id = {node["id"]: node for node in kg2c_dict["nodes"]}
        edges_by_id = {edge["id"]: edge for edge in kg2c_dict["edges"]}
        del kg2c_dict
    # Add the 'expanded' node labels (including category ancestors) into the node dictionary
    expanded_labels_property_name = "expanded_labels"
    for node in nodes_by_id.values():
        node[expanded_labels_property_name] = bh.get_ancestors(node["all_categories"], include_mixins=True)

    build_meta_kg(nodes_by_id, edges_by_id, meta_kg_file_name, bh, is_test)
    add_neighbor_counts_to_sqlite(nodes_by_id, edges_by_id, sqlite_file_name, expanded_labels_property_name, is_test)
    add_category_counts_to_sqlite(nodes_by_id, sqlite_file_name, expanded_labels_property_name)
    generate_fda_approved_drugs_pickle(edges_by_id, fda_approved_file_name)
    
    logging.info(f"Recording meta KG info took {round((time.time() - start) / 60, 1)} minutes.")


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.FileHandler("metainfo.log"),
                                  logging.StreamHandler()])
    logging.info("Starting to record KG2c meta info..")
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--test", dest="test", action='store_true', default=False)
    args = arg_parser.parse_args()

    record_meta_kg_info(args.test)


if __name__ == "__main__":
    main()
