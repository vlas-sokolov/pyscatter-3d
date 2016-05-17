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
    Merges several columns of the self.dataframe into one, removing NaN values.
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

# NOTE: the class below is a replacement for dict strcuture, to avoid
# mixing foo["bar"] and foo.bar access, something not recommended by
# python Zen masters. I am still using Pandas though...
class Backend(): pass

class ScatterPlot(): # TODO: inherit from self.dataframe maybe?
    """
    A class that holds all the self.data to be plotted, as well as a variety
    of the plotting functions for different backends.
    """
    def __init__(self, datasets, dset2text, dset2color, dset2symbol,
                which_x, which_y, which_z, which_s,
                outfile='output', plot_title='',
                backend='both', combine_columns={},
                xaxis_label='X', xaxis_range=[None,None], 
                yaxis_label='Y', yaxis_range=[None,None],
                zaxis_label='Z', zaxis_range=[None,None],
                marker_size=None, marker_srange=None,
                kill_plotly_button=False):

        self.which_x = which_x
        self.which_y = which_y
        self.which_z = which_z
        self.which_s = which_s

        self.xaxis_label = xaxis_label
        self.yaxis_label = yaxis_label
        self.zaxis_label = zaxis_label

        self.xaxis_range = xaxis_range
        self.yaxis_range = yaxis_range
        self.zaxis_range = zaxis_range

        self.dset2text   = dset2text
        self.dset2color  = dset2color
        self.dset2symbol = dset2symbol

        self.plot_title = plot_title

        self.combine_columns = combine_columns

        if type(marker_size) is int:
            marker_size = {'matplotlib': marker_size,'plotly': marker_size}
        if type(marker_srange) is int:
            marker_srange = {'matplotlib': marker_srange,'plotly': marker_srange}
        self.marker_size   = marker_size   or {'matplotlib': 30,'plotly': 10}
        self.marker_srange = marker_srange or {'matplotlib': 25,'plotly': 9}

        # read in the lists of .csv files
        self.read_data(datasets)

        # set up some plotting parameters
        self.plt_conf = Backend()
        self.plotly_conf = Backend()
        self.plotly_conf.data = {} # TODO: not a good idea?
        self.plotly_conf.kill_button = kill_plotly_button
        self.init_plot(backend)

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
            layout = get_plotly_layout(self.plot_title,
                                       self.xaxis_label, self.yaxis_label, self.zaxis_label,
                                       self.xaxis_range, self.yaxis_range, self.zaxis_range )
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
                self.data[dset].drop_duplicates(cols=[self.which_x,
                                                      self.which_y,
                                                      self.which_z],
                                                inplace=True)
            except KeyError:
                pass # TODO: what should be raised here?
            
    def plot(self, outfile='figure'):
        # TODO: move it somewhere else?
        from use_plotly import defaults_3d

        for dset in self.data.keys():
            try:
                X, Y, Z = (self.data[dset][self.which_x],
                           self.data[dset][self.which_y],
                           self.data[dset][self.which_z] )
            except KeyError as err:
                warning(" "+str(err)+"- plotting '%s' will not be possible!"%dset)
                continue
            if self.plt_conf.can_use:
               self.plt_conf.axis.scatter(xs=X, ys=Y, zs=Z,
                           s=get_size(self.data[dset], self.which_s,
                                      size=self.marker_size['matplotlib'],
                                      size_range=self.marker_srange['matplotlib']),
                           zdir='z',
                           # fix that: I think ditching lists is ok.
                           marker=self.dset2symbol['matplotlib'][dset],
                           c=self.dset2color[dset],
                           alpha=0.4, # TODO: make it flexible
                           edgecolor='#636363',
                           label=self.dset2text[dset])
            if self.plotly_conf.can_use:
                # TODO: this needs to be moved to self.plotly_conf.data
                self.plotly_conf.data[dset] = dict(
                        name = self.dset2text[dset],
                        x = X, y = Y, z = Z,
                        marker = dict(size=get_size(self.data[dset], self.which_s,
                                            size=self.marker_size['plotly'],
                                            size_range=self.marker_srange['plotly']),
                                      color=self.dset2color[dset],
                                      symbol=[self.dset2symbol['plotly'][dset]]*len(X)))
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
            matplotlib_set_plot(self.plt_conf.axis, self.plot_title, outfile,
                                self.xaxis_label, self.yaxis_label, self.zaxis_label,
                                self.xaxis_range, self.yaxis_range, self.zaxis_range )
