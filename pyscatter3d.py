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

class Scatter(): # TODO: inherit from self.dataframe maybe?
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
                remove_plotly_cloud_button=False):

        self.which_x = which_x
        self.which_y = which_y
        self.which_z = which_z

        self.xaxis_label = xaxis_label
        self.yaxis_label = yaxis_label
        self.zaxis_label = zaxis_label

        self.xaxis_range = xaxis_range
        self.yaxis_range = yaxis_range
        self.zaxis_range = zaxis_range

        if type(marker_size) is int:
            marker_size = {'matplotlib': marker_size,'plotly': marker_size}
        if type(marker_srange) is int:
            marker_srange = {'matplotlib': marker_srange,'plotly': marker_srange}
        self.marker_size   = marker_size   or {'matplotlib': 30,'plotly': 10}
        self.marker_srange = marker_srange or {'matplotlib': 25,'plotly': 9}

        ######### move to its own f-ion ########
        # this does not agree with the oop-approach, to be resolved elsewhere
        do_plotly = False if backend is 'matplotlib' else True
        do_matplotlib = False if backend is 'plotly' else True
        try:
            import plotly
            from use_plotly import (get_plotly_layout, defaults_3d,
                                    remove_plotly_buttons)
            layout = get_plotly_layout(plot_title,
                                       xaxis_label, yaxis_label, zaxis_label,
                                       xaxis_range, yaxis_range, zaxis_range )
        except ImportError:
            if backend is 'both':
                warning(" Can't import plotly, switching to matplotlib only.")
                do_plotly = False
            elif backend is 'plotly':
                raise ImportError("Can't import plotly!")
        
        if do_matplotlib:
            from use_matplotlib import matplotlib_make_figure, matplotlib_set_plot
            fig, ax = matplotlib_make_figure()
        ########################################

        ######### move to its own f-ion ########
        # reading in and processing the .csv files
        self.data = {}
        for dset, fname in datasets.iteritems():
            self.data[dset] = {'df': pd.read_csv(fname)}
        
        for dset in self.data.keys():
            for key_merged, keys_to_merge in combine_columns.iteritems():
                self.data[dset]['df'] = merge_df(self.data[dset]['df'], key_merged, 
                                        keys_to_merge, verify_integrity=True)
            # this should be optional, right?
            try:
                self.data[dset]['df'].drop_duplicates(cols=[self.which_x,
                                                       self.which_y,
                                                       self.which_z],
                                                inplace=True)
            except KeyError:
                pass # will catch it again later anyway
        ########################################
            
        ######### move to its own f-ion ########
        for dset in self.data.keys():
            try:
                X, Y, Z = (self.data[dset]['df'][self.which_x],
                           self.data[dset]['df'][self.which_y],
                           self.data[dset]['df'][self.which_z] )
            except KeyError as err:
                warning(" "+str(err)+"- plotting '%s' will not be possible!"%dset)
                continue
            if do_matplotlib:
                ax.scatter(xs=X, ys=Y, zs=Z,
                           s=get_size(self.data[dset]['df'], which_s,
                                      size=self.marker_size['matplotlib'],
                                      size_range=self.marker_srange['matplotlib']),
                           zdir='z',
                           # fix that: I think ditching lists is ok.
                           marker=dset2symbol['matplotlib'][dset],
                           c=dset2color[dset],
                           alpha=0.4, # TODO: make it flexible
                           edgecolor='#636363',
                           label=dset2text[dset])
            if do_plotly:
                self.data[dset]['plotly'] = dict(
                        name = dset2text[dset],
                        x = X, y = Y, z = Z,
                        marker = dict(size=get_size(self.data[dset]['df'], which_s,
                                            size=self.marker_size['plotly'],
                                            size_range=self.marker_srange['plotly']),
                                      color=dset2color[dset],
                                      symbol=[dset2symbol['plotly'][dset]]*len(X)))
                # setting default plotting parameters
                self.data[dset]['plotly'].update(defaults_3d)
        
        if do_plotly:
            fig = dict(data=[self.data[dset]['plotly'] for dset in self.data.keys() 
                       if 'plotly' in self.data[dset].keys()], layout=layout)
            # Use py.iplot() for IPython notebook
            url = plotly.offdset.plot(fig, filename=outfile,
                              show_link=False, auto_open=False)
            # don't want anyone importing private data 
            # into plotly via an accidental button click
            if remove_plotly_cloud_button:
                remove_plotly_buttons(url)
            plotly.offdset.offdset.webbrowser.open(url)
        
        if do_matplotlib:
            matplotlib_set_plot(ax, plot_title, outfile,
                                xaxis_label, yaxis_label, zaxis_label,
                                xaxis_range, yaxis_range, zaxis_range )
        ########################################

    def __getitem__(self, dset, cname=None):
        """
        Returns pandas self.data, or even a column in it?
        """
        raise NotImplementedError # TODO: needs testing
        if cname is None:
            return self.data[dset]
        else:
            return self.data[dset][cname]
