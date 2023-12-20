import matplotlib as mpl
#print(mpl.__version__)
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm as cm
#from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.lines as mlines
from matplotlib.ticker import MultipleLocator
from datetime import timedelta
import numpy as np
import ImageAvailabilityInfos as info
import importlib
importlib.reload(info)

# Function to visualize the info about the imagery from the given satellite / sensor
def visualize_imagery_info(collection_df, ax, j):
    
    if collection_df.empty:
        return

    # Define x and y values for plotting
    x = collection_df.index
    y = [j] * len(collection_df)
    
    # # Use the cloudiness values as the % opacity of the marker (alpha) 
    # alphas = np.array((collection_df_full['pctCloud'].fillna(0))/100)
    
    # Use the cloudiness value as the color of the marker, from white (no clouds) to grey (clouds)
    fills = np.array(collection_df['pctCloud']/100)

    # Use the % area coverage as the internal marker size, inside a 100% outer marker
    mdim = 30 # marker dimension
    msize = mdim**2 # marker size (square of dimension, since using area of a square)
    sizes = np.array((mdim*(collection_df['pctArea'])/100)**2)
    
    # Plot as scatter
    ax = ax or plt.gca()
    ax.scatter(x, y, alpha=1, facecolors='none', edgecolors='gray', marker='s', linestyle='-', s=msize, hatch='///') # outer edge for theoretical full 100% area
    ax.scatter(x, y, alpha=1, marker='s', edgecolors='none', c=fills, cmap='gray', vmin=0, vmax=1, s=sizes) # fill for cloudiness
    ax.scatter(x, y, alpha=1, facecolors='none', edgecolors='gray', marker='s', linestyle='-', s=sizes) # inner edge for actual % area coverage
    #ax.scatter(x, y, alpha=alphas, marker='o', edgecolors='none', facecolors='gray', s=sizes) # fill for cloudiness
    
    return ax

# Function to create the gra[hoc
def showImageAvailability(startDate, endDate, geometry, planetAPIKey, planetCSV=None, includeS2TOA=False):
    
    # Run GetDataFrames function to get dataframes for each sat-sensor
    date_list_df, sentinel2_df, sentinel1_df, modis_terra_df, landsat7_df, landsat8_df, landsat9_df, PlanetInfoDF, s2TOAFlag = info.GetDataFrames(startDate, endDate, geometry, planetAPIKey, planetCSV, includeS2TOA)

    # Create a second plot where the sat image availability is grouped by sat / sensor type
    # Define names for plotting
    if s2TOAFlag==True:
        names = ['Sentinel-1', 'Sentinel-2 TOA', 'MODIS', 'Landsat', 'Planet']
    else:
        names = ['Sentinel-1', 'Sentinel-2', 'MODIS', 'Landsat', 'Planet']
    js = range(len(names), 0, -1)

    # Create the plot
    fig, ax = plt.subplots(figsize=(len(date_list_df)/1.5, len(names)+1)) #0.75 * len(names)+1
    bottom, top = 0, 0.88
    left, right = 0, 1
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right, hspace=0.1, wspace=0.1)

    # Run the function to add each imagery info to the plot - ***can remove or add to this (i.e., plot more or fewer sats/sensors), so long as adjust the list 'names' and adjust the js[n] in the below functions
    visualize_imagery_info(sentinel1_df, ax, js[0])
    visualize_imagery_info(sentinel2_df, ax, js[1])
    visualize_imagery_info(modis_terra_df, ax, js[2]) # visualize_imagery_info(modis_aqua_df, ax, js[3])
    visualize_imagery_info(landsat7_df, ax, js[3])
    visualize_imagery_info(landsat8_df, ax, js[3])
    visualize_imagery_info(landsat9_df, ax, js[3])
    visualize_imagery_info(PlanetInfoDF, ax, js[4])

    # Format the ticks and gridlines
    major_tick = MultipleLocator(7)
    minor_tick = MultipleLocator(1)
    ax.xaxis.set_major_locator(major_tick)
    ax.xaxis.set_minor_locator(minor_tick)
    ax.tick_params(axis='x', which='major', labelsize=22)
    plt.yticks(ticks= range(len(names), 0, -1), labels=names, fontsize=22)
    ax.grid(False, axis = 'x')
    #ax.grid(True, axis = 'x', which='minor', linestyle=':')
    ax.grid(False, axis = 'y')


    # Format the plot title
    # fig.suptitle('Image availability for ' + nameArg, fontsize=24, x=0.15, y=0.88)

    # Format the x and y limits
    plt.xlim(date_list_df['date'].min()-timedelta(days=1), date_list_df['date'].max())
    plt.ylim(0.5, len(names)+0.5)

    # Add a marker legend for % area coverage
    mdim = 30 # marker dimension
    square = mlines.Line2D([], [], color='black', marker='s', linestyle='none', fillstyle='none', #marker='$\u2B1A$'
                            markersize=mdim, label='Image % of ROI coverage')
    square2 = mlines.Line2D([], [], color='black', marker='s', linestyle='none', fillstyle='none',
                            markersize=mdim/2, label='')
    plt.legend(handles=[square, square2], bbox_to_anchor=(0.50, 1.18), borderaxespad=0.1, frameon=False, labelspacing = -1.0, fontsize=16)

    # Add a cbar legend for % cloudiness
    #cbar_ax = fig.add_axes([0.88, 0.94, 0.08, 0.04]) # currently need to be done manually
    # cbar_ax = fig.add_axes([0.52, 0.96, 0.05, 0.04]) # currently need to be done manually
    cbar_ax = fig.add_axes([0.62, 0.88, 0.05, 0.04]) # currently need to be done manually
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=0, vmax=100), cmap='gray'), orientation='horizontal', cax=cbar_ax)
    cbar.set_ticks([0,100])
    cbar.set_ticklabels([0,100])
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label(label='Image % cloudiness', size=16, x = 2.6, labelpad=-33)

    fig.tight_layout()

    # Finalise the plot
    plt.show()
    return fig