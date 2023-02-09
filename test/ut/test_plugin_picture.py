import os
import sys
import tempfile
import unittest

import lxml.etree as etree

ECMDS_INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", ".."))

ECMDS_TEST_DATA_DIR = os.path.join(ECMDS_INSTALL_DIR, "test", "ut", "data", "plugin_picture")

sys.path.insert(1, ECMDS_INSTALL_DIR + os.sep + "lib")

import ecromedos.plugins.picture as picture
from ecromedos.error import ECMDSPluginError


class UTTestPluginPicture(unittest.TestCase):
    def test_gracefulFailOnFileNotFound(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "no_such_img_file.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)

            try:
                plugin.process(root.find("./img"), "xhtml")
            except ECMDSPluginError as e:
                self.assertTrue(e.msg().startswith("Could not find bitmap file at location"))

    def test_targetPDFLatexEPStoPDF(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "ecromedos_eps.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)
            plugin.process(root.find("./img"), "pdflatex")
            plugin.flush()

        os.unlink("img000001.pdf")

    def test_targetLatexIMGtoEPS(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "ecromedos_png.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)
            plugin.process(root.find("./img"), "latex")
            plugin.flush()

        os.unlink("img000001.eps")

    def test_targetXHTMLSetScreenWidth(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "ecromedos_png_explicit_width.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)
            plugin.process(root.find("./img"), "xhtml")
            plugin.flush()

        os.unlink("img000001.png")

    def test_targetXHTMLIdentifyWidth(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "ecromedos_png.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)
            plugin.process(root.find("./img"), "xhtml")
            plugin.flush()

        os.unlink("img000001.png")

    def test_targetXHTMLEPStoIMG(self):
        tree = etree.parse(ECMDS_TEST_DATA_DIR + os.sep + "ecromedos_eps.xml")
        root = tree.getroot()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "latex_bin": "/usr/bin/latex",
                "dvipng_bin": "/usr/bin/dvipng",
                "convert_bin": "/usr/bin/convert",
                "identify_bin": "/usr/bin/identify",
                "tmp_dir": tmpdir,
            }

            plugin = picture.getInstance(config)
            plugin.process(root.find("./img"), "xhtml")
            plugin.flush()

        os.unlink("img000001.jpg")
