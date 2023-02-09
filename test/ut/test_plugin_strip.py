import os
import sys
import tempfile
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.strip as strip
from ecromedos.error import ECMDSPluginError


class UTTestPluginStrip(unittest.TestCase):
    def test_stripPlainTextContent(self):
        content = "<root><p>    This is a test.    </p></root>"
        root = etree.fromstring(content)

        plugin = strip.getInstance({})
        plugin.process(root.find("./p"), "xhtml")
        plugin.flush()

        tree = etree.ElementTree(element=root)

        expected_result = b"<root><p>This is a test.</p></root>"
        result = etree.tostring(tree)

        self.assertEqual(result, expected_result)

    def test_stripNestedFormattingNodes(self):
        content = "<root><p> <i> <i> </i> </i> <i> X</i> This is a test. <i>X </i> <i> <i> </i> </i> </p></root>"
        root = etree.fromstring(content)

        plugin = strip.getInstance({})
        plugin.process(root.find("./p"), "xhtml")
        plugin.flush()

        tree = etree.ElementTree(element=root)

        expected_result = b"<root><p><i><i></i></i><i>X</i> This is a test. <i>X</i><i><i></i></i></p></root>"
        result = etree.tostring(tree)

        self.assertEqual(result, expected_result)

    def test_stripStopAtHardNodes(self):
        content = "<root><p> <idref/><i> </i> This is a test. <i> </i><counter/></p></root>"
        root = etree.fromstring(content)

        plugin = strip.getInstance({})
        plugin.process(root.find("./p"), "xhtml")
        plugin.flush()

        tree = etree.ElementTree(element=root)

        expected_result = b"<root><p><idref/><i> </i> This is a test. <i> </i><counter/></p></root>"
        result = etree.tostring(tree)

        self.assertEqual(result, expected_result)
