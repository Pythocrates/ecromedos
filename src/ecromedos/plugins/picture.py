# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from pathlib import Path
import re
import shutil
import tempfile

from ecromedos.argumentparser import GeneratorType
from ecromedos.error import ECMDSPluginError
from ecromedos.helpers import ExternalTool


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    _DEFAULT_RESOLUTION_DPI = 100

    def __init__(self, config):
        self._counter = 1
        self.imgmap = {}
        self.imgwidth = {}

        self._run_convert = ExternalTool(
            "convert", "-antialias", "-density", config.get("convert_dpi", self._DEFAULT_RESOLUTION_DPI)
        )
        self._run_identify = ExternalTool("identify")

        # temporary directory
        self._tmp_dir = Path(config["tmp_dir"])

    def process(self, node, format):
        """Prepare @node for target @format."""

        if format == GeneratorType.LATEX:
            self.LaTeX_prepareImg(node)
        elif format.endswith("latex"):
            self.LaTeX_prepareImg(node, format="pdf")
        else:
            self.XHTML_prepareImg(node)

        return node

    def flush(self):
        # reset counter
        self._counter = 1
        self.imgmap = {}
        self.imgwidth = {}

    def LaTeX_prepareImg(self, node, format="eps"):
        # get image src path
        src = self._get_image_source_path(node)
        dst = ""

        # check if we used this image before
        try:
            dst = self.imgmap[src][0]
        except KeyError:
            dst = "img%06d.%s" % (self._counter, format)
            self._counter += 1

            if not (extension := src.suffix[1:]) == format:
                if extension == ".eps" and format == "pdf":
                    self._eps_to_pdf(src, dst)
                else:
                    self._convert_image(src, dst)
            else:
                shutil.copyfile(src, dst)

            self.imgmap[src] = [dst]

        # set src attribute to new file
        node.attrib["src"] = dst

    def XHTML_prepareImg(self, node):
        # get image src path
        src = self._get_image_source_path(node)
        dst = ""

        width = node.attrib.get("screen-width", None)

        if width:
            width = re.match("[1-9][0-9]*", width).group()
        else:
            width = self._identify_width(src)

        try:
            imglist = self.imgmap[src]

            for img in imglist:
                img_width = self.imgwidth[img]

                if width == img_width:
                    dst = img
                    break
        except KeyError:
            pass

        if not dst:
            # check image format
            ext = src.suffix

            if ext.casefold() in ["jpg", "gif", "png"]:
                dst = "img%06d.%s" % (self._counter, ext.lower())
                self._convert_image(src, dst, width)
            else:
                dst = "img%06d.jpg" % (self._counter,)
                self._convert_image(src, dst, width)

            self.imgwidth[dst] = width
            self.imgmap.setdefault(src, []).append(dst)
            self._counter += 1

        # set src attribute to new file
        node.attrib["src"] = dst

    @staticmethod
    def _get_image_source_path(node):
        # location of image
        try:
            src = Path(node.attrib["src"])
        except KeyError:
            msg = f"Emtpy or missing 'src' attribute in 'img' tag on line {node.sourceline}."
            raise ECMDSPluginError(msg, "picture")

        # if src is a relative path, prepend doc's location
        if not src.is_absolute():
            # get the root node
            tree = node.getroottree()

            baseURL = Path(tree.docinfo.URL).absolute().parent
            src = baseURL.joinpath(src)

        if not src.is_file():
            msg = f"Could not find bitmap file at location {src} "
            msg += f"as specified in 'img' tag on line {node.sourceline}."
            raise ECMDSPluginError(msg, "picture")

        return src

    def _convert_image(self, src, dst, width=None):
        # build command line
        args = ["-scale", width + "x"] if width else []

        # remove alpha channel if not supported
        if not dst[-4:] in [".png", ".pdf", ".svg", ".eps"]:
            args += ["-alpha", "remove"]

        try:
            self._run_convert(*args, src, dst)
        except ECMDSPluginError:
            raise ECMDSPluginError(f"Could not convert graphics file {src}.", "picture")

    def _eps_to_pdf(self, src, dst):

        # look for bounding box
        rexpr = re.compile(r"(^%%BoundingBox:)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)")

        infile = None
        outfile = None

        try:
            # open source file and temporary output
            infile = open(src, "r", encoding="utf-8")
            _, tmpname = tempfile.mkstemp(suffix=".eps", dir=self._tmp_dir)

            # Look for bounding box and adjust
            done = False
            with open(tmpname, "w", encoding="utf-8") as outfile:
                for line in infile:
                    m = rexpr.match(line)

                    if not done and m:
                        llx = int(m.group(2))
                        lly = int(m.group(3))
                        urx = int(m.group(4))
                        ury = int(m.group(5))
                        width, height = (urx - llx, ury - lly)
                        xoff, yoff = (-llx, -lly)
                        outfile.write("%%%%BoundingBox: 0 0 %d %d\n" % (width, height))
                        outfile.write("<< /PageSize [%d %d] >> setpagedevice\n" % (width, height))
                        outfile.write("gsave %d %d translate\n" % (xoff, yoff))
                        done = True
                    else:
                        outfile.write(line)

            self._convert_image(tmpname, dst)
        except IOError:
            msg = "Could not convert EPS file '%s'" % src
            raise ECMDSPluginError(msg, "picture")
        finally:
            try:
                infile.close()
            except Exception:
                pass

    def _identify_width(self, src):
        # This is a bit of an interesting way to determine an error condition...
        result = self._run_identify(src)
        if result.startswith("identify:"):
            raise ECMDSPluginError(f"Could not determine bitmap's dimensions:\n  {result}.", "picture")

        rexpr = re.compile("[0-9]+x[0-9]+")
        try:
            return next(value.split("x")[0] for value in result.split() if rexpr.match(value))
        except StopIteration:
            raise ECMDSPluginError(f"Could not determine bitmap's dimensions:\n  {src}", "picture")
