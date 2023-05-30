#     GPL License Block
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "Focal Lock",
    "description": "Locks object in a camera's plane of focus",
    "author": "Anson Savage <artstation.com/ansonsavage>, Nathan Craddock <nathancraddock.com>",
    "version": (2, 0),
    "blender": (3, 5, 0),
    "location": "View 3D > Properties Panel > Camera",
    "doc_url": "https://github.com/AnsonSavage/Focal_Lock/wiki",
    "tracker_url": "https://github.com/AnsonSavage/Focal_Lock/issues",
    "support": "COMMUNITY",
    "category": "Camera",
    }

# LIBRARIES
############################################################################
from mathutils import Vector
import bpy
from bpy.props import BoolProperty, FloatProperty, PointerProperty
from bpy.types import Panel, PropertyGroup, Operator, Object
from bpy.app.handlers import persistent


#HELPER FUNCTIONS
############################################################################
def distance_to_plane(ob):
    context = bpy.context
    scene = context.scene
    cam = scene.camera
    # Special thanks to batFINGER's answer here: https://blender.stackexchange.com/questions/231817/how-to-obtain-the-vector-normal-to-the-camera-plane
    cam_axis = cam.matrix_world.to_3x3().normalized().col[2]
    cam_axis.negate()
    cam_loc = cam.matrix_world.translation
    v = ob.matrix_world.translation - cam_loc
    n = v.project(cam_axis)
    return n.length


#WATCHER FUNCTIONS
############################################################################
def update_focus_object(self, context):
    """Updates the focus object when the user changes the the focus object with the eyedropper"""

    settings = context.object.data.focal_lock
    update_enable_lock(self, context) # Set all the necessary initial settings
    if settings.enable_track:
        bpy.context.object.constraints["Track To"].target = settings.focus_object

def update_enable_lock(self, context):
    """Sets the original focal length and distance when the user enables the focal lock"""

    settings = context.object.data.focal_lock
    enable_lock = settings.enable_lock
    if enable_lock and settings.focus_object != None:
        # Set persistent properties
        settings.original_focal_length = context.camera.lens
        settings.original_distance = distance_to_plane(settings.focus_object)
        settings.focal_distance_ratio = settings.original_focal_length / settings.original_distance

def update_enable_track(self, context):
    """Adds or removes a track to constraint to the camera based on the enable_track property"""

    settings = context.object.data.focal_lock
    if settings.enable_track:
        bpy.ops.object.constraint_add(type='TRACK_TO')
        bpy.context.object.constraints["Track To"].target = settings.focus_object
    else:
        bpy.ops.constraint.delete(constraint="Track To", owner='OBJECT')

@persistent # This decorator makes sure that the handler is still installed each time the scene is reloaded
def update_focal_length(self, context):
    """Updates the focal length of the each camera with focal lock based on the distance to the focus object"""
    # for each camera with focal_lock enabled...
    for camera in bpy.data.cameras:
        if camera.focal_lock.enable_lock and camera.focal_lock.focus_object != None:
            currentDistance = distance_to_plane(camera.focal_lock.focus_object)
            camera.lens = currentDistance * (camera.focal_lock.focal_distance_ratio) + camera.focal_lock.focal_distance_offset # Set the new focal length to maintain the focal_distance_ratio

#OPERATORS
############################################################################
class BakeFocalLength(bpy.types.Operator):
    """Bake focal length to keyframes for active camera"""
    bl_idname = "wm.bake_focal_length"
    bl_label = "Bake Focal Length"
    def execute(self, context):
        context = bpy.context
        scene = context.scene
        cam = scene.camera
        for frame in range (bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            scene.frame_set(frame)
            cam.data.keyframe_insert(data_path="lens")
        return {'FINISHED'}

class ClearBakeFocalLength(bpy.types.Operator):
    """Clear baked focal length keyframes for active camera"""
    bl_idname = "wm.clear_bake_focal_length"
    bl_label = "Clear Bake"
    def execute(self, context):
        context = bpy.context
        scene = context.scene
        cam = scene.camera
        for frame in range (bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            scene.frame_set(frame)
            cam.data.keyframe_delete(data_path="lens")
        return {'FINISHED'}

#PANELS
############################################################################
class FOCALLOCK_PT_FocalLock(Panel):
    bl_category = "Focal Lock"
    bl_label = "Focal Lock"
    bl_space_type = 'PROPERTIES'
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header(self, context):
        cam = context.camera
        settings = cam.focal_lock
        layout = self.layout
        layout.active = settings.enable_lock
        layout.prop(settings, "enable_lock", text="")

    def draw(self, context):
        cam = context.camera
        settings = cam.focal_lock
        layout = self.layout
        layout.enabled = settings.enable_lock

        # Split layout to look kind of like usual camera settings
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)
        col = flow.column()
        sub = col.column(align=True)

        #Property to set the focus object
        col.prop(settings, "focus_object", text="Focus Object")

        col.prop(settings, 'focal_distance_offset', text="Focal Distance Offset")

        # Mechanics
        col = flow.column()
        #col.prop(settings, 'enable_lock')
        col.prop(settings, 'enable_track')
        col = flow.column()
        sub = col.column(align=True)
        sub.prop(cam, 'lens', text="Focal Length")

class FOCALLOCK_PT_BakeSettings(Panel):
    bl_category = "Baking"
    bl_label = "Baking"
    bl_parent_id = "FOCALLOCK_PT_FocalLock"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.operator("wm.bake_focal_length")
        layout.operator("wm.clear_bake_focal_length")
        layout.label(text="Bake focal length keyframes for active camera")


#PROPERTIES
############################################################################
class FocalLockSettings(PropertyGroup):
    original_distance: FloatProperty(
        name = "Original Distance",
        description = "This is the distance that the camera originally was from the focus object",
        )
    original_focal_length: FloatProperty(
        name = "Original Focal Length",
        description= "The focal length when the user clicked enabled",
        )
    focal_distance_offset: FloatProperty(
        name = "Focal Distance Offset",
        description= "Fine tune the focal length without moving the camera or focus object",
        soft_min = -1,
        soft_max = 1
        )
    focal_distance_ratio: FloatProperty(
        name = "Focal Distance Ratio",
        description= "Ratio of the original focal length over the original distance",
        )
    focus_object: PointerProperty(
        name="Focus Object",
        type=Object,
        description="The object you would like the camera to focus on",
        update = update_focus_object
        )
    enable_lock: BoolProperty(
        name= "Lock",
        description= "Lock camera zoom to focus object",
        default = False,
        update = update_enable_lock
        )
    enable_track: BoolProperty(
        name= "Track camera to object",
        description= "Add a tracking constraint to camera so it always stays focussed on the object",
        default = False,
        update = update_enable_track
        )

#REGISTRATION AND UNREGISTRATION
############################################################################
classes = (
    FOCALLOCK_PT_FocalLock,
    FocalLockSettings,
    BakeFocalLength,
    ClearBakeFocalLength,
    FOCALLOCK_PT_BakeSettings
    )

register, unregister = bpy.utils.register_classes_factory(classes)

# depsgraph_update_post is called when the scene is updated
# frame_change_post is called when the frame is changed
# load_post is called when the file is loaded
handlers = [bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post, bpy.app.handlers.load_post]

# Register and unregister the data classes
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Camera.focal_lock = bpy.props.PointerProperty(type=FocalLockSettings)

    for handler in handlers:
        [handler.remove(h) for h in handler if h.__name__ == "update_focal_length"]
        handler.append(update_focal_length)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Camera.focal_lock


    for handler in handlers:
        [handler.remove(h) for h in handler if h.__name__ == "update_focal_length"]

if __name__ == "__main__":
    register()
