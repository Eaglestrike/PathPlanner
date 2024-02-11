# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 21:05:36 2023

@author: degog
"""
import math

class Vector():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def ang(self):
        return math.atan2(self.y, self.x)
        
    def mag(self):
        return math.sqrt(self.x*self.x + self.y*self.y)
    
    def dot(self, v2):
        return self.x*v2.x + self.y*v2.y
    
    def cross(self, v2):
        return self.x*v2.y - self.y*v2.x
    
    def unit(self):
        mag = self.mag()
        if mag == 0.0:
            return Vector(1, 0)
        return Vector(self.x/mag, self.y/mag)
    
    def proj(self, v2):
        return v2.unit() * self.dot(v2)
    
    def extend(ang, mag):
        return Vector(math.cos(ang)*mag, math.sin(ang)*mag)
    
    def rotateCCW(self):
        return Vector(-self.y, self.x)
    
    def rotate(self, ang):
        cos = math.cos(ang)
        sin = math.sin(ang)
        x = self.x*cos - self.y*sin
        y = self.x*sin + self.y*cos
        return Vector(x,y)
    
    def getTuple(self):
        return (self.x, self.y)
    
    def copy(self):
        return Vector(self.x, self.y)
    
    def __add__(self, o):
        return Vector(self.x + o.x, self.y + o.y)
    
    def __iadd__(self, o):
        return Vector(self.x + o.x, self.y + o.y)
    
    def __sub__(self, o):
        return Vector(self.x - o.x, self.y - o.y)
    
    def __mul__(self, k):
        return Vector(self.x*k, self.y*k)
    
    def __rmul__(self, k):
        return Vector(self.x*k, self.y*k)
    
    def __truediv__(self, k):
        return Vector(self.x/k, self.y/k)
    
    def __repr__(self):
        return "<%.3f, %.3f>" %(self.x, self.y)
    
    def __str__(self):
        return "<%.3f, %.3f>" %(self.x, self.y)
    
    def __neg__(self):
        return Vector(-self.x, -self.y)
    