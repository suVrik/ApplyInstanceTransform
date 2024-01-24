'''
    Copyright (C) 2024  Andrei Suvorau

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


bl_info = {
    "name": "Apply Instance Transform",
    "author": "Andrei Suvorau",
    "version": (1, 0, 0),
    "blender": (3, 00, 0),
    "location": "Object > Apply",
    "description": ("Apply Instance Transform"),
    "warning": "",
    "wiki_url": "https://github.com/suVrik/ApplyInstanceTransform/wiki",
    "tracker_url": "https://github.com/suVrik/ApplyInstanceTransform/issues" ,
    "category": "Object"
}


import bpy
import mathutils


# https://blender.stackexchange.com/questions/159538/how-to-apply-all-transformations-to-an-object-at-low-level
def apply_transfrom(object, use_location = False, use_rotation = False, use_scale = False):
    matrix = object.matrix_basis
    I = mathutils.Matrix()
    location, rotation, scale = matrix.decompose()

    T = mathutils.Matrix.Translation(location)
    R = matrix.to_3x3().normalized().to_4x4()
    S = mathutils.Matrix.Diagonal(scale).to_4x4()

    transform = [I, I, I]
    basis = [T, R, S]

    def swap(i):
        transform[i], basis[i] = basis[i], transform[i]

    if use_location:
        swap(0)
    if use_rotation:
        swap(1)
    if use_scale:
        swap(2)
        
    M = transform[0] @ transform[1] @ transform[2]
    
    if hasattr(object.data, "transform"):
        object.data.transform(M)
        
    for child in object.children:
        child.matrix_local = M @ child.matrix_local
        
    object.matrix_basis = basis[0] @ basis[1] @ basis[2]

    return M.inverted_safe()


class ApplyInstanceTransform_OT(bpy.types.Operator):
    bl_label = 'Apply Instance Transform'
    bl_idname = 'object.transform_apply_instance'
    bl_options = {'REGISTER', 'UNDO'}

    location: bpy.props.BoolProperty(name = "Location")
    rotation: bpy.props.BoolProperty(name = "Rotation")
    scale: bpy.props.BoolProperty(name = "Scale")

    def execute(self, context):
        if bpy.context.active_object and bpy.context.active_object.select_get() and bpy.context.active_object.type == 'MESH':
            M = apply_transfrom(bpy.context.active_object, self.location, self.rotation, self.scale)
            
            result = 1

            for object in bpy.data.objects:
                if object.type == 'MESH' and object.data == bpy.context.active_object.data and object != bpy.context.active_object:
                    object.matrix_local = object.matrix_local @ M
                    result = result + 1

            self.report({'INFO'}, '%d instances were adjusted.' % result)
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, 'Active object must be mesh.')
            return {'CANCELLED'}


def VIEW3D_ApplyInstanceTransform_Menu(self, context):
    layout = self.layout
        
    layout.separator()
    
    props = layout.operator('object.transform_apply_instance', text = 'Apply Instance Location')
    props.location, props.rotation, props.scale = True, False, False
    
    props = layout.operator('object.transform_apply_instance', text = 'Apply Instance Rotation')
    props.location, props.rotation, props.scale = False, True, False
    
    props = layout.operator('object.transform_apply_instance', text = 'Apply Instance Scale')
    props.location, props.rotation, props.scale = False, False, True
    
    props = layout.operator('object.transform_apply_instance', text = 'Apply All Instance Transforms')
    props.location, props.rotation, props.scale = True, True, True
    
    props = layout.operator('object.transform_apply_instance', text = 'Apply Instance Rotation & Scale')
    props.location, props.rotation, props.scale = False, True, True


def register():
    bpy.utils.register_class(ApplyInstanceTransform_OT)
    bpy.types.VIEW3D_MT_object_apply.append(VIEW3D_ApplyInstanceTransform_Menu)


def unregister():
    bpy.types.VIEW3D_MT_object_apply.remove(VIEW3D_ApplyInstanceTransform_Menu)
    bpy.utils.unregister_class(ApplyInstanceTransform_OT)


if __name__ == '__main__':
    register()
