# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 18:48:57 2024

@author: degog
"""
import time

from Util.Vector import Vector

class Input():
    pressed = False
    screenPos = Vector(0,0) #Clicked Point in window coordinates
    
    mousePos = Vector(0,0)
    mouseVel = Vector(0,0)
    
    keys = {}
    
    def keyPressedCallback(event):#Override/Define elsewhere
        pass
    def keyPressed(event):
        Input.keyPressedCallback(event)
        Input.keys[event.keysym] = True
        
    def keyReleased(event):
        Input.keys[event.keysym] = False
    
    def getKey(key):
        if key in Input.keys:
            return Input.keys[key]
        return False
    
    def mousePressedCallback(event):#Override/Define elsewhere
        pass
    def mousePressed(event):
        Input.mousePressedCallback(event)
        Input.pressed = True
        Input.screenPos = Vector(event.x, event.y)
    
    def rightMousePressedCallback(event):
        pass
    def rightMousePressed(event):
        Input.rightMousePressedCallback(event)
    
    def mouseReleasedCallback(event):
        pass
    def mouseReleased(event):
        Input.mouseReleasedCallback(event)
        Input.pressed = False
                
    prevT = time.time()
    def motionCallback(event, dt):
        pass
    def motion(event):
        dt = time.time() - Input.prevT
        Input.motionCallback(event, dt)
        Input.prevT = time.time()