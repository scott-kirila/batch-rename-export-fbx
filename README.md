# Batch Rename & Export FBX

A Blender add-on for technical artists that streamlines renaming and exporting of multiple objects as FBX files.  
It adds a panel to the **3D Viewport > N-Panel > TA Tools** with simple options for prefixing object names, choosing axis presets, and exporting either as a single FBX or per-object.

---

## ✨ Features

- **Batch renaming**  
  Add a consistent prefix to selected objects with optional 3-digit indexing (e.g., `SM_001_Table`).

- **Axis presets**  
  Export using coordinate systems that match **Blender, Maya, Unity,** or **Unreal**.

- **Flexible export modes**  
  - Export all selected objects into one FBX file.  
  - Export each selected object as its own FBX file, named after the object.  

- **Confirmation dialog**  
  Preview how many FBX files will be generated before export.

- **Selection safe**  
  Uses a guard to restore your selection and active object, even if something goes wrong.

---

## 📦 Installation

1. Download the `.py` file.  
2. In Blender, go to **Edit > Preferences > Add-ons > Install...**  
3. Select the `.py` file and enable **Batch Rename & Export FBX**.  
4. The tool will appear in the **3D Viewport > N-Panel > TA Tools** tab.

---

## 🛠️ Usage

1. Select the objects you want to export.  
2. In the **Batch Rename & Export FBX** panel:  
   - Set your **Prefix** and whether to append an **Index**.  
   - Choose **Per-object FBX** (each object gets its own file) or leave unchecked (all exported together).  
   - Pick an **Export Path** and optional **Filename** (for combined export).  
   - Select an **Axis Preset** (Blender, Maya, Unity, Unreal).  
3. Click **Prefix & Export FBX**.  
4. Confirm the number of files to be generated.  

---

## 📂 File Naming

- **Combined export:** Uses the filename you specify (default: `Export.fbx`).  
- **Per-object export:** Each object is saved as `<object_name>.fbx` in the chosen folder.

---

## ⚠️ Notes

- If the export path is relative (`//`), Blender must have a saved `.blend` file. You’ll be prompted to save if not.  
- Requires Blender’s **Import-Export: FBX** add-on to be enabled (enabled by default).  
- Works with Blender 4.3 and newer.

---

## 📸 Demo

<img width="3024" height="1964" alt="image" src="https://github.com/user-attachments/assets/78435c1a-03ad-45cd-a4a8-56063740eac6" />


---

## 📄 License

MIT License – feel free to use, modify, and share.
