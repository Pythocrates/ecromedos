# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net

from importlib.resources import files
from pathlib import Path
import re
import sys

from ecromedos.argumentparser import ECMDS_INSTALL_DIR, GeneratorType
from ecromedos.error import ECMDSConfigError


class ECMDSConfigReader:
    def readConfig(self, config_file_path, target_format, validation_enabled, tmp_dir):
        """Read configuration files."""

        configuration = self._read_configuration_file(config_file_path, target_format, validation_enabled, tmp_dir)
        plugin_map = self._read_plugins_map(configuration=configuration)
        self._initialize_library_path(configuration=configuration)

        return configuration, plugin_map

    @classmethod
    def _read_configuration_file(cls, config_file_path, target_format, validation_enabled, tmp_dir):
        """Read config file and merge with user supplied options."""
        if not config_file_path.exists():
            raise ECMDSConfigError(f"Failed to find the configuration file {config_file_path}.")

        configuration = {
            "tmp_dir": tmp_dir,
            "target_format": GeneratorType.XHTML,
            "validation_enabled": True,
            "install_dir": ECMDS_INSTALL_DIR,
        }

        try:
            with open(config_file_path, "rt", encoding="utf-8") as fp:
                for lineno, line in enumerate(fp, start=1):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = [entry.strip() for entry in line.split("=", 1)]
                        except TypeError:
                            raise ECMDSConfigError(f"Formatting error in config file on line {lineno}.")
                        else:
                            configuration[key] = value
        except Exception:
            raise ECMDSConfigError(f"Failed to process the configuration file {config_file_path}.")

        # Merge user-supplied parameters.
        if target_format is not None:
            configuration["target_format"] = target_format
        if validation_enabled is not None:
            configuration["validation_enabled"] = validation_enabled
        #    config[key] = value

        # Expand variables.
        return cls._replace_variables(configuration)

    @staticmethod
    def _read_plugins_map(configuration):
        """Read plugins map."""

        config_file_path = Path(str(files("ecromedos"))) / "defaults" / "plugins.conf"

        if not config_file_path.exists():
            raise ECMDSConfigError(f"Failed to find the plugins file {config_file_path}.")

        plugins_map = {}

        try:
            with open(config_file_path, "rt", encoding="utf-8") as fp:
                for lineno, line in enumerate(fp, start=1):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            nname, plugins = line.split(":")
                            key = nname.strip()
                            values = [p.strip() for p in plugins.split(",")]
                        except Exception:
                            raise ECMDSConfigError(f"Formatting error in plugins map on line {lineno}.")
                        else:
                            plugins_map[key] = values
        except Exception:
            raise ECMDSConfigError(f"Error processing plugins map file {config_file_path}.")
        else:
            return plugins_map

    @staticmethod
    def _replace_variables(configuration):
        """Replace variables in config file definitions."""

        # create rexpr $param1|param2|...
        expr = "|".join([r"\$" + re.escape(key) for key in list(configuration.keys())])
        rexpr = re.compile(expr)

        def sub(match):
            return str(configuration[match.group()[1:]])

        substitution_performed = True
        while substitution_performed:
            substitution_performed = False

            for key, value in configuration.items():
                if isinstance(value, str):
                    configuration[key] = rexpr.sub(sub, value)
                    if value != configuration[key]:
                        substitution_performed = True

        return configuration

    @staticmethod
    def _initialize_library_path(configuration):
        if (lib_dir := configuration.get("lib_dir")) and lib_dir not in sys.path:
            sys.path.insert(1, lib_dir)
