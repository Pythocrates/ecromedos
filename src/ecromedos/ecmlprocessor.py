# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from pathlib import Path

import lxml.etree as etree

from ecromedos.error import ECMDSError
from ecromedos.preprocessor import progress


class ECMLProcessor:
    def __init__(self, resolver, preprocessor, target_format, style_dir):
        self._resolver = resolver
        self._preprocessor = preprocessor
        self._preprocessor.loadPlugins()
        self._stylesheet = self._load_stylesheet(target_format=target_format, style_dir=style_dir)
        self._style_dir = style_dir

    @progress(description="Reading document...", status="DONE")
    def _load_xml_document(self, filename):
        """Try to load XML document from @filename."""

        try:
            parser = etree.XMLParser(
                load_dtd=True, no_network=True, strip_cdata=True, remove_comments=True, resolve_entities=True
            )

            parser.resolvers.add(self._resolver)

            return etree.parse(filename, parser=parser)
        except Exception as e:
            raise ECMDSError(str(e))

    def _load_stylesheet(self, target_format, style_dir):
        """Load matching stylesheet for desired output format."""

        file_path = Path(style_dir) / target_format / "ecmds.xsl"
        try:
            tree = self._load_xml_document(file_path, verbose=False)
        except ECMDSError as e:
            raise ECMDSError(f"Could not load stylesheet:\n {e.msg()}")

        try:
            return etree.XSLT(tree)
        except Exception as e:
            raise ECMDSError(str(e))

    @progress(description="Validating document...", status="VALID")
    def _validate_document(self, document):
        """Validate the given document."""

        dtd_file_path = Path(self._style_dir) / "DTD" / "ecromedos.dtd"
        dtd = etree.DTD(dtd_file_path)

        result = dtd.validate(document)

        if not result:
            raise ECMDSError(dtd.error_log.last_error)
        else:
            return result

    @progress(description="Transforming document...", status="DONE")
    def applyStylesheet(self, document, xsl_parameters):
        """Apply stylesheet to document."""

        try:
            return self._stylesheet(document, **xsl_parameters)
        except Exception as e:
            raise ECMDSError(f"Error transforming document:\n {e}.")

    def process(self, filename, validation_enabled, xsl_parameters, verbose=True):
        """Convert the document stored under filename."""

        document = self._load_xml_document(filename)

        if validation_enabled:
            self._validate_document(document)

        self._preprocessor.prepareDocument(document)

        self.applyStylesheet(document=document, xsl_parameters=xsl_parameters, verbose=verbose)
