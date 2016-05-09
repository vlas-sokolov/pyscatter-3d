# pyscatter-3d
Reads collections of `.csv` files and plots selected columns as an interactive 3d scatter-plot.
* supports both
  * matplotlib, the standard Python plottling library, and
  * plotly, generating faster, more interactive figures viewed directly in a web browser
* works with [pandas](http://pandas.pydata.org/) `DataFrame` class, making it easy to manipulate the input data

An [example](example.py) dataset rendered with [plotly](https://plot.ly/~vlas-sokolov/5/sphere-vs-sincx/):
![plotly interactive figure](https://github.com/vlas-sokolov/pyscatter-3d/blob/master/example-plotly.png)
Same data drawn with [matplotlib](http://matplotlib.org/)'s `axes3d` projection:
![matplotlib 3d-scatter](https://github.com/vlas-sokolov/pyscatter-3d/blob/master/example-matplotlib.png)
