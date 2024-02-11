# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 15:09:56 2024

@author: degog
"""

from Util.Vector import Vector

class PID():
    def __init__(self, kp, ki, kd, target = 0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.target = target
        self.targetVel = 0.0
        
        self.prevPos = 0.0
        if isinstance(target, Vector):
            self.accum = Vector(0,0)
        else:
            self.accum = 0.0
    
    def getOutput(self, pos, dt, vel = None):
        error = self.target - pos
        if vel is None:
            vel = (pos - self.prevPos)/dt
        velError = self.targetVel - vel
        self.prevPos = pos
        self.accum += error * dt 
        return self.kp*error + self.kd*velError + self.ki*self.accum
    
    def setTarget(self, pos, vel):
        self.target = pos
        self.targetVel = vel
        if isinstance(self.accum, Vector):
            self.accum = Vector(0,0)
        else:
            self.accum = 0.0