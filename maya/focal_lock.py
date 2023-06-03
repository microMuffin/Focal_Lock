import maya.cmds as cmds
import math

# Maintain a script job ID
scriptJobId = None
objectCreationJobId = None
focalLengthRatio = 1.0
# add these function to calculate the dot product and the forward vector
def dotProduct(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def computeForwardVector(rotation):
    # Convert the rotation to radians
    rotation = [math.radians(x) for x in rotation]

    # Calculate the forward direction vector
    forwardVector = [math.cos(rotation[1])*math.cos(rotation[0]), math.sin(rotation[0]), math.cos(rotation[1])*math.sin(rotation[0])]

    return forwardVector

def computeFocalLengthRatio(cam, obj):
    if not cmds.objExists(cam) or not cmds.objExists(obj):
        print("Camera or object does not exist.")
        return

    # get current position of obj
    objPos = cmds.xform(obj, q=True, t=True, ws=True)

    # get current position and rotation of camera
    camPos = cmds.xform(cam, q=True, t=True, ws=True)
    camRot = cmds.xform(cam, q=True, rotation=True)

    # calculate the forward direction vector of the camera
    forwardVector = computeForwardVector(camRot)

    # calculate vector from cam to obj
    vec = [objPos[0] - camPos[0], objPos[1] - camPos[1], objPos[2] - camPos[2]]

    # calculate the dot product of vec and forwardVector
    actualDist = dotProduct(vec, forwardVector)

    # get the current camera's focal length
    currentFocalLength = cmds.getAttr(cam + '.focalLength')

    # calculate the focal length ratio
    global focalLengthRatio
    focalLengthRatio = currentFocalLength / actualDist

# similarly, update maintainFocalLengthRatio function
def maintainFocalLengthRatio(cam, obj):
    if not cmds.objExists(cam) or not cmds.objExists(obj):
        print("Camera or object does not exist.")
        return

    # get current position of obj
    objPos = cmds.xform(obj, q=True, t=True, ws=True)

    # get current position and rotation of camera
    camPos = cmds.xform(cam, q=True, t=True, ws=True)
    camRot = cmds.xform(cam, q=True, rotation=True)

    # calculate the forward direction vector of the camera
    forwardVector = computeForwardVector(camRot)

    # calculate vector from cam to obj
    vec = [objPos[0] - camPos[0], objPos[1] - camPos[1], objPos[2] - camPos[2]]

    # calculate the dot product of vec and forwardVector
    actualDist = dotProduct(vec, forwardVector)

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

def populateObjectMenu():
    # Get currently selected menu item
    selectedObj = cmds.optionMenu(objectMenu, query=True, value=True)

    # Clear the existing menu items
    cmds.optionMenu(objectMenu, edit=True, deleteAllItems=True)

    # Get list of new objects
    shapeNodes = cmds.ls(dag=True, leaf=True, noIntermediate=True, shapes=True)
    shapeNodes = [shapeNode for shapeNode in shapeNodes if shapeNode not in cameraShapeList] # Exclude cameras from the list
    transformNodes = cmds.listRelatives(shapeNodes, parent=True, fullPath=True) # Get parent transform nodes

    # Add new objects to menu
    for node in transformNodes:
        cmds.menuItem(label=node)

    # If previously selected object still exists, re-select it
    if selectedObj and cmds.objExists(selectedObj):
        cmds.optionMenu(objectMenu, edit=True, value=selectedObj)

def onObjectCreation(*args):
    """ Callback function for the object creation. """
    populateObjectMenu()
    onObjectChanged()

def onWindowClose(killOnClose=True):
    """ Callback function for window close. """
    global scriptJobId
    if scriptJobId and cmds.control(killOnCloseCheckbox, exists=True) and cmds.checkBox(killOnCloseCheckbox, query=True, value=True): 
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
populateObjectMenu()

focalLockCheckbox = cmds.checkBox(label='Lock Focal Length', changeCommand=onFocalLockChanged)
killOnCloseCheckbox = cmds.checkBox(label='Kill on Close', value=True)

# Show the window
cmds.showWindow(window)

# Create a script job that triggers when the window is deleted
cmds.scriptJob(uiDeleted=(window, onWindowClose))

# Create a script job that triggers when a new object is created
objectCreationJobId = cmds.scriptJob(e=("DagObjectCreated", onObjectCreation), protected=True)
