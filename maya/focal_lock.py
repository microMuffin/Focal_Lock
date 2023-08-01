import maya.cmds as cmds
import math
import logging

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize dictionary for all script job IDs
scriptJobIds = {
    'timeChange': None,
    'playbackRangeChange': None,
    'txChange': None,
    'tyChange': None,
    'tzChange': None
}

def cleanUptimeChangeJobIds():
    logger.info('Entered cleanUptimeChangeJobIds function')
    global scriptJobIds
    for jobId in scriptJobIds:
        if scriptJobIds[jobId] is not None:
            cmds.scriptJob(kill=scriptJobIds[jobId], force=True)
            scriptJobIds[jobId] = None
    logger.info('Exiting cleanUptimeChangeJobIds function')



# add these function to calculate the dot product and the forward vector
def dotProduct(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

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

def computeFocalLengthRatio(cam, obj):
    if not cam or not obj:
        return
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
    print(vec)
    print(forwardVector)
    actualDist = dotProduct(vec, forwardVector)

    # get the current camera's focal length
    currentFocalLength = cmds.getAttr(cam + '.focalLength')

    # calculate the focal length ratio
    global focalLengthRatio
    focalLengthRatio = currentFocalLength / actualDist

def maintainFocalLengthRatio():
    cam = cmds.optionMenu(cameraMenu, query=True, value=True)
    obj = cmds.optionMenu(objectMenu, query=True, value=True)
    if not cam or not obj:
        return
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
    logger.info('Entered onObjectChanged function')
    global scriptJobIds
    cam = cmds.optionMenu(cameraMenu, query=True, value=True)
    obj = cmds.optionMenu(objectMenu, query=True, value=True)
    if cam is not None and obj is not None and cmds.objExists(cam) and cmds.objExists(obj):
        computeFocalLengthRatio(cam, obj)
        if any(scriptJobIds.values()):  # if any script job is active
            cleanUptimeChangeJobIds()
        scriptJobIds['timeChange'] = cmds.scriptJob(e=("timeChanged", maintainFocalLengthRatio), protected=True)
        scriptJobIds['playbackRangeChange'] = cmds.scriptJob(e=("playbackRangeChanged", maintainFocalLengthRatio), protected=True)
        scriptJobIds['txChange'] = cmds.scriptJob(attributeChange=(cam + ".tx", maintainFocalLengthRatio), protected=True)
        scriptJobIds['tyChange'] = cmds.scriptJob(attributeChange=(cam + ".ty", maintainFocalLengthRatio), protected=True)
        scriptJobIds['tzChange'] = cmds.scriptJob(attributeChange=(cam + ".tz", maintainFocalLengthRatio), protected=True)
    else:
        logger.warning("Invalid camera or object selected.")
    logger.info('Exiting onObjectChanged function')

def onFocalLockChanged(enabled):
    """ Callback function for the focal lock checkbox change. """
    logger.info('Entered onFocalLockChanged function')
    global scriptJobIds
    if enabled:
        cam = cmds.optionMenu(cameraMenu, query=True, value=True)
        obj = cmds.optionMenu(objectMenu, query=True, value=True)
        if not cam or not obj or not cmds.objExists(cam) or not cmds.objExists(obj):
            cmds.warning("Invalid camera or object selected.")
            cmds.checkBox(focalLockCheckbox, edit=True, value=False)  # uncheck the checkbox
            return
        computeFocalLengthRatio(cam, obj)
        scriptJobIds['timeChange'] = cmds.scriptJob(e=("timeChanged", maintainFocalLengthRatio), protected=True)
        scriptJobIds['playbackRangeChange'] = cmds.scriptJob(e=("playbackRangeChanged", maintainFocalLengthRatio), protected=True)
        scriptJobIds['txChange'] = cmds.scriptJob(attributeChange=(cam + ".tx", maintainFocalLengthRatio), protected=True)
        scriptJobIds['tyChange'] = cmds.scriptJob(attributeChange=(cam + ".ty", maintainFocalLengthRatio), protected=True)
        scriptJobIds['tzChange'] = cmds.scriptJob(attributeChange=(cam + ".tz", maintainFocalLengthRatio), protected=True)
    else:
        # Kill the script job
        if any(scriptJobIds.values()):
            cleanUptimeChangeJobIds()
    logger.info('Exiting onFocalLockChanged function')

def populateCameraMenu():
    logger.info('Entered populateCameraMenu function')
    # Get currently selected menu item
    selectedCam = cmds.optionMenu(cameraMenu, query=True, value=True)
    logger.info('Selected camera: ' + str(selectedCam))

    # Clear the existing menu items
    cmds.optionMenu(cameraMenu, edit=True, deleteAllItems=True)

    # Get list of new cameras
    cameraShapeList = cmds.ls(cameras=True)
    cameraList = cmds.listRelatives(cameraShapeList, parent=True)

    # Add new cameras to menu
    for cam in cameraList:
        cmds.menuItem(label=cam)

    # If previously selected camera still exists, re-select it
    if selectedCam and cmds.objExists(selectedCam):
        cmds.optionMenu(cameraMenu, edit=True, value=selectedCam)
    logger.info('Exiting populateCameraMenu function')

def populateObjectMenu():
    # Get currently selected menu item
    logger.info('Entered populateObjectMenu function')
    selectedObj = cmds.optionMenu(objectMenu, query=True, value=True)
    logger.info('Selected object: ' + str(selectedObj))

    # Clear the existing menu items
    cmds.optionMenu(objectMenu, edit=True, deleteAllItems=True)
    print("All objects deleted from list!")

    # Get list of new objects
    shapeNodes = cmds.ls(dag=True, leaf=True, noIntermediate=True, shapes=True)
    shapeNodes = [shapeNode for shapeNode in shapeNodes if shapeNode not in cameraShapeList] # Exclude cameras from the list
    transformNodes = cmds.listRelatives(shapeNodes, parent=True, fullPath=True) # Get parent transform nodes

    if transformNodes is not None:
        # Add new objects to menu
        for node in transformNodes:
            cmds.menuItem(label=node)

        # If previously selected object still exists, re-select it
        if selectedObj and cmds.objExists(selectedObj):
            cmds.optionMenu(objectMenu, edit=True, value=selectedObj)
    logger.info('Exiting populateObjectMenu function')

def refreshLists(*args):
    """ Callback function for the refresh lists button click. """
    logger.info('Entered refreshLists function')
    populateCameraMenu()
    populateObjectMenu()
    logger.info('Exiting refreshLists function')

def onWindowClose(killOnClose=True):
    """ Callback function for window close. """
    logger.info('Entered onWindowClose function')
    # global timeChangeJobId
    # if timeChangeJobId and cmds.control(killOnCloseCheckbox, exists=True) and cmds.checkBox(killOnCloseCheckbox, query=True, value=True): 
    cleanUptimeChangeJobIds()
    logger.info('Exiting onWindowClose function')

# Create the window
window = cmds.window(title="Focal Lock", widthHeight=(200, 100))
cmds.columnLayout(adjustableColumn=True)

cameraShapeList = cmds.ls(cameras=True)
cameraList = cmds.listRelatives(cameraShapeList, parent=True)

# Create the user interface elements
cmds.text(label='Camera:')
cameraMenu = cmds.optionMenu(changeCommand=onObjectChanged)
populateCameraMenu()

cmds.text(label='Target Object:')
objectMenu = cmds.optionMenu(changeCommand=onObjectChanged)
populateObjectMenu()
# Create the button
refreshButton = cmds.button(label='Refresh Lists', command='refreshLists()')

focalLockCheckbox = cmds.checkBox(label='Lock Focal Length', changeCommand=onFocalLockChanged)
killOnCloseCheckbox = cmds.checkBox(label='Kill on Close', value=True)

# Show the window
cmds.showWindow(window)

# Create a script job that triggers when the window is deleted
cmds.scriptJob(uiDeleted=(window, onWindowClose))
logging.info('SCRIPT INITIALIZED\n\n')