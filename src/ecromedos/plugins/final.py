# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    def __init__(self, config):
        pass

    def flush(self):
        pass

    def process(self, node, format):
        """Prepare @node for target @format."""
        node.attrib["final"] = "yes"
        return node
