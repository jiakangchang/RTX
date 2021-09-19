#!/bin/env python3
import copy
import json
import sys
import os
import time

import aiohttp
import requests
from typing import List, Dict, Set, Union

import requests_cache

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import Expand.expand_utilities as eu
from Expand.expand_utilities import QGOrganizedKnowledgeGraph
from Expand.kp_selector import KPSelector
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../")  # ARAXQuery directory
from ARAX_response import ARAXResponse
from ARAX_messenger import ARAXMessenger
from ARAX_query import ARAXQuery
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from openapi_server.models.edge import Edge
from openapi_server.models.q_node import QNode
from openapi_server.models.q_edge import QEdge
from openapi_server.models.query_graph import QueryGraph
from openapi_server.models.result import Result


class TRAPIQuerier:

    def __init__(self, response_object: ARAXResponse, kp_name: str, user_specified_kp: bool, kp_selector: KPSelector,
                 force_local: bool = False):
        self.log = response_object
        self.kp_name = kp_name
        self.user_specified_kp = user_specified_kp
        self.force_local = force_local
        self.kp_endpoint = f"{eu.get_kp_endpoint_url(kp_name)}"
        self.kp_selector = kp_selector

    async def answer_one_hop_query_async(self, query_graph: QueryGraph) -> QGOrganizedKnowledgeGraph:
        """
        This function answers a one-hop (single-edge) query using the specified KP.
        :param query_graph: A TRAPI query graph.
        :return: An (almost) TRAPI knowledge graph containing all of the nodes and edges returned as
                results for the query. (Organized by QG IDs.)
        """
        log = self.log
        final_kg = QGOrganizedKnowledgeGraph()
        qg_copy = copy.deepcopy(query_graph)  # Create a copy so we don't modify the original

        self._verify_is_one_hop_query_graph(qg_copy)
        if log.status != 'OK':
            return final_kg

        # Verify that the KP accepts these predicates/categories/prefixes
        if self.kp_name != "RTX-KG2":
            if self.user_specified_kp:  # This is already done if expand chose the KP itself
                if not self.kp_selector.kp_accepts_single_hop_qg(qg_copy, self.kp_name):
                    log.error(f"{self.kp_name} cannot answer queries with the specified categories/predicates",
                              error_code="UnsupportedQG")
                    return final_kg

        # Convert the QG so that it uses curies with prefixes the KP likes
        qg_copy = eu.make_qg_use_supported_prefixes(self.kp_selector, qg_copy, self.kp_name, log)
        if not qg_copy:  # Means no equivalent curies with supported prefixes were found
            return final_kg

        # Answer the query using the KP and load its answers into our object model
        final_kg = await self._answer_query_using_kp_async(qg_copy)

        return final_kg

    def answer_one_hop_query(self, query_graph: QueryGraph) -> QGOrganizedKnowledgeGraph:
        """
        This function answers a one-hop (single-edge) query using the specified KP.
        :param query_graph: A TRAPI query graph.
        :return: An (almost) TRAPI knowledge graph containing all of the nodes and edges returned as
                results for the query. (Organized by QG IDs.)
        """
        # TODO: Delete this method once we're ready to let go of the multiprocessing (vs. asyncio) option
        log = self.log
        final_kg = QGOrganizedKnowledgeGraph()
        qg_copy = copy.deepcopy(query_graph)  # Create a copy so we don't modify the original

        self._verify_is_one_hop_query_graph(qg_copy)
        if log.status != 'OK':
            return final_kg

        # Verify that the KP accepts these predicates/categories/prefixes
        if self.kp_name != "RTX-KG2":
            if self.user_specified_kp:  # This is already done if expand chose the KP itself
                if not self.kp_selector.kp_accepts_single_hop_qg(qg_copy, self.kp_name):
                    log.error(f"{self.kp_name} cannot answer queries with the specified categories/predicates",
                              error_code="UnsupportedQG")
                    return final_kg

        # Convert the QG so that it uses curies with prefixes the KP likes
        qg_copy = eu.make_qg_use_supported_prefixes(self.kp_selector, qg_copy, self.kp_name, log)
        if not qg_copy:  # Means no equivalent curies with supported prefixes were found
            return final_kg

        # Answer the query using the KP and load its answers into our object model
        final_kg = self._answer_query_using_kp(qg_copy)
        return final_kg

    def answer_single_node_query(self, single_node_qg: QueryGraph) -> QGOrganizedKnowledgeGraph:
        """
        This function answers a single-node (edge-less) query using the specified KP.
        :param single_node_qg: A TRAPI query graph containing a single node (no edges).
        :return: An (almost) TRAPI knowledge graph containing all of the nodes and edges returned as
           results for the query. (Organized by QG IDs.)
        """
        log = self.log
        final_kg = QGOrganizedKnowledgeGraph()
        qg_copy = copy.deepcopy(single_node_qg)

        # Verify this query graph is valid, preprocess it for the KP's needs, and make sure it's answerable by the KP
        self._verify_is_single_node_query_graph(qg_copy)
        if log.status != 'OK':
            return final_kg

        # Answer the query using the KP and load its answers into our object model
        final_kg = self._answer_query_using_kp(qg_copy)
        return final_kg

    def _verify_is_one_hop_query_graph(self, query_graph: QueryGraph):
        if len(query_graph.edges) != 1:
            self.log.error(f"answer_one_hop_query() was passed a query graph that is not one-hop: "
                           f"{query_graph.to_dict()}", error_code="InvalidQuery")
        elif len(query_graph.nodes) > 2:
            self.log.error(f"answer_one_hop_query() was passed a query graph with more than two nodes: "
                           f"{query_graph.to_dict()}", error_code="InvalidQuery")
        elif len(query_graph.nodes) < 2:
            self.log.error(f"answer_one_hop_query() was passed a query graph with less than two nodes: "
                           f"{query_graph.to_dict()}", error_code="InvalidQuery")

    def _verify_is_single_node_query_graph(self, query_graph: QueryGraph):
        if len(query_graph.edges) > 0:
            self.log.error(f"answer_single_node_query() was passed a query graph that has edges: "
                           f"{query_graph.to_dict()}", error_code="InvalidQuery")

    @staticmethod
    def _get_kg_to_qg_mappings_from_results(results: List[Result]) -> Dict[str, Dict[str, Set[str]]]:
        """
        This function returns a dictionary in which one can lookup which qnode_keys/qedge_keys a given node/edge
        fulfills. Like: {"nodes": {"PR:11": {"n00"}, "MESH:22": {"n00", "n01"} ... }, "edges": { ... }}
        """
        qnode_key_mappings = dict()
        qedge_key_mappings = dict()
        for result in results:
            for qnode_key, node_bindings in result.node_bindings.items():
                kg_ids = {node_binding.id for node_binding in node_bindings}
                for kg_id in kg_ids:
                    if kg_id not in qnode_key_mappings:
                        qnode_key_mappings[kg_id] = set()
                    qnode_key_mappings[kg_id].add(qnode_key)
            for qedge_key, edge_bindings in result.edge_bindings.items():
                kg_ids = {edge_binding.id for edge_binding in edge_bindings}
                for kg_id in kg_ids:
                    if kg_id not in qedge_key_mappings:
                        qedge_key_mappings[kg_id] = set()
                    qedge_key_mappings[kg_id].add(qedge_key)
        return {"nodes": qnode_key_mappings, "edges": qedge_key_mappings}

    async def _answer_query_using_kp_async(self, query_graph: QueryGraph) -> QGOrganizedKnowledgeGraph:
        request_body = self._get_prepped_request_body(query_graph)
        query_timeout = self._get_query_timeout_length(query_graph)
        qedge_key = next(qedge_key for qedge_key in query_graph.edges)

        # Avoid calling the KG2 TRAPI endpoint if the 'force_local' flag is set (used only for testing/dev work)
        if self.force_local and self.kp_name == 'RTX-KG2':
            start = time.time()
            json_response = self._answer_query_force_local(request_body)
            wait_time = round(time.time() - start)
        # Otherwise send the query graph to the KP's TRAPI API
        else:
            self.log.debug(f"{self.kp_name}: Sending query to {self.kp_name} API")
            num_input_curies = max([len(eu.convert_to_list(qnode.ids)) for qnode in query_graph.nodes.values()])
            waiting_message = f"Query with {num_input_curies} curies sent: waiting for response"
            self.log.update_query_plan(qedge_key, self.kp_name, "Waiting", waiting_message)
            try:
                async with aiohttp.ClientSession() as session:
                    start = time.time()
                    async with session.post(f"{self.kp_endpoint}/query",
                                            json=request_body,
                                            headers={'accept': 'application/json'},
                                            timeout=query_timeout) as response:
                        kp_response = await response.json()
                        wait_time = round(time.time() - start)
                        if response.status != 200:
                            http_error_message = f"Returned HTTP error {response.status} after {wait_time} seconds"
                            self.log.warning(f"{self.kp_name}: {http_error_message}. "
                                             f"Response from KP was: {response.text()}")
                            self.log.update_query_plan(qedge_key, self.kp_name, "Error", http_error_message)
                            return QGOrganizedKnowledgeGraph()
                        else:
                            json_response = kp_response
            except Exception:
                timeout_message = f"Query timed out after {query_timeout} seconds"
                self.log.warning(f"{self.kp_name}: {timeout_message}")
                self.log.update_query_plan(qedge_key, self.kp_name, "Timed out", timeout_message)
                return QGOrganizedKnowledgeGraph()

        answer_kg = self._load_kp_json_response(json_response)
        done_message = f"Returned {len(answer_kg.edges_by_qg_id.get(qedge_key, dict()))} edges in {wait_time} seconds"
        self.log.update_query_plan(qedge_key, self.kp_name, "Done", done_message)
        return answer_kg

    def _answer_query_using_kp(self, query_graph: QueryGraph) -> QGOrganizedKnowledgeGraph:
        # TODO: Delete this method once we're ready to let go of the multiprocessing (vs. asyncio) option
        request_body = self._get_prepped_request_body(query_graph)
        query_timeout = self._get_query_timeout_length(query_graph)
        qedge_key = next(qedge_key for qedge_key in query_graph.edges) if query_graph.edges else None

        # Avoid calling the KG2 TRAPI endpoint if the 'force_local' flag is set (used only for testing/dev work)
        if self.force_local and self.kp_name == 'RTX-KG2':
            json_response = self._answer_query_force_local(request_body)
        # Otherwise send the query graph to the KP's TRAPI API
        else:
            self.log.debug(f"{self.kp_name}: Sending query to {self.kp_name} API")
            num_input_curies = max([len(eu.convert_to_list(qnode.ids)) for qnode in query_graph.nodes.values()])
            waiting_message = f"Query with {num_input_curies} curies sent: waiting for response"
            if qedge_key:
                self.log.update_query_plan(qedge_key, self.kp_name, "Waiting", waiting_message)
            try:
                with requests_cache.disabled():
                    start = time.time()
                    kp_response = requests.post(f"{self.kp_endpoint}/query",
                                                json=request_body,
                                                headers={'accept': 'application/json'},
                                                timeout=query_timeout)
                    self.log.wait_time = round(time.time() - start)
            except Exception:
                timeout_message = f"Query timed out after {query_timeout} seconds"
                self.log.warning(f"{self.kp_name}: {timeout_message}")
                if qedge_key:
                    self.log.update_query_plan(qedge_key, self.kp_name, "Timed out", timeout_message)
                self.log.timed_out = query_timeout
                return QGOrganizedKnowledgeGraph()
            if kp_response.status_code != 200:
                http_error_message = f"Returned HTTP error {kp_response.status_code} after {self.log.wait_time} seconds"
                self.log.warning(f"{self.kp_name} API returned response of {kp_response.status_code}. "
                                 f"Response from KP was: {kp_response.text}")
                if qedge_key:
                    self.log.update_query_plan(qedge_key, self.kp_name, "Error", http_error_message)
                self.log.http_error = f"HTTP {kp_response.status_code}"
                return QGOrganizedKnowledgeGraph()
            else:
                json_response = kp_response.json()

        answer_kg = self._load_kp_json_response(json_response)
        if qedge_key:
            done_message = f"Returned {len(answer_kg.edges_by_qg_id.get(qedge_key, dict()))} edges in {self.log.wait_time} seconds"
            self.log.update_query_plan(qedge_key, self.kp_name, "Done", done_message)
        return answer_kg

    def _get_prepped_request_body(self, qg: QueryGraph) -> dict:
        # Liberally use is_set to improve performance since we don't need individual results
        for qnode_key, qnode in qg.nodes.items():
            if not qnode.ids or len(qnode.ids) > 1:
                qnode.is_set = True

        # Strip non-essential and 'empty' properties off of our qnodes and qedges
        stripped_qnodes = {qnode_key: self._strip_empty_properties(qnode)
                           for qnode_key, qnode in qg.nodes.items()}
        stripped_qedges = {qedge_key: self._strip_empty_properties(qedge)
                           for qedge_key, qedge in qg.edges.items()}

        # Load the query into a JSON Query object
        json_qg = {'nodes': stripped_qnodes, 'edges': stripped_qedges}
        body = {'message': {'query_graph': json_qg}}
        if self.kp_name == "RTX-KG2":
            body['submitter'] = eu.get_translator_infores_curie('ARAX')
            # TODO: Later add submitter for all KP queries (isn't yet supported by all KPs - part of TRAPI 1.2.1) #1654
        return body

    def _answer_query_force_local(self, request_body: dict) -> dict:
        self.log.debug(f"{self.kp_name}: Pretending to send query to KG2 API (really it will be run locally)")
        arax_query = ARAXQuery()
        kg2_araxquery_response = arax_query.query(request_body, mode='RTXKG2')
        json_response = kg2_araxquery_response.envelope.to_dict()
        return json_response

    def _load_kp_json_response(self, json_response: dict) -> QGOrganizedKnowledgeGraph:
        # Load the results into the object model
        answer_kg = QGOrganizedKnowledgeGraph()
        if not json_response.get("message"):
            self.log.warning(f"{self.kp_name}: No 'message' was included in the response from {self.kp_name}. "
                             f"Response was: {json.dumps(json_response, indent=4)}")
            return answer_kg
        elif not json_response["message"].get("results"):
            self.log.debug(f"{self.kp_name}: No 'results' were returned.")
            json_response["message"]["results"] = []  # Setting this to empty list helps downstream processing
            return answer_kg
        else:
            self.log.debug(f"{self.kp_name}: Got results from {self.kp_name}.")
            kp_message = ARAXMessenger().from_dict(json_response["message"])

        # Build a map that indicates which qnodes/qedges a given node/edge fulfills
        kg_to_qg_mappings = self._get_kg_to_qg_mappings_from_results(kp_message.results)

        # Populate our final KG with the returned nodes and edges
        for returned_edge_key, returned_edge in kp_message.knowledge_graph.edges.items():
            arax_edge_key = self._get_arax_edge_key(returned_edge)  # Convert to an ID that's unique for us
            if not returned_edge.attributes:
                returned_edge.attributes = []
            # Put in a placeholder for missing required attribute fields to try to keep our answer TRAPI-compliant
            for attribute in returned_edge.attributes:
                if not attribute.attribute_type_id:
                    attribute.attribute_type_id = f"not provided (this attribute came from {self.kp_name})"

            # Check if KPs are properly indicating that these edges came from them (indicate it ourselves if not)
            kp_infores_curie = eu.get_translator_infores_curie(self.kp_name)
            if not any(attribute.value == kp_infores_curie for attribute in returned_edge.attributes):
                returned_edge.attributes.append(eu.get_kp_source_attribute(self.kp_name))
            # Add an attribute to indicate that this edge passed through ARAX
            returned_edge.attributes.append(eu.get_arax_source_attribute())

            for qedge_key in kg_to_qg_mappings['edges'][returned_edge_key]:
                answer_kg.add_edge(arax_edge_key, returned_edge, qedge_key)
        for returned_node_key, returned_node in kp_message.knowledge_graph.nodes.items():
            if returned_node_key not in kg_to_qg_mappings['nodes']:
                self.log.warning(f"{self.kp_name}: Node {returned_node_key} was found in {self.kp_name}'s "
                                 f"answer KnowledgeGraph but not in its Results. Skipping since there is no binding.")
            else:
                for qnode_key in kg_to_qg_mappings['nodes'][returned_node_key]:
                    answer_kg.add_node(returned_node_key, returned_node, qnode_key)
            if returned_node.attributes:
                for attribute in returned_node.attributes:
                    if not attribute.attribute_type_id:
                        attribute.attribute_type_id = f"not provided (this attribute came from {self.kp_name})"
        return answer_kg

    @staticmethod
    def _strip_empty_properties(qnode_or_qedge: Union[QNode, QEdge]) -> Dict[str, any]:
        dict_version_of_object = qnode_or_qedge.to_dict()
        stripped_dict = {property_name: value for property_name, value in dict_version_of_object.items()
                         if dict_version_of_object.get(property_name) not in [None, []]}
        return stripped_dict

    def _get_arax_edge_key(self, edge: Edge) -> str:
        return f"{self.kp_name}:{edge.subject}-{edge.predicate}-{edge.object}"

    def _get_query_timeout_length(self, qg: QueryGraph) -> int:
        # Returns the number of seconds we should wait for a response based on the number of curies in the QG
        node_curie_counts = [len(qnode.ids) for qnode in qg.nodes.values() if qnode.ids]
        num_total_curies_in_qg = sum(node_curie_counts)
        num_qnodes_with_curies = len(node_curie_counts)
        if self.kp_name == "RTX-KG2":
            return 600
        elif self.user_specified_kp:
            return 300
        elif num_qnodes_with_curies == 1:
            if num_total_curies_in_qg < 250:
                return 30
            elif num_total_curies_in_qg < 500:
                return 60
            elif num_total_curies_in_qg < 1000:
                return 120
            else:
                return 180
        else:  # Both nodes in the one-hop query must have curies specified
            if num_total_curies_in_qg < 500:
                return 30
            elif num_total_curies_in_qg < 1000:
                return 60
            else:
                return 120

