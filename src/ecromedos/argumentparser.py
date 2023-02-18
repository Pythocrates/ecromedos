from argparse import ArgumentParser, BooleanOptionalAction, RawTextHelpFormatter
from enum import StrEnum, auto
from importlib.resources import files
from pathlib import Path

from ecromedos.version import VERSION

# make ecromedos relocatable
ECMDS_INSTALL_DIR = Path(str(files("ecromedos")))


class DocumentType(StrEnum):
    ARTICLE = auto()
    BOOK = auto()
    REPORT = auto()


class GeneratorType(StrEnum):
    XHTML = auto()
    LATEX = auto()
    PDFLATEX = auto()
    XELATEX = auto()


class ECMDSArgumentParser(ArgumentParser):
    _VERSION_STRING = f"%(prog)s, version {VERSION}\nCopyright (C) 2005-2016, Tobias Koch <tobias@tobijk.de>"

    def __init__(self, *args, **kwargs):
        super().__init__(formatter_class=RawTextHelpFormatter, prog="ecromedos Document Processor", *args, **kwargs)
        self.add_argument(
            "source_file", type=Path, metavar="source-file", help="Source file for the document generation."
        )
        self.add_argument("-v", "--version", action="version", version=self._VERSION_STRING)
        self.add_argument(
            "-b",
            "--basedir",
            type=Path,
            help="Use an alternative base directory from where to look up the transformation rules.",
        )
        self.add_argument(
            "-c",
            "--config",
            type=Path,
            default=ECMDS_INSTALL_DIR / "defaults" / "ecmds.conf",
            help="Use an alternative configuration file.",
        )
        self.add_argument(
            "-f",
            "--format",
            type=GeneratorType,
            choices=GeneratorType,
            help="Generate the specified output format.",
        )
        self.add_argument(
            "-n",
            "--new",
            type=DocumentType,
            choices=DocumentType,
            help="Start a new document of given doctype.",
        )
        self.add_argument("-s", "--style", type=Path, help="Use an alternative style definition file.")
        self.add_argument(
            "--draft",
            action="store_true",
            help="Don't generate glossary or keyword indexes, which can save a substantial amounts of time.",
        )
        self.add_argument(
            "--finedtp",
            action="store_true",
            help="Activate pedantic typesetting, this can result in overfull horizontal boxes.",
        )
        self.add_argument(
            "--hyperref", action=BooleanOptionalAction, default=True, help="Enable/disable active links in PDF output."
        )
        self.add_argument("--validate", action=BooleanOptionalAction, help="Enable/disable validation of the document.")
