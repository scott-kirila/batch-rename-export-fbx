# batch_rename_export_fbx.py

"""
Batch Rename & Export FBX
- Rename selection with prefix (index optional).
- Export as a single FBX, or individual FBXs per selected object.
- Axis presets: Blender, Maya, Unity, Unreal.
- Confirmation dialog shows how many files will be generated.
"""

bl_info = {
    "name": "Batch Rename & Export FBX",
    "author": "Scott Kirila",
    "version": (1, 0, 0),
    "blender": (4, 3, 2),
    "location": "3D Viewport > N-Panel > TA Tools",
    "description": "Rename and export selection as FBX with prefixing, per-object, and axis preset options.",
    "category": "Import-Export",
}

import os
import bpy
from typing import List, Sequence
from bpy.types import Operator, Panel, Context, Object
from bpy.props import StringProperty, EnumProperty, BoolProperty

# ---------------- Axis presets ----------------
ENGINE_AXIS_PRESETS = {
    "BLENDER": dict(axis_forward='-Y', axis_up='Z'),
    "MAYA": dict(axis_forward='Z', axis_up='Y'),
    "UNITY": dict(axis_forward='-Z', axis_up='Y'),
    "UNREAL": dict(axis_forward='X', axis_up='Z'),
}

AXIS_ITEMS = (
    ("BLENDER", "Blender", "Z Up, -Y Forward"),
    ("MAYA", "Maya", "Y Up,  Z Forward"),
    ("UNITY", "Unity", "Y Up, -Z Forward"),
    ("UNREAL", "Unreal", "Z Up,  X Forward"),
)


class Utilities:
    @staticmethod
    def get_export_dir(export_path: str) -> str:

        raw = export_path or "//"
        abs_path = bpy.path.abspath(raw)
        os.makedirs(abs_path, exist_ok=True)

        return abs_path

    @staticmethod
    def get_selection(context: Context) -> List[Object]:
        sel = list(context.selected_objects)

        # Sort by a cleaned base name so numbering is predictable
        def _key(o):
            tokens = o.name.split("_")
            if tokens and tokens[0].isupper():
                tokens = tokens[1:]

            if tokens and tokens[0].isdigit():
                tokens = tokens[1:]

            return "_".join(tokens) or o.name

        return sorted(sel, key=_key)

    @staticmethod
    def ensure_object_mode(context, *, report=None) -> bool:
        """Ensure we're in OBJECT mode before selection/export ops."""
        active = context.view_layer.objects.active
        mode = getattr(active, "mode", "OBJECT") if active else "OBJECT"

        if mode != 'OBJECT':
            try:
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode='OBJECT')

            except Exception as e:
                if report:
                    report({'ERROR'}, f"Could not switch to Object Mode: {e}")

                return False

            # Verify
            active = context.view_layer.objects.active
            if getattr(active, "mode", "OBJECT") != 'OBJECT':
                if report:
                    report({'ERROR'}, "Please switch to Object Mode before exporting.")

                return False

        return True

    @staticmethod
    def add_prefix(objects: Sequence[Object], prefix: str, add_index: bool, sep: str = "_") -> int:
        prefix = prefix.rstrip(sep)
        count = 0

        for i, obj in enumerate(objects, 1):
            tokens = obj.name.split(sep)

            # If the first token is ALL CAPS, strip it
            if tokens and tokens[0].isupper():
                tokens = tokens[1:]

            # If the next token is numeric (like "001"), strip it too
            if tokens and tokens[0].isdigit():
                tokens = tokens[1:]

            base_name = sep.join(tokens)
            parts = [prefix]

            if add_index:
                parts.append(f"{i:03d}")

            if base_name:
                parts.append(base_name)

            obj.name = sep.join(parts)
            count += 1

        return count

    @staticmethod
    def export_fbx(filepath: str, axis_key: str) -> None:
        preset = ENGINE_AXIS_PRESETS.get(axis_key, ENGINE_AXIS_PRESETS["BLENDER"])

        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            apply_unit_scale=True,
            bake_space_transform=True,
            apply_scale_options="FBX_SCALE_ALL",
            **preset
        )


class SelectionGuard:
    """Preserves user selection even if an error occurs."""
    def __init__(self, context: Context):
        self.context = context
        self.prev_active = context.view_layer.objects.active
        self.prev_sel = list(context.selected_objects)

    def __enter__(self):
        bpy.ops.object.select_all(action='DESELECT')

        return self

    def set(self, objs: Sequence[Object]):
        for o in objs:
            o.select_set(True)

        if objs:
            self.context.view_layer.objects.active = objs[0]

    def __exit__(self, exc_type, exc, tb):
        bpy.ops.object.select_all(action='DESELECT')

        for o in self.prev_sel:
            o.select_set(True)

        self.context.view_layer.objects.active = self.prev_active



class TA_OT_BatchRenameExportFBX(Operator):
    bl_idname = "ta_tools.batch_rename_export_fbx"
    bl_label = "Prefix & Export FBX"
    bl_options = {'REGISTER', 'UNDO'}

    _confirm_text: str = ""

    def invoke(self, context: Context, _event):
        scene = context.scene
        targets = Utilities.get_selection(context)

        if not targets:
            self.report({'WARNING'}, "No objects selected.")

            return {'CANCELLED'}

        # How many files will be generated?
        count = len(targets) if scene.ta_per_object else 1

        s_for_plural = "" if count == 1 else "s"

        self._confirm_text = f"This will generate {count} FBX file{s_for_plural}.\nProceed?"

        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, _context: Context):
        if self._confirm_text:
            col = self.layout.column(align=True)

            for line in self._confirm_text.split("\n"):
                col.label(text=line)

    def execute(self, context: Context):
        # Cancel early in 4 scenarios:
        # 1) We can't switch (if necessary) to OBJECT mode
        # 2) FBX export not supported
        # 3) Exporting to a relative path in an unsaved project
        # 4) No objects are selected

        ### 1 ###
        if not Utilities.ensure_object_mode(context, report=self.report):

            return {'CANCELLED'}

        ### 2 ###
        if not hasattr(bpy.ops.export_scene, "fbx"):
            self.report({'ERROR'}, "FBX exporter not available. Enable 'Import-Export: FBX' in Preferences.")

            return {'CANCELLED'}

        scene = context.scene

        ### 3 ###
        if scene.ta_export_path.startswith("//") and bpy.data.filepath == "":
            bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')
            self.report({'WARNING'}, "Save your .blend, then run export again.")

            return {'CANCELLED'}

        out_dir = Utilities.get_export_dir(scene.ta_export_path)

        targets = Utilities.get_selection(context)

        ### 4 ###
        if not targets:
            self.report({'WARNING'}, "No objects selected.")

            return {'CANCELLED'}

        prefixed = Utilities.add_prefix(targets, prefix=scene.ta_prefix, add_index=scene.ta_add_index)

        try:
            if scene.ta_per_object:
                exported = 0

                with SelectionGuard(context) as sel:
                    for obj in targets:
                        sel.set([obj])
                        out_path = os.path.join(out_dir, f"{obj.name}.fbx")
                        Utilities.export_fbx(out_path, scene.ta_axis_preset)
                        exported += 1

                self.report({'INFO'},
                            f"Renamed {prefixed} object(s); exported {exported} FBX files to {out_dir} ({scene.ta_axis_preset}).")

            else:
                with SelectionGuard(context) as sel:
                    sel.set(targets)
                    out_path = os.path.join(out_dir, scene.ta_export_filename or "Export.fbx")
                    Utilities.export_fbx(out_path, scene.ta_axis_preset)

                self.report({'INFO'}, f"Renamed {prefixed} object(s); exported {out_path} ({scene.ta_axis_preset}).")

        except RuntimeError as e:
            self.report({'ERROR'}, f"Export failed: {e}")

            return {'CANCELLED'}

        return {'FINISHED'}


class TA_PT_BatchRenameExportPanel(Panel):
    bl_label = "Batch Rename & Export FBX"
    bl_idname = "TA_PT_batch_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TA Tools"

    def draw(self, context: Context):
        scene = context.scene
        layout = self.layout

        # Rename
        box = layout.box()
        box.label(text="Rename", icon="OUTLINER_OB_GROUP_INSTANCE")

        row = box.row(align=True)
        row.prop(scene, "ta_prefix")
        row.prop(scene, "ta_add_index", text="Index")

        # Export
        box2 = layout.box()
        box2.label(text="Export", icon="EXPORT")
        box2.prop(scene, "ta_per_object", text="Per-object FBX")
        box2.prop(scene, "ta_export_path", text="Folder")

        row = box2.row(align=True)
        row.enabled = not scene.ta_per_object
        row.label(text="Filename:")
        row.prop(scene, "ta_export_filename", text="")

        # box2.label(text="Axis Preset")
        row2 = box2.row(align=True)
        row2.label(text="Axis Preset:")
        row2.prop(scene, "ta_axis_preset", text="")

        layout.separator()
        layout.operator(TA_OT_BatchRenameExportFBX.bl_idname, icon="FILE_TICK")


# RNA Registration
classes = (TA_OT_BatchRenameExportFBX, TA_PT_BatchRenameExportPanel)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    scene = bpy.types.Scene

    # Custom properties
    scene.ta_prefix = StringProperty(
        name="Prefix",
        default="SM_",
        description="Text added to the start of each object name (e.g. SM_)."
    )

    scene.ta_add_index = BoolProperty(
        name="Add Index",
        default=True,
        description="Append a 3-digit index after the prefix (001, 002...)."
    )

    scene.ta_per_object = BoolProperty(
        name="Per-Object FBX",
        default=True,
        description="Export one FBX per selected object (file named after the object)."
    )

    scene.ta_export_path = StringProperty(
        name="Export Path",
        subtype='DIR_PATH',
        default="//",
        description="Folder to write exported files. '//' is relative to this .blend file."
    )

    scene.ta_export_filename = StringProperty(
        name="Filename",
        default="Export.fbx",
        description="Used only for a single combined export. Ignored if 'Per-object FBX' is enabled."
    )

    scene.ta_axis_preset = EnumProperty(
        name="Axis Preset",
        items=AXIS_ITEMS,
        default="UNITY",
        description="Coordinate system for FBX export (affects orientation in target DCC/engine)"
    )


def unregister():
    scene = bpy.types.Scene
    for attr in (
            "ta_prefix",
            "ta_add_index",
            "ta_per_object",
            "ta_export_path",
            "ta_export_filename",
            "ta_axis_preset",
    ):
        if hasattr(scene, attr):
            delattr(scene, attr)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
