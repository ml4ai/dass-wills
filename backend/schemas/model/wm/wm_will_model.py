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

class WMWillModel(object):
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
        'text': 'str',
        'testator': 'WMPerson',
        'witnesses': 'list[WMPerson]',
        '_date': 'date',
        'directives': 'list[WMDirectiveBody]',
        'dass_type': 'str'
    }

    attribute_map = {
        'text': 'text',
        'testator': 'testator',
        'witnesses': 'witnesses',
        '_date': 'date',
        'directives': 'directives',
        'dass_type': 'dass_type'
    }

    def __init__(self, text=None, testator=None, witnesses=None, _date=None, directives=None, dass_type='WM_WillModel'):  # noqa: E501
        """WMWillModel - a model defined in Swagger"""  # noqa: E501
        self._text = None
        self._testator = None
        self._witnesses = None
        self.__date = None
        self._directives = None
        self._dass_type = None
        self.discriminator = None
        self.text = text
        if testator is not None:
            self.testator = testator
        if witnesses is not None:
            self.witnesses = witnesses
        self._date = _date
        if directives is not None:
            self.directives = directives
        self.dass_type = dass_type
        self.checksum=None

    @property
    def text(self):
        """Gets the text of this WMWillModel.  # noqa: E501

        The original raw text of the will.   # noqa: E501

        :return: The text of this WMWillModel.  # noqa: E501
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, text):
        """Sets the text of this WMWillModel.

        The original raw text of the will.   # noqa: E501

        :param text: The text of this WMWillModel.  # noqa: E501
        :type: str
        """
        if text is None:
            raise ValueError("Invalid value for `text`, must not be `None`")  # noqa: E501

        self._text = text

    @property
    def testator(self):
        """Gets the testator of this WMWillModel.  # noqa: E501


        :return: The testator of this WMWillModel.  # noqa: E501
        :rtype: WMPerson
        """
        return self._testator

    @testator.setter
    def testator(self, testator):
        """Sets the testator of this WMWillModel.


        :param testator: The testator of this WMWillModel.  # noqa: E501
        :type: WMPerson
        """

        self._testator = testator

    @property
    def witnesses(self):
        """Gets the witnesses of this WMWillModel.  # noqa: E501

        Array of Witnesses witnessing the will creation.   # noqa: E501

        :return: The witnesses of this WMWillModel.  # noqa: E501
        :rtype: list[WMPerson]
        """
        return self._witnesses

    @witnesses.setter
    def witnesses(self, witnesses):
        """Sets the witnesses of this WMWillModel.

        Array of Witnesses witnessing the will creation.   # noqa: E501

        :param witnesses: The witnesses of this WMWillModel.  # noqa: E501
        :type: list[WMPerson]
        """

        self._witnesses = witnesses

    @property
    def _date(self):
        """Gets the _date of this WMWillModel.  # noqa: E501

        The date of the creation or modification of the current WillModel   # noqa: E501

        :return: The _date of this WMWillModel.  # noqa: E501
        :rtype: date
        """
        return self.__date

    @_date.setter
    def _date(self, _date):
        """Sets the _date of this WMWillModel.

        The date of the creation or modification of the current WillModel   # noqa: E501

        :param _date: The _date of this WMWillModel.  # noqa: E501
        :type: date
        """
        if _date is None:
            raise ValueError("Invalid value for `_date`, must not be `None`")  # noqa: E501

        self.__date = _date

    @property
    def directives(self):
        """Gets the directives of this WMWillModel.  # noqa: E501

        Array of will Directives   # noqa: E501

        :return: The directives of this WMWillModel.  # noqa: E501
        :rtype: list[WMDirectiveBody]
        """
        return self._directives

    @directives.setter
    def directives(self, directives):
        """Sets the directives of this WMWillModel.

        Array of will Directives   # noqa: E501

        :param directives: The directives of this WMWillModel.  # noqa: E501
        :type: list[WMDirectiveBody]
        """

        self._directives = directives

    @property
    def dass_type(self):
        """Gets the dass_type of this WMWillModel.  # noqa: E501


        :return: The dass_type of this WMWillModel.  # noqa: E501
        :rtype: str
        """
        return self._dass_type

    @dass_type.setter
    def dass_type(self, dass_type):
        """Sets the dass_type of this WMWillModel.


        :param dass_type: The dass_type of this WMWillModel.  # noqa: E501
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
        if issubclass(WMWillModel, dict):
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
        if not isinstance(other, WMWillModel):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
