# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import getopt
import os
import sys
import tempfile
from importlib.resources import as_file, files

# make ecromedos relocatable
ECMDS_INSTALL_DIR = str(files("ecromedos"))

import ecromedos.templates as document_templates
from ecromedos.ecmlprocessor import ECMLProcessor
from ecromedos.error import ECMDSError, ECMDSPluginError
from ecromedos.version import VERSION

# exit values
ECMDS_ERR_INVOCATION = 1
ECMDS_ERR_PROCESSING = 2
ECMDS_ERR_UNKNOWN = 3


def printVersion():
    """Display version information."""

    print("ecromedos Document Processor, version %s" % VERSION)
    print("Copyright (C) 2005-2016, Tobias Koch <tobias@tobijk.de>                      ")


def printUsage():
    """Display usage information."""

    print("                                                                             ")
    print("Usage: ecromedos [OPTIONS] <sourcefile>                                      ")
    print("                                                                             ")
    print("Options:                                                                     ")
    print("                                                                             ")
    print(" --help, -h            Display this help text and exit.                      ")
    print(" --basedir, -b <dir>   Use an alternative base directory from where to look  ")
    print("                       up the transformation rules.                          ")
    print(" --config, -c <file>   Use an alternative configuration file.                ")
    print(" --format, -f <format> Generate the specified output format                  ")
    print("                       (xhtml, latex, pdflatex or xelatex).                  ")
    print(" --new, -n <doctype>   Start a new document of given doctype                 ")
    print("                       (article, book or report).                            ")
    print(" --style, -s <file>    Use an alternative style definition file.             ")
    print(" --version, -v         Print version information and exit.                   ")
    print("                                                                             ")
    print(" --draft               Don't generate glossary or keyword indexes, which can ")
    print("                       save substantial amounts of time.                     ")
    print(" --finedtp             Activate pedantic typesetting, this can result in     ")
    print("                       overful horizontal boxes.                             ")
    print(" --nohyperref          Disable active links in PDF output.                   ")
    print(" --novalid             Skip validation of the document.                      ")


def parseCmdLine():
    """Parse and extract arguments of command line options."""

    options = {}

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hvn:f:s:b:c:",
            [
                "help",
                "basedir=",
                "config=",
                "format=",
                "new=",
                "style=",
                "draft",
                "finedtp",
                "nohyperref",
                "novalid",
                "version",
            ],
        )
    except getopt.GetoptError as e:
        msg = "Error while parsing command line: %s\n" % e.msg
        msg += "Type 'ecromedos --help' for more information."
        raise ECMDSError(msg)

    params = options.setdefault("xsl_params", {})

    for o, v in opts:
        if o == "--draft":
            params["global.draft"] = "'yes'"
        elif o == "--finedtp":
            params["global.lazydtp"] = "'no'"
        elif o in ["--help", "-h"]:
            printVersion()
            printUsage()
            sys.exit(0)
        elif o == "--nohyperref":
            params["global.hyperref"] = "'no'"
        elif o == "--novalid":
            options["do_validate"] = False
        elif o in ["--basedir", "-b"]:
            options["style_dir"] = v
        elif o in ["--config", "-c"]:
            options["config_file"] = v
        elif o in ["--format", "-f"]:
            options["target_format"] = v.lower()
        elif o in ["--new", "-n"]:
            startDoc(v)
            sys.exit(0)
        elif o in ["--style", "-s"]:
            if not os.path.isfile(v):
                msg = "Style definition file '%s' not found." % v
                raise ECMDSError(msg)
            else:
                v = os.path.abspath(v)
            params["global.stylesheet"] = "document('%s')" % v
        elif o in ["--version", "-v"]:
            printVersion()
            sys.exit(0)
        else:
            msg = "Unrecognized option '%s'.\n" % (o,)
            msg += "Type 'ecromedos --help' for more information."
            raise ECMDSError(msg)

    return options, args


def startDoc(doctype):
    """Outputs a template for a new document of "doctype" to stdout."""

    if not hasattr(document_templates, doctype):
        msg = "No template available for doctype '" + doctype + "'."
        raise ECMDSError(msg)
    else:
        template = document_templates.__dict__[doctype]

    sys.stdout.write(template)
    sys.stdout.flush()


def main():
    try:
        # SETUP
        try:
            options, files = parseCmdLine()
            if len(files) < 1:
                msg = "ecromedos: no source file specified"
                raise ECMDSError(msg)
            if not os.path.isfile(files[0]):
                msg = "ecromedos: '%s' doesn't exist or is not a file" % files[0]
                raise ECMDSError(msg)
        except ECMDSError as e:
            sys.stderr.write(e.msg() + "\n")
            sys.exit(ECMDS_ERR_INVOCATION)

        # TRANSFORMATION
        try:
            with tempfile.TemporaryDirectory(prefix="ecmds-") as tmp_dir:
                # MAKE THE PROCESSOR USE THE TMPDIR CONTEXT
                options["tmp_dir"] = tmp_dir

                # SET INSTALLATION PATH
                options.setdefault("install_dir", ECMDS_INSTALL_DIR)

                # DO DOCUMENT TRANSFORMATION
                ECMLProcessor(options).process(files[0])
        except ECMDSError as e:
            sys.stderr.write(e.msg() + "\n")
            sys.exit(ECMDS_ERR_PROCESSING)
    except KeyboardInterrupt:
        sys.stdout.write("\n -> Caught SIGINT, terminating.\n")
