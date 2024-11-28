import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import constants as const
from phidl import quickplot as qp
from phidl import Device
from phidl import CrossSection
from phidl import Path
import phidl.geometry as pg
import phidl.routing as pr
import phidl.path as pp

def device_Wafer(inch = 4):
    wafer = Device('wafer')
    wafer_radius = 0.5 * inch * 25.4 * 1e3 # inch to um
    circle = pg.circle(radius = wafer_radius, angle_resolution = 2.5, layer = 21)
    inv_circle = pg.invert(circle, border = 7000, precision = 1e-6, layer = 21)
    wafer.add_ref( inv_circle )
    return wafer

def device_LaunchPad():
    LP=Device('launchpad')

    # LP oriented in x direction (x = length, y = width)
    pad_length = 300
    pad_width = 200
    padgap_length = 400
    padgap_width = 500

    trace_length = 200
    trace_width = 20
    tracegap_length = 200
    tracegap_width = 42

    components = {}
    components["pad"] = pg.rectangle(size = (pad_length, pad_width)).movey(-0.5*pad_width)
    components["padgap"] = pg.rectangle(size = (padgap_length, padgap_width)).movey(-0.5*padgap_width)
    components["pad"] = pg.boolean(components["padgap"], components["pad"], 'not', layer = 4)
    components["pad"].add_port(name = 'out', midpoint = [0., 0.], width = padgap_width, orientation = 180)

    components["trace"]    = pg.taper(length = trace_length,    width1 = pad_width, width2 = trace_width, port = None, layer = 0)
    components["tracegap"] = pg.taper(length = tracegap_length, width1 = padgap_width, width2 = tracegap_width, port = None, layer = 4)
    components["trace"] = pg.boolean(components["tracegap"], components["trace"], 'not', layer = 4)
    components["trace"].add_port(name = 'out', midpoint = [0., 0.], width = padgap_width, orientation = 180)

    components["trace"] = LP.add_ref( components["trace"] )
    components["pad"] = LP.add_ref( components["pad"] )

    components["trace"].connect(port = 'out', destination = components["pad"].ports['out'])
    # components["pad"].connect(port = 'out', destination = components["padgap"].ports['out'])

    LP.add_port(name = 'out', midpoint = [-trace_length, 0.], width = tracegap_width, orientation = 180)
    LP.center = (0,0)

    return LP

def device_FeedLine():
    # make 2 pads
    FL = Device("feedline")
    LP_in = pg.copy(device_LaunchPad())
    LP_in.move((750, 2025))
    LP_out = pg.copy(device_LaunchPad())
    LP_out.rotate(90).move((1950, 800))
    FL.add_ref(LP_in)
    FL.add_ref(LP_out)

    X = CrossSection()
    X.add(width=11, offset = 10 + 5.5, layer = 4)
    X.add(width=11, offset = -10 - 5.5, layer = 4)
    D3 = pr.route_smooth(LP_in.ports['out'], LP_out.ports['out'], width = X, radius=100, path_type='J', length1=790, length2=768, smooth_options={'corner_fun': pp.arc})
    FL.add_ref(D3)
    return FL

def device_DCLine():
    DC = Device("DCLine")
    LP_in = DC.add_ref( device_LaunchPad() )
    LP_in.move((1950, -1300))

    dcline_radius = 100
    dcline_width = 20
    dcline_gap_width = 5.5

    P = Path()
    left_turn = pp.arc(radius = dcline_radius, angle = 90)
    right_turn = pp.arc(radius = dcline_radius, angle = -90)
    straight1 = pp.straight(length = 235)
    straight2 = pp.straight(length = 805)
    straight3 = pp.straight(length = 2973)
    straight4 = pp.straight(length = 2960)

    P.append([
        straight1,
        left_turn,
        straight2,
        right_turn,
        straight3,
        right_turn,
        straight4,
    ])

    X = CrossSection()
    X.add(width=dcline_width, offset = 0., layer = 1)
    X.add(width=11, offset = 0.5*dcline_width + dcline_gap_width, layer = 4)
    X.add(width=11, offset = -0.5*dcline_width - dcline_gap_width, layer = 4)

    DCLine_device = P.extrude(X)
    DCLine_device.add_port(name = 'out', midpoint = [0., 0.], width = dcline_width, orientation = 180)

    DCLine_device = DC.add_ref( DCLine_device )
    DCLine_device.connect(port = 'out', destination = LP_in.ports['out'])

    return DC

def device_CornerPoints(point_pos = [(2150,2150),(-2150,2150),(-2150,-2150),(2150,-2150)]):
    CP = Device("CornerPoints")
    box_width = 10
    box_gap_width = 20
    rectangle = pg.rectangle( (box_width, box_width), layer = 4)
    CornerPoint = pg.invert(rectangle, border = box_gap_width, precision = 1e-6, layer = 4)
    for center in point_pos:
        cp = CP.add_ref( CornerPoint )
        cp.center = center
    return CP

def device_TestAreas(DCLine = False):

    if DCLine:
        point_pos = [(-1493.5, -1181.413), (-1493.5, -1831.408), (-843.5, -1181.413), (-843.5, -1831.408)]
    else:
        point_pos = [(-1743.5, -1231.413), (-1743.5, -1881.408), (-1093.5, -1231.413), (-1093.5, -1881.408)]

    TPs = Device("TestPoints")
    TP = Device("TestPoint")    
    box_width = 279
    box_length = 135
    box_gap_width = 27
    box = pg.bbox([(-0.5*box_width,-box_length),(0.5*box_width,0)], layer = 4)
    box = pg.invert(box, border = box_gap_width, precision = 1e-6, layer = 4)

    stub_width = 18
    stub_length = 68.4
    stub = pg.bbox([(-0.5*stub_width, 0),(0.5*stub_width, stub_length)], layer = 4)
    box = pg.boolean(box, stub, 'not', layer = 4)
    TP.add_ref(box)

    stub_gap_width = 18
    stub_gap_length = 14.4    

    polpoints = [
        ( -0.5*stub_width-stub_gap_width, box_gap_width                 ),
        ( -0.5*stub_width-stub_gap_width, stub_length + stub_gap_length ),
        (  0.5*stub_width+stub_gap_width, stub_length + stub_gap_length ),
        (  0.5*stub_width+stub_gap_width, box_gap_width                 ),
        (  0.5*stub_width               , box_gap_width                 ),
        (  0.5*stub_width               , stub_length                   ),
        (  -0.5*stub_width              , stub_length                   ),
        (  -0.5*stub_width              , box_gap_width                 ),
    ]
    TP.add_polygon(polpoints)
    TP = pg.union(TP, by_layer = False, layer = 4)
    qp(TP)

    for center in point_pos:
        tp = TPs.add_ref( TP )
        tp.xmin = center[0] - 0.5*box_width - box_gap_width
        tp.ymin = center[1] - 0.5*box_length - box_gap_width

    return TPs

def device_TestBoxes(DCLine = False):

    if DCLine:
        point_pos = [(-1493.5, -1181.413), (-1493.5, -1831.408), (-1493.5, -1500.0), (-843.5, -1181.413), (-843.5, -1831.408), (-843.5, -1500.0)]
    else:
        point_pos = [(-1743.5, -1231.413), (-1743.5, -1881.408), (-1743.5, -1550), (-1093.5, -1231.413), (-1093.5, -1881.408), (-1093.5, -1550)]

    TBXs = Device("TestBoxes")
    TBX = Device("TestBox")
    box_size = 45
    box1 = pg.rectangle((box_size, box_size), layer = 1)
    box2 = pg.copy_layer(box1, 1, 2)
    TBX.add_ref(box1)
    TBX.add_ref(box2)

    for center in point_pos:
        tbx = TBXs.add_ref( TBX )
        tbx.center = center

    return TBXs

def device_Resonator(resonator_straight1 = 240, resonator_straight2 = 290, resonator_straight3 = 475, resonator_straight4 = 1400, side = False):
    Resonator = Device("resonator")
    
    resonatorgap_width = 6
    resonator_width = 10
    resonator_radius = 75

    pad_width = 700
    pad_length = 700

    P = Path()
    left180_turn = pp.arc(radius = resonator_radius, angle = 180)
    right180_turn = pp.arc(radius = resonator_radius, angle = -180)
    # left_turn = pp.euler(radius = resonator_radius, angle = 90)
    # right_turn = pp.euler(radius = resonator_radius, angle = -90)
    left_turn = pp.arc(radius = resonator_radius, angle = 90)
    right_turn = pp.arc(radius = resonator_radius, angle = -90)
    straight1 = pp.straight(length = resonator_straight1)
    straight2 = pp.straight(length = resonator_straight2)
    straight3 = pp.straight(length = resonator_straight3)
    straight4 = pp.straight(length = resonator_straight4)
    straight5 = pp.straight(length = 250)

    if side:
        P.append([
            straight5,
            right_turn,
            straight4,
            right_turn,
            straight3,
            right180_turn,
            straight2,
            left180_turn,
            straight2,
            right180_turn,
            straight2,
            left180_turn,   
            straight1,
        ])
    else:
        P.append([
            straight4,
            right_turn,
            straight3,
            right180_turn,
            straight2,
            left180_turn,
            straight2,
            right180_turn,
            straight2,
            left180_turn,   
            straight1,
        ])

    # Create a blank CrossSection
    X = CrossSection()

    # Add a a few "sections" to the cross-section
    X.add(width=resonator_width, offset = 0., layer = 1)
    X.add(width=resonatorgap_width, offset = 0.5*(resonator_width + resonatorgap_width), layer = 4)
    X.add(width=resonatorgap_width, offset = -0.5*(resonator_width + resonatorgap_width), layer = 4)
    
    # Combine the Path and the CrossSection
    waveguide_device = P.extrude(X)
    waveguide_device.add_port(name = 'out', midpoint = [0., 0.], width = resonator_width, orientation = 180)
    waveguide_device.rotate(90)
    waveguide_device.movex(-(resonator_straight1+resonator_radius))

    # capacitor (resonator -> qubit)
    cap_gap1 = 15
    cap_width = 50
    cap_length = 10
    stub_width = resonator_width
    stub_length = 2*resonator_width
    cap = pg.tee(size = (cap_width,cap_length), stub_size = (stub_width,stub_length), taper_type = 'fillet', layer = 0)
    line = pg.bbox([(-0.5*stub_width, -pad_length),(0.5*stub_width, 0)])
    cap = pg.boolean(cap, line, 'or', layer = 4)

    # capacitor (qubit)
    cap_gap2 = 16
    cap_width2 = 540
    cap_length2 = 50
    cap_qubit_up = pg.compass_multi(size = (cap_width2, cap_length2), ports = {'N':3,'S':3}, layer = 0)
    cap_qubit_down = pg.compass_multi(size = (cap_width2, cap_length2), ports = {'N':3,'S':3}, layer = 0)

    cap_qubit_down.ymin = cap.ymax + cap_gap1
    cap_qubit_up.ymin = cap_qubit_down.ymax + cap_gap2

    # Subtract from pad
    pad = pg.bbox([(-0.5*pad_width, -0.5*pad_length),(0.5*pad_width, 0.5*pad_length)])
    pad.movey(cap_length + cap_gap1 + cap_length2 + 0.5*cap_gap2)
    pad = pg.boolean(pad, cap, 'not', layer = 4)
    pad = pg.boolean(pad, cap_qubit_up, 'not', layer = 4)    
    pad = pg.boolean(pad, cap_qubit_down, 'not', layer = 4)        

    pad.add_port(name = 'out', midpoint = [0., -stub_width], width = stub_width, orientation = 270)

    print(f"Length : {P.length()} [um]")

    s, K = P.curvature()
    plt.plot(s, K, ".-")
    plt.xlabel("Position along curve (arc length)")
    plt.ylabel("Curvature")

    # Quickplot the resulting Device
    pad = Resonator.add_ref(pad)
    waveguide_device = Resonator.add_ref(waveguide_device)

    pad.connect(port = 'out', destination = waveguide_device.ports['out'])

    return Resonator

def device_JJ( width = 0.135, JJtype = "manhattan", squid = False, bandage = True):
    JJ=Device('JJ')
    JJ_half=Device('JJ_half')

    finger_layer = 1
    box_layer = 2

    if JJtype == "manhattan" and bandage:
        box_finger_overlay_outer = 0.68
        box_finger_overlay_inner = 0.18

        box_outer_width = 1.8
        finger_width_outer1 = 0.405
        finger_length_outer1 = 13.7

        finger_width_outer2 = 0.315
        finger_length_outer2 = 3.6

        finger_width_inner1 = 0.315
        finger_length_inner1 = 4.5

        finger_width_inner2 = width
        finger_length_inner2 = 4.2

        box_inner_width = 0.9

        box_outer = pg.rectangle((box_outer_width, box_outer_width), box_layer)
        box_outer.movex(-box_outer.center[0])
        box_outer.add_port(name = 'out', midpoint = [0, box_finger_overlay_outer], width = finger_width_outer1, orientation = 270)
        # rectangle_subtract = pg.rectangle((finger_width_outer1, box_finger_overlay_outer), box_layer)
        # rectangle_subtract.movex(-rectangle_subtract.center[0])
        # box_outer = pg.boolean(A = box_outer, B = rectangle_subtract, operation = 'not', precision = 1e-6, num_divisions = [1,1], layer = box_layer)

        # finger
        finger_outer1 = pg.rectangle((finger_width_outer1, finger_length_outer1), finger_layer)
        finger_outer1.movex(-finger_outer1.center[0])
        finger_outer1.add_port(name = 'in', midpoint = [0, finger_length_outer1], width = finger_width_outer1, orientation = 90)
        finger_outer1.add_port(name = 'out', midpoint = [0, 0], width = finger_width_outer1, orientation = 270)

        finger_outer2 = pg.rectangle((finger_width_outer2, finger_length_outer2), finger_layer)
        finger_outer2.movex(-finger_outer2.center[0])
        finger_outer2.add_port(name = 'in', midpoint = [0, finger_length_outer2], width = finger_width_outer2, orientation = 90)
        finger_outer2.add_port(name = 'out', midpoint = [0, 0], width = finger_width_outer2, orientation = 270)

        finger_inner1 = pg.rectangle((finger_width_inner1, finger_length_inner1), finger_layer)
        finger_inner1.movex(-finger_inner1.center[0])
        finger_inner1.add_port(name = 'in', midpoint = [0, finger_length_inner1], width = finger_width_inner1, orientation = 90)
        finger_inner1.add_port(name = 'out', midpoint = [0, 0], width = finger_width_inner1, orientation = 270)

        finger_inner2 = pg.rectangle((finger_width_inner2, finger_length_inner2), finger_layer)
        finger_inner2.movex(-finger_inner2.center[0])
        finger_inner2.add_port(name = 'in', midpoint = [0, finger_length_inner2], width = finger_width_inner2, orientation = 90)
        finger_inner2.add_port(name = 'out', midpoint = [0, 0], width = finger_width_inner2, orientation = 270)

        # inner box (x 3)
        box_inner = pg.rectangle((box_inner_width, box_inner_width), box_layer)
        box_inner.movex(-box_inner.center[0])
        box_inner.add_port(name = 'out', midpoint = [0, box_finger_overlay_inner], width = finger_width_inner1, orientation = 270)

        box_outer = JJ_half.add_ref( box_outer )
        finger_outer1 = JJ_half.add_ref( finger_outer1 )
        finger_outer2 = JJ_half.add_ref( finger_outer2 )
        box_inner1 = JJ_half.add_ref( box_inner )
        box_inner1.rotate(180)

        box_inner2 = JJ_half.add_ref( box_inner )
        box_inner2.rotate(45)
        box_inner2.center = (-1.5, -13.5)
        finger_inner1 = JJ_half.add_ref( finger_inner1 )
        finger_inner2 = JJ_half.add_ref( finger_inner2 )
        box_inner3 = JJ_half.add_ref( box_inner )

        finger_outer1.connect(port = 'in', destination = box_outer.ports['out'])
        finger_outer2.connect(port = 'in', destination = finger_outer1.ports['out'])
        box_inner1.connect(port = 'out', destination = finger_outer2.ports['out'])

        finger_inner1.connect(port = 'in', destination = box_inner2.ports['out'])
        finger_inner2.connect(port = 'in', destination = finger_inner1.ports['out'])
        box_inner3.connect(port = 'out', destination = finger_inner2.ports['out'])

        JJ.add_ref( JJ_half )
        JJ.add_ref( pg.copy(JJ_half).mirror(p1 = (-5, -18), p2 = (5, -18)) )
        if squid:
            JJ.add_ref( pg.copy(JJ).movex(-10) )
        JJ.center = (0,0)

    elif JJtype == "manhattan" and not bandage:
        pad_box_width = 18
        pad_box_length = 10
        pad_triangle_length = 16
        pad_rounding_radius = 2

        finger_width = width
        finger_length = 8

        box_width = 1.2
        box_finger_overlay = 0.24
        pad_finger_overlay = 2

        # make pad
        pad_box = pg.rectangle((pad_box_width, pad_box_length), finger_layer)
        pad_box.movex(-pad_box.center[0])
        pad_box.add_port(name = 'out', midpoint = [0, 0], width = pad_box_width, orientation = 270)
        pad_triangle = pg.taper(length = pad_triangle_length, width1 = pad_box_width, width2 = 0, port = None, layer = finger_layer)
        pad_triangle.add_port(name = 'out1', midpoint = [0.95*(pad_triangle_length-pad_rounding_radius), 0], width = pad_box_width, orientation = 45)
        pad_triangle.add_port(name = 'out2', midpoint = [0.95*(pad_triangle_length-pad_rounding_radius), 0], width = pad_box_width, orientation = -45)
        pad_box = JJ_half.add_ref( pad_box )
        pad_triangle = JJ_half.add_ref( pad_triangle )
        pad_triangle.connect(port = 1, destination = pad_box.ports['out'])
        JJ_half = pg.union(JJ_half, by_layer = False, layer = finger_layer)
        JJ_half.polygons[0].fillet( pad_rounding_radius )

        # make finger
        finger = pg.taper(length = finger_length + pad_finger_overlay, width1 = finger_width, width2 = finger_width, port = None, layer = finger_layer)
        finger.add_port(name = 'out1', midpoint = [pad_finger_overlay, 0], width = finger_width, orientation = 180)
        finger1 = JJ_half.add_ref( finger )
        finger1.connect(port = 'out1', destination = pad_triangle.ports['out1'])
        if squid:
            finger2 = JJ_half.add_ref( finger )        
            finger2.connect(port = 'out1', destination = pad_triangle.ports['out2'])

        # make box
        box = pg.rectangle((box_width, box_width), box_layer)
        box.movex(-box.center[0])
        box.add_port(name = 'out', midpoint = [0, box_finger_overlay], width = finger_width, orientation = 270)
        box1 = JJ_half.add_ref( box )
        box1.connect(port = 'out', destination = finger1.ports[2])
        if squid:
            box2 = JJ_half.add_ref( box )
            box2.connect(port = 'out', destination = finger2.ports[2])

        JJ.add_ref( JJ_half )
        JJ.add_ref( pg.copy(JJ_half).mirror(p1 = (-5, -18), p2 = (5, -18)) ) 
        JJ.center = (0,0)

    if JJtype == "dolan" and bandage:
        finger_width = 0.2
        finger_length = 1.5

        bridge_width = width
        bridge_length = 2.0

        bridge_finger_overlay = 0.8
        bridge_pad_overlay = 0.42

        pad_width = 2
        pad_length = 16

        bandage_gap = 0.65
        bandage1_width = 0.2
        bandage1_length = 3.0
        bandage2_width = 0.45
        bandage2_length = 3.2

        nbandage = 4

        finger = pg.bbox([(-0.5*finger_width, -finger_length), (0.5*finger_width, 0)], finger_layer)
        finger.add_port(name = 'finger_bridge', midpoint = [0, 0], width = finger_width, orientation = 90)
        finger.add_port(name = 'finger_pad', midpoint = [0, -finger_length], width = finger_width, orientation = 270)

        bridge = pg.rectangle((bridge_width, bridge_length), box_layer)
        bridge.add_port(name = 'bridge_finger', midpoint = [0.5*bridge_width, bridge_finger_overlay] , width = finger_width, orientation = 270)
        bridge.add_port(name = 'bridge_pad', midpoint = [0.5*bridge_width, bridge_length - bridge_pad_overlay] , width = finger_width, orientation = 90)        

        pad = pg.rectangle((pad_width, pad_length), finger_layer)
        pad.add_port(name = 'out', midpoint = [0.5*pad_width, 0], width = pad_width, orientation = 270)
        for i in range(nbandage):
            pad.add_port(name = f'bandage{i}', midpoint = [0.5*pad_width, pad_length - (i+1)*bandage_gap - (i + 0.5)*bandage2_width], width = bandage2_width, orientation = 0)

        bandage1 = pg.rectangle((bandage1_width, bandage1_length), finger_layer)
        bandage2 = pg.rectangle((bandage2_width, bandage2_length), box_layer)
        bandage1.add_port(name = 'bandage1_pad', midpoint = [0.5*bandage1_width, 0], width = bandage1_width, orientation = 270)
        bandage2.add_port(name = 'bandage2_pad', midpoint = [0.5*bandage2_width, 0], width = bandage2_width, orientation = 270)

        finger = JJ_half.add_ref( finger )
        bridge = JJ_half.add_ref( bridge )
        pad_up = JJ_half.add_ref( pad )
        pad_down = JJ_half.add_ref( pad )
        pad_down.mirror(p1 = (0,0), p2 = (0, -5)) 

        bandage1_up = []
        bandage2_up = []        
        bandage1_down = []
        bandage2_down = []        
        for i in range(nbandage):
            bandage1_up.append( JJ_half.add_ref(bandage1) )
            bandage2_up.append( JJ_half.add_ref(bandage2) )            
            bandage1_down.append( JJ_half.add_ref(bandage1) )
            bandage2_down.append( JJ_half.add_ref(bandage2) )                        

        bridge.connect(port = 'bridge_finger', destination = finger.ports['finger_bridge'])
        pad_up.connect(port = 'out', destination = bridge.ports['bridge_pad'])
        pad_down.connect(port = 'out', destination = finger.ports['finger_pad'])

        for i in range(nbandage):
            bandage1_up[i].connect(port = 'bandage1_pad', destination = pad_up.ports[f'bandage{i}'])
            bandage2_up[i].connect(port = 'bandage2_pad', destination = pad_up.ports[f'bandage{i}'])            
            bandage1_down[i].connect(port = 'bandage1_pad', destination = pad_down.ports[f'bandage{i}'])
            bandage2_down[i].connect(port = 'bandage2_pad', destination = pad_down.ports[f'bandage{i}'])                        

        JJ.add_ref( JJ_half )
        if squid:
            JJ.add_ref( pg.copy(JJ).movex(-10) )
        JJ.center = (0,0)

    if JJtype == "dolan" and not bandage:
        finger_width = 0.2
        finger_length = 1.5

        bridge_width = width
        bridge_length = 2.0

        bridge_finger_overlay = 0.8
        bridge_pad_overlay = 0.42

        pad_box_width = 18
        pad_box_length = 10
        pad_triangle_length = 16
        pad_rounding_radius = 2
        pad_finger_dist = 4.5

        pad_inner_width = 2
        pad_inner_length = 16

        # make pad
        pad_box = pg.rectangle((pad_box_width, pad_box_length), finger_layer)
        pad_box.movex(-pad_box.center[0])
        pad_box.add_port(name = 'out', midpoint = [0, 0], width = pad_box_width, orientation = 270)
        pad_triangle = pg.taper(length = pad_triangle_length, width1 = pad_box_width, width2 = 0, port = None, layer = finger_layer)
        pad_triangle.rotate(-90)
        pad_outer = pg.boolean(A = pad_box, B = pad_triangle, operation = 'or',  precision = 1e-6, num_divisions = [1,1], layer = finger_layer)
        pad_outer.add_port(name = 'out', midpoint = [0, -(pad_triangle_length + pad_finger_dist)], width = pad_box_width, orientation = 270)
        pad_outer.polygons[0].fillet( pad_rounding_radius )
        
        pad_inner = pg.rectangle((pad_inner_width, pad_inner_length), finger_layer)
        pad_inner.add_port(name = 'out', midpoint = [0.5*pad_inner_width, 0], width = pad_inner_width, orientation = 270)

        finger = pg.bbox([(-0.5*finger_width, -finger_length), (0.5*finger_width, 0)], finger_layer)
        finger.add_port(name = 'finger_bridge', midpoint = [0, 0], width = finger_width, orientation = 90)
        finger.add_port(name = 'finger_pad', midpoint = [0, -finger_length], width = finger_width, orientation = 270)

        bridge = pg.rectangle((bridge_width, bridge_length), box_layer)
        bridge.add_port(name = 'bridge_finger', midpoint = [0.5*bridge_width, bridge_finger_overlay] , width = finger_width, orientation = 270)
        bridge.add_port(name = 'bridge_pad', midpoint = [0.5*bridge_width, bridge_length - bridge_pad_overlay] , width = finger_width, orientation = 90)        

        finger = JJ_half.add_ref( finger )
        bridge = JJ_half.add_ref( bridge )
        pad_inner_up = JJ_half.add_ref( pad_inner )
        pad_inner_down = JJ_half.add_ref( pad_inner )         
        pad_outer_up = JJ_half.add_ref( pad_outer )
        pad_outer_down = JJ_half.add_ref( pad_outer ) 

        bridge.connect(port = 'bridge_finger', destination = finger.ports['finger_bridge'])
        pad_inner_up.connect(port = 'out', destination = bridge.ports['bridge_pad'])
        pad_inner_down.connect(port = 'out', destination = finger.ports['finger_pad'])
        pad_outer_up.connect(port = 'out', destination = pad_inner_up.ports['out'])
        pad_outer_down.connect(port = 'out', destination = pad_inner_down.ports['out'])                             

        JJ.add_ref( JJ_half )
        if squid:
            JJ.add_ref( pg.copy(JJ).movex(-10) )
        JJ.center = (0,0)

    return JJ

def device_EBLine( width = 0.473 ):
    EBLine=Device('EBLine')

    finger_layer = 1
    box_layer = 2

    box_width = 2.7
    box_finger_overlay = 0.27

    finger_width_outer = 0.608
    finger_length_outer = 10.8

    finger_width_inner = width
    finger_length_inner = 16.2

    box = pg.rectangle((box_width, box_width), box_layer)
    box.movex(-box.center[0])
    box.add_port(name = 'out', midpoint = [0, box_finger_overlay], width = finger_width_outer, orientation = 270)

    # finger
    finger_outer = pg.rectangle((finger_width_outer, finger_length_outer), finger_layer)
    finger_outer.movex(-finger_outer.center[0])
    finger_outer.add_port(name = 'in', midpoint = [0, finger_length_outer], width = finger_width_outer, orientation = 90)
    finger_outer.add_port(name = 'out', midpoint = [0, 0], width = finger_width_outer, orientation = 270)

    finger_inner = pg.rectangle((finger_width_inner, finger_length_inner), finger_layer)
    finger_inner.movex(-finger_inner.center[0])
    finger_inner.add_port(name = 'in', midpoint = [0, finger_length_inner], width = finger_width_inner, orientation = 90)
    finger_inner.add_port(name = 'out', midpoint = [0, 0], width = finger_width_inner, orientation = 270)

    box_up = EBLine.add_ref( box )
    box_down = EBLine.add_ref( box )    
    finger_outer_up = EBLine.add_ref( finger_outer )
    finger_outer_down = EBLine.add_ref( finger_outer )
    finger_inner = EBLine.add_ref( finger_inner )

    finger_outer_up.connect(port = 'in', destination = box_up.ports['out'])
    finger_inner.connect(port = 'in', destination = finger_outer.ports['out'])
    finger_outer_down.connect(port = 'in', destination = finger_inner.ports['out'])
    box_down.connect(port = 'out', destination = finger_outer_down.ports['out'])

    EBLine.center = (0,0)
    return EBLine

def device_EBmarkers(marker_pos = [(0,0),(0,38400),(-19200,-28800),(38400,0), (0,-38400),(-19200,-38400),(-38400,0)],layer = 3):
    EBmarkers = Device("EBmarkers")
    EBmarker = Device("EBmarker")
    markers = {}
    tmp1 = pg.bbox([(-5,-20), (5,20)])
    tmp2 = pg.bbox([(-20,-5), (20,5)])
    markers["EBr1"] = pg.boolean(tmp1, tmp2, 'or', layer = layer)
    tmp1 = pg.bbox([(-40,-40), (40,40)])
    tmp2 = pg.bbox([(-30,-30), (30,30)])
    markers["EBr2"] = pg.boolean(tmp1, tmp2, 'not', layer = layer)

    markers["EBf1"] = pg.rectangle((10,10), layer)
    markers["EBf1"].move((-5,-5-200))
    markers["EBf2"] = pg.copy(markers["EBf1"]).rotate(90)
    markers["EBf3"] = pg.copy(markers["EBf1"]).rotate(180)
    markers["EBf4"] = pg.copy(markers["EBf1"]).rotate(270)


    markers["guide1"] = pg.rectangle((10,1850), layer)
    markers["guide1"].move((-5,500))
    markers["guide2"] = pg.copy(markers["guide1"]).rotate(90)
    markers["guide3"] = pg.copy(markers["guide1"]).rotate(180)
    markers["guide4"] = pg.copy(markers["guide1"]).rotate(270)

    # markers["EB_EPFL1"] = pg.rectangle((20,20), layer)
    # markers["EB_EPFL1"].move((-10,-10-2900))
    # markers["EB_EPFL2"] = pg.copy(markers["EB_EPFL1"]).rotate(90)
    # markers["EB_EPFL3"] = pg.copy(markers["EB_EPFL1"]).rotate(180)
    # markers["EB_EPFL4"] = pg.copy(markers["EB_EPFL1"]).rotate(270)

    for key in markers.keys():
        EBmarker.add_ref(markers[key])

    for ii in range(len(marker_pos)):
        marker = EBmarkers.add_ref(EBmarker)
        marker.center = marker_pos[ii]
    return EBmarkers

def device_Grid(inch = 4, n_gridline = 20):
    grid = Device("Grid")
    wafer_radius = 0.5 * inch * 25.4 * 1e3 # inch to um
    device_list = [pg.rectangle(size = (100, 2*wafer_radius), layer = 25) for i in range(n_gridline)]
    grid = pg.grid(device_list,
                spacing = (4800,0),
                separation = False,
                shape = (n_gridline,1))
    grid.center = (0, 0)
    circle = pg.circle(radius = wafer_radius, angle_resolution = 2.5, layer = 21)
    inv_circle = pg.invert(circle, border = 7000, precision = 1e-6, layer = 21)
    grid = pg.boolean(A = grid, B = inv_circle, operation = 'not', precision = 1e-6,
                num_divisions = [1,1], layer = 25)
    grid.add_ref( pg.copy(grid).rotate(90) )
    return grid