# coding: utf-8

"""
    DASS Will Model Schema

    OpenAPI-style specification of the Will Model Schema   # noqa: E501

    OpenAPI spec version: 0.1.0
    Contact: salena@arizona.edu, claytonm@arizona.edu
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class WMVariableReference(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'name': 'str',
        'dass_type': 'str'
    }

    attribute_map = {
        'name': 'name',
        'dass_type': 'dass_type'
    }

    def __init__(self, name=None, dass_type='WM_VariableReference'):  # noqa: E501
        """WMVariableReference - a model defined in Swagger"""  # noqa: E501
        self._name = None
        self._dass_type = None
        self.discriminator = None
        self.name = name
        self.dass_type = dass_type

    @property
    def name(self):
        """Gets the name of this WMVariableReference.  # noqa: E501

        The name of the Variable  # noqa: E501

        :return: The name of this WMVariableReference.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this WMVariableReference.

        The name of the Variable  # noqa: E501

        :param name: The name of this WMVariableReference.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def dass_type(self):
        """Gets the dass_type of this WMVariableReference.  # noqa: E501


        :return: The dass_type of this WMVariableReference.  # noqa: E501
        :rtype: str
        """
        return self._dass_type

    @dass_type.setter
    def dass_type(self, dass_type):
        """Sets the dass_type of this WMVariableReference.


        :param dass_type: The dass_type of this WMVariableReference.  # noqa: E501
        :type: str
        """
        if dass_type is None:
            raise ValueError("Invalid value for `dass_type`, must not be `None`")  # noqa: E501

        self._dass_type = dass_type

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(WMVariableReference, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, WMVariableReference):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
