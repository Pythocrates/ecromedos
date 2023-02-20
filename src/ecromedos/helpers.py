import shutil
import subprocess

from ecromedos.error import ECMDSError, ECMDSPluginError
from ecromedos import templates


class ExternalTool:
    """This class wraps an external executable and its execution."""

    def __init__(self, name, *default_args):
        try:
            self._executable_string = shutil.which(name)
        except TypeError:
            raise ECMDSPluginError(f"The {name} executable was not found.", "picture")
        else:
            self._default_args = default_args

    def __call__(self, *args, cwd=None):
        command = [self._executable_string, *self._default_args, *args]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd) as proc:
            result = proc.stdout.read().decode("utf-8")

        if proc.returncode:
            raise ECMDSPluginError(f"Failed to execute command {' '.join(str(c) for c in command)}.", "picture")
        else:
            return result


def print_document_template(document_type):
    """Outputs a template for a new document of @document_type to stdout."""

    try:
        template = getattr(templates, document_type)
    except KeyError:
        raise ECMDSError(f"No template available for doctype {document_type}.")
    else:
        print(template)


def progress(description, final_status):
    def inner(func):
        def wrapper(*args, verbose=True, **kwargs):
            if verbose:
                print(f" * {description}{' ' * (40 - len(description))}", end="")
            result = func(*args, **kwargs)
            if verbose:
                print(final_status)

            return result

        return wrapper

    return inner
