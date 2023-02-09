import os
import sys
import tempfile
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.math as math
from ecromedos.error import ECMDSPluginError


class UTTestPluginMath(unittest.TestCase):
    def test_handleMathNodeLatex(self):
        root = etree.fromstring("<root><m>Formula Here</m></root>")

        config = {"latex_bin": "/usr/bin/latex", "dvipng_bin": "/usr/bin/dvipng", "tmp_dir": "/tmp"}

        plugin = math.getInstance(config)
        plugin.process(root.find("./m"), "latex")

        tree = etree.ElementTree(element=root)
        result = etree.tostring(tree, encoding="utf-8", method="xml")

        expected_result = b"<root><m><copy>Formula Here</copy></m></root>"
        self.assertEqual(result, expected_result)

    def test_handleMathNodeXHTML(self):
        root = etree.fromstring("<root><m>Formula Here</m></root>")

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"latex_bin": "/usr/bin/latex", "dvipng_bin": "/usr/bin/dvipng", "tmp_dir": tmpdir}
            plugin = math.getInstance(config)
            plugin.process(root.find("./m"), "xhtml")
            plugin.flush()

        tree = etree.ElementTree(element=root)
        result = etree.tostring(tree, encoding="utf-8", method="xml")

        expected_result = b'<root><copy><img src="m000001.gif" alt="formula" class="math" style="vertical-align: -1px;"/></copy></root>'
        self.assertEqual(result, expected_result)
        os.unlink("m000001.gif")
