# Quantum GDS Design

Scripts used to produce gds designs with the [PHIDL](https://phidl.readthedocs.io/en/latest/index.html) package are placed in this repository.
There are other packages such as [gdsfactory](https://gdsfactory.github.io/gdsfactory/index.html) and [gdstk](https://heitzmann.github.io/gdstk/) which use similar syntax.

1. [Install](#Install)
2. [Functions](#Functions)


## Install

### Conda environment

Use the conda environment to install the phidl package and other useful packages.  
[Link](https://github.com/conda-forge/phidl-feedstock) to some instructions.

```
$ conda config --add channels conda-forge
$ conda config --set channel_priority strict
$ conda create -n phidl python=3.11 
$ conda activate phidl
$ conda install phidl
$ conda install matplotlib
$ conda install pyyaml
$ conda install scipy
```

## Functions

Functions are summarized in the ```util/qubit_templates.py``` file.

|    Function name    |                   Description                   |
| :------------------ | :---------------------------------------------- |
| device_Wafer        | Return wafer design                             |
| device_LaunchPad    | Return launch pad design                        |
| device_FeedLine     | Return feed line which connects two launch pads |
| device_CornerPoints | Return boxes placed in the corners              |
| device_TestAreas    | Return areas to place test JJs                  |
| device_Resonator    | Return resonator design                         |

## Designs for qiskit-metal

The BaseDevice class in ```util/BaseDevice.py``` is used to produce designs for qiskit-metal.
Users need to provide the following designs.

1. device : Lithography area.
2. pocket : Area which includes the lithography and gap area.
3. metal  : Area which will be evaporated with metal. The area does not include the ground plane. The metal area is usually produced by subtracting the pocket area by the device area.

The BaseDevice class has its own functions to move and rotate all of the designs at the same time.

The device functions inherit the BaseDevice class.
After making the objects, you can pass them to the ```phidl_to_metal()``` function to produce gds and yaml files.
These files can be processed by qiskit-metal to produce your own QComponents and can be easily passed to HFSS simulations.

```python
device_list = [
    dict(device = FL, name = "FeedLine"),
    dict(device = R1, name = "Resonator1"),    
    dict(device = R2, name = "Resonator2"),
]

phidl_to_metal(
    device_list = device_list, 
    outname = "TcSampleDesign"
)
```

After converting PHIDL to qiskit-metal designs, you can find the output files under ```output/qiskit-metal/```.