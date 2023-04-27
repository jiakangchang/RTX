import csv
import itertools
import logging
import os
import pathlib
import subprocess
from typing import Set, List

import pandas as pd
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KG2C_DIR = f"{SCRIPT_DIR}/../"
SYNONYMIZER_BUILD_DIR = f"{KG2C_DIR}/synonymizer_build"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.StreamHandler()])


def strip_biolink_prefix(item: str) -> str:
    return item.replace("biolink:", "")


def get_kg2pre_node_ids():
    logging.info(f"Grabbing KG2pre node IDs from KG2pre match graph..")
    kg2pre_nodes_df = pd.read_table(f"{SYNONYMIZER_BUILD_DIR}/match_nodes_kg2pre.tsv")
    kg2pre_node_ids = kg2pre_nodes_df.id.values
    return set(kg2pre_node_ids)


def get_most_specific_category(categories: List[str]) -> str:
    # TODO
    return ""


def create_sri_match_graph(kg2pre_node_ids_set: Set[str]):
    kg2pre_node_ids = list(kg2pre_node_ids_set)
    logging.info(f"Starting to build SRI match graph based on {len(kg2pre_node_ids):,} KG2pre node IDs..")

    # Save the current version of SRI match graph, if it exists (as backup, in case the SRI NN API is down)
    sri_match_nodes_file_path = f"{SYNONYMIZER_BUILD_DIR}/match_nodes_sri.tsv"
    sri_match_edges_file_path = f"{SYNONYMIZER_BUILD_DIR}/match_edges_sri.tsv"
    if pathlib.Path(sri_match_nodes_file_path).exists():
        subprocess.check_call(["mv", sri_match_nodes_file_path, f"{sri_match_nodes_file_path}_PREVIOUS"])
    if pathlib.Path(sri_match_edges_file_path).exists():
        subprocess.check_call(["mv", sri_match_edges_file_path, f"{sri_match_edges_file_path}_PREVIOUS"])

    # Divide KG2pre node IDs into batches
    batch_size = 1000  # This is the suggested max batch size from Chris Bizon (in Translator slack..)
    logging.info(f"Dividing KG2pre node IDs into batches of {batch_size}")
    kg2pre_node_id_batches = [kg2pre_node_ids[batch_start:batch_start + batch_size]
                              for batch_start in range(0, len(kg2pre_node_ids), batch_size)]

    # Send each batch to the normalizer and transform results into 'match graph' format
    sri_nn_url = "https://nodenormalization-sri.renci.org/1.3/get_normalized_nodes"
    batch_num = 0
    num_failed_batches = 0
    num_kg2pre_nodes_recognized = 0
    sri_cluster_ids_seen = set()
    node_cols = ["id", "name", "category", "cluster_id"]
    edge_cols = ["id", "subject", "predicate", "object"]
    nodes_df = pd.DataFrame(columns=node_cols).set_index("id")
    edges_df = pd.DataFrame(columns=edge_cols).set_index("id")
    logging.info(f"Sending {len(kg2pre_node_id_batches)} batches to the SRI Node Normalizer RestAPI ({sri_nn_url})")
    for node_id_batch in kg2pre_node_id_batches:
        batch_num += 1
        query_body = {"curies": node_id_batch,
                      "conflate": True}
        response = requests.post(sri_nn_url, json=query_body)
        if response.status_code == 200:
            # Transform the returned SRI clusters into 'match graph' format
            batch_nodes = dict()
            batch_edges = list()
            for input_node_id, normalized_info in response.json().items():

                if normalized_info:  # We skip KG2pre nodes the SRI NN didn't recognize
                    num_kg2pre_nodes_recognized += 1

                    # First parse the cluster-level info
                    preferred_node = normalized_info["id"]
                    cluster_id = preferred_node["identifier"]

                    # Process this cluster if we haven't seen it before
                    if cluster_id not in sri_cluster_ids_seen:
                        sri_cluster_ids_seen.add(cluster_id)
                        cluster_category = get_most_specific_category(normalized_info["type"])

                        # Then create nodes and edges for each cluster member and add them to this batch's nodes
                        cluster_nodes = {}
                        for equivalent_node in normalized_info["equivalent_identifiers"]:
                            node_id = equivalent_node["identifier"]
                            node_name = equivalent_node.get("label")
                            cluster_nodes[node_id] = [node_id, node_name, cluster_category, cluster_id]
                        batch_nodes = dict(cluster_nodes, **batch_nodes)  # Effectively takes union of dictionaries

                        # Then create intra-cluster edges and add them to our edges dataframe
                        if len(cluster_nodes) > 1:
                            possible_node_id_combos = itertools.combinations(list(cluster_nodes), 2)
                            for subject_node_id, object_node_id in possible_node_id_combos:
                                edge_id = f"SRINN:{subject_node_id}--{object_node_id}"
                                batch_edges.append([edge_id, subject_node_id, "same_as", object_node_id])

            # Add this batch of nodes/edges to our overarching SRI nodes/edges dataframes
            batch_nodes_df = pd.DataFrame(batch_nodes.values(), columns=node_cols).set_index("id")
            nodes_df = pd.concat([nodes_df, batch_nodes_df])
            batch_edges_df = pd.DataFrame(batch_edges, columns=edge_cols).set_index("id")
            edges_df = pd.concat([edges_df, batch_edges_df])
        else:
            logging.warning(f"Batch {batch_num} returned non-200 status ({response.status_code}): {response.text}")
            num_failed_batches += 1

    logging.info(f"Final SRI NN match nodes df is: \n{nodes_df}")
    logging.info(f"Final SRI NN match edges df is: \n{edges_df}")

    # Report some final stats
    logging.info(f"SRI NN API recognized {num_kg2pre_nodes_recognized:,} of {len(kg2pre_node_ids):,} KG2pre node IDs"
                 f" ({round(num_kg2pre_nodes_recognized / len(kg2pre_node_ids), 2) * 100}%)")
    logging.info(f"Our SRI match graph includes {len(sri_cluster_ids_seen):,} SRI clusters")
    if num_failed_batches:
        logging.warning(f"{num_failed_batches} requests to SRI NN API failed. Each failed request included "
                        f"{batch_size} KG2pre node IDs.")


def main():
    logging.info(f"\n\n  ------------------- STARTING TO RUN SCRIPT {os.path.basename(__file__)} ------------------- \n")

    # Transform SRI NN data into 'match graph' format, only including KG2-related nodes
    kg2pre_node_ids = get_kg2pre_node_ids()
    create_sri_match_graph(kg2pre_node_ids)


if __name__ == "__main__":
    main()
