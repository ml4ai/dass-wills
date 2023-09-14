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

class WMDirectiveBequeath(object):
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
        'type': 'str',
        'beneficiaries': 'list[WMTypeBeneficiary]',
        'assets': 'list[WMAsset]',
        'dass_type': 'str'
    }

    attribute_map = {
        'type': 'type',
        'beneficiaries': 'beneficiaries',
        'assets': 'assets',
        'dass_type': 'dass_type'
    }

    def __init__(self, type='DirectiveBequeath', beneficiaries=None, assets=None, dass_type='WM_DirectiveBequeath'):  # noqa: E501
        """WMDirectiveBequeath - a model defined in Swagger"""  # noqa: E501
        self._type = None
        self._beneficiaries = None
        self._assets = None
        self._dass_type = None
        self.discriminator = None
        self.type = type
        self.beneficiaries = beneficiaries
        self.assets = assets
        self.dass_type = dass_type

    @property
    def type(self):
        """Gets the type of this WMDirectiveBequeath.  # noqa: E501


        :return: The type of this WMDirectiveBequeath.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this WMDirectiveBequeath.


        :param type: The type of this WMDirectiveBequeath.  # noqa: E501
        :type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501

        self._type = type

    @property
    def beneficiaries(self):
        """Gets the beneficiaries of this WMDirectiveBequeath.  # noqa: E501


        :return: The beneficiaries of this WMDirectiveBequeath.  # noqa: E501
        :rtype: list[WMTypeBeneficiary]
        """
        return self._beneficiaries

    @beneficiaries.setter
    def beneficiaries(self, beneficiaries):
        """Sets the beneficiaries of this WMDirectiveBequeath.


        :param beneficiaries: The beneficiaries of this WMDirectiveBequeath.  # noqa: E501
        :type: list[WMTypeBeneficiary]
        """
        if beneficiaries is None:
            raise ValueError("Invalid value for `beneficiaries`, must not be `None`")  # noqa: E501

        self._beneficiaries = beneficiaries

    @property
    def assets(self):
        """Gets the assets of this WMDirectiveBequeath.  # noqa: E501


        :return: The assets of this WMDirectiveBequeath.  # noqa: E501
        :rtype: list[WMAsset]
        """
        return self._assets

    @assets.setter
    def assets(self, assets):
        """Sets the assets of this WMDirectiveBequeath.


        :param assets: The assets of this WMDirectiveBequeath.  # noqa: E501
        :type: list[WMAsset]
        """
        if assets is None:
            raise ValueError("Invalid value for `assets`, must not be `None`")  # noqa: E501

        self._assets = assets

    @property
    def dass_type(self):
        """Gets the dass_type of this WMDirectiveBequeath.  # noqa: E501


        :return: The dass_type of this WMDirectiveBequeath.  # noqa: E501
        :rtype: str
        """
        return self._dass_type

    @dass_type.setter
    def dass_type(self, dass_type):
        """Sets the dass_type of this WMDirectiveBequeath.


        :param dass_type: The dass_type of this WMDirectiveBequeath.  # noqa: E501
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
        if issubclass(WMDirectiveBequeath, dict):
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
        if not isinstance(other, WMDirectiveBequeath):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
