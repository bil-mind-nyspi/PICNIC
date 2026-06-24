# =======================================
# Imports

# =======================================
# Constants

# =======================================
# Classes

# =======================================
# Functions
def create_report(report_type, files, basename='', extras=None):
    """ a function to create reports
    
    Parameters
    ----------
    report_type - str
        the type of report to create
    files - list
        a list of input files
    """

    if extras is None:
        extras = list()

    # control flow for reports
    #  image report
    if report_type=='image':
        return image_summary(files[0], basename)
    
    # motion correction report
    elif report_type=='motioncorrection':
        return motion_correction_summary(
            base_file = files[0],
            moco_file = files[1],
            mats = files[2:],
            ref_frame = extras[0],
            basename = basename
        )
    
    # coregistration report
    elif report_type=='coregistration':
        return coregistration_summary(
            base_file = files[0],
            overlay_file = files[1],
            basename = basename
        )
    
    # camra report
    elif report_type=='camra':
        return camra_summary(
            base_file = files[0],
            overlay_files = files[1],
            rank_list = extras[0],
            mats = files[2:],
            rank = extras[1],
            basename = basename
        )
    
    # tacs report
    elif report_type=='tacs':
        return tacs_summary(
            tacs_file = files[0],
            units = extras[0],
            basename = basename
        )


def image_summary(in_file, basename='image'):
    """ wrap the necessary steps to create a summary report of \*image

    Parameters
    ----------
    in_file - file-like string
        the image for which we are creating a summary
    basename - string
        the basename for the output filename
    """

    import os
    import numpy as np
    import nibabel as nib
    from PIL import Image
    from nilearn.plotting import plot_anat

    # load file and calculate coords bounds
    image = nib.load(in_file)
    cut_coords_bounds = calculate_cut_coords_bounds(image)
    filename = os.path.join(os.getcwd(), basename+'.png')

    # if the image is a 4d image, assume it is a pet image and create a summary movie
    if len(image.shape)==4:
        # tmean the 4d image and create a screenshot
        fdata = image.get_fdata()
        mean_image = nib.Nifti1Image(np.mean(fdata, axis=3), image.affine)
        clim = advanced_colorbar_limits(mean_image)
        coords = plot_anat(mean_image, cut_coords_bounds, cmap='jet', vmin=clim[0], vmax=clim[1])
        assembled_image = assemble_images([Image.open(coords[direction]) for direction in 'yxz'])
        assembled_image.save(filename)

        # loop over all the frames and create a mosaic image for each
        assembled_images = []
        for frame in range(fdata.shape[3]):
            slice_image = nib.Nifti1Image(fdata[:,:,:,frame], image.affine)
            coords = plot_anat(slice_image, cut_coords_bounds, cmap='jet', vmin=clim[0], vmax=clim[1])
            assembled_images.append(assemble_images([Image.open(coords[direction]) for direction in 'yxz']))

        # create a movie from the saved images
        movie_filename = os.path.join(os.getcwd(), basename+'.mp4')
        create_mp4_from_image_list(assembled_images, movie_filename)

        return (filename, movie_filename)
    else:
        coords = plot_anat(image, cut_coords_bounds)
        assembled_image = assemble_images([Image.open(coords[direction]) for direction in 'yxz'])

        # save the image
        assembled_image.save(filename)

        movie_filename = os.path.join(os.getcwd(), basename+'.txt')
        with open(movie_filename, 'w') as f:
            _ = f.write('3d image. No movie')

        return (filename, movie_filename)


def motion_correction_summary(base_file, moco_file, mats=None, ref_frame=None, basename='motion_correction'):
    """ wrap the necessary steps to create a desired subsidiary of the \*image summary

    Parameters
    ----------
    base_file - file-like string
        the base image
    moco_file - file-like string
        the motion corrected image
    mats - list
        a list of all the transformation matrices
    ref_frame - int
        which frame is the reference frame
    basename - string
        the basename for the output filename
    """

    import os
    import numpy as np
    import nibabel as nib
    from math import atan2, asin, degrees
    from PIL import Image, ImageDraw

    # load files and calculate coords bounds
    base_image = nib.load(base_file)
    moco_image = nib.load(moco_file)
    cut_coords_bounds = calculate_cut_coords_bounds(moco_image)
    filename = os.path.join(os.getcwd(), basename+'.mp4')

    # loop through all the transformation matrices and derive all 6 dofs
    if mats is not None:
        all_dof = []
        for mat in mats:
            m = np.loadtxt(mat)
            x, y, z = m[0,3], m[1, 3], m[2, 3]
            rx = degrees(atan2(-m[1, 2], m[2, 2]))
            ry = degrees(asin(m[0, 2]))
            rz = degrees(atan2(-m[0, 1], m[0, 0]))
            all_dof.append(np.array([x, y, z, rx, ry, rz]))
        all_dof = np.array(all_dof)

    # get ready to create some motion correction graphs
    base_fdata = base_image.get_fdata()
    moco_fdata = moco_image.get_fdata()
    clim = advanced_colorbar_limits(
        nib.Nifti1Image(
            np.mean(base_fdata, axis=3),
            base_image.affine
        )
    )
    t = np.arange(base_fdata.shape[3])

    # loop over each frame and create some brain images and a transformation graph
    assembled_images = []
    for frame in range(base_fdata.shape[3]):
        coords = []
        for img in (base_fdata, moco_fdata):
            coords.append(
                plot_motion_correction_image(
                    nib.Nifti1Image(img[:,:,:,frame], base_image.affine),
                    cut_coords_bounds,
                    cmap='jet',
                    vmin=clim[0],
                    vmax=clim[1]
                )
            )

            # draw lines on the brain images
            i = Image.open(coords[-1])
            w, h = i.size
            draw = ImageDraw.Draw(i)
            for line_height in np.linspace(0, h, 9)[1:-1]:
                draw.line((0, line_height, w, line_height), width=1)
            for line_width in np.linspace(0, w, 23)[1:-1]:
                draw.line((line_width, 0, line_width, h), width=1)
            i.save(coords[-1].name)

        # create the transformation graph
        if mats is not None:
            coords.append(plot_motion_correction_graph(t, all_dof, frame, ref_frame))

        assembled_images.append(assemble_images([Image.open(c) for c in coords], STANDARD_WIDTH=600))

    # create a movie from the saved images
    create_mp4_from_image_list(assembled_images, filename)

    return filename


def coregistration_summary(base_file, overlay_file, basename='coregistration'):
    """ use nilearn create a movie for coregistration

    Parameters
    ----------
    base_file - file-like string
        the base file
    overlay_file - file-like string
        the overlaying image file
    basename - string
        the basename for the output filename
    """

    import os
    import numpy as np
    import nibabel as nib
    from PIL import Image

    # load all the files with nibabel and tmean all the 4d images
    imgs = []
    for fn in (base_file, overlay_file):
        img = nib.load(fn)
        if len(img.shape)==4:
            img = nib.Nifti1Image(np.mean(img.get_fdata(), axis=3), img.affine)
        imgs.append(img)
    clim = advanced_colorbar_limits(imgs[1])
    cut_coords_bounds = calculate_cut_coords_bounds(imgs[0])
    filename = os.path.join(os.getcwd(), basename+'.mp4')

    # plot the overlaid images
    assembled_images = []
    for alpha in np.linspace(0.0, 0.7, 6):
        coords = plot_coregistration(imgs[1], imgs[0], cut_coords_bounds, alpha=alpha, vmin=clim[0], vmax=clim[1])
        assembled_images.append(assemble_images([Image.open(coords[direction]) for direction in 'xyz']))

    # create a movie from the saved images
    create_mp4_from_image_list(assembled_images, filename)

    return filename


def camra_summary(base_file, overlay_files, rank_list, mats=None, rank=1, basename='motion_correction'):
    """ wrap the necessary steps to create a desired subsidiary of the \*image summary

    Parameters
    ----------
    base_file - file-like string
        the base image (aka T1)
    overlay_files - list of file-like strings
        the camra attempts
    mats - list
        a list of all the transformation matrices
    rank - int
        which camra method was picked
    basename - string
        the basename for the output filename
    """

    import os
    import numpy as np
    import nibabel as nib
    from math import atan2, asin, degrees, ceil
    from PIL import Image

    # load files and calculate coords bounds
    base_image = nib.load(base_file)
    overlay_images = []
    for fn in overlay_files:
        img = nib.load(fn)
        if len(img.shape)==4:
            img = nib.Nifti1Image(np.mean(img.get_fdata(), axis=3), img.affine)
        overlay_images.append(img)
    cut_coords_bounds = calculate_cut_coords_bounds(base_image)
    clim = advanced_colorbar_limits(overlay_images[0])
    filename = os.path.join(os.getcwd(), basename+'.mp4')
    sorted_rank_list = sorted(rank_list)

    # create a toggle of for all mri and overlaid coreg movie
    assembled_images = []
    STANDARD_WIDTH = 300
    toggle_filename = os.path.join(os.getcwd(), basename+'_toggle.mp4')
    for alpha in [0.0, 0.7]:
        images = []
        for idx in sorted_rank_list:
            img = overlay_images[rank_list.index(idx)]
            images.append(
                plot_camra_image(
                    base_image,
                    img,
                    cut_coords_bounds,
                    cmap='jet',
                    alpha=alpha,
                    vmin=clim[0],
                    vmax=clim[1],
                    title=str(idx)
                )
            )

        # open the temporary images and resize them to the same width
        images_across = 4
        images = [Image.open(im) for im in images]
        resized_images = [
            im.resize((STANDARD_WIDTH, ceil(im.size[1]*(STANDARD_WIDTH/im.size[0]))))
            for im in images
        ]
        widths, heights = zip(*(im.size for im in resized_images))
        assembled_image = Image.new(
            'RGB',
            (
                ceil(STANDARD_WIDTH*images_across/10.)*10,
                ceil(ceil(len(images)/images_across)*heights[0]/10.)*10
            )
        )

        # paste all three resized images into one new image
        y_offset = 0
        for idx, im in enumerate(resized_images):
            assembled_image.paste(im, (int((idx % images_across)*STANDARD_WIDTH), y_offset))
            if idx % images_across == images_across-1:
                y_offset += im.size[1]
        assembled_images.append(assembled_image)
    create_mp4_from_image_list(assembled_images, toggle_filename)

    # loop through all the transformation matrices and derive all 6 dofs
    if mats is not None:
        all_dof = []
        for idx in sorted_rank_list:
            m = np.loadtxt(mats[rank_list.index(idx)])
            x, y, z = m[0,3], m[1, 3], m[2, 3]
            rx = degrees(atan2(-m[1, 2], m[2, 2]))
            ry = degrees(asin(m[0, 2]))
            rz = degrees(atan2(-m[0, 1], m[0, 0]))
            all_dof.append(np.array([x, y, z, rx, ry, rz]))

        autoselect_mat = all_dof[rank-1]
        all_dof = [d-autoselect_mat for d in all_dof]
        all_dof = np.array(all_dof)

    # plot the overlay for the autoselected image
    auto_overlay_plot = plot_camra_image(
        base_image, overlay_images[rank-1], cut_coords_bounds, cmap='jet', alpha=0.2, vmin=clim[0], vmax=clim[1]
    )

    # loop over each camra method and create some brain images and a transformation graph
    assembled_images = []
    for idx in sorted_rank_list:
        img = overlay_images[rank_list.index(idx)]
        coords = [auto_overlay_plot]
        coords.append(
            plot_camra_image(
                base_image, img, cut_coords_bounds, cmap='jet', alpha=0.2, vmin=clim[0], vmax=clim[1], title=str(idx)
            )
        )

        # create the transformation graph
        if mats is not None:
            coords.append(plot_camra_graph(sorted_rank_list, all_dof, idx, rank))

        assembled_images.append(assemble_images([Image.open(c) for c in coords], STANDARD_WIDTH=600))

    # create a movie from the saved images
    create_mp4_from_image_list(assembled_images, filename)

    return (filename, toggle_filename)


def tacs_summary(tacs_file, units, basename='tacs'):
    """ use matplotlib to plot all the tacs

    Parameters
    ----------
    tacs_file - file-like string
        the tac tsv
    units - string
        uci or bq
    basename - string
        the basename for the output filename
    """

    import os
    import pandas as pd
    import matplotlib.pyplot as plt

    # load tacs files
    data = pd.read_csv(tacs_file, delimiter='\t', header=0, index_col=0)

    # create a plot
    fig, ax = plt.subplots(figsize=(12, 4))
    ax = data.plot(ax=ax)
    ax.legend().remove()
    ax.title.set_text('All TACs')
    _ = ax.set_xlabel('Time (min)')
    if units=='uci':
        _ = ax.set_ylabel('Counts (uCi/cc)')
    elif units=='bq':
        _ = ax.set_ylabel('Counts (Bq/mL)')
    _ = ax.set_xlim(0.)

    # save file
    filename = os.path.join(os.getcwd(), basename+'.png')
    fig.savefig(filename)

    return filename


def calculate_cut_coords_bounds(nifti):
    """ use nibabel to calculate the cut coords bounds

    Parameters
    ----------
    nifti - nibabel.Nifti1Image
        the nibabel image
    """

    import numpy as np

    # isolate constants
    COORDS_IDX_KEY = {'x':0, 'y':1, 'z':2}
    COORDS_AXIS = {'x':(1, 2), 'y':(0, 2), 'z':(0, 1)}
    COORDS_THRESHOLD = {'x':(10., 90.), 'y':(90., 10.), 'z':(50., 90.)}

    # get the data and affine from nibabel information
    fdata = nifti.get_fdata()
    if len(fdata.shape)==4:
        fdata = np.mean(fdata, axis=3)
    affine = nifti.affine
    zooms = [affine[i, i] for i in range(3)]

    # loop over each direction
    cut_coords_bounds = dict()
    for direction in 'xyz':
        dist = np.mean(fdata, axis=COORDS_AXIS[direction])

        cut_coords_bounds[direction] = []
        for thr in COORDS_THRESHOLD[direction]:
            lower_idx, upper_idx = int(0), len(dist)
            total_area = np.trapezoid(dist)

            while upper_idx-lower_idx > 1.:
                idx = (lower_idx + upper_idx) // 2
                area = np.trapezoid(dist[:idx])
                if area/total_area > (thr/100.)+0.005:
                    upper_idx = idx
                elif area/total_area < (thr/100.)-0.005:
                    lower_idx = idx
                else:
                    break

            cut_coords_bounds[direction].append(
                affine[COORDS_IDX_KEY[direction], 3] + (idx * zooms[COORDS_IDX_KEY[direction]])
            )

    return cut_coords_bounds


def plot_anat(image, cut_coords_bounds, cmap='gray', vmin=None, vmax=None, n_cuts=7):
    """ use nilearn.plotting to plot the anatomy

    Parameters
    ----------
    image - nibabel.Nifti1Image
        the nibabel image
    cut_coords_bounds - dict
        the cut bounds in xyz (mm); must contain 'x', 'y' and 'z' key
    cmap - string
        color map
    vmin - float
        the min value for the color map
    vmax - float
        the min value for the color map
    """

    import tempfile
    import numpy as np
    from nilearn.plotting import plot_anat

    # create the temporary images for each direction (x, y and z)
    coords = dict()
    for direction in 'xyz':
        coords[direction] = tempfile.NamedTemporaryFile(suffix='.png').name
        _ = plot_anat(
            image,
            display_mode=direction,
            cut_coords=np.linspace(*cut_coords_bounds[direction], n_cuts),
            output_file=coords[direction],
            dim=0.,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax
        )
    return coords


def plot_image_overlay(
        overlay_image, base_image, cut_coords_bounds,
        direction='y', cmap='gray', n_cuts=5, alpha=0.7, vmin=None, vmax=None
):
    """ use nilearn.plotting to plot the anatomy

    Parameters
    ----------
    image - nibabel.Nifti1Image
        the nibabel image
    cut_coords_bounds - dict
        the cut bounds in xyz (mm); must contain 'x', 'y' and 'z' key
    direction - str
        the direction we are looking at. Should be 'x', 'y' or 'z'
    cmap - string
        color map
    n_cuts - int
        how many images per row
    alpha - float
        the opacity of the image
    vmin - float
        the min value for the color map
    vmax - float
        the min value for the color map
    """

    import tempfile
    import numpy as np
    from nilearn.plotting import plot_roi

    # create the temporary images for each direction (x, y and z)
    all_coords = np.linspace(*cut_coords_bounds[direction], 3*n_cuts+1)
    coords = []
    for line in range(3):
        coords.append(tempfile.NamedTemporaryFile(suffix='.png').name)
        _ = plot_roi(
            overlay_image,
            base_image,
            output_file=coords[-1],
            cut_coords=all_coords[int(line)*n_cuts:int(line)*n_cuts+n_cuts],
            display_mode=direction,
            alpha=alpha,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax
        )
    return coords


def plot_motion_correction_image(image, cut_coords_bounds, cmap='jet', vmin=None, vmax=None):
    """ use nilearn.plotting to plot the ortho for motion correction

    Parameters
    ----------
    image - nibabel.Nifti1Image
        the nibabel image
    cut_coords_bounds - dict
        the cut bounds in xyz (mm); must contain 'x', 'y' and 'z' key
    cmap - string
        color map
    vmin - float
        the min value for the color map
    vmax - float
        the min value for the color map
    """

    import tempfile
    import numpy as np
    from nilearn.plotting import plot_anat

    # create the temporary images for each direction (x, y and z)
    ortho_cut_coords = [np.mean(cut_coords_bounds[direction]) for direction in 'xyz']
    temp_png = tempfile.NamedTemporaryFile(suffix='.png').name
    _ = plot_anat(
        image,
        display_mode='ortho',
        cut_coords=ortho_cut_coords,
        output_file=temp_png,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        draw_cross=False
    )
    return temp_png


def plot_motion_correction_graph(t, all_dof, frame, ref_frame=None):
    """ create pyplots for motion correction

    Parameters
    ----------
    t - np array
        time
    all_dof - np array
        x, y, z, rx, ry, rz in an array
    frame - int
        denote which frame we are looking at
    ref_frame -int
        denote the reference frame
    """

    import tempfile
    import numpy as np
    import matplotlib.pyplot as plt

    # create a pyplot
    temp_png = tempfile.NamedTemporaryFile(suffix='.png').name
    fig, ax = plt.subplots(figsize=(9, 3))
    a, = ax.plot(t, all_dof[:, 0])
    a.set_label('x')
    b, = ax.plot(t, all_dof[:, 1])
    b.set_label('y')
    c, = ax.plot(t, all_dof[:, 2])
    c.set_label('z')
    d, = ax.plot(t, all_dof[:, 3])
    d.set_label('yaw')
    e, = ax.plot(t, all_dof[:, 4])
    e.set_label('pitch')
    f, = ax.plot(t, all_dof[:, 5])
    f.set_label('roll')

    # create vertical lines for the current and reference frame
    _ = ax.vlines(t[frame], np.min(all_dof[:, :3]), np.max(all_dof[:, :3]), colors='r', linestyles='dashed', label='current frame')
    if ref_frame is not None:
        _ = ax.vlines(ref_frame, np.min(all_dof[:, :3]), np.max(all_dof[:, :3]), colors='g', linestyles='dashed', label='reference frame')

    # create some labels
    ax.set_xlabel('Frame Number')
    ax.set_ylabel('Displacement (mm and deg)')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    fig.savefig(temp_png)
    plt.close('all')

    return temp_png


def plot_coregistration(
        overlay_image, base_image, cut_coords_bounds,
        cmap='jet', n_cuts=7, alpha=0.7, vmin=None, vmax=None
):
    """ use nilearn.plotting to plot the anatomy

    Parameters
    ----------
    image - nibabel.Nifti1Image
        the nibabel image
    cut_coords_bounds - dict
        the cut bounds in xyz (mm); must contain 'x', 'y' and 'z' key
    cmap - string
        color map
    n_cuts - int
        how many images per row
    alpha - float
        the opacity of the image
    vmin - float
        the min value for the color map
    vmax - float
        the min value for the color map
    """

    import tempfile
    import numpy as np
    from nilearn.plotting import plot_roi

    # create the temporary images for each direction (x, y and z)
    coords = dict()
    for direction in 'xyz':
        coords[direction] = tempfile.NamedTemporaryFile(suffix='.png').name
        _ = plot_roi(
            overlay_image,
            base_image,
            output_file=coords[direction],
            cut_coords=np.linspace(*cut_coords_bounds[direction], n_cuts),
            display_mode=direction,
            alpha=alpha,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax
        )
    return coords


def plot_camra_image(
        base_image, overlay_image, cut_coords_bounds,
        cmap='jet', alpha=0.5, vmin=None, vmax=None, title=None
):
    """ use nilearn.plotting to plot the ortho for motion correction

    Parameters
    ----------
    base_image - nibabel.Nifti1Image
        the nibabel image
    overlay_image - nibabel.Nifti1Image
        the nibabel image
    cut_coords_bounds - dict
        the cut bounds in xyz (mm); must contain 'x', 'y' and 'z' key
    cmap - string
        color map
    alpha - float
        the opacity number
    vmin - float
        the min value for the color map
    vmax - float
        the min value for the color map
    """

    import tempfile
    import numpy as np
    from nilearn.plotting import plot_roi

    # create the temporary images for each direction (x, y and z)
    ortho_cut_coords = [np.mean(cut_coords_bounds[direction]) for direction in 'xyz']
    temp_png = tempfile.NamedTemporaryFile(suffix='.png').name
    _ = plot_roi(
        overlay_image,
        base_image,
        display_mode='ortho',
        cut_coords=ortho_cut_coords,
        output_file=temp_png,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        alpha=alpha,
        draw_cross=False,
        title=title
    )
    return temp_png


def plot_camra_graph(t, all_dof, idx, autoselect=None):
    """ create pyplots for motion correction

    Parameters
    ----------
    t - numpy array
        time
    all_dof - numpy array
        x, y, z, rx, ry, rz in an array
    idx - int
        denote which frame we are looking at
    autoselect -int
        denote the reference frame
    """

    import tempfile
    import numpy as np
    import matplotlib.pyplot as plt

    # create a pyplot
    temp_png = tempfile.NamedTemporaryFile(suffix='.png').name
    fig, ax = plt.subplots(figsize=(9, 3))
    a, = ax.plot(t, all_dof[:, 0])
    a.set_label('x')
    b, = ax.plot(t, all_dof[:, 1])
    b.set_label('y')
    c, = ax.plot(t, all_dof[:, 2])
    c.set_label('z')
    d, = ax.plot(t, all_dof[:, 3])
    d.set_label('yaw')
    e, = ax.plot(t, all_dof[:, 4])
    e.set_label('pitch')
    f, = ax.plot(t, all_dof[:, 5])
    f.set_label('roll')

    # create vertical lines for the current and reference frame
    _ = ax.vlines(idx, np.min(all_dof[:, :3]), np.max(all_dof[:, :3]), colors='r', linestyles='dashed', label='Current')
    if autoselect is not None:
        _ = ax.vlines(autoselect, np.min(all_dof[:, :3]), np.max(all_dof[:, :3]), colors='g', linestyles='dashed', label='Autoselected')

    # create some labels
    ax.set_xlabel('CAMRA Attempt')
    ax.set_ylabel('Displacement (mm and deg)')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    fig.savefig(temp_png)
    plt.close('all')

    return temp_png


def assemble_images(images, STANDARD_WIDTH=1120):
    """ paste together images

    Parameters
    ----------
    image - list
        a list of all the images that will be pasted together
    """

    from PIL import Image

    # open the temporary images and resize them to the same width
    resized_images = [im.resize((STANDARD_WIDTH, int(im.size[1]*(STANDARD_WIDTH/im.size[0])))) for im in images]
    widths, heights = zip(*(im.size for im in resized_images))
    assembled_image = Image.new('RGB', (STANDARD_WIDTH, sum(heights)))

    # paste all three resized images into one new image
    y_offset = 0
    for im in resized_images:
        assembled_image.paste(im, (0, y_offset))
        y_offset += im.size[1]

    return assembled_image


def create_mp4_from_image_list(image_list, output_filename, fps=2):
    """ create a movie from a list of Image objects

    Parameters
    ----------
    image_list - list of Images
        list of mosaic images
    output_filename - string
        must be a movie file type (.mp4)
    fps - int
        frames per second
    """
    import os

    for idx, im in enumerate(image_list):
        im.save('image_'+str(idx).zfill(4)+'.png')

    os.system('ffmpeg -r '+str(fps)+' -f image2 -pattern_type glob -i "*.png" -vcodec libx264 -crf 20 -pix_fmt yuv420p '+output_filename)


def advanced_colorbar_limits(image):
    """ calculate the colorbar limits by reducing the weight of the edge most voxels

    Parameters
    ----------
    image - nibabel.Nifti1Image obj
        the pet image we are trying to get the colorbar limit from
    """

    import numpy as np
    from math import sin, pi

    fdata = image.get_fdata()

    # create the weighting array by using the sin function. The middle voxels
    #   will have a weight of 1.0, the outer frames will have a weight of
    #   root(2). Sin(pi/2) and sin(pi/4)|sin(3*pi/4) respectively
    weight_array = np.zeros(fdata.shape)
    x, y, z = weight_array.shape
    for i in range(x):
        for j in range(y):
            for k in range(z):
                weight_array[i, j, k] = np.prod([sin((float(a/b) * pi / 2.) + (pi / 4.)) for a, b in zip([i, j, k], [x, y, z])])
    weighted_fdata = weight_array * fdata
    return (0., np.percentile(weighted_fdata[weighted_fdata > 0.], 99.5))
