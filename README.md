# Scaling_Python

Jupyter notebook I used in my scaling up Python Meetup talk. Below are the command lines to create a conda environment that can run this notebook (including the jupyter lab extensions). I work almost exclusively with Conda so I'm afraid I don't know the setup for pip but all these packages (bar rapids) can be installed with pip if you check the instructions on the corresponding PyPi or GitHub sites.

## Conda Environment (if you have Linux and a recent NVidia GPU - to run everything including the CuDF example)

conda create -n scaling -c rapidsai -c nvidia -c conda-forge -c anaconda -c defaults rapids python cudatoolkit jupyterlab pandas black dask-labextension jupyterlab_code_formatter matplotlib vaex jupyterlab-nvdashboard

jupyter labextension install @jupyter-widgets/jupyterlab-manager @ryantam626/jupyterlab_code_formatter dask-labextension jupyterlab-nvdashboard

jupyter serverextension enable --py jupyterlab_code_formatter

jupyter serverextension enable dask_labextension

## Conda Environment for every other example (will work on Windows, Mac, and Linux)

conda create -n scaling -c conda-forge -c anaconda -c defaults python jupyterlab pandas black dask-labextension jupyterlab_code_formatter matplotlib vaex

jupyter labextension install @jupyter-widgets/jupyterlab-manager @ryantam626/jupyterlab_code_formatter dask-labextension

jupyter serverextension enable --py jupyterlab_code_formatter

jupyter serverextension enable dask_labextension
