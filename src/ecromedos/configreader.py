# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from importlib.resources import files
from pathlib import Path
import re
import sys

from ecromedos.error import ECMDSConfigError


class ECMDSConfigReader:
    def readConfig(self, options):
        """Read configuration files."""

        configuration = self.readConfigFile(options)
        plugin_map = self.readPluginsMap(configuration=configuration)

        return configuration, plugin_map

    def readConfigFile(self, options=None):
        """Read config file and merge with user supplied options."""
        options = options or {}
        cfile = None

        # path to config file
        if "config_file" in options:
            cfile = Path(options["config_file"]).absolute()
        else:
            cfile = Path(str(files("ecromedos").joinpath("defaults/ecmds.conf")))

        if not (cfile and cfile.exists()):
            msg = "Please specify the location of the config file."
            raise ECMDSConfigError(msg)

        # some hard-coded defaults
        config = {"target_format": "xhtml", "do_validate": True}

        # open file
        try:
            with open(cfile, "rt", encoding="utf-8") as fp:
                # parse the file
                lineno = 1
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = self._processConfigLine(line, lineno)
                        config[key] = value
                    lineno += 1
        except Exception:
            msg = "Error processing config file '%s'." % (cfile,)
            raise ECMDSConfigError(msg)

        # merge user supplied parameters
        for key, value in list(options.items()):
            config[key] = value

        # expand variables
        config = self._replaceVariables(config)

        # init lib path
        self._initLibPath(configuration=config)

        return config

    def readPluginsMap(self, configuration):
        """Read plugins map."""

        if not configuration:
            configuration = self.readConfigFile()

        cfile = None

        # path to config file
        if "plugins_map" in configuration:
            cfile = Path(configuration["plugins_map"])
        else:
            cfile = Path(str(files("ecromedos").joinpath("defaults/plugins.conf")))

        if not (cfile and cfile.exists()):
            sys.stderr.write("Warning: plugins map not found..\n")
            return False

        plugins_map = {}

        # open file
        try:
            with open(cfile, "rt", encoding="utf-8") as fp:
                lineno = 1
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = self._processPluginsMapLine(line, lineno)
                        plugins_map[key] = value
                    lineno += 1
        except Exception:
            raise ECMDSConfigError(f"Error processing plugins map file {cfile}.")

        return plugins_map

    # PRIVATE

    def _processConfigLine(self, line, lineno):
        """Extract key, value from line."""

        try:
            key, value = [entry.strip() for entry in line.split("=", 1)]
        except Exception:
            msg = "Formatting error in config file on line %d" % (lineno,)
            raise ECMDSConfigError(msg)

        return key, value

    def _processPluginsMapLine(self, line, lineno):
        """extract node name and plugins list from line."""

        try:
            nname, plugins = line.split(":")
            nname = nname.strip()
            plugins = [p.strip() for p in plugins.split(",")]
        except Exception:
            msg = "Formatting error in plugins map on line %d" % (lineno,)
            raise ECMDSConfigError(msg)

        return nname, plugins

    def _replaceVariables(self, config):
        """Replace variables in config file definitions."""

        # if there is nothing, do nothing
        if not config:
            return config

        # create rexpr $param1|param2|...
        expr = "|".join([r"\$" + re.escape(key) for key in list(config.keys())])
        rexpr = re.compile(expr)

        def sub(match):
            return config[match.group()[1:]]

        while True:
            # continue until there are no more substitutions
            subst_performed = False

            for key, value in list(config.items()):
                if type(value) == str:
                    config[key] = rexpr.sub(sub, value)
                    if value != config[key]:
                        subst_performed = True

            if not subst_performed:
                break

        return config

    def _initLibPath(self, configuration):
        """Initialize library path."""

        try:
            lib_dir = configuration["lib_dir"]
        except KeyError:
            return

        if lib_dir not in sys.path:
            sys.path.insert(1, lib_dir)
