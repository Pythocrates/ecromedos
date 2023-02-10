# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import functools
import locale
import sys

import lxml.etree as etree


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    def __init__(self, config):
        self.index = {}
        self.counter = 0
        try:
            self.__draft = config["xsl_params"]["global.draft"]
        except KeyError:
            self.__draft = "'no'"

    def process(self, node, format):
        """Either saves a glossary entry or sorts and builds the glossary,
        depending on which node triggered the plugin."""

        # skip if in draft mode
        if self.__draft == "'yes'":
            return node

        if node.tag == "idxterm":
            node = self.__saveNode(node)
        elif node.tag == "make-index":
            node = self.__makeIndex(node)

        return node

    def flush(self):
        self.index = {}
        self.counter = 0

    # PRIVATE

    def __saveNode(self, node):
        """Substitutes a 'defterm' node with a label and stores a reference
        to the node for later when the index is to be built."""

        sortkey = node.attrib.get("sortkey", None)
        group = node.attrib.get("group", "default")

        item = None
        subitem = None
        subsubitem = None

        # read idxterm items
        for child in node.iterchildren():
            if child.tag == "item":
                item = child.text.strip()
            elif child.tag == "subitem":
                subitem = child.text.strip()
            elif child.tag == "subsubitem":
                subsubitem = child.text.strip()

        # create label
        label_id = "idx:item%06d" % self.counter

        # replace node itself with label node
        label_node = etree.Element("label", id=label_id)
        label_node.tail = node.tail
        node.getparent().replace(node, label_node)

        # at least 'item' must exist
        if item is not None:
            index = self.index.setdefault(group, [group, {}, [], None])

            for entry in [item, subitem, subsubitem, None]:
                if entry is None:
                    index[2].append(label_id)
                    index[3] = sortkey
                    break

                index = index[1].setdefault(entry, [entry, {}, [], None])

        self.counter += 1
        return label_node

    def __makeIndex(self, node):
        """Read configuration. Sort items. Build index. Build XML."""

        if not self.index:
            return node

        # build configuration
        config = self.__configuration(node)

        # set locale
        self.__setLocale(config["locale"], config["locale_encoding"], config["locale_variant"])

        # build DOM structures
        index = self.__buildIndex(node, config)

        # reset locale
        self.__resetLocale()

        return index

    def __configuration(self, node):
        """Read node attributes and build a dictionary holding
        configuration information for the collator"""

        # presets
        properties = {
            "columns": "2",
            "group": "default",
            "separator": ", ",
            "locale": "C",
            "locale_encoding": None,
            "locale_variant": None,
            "alphabet": "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z",
        }

        # read element attributes
        properties.update(dict(node.items()))

        # split locale into locale/encoding/variant
        if "@" in properties["locale"]:
            properties["locale"], properties["locale_variant"] = properties["locale"].split("@", 1)
        if "." in properties["locale"]:
            properties["locale"], properties["locale_encoding"] = properties["locale"].split(".", 1)

        # parse the alphabet
        alphabet = []
        for ch in [x.strip() for x in properties["alphabet"].split(",")]:
            if ch[0] == "[" and ch[-1] == "]":
                properties["symbols"] = ch[1:-1].strip()
            else:
                alphabet.append(ch)
        properties["alphabet"] = alphabet

        return properties

    def __setLocale(self, collate="C", encoding=None, variant=None):
        """Sets the locale to the specified locale, encoding and locale
        variant."""

        success = False

        for e in [encoding, "UTF-8"]:
            if success:
                break
            for v in [variant, ""]:
                localestring = ".".join([x for x in [collate, e] if x])
                localestring = "@".join([x for x in [localestring, v] if x])
                try:
                    locale.setlocale(locale.LC_COLLATE, localestring)
                    success = True
                    break
                except locale.Error:
                    pass

        if not success:
            msg = "Warning: cannot set locale '%s'." % collate
            sys.stderr.write(msg)

    def __resetLocale(self):
        """Resets LC_COLLATE to its default."""
        locale.resetlocale(locale.LC_COLLATE)

    def __sortIndex(self, index, level="item", config=None):
        """Sort index terms."""

        # stop recursion
        if not index:
            return index

        # recursive sortkey evaluation
        itemlist = []
        for v in index.values():
            # set sortkey
            if not v[-1]:
                v[-1] = v[0]
            # recursion
            v[1] = self.__sortIndex(v[1], "sub" + level, config)
            itemlist.append(v)

        # insert alphabet
        if level == "item":
            for ch in config["alphabet"]:
                newnode = etree.Element("idxsection", name=ch)
                itemlist.append(["idxsection", newnode, ch])

        # comparison function
        def compare(a, b):
            x1 = a[-1]
            x2 = b[-1]

            y1 = a[1]
            y2 = b[1]

            if isinstance(y1, etree._Element) != isinstance(y2, etree._Element):
                result = locale.strcoll(x1.lower(), x2.lower())
            else:
                result = locale.strcoll(a[-1], b[-1])

            if result != 0:
                return result
            elif isinstance(y1, etree._Element) and isinstance(y2, etree._Element):
                return 0
            elif isinstance(y1, etree._Element):
                return -1
            elif isinstance(y2, etree._Element):
                return +1
            else:
                return 0

        itemlist.sort(key=functools.cmp_to_key(compare))
        return itemlist

    def __buildIndexHelper(self, section, index, level, separator):
        """Build index recursively from nested lists structure."""

        # stop recursion
        if not index:
            return index

        for item in index:
            term = item[0]

            item_node = etree.Element(level)
            item_node.text = term

            i = 0
            references = item[2]
            num_ref = len(references)

            # build referrer node
            while i < num_ref:
                ref = references[i]

                # add single space
                if i == 0:
                    item_node.text += " "

                # add reference to list
                etree.SubElement(item_node, "idxref", idref=ref)

                # add separator (this should be configurable)
                if i < num_ref - 1:
                    if not item_node[-1].tail:
                        item_node[-1].tail = separator
                    else:
                        item_node[-1].tail += separator

                i += 1

            section.append(item_node)

            # recursion
            self.__buildIndexHelper(section, item[1], "sub" + level, separator)

    def __buildIndex(self, node, config):
        """Build XML DOM structure."""

        # detect group name
        group = node.attrib.get("group", "default")

        # load group
        try:
            index = self.index[group][1]
        except Exception:
            return node

        # sort index
        localestring, encoding = locale.getlocale(locale.LC_COLLATE)
        index = self.__sortIndex(index, level="item", config=config)

        # build base node
        for prop_name in ["columns", "title", "tocentry"]:
            try:
                node.attrib[prop_name] = config[prop_name]
            except KeyError:
                pass

        # start building index...
        section = etree.Element("idxsection")
        try:
            section.attrib["name"] = config["symbols"]
        except KeyError:
            pass

        separator = config["separator"]

        for item in index:
            if isinstance(item[1], etree._Element):
                node.append(section)
                section = item[1]
            else:
                term = item[0]
                item_node = etree.Element("item")
                item_node.text = term

                i = 0
                references = item[2]
                num_ref = len(references)

                # build referrer node
                while i < num_ref:
                    ref = references[i]

                    # add single space
                    if i == 0:
                        item_node.text += " "

                    # add reference to list
                    etree.SubElement(item_node, "idxref", idref=ref)

                    # add separator (this should be configurable)
                    if i < num_ref - 1:
                        if not item_node[-1].tail:
                            item_node[-1].tail = separator
                        else:
                            item_node[-1].tail += separator

                    i += 1

                section.append(item_node)

                # recursion
                self.__buildIndexHelper(section, item[1], "subitem", separator)

        node.append(section)
        node.tag = "index"

        return node
