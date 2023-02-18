# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from ecromedos.error import ECMDSPluginError


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    def __init__(self, config):
        # set counter
        self.counter = 1
        self.imgmap = {}
        self.imgwidth = {}

        # look for conversion tool
        try:
            self.convert_bin = config["convert_bin"]
        except KeyError:
            msg = "Location of the 'convert' executable not specified."
            raise ECMDSPluginError(msg, "picture")
        if not Path(self.convert_bin).is_file():
            msg = "Could not find 'convert' executable '%s'." % (self.convert_bin,)
            raise ECMDSPluginError(msg, "picture")

        # look for identify tool
        try:
            self.identify_bin = config["identify_bin"]
        except KeyError:
            msg = "Location of the 'identify' executable not specified."
            raise ECMDSPluginError(msg, "picture")
        if not os.path.isfile(self.identify_bin):
            msg = "Could not find 'identify' executable '%s'." % (self.identify_bin,)
            raise ECMDSPluginError(msg, "picture")

        # temporary directory
        self.tmp_dir = config["tmp_dir"]

        # conversion dpi
        try:
            self.convert_dpi = config["convert_dpi"]
        except KeyError:
            self.convert_dpi = "100"

    def process(self, node, format):
        """Prepare @node for target @format."""

        if format == "latex":
            self.LaTeX_prepareImg(node)
        elif format.endswith("latex"):
            self.LaTeX_prepareImg(node, format="pdf")
        else:
            self.XHTML_prepareImg(node)

        return node

    def flush(self):
        # reset counter
        self.counter = 1
        self.imgmap = {}
        self.imgwidth = {}

    def LaTeX_prepareImg(self, node, format="eps"):
        # get image src path
        src = self.__imgSrc(node)
        dst = ""

        # check if we used this image before
        try:
            dst = self.imgmap[src][0]
        except KeyError:
            dst = "img%06d.%s" % (self.counter, format)
            self.counter += 1

            if not src.endswith(format):
                if src.endswith(".eps") and format == "pdf":
                    self.__eps2pdf(src, dst)
                else:
                    self.__convertImg(src, dst)
            else:
                shutil.copyfile(src, dst)

            self.imgmap[src] = [dst]

        # set src attribute to new file
        node.attrib["src"] = dst

    def XHTML_prepareImg(self, node):
        # get image src path
        src = self.__imgSrc(node)
        dst = ""

        width = node.attrib.get("screen-width", None)

        if width:
            width = re.match("[1-9][0-9]*", width).group()
        else:
            width = self.__identifyWidth(src)

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
            ext = src.strip().split(".")[-1]

            if ext.lower() in ["jpg", "gif", "png"]:
                dst = "img%06d.%s" % (self.counter, ext.lower())
                self.__convertImg(src, dst, width)
            else:
                dst = "img%06d.jpg" % (self.counter,)
                self.__convertImg(src, dst, width)

            self.imgwidth[dst] = width
            self.imgmap.setdefault(src, []).append(dst)
            self.counter += 1

        # set src attribute to new file
        node.attrib["src"] = dst

    # PRIVATE

    def __imgSrc(self, node):
        # location of image
        src = node.attrib.get("src", "")

        if not src:
            msg = "Emtpy or missing 'src' attribute in 'img' tag "
            msg += "on line '%d'." % node.sourceline
            raise ECMDSPluginError(msg, "picture")

        # if src is a relative path, prepend doc's location
        if src and not os.path.isabs(src):
            # get the root node
            tree = node.getroottree()

            baseURL = os.path.dirname(os.path.normpath(tree.docinfo.URL))
            src = os.path.join(baseURL, os.path.normpath(src))

        if not os.path.isfile(src):
            msg = "Could not find bitmap file at location '%s' " % (src,)
            msg += "as specified in 'img' tag on line '%d'." % node.sourceline
            raise ECMDSPluginError(msg, "picture")

        return src

    def __convertImg(self, src, dst, width=None):
        # build command line
        if width:
            cmd = [self.convert_bin, "-antialias", "-density", self.convert_dpi, "-scale", width + "x"]
        else:
            cmd = [self.convert_bin, "-antialias", "-density", self.convert_dpi]

        # remove alpha channel if not supported
        if not dst[-4:] in [".png", ".pdf", ".svg", ".eps"]:
            cmd += ["-alpha", "remove"]

        # add source and destination filenames
        cmd += [src, dst]

        with open(os.devnull, "wb") as devnull:
            proc = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
            rval = proc.wait()

        # test exit status
        if rval != 0:
            msg = "Could not convert graphics file '%s'." % src
            raise ECMDSPluginError(msg, "picture")

    def __eps2pdf(self, src, dst):

        # look for bounding box
        rexpr = re.compile(r"(^%%BoundingBox:)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)")

        infile = None
        outfile = None

        try:
            # open source file and temporary output
            infile = open(src, "r", encoding="utf-8")
            tmpfd, tmpname = tempfile.mkstemp(suffix=".eps", dir=self.tmp_dir)
            outfile = os.fdopen(tmpfd, "w", encoding="utf-8")

            # Look for bounding box and adjust
            done = False
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

            self.__convertImg(tmpname, dst)
        except IOError:
            msg = "Could not convert EPS file '%s'" % src
            raise ECMDSPluginError(msg, "picture")
        finally:
            try:
                infile.close()
            except Exception:
                pass
            try:
                outfile.close()
            except Exception:
                pass

    def __identifyWidth(self, src):
        cmd = [self.identify_bin, src]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            result = proc.stdout.read().decode("utf-8")

        # this is a bit of an interesting way to determine an error condition...
        if result.startswith("identify:"):
            msg = "Could not determine bitmap's dimensions:\n  '%s'." % (result,)
            raise ECMDSPluginError(msg, "picture")

        result = result.split()
        rexpr = re.compile("[0-9]+x[0-9]+")
        width = None

        for value in result:
            if rexpr.match(value):
                width = value.split("x")[0]
                break

        if not width:
            msg = "Could not determine bitmap's dimensions:\n  '%s'." % (src,)
            raise ECMDSPluginError(msg, "picture")

        return width
