# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import lxml.etree as etree

from ecromedos.error import ECMDSError
from ecromedos.helpers import progress


class ECMLProcessor:
    def __init__(self, resolver, preprocessor, target_format, style_dir):
        self._resolver = resolver
        self._preprocessor = preprocessor
        self._style_dir = style_dir
        self._target_format = target_format
        self._stylesheet = self._load_stylesheet()

    @progress(description="Reading document...", final_status="DONE")
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

    def _load_stylesheet(self):
        """Load matching stylesheet for desired output format."""

        file_path = self._style_dir / self._target_format / "ecmds.xsl"
        try:
            tree = self._load_xml_document(file_path, verbose=False)
        except ECMDSError as e:
            raise ECMDSError(f"Could not load stylesheet:\n {e.msg()}")

        try:
            return etree.XSLT(tree)
        except Exception as e:
            raise ECMDSError(str(e))

    @progress(description="Validating document...", final_status="VALID")
    def _validate_document(self, document):
        """Validate the given document."""

        dtd = etree.DTD(self._style_dir / "DTD" / "ecromedos.dtd")
        result = dtd.validate(document)

        if not result:
            raise ECMDSError(dtd.error_log.last_error)
        else:
            return result

    @progress(description="Transforming document...", final_status="DONE")
    def _apply_stylesheet(self, document, xsl_parameters):
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

        self._preprocessor.prepareDocument(document, target_format=self._target_format)

        self._apply_stylesheet(document=document, xsl_parameters=xsl_parameters, verbose=verbose)
