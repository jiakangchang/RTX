#!/bin/env python3
"""
This script provides a way to estimate the percentage of nodes in KG2/KG1 that are "covered" by our ultrafast NGD
system (meaning, they can be mapped to a list of PMIDs).
Usage: python estimate_coverage.py
Note: The pickle DB "curie_to_pmids.db" must exist in the directory this script is run from.
"""
import os
import sys
import traceback

from typing import Set

from neo4j import GraphDatabase
import pickledb

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../NodeSynonymizer/")
from node_synonymizer import NodeSynonymizer
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../../")  # code directory
from RTXConfiguration import RTXConfiguration


def _get_random_node_ids(batch_size: int, kg='KG2') -> Set[str]:
    print(f"    Getting random selection of node IDs from {kg} neo4j")
    cypher_query = f"match (a) return a.id, rand() as r order by r limit {batch_size}"
    rtxc = RTXConfiguration()
    if kg == 'KG2':
        rtxc.live = "KG2"
    try:
        driver = GraphDatabase.driver(rtxc.neo4j_bolt, auth=(rtxc.neo4j_username, rtxc.neo4j_password))
        with driver.session() as session:
            query_results = session.run(cypher_query).data()
        driver.close()
    except Exception:
        tb = traceback.format_exc()
        error_type, error, _ = sys.exc_info()
        print(f"Encountered an error interacting with {kg} neo4j. {tb}")
        return set()
    else:
        return {result['a.id'] for result in query_results}


def estimate_percent_nodes_with_mesh_mapping_via_synonymizer(kg: str):
    print(f"Estimating the percent of {kg} nodes mappable to a MESH curie via NodeSynonymizer")
    percentages_with_mesh = []
    num_batches = 20
    batch_size = 4000
    for number in range(num_batches):
        print(f"  Batch {number + 1}")
        # Get random selection of node IDs from the KG
        random_node_ids = _get_random_node_ids(batch_size, kg)

        # Use synonymizer to get their equivalent curies and check for a MESH term
        print(f"    Getting equivalent curies for those random node IDs..")
        synonymizer = NodeSynonymizer()
        curie_synonym_info = synonymizer.get_equivalent_curies(list(random_node_ids), kg_name='KG2')
        num_curies_with_mesh_term = 0
        for input_curie, synonym_curies in curie_synonym_info.items():
            if synonym_curies:
                if any(curie for curie in synonym_curies if curie.startswith('MESH')):
                    num_curies_with_mesh_term += 1
        percentage_with_mesh = (num_curies_with_mesh_term / len(random_node_ids)) * 100
        print(f"    {percentage_with_mesh}% of nodes had a synonym MESH term in this batch.")
        percentages_with_mesh.append(percentage_with_mesh)
    print(f"  Percentages for all batches: {percentages_with_mesh}.")
    average = sum(percentages_with_mesh) / len(percentages_with_mesh)
    print(f"Final estimate of {kg} nodes mappable to a MESH term via NodeSynonymizer: {round(average)}%")


def estimate_percent_nodes_covered_by_ultrafast_ngd(kg: str):
    print(f"Estimating the percent of {kg} nodes covered by the ultrafast NGD system")
    pickle_db = pickledb.load("curie_to_pmids.db", False)
    percentages_mapped = []
    num_batches = 20
    batch_size = 4000
    for number in range(num_batches):
        print(f"  Batch {number + 1}")
        # Get random selection of node IDs from the KG
        random_node_ids = _get_random_node_ids(batch_size, kg)

        # Use synonymizer to get their canonical curies
        print(f"    Getting canonical curies for those random node IDs..")
        synonymizer = NodeSynonymizer()
        canonical_curie_info = synonymizer.get_canonical_curies(list(random_node_ids))
        recognized_curies = {input_curie for input_curie in canonical_curie_info if canonical_curie_info.get(input_curie)}

        # See if those canonical curies are in our pickledb
        num_mapped_to_pmids = 0
        for input_curie in recognized_curies:
            canonical_curie = canonical_curie_info[input_curie].get('preferred_curie')
            if canonical_curie and pickle_db.get(canonical_curie):
                num_mapped_to_pmids += 1
        percentage_mapped = (num_mapped_to_pmids / len(random_node_ids)) * 100
        print(f"    {percentage_mapped}% of nodes were covered by ultrafastNGD in this batch.")
        percentages_mapped.append(percentage_mapped)

    print(f"  Percentages for all batches: {percentages_mapped}.")
    average = sum(percentages_mapped) / len(percentages_mapped)
    print(f"Final estimate of ultrafastNGD's coverage of {kg} nodes: {round(average)}%")


if __name__ == "__main__":
    estimate_percent_nodes_covered_by_ultrafast_ngd('KG2')
