import numpy as np
from pyscatter3d import ScatterPlot

# generating an sinc(R) dataset
X0, Y0 = np.meshgrid(np.linspace(-3,3,50), np.linspace(-3,3,50))
D = np.sqrt(X0**2+Y0**2) # radial distance
Z0 = np.sinc(D)

# drawing random points of a sphere
_ = np.random.randn(3, 1e3)
X1,Y1,Z1 = _/np.linalg.norm(_, axis=0)

np.savetxt('sinc.csv', np.array([arr.flatten() for arr in [X0,Y0,Z0,1/D]]).T,
           delimiter=',', header='A,B,C,inv_dist', comments='')

np.savetxt('sphere.csv', np.array([arr.flatten() for arr in [X1,Y1,Z1]]).T,
           delimiter=',', header='A,B,C', comments='')

# dataset names and their corresponding filenames
filedict = {'sinc'  : 'sinc.csv',
            'sphere': 'sphere.csv'}

# output file name (without an extension)
outfile = 'example'

line2text  = {'sinc': 'sinc(r)', 'sphere': 'sphere' }
line2color = {'sinc': '#e41a1c', 'sphere': '#377eb8'}

# supported marker symbols in plotly scatter-3d:
# (enumerated: "circle" | "circle-open" | "square" | "square-open" | 
#                         "diamond" | "diamond-open" | "cross" | "x" )
line2symbol = {'matplotlib': {'sphere': 'd',       'sinc': 'o'     },
               'plotly'    : {'sphere': 'diamond', 'sinc': 'circle'} }

# plotting both matplotlib and plotly figures, using A, B, and C as X,Y,Z:
method = 'both' # allowed values: 'matplotlib', 'plotly', and 'both'
pysc = ScatterPlot(x='A', y='B', z='C', s='inv_dist', datasets=filedict,
                   labels=line2text, colors=line2color, symbols=line2symbol,
                   backend=method)
pysc.plot()
