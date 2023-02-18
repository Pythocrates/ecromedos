# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

import imp
import os
import sys

from ecromedos.error import ECMDSError, ECMDSPluginError


def progress(description, status):
    def inner(func):
        def wrapper(*args, verbose=True, **kwargs):
            if verbose:
                print(f" * {description}{' ' * (40 - len(description))}", end="")
            result = func(*args, **kwargs)
            if verbose:
                print(status)

            return result

        return wrapper

    return inner


class ECMDSPreprocessor:
    def __init__(self, configuration, plugins_map):
        self._configuration = configuration
        self._plugins_map = plugins_map
        self.plugins = {}

    def loadPlugins(self):
        """Import everything from the plugin directory."""

        try:
            plugin_dir = self._configuration["plugin_dir"]
        except KeyError:
            msg = "No plugins directory specified. Not loading plugins."
            sys.stderr.write(msg)
            return

        def genList():
            filelist = []
            print(plugin_dir)
            for filename in os.listdir(plugin_dir):
                abspath = os.path.join(plugin_dir, filename)
                if os.path.isfile(abspath) and not os.path.islink(abspath):
                    if filename.endswith(".py"):
                        filelist.append(filename[:-3])
            return filelist

        try:
            plugins_list = genList()
        except IOError:
            msg = "IO-error while scanning plugins directory."
            raise ECMDSError(msg)

        self.plugins = {}
        for name in plugins_list:
            try:
                fp, path, desc = imp.find_module(name, [plugin_dir])
                try:
                    module = imp.load_module(name, fp, path, desc)
                finally:
                    if fp:
                        fp.close()
                # got'cha
                self.plugins[name] = module.getInstance(self._configuration)
            except AttributeError:
                msg = "Warning: '%s' is not a plugin." % (name,)
                sys.stderr.write(msg + "\n")
                continue
            except Exception as e:
                msg = "Warning: could not load module '%s': " % (name,)
                msg += str(e) + "\n"
                sys.stderr.write(msg + "\n")
                raise
                continue

    @progress(description="Preprocessing document tree...", status="DONE")
    def prepareDocument(self, document):
        """Prepare document tree for transformation."""

        target_format = self._configuration["target_format"]
        node = document.getroot()

        while node is not None:
            node = self.__processNode(node, target_format)

            if node.tag == "copy" or node.attrib.get("final", "no") == "yes":
                is_final = True
            else:
                is_final = False

            if not is_final and node.text:
                node.text = self.__processNode(node.text, target_format)

            if not is_final and len(node) != 0:
                node = node[0]
                continue

            while node is not None:
                if node.tail:
                    node.tail = self.__processNode(node.tail, target_format)

                following_sibling = node.getnext()

                if following_sibling is not None:
                    node = following_sibling
                    break

                node = node.getparent()

        # call post-actions
        self.__flushPlugins()

        return document

    # PRIVATE

    def __processNode(self, node, format):
        """Check if there is a filter registered for node."""

        if isinstance(node, str):
            plist = self._plugins_map.get("@text", [])
        else:
            plist = self._plugins_map.get(node.tag, [])

        # pass node through plugins
        for pname in plist:
            try:
                plugin = self.plugins[pname]
            except KeyError:
                msg = "Warning: no plugin named '%s' registered." % (pname,)
                sys.stderr.write(msg + "\n")
            try:
                node = plugin.process(node, format)
            except ECMDSPluginError:
                raise  # caught in __main__
            except Exception as e:
                msg = "Plugin '%s' caused an exception: %s" % (pname, str(e))
                raise ECMDSError(msg)

        return node

    def __flushPlugins(self):
        """Call flush function of all registered plugins."""
        for pname, plugin in self.plugins.items():
            plugin.flush()
