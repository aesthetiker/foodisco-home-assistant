"""Load the integration's Home-Assistant-free modules (api, logic, const) without
executing the package __init__, which imports Home Assistant.

CI and any machine without Home Assistant installed can then run these tests.
"""

import pathlib
import sys
import types

_pkg_dir = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "foodisco"

for _name, _path in (
    ("custom_components", _pkg_dir.parent),
    ("custom_components.foodisco", _pkg_dir),
):
    _module = types.ModuleType(_name)
    _module.__path__ = [str(_path)]
    sys.modules[_name] = _module
