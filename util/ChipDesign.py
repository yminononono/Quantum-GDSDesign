import sys, copy
from qubit_templates import *
from functions import *

def deep_set(config, path, value, sep=":"):
    keys = path.split(sep)
    *parents, last = keys
    cur = config
    for k in parents:
        if k.isdecimal():
            k = int(k)
        cur = cur[k]
    if last.isdecimal():
        last = int(last)
    cur[last] = value

def init_chipdesign(config, param_x, param_y, x, y):

    # param_x
    if (param_x is None):
        pass
    elif type(param_x) is list:
        for par, var in zip(param_x, x):
            if ":" in par:
                deep_set(config, par, var)
            else:
                config[par] = var
    elif ":" in param_x:
        deep_set(config, param_x, x)
    elif ((param_x in config) or (param_x == "dummy")):
        config[param_x] = x
    else:
        raise ValueError(f"{param_x} is not in config dictionary!!")
    
    # param_y    
    if (param_y is None):
        pass    
    elif type(param_y) is list:
        for par, var in zip(param_y, y):
            if ":" in par:
                deep_set(config, par, var)
            else:
                config[par] = var
    elif ":" in param_y:        
        deep_set(config, param_y, y)
    elif ((param_y in config) or (param_y == "dummy")):
        config[param_y] = y
    else:
        raise ValueError(f"{param_y} is not in config dictionary!!")


def sweep_chipdesign( config, userfunction = None ):

    def custom_design(n_level, param_x, param_y, x, y):
        
        init_chipdesign(config, param_x, param_y, x, y)

        # count_down
        n_level -= 1

        array = config["Grid_sweep_array"][n_level]

        if n_level == 0:
            if userfunction:
                function = userfunction
            else:
                function = globals()["chipdesign_" + config["Grid_name"]]
            param_defaults = { 'config' : config }
        else:
            function = custom_design
            param_defaults = { 'n_level' : n_level }
        param_defaults = {
            **param_defaults, 
            'param_x' : array["param_x"],
            'param_y' : array["param_y"],   
        }

        design = pg.gridsweep(
            function = function,
            param_x = {'x' : array["x"]},
            param_y = {'y' : array["y"]},
            param_defaults = param_defaults,
            spacing = (
                array["gap_x"] * config["Frame_size_width"], 
                array["gap_y"] * config["Frame_size_height"],
            ),
            # separation = False,
            label_layer = None
            )
        design.center = (0,0)
            
        return design
    

    if config["Grid_sweep_type"] == "array":
        devices = []
        for device in config["Grid_sweep_devices"]:
            updated_config = copy.copy(config)
            for key in device:
                updated_config[key] = device[key]
            devices.append( globals()["chipdesign_" + config["Grid_name"]](updated_config) )
        devices.append( globals()["chipdesign_" + config["Grid_name"]](updated_config, only_frame = True) )
        device_list = []
        for row in config["Grid_sweep_array"]:
            for cell in row:
                if cell is None:
                    device_list.append( devices[-1] )
                else:
                    device_list.append( devices[cell] )
        D = pg.grid(
            device_list,
            spacing = (config["Grid_sweep_gap_x"] * config["Frame_size_width"], config["Grid_sweep_gap_y"] * config["Frame_size_height"]),
            shape = np.array(config["Grid_sweep_array"], dtype=object).shape
        )
    elif config["Grid_sweep_type"] == "gridsweep":
        n_level = len(config["Grid_sweep_array"]) - 1
        array = config["Grid_sweep_array"][n_level]

        if n_level == 0:
            if userfunction:
                function = userfunction
            else:
                function = globals()["chipdesign_" + config["Grid_name"]]
            param_defaults = { 'config' : config }
        else:
            function = custom_design
            param_defaults = { 'n_level' : n_level }
        param_defaults = {
            **param_defaults, 
            'param_x' : array["param_x"],
            'param_y' : array["param_y"],   
        }

        D = pg.gridsweep(
            function = function,
            param_x = {'x' : array["x"]},
            param_y = {'y' : array["y"]},
            param_defaults = param_defaults,
            spacing = (
                array["gap_x"] * config["Frame_size_width"], 
                array["gap_y"] * config["Frame_size_height"],
            ),
            label_layer = None
        )
    else:
        raise ValueError("Incorrect Grid_sweep_type !!")

    return D

def chipdesign_Test(config, param_x, param_y, x, y):

    init_chipdesign(config, param_x, param_y, x, y)

    chipdesign = Device('chipdesign')

    # Frame
    FM=Device('frame')
    rectangle = pg.rectangle((Frame_size_width, Frame_size_height), Frame_layer)
    FM.add_ref( pg.invert(rectangle, border = Frame_width, precision = 1e-6, layer = Frame_layer) )
    FM.center = (0, 0)
    chipdesign.add_ref(FM)

    return chipdesign


def chipdesign_transmon3D(config, param_x = None, param_y = None, x = None, y = None, only_frame = False):

    init_chipdesign(config, param_x, param_y, x, y)

    chipdesign = Device('chipdesign')

    FM = device_Frame(config)
    
    if only_frame or ((param_x is not None and x is None) or (param_y is not None and y is None)):
        chipdesign.add_ref(FM)
        return chipdesign

    PAD=Device('PAD')
    rectangle = pg.rectangle(( config["Pad_width"], config["Pad_height"]), config["Pad_layer"])
    rectangle.polygons[0].fillet( config["Pad_rounding"] )
    PAD.add_ref( rectangle ).movex(0).movey(0.5*config["Pad_gap"])
    PAD.add_ref( rectangle ).mirror(p1 = (0, 0), p2 = (200, 0)).movex(0).movey(-0.5*config["Pad_gap"])
    PAD.center = (0, 0)

    chipdesign.add_ref(PAD)

    JJ       = device_JJ({**config, **dict(JJ_squid = False)})          
    JJ_squid = device_JJ({**config, **dict(JJ_squid = True)})  
    if config["JJ_squid"]:
        chipdesign.add_ref(JJ_squid)
    else:
        chipdesign.add_ref(JJ)

    chipdesign = pg.union( chipdesign, layer = config["Pad_layer"] )
    for pol in chipdesign.polygons: # unions are separated in dolan structure, so loop through all polygons
        pol.fillet( config["Pad_JJ_rounding"] )
    chipdesign = pg.union( chipdesign, layer = config["Pad_layer"] )

    text = eval(config["Text_string"], {"width": x, "height": y})
    move_x = config["Text_pos_x"]*0.5*config["Frame_size_width"]
    move_y = config["Text_pos_y"]*0.5*config["Frame_size_height"]    

    T = pg.text(text, size=config["Text_size"], layer = config["Text_layer"])
    T.center=(0,0)
    T.move([move_x,move_y])
    chipdesign.add_ref(T)

    TA = Device('TestArea')
    rectangle = pg.rectangle(( config["TestPoint_box_width"], config["TestPoint_box_length"]), config["TestPoint_layer"])
    rectangle.polygons[0].fillet( config["TestPoint_box_rounding"] )
    TA.add_ref( rectangle ).movex(0).movey(0.5*config["TestPoint_gap"])
    TA.add_ref( rectangle ).mirror(p1 = (0, 0), p2 = (200, 0)).movex(0).movey(-0.5*config["TestPoint_gap"])
    TA.center = (0, 0)  
    TA_squid = pg.copy(TA)  
    TA_squid.add_ref(JJ_squid)
    TA_squid.movex(4*config["TestPoint_box_width"])
    TA.add_ref(JJ)
    TA.add_ref(TA_squid)
    TA.center = (0,0)
    
    move_x = config["TestPoint_pos_x"]*0.5*config["Frame_size_width"]
    move_y = config["TestPoint_pos_y"]*0.5*config["Frame_size_height"]   
    TA.move([move_x, move_y])
    TA = pg.union(TA, layer = config["TestPoint_layer"])     
    chipdesign.add_ref(TA)

    chipdesign.add_ref(FM)
    return chipdesign


def chipdesign_TcSample(config, param_x = None, param_y = None, x = None, y = None, only_frame = False):

    init_chipdesign(config, param_x, param_y, x, y)

    chipdesign = Device('chipdesign')

    # Frame
    FM = device_Frame(config)
    chipdesign.add_ref(FM)

    if only_frame or ((param_x is not None and x is None) or (param_y is not None and y is None)):
        return chipdesign

    # Feed line
    FL = device_FeedLine(config)
    chipdesign.add_ref(FL.device)

    # Corner points
    CP = device_CornerPoints(config)
    chipdesign.add_ref(CP)

    # Resonator
    R = []
    # print(config["Resonator_devices"][0]["norm_to_frequency"])
    for i, resonator_config in enumerate(config["Resonator_devices"]):
        R.append( device_Resonator(config, **resonator_config) )
        R[i].rotate(resonator_config["angle"])

        if config["FeedLine_path_type"] == "straight":
            R[i].xmin = FL.device.x + 0.5*config["LaunchPad_trace_width"] + config["LaunchPad_trace_gap_width"] + resonator_config["feedline_gap"]
            R[i].y = resonator_config["y"]
        elif config["FeedLine_path_type"] == "manual":
            R[i].xmin = config["FeedLine_path_points"][resonator_config["x_pathpoint"]][0] + 0.5*config["LaunchPad_trace_width"] + config["LaunchPad_trace_gap_width"] + resonator_config["feedline_gap"]
            R[i].y = resonator_config["y"]
        elif config["FeedLine_path_type"] == "extrude":
            sys.exit("Currently I don't know how to extract the right position to place the resonators...")
        chipdesign.add_ref(R[i].device)

    return chipdesign