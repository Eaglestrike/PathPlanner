# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 23:49:05 2023

@author: degog
"""

import itertools

class Plotter():
    def __init__(self, points, color, canvas, fade = 0.0, layer = 0):
        self.points = points
        self.times = [0]*len(points)
        self.fade = fade
        
        self.updated = False
        
        self.canvas = canvas
        self.id = None
        self.layer = layer
        
        self.draw(True)
        self.setColor(color)
        
    def addPoint(self, point, time):
        for n, i in enumerate(self.times[::-1]): #reverse index finder
            if time > i:
                self.points.insert(len(self.times) - n, point)
                self.times.insert(len(self.times) - n, time)
                self.updated = True
                self._fadePoints()
                return
        self.points.insert(0, point) #added point before tracked time
        self.times.insert(0, time)
        self._reverseFade() 
        self.updated = True
        
    def editPoint(self, index, pos):
        self.points[index] = pos
        self.updated = True
        
    def _reverseFade(self): #fade from back
        if self.fade <= 0.0 or len(self.points) < 2:
            return
        fadeTime = self.times[0] + self.fade
        while self.times[-1] > fadeTime:
            self.points.pop(-1)
            self.times.pop(-1)
        
    def _fadePoints(self): #fade from front
        if self.fade <= 0.0 or len(self.points) < 2:
            return
        fadeTime = self.times[-1] - self.fade
        while self.times[0] < fadeTime:
            self.points.pop(0)
            self.times.pop(0)
        
    def draw(self, update = False):
        if (not self.updated) and (not update):
            return
        canvasPoints = [
            self.canvas.getCanvasPos(p).getTuple() for p in self.points
        ]
        if self.id is not None:
            if len(self.points) < 2:
                self.canvas.canvas.coords(self.id, 0, 0, 0, 0)
            else:
                self.canvas.canvas.coords(self.id, *itertools.chain.from_iterable(canvasPoints))
        else:
            if len(self.points) < 2:
                self.id = self.canvas.canvas.create_line(0,0,0,0, tags = ("layer "+str(self.layer),))
            else:
                self.id = self.canvas.canvas.create_line(*canvasPoints, tags = ("layer "+str(self.layer),))
        self.updated = False
        
    def setColor(self, color):
        self.canvas.canvas.itemconfig(self.id, fill = color)
        
    def setPoints(self, points, t = 0):
        self.points = points
        self.times = [t]*len(points)
        self.updated = True
        
    def clear(self):
        self.points.clear()
        self.times.clear()
        self.draw(True)
        
    def delete(self):
        self.canvas.canvas.delete(self.id)
        self.canvas.delete(self)