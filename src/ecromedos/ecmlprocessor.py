# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from pathlib import Path

import lxml.etree as etree

from ecromedos.configreader import ECMDSConfigReader
from ecromedos.dtdresolver import ECMDSDTDResolver
from ecromedos.error import ECMDSError
from ecromedos.preprocessor import ECMDSPreprocessor, progress


class ECMLProcessor(ECMDSConfigReader, ECMDSDTDResolver, ECMDSPreprocessor):
    def __init__(self, options=None):
        ECMDSConfigReader.__init__(self)
        ECMDSDTDResolver.__init__(self)
        ECMDSPreprocessor.__init__(self)

        self.readConfig(options or {})
        self.loadPlugins()
        self.loadStylesheet()

    @progress(description="Reading document...", status="DONE")
    def loadXMLDocument(self, filename):
        """Try to load XML document from @filename."""

        try:
            # create parser
            parser = etree.XMLParser(
                load_dtd=True, no_network=True, strip_cdata=True, remove_comments=True, resolve_entities=True
            )

            # register custom resolver
            parser.resolvers.add(self)

            # parse the document
            tree = etree.parse(filename, parser=parser)
        except Exception as e:
            raise ECMDSError(str(e))

        # return document tree
        return tree

    def loadStylesheet(self):
        """Load matching stylesheet for desired output format."""

        target_format = self.config["target_format"]

        try:
            style_dir = Path(self.config["style_dir"])
        except KeyError:
            msg = "Please specify the location of the stylesheets."
            raise ECMDSError(msg)

        file_path = style_dir / target_format / "ecmds.xsl"
        try:
            tree = self.loadXMLDocument(file_path, verbose=False)
        except ECMDSError as e:
            raise ECMDSError(f"Could not load stylesheet:\n {e.msg()}")

        try:
            self.stylesheet = etree.XSLT(tree)
        except Exception as e:
            raise ECMDSError(str(e))

        return self.stylesheet

    @progress(description="Validating document...", status="VALID")
    def validateDocument(self, document):
        """Validate the given document."""

        try:
            style_dir = Path(self.config["style_dir"])
        except KeyError:
            msg = "Please specify the location of the stylesheets."
            raise ECMDSError(msg)

        # load the DTD
        dtd_file_path = style_dir / "DTD" / "ecromedos.dtd"
        dtd = etree.DTD(dtd_file_path)

        # validate the document
        result = dtd.validate(document)

        if not result:
            raise ECMDSError(dtd.error_log.last_error)

        return result

    @progress(description="Transforming document...", status="DONE")
    def applyStylesheet(self, document):
        """Apply stylesheet to document."""

        params = None
        try:
            params = self.config["xsl_params"]
        except KeyError:
            pass

        try:
            result = self.stylesheet(document, **params)
        except Exception as e:
            msg = "Error transforming document:\n %s." % (str(e),)
            raise ECMDSError(msg)

        return result

    def process(self, filename, verbose=True):
        """Convert the document stored under filename."""

        document = self.loadXMLDocument(filename)

        if self.config["do_validate"]:
            self.validateDocument(document)

        self.prepareDocument(document)

        self.applyStylesheet(document=document, verbose=verbose)
