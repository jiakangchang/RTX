# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class Node(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, type: str=None, id: str=None, symbol: str=None, name: str=None, accession: str=None, description: str=None):  # noqa: E501
        """Node - a model defined in Swagger

        :param type: The type of this Node.  # noqa: E501
        :type type: str
        :param id: The id of this Node.  # noqa: E501
        :type id: str
        :param symbol: The symbol of this Node.  # noqa: E501
        :type symbol: str
        :param name: The name of this Node.  # noqa: E501
        :type name: str
        :param accession: The accession of this Node.  # noqa: E501
        :type accession: str
        :param description: The description of this Node.  # noqa: E501
        :type description: str
        """
        self.swagger_types = {
            'type': str,
            'id': str,
            'symbol': str,
            'name': str,
            'accession': str,
            'description': str
        }

        self.attribute_map = {
            'type': 'type',
            'id': 'id',
            'symbol': 'symbol',
            'name': 'name',
            'accession': 'accession',
            'description': 'description'
        }

        self._type = type
        self._id = id
        self._symbol = symbol
        self._name = name
        self._accession = accession
        self._description = description

    @classmethod
    def from_dict(cls, dikt) -> 'Node':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Node of this Node.  # noqa: E501
        :rtype: Node
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self) -> str:
        """Gets the type of this Node.

        Entity type of this node (e.g., protein, disease, etc.)  # noqa: E501

        :return: The type of this Node.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this Node.

        Entity type of this node (e.g., protein, disease, etc.)  # noqa: E501

        :param type: The type of this Node.
        :type type: str
        """

        self._type = type

    @property
    def id(self) -> str:
        """Gets the id of this Node.

        URI identifier for this response  # noqa: E501

        :return: The id of this Node.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Node.

        URI identifier for this response  # noqa: E501

        :param id: The id of this Node.
        :type id: str
        """

        self._id = id

    @property
    def symbol(self) -> str:
        """Gets the symbol of this Node.

        Short abbreviation or symbol for this entity  # noqa: E501

        :return: The symbol of this Node.
        :rtype: str
        """
        return self._symbol

    @symbol.setter
    def symbol(self, symbol: str):
        """Sets the symbol of this Node.

        Short abbreviation or symbol for this entity  # noqa: E501

        :param symbol: The symbol of this Node.
        :type symbol: str
        """

        self._symbol = symbol

    @property
    def name(self) -> str:
        """Gets the name of this Node.

        Formal name of the entity  # noqa: E501

        :return: The name of this Node.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this Node.

        Formal name of the entity  # noqa: E501

        :param name: The name of this Node.
        :type name: str
        """

        self._name = name

    @property
    def accession(self) -> str:
        """Gets the accession of this Node.

        Accession number in an external resource for this entity  # noqa: E501

        :return: The accession of this Node.
        :rtype: str
        """
        return self._accession

    @accession.setter
    def accession(self, accession: str):
        """Sets the accession of this Node.

        Accession number in an external resource for this entity  # noqa: E501

        :param accession: The accession of this Node.
        :type accession: str
        """

        self._accession = accession

    @property
    def description(self) -> str:
        """Gets the description of this Node.

        One to three sentences of description/definition of this entity  # noqa: E501

        :return: The description of this Node.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description: str):
        """Sets the description of this Node.

        One to three sentences of description/definition of this entity  # noqa: E501

        :param description: The description of this Node.
        :type description: str
        """

        self._description = description
