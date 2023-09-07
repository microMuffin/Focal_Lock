import maya.cmds as cmds
import math

focal_length_ratio = None

def dotProduct(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def subtractVector(v1, v2):
    return [v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]]

def computeForwardVector(rotation):
    # Convert the rotation to radians
    rotation = [math.radians(x) for x in rotation]

    # Calculate the forward direction vector based on Maya's default orientation
    forwardVector = [
        -math.sin(rotation[1])*math.cos(rotation[0]), 
        math.sin(rotation[0]), 
        -math.cos(rotation[1])*math.cos(rotation[0])
    ]

    return forwardVector

def compute_distance_along_camera_forward_vector(camera_name, target_object_name):
    object_position = cmds.xform(target_object_name, query=True, translation=True, worldSpace=True)
    camera_position = cmds.xform(camera_name, query=True, translation=True, worldSpace=True)
    camera_rotation = cmds.xform(camera_name, query=True, rotation=True, worldSpace=True)

    camera_forward_vector = computeForwardVector(camera_rotation)

    # Calculate the vector from the camera to the object
    camera_to_object_vector = [object_position[0] - camera_position[0], object_position[1] - camera_position[1], object_position[2] - camera_position[2]]

    # Calculate the distance along the camera's forward vector
    distance = dotProduct(camera_to_object_vector, camera_forward_vector)

    return distance

def add_focal_length_expression(camera_name, target_object_name):
    global focal_length_ratio

    # Get the transform node associated with the camera
    camera_transform_node = cmds.listRelatives(camera_name, parent=True, fullPath=True)[0]

    initial_focal_length = cmds.getAttr(camera_name + '.focalLength')
    initial_distance = compute_distance_along_camera_forward_vector(camera_transform_node, target_object_name)
    if (initial_distance == 0):
        # Report an error to the user
        cmds.error("The selected objects do not have a distance between them. Please ensure that you have selected the camera's shape node and the object's transform node. Please also ensure that the camera and target object have distance between them.")
        return
    focal_length_ratio = initial_focal_length / initial_distance

    expression_name = 'DistanceToFocalLengthExpression'

    expression_string = f"""
    float $distance = pow(pow(({camera_transform_node}.translateX - {target_object_name}.translateX), 2.0) + 
                         pow(({camera_transform_node}.translateY - {target_object_name}.translateY), 2.0) + 
                         pow(({camera_transform_node}.translateZ - {target_object_name}.translateZ), 2.0), 0.5);

    // Store initial focal length and distance when the expression is created
    // Calculate updated focal length based on the initial ratio
    {camera_name}.focalLength = $distance * {focal_length_ratio};
    """

    # Check if the expression already exists and delete it if it does
    if expression_name in cmds.ls(type='expression'):
        cmds.delete(expression_name)

    # Create the expression
    cmds.expression(name=expression_name, string=expression_string)

def clear_focal_length_expression(camera_name):
    expression_name = 'DistanceToFocalLengthExpression'

    # Check if the expression exists and delete it if it does
    if expression_name in cmds.ls(type='expression'):
        cmds.delete(expression_name)

def create_ui():
    if cmds.window('DistanceToFocalLengthUI', exists=True):
        cmds.deleteUI('DistanceToFocalLengthUI', window=True)

    cmds.window('DistanceToFocalLengthUI', title='Focal Lock', widthHeight=(300, 120))
    cmds.columnLayout(adjustableColumn=True)

    # Camera selection
    cmds.text(label='Select a camera:')
    camera_option_menu = cmds.optionMenu()
    for camera in cmds.ls(type='camera'):
        cmds.menuItem(label=camera)

    # Object selection
    cmds.text(label='Select a target object:')
    object_option_menu = cmds.optionMenu()
    for obj in cmds.ls(type='transform'):
        cmds.menuItem(label=obj)

    # Button to Add Focal Length Expression
    cmds.button(label='Add Focal Length Expression to Camera', command=lambda *args: add_expression_btn_clicked(camera_option_menu, object_option_menu))

    # Button to Remove Focal Length Expression
    cmds.button(label='Remove Focal Length Expression from Camera', command=lambda *args: clear_expression_btn_clicked(camera_option_menu))

    cmds.showWindow('DistanceToFocalLengthUI')

def add_expression_btn_clicked(camera_option_menu, object_option_menu):
    selected_camera = cmds.optionMenu(camera_option_menu, query=True, value=True)
    selected_object = cmds.optionMenu(object_option_menu, query=True, value=True)

    add_focal_length_expression(selected_camera, selected_object)

def clear_expression_btn_clicked(camera_option_menu):
    selected_camera = cmds.optionMenu(camera_option_menu, query=True, value=True)

    clear_focal_length_expression(selected_camera)

create_ui()
