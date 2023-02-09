# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net


class ECMDSError(Exception):
    """Generic base class."""

    def __init__(self, value):
        self.value = value

    def repr(self, arg):
        if isinstance(arg, str):
            return arg
        else:
            return repr(arg)

    def __str__(self):
        return self.repr(self.value)

    def msg(self):
        return self.__str__()


class ECMDSConfigError(ECMDSError):
    pass


class ECMDSPluginError(ECMDSError):
    def __init__(self, value, plugin_name):
        ECMDSError.__init__(self, value)
        self.plugin_name = plugin_name

    def pluginName(self):
        return self.repr(self.plugin_name)
