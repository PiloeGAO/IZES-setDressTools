from maya import utils
from maya import cmds

def init_setDressTools_Menu():
    print("Loading setDressTools Menu.")

    # Add a menu to the main window.
    cmds.menu("setDressToolsMenu", label="SetDressTools", parent="MayaWindow", tearOff=False)

    # Add browser to menu.
    cmds.menuItem("exportSetDress", label="Export Selection", command="from setDressTools import export_setdress; export_setdress()", parent="setDressToolsMenu")

# Delay execution on UI startup
utils.executeDeferred(init_setDressTools_Menu)