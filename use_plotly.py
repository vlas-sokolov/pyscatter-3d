"""
All the plotting defauls for plotly should be stored
here to avoid cluttering of the main plotting script.
"""
defaults_3d = dict(mode = "markers", type = "scatter3d", opacity = 0.5)

def get_plotly_layout(title=None, x_label=None, y_label=None, z_label=None, 
                                  x_range=None, y_range=None, z_range=None ):
    family = 'Computer Modern' # usually used for TeX stuff
    titlefont = dict(family=family, size=18, color='black')
    axisfont  = dict(family=family, size=18, color='grey')
    layout = dict(title = title, titlefont=titlefont, scene = dict(
            xaxis = dict(title=x_label, range=x_range, titlefont=axisfont),
            yaxis = dict(title=y_label, range=y_range, titlefont=axisfont),
            zaxis = dict(title=z_label, range=z_range, titlefont=axisfont)),
            legend = dict(xanchor = 'center', yanchor = 'top', x = 0.7))
    return layout

# tinkering with the upper-right buttons is hard! see here:
# http://community.plot.ly/t/remove-options-from-the-hover-toolbar/130
# see the links here: apparently it may be implemented soon
# http://www.mzan.com/article/36554705-adding-config- \
#                   modes-to-plotly-py-offline-modebar.shtml
def remove_plotly_buttons(url):
    with open(url[7:], 'r') as file: # [:7] removes file:// form file:///foo
        temp_url = file.read()
    # Replace the target strings
    #temp_url = temp_url.replace('displaylogo:!0', 'displaylogo:!1')
    temp_url = temp_url.replace('modeBarButtonsToRemove:[]',
                        'modeBarButtonsToRemove:["sendDataToCloud"]')
    with open(url[7:], 'w') as file: 
        file.write(temp_url)
        del temp_url 
