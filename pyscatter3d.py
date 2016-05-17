import numpy as np
import pandas as pd
from logging import warning

def values_to_sizes(values, size, size_range):
    maxval, minval = np.nanmax(values), np.nanmin(values)
    try:
        medval = np.nanmedian(values)
    except KeyError:
        medval = np.nanmedian(values.values)
    sizes = (values-medval)/(maxval-medval)*size_range + size
    return sizes

def get_size(df, key, size=10, size_range=9):
    try:
        return values_to_sizes(df[key], size, size_range)
    except KeyError:
        return np.full((len(df),), size, dtype=np.int64)

def merge_df(df, merged_column, columns = [], delete_originals=True, **kwargs):
    """
    Merges several columns of the dataframe into one, removing NaN values.
    """
    # TODO: would be nice to know a better, pandas-like, apporach
    to_merge = []
    for col in columns:
        try:
            to_merge.append(df[~df[col].isnull()])
        except KeyError:
            continue
        to_merge[-1] = to_merge[-1].rename(columns={col:merged_column})
    if len(to_merge):
        df = pd.concat(to_merge, ignore_index=True, **kwargs)
        if delete_originals:
            for col in columns:
                try:
                    df = df.drop(col, 1)
                except ValueError:
                    pass
    return df

class Backend(): 
    pass

class Plotter():
    """
    This class holds general plotting variables and
    should be called as a main plotting function
    """
    def __init__(self, plotfunc, 
                 outfile='output', plot_title='',
                 xaxis_label='X', xaxis_range=[None,None], 
                 yaxis_label='Y', yaxis_range=[None,None],
                 zaxis_label='Z', zaxis_range=[None,None],
                 marker_size=None, marker_srange=None):

        self._plotfunc = plotfunc
        self.xaxis_label = xaxis_label
        self.yaxis_label = yaxis_label
        self.zaxis_label = zaxis_label
        self.xaxis_range = xaxis_range
        self.yaxis_range = yaxis_range
        self.zaxis_range = zaxis_range
        self.plot_title  = plot_title

        if type(marker_size) is int:
            marker_size = {'matplotlib': marker_size,'plotly': marker_size}
        if type(marker_srange) is int:
            marker_srange = {'matplotlib': marker_srange,'plotly': marker_srange}
        self.marker_size   = marker_size   or {'matplotlib': 30,'plotly': 10}
        self.marker_srange = marker_srange or {'matplotlib': 25,'plotly': 9}

    def __call__(self, **kwargs):
        self._plotfunc(**kwargs)

class ScatterPlot(): # TODO: inherit from dataframe maybe?
    """
    A class that holds all the self.data to be plotted, as well as a variety
    of the plotting functions for different backends.
    """
    def __init__(self, datasets, which_x, which_y, which_z, which_s, 
                 dset2text, dset2color, dset2symbol, **kwargs):
        print kwargs
        scatter_default_args = dict(kill_plotly_button = False, 
                                    backend            = 'both',
                                    combine_columns    = {}     )
        for key, def_val in scatter_default_args.iteritems():
            if key in kwargs:
                setattr(self, key, kwargs.get(key))
                kwargs.pop(key)
            else:
                setattr(self, key, def_val)

        # a holder for general plotting parameters
        self.plot = Plotter(self._plotfunc, **kwargs)
        self.plot.which_x = which_x
        self.plot.which_y = which_y
        self.plot.which_z = which_z
        self.plot.which_s = which_s
        self.plot.dset2text   = dset2text
        self.plot.dset2color  = dset2color
        self.plot.dset2symbol = dset2symbol

        #for key, val in kwargs.iteritems():
        #    setattr(self.plot, key, val)
        combine_columns = kwargs.get('combine_columns') if 'combine_columns' in kwargs else {}
        self.combine_columns = combine_columns

        # read in the lists of .csv files
        self.read_data(datasets)

        # set up some plotting parameters
        self.plt_conf = Backend()
        self.plotly_conf = Backend()
        self.plotly_conf.data = {} # TODO: not a good idea?
        self.plotly_conf.kill_button = self.kill_plotly_button
        self.init_plot(self.backend)

    def __getitem__(self, dset):
        """
        Returns pandas dataframe
        """
        return self.data[dset]

    def init_plot(self, backend):
        # this does not agree with the oop-approach, to be resolved elsewhere
        self.plotly_conf.can_use = False if backend is 'matplotlib' else True
        self.plt_conf.can_use = False if backend is 'plotly' else True
        try:
            import plotly
            from use_plotly import get_plotly_layout
            layout = get_plotly_layout(self.plot)
            self.plotly_conf.layout = layout
        except ImportError:
            if backend is 'both':
                warning(" Can't import plotly, switching to matplotlib only.")
                self.backends['plotly']['can_use'] = False
            elif backend is 'plotly':
                raise ImportError("Can't import plotly!")
        
        if self.plt_conf.can_use:
            from use_matplotlib import matplotlib_make_figure
            fig, ax = matplotlib_make_figure()
            self.plt_conf.axis = ax
            self.plt_conf.figure = fig

    def read_data(self, datasets):
        # reading in and processing the .csv files
        self.data = {}
        for dset, fname in datasets.iteritems():
            self.data[dset] = pd.read_csv(fname)
        
        for dset in self.data.keys():
            for key_merged, keys_to_merge in self.combine_columns.iteritems():
                self.data[dset] = merge_df(self.data[dset], key_merged,
                                           keys_to_merge, verify_integrity=True)
            # TODO: this should be optional, right?
            try:
                self.data[dset].drop_duplicates(cols=[self.plot.which_x,
                                                      self.plot.which_y,
                                                      self.plot.which_z],
                                                inplace=True)
            except KeyError:
                pass # TODO: what should be raised here?
            
    def _plotfunc(self, outfile='figure'):
        xlab, ylab, zlab, slab = (self.plot.which_x, self.plot.which_y,
                                  self.plot.which_z, self.plot.which_s )

        # TODO: move it somewhere else?
        # could put it as an attribute under self.plotly_conf
        from use_plotly import defaults_3d

        for dset in self.data.keys():
            try:
                X, Y, Z = (self.data[dset][xlab],
                           self.data[dset][ylab],
                           self.data[dset][zlab] )
            except KeyError as err:
                warning(" "+str(err)+"- plotting '%s' will not be possible!"%dset)
                continue
            if self.plt_conf.can_use:
               self.plt_conf.axis.scatter(xs=X, ys=Y, zs=Z,
                           s=get_size(self.data[dset], slab,
                                      size=self.plot.marker_size['matplotlib'],
                                      size_range=self.plot.marker_srange['matplotlib']),
                           zdir='z',
                           # fix that: I think ditching lists is ok.
                           marker=self.plot.dset2symbol['matplotlib'][dset],
                           c=self.plot.dset2color[dset],
                           alpha=0.4, # TODO: make it flexible
                           edgecolor='#636363',
                           label=self.plot.dset2text[dset])
            if self.plotly_conf.can_use:
                # TODO: this needs to be moved to self.plotly_conf.data
                self.plotly_conf.data[dset] = dict(
                        name = self.plot.dset2text[dset],
                        x = X, y = Y, z = Z,
                        marker = dict(size=get_size(self.data[dset], slab,
                                            size=self.plot.marker_size['plotly'],
                                            size_range=self.plot.marker_srange['plotly']),
                                      color=self.plot.dset2color[dset],
                                      symbol=[self.plot.dset2symbol['plotly'][dset]]*len(X)))
                # setting default plotting parameters
                self.plotly_conf.data[dset].update(defaults_3d)
        
        if self.plotly_conf.can_use:
            from plotly import offline
            from use_plotly import remove_plotly_buttons
            fig = dict(data=self.plotly_conf.data.values(), layout=self.plotly_conf.layout)
            # Use py.iplot() for IPython notebook
            url = offline.plot(fig, filename=outfile,
                               show_link=False, auto_open=False)
            # don't want anyone importing private data 
            # into plotly via an accidental button click
            if self.plotly_conf.kill_button:
                remove_plotly_buttons(url)
            offline.offline.webbrowser.open(url)
        
        if self.plt_conf.can_use:
            from use_matplotlib import matplotlib_set_plot
            matplotlib_set_plot(self.plt_conf.axis, self.plot, outfile)
