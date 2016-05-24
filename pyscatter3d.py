import numpy as np
import pandas as pd
from logging import warning

# TODO: some functions below should be class methods!

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

def ravel_columns(df, columns_to_ravel=[], new_columns=[]):
    """
    "Flattens" the dataframe. Example usage: 
    >>> ravel_columns(df, [['A1','B1'],['A2','B2']], ['A','B'])
    
    will return a dataframe with all A2/B2 values merged under A1/B1 into
    new columns called A and B. Warning: the remaining columns will be
    duplicated!

    Parameters
    ----------
    df : pandas.DataFrame;

    columns_to_ravel : list of lists; a list of collestions of column names
                       that will be put under new_columns (see below)

    new_columns : list; new column fields

    Returns
    -------
    df : a modified dataframe object
    """
    to_merge=[]
    for old_columns in columns_to_ravel:
        subdf = df.rename(columns=dict(zip(old_columns, new_columns)))
        killst = [c for c in columns_to_ravel if c is not old_columns]
        for killkey in killst:
            subdf = subdf.drop(killkey, 1)
        to_merge.append(subdf)
    # snap, this causes pandas bug #6963!
    df = pd.concat(to_merge, ignore_index=True)
    # should remove theth pu

    return df

def merge_df(df, merged_column, columns = [], delete_originals=True, **kwargs):
    """
    Merges several columns of the dataframe into one, removing NaN values.
    FIXME: does not always work? I think it creates doubles for more than
    two columns... use ravel_columns for now.
    """
    # TODO: would be nice to know a better, pandas-like, apporach
    warning(" may contain bugs.")
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
    def __init__(self, which, kill_plotly_button=False, **kwargs):
        if which is 'plotly':
            self.data = {} # TODO: not a good idea?
            self.kill_button = kill_plotly_button
        if which is 'plt' or which is 'matplotlib':
            pass

class Plotter():
    """
    This class holds general plotting variables and
    should be called as a main plotting function
    """
    def __init__(self, x='X', y='Y', z='Z', s='S',
                 labels=None, colors=None, symbols=None,
                 outfile='output', plot_title='',
                 xlabel='X', xrange=[None,None],
                 ylabel='Y', yrange=[None,None],
                 zlabel='Z', zrange=[None,None],
                 marker_size=None, marker_srange=None, **kwargs):
        """
        Returns a collection of general plotting parameters.

        TODO: docstring with parameter description.
        """
        self.which_x = x
        self.which_y = y
        self.which_z = z
        self.which_s = s
        from collections import defaultdict
        self.dset2text   =  labels  or defaultdict(lambda: None)
        self.dset2color  =  colors  or defaultdict(lambda: None)
        self.dset2symbol = (symbols or
            {'matplotlib': defaultdict(lambda: 'o'),
             'plotly'    : defaultdict(lambda: 'circle')})

        self.xaxis_label = xlabel
        self.yaxis_label = ylabel
        self.zaxis_label = zlabel
        self.xaxis_range = xrange
        self.yaxis_range = yrange
        self.zaxis_range = zrange
        self.plot_title  = plot_title

        if type(marker_size) is int:
            marker_size = {'matplotlib': marker_size,'plotly': marker_size}
        if type(marker_srange) is int:
            marker_srange = {'matplotlib': marker_srange,
                             'plotly'    : marker_srange }
        self.marker_size   = marker_size   or {'matplotlib': 30,'plotly': 10}
        self.marker_srange = marker_srange or {'matplotlib': 25,'plotly': 9}

    def __call__(self, **kwargs):
        self._plotfunc(**kwargs)

class ScatterPlot(): # TODO: inherit from dataframe maybe?
    """
    A class that holds all the self.data to be plotted, as well as a variety
    of the plotting functions for different backends.
    """
    def __init__(self, **kwargs):
        self.plot = Plotter(**kwargs)
        self.plot._plotfunc = self._plotfunc
        self.plt_conf = Backend('matplotlib', **kwargs)
        self.plotly_conf = Backend('plotly', **kwargs)
        self.set_backend(**kwargs)

        # read in the lists of .csv files
        self.read_data(**kwargs)

    def __getitem__(self, dset):
        """
        Returns pandas dataframe.
        """
        return self.data[dset]

    def __setitem__(self, dset, item):
        """
        Set pandas dataframe.
        """
        self.data[dset] = item

    def set_backend(self, backend = 'both', **kwargs):
        """
        Set the backend(s) to be used for plotting.

        Parameters
        ----------
        backend : str, can be 'plotly', 'matplotlib', or 'both'
        """
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
                self.plotly_conf.can_use = False
            elif backend is 'plotly':
                raise ImportError("Can't import plotly!")
        
        if self.plt_conf.can_use:
            from use_matplotlib import matplotlib_make_figure
            fig, ax = matplotlib_make_figure()
            self.plt_conf.axis = ax
            self.plt_conf.figure = fig

    def read_data(self, datasets=None, combine_columns={}, **kwargs):
        self.data = {}
        self.combine_columns = combine_columns
        if datasets is None:
            warning(" No data to read. Try setting the `datasets` keyword.")
            return

        # reading in and processing the .csv files
        for dset, fname in datasets.iteritems():
            self.data[dset] = pd.read_csv(fname)
        
        for dset in self.data.keys():
            for key_merged, keys_to_merge in combine_columns.iteritems():
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
        msize, mrange = self.plot.marker_size, self.plot.marker_srange
        get_col=self.plot.dset2color
        get_sym=self.plot.dset2symbol
        get_txt=self.plot.dset2text
        # TODO: move it somewhere else?
        # could put it as an attribute under self.plotly_conf
        from use_plotly import defaults_3d
        from use_matplotlib import fix_axes3d_color
        for dset in self.data.keys():
            try:
                X, Y, Z = (self.data[dset][xlab],
                           self.data[dset][ylab],
                           self.data[dset][zlab] )
            except KeyError as err:
                warning(" %s- plotting '%s' will not"
                        " be possible!" % (dset, str(err)))
                continue
            if self.plt_conf.can_use:
                ax = self.plt_conf.axis
                ax.scatter(xs=X, ys=Y, zs=Z,
                           s=get_size(self.data[dset], slab,
                                      size=msize['matplotlib'],
                                      size_range=mrange['matplotlib']),
                           zdir='z',
                           # fix that: I think ditching lists is ok.
                           marker=get_sym['matplotlib'][dset],
                           c=fix_axes3d_color(ax, get_col[dset]),
                           alpha=0.4, # TODO: make it flexible
                           edgecolor='#636363',
                           label=dset if get_txt[dset] is None
                                      else get_txt[dset])
            if self.plotly_conf.can_use:
                # TODO: this needs to be moved to self.plotly_conf.data
                self.plotly_conf.data[dset] = dict(
                        name = get_txt[dset],
                        x = X, y = Y, z = Z,
                        marker = dict(size=get_size(self.data[dset], slab,
                                               size=msize['plotly'],
                                               size_range=mrange['plotly']),
                                      color=get_col[dset],
                                      symbol=len(X)*[get_sym['plotly'][dset]])
                        )
                # setting default plotting parameters
                self.plotly_conf.data[dset].update(defaults_3d)
        
        if self.plotly_conf.can_use:
            from plotly import offline
            from use_plotly import remove_plotly_buttons
            fig = dict(data=self.plotly_conf.data.values(),
                       layout=self.plotly_conf.layout)
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
