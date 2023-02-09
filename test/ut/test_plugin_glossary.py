#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import sys
import tempfile
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.glossary as glossary
from ecromedos.error import ECMDSPluginError


class UTTestPluginGlossary(unittest.TestCase):
    def test_collectDeftermsAndBuildGlossary(self):
        defterms = [
            """
<defterm>
    <dt>Gabcde</dt>
    <dd>
    Here comes Gabcde's definition.
    </dd>
</defterm>
""",
            """
<defterm>
    <dt>Babcde</dt>
    <dd>
    Here comes Babcde's definition.
    </dd>
</defterm>
""",
            """
<defterm>
    <dt>Abcde</dt>
    <dd>
    Here comes Aabcde's definition.
    </dd>
</defterm>
""",
            """
<defterm>
    <dt>@__</dt>
    <dd>
    Here comes @__ definition.
    </dd>
</defterm>
""",
        ]
        plugin = glossary.getInstance({})

        for term in defterms:
            defterm_node = etree.fromstring(term)
            plugin.process(defterm_node, "xhtml")
        # end for

        glossary_node = etree.fromstring(
            """<make-glossary
                alphabet="[S y m b o l e],A,B,C,G,Z"
                locale="de_DE.UTF-8"/>"""
        )
        plugin.process(glossary_node, "xhtml")

        tree = etree.ElementTree(element=glossary_node)
        result = etree.tostring(tree, pretty_print=True, encoding="unicode")

        expected_result = """\
<glossary alphabet="[S y m b o l e],A,B,C,G,Z" locale="de_DE.UTF-8">
  <glsection name="S y m b o l e">
    <dl><dt>@__</dt>
    <dd>
    Here comes @__ definition.
    </dd>
</dl>
  </glsection>
  <glsection name="A">
    <dl><dt>Abcde</dt>
    <dd>
    Here comes Aabcde's definition.
    </dd>
</dl>
  </glsection>
  <glsection name="B">
    <dl><dt>Babcde</dt>
    <dd>
    Here comes Babcde's definition.
    </dd>
</dl>
  </glsection>
  <glsection name="C">
    <dl/>
  </glsection>
  <glsection name="G">
    <dl><dt>Gabcde</dt>
    <dd>
    Here comes Gabcde's definition.
    </dd>
</dl>
  </glsection>
  <glsection name="Z">
    <dl/>
  </glsection>
</glossary>
       """

        self.assertEqual(result.strip(), expected_result.strip())

    # end function


# end class

if __name__ == "__main__":
    unittest.main()
