import yaml
from scipy.special import ellipk
from scipy.constants import *
import math
import numpy as np

from phidl import quickplot as qp
from phidl import Device
import phidl.geometry as pg

# YAML 設定ファイルを読み込む関数
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    flat_data = flatten_dict(config)
    global_data = {f"{k}": v for k, v in flat_data.items()}

    return global_data

# 再帰的にフラットな変数名で辞書を展開
def flatten_dict(d, parent_key="", sep="_"):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def phidl_to_metal(device_list, outname):

    chipdesign_qiskit = Device('chipdesign_qiskit')
    chipdesign_qiskit_pocket = Device('chipdesign_qiskit_pocket')

    for ilayer, device in enumerate(device_list):
        pocket = device["device"].pocket
        metal  = device["device"].metal
        for i in pocket.get_layers():
            chipdesign_qiskit_pocket.add_ref( pg.copy_layer(pocket, layer = i, new_layer=ilayer) )
        for i in metal.get_layers():
            chipdesign_qiskit.add_ref( pg.copy_layer(metal, layer = i, new_layer=ilayer) )            

    chipdesign_qiskit = pg.union( chipdesign_qiskit, by_layer = True )
    chipdesign_qiskit_pocket = pg.union( chipdesign_qiskit_pocket, by_layer = True )
    chipdesign_qiskit.flatten()
    chipdesign_qiskit_pocket.flatten()
    qp(chipdesign_qiskit)
    qp(chipdesign_qiskit_pocket)
    chipdesign_qiskit.write_gds(f'output/qiskit-metal/{outname}.gds')
    chipdesign_qiskit_pocket.write_gds(f'output/qiskit-metal/{outname}_pocket.gds')


    # Dump port data
    data = {}
    for ilayer, device in enumerate(device_list):
        key =  device["name"]
        data[key] = dict(
            layer = ilayer
        )

        port_data = {}
        jj_data = {}        
        for port in device["device"].pocket.get_ports():
            if "LaunchPad" in str(port.name):
                name, gap = port.name.split('_')
                start, end = phidl_port_to_metal_pin(port)
                port_data[name] = dict(
                    start = start,
                    end   = end,
                    width = float(port.width),
                    gap   = float(gap),
                )
            elif port.name == "Junction_up":
                jj_data["start"] = [float(port.midpoint[0]), float(port.midpoint[1])]
            elif port.name == "Junction_down":
                jj_data["end"] = [float(port.midpoint[0]), float(port.midpoint[1])]           
                jj_data["width"] = float(port.width)

        if port_data:
            data[key]["ports"] = port_data
        if jj_data:
            data[key]["jj"] = jj_data            

    print(data)
    with open(f'output/qiskit-metal/{outname}.yaml', 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)

def extract_with_ports(device, layers_to_extract):

    print(device.get_ports())
    extracted = pg.extract(device, layers_to_extract)
    
    for port in device.get_ports():
        if port.name not in [x.name for x in extracted.get_ports()]:
            extracted.add_port(
                name=port.name, 
                midpoint=port.midpoint, 
                width=port.width, 
                orientation =port.orientation
            )
    
    return extracted

def boolean_with_ports(deviceA, deviceB, logic, layer):

    boolean = pg.boolean(deviceA, deviceB, logic, layer = layer)
    
    for port in deviceA.get_ports() + deviceB.get_ports():
        if port.name not in [x.name for x in boolean.get_ports()]:
            boolean.add_port(
                name=port.name, 
                midpoint=port.midpoint, 
                width=port.width, 
                orientation =port.orientation
            ) 

    return boolean

def phidl_port_to_metal_pin(port):
    x0, y0 = port.midpoint
    theta_rad = np.deg2rad(port.orientation + 90)  # orientationに90度足す（垂直方向）

    dx = (port.width / 2) * np.cos(theta_rad)
    dy = (port.width / 2) * np.sin(theta_rad)

    point1 = [float(x0 + dx), float(y0 + dy)]
    point2 = [float(x0 - dx), float(y0 - dy)]

    return point1, point2

def calculate_resonator_frequency(
        length = 3000, # um
        core_width = 10, # um
        gap_width = 6, # um
        height = 525, # um
        material = "silicon"
        ):

    # convert um to m
    l = length * 1e-6
    w = core_width * 1e-6
    s = gap_width * 1e-6
    h = height * 1e-6

    if material == "silicon":
        eps_r = 11.9
        #eps_r = 11.45
    elif material == "sapphire":
        eps_r = 9.4
    else:
        ValueError()

    k0 = w/(w + 2*s)
    k0_prime = math.sqrt(1-pow(k0, 2))
    k3 = math.tanh((math.pi*w)/(4*h))/math.tanh((math.pi*(w+2*s))/(4*h))
    k3_prime = math.sqrt(1-pow(k3, 2))
    K_k0 = ellipk(k0**2)
    K_k0_prime=ellipk(k0_prime**2)
    K_k3 = ellipk(k3**2)
    K_k3_prime=ellipk(k3_prime**2)
    K_tilde = (K_k0_prime/K_k0)*(K_k3/K_k3_prime)
    eps_eff = (1 + eps_r * K_tilde)/(1 + K_tilde)
    #eps_eff = 0.5*(1 + eps_r)
    print("eps_eff : ", eps_eff)
    c_eff = c / math.sqrt(eps_eff)
    f = c_eff / (4*l)

    return f