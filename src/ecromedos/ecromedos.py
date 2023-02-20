# PYTHON_ARGCOMPLETE_OK
# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from argparse import ArgumentError
from enum import IntEnum, auto
from pathlib import Path
import sys
import tempfile

from argcomplete import autocomplete

from ecromedos.argumentparser import ECMDSArgumentParser
from ecromedos.configreader import ECMDSConfigReader
from ecromedos.dtdresolver import ECMDSDTDResolver
from ecromedos.ecmlprocessor import ECMLProcessor
from ecromedos.error import ECMDSError
from ecromedos.helpers import print_document_template
from ecromedos.preprocessor import ECMDSPreprocessor


# exit values
class ExitValue(IntEnum):
    ECMDS_ERR_INVOCATION = 1
    ECMDS_ERR_PROCESSING = auto()
    ECMDS_ERR_UNKNOWN = auto()


def main():
    autocomplete(parser := ECMDSArgumentParser(exit_on_error=False))
    try:
        args = parser.parse_args()
    except ArgumentError as ae:
        print(f"ecromedos: {ae}", file=sys.stderr)
        sys.exit(ExitValue.ECMDS_ERR_INVOCATION)

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
        sys.exit(ExitValue.ECMDS_ERR_INVOCATION)

    else:
        try:
            with tempfile.TemporaryDirectory(prefix="ecmds-") as tmp_dir:
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
                    style_dir=Path(configuration["style_dir"]),
                ).process(
                    args.source_file, validation_enabled=configuration["validation_enabled"], xsl_parameters=params
                )
        except ECMDSError as e:
            print(e.msg(), file=sys.stderr)
            sys.exit(ExitValue.ECMDS_ERR_PROCESSING)
        except KeyboardInterrupt:
            print("\n -> Caught SIGINT, terminating.", file=sys.stderr)
