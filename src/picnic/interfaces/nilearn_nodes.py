# =======================================
# Imports

# =======================================
# Constants

# =======================================
# Classes

# =======================================
# Functions

# =======================================
# Nipype Specific Functions
def _create_report(type_, in_files, additional_args=[]):
    """
    a function to hold all the reports
    
    :Parameters:
      -. `type_`: str, the star keyword
      -. `in_files`: list, a list of image files
      -. `additional_args`: list, a list of additional_args
    """
    # ============================================================== High Level
    STANDARD_WIDTH = 1120
    UPPER_COLORMAP_LIMIT = 99.5
    FRAMES_PER_SECOND = 4
    
    def image_report(in_file, basename='image'):
        """
        wrap the necessary steps to create a report of *image

        :Parameters:
          -. `in_file`: file-like str, the nibabel readable image file
          -. `basename`: str, name of the output filename
        """

        import os
        import nibabel as nib

        # Load file
        image = nib.load(in_file)

        # if the image is a 4d image, assume it is a pet image and create a mp4
        if len(image.shape) > 3:
            # create an optimized colormap for pet brains
            cmap_limits = calculate_colormap_limits(
                image,
                UPPER_COLORMAP_LIMIT
            )
            
            # calculate the bounds early so the mp4 and png have the same bound
            bounds = calculate_bounds(image)

            # create movie and png report
            mov = create_mp4_mosaic(
                image,
                basename,
                bounds = bounds,
                cmap = 'jet',
                vmin = cmap_limits[0],
                vmax = cmap_limits[1]
            )
            png = create_png_mosaic(
                image,
                basename,
                bounds = bounds,
                cmap = 'jet',
                vmin = cmap_limits[0],
                vmax = cmap_limits[1]
            )
        else:
            # for 3d images, just make a mosaic image
            png = create_png_mosaic(image, basename)
            
            # we need to return something so create a dummy txt file
            mov = os.path.abspath(basename + '.txt')
            with open(mov, 'w') as f:
                _ = f.write('3d image. No movie.')
        
        return png, mov
    
    def motion_correction_report(
        base_file,
        moco_file,
        mats = None,
        ref_frame = None,
        basename = 'motion_correction',
        width = 600
    ):
        """
        Wrap the necessary steps to create a report of *motion correction
        
        :Parameters:
          -. `base_file`: file-like str, the nibabel readable image file
          -. `moco_file`: file-like str, the nibabel readable image file
          -. `mats`: None or list of file-like str, the list of transformation
            files
          -. `ref_frame`: None or int, the reference frame
          -. `basename`: str, name of the output filename
          -. `width`: int,number of pixels wide used in the report image
        """

        import math
        import numpy as np
        import nibabel as nib

        from PIL import Image

        # load the files
        base_image = nib.load(base_file)
        moco_image = nib.load(moco_file)
        
        # create an optimized colormap for pet brains
        cmap_lims = calculate_colormap_limits(base_image, UPPER_COLORMAP_LIMIT)
        
        # calculate the bounds early so the mp4 and png have the same bound
        bounds = calculate_bounds(moco_image)
        ortho_cuts = [np.mean(bounds[direction]) for direction in 'xyz']
        
        # loop through all the transformation matrices and derive all 6 dofs
        if mats is not None:
            dofs = []
            for mat in mats:
                m = np.loadtxt(mat)
                x, y, z = m[0,3], m[1, 3], m[2, 3]
                rx = math.atan2(-m[1, 2], m[2, 2])
                ry = math.asin(m[0, 2])
                rz = math.atan2(-m[0, 1], m[0, 0])
                dofs.append(np.array([x, y, z, rx, ry, rz]))
            dofs = np.array(dofs)
        
        # loop over each frame and create a comparison orthogonal image for 
        #   pre- and post- correction
        stills = []
        for frame in range(moco_image.shape[3]):
            panels = []
            for image in (base_image, moco_image):
                panels.append(
                    draw_lines_on_image(
                        create_png_ortho(
                            image.slicer[..., frame],
                            ortho_cuts,
                            basename = None,
                            cmap = 'jet',
                            vmin = cmap_lims[0],
                            vmax = cmap_lims[1],
                            width = width
                        ),
                        23,
                        9
                    )
                )
            
            # if a list of mat files were provided, create tracer plots
            if mats is not None:
                # create a motion plot for the x, y and z dofs
                # print(np.arange(moco_image.shape[3]))
                # print(dofs[:, :3])
                panels.append(
                    create_moco_plot(
                        np.arange(moco_image.shape[3]),
                        dofs[:, :3],
                        frame,
                        basename = None,
                        ref_frame = None,
                        labels = ['x', 'y', 'z'],
                        width = width
                    )
                )
                
                # create a motion plot for the rx, ry and rz dofs
                panels.append(
                    create_moco_plot(
                        np.arange(moco_image.shape[3]),
                        dofs[:, 3:],
                        frame,
                        basename = None,
                        ref_frame = None,
                        labels = ['rx', 'ry', 'rz'],
                        width = width
                    )
                )
            
            # open the temporary images of panels and resize them to the same width
            resized_panels, heights = [], []
            for panel in panels:
                resized_panel = panel.resize(
                    (width, int(panel.size[1]*(width/panel.size[0])))
                )
                resized_panels.append(resized_panel)
                heights.append(resized_panel.size[1])
            
            # create a new image and paste in the resized panels
            y_offset = 0
            img = Image.new('RGB', (width, sum(heights)))
            for panel in resized_panels:
                img.paste(panel, (0, y_offset))
                y_offset += panel.size[1]
            stills.append(img)
        
        # create an mp4 from the list of pngs
        output_filename = basename + '.mp4'
        return create_mp4_from_image_list(
            stills,
            output_filename
        )
    
    def coregistration_report(
        base_file,
        over_file,
        basename = 'coregistration',
        width = STANDARD_WIDTH
    ):
        """
        wrap the necessary steps to create a report of *coregistration and camra
        
        :Parameters:
          -. `base_file`: file-like str, the nibabel readable image file
          -. `over_file`: file-like str, the nibabel readable image file
          -. `basename`: str, name of the output filename
          -. `width`: int, number of pixels wide used in the report image
        """

        import numpy as np
        import nibabel as nib

        # load file
        base_image = nib.load(base_file)
        over_image = nib.load(over_file)
        
        # create an optimized colormap for pet brains
        cmap_limits = calculate_colormap_limits(
            over_image,
            UPPER_COLORMAP_LIMIT
        )
        
        # calculate the bounds early so the mp4 and png have the same bound
        bounds = calculate_bounds(base_image)
        
        # create different pngs ramping up the opacity
        stills = []
        for opacity in np.linspace(0., 0.7, 6):
            stills.append(
                create_png_mosaic(
                    base_image,
                    basename = None,
                    bounds = bounds,
                    cmap = 'jet',
                    vmin = cmap_limits[0],
                    vmax = cmap_limits[1],
                    overlay_image = over_image,
                    opacity = opacity,
                    width = width
                )
            )
        
        # create an mp4 from the list of pngs
        output_filename = basename + '.mp4'
        return create_mp4_from_image_list(
            stills,
            output_filename
        )
    
    def tacs_report(
        tac_file,
        units = 'uci',
        selected_rois = [],
        basename = 'tacs',
        width = STANDARD_WIDTH
    ):
        """
        wrap the necessary steps to create a report of *tacs
        
        :Parameters:
          -. `tac_file`: file-like str, the nibabel readable image file
          -. `units`: str, 'uci' or 'Bq'
          -. `basename`: str, name of the output filename
          -. `width`: int, number of pixels wide used in the report image
        """

        import pandas as pd

        # load tacs file as a pandas dataset
        data = pd.read_csv(tac_file, delimiter='\t', header=0, index_col=0)
        
        # create a plot
        tac_plot = create_tacs_plot(
            data,
            basename = basename,
            units = units,
            selected_rois = selected_rois,
            width = width
        )
        return tac_plot
    
    # ======================================================= png/mp4 Generator
    def create_png_mosaic(
        image,
        basename = 'image',
        bounds = None,
        cmap = 'gray',
        vmin = None,
        vmax = None,
        n_cuts = 7,
        overlay_image = None,
        opacity = 0.7,
        width = STANDARD_WIDTH
    ):
        """
        Create a still picture of a brain image in a mosaic format
        
        |----------------------|
        | [] [] [] [] [] [] [] | y
        | [] [] [] [] [] [] [] | x
        | [] [] [] [] [] [] [] | z
        |----------------------|
        
        :Parameters:
          -. `image`: nibabel.Nifti1Image, the nibabel image
          -. `basename`: str or None, the base for the png filename. If None
            do not create png, return the Image obj
          -. `bounds`: dict or None, {'x': [float(lower bound), float(upper
            bound), 'y':...}
          -. `cmap`: str, the colormap. Only tested with 'gray' and 'jet'
          -. `vmin`: float, the min value for the colormap
          -. `vmax`: float, the max value for the colormap
          -. `n_cuts': int, the number of stills in a panel
          -. `width`: int, width (in pixels) for the output image
        """

        import os
        import tempfile
        import numpy as np
        from PIL import Image
        from nilearn.plotting import plot_anat, plot_roi

        # if the image is a 4d image, get the tmean
        image = force_3d_image(image)
        if overlay_image is not None:
            overlay_image = force_3d_image(overlay_image)
        
        # if not provided, calculate the mosaic bounds
        if bounds is None:
            bounds = calculate_bounds(image)
        
        # use nilearn's plot_anat to create each panel
        panels = {}
        for direction in 'xyz':
            panels[direction] = tempfile.NamedTemporaryFile(suffix='.png').name
            if overlay_image is None:
                _ = plot_anat(
                    image,
                    display_mode = direction,
                    cut_coords = np.linspace(*bounds[direction], n_cuts),
                    output_file = panels[direction],
                    black_bg = True,
                    dim = 0.,
                    cmap = cmap,
                    vmin = vmin,
                    vmax = vmax,
                )
            else:
                _ = plot_roi(
                    overlay_image,
                    image,
                    display_mode = direction,
                    cut_coords = np.linspace(*bounds[direction], n_cuts),
                    output_file = panels[direction],
                    black_bg = True,
                    dim = 0.,
                    cmap = cmap,
                    vmin = vmin,
                    vmax = vmax,
                    alpha = opacity
                )
        
        # open the temporary images of panels and resize them to the same width
        resized_panels, heights = [], []
        for direction in 'yxz':
            panel = Image.open(panels[direction])
            resized_panel = panel.resize(
                (width, int(panel.size[1]*(width/panel.size[0])))
            )
            resized_panels.append(resized_panel)
            heights.append(resized_panel.size[1])
        
        # create a new image and paste in the resized panels
        y_offset = 0
        mosaic = Image.new('RGB', (width, sum(heights)))
        for panel in resized_panels:
            mosaic.paste(panel, (0, y_offset))
            y_offset += panel.size[1]
        
        # save image
        if basename is not None:
            filename = basename + '.png'
            mosaic.save(filename)
            return os.path.abspath(filename)
        else:
            return mosaic
        
    def create_png_ortho(
        image,
        ortho_cuts,
        basename = 'image',
        cmap = 'gray',
        vmin = None,
        vmax = None,
        width = STANDARD_WIDTH,
    ):
        """
        use nilearn create ortho images
        
        :Parameters:
          -. `image` : nibabel.Nifti1Image, the nibabel image
          -. `ortho_cuts` : list, a list of the cuts [x, y, z]
          -. `basename` : str, the base for the png filename
          -. `cmap` : str, the colormap. Only tested with 'gray' and 'jet'
          -. `vmin` : float, the min value for the colormap
          -. `vmax` : float, the max value for the colormap
          -. `width` : int, width (in pixels) for the output image
        """

        import os
        import tempfile
        import numpy as np
        from PIL import Image
        from nilearn.plotting import plot_anat

        # if the image is a 4d image, get the tmean
        image = force_3d_image(image)
        
        # if not provided, calculate the mosaic bounds
        if ortho_cuts is None:
            bounds = calculate_bounds(image)
            ortho_cuts = [np.mean(bounds[direction]) for direction in ['xyz']]

        # Use nilearn's plot_anat to create each panel
        temp_panel = tempfile.NamedTemporaryFile(suffix='.png').name
        _ = plot_anat(
            image,
            display_mode = 'ortho',
            cut_coords = ortho_cuts,
            output_file = temp_panel,
            black_bg = True,
            dim = 0.,
            cmap = cmap,
            vmin = vmin,
            vmax = vmax,
            draw_cross = False
        )
        
        # resize the image to the desired width
        panel = Image.open(temp_panel)
        resized_panel = panel.resize(
            (width, int(panel.size[1]*(width/panel.size[0])))
        )
        
        # either save the resized image or return the Image obj
        if basename is not None:
            filename = basename + '.png'
            resized_panel.save(filename)
            return os.path.abspath(filename)
        else:
            return resized_panel
    
    def create_moco_plot(
        t,
        dofs,
        frame,
        basename = 'image',
        ref_frame = None,
        labels = ['x', 'y', 'z'],
        width = STANDARD_WIDTH
    ):
        """
        Create pyplots for motion correction
        
        :Parameters:
          -. `t` : numpy array, x axis
          -. `dofs` : numpy array, an array of dofs (x, y, z or rx, ry, rz)
          -. `frame` : int, denote which frame we are looking at
          -. `ref_frame` :int or None, denote the reference frame
          -. `width` : int, width (in pixels) for the output image
        """

        import os
        import tempfile
        import numpy as np
        import matplotlib.pyplot as plt

        from PIL import Image

        # create a pyplot
        tmp_png = tempfile.NamedTemporaryFile(suffix = '.png').name
        fig, ax = plt.subplots(figsize = (9, 3))
        a, = ax.plot(t, dofs[:, 0])
        a.set_label(labels[0])
        b, = ax.plot(t, dofs[:, 1])
        b.set_label(labels[1])
        c, = ax.plot(t, dofs[:, 2])
        c.set_label(labels[2])
        
        # create vertical lines for the current and reference frame
        _ = ax.vlines(
            t[frame],
            np.min(dofs[:, :3]),
            np.max(dofs[:, :3]),
            colors = 'r',
            linestyles = 'dashed',
            label = 'current'
        )
        if ref_frame is not None:
            _ = ax.vlines(
                ref_frame,
                np.min(dofs[:, :3]),
                np.max(dofs[:, :3]),
                colors = 'g',
                linestyles = 'dashed',
                label = 'ref'
            )
        
        # create some labels
        ax.set_xlabel('Frame Number')
        ax.set_ylabel('Detected Motion')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        fig.savefig(tmp_png)
        plt.close('all')
        
        # resize the image to the desired width
        panel = Image.open(tmp_png)
        resized_panel = panel.resize(
            (width, int(panel.size[1]*(width/panel.size[0])))
        )
        
        # either save the resized image or return the Image obj
        if basename is not None:
            filename = basename + '.png'
            resized_panel.save(filename)
            return os.path.abspath(filename)
        else:
            return resized_panel
    
    def create_tacs_plot(
        dataframe,
        basename = 'tacs',
        units = 'uci',
        selected_rois = [],
        width = STANDARD_WIDTH
    ):
        """
        use matplotlib to plot all the tacs
        
        :Parameters:
          -. `dataframe` : pandas.DataFrame, the table for tacs
          -. `basename` : str, the base for the mp4 filename
          -. `units` : str, 'uci' or 'Bq'
          -. `selected_rois` : list, a list of roi strings to plot
          -. `width` : int, width (in pixels) for the output image
        """

        import os
        import tempfile
        import matplotlib.pyplot as plt
        from PIL import Image

        # if selected plots are given, reduce the dataset
        title = 'All TACs'
        if len(selected_rois) > 0:
            dataframe = dataframe[selected_rois]
            title = 'Selected TACs'
        
        # create plot
        tmp_png = tempfile.NamedTemporaryFile(suffix = '.png').name
        fig, ax = plt.subplots(figsize=(12, 4))
        ax = dataframe.plot(ax=ax)
        if len(selected_rois) == 0:
            ax.legend().remove()
        ax.title.set_text(title)
        _ = ax.set_xlabel('Time (min)')
        if units=='uci':
            _ = ax.set_ylabel('Counts (uCi/cc)')
        elif units=='bq':
            _ = ax.set_ylabel('Counts (Bq/mL)')
        _ = ax.set_xlim(0.)
        plt.tight_layout()
        fig.savefig(tmp_png)
        
        # resize the image to the desired width
        panel = Image.open(tmp_png)
        resized_panel = panel.resize(
            (width, int(panel.size[1]*(width/panel.size[0])))
        )
        
        # either save the resized image or return the Image obj
        if basename is not None:
            filename = basename + '.png'
            resized_panel.save(filename)
            return os.path.abspath(filename)
        else:
            return resized_panel
    
    def create_mp4_mosaic(
        image,
        basename = 'image',
        bounds = None,
        cmap = 'jet',
        vmin = None,
        vmax = None,
        n_cuts = 7,
        width = STANDARD_WIDTH,
        fps = FRAMES_PER_SECOND
    ):
        """
        Create a movie based on stills from the create_png_mosaic function
        
        |----------------------|
        | [] [] [] [] [] [] [] | y
        | [] [] [] [] [] [] [] | x
        | [] [] [] [] [] [] [] | z
        |----------------------|
        
        :Parameters:
          -. `image` : nibabel.Nifti1Image, the nibabel image
          -. `basename` : str, the base for the mp4 filename
          -. `bounds` : dict or None, {'x' : [float(lower bound), float(upper
            bound), 'y' :...}
          -. `cmap` : str, the colormap. Only tested with 'gray' and 'jet'
          -. `vmin` : float, the min value for the colormap
          -. `vmax` : float, the max value for the colormap
          -. `n_cuts` : int, the number of stills in a panel
          -. `width` : int, width (in pixels) for the output image
          -. `fps` : int, frames per seconds
        """

        # if not provided, calculate the mosaic bounds
        if bounds is None:
            image3d = force_3d_image(image)
            bounds = calculate_bounds(image3d)
        
        # loop over each frame and create a mosaic still of that frame
        images = []
        for frame in range(image.shape[3]):
            images.append(
                create_png_mosaic(
                    image.slicer[..., frame],
                    basename = None,
                    bounds = bounds,
                    cmap = cmap,
                    vmin = vmin,
                    vmax = vmax,
                    n_cuts = n_cuts,
                    width = width
                )
            )
        
        output_filename = basename + '.mp4'
        return create_mp4_from_image_list(
            images,
            output_filename,
            fps = fps
        )
        
    def create_mp4_from_image_list(
        images,
        output_filename,
        fps=FRAMES_PER_SECOND
    ):
        """
        create a movie from a list of Image objects
        
        :Parameters:
          -. `image_list` : list of Images, list of mosaic images
          -. `output_filename` : str, must be a movie file type (.mp4)
          -. `fps` : int, frames per second
        """

        import os
        import glob

        # from each image in the list, save it as a temporary image
        for idx, image in enumerate(images):
            image.save('_image_' + str(idx).zfill(4) + '.png')
        
        # use ffmpeg to create an mp4 from the list of temporary images
        os.system(' '.join([
            'ffmpeg',
            '-r ' + str(fps),
            '-f image2',
            '-pattern_type glob',
            '-i "_image_*.png"',
            '-vcodec libx264',
            '-crf 20',
            '-pix_fmt yuv420p',
            output_filename
        ]))
        
        # remove the dummy pngs
        for tmp_file in glob.glob('_image_*.png'):
            os.remove(tmp_file)
            
        return os.path.abspath(output_filename)
    
    # ============================================================ Calculations
    def calculate_bounds(image):
        """
        Use nibabel to calculate the cut coords bounds. Calculations are
        done by:
        (a) finding the distribution over a single axis
        |   __
        |  /  \
        |  |   |
        | /     \
        |/       \
        -----------
        (b) get the total area under the curve
        (c) mark the location where the area is a percentage of the total area
        |   __
        |  /  \
        |  |   |
        | /|    \
        |/ |    |\
        ---*---*---
            see the asterisks
        
        :Parameters:
          -. image : nibabel.Nifti1Image, the nibabel image
        """

        import numpy as np

        # isolate constants
        COORDS_IDX_KEY = {'x':0, 'y':1, 'z':2}
        COORDS_AXIS = {'x':(1, 2), 'y':(0, 2), 'z':(0, 1)}
        COORDS_THRESHOLD = {'x':(10., 90.), 'y':(90., 10.), 'z':(50., 90.)}
        
        # get the data and affine from nibabel information
        image = force_3d_image(image)
        fdata = image.get_fdata()
        affine = image.affine
        zooms = [affine[idx, idx] for idx in range(3)]
        
        # loop over each direction
        bounds = {}
        for direction in 'xyz':
            distribution = np.mean(fdata, axis=COORDS_AXIS[direction])
            
            # loop over low and high threshold
            bounds[direction] = []
            for thr in COORDS_THRESHOLD[direction]:
                # bounce back and forth to locate the bounds
                l_idx, u_idx = (0, len(distribution))
                total_area = np.trapezoid(distribution)
                
                while u_idx - l_idx > 1.:
                    idx = (l_idx + u_idx) // 2
                    area = np.trapezoid(distribution[:idx])
                    if area/total_area > (thr/100.)+0.005:
                        u_idx = idx
                    elif area/total_area < (thr/100.)-0.005:
                        l_idx = idx
                    else:
                        break
                
                bounds[direction].append(
                    affine[COORDS_IDX_KEY[direction], 3] + (idx * zooms[COORDS_IDX_KEY[direction]])
                )
        
        return bounds
    
    def force_3d_image(image):
        """
        check if the image is a 4d image. If it is, time average the data
        
        :Parameters:
          -. `image` : nibabel.Nifti1Image, the nibabel image
        """

        import numpy as np
        import nibabel as nib

        # check the image dimensionality
        if len(image.shape) > 3:
            # average along the time axis and return a Nifti
            fdata = image.get_fdata()
            fdata = np.mean(fdata, axis=3)
            return nib.Nifti1Image(fdata, image.affine)
        
        return image
    
    def calculate_colormap_limits(image, upper_limit=UPPER_COLORMAP_LIMIT):
        """ calculate the colormap's limits by:
        (a) weighting the voxels closest to the center
        (b) set the lower bound to 0. and the upper bound to a value in the 
        upper_limit-th percentile
        
        :Parameters:
          -. `image` : nibabel.Nifti1Image, the nibabel image
          -. `upper_limit` : float, value between 0 and 100
        """

        import math
        import numpy as np

        image = force_3d_image(image)
        fdata = image.get_fdata()
        
        # let's create a vectorizing function as a nested function. This will 
        #   make 0 -> root(2)/2  |  0.5 -> 1.0  |  1.0 -> root(2)/2
        def vector_function(float_):
            """
            used for numpy.vectorize

            :Parameters:
              -. `float_` : float (duh), a value between 0. and 1.
            """

            return math.sin(float_ * math.pi / 2. + math.pi / 4.)
        
        # create a 3d array of 1s, multiply that by the x vector function above
        #   then the y and z. This gives a 3d array where the innermost voxels 
        #   will have a value of 1 and the outermost will be (root(2)/2.)**3.
        wa = np.ones(image.shape)
        vec = np.vectorize(vector_function)
        wa *= vec(np.linspace(0., 1., fdata.shape[0]))[:, None, None]
        wa *= vec(np.linspace(0., 1., fdata.shape[1]))[None, :, None]
        wa *= vec(np.linspace(0., 1., fdata.shape[2]))[None, None, :]
        
        wght_fdata = wa * fdata
        
        # set lower bound to 0. and upper bound to the xth percentile (ignoring
        #  all values less than 0.)
        return 0., np.percentile(wght_fdata[wght_fdata > 0.], upper_limit)
    
    def draw_lines_on_image(image, numx, numy):
        """
        draw orthogonal lines over top an Image obj. I don't really see a use
        case outside of motion correction.
        
        :Parameters:
          -. `image`: Image obj, the image
          -. `numx`: int, number of equally spaced vertical lines
          -. `numy`: int, number of equally spaced horizontal lines
        """

        import numpy as np
        from PIL import ImageDraw

        # draw lines
        w, h = image.size
        draw = ImageDraw.Draw(image)
        for line_height in np.linspace(0, h, numy)[1:-1]:
            draw.line((0, line_height, w, line_height), width=1)
        for line_width in np.linspace(0, w, numx)[1:-1]:
            draw.line((line_width, 0, line_width, h), width=1)
        
        return image
    
    # ============================================================ Control Flow
    if type_ == 'image':
        return image_report(in_files[0], additional_args[0])
    elif type_ == 'motion correction':
        return motion_correction_report(
            in_files[0],
            in_files[1],
            in_files[2:],
            *additional_args
        )
    elif type_ == 'coregistration':
        return coregistration_report(
            in_files[0],
            in_files[1],
            *additional_args
        )
    elif type_ == 'tacs':
        return tacs_report(
            in_files[0],
            *additional_args
        )
