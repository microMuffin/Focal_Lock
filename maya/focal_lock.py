import maya.cmds as cmds

def maintainFocalLengthRatio(cam, obj, focalLengthRatio):
    # get current position of obj
    objPos = cmds.xform(obj, q=True, t=True, ws=True)
    
    # get current position of camera
    camPos = cmds.xform(cam, q=True, t=True, ws=True)

    # calculate vector from cam to obj
    vec = [objPos[0] - camPos[0], objPos[1] - camPos[1], objPos[2] - camPos[2]]

    # calculate actual distance
    actualDist = (vec[0]**2 + vec[1]**2 + vec[2]**2)**0.5

    # adjust camera focal length based on the distance and the desired ratio
    newFocalLength = actualDist * focalLengthRatio
    cmds.setAttr(cam + '.focalLength', newFocalLength)


# initialize distance and focal length ratio
focalLengthRatio = 1.0

def maintainFocalLength(*args):
    """ Callback function for the button. """
    global focalLengthRatio
    cam = cmds.optionMenu(cameraMenu, query=True, value=True)
    obj = cmds.optionMenu(objectMenu, query=True, value=True)
    maintainFocalLengthRatio(cam, obj, focalLengthRatio)

def onFocalLengthRatioChanged(*args):
    """ Callback function for the focal length ratio field. """
    global focalLengthRatio
    focalLengthRatio = cmds.floatField(focalLengthRatioField, query=True, value=True)

# create the window
window = cmds.window(title="Focal Lock", widthHeight=(200, 100))
cmds.columnLayout(adjustableColumn=True)

# create the user interface elements
cmds.text(label='Camera:')
cameraMenu = cmds.optionMenu()
for cam in cmds.ls(cameras=True):
    cmds.menuItem(label=cam)

cmds.text(label='Target Object:')
objectMenu = cmds.optionMenu()
objects = cmds.ls(dag=True, leaf=True, noIntermediate=True, shapes=True)
objects = [object for object in objects if object not in cmds.ls(cameras=True)] # Exclude the cameras from this list
for obj in objects:
    cmds.menuItem(label=obj)

cmds.text(label='Focal Length Ratio:')
focalLengthRatioField = cmds.floatField(minValue=0.0, value=focalLengthRatio, changeCommand=onFocalLengthRatioChanged)

cmds.button(label="Lock Focal Length", command=maintainFocalLength)

cmds.showWindow(window)

# Test
