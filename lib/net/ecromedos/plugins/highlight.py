# -*- coding: UTF-8 -*-
#
# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net
#

from lxml import etree
from net.ecromedos.error import ECMDSPluginError
from net.ecromedos.highlight.formatter import ECMLPygmentsFormatter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound as PygmentsClassNotFound

def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)
#end function

class Plugin():

    def __init__(self, config):
        pass
    #end function

    def process(self, node, format):
        """Prepare @node for target @format."""

        # does user want highlighting?
        if not node.attrib.get('syntax'):
            return node

        # fetch content and highlight
        highlighted = self.__highlight(etree.tostring(node, method="text",
            encoding="unicode"), node.attrib)

        # parse result into element
        newnode = etree.fromstring(highlighted)

        # copy node properties to new node
        for k, v in node.attrib.items():
            if not k in newnode.attrib:
                newnode.attrib[k] = v
            else:
                if k == "bgcolor":
                    newnode.attrib["bgcolor"] = v
                else:
                    # only bgcolor can be overridden
                    pass
                #end if
            #end if
        #end for

        # replace original node
        newnode.tail = node.tail
        node.getparent().replace(node, newnode)

        return newnode
    #end function

    def flush(self):
        pass
    #end function

    # PRIVATE

    def __highlight(self, string, options):
        """Call syntax highlighter."""

        # output line numbers?
        try:
            self.__startline = int(options["startline"])
            self.__haveLineNumbers = True
        except ValueError:
            msg = "Invalid start line '%s'." % (options["startline"],)
            raise ECMDSPluginError(msg, "highlight")
        except KeyError:
            self.__haveLineNumbers = False
            self.__startline = 1
        #end try

        # increment to add to each line
        try:
            self.__lineStepping = int(options["linestep"])
        except ValueError:
            msg = "Invalid line stepping '%s'." % (options["linestep"],)
            raise ECMDSPluginError(msg, "highlight")
        except KeyError:
            self.__lineStepping = 1
        #end try

        # style to use
        try:
            self.__style = get_style_by_name(options['colorscheme'])
        except PygmentsClassNotFound:
            msg = "No style by name '%s'" % options["colorscheme"]
            raise ECMDSPluginError(msg, "highlight")
        except KeyError:
            self.__style = get_style_by_name("default")
        #end try

        # get a lexer for given syntax
        try:
            lexer = get_lexer_by_name(options["syntax"])
        except PygmentsClassNotFound:
            msg = "No lexer class found for '%s'." % options["syntax"]
            raise ECMDSPluginError(msg, "highlight")
        #end try

        # do the actual highlighting
        formatter = ECMLPygmentsFormatter(
            emit_line_numbers=self.__haveLineNumbers,
            startline=self.__startline,
            line_step=self.__lineStepping,
            style=self.__style
        )

        return highlight(string, lexer, formatter)
    #end function

#end class
