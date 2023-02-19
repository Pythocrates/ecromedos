# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import io
from pathlib import Path
import re
import tempfile

from lxml import etree
from ecromedos.argumentparser import GeneratorType

from ecromedos.error import ECMDSPluginError
from ecromedos.helpers import ExternalTool


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    def __init__(self, config):
        self._counter = 1
        self._nodes = []

        self._run_latex = ExternalTool("latex", "-interaction", "nonstopmode")
        self._run_dvipng = ExternalTool(
            "dvipng", "-D", config.get("dvipng_dpi", "100"), "--depth", "-gif", "-T", "tight", "-o", "m%06d.gif"
        )

        # temporary directory
        self._tmp_dir = Path(config["tmp_dir"])

        # output document
        self.out = io.StringIO()

    def process(self, node, format):
        """Prepare @node for target @format."""

        if format.endswith("latex"):
            result = self.LaTeX_ProcessMath(node)
        else:
            result = self.XHTML_ProcessMath(node)

        return result

    def flush(self):
        """If target format is XHTML, generate GIFs from formulae."""

        # generate bitmaps of formulae
        if self.out.tell() > 0:
            self.out.write("\\end{document}\n")
            self._latex_to_dvi_to_gif()
            self.out.close()
            self.out = io.StringIO()

        self._counter = 1
        self._nodes = []

    def LaTeX_ProcessMath(self, node):
        """Mark node, to be copied 1:1 to output document."""

        math_node = etree.Element("m")

        parent = node.getparent()
        math_node.tail = node.tail
        parent.replace(node, math_node)

        node.tag = "copy"
        node.tail = ""
        math_node.append(node)

        return math_node

    def XHTML_ProcessMath(self, node):
        """Call LaTeX and ImageMagick to produce a GIF."""

        if self.out.tell() == 0:
            self.out.write(
                """\
\\documentclass[12pt]{scrartcl}\\usepackage{courier}
\\usepackage{courier}
\\usepackage{helvet}
\\usepackage{mathpazo}
\\usepackage{amsmath}
\\usepackage[active,displaymath,textmath]{preview}
\\frenchspacing{}
\\usepackage{ucs}
\\usepackage[utf8x]{inputenc}
\\usepackage[T1]{autofe}
\\PrerenderUnicode{äöüß}
\\pagestyle{empty}
\\begin{document}"""
            )

        # save TeX markup
        # formula = etree.tostring(node, method="text", encoding="unicode")

        # give each formula one page
        self.out.write("$%s$\n\\clearpage{}\n" % node.text)

        copy_node = etree.Element("copy")
        img_node = etree.Element("img")

        img_node.attrib["src"] = "m%06d.gif" % (self._counter,)
        img_node.attrib["alt"] = "formula"
        img_node.attrib["class"] = "math"

        copy_node.tail = node.tail
        copy_node.append(img_node)
        copy_node.tail = node.tail
        node.getparent().replace(node, copy_node)

        # keep track of images for flush
        self._nodes.append(img_node)
        self._counter += 1

        return copy_node

    def _latex_to_dvi_to_gif(self):
        """Write formulae to LaTeX file, compile and extract images."""

        # open a temporary file for TeX output
        tmp_tex_file_path = Path(tempfile.mkstemp(suffix=".tex", dir=self._tmp_dir)[-1])

        try:
            with open(tmp_tex_file_path, "w", encoding="utf-8") as tex_file:
                tex_file.write(self.out.getvalue())
        except IOError:
            raise ECMDSPluginError("Error while writing temporary TeX file.", "math")

        for _ in range(2):
            try:
                self._run_latex(tmp_tex_file_path, cwd=self._tmp_dir)
            except ECMDSPluginError:
                raise ECMDSPluginError("Could not compile temporary TeX file.", "math")

        # determine dvi file name
        dvi_file_path = self._tmp_dir / tmp_tex_file_path.with_suffix(".dvi").name

        # convert dvi file to GIF image
        try:
            result = self._run_dvipng(dvi_file_path)
        except ECMDSPluginError:
            raise ECMDSPluginError(f"Could not convert dvi file {dvi_file_path} to GIF images.", "math")

        # look for [??? depth=???px]
        rexpr = re.compile("\\[[0-9]* depth=[0-9]*\\]")

        # add style property to node
        for match, node in zip(rexpr.finditer(result), self._nodes):
            align = match.group().split("=")[1].strip(" []")
            node.attrib["style"] = "vertical-align: -" + align + "px;"
