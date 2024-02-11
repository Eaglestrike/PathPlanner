# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 20:48:34 2023

@author: degog
"""

import time
import tkinter as tk
from PIL import Image
import numpy as np
import sys

from Util.Vector import Vector
import Util.FileUtil as FileUtil

import Follow.Follow as Follow

from GUI.Input import Input
from GUI.Canvas import Canvas
from GUI.VarDisplay import VarDisplay

import Simulation.Drivebase as DB

import Code.Path as Path

#%% Window Setup
#Settings file
settingsFileName = "settings.json"
settings = FileUtil.openJsonFile(settingsFileName)
if settings is None:
    settings = {}
    
#Window
window = tk.Tk()
window.title("Path Planner")
window.state('zoomed')
WIDTH = window.winfo_screenwidth()
HEIGHT = window.winfo_screenheight()

#Canvas
CANVASWIDTH = int(WIDTH*(2/3))
CANVASHEIGHT = HEIGHT
canvas = Canvas(window, width=CANVASWIDTH, height=CANVASHEIGHT, relief = "solid", borderwidth = 2)
canvas.pack(side = 'left')

#%%Objects

#Field Image
field = Image.open("2024Game.png")
#canvas.addImage(Vector(-12.072 + 8.89, 2.288 + 7.388), 26.71866/1.15, field, layer = -1)
field2 = Image.open("2024Game2.png")
canvas.addImage(Vector(-3.561, 9.948), 23.429521, field2, layer = -1)

#Eaglestrike Logo
logo = Image.open("eaglestrike.png")
logo = logo.convert('RGBA')
data = np.array(logo)   # "data" is a height x width x 4 numpy array
red, green, blue, alpha = data.T # Temporarily unpack the bands for readability
# Replace white with red... (leaves alpha values alone...)
white_areas = (red == 255) & (blue == 255) & (green == 255)
data[..., :-1][white_areas.T] = (255, 0, 0) # Transpose back needed
logo = Image.fromarray(data)
#canvas.addImage(Vector(0.0,0.0), 2.0, logo)

path = Path.Path(mode = "trapezoidal", canvas = canvas, layer = 5)
path.maxA = 2.5
path.maxV = 3.0

pose = DB.DrivePose(Vector(0,0), 0.5, Vector(0,0), 0.0)
drivebase = DB.Drivebase(pose, 0.6858, canvas, trails = True, vectors = True, wheelTrails= False)

'''
#Testing trapezoidal profile
pose1 = TP.Pose(0,0,0)
pose2 = TP.Pose(10,0,0)
profile = TP.TrapezoidalProfile(10.0, 1.0, pose1, pose2)
points = []
points2 = []
t = 0.0
while t < profile.getDuration():
    pose = profile.getPose(t)
    points.append(Vector(t, pose.vel))
    points2.append(Vector(t, pose.pos))
    t+=0.1
print(profile.getDuration())
canvas.addPlotter(points, "blue", layer = 100)
canvas.addPlotter(points2, "red", layer = 100)
'''

sides = [
    "Left",
    "Mid",
    "Right"
]
types = [
    "Intake",
    "Score",
    "End"
]
wayPoints = []
for s in sides:
    for t in types:
        wayPoints.append(s + t)

#%% Functions
state = 'default'
paused = False
def setState(newState, paused_ = False):
    global state
    global paused
    state = newState
    paused = paused_
    canvas.canDrag = True
    
def togglePause():
    global paused
    paused = not paused

t = 0
def run(dt):
    global t
    global isRunning
    n = 10
    for i in range(n):
        drivebase.run(dt/n)
    t += dt

def keyPressedCallback(event):
    if event.keysym == "space":
        togglePause()
    elif event.keysym == "Escape":
        setState("default")
    if state == "editPoint":
        if event.keysym == "Down":
            path.shiftSelect(-1)
            setPathPoint()
        elif event.keysym == "Up":
            path.shiftSelect(1)
            setPathPoint()
Input.keyPressedCallback = keyPressedCallback

robotFollowPath = None
def mousePressedCallback(event):
    if event.widget == canvas.canvas:
        window.focus()
        if state == "editPoint":
            path.selectPoint(canvas.getFieldPos(Vector(event.x, event.y)))
            canvas.canDrag = path.selectedIndex < 0
            setPathPoint()
        elif state == "selectRobotPos":
            global robotFollowPath #Path where robot pos lines up with current path
            robotPos = drivebase.pose.getRobotPos(canvas.getFieldPos(Vector(event.x, event.y)))
            if robotFollowPath is not None:
                robotFollowPath.clear()
            robotFollowPath = Follow.followPath(path, robotPos)
            robotFollowPath.layer = path.layer
            robotFollowPath.color = "red"
            robotFollowPath.setCanvas(canvas)
            print("path length:", len(robotFollowPath))
            
Input.mousePressedCallback = mousePressedCallback

def mouseReleasedCallback(event):
    windowPos = Vector(event.x, event.y)
    pos = canvas.getFieldPos(windowPos)
    if state == 'addPoint':
        if event.widget == canvas.canvas and (windowPos - Input.screenPos).mag() < 10.0: # did not move
            ang = len(path)*0
            path.addPose(DB.DrivePose(pos, ang), float(len(path)))
Input.mouseReleasedCallback = mouseReleasedCallback

def rightMousePressedCallback(event):
    if state == 'addPoint':
        setState('default')
Input.rightMousePressedCallback = rightMousePressedCallback

def motionCallback(event, dt):
    if event.widget == canvas.canvas:
        windowPos = Vector(event.x, event.y)
        pos = canvas.getFieldPos(windowPos)
        if dt != 0.0:
            Input.mousePos = pos
            Input.mouseVel = (pos - Input.mousePos)/dt
        if state == "editPoint":
            if Input.pressed:
                path.dragged(pos)
Input.motionCallback = motionCallback
    
def default():
    if paused:
        return
    x = 0.0
    y = 0.0
    ang = 0.0
    speed = 12.0
    angSpeed = 12.0
    if Input.getKey("d") or Input.getKey("Right"):
        x += speed
    if Input.getKey("a") or Input.getKey("Left"):
        x -= speed
    if Input.getKey("w") or Input.getKey("Up"):
        y += speed
    if Input.getKey("s") or Input.getKey("Down"):
        y -= speed
    if Input.getKey("comma"):
        ang += angSpeed
    if Input.getKey("period"):
        ang -= angSpeed
    drivebase.setTarget(Vector(x, y), ang)
    run(0.02)

#%% Side bar
#Side bar
SIDEWIDTH = WIDTH - CANVASWIDTH
SIDEHEIGHT = HEIGHT
side = tk.Frame(window, width = SIDEWIDTH, height = SIDEHEIGHT)
side.pack(side = "left", expand=True)
    
#Pathing buttons

def clear():
    global robotFollowPath
    if robotFollowPath is not None:
        robotFollowPath.clear()
        robotFollowPath = None
    path.clear()
    setPathPoint()
    
pathMaker = tk.Frame(side)
tk.Button(pathMaker, text = 'add points', command = lambda:setState("addPoint")).pack(side = "left")
tk.Button(pathMaker, text = 'clear', command = clear).pack(side = "left")
tk.Button(pathMaker, text = 'edit points', command = lambda:setState("editPoint")).pack(side = "left")
tk.Button(pathMaker, text = 'zero', command = path.zero).pack(side = "left")
pathMaker.pack()

scale = 1.0
def scalePath():
    path.scale(scale)
    
VarDisplay(side, sys.modules[__name__], "scale", edit = True)
tk.Button(side, text = 'scale', command = scalePath).pack()


VarDisplay(side, sys.modules[__name__], "state", edit = False)
VarDisplay(side, sys.modules[__name__], "paused", edit = False)

def savePath():
    filepath = FileUtil.selectSaveFile([("Save File", ".csv")], "Saves")
    if filepath is None:
        return
    if ".csv" not in filepath.name:
        filepath = filepath.name + ".csv"
    path.toDataframe().to_csv(filepath, index = False, lineterminator='\n')
    
def saveFollowPath():
    if robotFollowPath is None:
        return
    filepath = FileUtil.selectSaveFile([("Save File", ".csv")], "Saves")
    if filepath is None:
        return
    if ".csv" not in filepath.name:
        filepath = filepath.name + ".csv"
    robotFollowPath.toDataframe().to_csv(filepath, index = False, lineterminator='\n')
    
def openPath():
    data = FileUtil.selectDataframe("Saves")
    if data is not None:
        path.setDataFrame(data)
    setPathPoint()
    
def addPath():
    data = FileUtil.selectDataframe("Saves")
    if data is not None:
        path.addDataFrame(data)
    setPathPoint()
    
fileStuff = tk.Frame(side)
tk.Button(fileStuff, text = 'save', command = savePath).pack(side = "left")
tk.Button(fileStuff, text = 'saveFollow', command = saveFollowPath).pack(side = "left")
tk.Button(fileStuff, text = 'open', command = openPath).pack(side = "left")
tk.Button(fileStuff, text = 'add', command = addPath).pack(side = "left")
fileStuff.pack()

tk.Button(side, text = 'follow mouse', command = lambda:setState("followMouse")).pack()
tk.Button(side, text = 'generate follow path', command = lambda:setState("selectRobotPos")).pack()

pathTime = 0
ghost = None
follow = False
def followPath(dt):
    global pathTime
    global ghost
    global displayTime
    if paused:
        return
    pathTime += dt
    if robotFollowPath is None:
        maxTime = path.getMaxTime()
        targPose = path.getPose(pathTime)
    else:
        maxTime = robotFollowPath.getMaxTime()
        targPose = robotFollowPath.getPose(pathTime)
    if pathTime > maxTime:
        if ghost is not None:
            ghost.delete()
            ghost = None
        setState("default")
        return
    if follow:
        drivebase.setTargetPose(targPose)
    ghost.setPose(targPose, pathTime)
    run(dt)
    
def startPath():
    global pathTime
    global ghost
    pathTime = 0.0
    setState("play")
    drivebase.clearTrails()
    if ghost is None:
        ghost = DB.Drivebase(path.getPose(0.0), drivebase.size, canvas, vectors = True)
        ghost.canvasObject.setColor("light green")
    startPose = path.getPose(0.0)
    startPose.vel.x = 0.0
    startPose.vel.y = 0.0
    if follow:
        drivebase.setPose(startPose, 0.0)

tk.Button(side, text = 'play', command = startPath).pack()
VarDisplay(side, sys.modules[__name__], "follow", edit = True)
VarDisplay(side, sys.modules[__name__], "pathTime", edit = False)

#Config options
switch = tk.Frame(side)
switch.config(relief = "solid", border = 1)
switch.pack(side="top", fill="both", expand=True)

C_WIDTH = SIDEWIDTH
C_HEIGHT = SIDEHEIGHT/2.0

container = tk.Frame(side, width = C_WIDTH, height = C_HEIGHT)
container.config(relief = "solid", border = 1)
container.pack(side="top", fill="both", expand=True)
container.grid_rowconfigure(0)
container.grid_columnconfigure(0)

simConfig = tk.Frame(container, width = C_WIDTH, height = C_HEIGHT)
simConfig.grid(row=0, column=0, sticky="new")

tk.Label(simConfig, text="Simulation Config").pack(side="top", fill="x", pady=10)
VarDisplay(simConfig, DB.Wheel, "kResponse", edit = True)
VarDisplay(simConfig, DB.Wheel, "kEMF", edit = True)
VarDisplay(simConfig, DB.Drivebase, "linFrict", edit = True)
VarDisplay(simConfig, DB.Drivebase, "angFrict", edit = True)

tuning = tk.Frame(container, width = C_WIDTH, height = C_HEIGHT)
tuning.grid(row=0, column=0, sticky="new")

tk.Label(tuning, text="Tuning").pack(side="top", fill="x", pady=10)
VarDisplay(tuning, DB.Wheel, "useDot", edit = True)
VarDisplay(tuning, DB.Wheel, "kP", name = "wheel kp", edit = True)
VarDisplay(tuning, DB.Drivebase, "kLinP", edit = True)
VarDisplay(tuning, DB.Drivebase, "kLinD", edit = True)
VarDisplay(tuning, DB.Drivebase, "kLinV", edit = True)
VarDisplay(tuning, DB.Drivebase, "kAngP", edit = True)
VarDisplay(tuning, DB.Drivebase, "kAngD", edit = True)
VarDisplay(tuning, DB.Drivebase, "kAngV", edit = True)

info = tk.Frame(container, width = C_WIDTH, height = C_HEIGHT)
info.grid(row=0, column=0, sticky="new")

VarDisplay(info, drivebase, "pose.pos", edit = False)
VarDisplay(info, drivebase, "pose.vel", edit = False)
VarDisplay(info, drivebase, "pose.vel.mag", edit = False)
VarDisplay(info, drivebase, "pose.ang", edit = False)
VarDisplay(info, drivebase, "pose.angVel", edit = False)

pathPoint = tk.Frame(container, width = C_WIDTH, height = C_HEIGHT)
pathPoint.grid(row=0, column=0, sticky="new")
VarDisplay(pathPoint, path, "getMaxTime", edit = False)
VarDisplay(pathPoint, path, "maxA", edit = True)
VarDisplay(pathPoint, path, "maxV", edit = True)
VarDisplay(pathPoint, path, "mode", edit = True)

#Rebuild path
def regenerate():
    path.regenerate()
    setPathPoint()
tk.Button(pathPoint, text = "regenerate", command = regenerate).pack(side = "top")

pathDisplays = []
def setPathPoint():
    for display in pathDisplays:
        display.delete()
    pathDisplays.clear()
    index = path.selectedIndex
    if index < 0:
        return
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].pos.x"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].pos.y"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].vel.x"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].vel.y"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].ang"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][0].angVel"%(index), edit = True))
    pathDisplays.append(VarDisplay(pathPoint, path, "poses[%s][1]"%(index), edit = True))


frames = {
    "simConfig":simConfig,
    "tuning":tuning,
    "info":info,
    "pathPoint":pathPoint
}
def showFrame(pageName):
    for frame in frames.values():
        frame.grid_remove()
    frame = frames[pageName]
    frame.grid()
    
tk.Button(switch, text = "Sim Config", command = lambda:showFrame("simConfig")).pack(side = "left")
tk.Button(switch, text = "Tuning", command = lambda:showFrame("tuning")).pack(side = "left")
tk.Button(switch, text = "Info", command = lambda:showFrame("info")).pack(side = "left")
tk.Button(switch, text = "Path Point", command = lambda:showFrame("pathPoint")).pack(side = "left")
showFrame("simConfig")

#Key binding
window.bind("<Key>", Input.keyPressed)
window.bind("<KeyRelease>", Input.keyReleased)
window.bind("<Motion>", Input.motion)
window.bind("<Button-1>", Input.mousePressed)
window.bind("<Button-3>", Input.rightMousePressed)
window.bind("<ButtonRelease-1>", Input.mouseReleased)
    
#%% Main
prevTime = time.time()
def main():
    global prevTime
    dt = time.time() - prevTime
    if state == "default":
        default()
    elif state == "play":
        followPath(dt)
    elif state == "followMouse":
        drivebase.setTargetPose(DB.DrivePose(Input.mousePos, Input.mouseVel.ang()), True)
        run(dt)
    elif state == "selectRobotPos":
        pass
    canvas.update()
    for display in pathDisplays:
        if display.updated:
            path._updateSelect()
            break
    VarDisplay.updateAll()
    prevTime = time.time()
    window.after(20, main)

def _quit():
    window.quit()     # stops mainloop
    window.destroy() 
    FileUtil.saveJsonFile(settings, settingsFileName)
    
main()
window.mainloop()
FileUtil.saveJsonFile(settings, settingsFileName)