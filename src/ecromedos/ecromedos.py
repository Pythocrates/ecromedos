# PYTHON_ARGCOMPLETE_OK
# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from argparse import ArgumentError
import getopt
import os
import sys
import tempfile

from argcomplete import autocomplete
from ecromedos.argumentparser import ECMDSArgumentParser
from ecromedos.configreader import ECMDSConfigReader
from ecromedos.dtdresolver import ECMDSDTDResolver
from ecromedos.preprocessor import ECMDSPreprocessor

import ecromedos.templates as document_templates
from ecromedos.ecmlprocessor import ECMLProcessor
from ecromedos.error import ECMDSError


# exit values
ECMDS_ERR_INVOCATION = 1
ECMDS_ERR_PROCESSING = 2
ECMDS_ERR_UNKNOWN = 3


# FIXME: Delete this
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


def print_document_template(document_type):
    """Outputs a template for a new document of @document_type to stdout."""

    try:
        template = getattr(document_templates, document_type)
    except KeyError:
        raise ECMDSError(f"No template available for doctype {document_type}.")
    else:
        print(template)


def main():
    autocomplete(parser := ECMDSArgumentParser(exit_on_error=False))
    try:
        args = parser.parse_args()
    except ArgumentError as ae:
        print(f"ecromedos: {ae}", file=sys.stderr)
        sys.exit(ECMDS_ERR_INVOCATION)

    print(args)

    params = {}
    if args.draft:
        params["global.draft"] = "'yes'"
    if args.finedtp:
        params["global.lazydtp"] = "'no'"
    if not args.hyperref:
        params["global.hyperref"] = "'no'"
    if args.style:
        params["global.stylesheet"] = f"document('{args.style.absolute()}')"

    if args.new:
        print_document_template(args.new)
        sys.exit(0)

    elif not (args.source_file.exists() and args.source_file.is_file()):
        print(f"ecromedos: {args.source_file} doesn't exist or is not a file", file=sys.stderr)
        sys.exit(ECMDS_ERR_INVOCATION)

    else:
        try:
            with tempfile.TemporaryDirectory(prefix="ecmds-") as tmp_dir:
                # MAKE THE PROCESSOR USE THE TMPDIR CONTEXT
                # options["tmp_dir"] = tmp_dir

                # SET INSTALLATION PATH
                # options.setdefault("install_dir", ECMDS_INSTALL_DIR)

                configuration, plugins_map = ECMDSConfigReader().readConfig(
                    config_file_path=args.config,
                    target_format=args.format,
                    validation_enabled=args.validate,
                    tmp_dir=tmp_dir,
                )
                resolver = ECMDSDTDResolver(configuration=configuration)
                preprocessor = ECMDSPreprocessor(configuration=configuration, plugins_map=plugins_map)
                ECMLProcessor(
                    resolver=resolver,
                    preprocessor=preprocessor,
                    target_format=configuration["target_format"],
                    style_dir=configuration["style_dir"],
                ).process(
                    args.source_file, validation_enabled=configuration["validation_enabled"], xsl_parameters=params
                )
        except ECMDSError as e:
            sys.stderr.write(e.msg() + "\n")
            sys.exit(ECMDS_ERR_PROCESSING)
        except KeyboardInterrupt:
            sys.stdout.write("\n -> Caught SIGINT, terminating.\n")
