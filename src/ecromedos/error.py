# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net


class ECMDSError(Exception):
    """Generic base class."""

    def __init__(self, value):
        self._value = value

    def repr(self, arg):
        if isinstance(arg, str):
            return arg
        else:
            return repr(arg)

    def __str__(self):
        return self.repr(self._value)

    def msg(self):
        return str(self)


class ECMDSConfigError(ECMDSError):
    pass


class ECMDSPluginError(ECMDSError):
    def __init__(self, value, plugin_name):
        super().__init__(value)
        self._plugin_name = plugin_name
