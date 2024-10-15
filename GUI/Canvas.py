# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 21:06:24 2023

@author: degog
"""

import tkinter as tk
from PIL import ImageTk
import itertools

from Util.Vector import Vector

from GUI.Plotter import Plotter

displayInches = False

class CanvasPoint():
    def __init__(self, pos, color, canvas, layer = 0):
        self.pos = pos
        
        self.canvas = canvas
        self.id = None
        self.layer = layer
        
        self.updated = False
        
        self.draw(True)
        self.setColor(color)
    
    def setPos(self, pos):
        self.pos = pos
        self.updated = True
    
    def draw(self, update = False):
        if (not self.updated) and (not update):
            return
        canvasPoint = self.canvas.getCanvasPos(self.pos)
        boundBox = [
            (canvasPoint + Vector(-2,-2)).getTuple(),
            (canvasPoint + Vector(2,2)).getTuple()
        ]
        if self.id is not None:
            self.canvas.canvas.coords(self.id, *itertools.chain.from_iterable(boundBox))
        else:
            self.id = self.canvas.canvas.create_oval(*boundBox, tags = ("layer "+str(self.layer),))
        self.updated = False
    
    def setColor(self, color):
        self.canvas.canvas.itemconfig(self.id, fill = color, outline = color, width = 1.0)
        
    def config(self, **kwargs):
        self.canvas.canvas.itemconfig(self.id, *kwargs)
        
    def delete(self):
        self.canvas.canvas.delete(self.id)
        self.canvas.delete(self)
        
class CanvasVector():
    def __init__(self, pos, vec, color, canvas, layer = 0):
        self.pos = pos
        self.vec = vec
        
        self.canvas = canvas
        self.id = None
        self.layer = layer
        
        self.updated = False
        
        self.draw(True)
        self.setColor(color)
    
    def setState(self, pos, vec):
        self.pos = pos
        self.vec = vec
        self.updated = True
    
    def draw(self, update = False):
        if (not self.updated) and (not update):
            return
        
        side = (self.vec*0.1).rotateCCW()
        side2 = side * 0.3
        stem = self.vec*0.8
        
        fieldShape = [
            self.pos,
            stem + side2 + self.pos,
            stem + side + self.pos,
            self.vec + self.pos,
            stem - side + self.pos,
            stem - side2 + self.pos
        ]
        canvasShape = [
            self.canvas.getCanvasPos(p).getTuple() for p in fieldShape
        ]
        if self.id is not None:
            self.canvas.canvas.coords(self.id, *itertools.chain.from_iterable(canvasShape))
        else:
            self.id = self.canvas.canvas.create_polygon(*canvasShape, tags = ("layer "+str(self.layer),))
        self.updated = False
    
    def setColor(self, color):
        self.canvas.canvas.itemconfig(self.id, fill = color)
        
    def delete(self):
        self.canvas.canvas.delete(self.id)
        self.canvas.delete(self)

class CanvasObject():
    def __init__(self, pos, ang, shape, canvas, layer = 0):
        self.pos = pos
        self.ang = ang
        self.baseShape = shape
        
        self.updated = False
        
        self.canvas = canvas
        self.id = None
        self.layer = layer
        
        self.draw(True)
        
    def setPos(self, pos):
        self.pos = pos
        self.updated = True
        
    def setAng(self, ang):
        self.ang = ang
        self.updated = True
        
    def setState(self, pos, ang):
        self.pos = pos
        self.ang = ang
        self.updated = True
        
    def draw(self, update = False):
        if (not self.updated) and (not update):
            return
        fieldShape = [
            v.rotate(self.ang)+self.pos for v in self.baseShape
        ]
        canvasShape = [
            self.canvas.getCanvasPos(p).getTuple() for p in fieldShape
        ]
        if self.id is not None:
            self.canvas.canvas.coords(self.id, *itertools.chain.from_iterable(canvasShape))
        else:
            self.id = self.canvas.canvas.create_polygon(*canvasShape, tag = ("layer "+str(self.layer),))
        self.updated = False
    
    def setColor(self, color):
        self.canvas.canvas.itemconfig(self.id, fill = color)
        
    def delete(self):
        self.canvas.canvas.delete(self.id)
        self.canvas.delete(self)
        
class CanvasImage():
    def __init__(self, pos, size, img, canvas, layer = 0):
        self.pos = pos
        self.size = size
        self.img = img
        
        self.prevScale = None
        self.prevSize = None
        self.prevTopLeft = None
        self.updated = False
        
        self.canvas = canvas
        self.id = None
        self.layer = layer
        
        self.draw(True)
        
    def setPos(self, pos):
        self.pos = pos
        self.updated = True
        
    def setState(self, pos, size):
        self.pos = pos
        self.size = size
        self.updated = True
        
    def draw(self, update = False):
        if (not self.updated) and (not update):
            return
        self.updated = False
        
        width, height = self.img.size
        scale = self.size*self.canvas.scale
        cPos = self.canvas.getCanvasPos(self.pos)
        
        newSize = (int(scale), int(scale*height/width))
        
        #Cropping sides
        cWidth, cHeight = self.canvas.getSize()
        left = max(0.0, cPos.x)
        top = max(0.0, cPos.y)
        right = min(cWidth, newSize[0] + cPos.x)
        bottom = min(cHeight, newSize[1] + cPos.y)
        newSize = (int(right-left), int(bottom-top))
        
        if (self.prevSize is not None) and (self.id is not None): #Save computation when image is only shifted and greater than view
            prevLeft = cPos.x + self.prevTopLeft[0]
            prevTop = cPos.y + self.prevTopLeft[1] 
            shifted = (self.prevScale == scale and
                       prevLeft <= left and
                       prevTop <= top and
                       prevLeft + self.prevSize[0] >= right and
                       prevTop + self.prevSize[1] >= bottom)
            if shifted:
                self.canvas.canvas.coords(self.id, cPos.x + self.prevTopLeft[0], cPos.y + self.prevTopLeft[1])
                return
            
        isZero = (newSize[0] < 0) or (newSize[1] < 0)
        if self.id is not None: #Delete item if exists to redraw (or not)
            self.canvas.canvas.delete(self.id)
            self.id = None
        if not isZero: #Don't draw when image size is 0
            imgLeft = width*(left-cPos.x)/scale
            imgTop = width*(top-cPos.y)/scale
            imgRight = imgLeft + width*newSize[0]/scale
            imgBottom = imgTop + width*newSize[1]/scale
            crop = self.img.crop((imgLeft, imgTop, imgRight, imgBottom))
            
            if 0 not in crop.size:
                resize = crop.resize(newSize)
                self.tkImage = ImageTk.PhotoImage(resize)
                self.id = self.canvas.canvas.create_image((left, top),
                                                          image = self.tkImage,
                                                          anchor = tk.NW,
                                                          tags = ("layer "+str(self.layer),))
        self.prevTopLeft = (left-cPos.x, top-cPos.y)
        self.prevSize = newSize
        self.prevScale = scale
    
    def setColor(self, color):
        self.canvas.canvas.itemconfig(self.id, fill = color)
        
    def delete(self):
        self.canvas.canvas.delete(self.id)
        self.canvas.delete(self)
        
class Canvas():
    def __init__(self, window, **kwargs):
        self.canvas = tk.Canvas(window, **kwargs)
        
        self.clickedPoint = None
        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<B1-Motion>", self.dragged)
        self.canvas.bind("<MouseWheel>", self.scrolled)
        
        self.layers = [0]
        self.canvasObjects = []
        self.tempObjects = []
        self.deleteObjects = []
        
        self.pos = Vector(0,0)
        self.center = Vector(0, 0)
        self.scale = 1
        
        self.canDrag = True
        
        self.mouseText = self.canvas.create_text(0,0, tags = ("UI",))
        self.pointClicked = self.addPoint(Vector(0,0), "light green")
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
        self.canvas.update()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.center = Vector(width/2.0, height/2.0)
        self.scale = min(width, height)*0.1
        
    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)
        self.canvas.update()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.center = Vector(width/2.0, -height/2.0)
        self.scale = min(width, height)*0.1
        
    def addObject(self, obj):
        self.canvasObjects.append(obj)
        if obj.layer not in self.layers:
            self.layers.append(obj.layer)
            self.layers.sort()
        
    def drawObject(self, obj):
        self.tempObjects.append(obj)
        if obj.layer not in self.layers:
            self.layers.append(obj.layer)
            self.layers.sort()
        
    def addShape(self, pos, ang, shape, layer = 0):
        canvasObj = CanvasObject(pos, ang, shape, self, layer = layer)
        self.addObject(canvasObj)
        return canvasObj
    
    def addPlotter(self, points, color, fade = 0.0, layer = 0):
        plotter = Plotter(points, color, self, fade, layer = layer)
        self.addObject(plotter)
        return plotter
    
    def addPoint(self, point, color, layer = 0):
        cPoint = CanvasPoint(point, color, self, layer = layer)
        self.addObject(cPoint)
        return cPoint
    
    def addVector(self, point, vector, color, layer = 0):
        cVector = CanvasVector(point, vector, color, self, layer = layer)
        self.addObject(cVector)
        return cVector
    
    def drawVector(self, point, vector, color, layer = 0):
        cVector = CanvasVector(point, vector, color, self, layer = layer)
        self.drawObject(cVector)
        
    def addImage(self, pos, size, image, layer = 0):
        cImg = CanvasImage(pos, size, image, self, layer = layer)
        self.addObject(cImg)
        return cImg
    
    def update(self, allUpdate = False):
        #Draw temporary objects once
        for obj in self.deleteObjects:
            obj.delete()
            pass
        for obj in self.tempObjects:
            obj.draw(allUpdate)
        self.deleteObjects = self.tempObjects.copy()
        self.tempObjects.clear()
        
        #Draw permanent objects
        for obj in self.canvasObjects:
            obj.draw(allUpdate)
        
        #Deal with layers by raising objects
        for layer in self.layers:
            self.canvas.tag_raise("layer "+str(layer))
        self.canvas.tag_raise("UI")
    
    def clicked(self, event):
        self.clickedPoint = Vector(event.x, event.y)
        pos = self.getFieldPos(self.clickedPoint)
        self.pointClicked.setPos(pos)
        
    def motion(self, event):
        canvasPos = Vector(event.x, event.y)
        pos = self.getFieldPos(canvasPos)
        self.canvas.coords(self.mouseText, canvasPos.x, canvasPos.y-10)
        if displayInches:
            self.canvas.itemconfig(self.mouseText, text = str(pos/0.0254))
        else:
            self.canvas.itemconfig(self.mouseText, text = str(pos))
        
    def dragged(self, event):
        point = Vector(event.x, event.y)
        self.canvas.coords(self.mouseText, point.x, point.y-10)
        if self.clickedPoint is None or not self.canDrag:
            return
        d = (self.clickedPoint-point)/self.scale
        self.pos += d
        self.clickedPoint = point
        
        pos = self.getFieldPos(point)
        self.canvas.itemconfig(self.mouseText, text = str(pos))
        
        self.update(True)
        
    def scrolled(self, event):
        self.scale *= 2**(event.delta/1000.0)
        self.update(True)
        
    def getFieldPos(self, point):
        p = point.copy()
        pos = (p - self.center)/self.scale + self.pos
        pos.y = -pos.y
        return pos
        
    def getCanvasPos(self, point):
        p = point.copy()
        p.y = -p.y
        pos = ((p - self.pos)*self.scale+self.center)
        return pos
    
    def getSize(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        return (width, height)
    
    def getCorners(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        return [
            self.getFieldPos(Vector(0.0, 0.0)),
            self.getFieldPos(Vector(0.0, height)),
            self.getFieldPos(Vector(width,height)),
            self.getFieldPos(Vector(width, 0.0))
            ]
    
    def config(self, **kwargs):
        self.canvas.config(**kwargs)
    
    def delete(self, obj):
        if obj in self.canvasObjects:
            self.canvasObjects.remove(obj)