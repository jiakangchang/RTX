import unittest
import json

import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

from Neo4jConnection import Neo4jConnection

class KGTestCase(unittest.TestCase):

    def test_anatomical_entity_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("UBERON:0001753")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "UBERON:0001753")
        self.assertEqual(nodes['n']['name'], "cementum")
        self.assertEqual(nodes['n']['description'], "Odontoid tissue that is deposited by cementoblasts onto dentine "
                                                    "tissue and functions to attach teeth, odontodes and other "
                                                    "odontogenic derivatives to bone tissue and the integument.")
        self.assertEqual(nodes['n']['category'], "anatomical_entity")
        self.assertEqual(nodes['n']['UUID'], "b0336992-9875-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_biological_process_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("GO:0048817")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "GO:0048817")
        self.assertEqual(nodes['n']['name'], "negative regulation of hair follicle maturation")
        self.assertEqual(nodes['n']['description'], "Any process that stops, prevents, or reduces the frequency, "
                                                    "rate or extent of hair follicle maturation.")
        self.assertEqual(nodes['n']['category'], "biological_process")
        self.assertEqual(nodes['n']['UUID'], "d47e7670-96e0-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_cellular_component_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("GO:0071005")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "GO:0071005")
        self.assertEqual(nodes['n']['name'], "U2-type precatalytic spliceosome")
        self.assertEqual(nodes['n']['description'], "A spliceosomal complex that is formed by the recruitment of the "
                                                    "preassembled U4/U6.U5 tri-snRNP to the prespliceosome. Although "
                                                    "all 5 snRNPs are present, the precatalytic spliceosome is "
                                                    "catalytically inactive. The precatalytic spliceosome includes "
                                                    "many proteins in addition to those found in the U1, U2 and "
                                                    "U4/U6.U5 snRNPs.")
        self.assertEqual(nodes['n']['category'], "cellular_component")
        self.assertEqual(nodes['n']['UUID'], "d5061044-96e0-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_chemical_substance_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("CHEMBL1236962")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "CHEMBL1236962")
        self.assertEqual(nodes['n']['name'], "omipalisib")
        self.assertEqual(nodes['n']['description'], "None")
        self.assertEqual(nodes['n']['category'], "chemical_substance")
        self.assertEqual(nodes['n']['UUID'], "d205341a-96e0-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_disease_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("DOID:6016")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "DOID:6016")
        self.assertEqual(nodes['n']['name'], "adult central nervous system mature teratoma")
        self.assertEqual(nodes['n']['description'], "None")
        self.assertEqual(nodes['n']['category'], "disease")
        self.assertEqual(nodes['n']['UUID'], "16301a48-96e0-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_metabolite_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("KEGG:C19630")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "KEGG:C19630")
        self.assertEqual(nodes['n']['name'], "Diketone")
        self.assertEqual(nodes['n']['description'], "None")
        self.assertEqual(nodes['n']['category'], "metabolite")
        self.assertEqual(nodes['n']['UUID'], "d7ad8084-96e0-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    def test_microRNA_nodes(self):
        f = open('config.json', 'r')
        config_data = f.read()
        f.close()
        config = json.loads(config_data)

        conn = Neo4jConnection(config['url'], config['username'], config['password'])
        nodes = conn.get_node("NCBIGene:100302124")

        self.assertIsNotNone(nodes)
        self.assertEqual(nodes['n']['rtx_name'], "NCBIGene:100302124")
        self.assertEqual(nodes['n']['name'], "MIR1288")
        self.assertEqual(nodes['n']['symbol'], "MIR1288")
        self.assertEqual(nodes['n']['category'], "microRNA")
        self.assertEqual(nodes['n']['UUID'], "0c04b8fa-96e3-11e8-b6f4-0242ac110002")
        self.assertEqual(nodes['n']['seed_node_uuid'], "14aa4450-96e0-11e8-b6f4-0242ac110002")

        conn.close()

    
