import os
import sys
import tempfile
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.text as text
from ecromedos.error import ECMDSPluginError


class UTTestPluginText(unittest.TestCase):
    def test_escapeLatexSpecialChars(self):
        content = "<root>Here comes text: []{}#&amp;_%$^\\~-:;!?\"`'=\n</root>"
        root = etree.fromstring(content)

        plugin = text.getInstance({})
        root.text = plugin.process(root.text, "latex")
        plugin.flush()

        tree = etree.ElementTree(element=root)
        result = etree.tostring(tree)

        expected_result = b"<root>Here comes text{}{\\string:}{} {[}{]}\\{{}\\}{}\\#{}\\&amp;{}\\_{}\\%{}\\${}\\^{}\\textbackslash{}\\textasciitilde{}{}{\\string-}{}{}{\\string:}{}{}{\\string;}{}{}{\\string!}{}{}{\\string?}{}{}{\\string\"}{}{}{\\string`}{}{}{\\string'}{}{}{\\string=}{}\n</root>"

        self.assertEqual(result, expected_result)
