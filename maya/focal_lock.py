import maya.cmds as cmds

# Maintain a script job ID
scriptJobId = None
focalLengthRatio = 1.0

def computeFocalLengthRatio(cam, obj):
    if not cmds.objExists(cam) or not cmds.objExists(obj):
        print("Camera or object does not exist.")
        return

    print(obj)
    # get current position of obj
    objPos = cmds.xform(obj, q=True, t=True, ws=True)

    # get current position of camera
    camPos = cmds.xform(cam, q=True, t=True, ws=True)

    # calculate vector from cam to obj
    vec = [objPos[0] - camPos[0], objPos[1] - camPos[1], objPos[2] - camPos[2]]

    # calculate actual distance
    actualDist = (vec[0]**2 + vec[1]**2 + vec[2]**2)**0.5

    # get the current camera's focal length
    currentFocalLength = cmds.getAttr(cam + '.focalLength')

    # calculate the focal length ratio
    global focalLengthRatio
    focalLengthRatio = currentFocalLength / actualDist

def maintainFocalLengthRatio(cam, obj):
    if not cmds.objExists(cam) or not cmds.objExists(obj):
        print("Camera or object does not exist.")
        return

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

def onObjectChanged(*args):
    """ Callback function for the object dropdown menu change. """
    global scriptJobId
    cam = cmds.optionMenu(cameraMenu, query=True, value=True)
    obj = cmds.optionMenu(objectMenu, query=True, value=True)
    computeFocalLengthRatio(cam, obj)
    if scriptJobId:
        cmds.scriptJob(kill=scriptJobId, force=True)
        scriptJobId = cmds.scriptJob(e=("idle", lambda: maintainFocalLengthRatio(cam, obj)), protected=True)

# def onEnableLockChanged(*args):
#     """ Callback function for the lock checkbox. """
#     global lockId, focalLengthRatio

    if cmds.checkBox(lockCheckBox, query=True, value=True):
        cam = cmds.optionMenu(cameraMenu, query=True, value=True)
        obj = cmds.optionMenu(objectMenu, query=True, value=True)

        # check if cam or obj is None or invalid
        if not cam or not obj or not cmds.objExists(cam) or not cmds.objExists(obj):
            cmds.warning("Invalid camera or object selected.")
            cmds.checkBox(lockCheckBox, edit=True, value=False)  # uncheck the checkbox
            return
        
        # further operations with cam and obj...

def onFocalLockChanged(enabled):
    """ Callback function for the focal lock checkbox change. """
    global scriptJobId
    if enabled:
        cam = cmds.optionMenu(cameraMenu, query=True, value=True)
        obj = cmds.optionMenu(objectMenu, query=True, value=True)
        if not cam or not obj or not cmds.objExists(cam) or not cmds.objExists(obj):
            cmds.warning("Invalid camera or object selected.")
            cmds.checkBox(focalLockCheckbox, edit=True, value=False)  # uncheck the checkbox
            return
        computeFocalLengthRatio(cam, obj)
        scriptJobId = cmds.scriptJob(e=("idle", lambda: maintainFocalLengthRatio(cam, obj)), protected=True)
    else:
        # Kill the script job
        if scriptJobId:
            cmds.scriptJob(kill=scriptJobId, force=True)
            scriptJobId = None

def onWindowClose(killOnClose=True):
    """ Callback function for window close. """
    global scriptJobId
    if scriptJobId and killOnClose:
        # Kill the script job
        cmds.scriptJob(kill=scriptJobId, force=True)
        scriptJobId = None

# Create the window
window = cmds.window(title="Focal Lock", widthHeight=(200, 100))
cmds.columnLayout(adjustableColumn=True)

cameraShapeList = cmds.ls(cameras=True)
cameraList = cmds.listRelatives(cameraShapeList, parent=True)

# Create the user interface elements
cmds.text(label='Camera:')
cameraMenu = cmds.optionMenu(changeCommand=onObjectChanged)
for cam in cameraList:
    cmds.menuItem(label=cam)

cmds.text(label='Target Object:')
objectMenu = cmds.optionMenu(changeCommand=onObjectChanged)
shapeNodes = cmds.ls(dag=True, leaf=True, noIntermediate=True, shapes=True)
transformNodes = cmds.listRelatives(shapeNodes, parent=True, fullPath=True) # Get parent transform nodes
transformNodes = [node for node in transformNodes if node not in cameraList] # Exclude camera transform nodes from this list
for node in transformNodes:
    cmds.menuItem(label=node)

focalLockCheckbox = cmds.checkBox(label='Lock Focal Length', changeCommand=onFocalLockChanged)
killOnCloseCheckbox = cmds.checkBox(label='Kill on Close', value=True)

# Show the window
cmds.showWindow(window)

# Create a script job that triggers when the window is deleted
cmds.scriptJob(uiDeleted=(window, onWindowClose))
