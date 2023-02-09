import os
import sys
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.data as data
from ecromedos.error import ECMDSPluginError


class UTTestPluginData(unittest.TestCase):
    def test_markNodeAsFinal(self):
        filelist = ["next.gif", "prev.gif", "up.gif"]

        xmldoc = """<root secsplitdepth="1"></root>"""

        root = etree.fromstring(xmldoc)
        tree = etree.ElementTree(element=root)

        plugin = data.getInstance({"data_dir": ECMDS_INSTALL_DIR + os.sep + "data"})
        plugin.process(root, "xhtml")
        plugin.flush()

        all_files_found = True
        for f in filelist:
            try:
                os.unlink(f)
            except:
                all_files_found = False

        self.assertTrue(all_files_found)
