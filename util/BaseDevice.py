
from phidl import Device

class BaseDevice:
    def __init__(self, name):
        self.device = Device(name)
        self.metal  = Device(f'{name}_metal')
        self.pocket = Device(f'{name}_pocket')
        self.devices = [self.device, self.metal, self.pocket]

    def rotate(self, degree):
        for d in self.devices:
            d.rotate(degree)
        return self  

    def move(self, p):   
        for d in self.devices:
            d.move(p)         
        return self

    def movex(self, x):       
        for d in self.devices:
            d.movex(x)                      
        return self

    def movey(self, y):  
        for d in self.devices:
            d.movey(y)            
        return self
    
    def mirror(self, p1, p2):
        for d in self.devices:
            d.mirror(p1 = p1, p2 = p2)
        return self

    def add_ref(self, devices):    
        refs = []
        for a, b in zip(self.devices, devices.devices):        
            refs.append(a.add_ref(b))
        return refs # device, metal, pocket

    @property
    def xmin(self):
        return self.device.xmin

    @xmin.setter
    def xmin(self, value):
        dx = value - self.xmin
        self.movex(dx) 

    @property
    def xmax(self):
        return self.device.xmax

    @xmax.setter
    def xmax(self, value):
        dx = value - self.xmax
        self.movex(dx) 

    @property
    def ymin(self):
        return self.device.ymin

    @ymin.setter
    def ymin(self, value):
        dy = value - self.ymin
        self.movey(dy) 

    @property
    def ymax(self):
        return self.device.ymax

    @ymax.setter
    def ymax(self, value):
        dy = value - self.ymax
        self.movey(dy) 

    @property
    def x(self):
        return self.device.x

    @x.setter
    def x(self, value):
        dx = value - self.x
        self.movex(dx) 

    @property
    def y(self):
        return self.device.y

    @y.setter
    def y(self, value):
        dy = value - self.y
        self.movey(dy) 

    @property
    def center(self):
        return self.device.center
    
    @center.setter
    def center(self, value):
        dist = value - self.center
        self.move(dist)