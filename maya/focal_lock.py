import maya.cmds as cmds

def add_focal_length_expression(camera_name, target_object_name):
    # Get the transform node associated with the camera
    transform_node = cmds.listRelatives(camera_name, parent=True, fullPath=True)[0]

    expression_name = 'DistanceToFocalLengthExpression'

    expression_string = f"""
    float $distance = pow(pow(({transform_node}.translateX - {target_object_name}.translateX), 2.0) + 
                         pow(({transform_node}.translateY - {target_object_name}.translateY), 2.0) + 
                         pow(({transform_node}.translateZ - {target_object_name}.translateZ), 2.0), 0.5);
    {camera_name}.focalLength = $distance;
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

    cmds.window('DistanceToFocalLengthUI', title='Distance to Focal Length', widthHeight=(300, 120))
    cmds.columnLayout(adjustableColumn=True)

    # Camera selection
    cmds.text(label='Select a camera:')
    camera_option_menu = cmds.optionMenu()
    for camera in cmds.ls(type='camera'):
        cmds.menuItem(label=camera)

    # Object selection
    cmds.text(label='Select an object:')
    object_option_menu = cmds.optionMenu()
    for obj in cmds.ls(type='transform'):
        cmds.menuItem(label=obj)

    # Button to add expression
    cmds.button(label='Add Expression', command=lambda *args: add_expression_btn_clicked(camera_option_menu, object_option_menu))

    # Button to clear expression
    cmds.button(label='Clear Expression', command=lambda *args: clear_expression_btn_clicked(camera_option_menu))

    cmds.showWindow('DistanceToFocalLengthUI')

def add_expression_btn_clicked(camera_option_menu, object_option_menu):
    selected_camera = cmds.optionMenu(camera_option_menu, query=True, value=True)
    selected_object = cmds.optionMenu(object_option_menu, query=True, value=True)

    add_focal_length_expression(selected_camera, selected_object)

def clear_expression_btn_clicked(camera_option_menu):
    selected_camera = cmds.optionMenu(camera_option_menu, query=True, value=True)

    clear_focal_length_expression(selected_camera)

create_ui()
