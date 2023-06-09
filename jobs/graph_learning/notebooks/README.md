
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

- Note, might need to reboot before kernel appears in dropdown.

## 6. Add path to jupyter sys and read dotenv

```py
import sys

if '../' not in sys.path:
    sys.path.append("../")

%load_ext dotenv
%dotenv
```

## 7. Import local modules to use in notebook