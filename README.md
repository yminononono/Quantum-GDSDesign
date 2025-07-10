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
