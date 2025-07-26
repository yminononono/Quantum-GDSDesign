import yaml
from scipy.special import ellipk
from scipy.constants import *
import math

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