# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
#from openapi_server.models.one_ofstringarray import OneOfstringarray
from openapi_server import util

#from openapi_server.models.one_ofstringarray import OneOfstringarray  # noqa: E501

class QNode(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None, category=None, is_set=False, option_group_id=None):  # noqa: E501
        """QNode - a model defined in OpenAPI

        :param id: The id of this QNode.  # noqa: E501
        :type id: OneOfstringarray
        :param category: The category of this QNode.  # noqa: E501
        :type category: OneOfstringarray
        :param is_set: The is_set of this QNode.  # noqa: E501
        :type is_set: bool
        :param option_group_id: The option_group_id of this QNode.  # noqa: E501
        :type option_group_id: str
        """
        self.openapi_types = {
            #'id': OneOfstringarray,
            'id': str,
            #'category': OneOfstringarray,
            'category': str,
            'is_set': bool,
            'option_group_id': str
        }

        self.attribute_map = {
            'id': 'id',
            'category': 'category',
            'is_set': 'is_set',
            'option_group_id': 'option_group_id'
        }

        self._id = id
        self._category = category
        self._is_set = is_set
        self._option_group_id = option_group_id

    @classmethod
    def from_dict(cls, dikt) -> 'QNode':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The QNode of this QNode.  # noqa: E501
        :rtype: QNode
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this QNode.

        CURIE identifier for this node  # noqa: E501

        :return: The id of this QNode.
        :rtype: OneOfstringarray
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this QNode.

        CURIE identifier for this node  # noqa: E501

        :param id: The id of this QNode.
        :type id: OneOfstringarray
        """

        self._id = id

    @property
    def category(self):
        """Gets the category of this QNode.


        :return: The category of this QNode.
        :rtype: OneOfstringarray
        """
        return self._category

    @category.setter
    def category(self, category):
        """Sets the category of this QNode.


        :param category: The category of this QNode.
        :type category: OneOfstringarray
        """

        self._category = category

    @property
    def is_set(self):
        """Gets the is_set of this QNode.

        Boolean that if set to true, indicates that this QNode MAY have multiple KnowledgeGraph Nodes bound to it within each Result. The nodes in a set should be considered as a set of independent nodes, rather than a set of dependent nodes, i.e., the answer would still be valid if the nodes in the set were instead returned individually. Multiple QNodes may have is_set=True. If a QNode (n1) with is_set=True is connected to a QNode (n2) with is_set=False, each n1 must be connected to n2. If a QNode (n1) with is_set=True is connected to a QNode (n2) with is_set=True, each n1 must be connected to at least one n2.  # noqa: E501

        :return: The is_set of this QNode.
        :rtype: bool
        """
        return self._is_set

    @is_set.setter
    def is_set(self, is_set):
        """Sets the is_set of this QNode.

        Boolean that if set to true, indicates that this QNode MAY have multiple KnowledgeGraph Nodes bound to it within each Result. The nodes in a set should be considered as a set of independent nodes, rather than a set of dependent nodes, i.e., the answer would still be valid if the nodes in the set were instead returned individually. Multiple QNodes may have is_set=True. If a QNode (n1) with is_set=True is connected to a QNode (n2) with is_set=False, each n1 must be connected to n2. If a QNode (n1) with is_set=True is connected to a QNode (n2) with is_set=True, each n1 must be connected to at least one n2.  # noqa: E501

        :param is_set: The is_set of this QNode.
        :type is_set: bool
        """

        self._is_set = is_set

    @property
    def option_group_id(self):
        """Gets the option_group_id of this QNode.

        Optional string acting as a label on a set of nodes and/or edges indicating that they belong to a group that are to be evaluated as a group.   # noqa: E501

        :return: The option_group_id of this QNode.
        :rtype: str
        """
        return self._option_group_id

    @option_group_id.setter
    def option_group_id(self, option_group_id):
        """Sets the option_group_id of this QNode.

        Optional string acting as a label on a set of nodes and/or edges indicating that they belong to a group that are to be evaluated as a group.   # noqa: E501

        :param option_group_id: The option_group_id of this QNode.
        :type option_group_id: str
        """

        self._option_group_id = option_group_id
