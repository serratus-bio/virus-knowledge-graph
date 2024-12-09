
## 1. Set up new env with conda or virtualenv 

- (Conda) `conda create --name {myenv}`
- (virtualenv) `virtualenv {myenv}`

## 2. Activate env

- (Conda) `conda activate {myenv}`
- (virtualenv) `source {myenv}/bin/activate`

## 3. Install container requirements and notebook specific requirements

- `pip3 install -r ../requirements.txt`
- `pip3 install -r ./requirements.txt`

## 4. Set up jupyter kernel using virtual env

- (conda) https://stackoverflow.com/questions/58068818/how-to-use-jupyter-notebooks-in-a-conda-environment
- (virtualenv) https://stackoverflow.com/questions/37891550/jupyter-notebook-running-kernel-in-different-env

## 5. Select kernel inside jupyter notebook

- Note: Might need to reboot before kernel appears in dropdown
- Note: In VSCode, make sure workspace directory has access to virtual env folder

## 6. Add path to jupyter sys and read dotenv

```py
import sys

if '../' not in sys.path:
    sys.path.append("../")

%load_ext dotenv
%dotenv
```

## 7. Import local modules to use in notebook

---

# Installation on Boltzmann GPU cluster

```sh
conda remove -n rnalab --all
pip cache purge

conda create --name rnalab python=3.8 ipython
conda activate rnalab
conda install -y ipykernel
ipython kernel install --user --name=rnalab

conda install -y cuda -c nvidia
conda install -y cudatoolkit
conda install -y cudnn

nvcc --version

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -c "import torch; print(torch.__version__)"
#2.3.0+cu121
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.3.0+cu121.html
pip install -r requirements.txt
pip install faiss-gpu
```