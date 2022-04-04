from maya import cmds
from maya import mel

alembicBaseCommand = 'AbcExport2 -j "-frameRange <startFrame> <endFrame> -attr assetName -attr assetInstance -attr mayaReferencePath -attr assetType -attr animatedAsset -uvWrite -worldSpace -writeUVSets -dataFormat ogawa -root <objectList> -file <filePath>"'

def export_setdress():
    """Export Selection
    """
    export_filename = cmds.fileDialog2(fileMode=0, caption="Export Set Dress", fileFilter="ABC Files (*.abc)")
    export_filename = export_filename[0]

    if(cmds.ls(sl=True) == []):
        raise RuntimeError("Nothing selected, please select groups.")
    
    sdt = SetDressTools()
    sdt.export(1, 1, export_filename)

class SetDressTools:

    def __init__(self):

        self.transformsToExport = []
        self.srtGlobals         = []
        self.srtLocals          = []
        self.startFrame         = 0
        self.endFrame           = 0
        self.alembicFileName    = ""
        self.userAttrs          = []

    def getAssetNameAndInstance(self, objLongName):
        """ Use the namespace to extract the asset name and instance.

        Args:

            objLongName (str): The long name of the object.

        Returns:
            tuple(str,str) : The asset name and instance.

        """
        splitHierarchy  = objLongName.split("|")
        splitObjectName = splitHierarchy[1].split(":")
        splitNameSpace  = splitObjectName[0].split("_")

        assetName       = "_".join(splitNameSpace[0:-1])
        assetInstance   = int(splitNameSpace[-1])

        return assetName, assetInstance

    def getAssetReferencePath(self, objLongName):
        """ Get the asset reference path.

        Args:

            objLongName (str) : The long name of the object.
        """
        if(cmds.referenceQuery(objLongName, isNodeReferenced=True)):
            reference   = cmds.referenceQuery(objLongName, referenceNode=True)
            filePath    = cmds.referenceQuery(reference, filename=True)
            if(filePath.find("{") != -1):
                return filePath.split("{")[0]
            return filePath
        return None

    def addIntAttribute(self, obj, name, value):
        """ Add or update a integer attribute to an object.
        
        Args:
            obj (str) : The long name of the object.
            name (str) : The name of the attribute.
            value (str) : The value of the attribute.
        """
        attributePath   = "%s.%s" % (obj, name)

        # Check if the attribute already exist.
        if(cmds.attributeQuery(name, node=obj, exists=True) == False):
            # Need to select the object to use the addAttr.... LOL !!!!
            cmds.select(obj)
            # Add the attribute.
            cmds.addAttr(longName=name , at='long')

        cmds.setAttr(attributePath, value)

    def addStringAttribute(self, obj, name, value):
        """ Add or update a string attribute to an object.

        Args:
            obj (str) : The long name of the object.
            name (str) : The name of the attribute.
            value (str) : The value of the attribute.
        """
        attributePath   = "%s.%s" % (obj, name)

        # Check if the attribute already exist.
        if(cmds.attributeQuery(name, node=obj, exists=True) == False):
            # Need to select the object to use the addAttr.... LOL !!!!
            cmds.select(obj)
            # Add the attribute.
            cmds.addAttr(longName=name , dt='string')
        cmds.setAttr(attributePath, value, type='string')


    def addReferenceAssetAttributes(self):
        """ Add or update the referenced asset attribute to the shape of the transform object.
            The export of the attribute work only on the shape object.
        """
        for transform in self.srtLocals:
            # Get the transform shape.
            transformShape = cmds.listRelatives(transform, shapes=True)[0]
            # Extract the asset name and instance form the namespace.
            assetName, assetInstance = self.getAssetNameAndInstance(transform)

            # Add the asset name.
            self.addStringAttribute(transformShape, 'assetName', assetName)
            # Add the asset instance.
            self.addIntAttribute(transformShape, 'assetInstance', assetInstance)
            # Add the reference path.
            mayaScenePath = self.getAssetReferencePath(transformShape)
            if(mayaScenePath is not None):
                self.addStringAttribute(transformShape, 'mayaReferencePath', mayaScenePath)
            
            # Add asset type.
            if(mayaScenePath is not None):
                assetType = mayaScenePath.split("/")[4]
            else:
                assetType = "Prop"
            
            self.addStringAttribute(transformShape, 'assetType', assetType)

            if(len(self.getControllers(transform)) > 2):
                animatedAsset = True
            else:
                animatedAsset = False

            self.addIntAttribute(transformShape, 'animatedAsset', int(animatedAsset))

            # ----[DEBUG]-----
            # print(transform)
            # print(assetName)
            # print(assetInstance)
            # print(assetType)
            # print(int(animatedAsset))
            # ----[DEBUG]-----

    def getControllers(self, obj):
        """Get the list of controllers for a given object.

        Args:
            obj (str): Name of the object.

        Returns:
            list: Controllers
        """
        controllers = [
            obj for obj in cmds.listRelatives(obj, allDescendents=True) if not "Shape" in obj
        ]

        return [
            obj for obj in controllers if not "GRP" in obj
        ]

    def checkTransform(self, obj):
        """ Check if the object local position has moved.

        Args:

            obj (str): The object to test.
        
        Returns:

            bool : True if moved, otherwise False.
        """

        # Get the object local position.
        posX = cmds.getAttr("%s.translateX" % obj)
        posY = cmds.getAttr("%s.translateY" % obj)
        posZ = cmds.getAttr("%s.translateZ" % obj)
        # Check if position axis are not equal to 0.0.
        if(posX != 0.0 or posY != 0.0 or posZ != 0.0):
            return True
        
        return False

    def exportTransformsABC(self):
        """ Export the transform list to alembic file.
        """
        # print(len(cmds.ls(sl=True)))
        # print(len(self.srtGlobals))

        alembicCmd  = alembicBaseCommand.replace('<startFrame>', str(self.startFrame))
        alembicCmd  = alembicCmd.replace('<endFrame>', str(self.endFrame))
        alembicCmd  = alembicCmd.replace('<objectList>', " -root ".join(self.srtGlobals))
        alembicCmd  = alembicCmd.replace('<filePath>', self.alembicFileName)

        # print(alembicCmd)

        return_message = mel.eval(alembicCmd)
        # print("ABCExport2 return:")
        # print(return_message)
    
    def exportAnimatedMeshes(self):
        for elem in self.srtGlobals:
            print(elem)

    def export(self, startFrame, endFrame, filePath):
        """ Export the pivot of the selected references in an alembic file.
        """

        self.startFrame         = startFrame
        self.endFrame           = endFrame
        self.alembicFileName    = filePath

        # Loop over the selected reference to export.
        for ref in cmds.ls(sl=True):
            # Get the nameSpace.
            splitName = ref.split(":")
            nameSpace = splitName[0]
            # Get the srt global and srt local.
            srtGlobal 	= "%s:main_SRT_global" % nameSpace
            srtLocal	= "%s:main_SRT_local" % nameSpace
            # Check if the srt global and local exist.
            if(cmds.objExists(srtGlobal) and cmds.objExists(srtLocal)):
                # Check if the srt global has moved.
                # print("SRT GLOBAL")
                srtGlobal = cmds.ls(srtGlobal, long=True)[0]
                self.srtGlobals.append(srtGlobal)
                srtLocal = cmds.ls(srtLocal, long=True)[0]
                self.srtLocals.append(srtLocal)    
            else:
                # print("NO SRT")
                continue
        
        self.addReferenceAssetAttributes()

        # Export the alembic file if the export list is not empty.
        if(len(self.srtGlobals) > 0):
            self.exportTransformsABC()

        # Select the transform exported.
        cmds.select(self.srtGlobals)


# sdt = SetDressTools()
# sdt.export(1,1,"C:/Users/gbaratte/Documents/DEV/temp/testSetDressAlembic6.abc")
