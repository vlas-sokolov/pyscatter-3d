import numpy as np
from pyscatter3d import pyscatter3d

X0,Y0 = np.meshgrid(np.linspace(-3,3,50), np.linspace(-3,3,50))
D = np.sqrt(X0**2+Y0**2) # radial distance
Z0 = np.sinc(D)

_ = np.random.randn(3, 1e3)
X1,Y1,Z1 = _/np.linalg.norm(_, axis=0)

np.savetxt('sinc.csv', np.array([arr.flatten() for arr in [X0,Y0,Z0,1/D]]).T,
           delimiter=',', header='X,Y,Z,inv_dist', comments='')

np.savetxt('sphere.csv', np.array([arr.flatten() for arr in [X1,Y1,Z1]]).T,
           delimiter=',', header='X,Y,Z', comments='')

csv_dir = '/home/vsokolov/Projects/g35.39/tables/'
# dataset names and their corresponding filenames
datasets = {'sinc'  : 'sinc.csv',
            'sphere': 'sphere.csv'}

# what column names to use as X/Y/Z values
which_x, which_y, which_z = 'X', 'Y', 'Z'
# which_s controls the marker size
which_s = 'inv_dist'

# output file name (without an extension)
outfile = 'example'

default_size = {'matplotlib': 30,              
                'plotly'    : 10 }

line2text  = {'sinc': 'sinc(x)', 'sphere': 'sphere' }
line2color = {'sinc': '#e41a1c', 'sphere': '#377eb8'}

# NOTE: the 'star' symbol doesn't work with plotly scatter3d :C
# see here: https://github.com/plotly/plotly.py/issues/454
# supported marker symbols in plotly scatter-3d:
# (enumerated: "circle" | "circle-open" | "square" | "square-open" | 
#                         "diamond" | "diamond-open" | "cross" | "x" )
line2symbol = {'matplotlib': {'sphere': 'd',       'sinc': 'o'     },
               'plotly'    : {'sphere': 'diamond', 'sinc': 'circle'} }

pyscatter3d(datasets, line2text, line2color, line2symbol,
            which_x, which_y, which_z, which_s, default_size,
            outfile=outfile, backend='both')
