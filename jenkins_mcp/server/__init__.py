from mcp.server.fastmcp import FastMCP
import importlib
import pkgutil
import sys

mcp = FastMCP('rhoai-jenkins')

# Dynamically import all modules in this package (except __init__)
print(f"Dynamically importing modules from {__name__}")
package = __name__
for _, modname, ispkg in pkgutil.iter_modules(__path__):
    print(f"Importing {modname} from {package}")
    if not ispkg and modname != '__init__':
        importlib.import_module(f"{package}.{modname}")
    