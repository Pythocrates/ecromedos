# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from importlib.util import LazyLoader, module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from ecromedos.error import ECMDSError
from ecromedos.helpers import progress


class ECMDSPreprocessor:
    def __init__(self, configuration, plugins_map):
        self._configuration = configuration
        self._plugins_map = plugins_map
        self._plugins = self._load_plugins()

    def _iter_plugin_paths(self):
        try:
            plugin_dir = Path(self._configuration["plugin_dir"])
        except KeyError:
            print("No plugins directory specified. Not loading plugins.", file=sys.stderr)
        else:
            try:
                for file_path in plugin_dir.iterdir():
                    abspath = file_path.absolute()
                    if abspath.is_file() and not abspath.is_symlink() and file_path.suffix == ".py":
                        yield file_path
            except IOError:
                raise ECMDSError(f"IO-error while scanning plugins directory {plugin_dir}.")

    def _load_plugins(self):
        """Import everything from the plugin directory."""

        plugins = {}
        for module_file_path in self._iter_plugin_paths():
            module_name = module_file_path.stem
            try:
                if (module_spec := spec_from_file_location(module_name, module_file_path)) and module_spec.loader:
                    module_spec.loader = LazyLoader(module_spec.loader)
                    module = module_from_spec(module_spec)
                    sys.modules[module_name] = module
                    module_spec.loader.exec_module(module)
                    # got'cha
                    plugins[module_name] = module.getInstance(self._configuration)
                else:
                    raise ECMDSError(f"Failed to load plugin {module_name}.")

            except AttributeError:
                print(f"Warning: {module_name} is not a plugin.", file=sys.stderr)
            except Exception as ex:
                print(f"Warning: could not load module {module_name}: {ex}", file=sys.stderr)

        return plugins

    @progress(description="Preprocessing document tree...", final_status="DONE")
    def prepareDocument(self, document, target_format):
        """Prepare document tree for transformation."""

        node = document.getroot()

        while node is not None:
            node = self._process_node(node, target_format)

            if node.tag == "copy" or node.attrib.get("final", "no") == "yes":
                is_final = True
            else:
                is_final = False

            if not is_final and node.text:
                node.text = self._process_node(node.text, target_format)

            if not is_final and len(node) != 0:
                node = node[0]
                continue

            while node is not None:
                if node.tail:
                    node.tail = self._process_node(node.tail, target_format)

                following_sibling = node.getnext()

                if following_sibling is not None:
                    node = following_sibling
                    break

                node = node.getparent()

        # call post-actions
        self._flush_plugins()

        return document

    def _process_node(self, node, format):
        """Check if there is a filter registered for node."""

        plugins = self._plugins_map.get("@text" if isinstance(node, str) else node.tag, [])

        # pass node through plugins
        for plugin_name in plugins:
            try:
                plugin = self._plugins[plugin_name]
            except KeyError:
                raise ECMDSError(f"No plugin named {plugin_name} registered.")
            else:
                try:
                    node = plugin.process(node, format)
                except Exception as ex:
                    raise ECMDSError(f"Plugin {plugin_name} caused an exception: {ex}")

        return node

    def _flush_plugins(self):
        """Call flush function of all registered plugins."""
        for plugin in self._plugins.values():
            plugin.flush()
