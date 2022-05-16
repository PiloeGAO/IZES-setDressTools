import os
import json

import hou

class ImportSetDress:
    asset_folder_template = "<drive>:/shows/<project>/assets/<assetType>/<asset>/publishs/<step>"

    processing_nodes = [
        "IMPORT_SET_DRESS",
        "EXPORT_MTLX"
    ]

    def __init__(self) -> None:
        pass

    def build_ui(self, hou_node) -> None:
        """ Build the ui interface.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        # Unlock node
        hou_node.allowEditingOfContents()

        # Get the interface template group.
        ptg = hou_node.parmTemplateGroup()

        # Add a set dressing cache entry.
        set_dressing_cache = hou.StringParmTemplate(
            "setDressingCachePath",
            "Set Dress File",
            1,
            string_type=hou.stringParmType.FileReference,
            file_type=hou.stringParmType.FileReference,
            script_callback="hou.phm().data.import_set_dress_cache(kwargs['node'])",
            script_callback_language=hou.scriptLanguage.Python
        )

        # Add set dressing cache to template group.
        ptg.addParmTemplate(set_dressing_cache)

        # Add Export JSON Button.
        ptg.addParmTemplate(
            hou.ButtonParmTemplate(
                "exportShadersJSON",
                "Export Shaders as JSON",
                join_with_next=True,
                script_callback="hou.phm().data.export_shaders_as_json(kwargs['node'])",
                script_callback_language=hou.scriptLanguage.Python
            )
        )

        # Add Import JSON Button.
        ptg.addParmTemplate(
            hou.ButtonParmTemplate(
                "importShaderJSON",
                "Import Shaders as JSON",
                script_callback="hou.phm().data.import_json_shaders(kwargs['node'])",
                script_callback_language=hou.scriptLanguage.Python
            )
        )

        # Add Clear Assets Button.
        ptg.addParmTemplate(
            hou.ButtonParmTemplate(
                "clearAssets",
                "Clear Assets",
                script_callback="hou.phm().data.clear_assets(kwargs['node'])",
                script_callback_language=hou.scriptLanguage.Python
            )
        )

        # Add Export MTLX Button.
        ptg.addParmTemplate(
            hou.ButtonParmTemplate(
                "exportMTLX",
                "Export MTLX",
                script_callback="hou.phm().data.export_materialx(kwargs['node'])",
                script_callback_language=hou.scriptLanguage.Python
            )
        )

        # TODO: Add a function to display assets from a search bar.
        """
        # Add a folder to display the Assets.
        displayAssetFolder = hou.FolderParmTemplate(
            "displayAssets",
            "Assets",
            parm_templates=(
                hou.StringParmTemplate(
                    "name#",
                    "Name",
                    1
                ),
                hou.IntParmTemplate(
                    "instance#",
                    "Instance",
                    1,
                    min=1,
                    default_value=[1]
                ),
                hou.IntParmTemplate(
                    "version#",
                    "Version",
                    1,
                    min=1,
                    default_value=[1]
                ),
                hou.StringParmTemplate(
                    "path#",
                    "Path",
                    1
                ),
                hou.MenuParmTemplate(
                    "display#",
                    "Display",
                    [
                        "Full Geometry",
                        "Point Cloud",
                        "Bounding Box",
                        "Centroid",
                        "Hidden",
                    ]
                )
            ),
            folder_type=hou.folderType.MultiparmBlock
        )
        
        # Add folder to template group.
        ptg.addParmTemplate(displayAssetFolder)
        """

        # Update the node interface.
        hou_node.setParmTemplateGroup(ptg)

    #########
    # UTILS #
    #########
    def export_shaders_as_json(self, hou_node):
        """Write shader to disk.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        path_to_json = os.path.join(os.path.dirname(hou.hipFile.path()), "shaders.json")
        json_datas = json.dumps(self.get_materials_assignations(hou_node), indent = 4)

        with open(path_to_json, 'w') as output_file:
            output_file.write(json_datas)

    def import_json_shaders(self, hou_node):
        """Import and apply shaders from disk.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        path_to_json = os.path.join(os.path.dirname(hou.hipFile.path()), "shaders.json")
        if(not os.path.isfile(path_to_json)): raise RuntimeError("No JSON found on disk.")

        with open(path_to_json, 'r') as output_file:
            json_datas = json.load(output_file)
        
        self.update_materials(hou_node, json_datas)

    ########################
    # Processing Functions #
    ########################
    def import_set_dress_cache(self, hou_node):
        """This function load the list of assets from the Alembic File to the hidden list.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        shaders_assignations = self.get_materials_assignations(hou_node)
        if(len(shaders_assignations) > 0): self.clear_assets(hou_node)

        # Set the path to the alembic.
        hou_node.parm('cachePath').set(
            hou_node.parm('setDressingCachePath').evalAsString()
        )

        # Find all the informations from the attributes and store them in the root node.
        setDressNode    = hou_node.node('IMPORT_SET_DRESS').node('OUT')
        setDressGeo     = setDressNode.geometry()
        
        points          = setDressGeo.points()
        
        hou_node.parm("assets").set(len(points))
        
        for point in setDressGeo.points():
            pointID         = point.number()
            assetName       = point.stringAttribValue('assetName')
            assetInstance   = point.intAttribValue('assetInstance')
            assetType       = point.stringAttribValue('assetType')
            assetStep       = hou_node.parm("assetStep%i" % pointID).evalAsString()
            
            hou_node.parm("assetType%i" % pointID).set(assetType)
            hou_node.parm("assetName%i" % pointID).set(assetName)
            hou_node.parm("assetInstance%i" % pointID).set("%03d" % assetInstance)

            assetPublishPath = self.asset_folder_template.replace('<drive>', 'O')
            assetPublishPath = assetPublishPath.replace('<project>', 'IZES')
            assetPublishPath = assetPublishPath.replace('<assetType>', assetType)
            assetPublishPath = assetPublishPath.replace('<asset>', assetName)
            assetPublishPath = assetPublishPath.replace('<step>', assetStep)

            versions    = self.get_asset_versions(assetPublishPath)
            lastVersion = self.get_last_version(versions)
            
            hou_node.parm("assetVersion%i" % pointID).set(lastVersion)
            
            assetPublishPath = "%s/v%s/caches" % (assetPublishPath, lastVersion)
            
            fileName = self.get_version_file(assetPublishPath)
            
            if(fileName is not None):
                assetPublishPath = "%s/%s" % (assetPublishPath, fileName)
                
            hou_node.parm("assetPath%i" % pointID).set(assetPublishPath)
        
        self.load_assets(hou_node)
        if(len(shaders_assignations)>0): self.update_materials(hou_node, shaders_assignations)
    
    def get_asset_versions(self, publishPath):
        """ Get the list of available versions for the current publish path.
        """
        versionList = []
        
        if(os.path.exists(publishPath)):
            for folder in os.listdir(publishPath):
                if(folder[0] == 'v'):
                    versionList.append(folder.split('v')[1])
                    
        return versionList

    def get_last_version(self, versions):
        """ Get the last version number from the version list.
        """
        lastVersion = '000'
        
        for ver in versions:
            if(int(lastVersion) < int(ver)):
                lastVersion = ver

        return lastVersion
        
    def get_version_file(self, path):
        """ Get the version from the filepath.
        """
        if(os.path.exists(path)):
            files = os.listdir(path)
            if(len(files) > 0):
                return files[0]
                
        return None
    
    def load_assets(self, hou_node):
        """ Load all the assets from the UI.
        """
        for i in range(hou_node.parm('assets').eval()):
            assetName       = hou_node.parm('assetName%i' % i).evalAsString()
            assetInstance   = hou_node.parm('assetInstance%i' % i).evalAsString()
            
            assetPath       = hou_node.parm('assetPath%i' % i).evalAsString()
            
            nodeName        = "%s_%s" % (assetName, assetInstance)
                    
            if(hou_node.node(nodeName) is None):
                assetNode   = hou_node.createNode('loadAsset', node_name=nodeName)
                assetNode.parm("alembicFile").set(hou_node.parm('assetPath%i' % i))
                assetNode.parm("setDressGeometry").set('../IMPORT_SET_DRESS/OUT')
                assetNode.parm("assetInstance").set(hou_node.parm('assetInstance%i' % i))
                assetNode.parm("viewportlod").set(hou_node.parm('assetDisplay%i' % i))
                assetNode.parm("viewportlod2").set(hou_node.parm('assetDisplay%i' % i))
                
        hou_node.layoutChildren()
    
    def clear_assets(self, hou_node):
        """Clear all the generated assets.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        for child in hou_node.children():
            if(child.name() in self.processing_nodes): continue
            child.destroy()
    
    def get_materials_assignations(self, hou_node):
        """Get the materials from the scene.

        Args:
            hou_node (`class` : hou.Node): the current hda node.

        Returns:
            list: List of the shaders by objects.
        """
        assignations = []

        base_material_structure = {}

        for child in hou_node.children():
            if(child.name() in self.processing_nodes): continue

            # First check if the shader is assigned to the objects.
            if(child.isLockedHDA()):
                assignations.append(
                    {
                        "obj" : child.name(),
                        "materials" : [
                            {
                                "paths" : "#",
                                "sop_materialpath" : child.parm('shop_materialpath').evalAsString()
                            }
                        ]
                    }
                )
            # Then check if the shader is splitted.
            elif(child.node('material1') != None):
                datas = {
                    "obj" : child.name(),
                    "materials" : []
                }

                for matID in range(1, 1+int(child.node('material1').parm('num_materials').evalAsString())):
                    datas["materials"].append(
                        {
                            "paths" : child.node('material1').parm(f'group{matID}').evalAsString(),
                            "sop_materialpath" : child.node('material1').parm(f'shop_materialpath{matID}').evalAsString()
                        }
                    )

                assignations.append(datas)
            else:
                print(f"ERROR: Failed to get material for {child.name()}")
        
        return assignations

    def update_materials(self, hou_node, shaders_assignations):
        """Update materials.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
            shaders_assignations (list): List of the assignations between objects and shaders.
        """
        for assignation in shaders_assignations:
            if(hou_node.node(assignation["obj"]) == None): continue

            target_obj = hou_node.node(assignation["obj"])

            for matID, matAssign in enumerate(assignation["materials"]):
                if(matAssign["paths"] == "#"):
                    target_obj.parm('shop_materialpath').set(
                        matAssign["sop_materialpath"]
                    )
                    continue
            
                if(target_obj.node('material1') == None):
                    target_obj.allowEditingOfContents()
                    target_obj.createNode('material', node_name="material1")
                    target_obj.node("material1").setInput(
                        0,
                        target_obj.node("attribwrangle1")
                    )
                    target_obj.node("OUT").setInput(
                        0,
                        target_obj.node("material1")
                    )
                    
                    target_obj.layoutChildren()

                target_obj.node("material1").parm("num_materials").set(
                    len(assignation["materials"])
                )
                
                target_obj.node('material1').parm(f"group{matID+1}").set(
                    matAssign['paths']
                )
                target_obj.node('material1').parm(f"shop_materialpath{matID+1}").set(
                    matAssign['sop_materialpath']
                )
    
    def export_materialx(self, hou_node):
        """Export materialx from objects.

        Args:
            hou_node (`class` : hou.Node): the current hda node.
        """
        houdini_scene_directory = os.path.dirname(hou.hipFile.path())
        splitted_path = houdini_scene_directory.split("/")

        # TODO: Make that much better ;)
        output_directory_path = os.path.join(
            f"{splitted_path[0]}\\",
            splitted_path[1],
            splitted_path[2],
            splitted_path[3],
            splitted_path[4],
            splitted_path[5],
            "publishs",
            splitted_path[7]
        )

        version = int(self.get_last_version(self.get_asset_versions(output_directory_path))) + 1

        output_directory_path = os.path.join(output_directory_path, f"v{str(version).zfill(3)}")
        os.makedirs(output_directory_path)

        export_node = hou_node.node('EXPORT_MTLX').node('output')

        for child in hou_node.children():
            if(child.name() in self.processing_nodes): continue

            export_node.parm('vobject').set(
                f"{hou_node.name()}/{child.name()}"
            )

            export_node.parm('ar_materialx_file').set(
                os.path.join(output_directory_path, f"{child.name()}.mtlx")
            )

            export_node.parm('execute').pressButton()