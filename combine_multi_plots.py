import matplotlib.pyplot as plt
from PIL import Image
import os, string

def combine_plots(input_files, ncol=1, figsize = (10, 10), title_position = 'left', **kwargs):

    '''
    This function combines multiple images into a single plot.

    Parameters: 
        input_files (list): List of image file paths.
        ncol (int): Number of columns in the plot. Default is 1.
        figsize (tuple): Figure size in inches. Default is (10, 10).
        title_position (str): Position of the title. Default is 'left'.
        **kwargs: Additional arguments to be passed to the title

    Returns:
        None

    '''

    num_plots = len(input_files)
    nrows = num_plots // ncol + (num_plots % ncol > 0)
    labels = string.ascii_lowercase[:num_plots]  # Generate sequence of letters a), b), c), ...
    
    fig, axes = plt.subplots(nrows = nrows, ncols = ncol, figsize = figsize)
    axes = axes.ravel()  # Flatten the subplots to a 1-dimensional array
    
    for i, file in enumerate(input_files):
        img = Image.open(file)
        ax = axes[i]
        
        ax.imshow(img)
        ax.axis('off')
        
        # Add sequence label and image file name as the title
        label = labels[i] + ')'
        ax.set_title(label, loc=title_position, **kwargs)
        
        # Set the DPI of the subplot to match the original image DPI
        # Default DPI is set to 300 if not available
        dpi = int(img.info.get('dpi', (300, 300))[0])  
        ax.figure.set_dpi(dpi)
        
    # Remove any unused subplots
    for j in range(num_plots, nrows * ncol):
        axes[j].axis('off')
    
    plt.savefig(os.path.join(os.path.dirname(input_files[0]), 'combined_plots.jpeg'), dpi = 300, bbox_inches = 'tight')
    plt.tight_layout()
    plt.show()

# ---------------- Example ---------------- #
# input_files = ['image1.jpeg', 'image2.jpeg', 'image3.jpeg', 'image4.jpeg']
# combine_plots(input_files, ncol = 2, title_position = 'center', figsize = (10, 10)
