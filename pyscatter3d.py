import numpy as np
import pandas as pd

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

def pyscatter3d(datasets, line2text, line2color, line2symbol,
                which_x, which_y, which_z, which_s,
                outfile='output', plot_title='',
                backend='both', combine_columns={},
                xaxis_label='X', xaxis_range=[None,None], 
                yaxis_label='Y', yaxis_range=[None,None],
                zaxis_label='Z', zaxis_range=[None,None],
                marker_size=None, marker_srange=None,
                remove_plotly_cloud_button=False):

    if type(marker_size) is int:
        marker_size = {'matplotlib': marker_size,'plotly': marker_size}
    if type(marker_srange) is int:
        marker_srange = {'matplotlib': marker_srange,'plotly': marker_srange}
    marker_size   = marker_size   or {'matplotlib': 30,'plotly': 10}
    marker_srange = marker_srange or {'matplotlib': 25,'plotly': 9}

    do_plotly = False if backend is 'matplotlib' else True
    do_matplotlib = False if backend is 'plotly' else True
    try:
        import plotly
        from use_plotly import get_plotly_layout, defaults_3d, remove_plotly_buttons
        layout = get_plotly_layout(plot_title,
                                   xaxis_label, yaxis_label, zaxis_label,
                                   xaxis_range, yaxis_range, zaxis_range )
    except ImportError:
        if backend is 'both':
            print "WARNING: can't import plotly, switching to matplotlib only."
            do_plotly = False
        elif backend is 'plotly':
            raise ImportError("Can't import plotly!")
    
    if do_matplotlib:
        from use_matplotlib import matplotlib_make_figure, matplotlib_set_plot
        fig, ax = matplotlib_make_figure()
    
    # reading in and processing the .csv files
    ppv = {}
    for line, fname in datasets.iteritems():
        ppv[line] = {'df': pd.read_csv(fname)}
    
    for line in ppv.keys():
        for key_merged, keys_to_merge in combine_columns.iteritems():
            ppv[line]['df'] = merge_df(ppv[line]['df'], key_merged, 
                                    keys_to_merge, verify_integrity=True)
        try:
            ppv[line]['df'].drop_duplicates(cols=[which_x,which_y,which_z],
                                                        inplace=True)
        except KeyError:
            pass # will catch it again later anyway
        
    for line in ppv.keys():
        try:
            X, Y, Z = (ppv[line]['df'][which_x],
                       ppv[line]['df'][which_y],
                       ppv[line]['df'][which_z] )
        except KeyError as err:
            print "WARNING: "+str(err)+"- plotting '%s' will not be possible!"%line
            continue
        if do_matplotlib:
            ax.scatter(xs=X, ys=Y, zs=Z,
                       s=get_size(ppv[line]['df'], which_s,
                                  size=marker_size['matplotlib'],
                                  size_range=marker_srange['matplotlib']),
                       zdir='z',
                       # fix that: I think ditching lists is ok.
                       marker=line2symbol['matplotlib'][line],
                       c=line2color[line],
                       alpha=0.4, # TODO: make it flexible
                       edgecolor='#636363',
                       label=line2text[line])
        if do_plotly:
            ppv[line]['plotly'] = dict(
                    name = line2text[line],
                    x = X, y = Y, z = Z,
                    marker = dict(size=get_size(ppv[line]['df'], which_s,
                                        size=marker_size['plotly'],
                                        size_range=marker_srange['plotly']),
                                  color=line2color[line],
                                  symbol=[line2symbol['plotly'][line]]*len(X)))
            # setting default plotting parameters
            ppv[line]['plotly'].update(defaults_3d)
    
    if do_plotly:
        fig = dict(data=[ppv[line]['plotly'] for line in ppv.keys() 
                   if 'plotly' in ppv[line].keys()], layout=layout)
        # Use py.iplot() for IPython notebook
        url = plotly.offline.plot(fig, filename=outfile,
                          show_link=False, auto_open=False)
        # don't want anyone importing private data 
        # into plotly via an accidental button click
        if remove_plotly_cloud_button:
            remove_plotly_buttons(url)
        plotly.offline.offline.webbrowser.open(url)
    
    if do_matplotlib:
        matplotlib_set_plot(ax, plot_title, outfile,
                            xaxis_label, yaxis_label, zaxis_label,
                            xaxis_range, yaxis_range, zaxis_range )
