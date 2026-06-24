# =======================================
# Imports
import copy
import os
import shutil
import glob
import nibabel as nib
from pathlib import Path

from nipype import Function
from nipype.interfaces.utility import Merge

from picnic.workflows.custom_workflow_constructors import NipibipyWorkflow
from picnic.interfaces.nibabel_nodes import _reorient_image, _crop_image
from picnic.interfaces.custom_fsl_interfaces import ApplyXfm4D
from picnic.interfaces.io_nodes import _rename_image, _find_associated_sidecar
from picnic.interfaces.nilearn_nodes import _create_report
from picnic.interfaces.string_template_nodes import _fill_report_template


# =======================================
# Constants
REPORT_TEMPLATE_PATH = os.path.join(
    Path(__file__).parent.absolute(),
    'report_templates',
    'motion_correction_template.html'
)

# =======================================
# Classes
class MotionCorrectionWorkflow():
    """ A parent class for all the different motion correction methods. Most of 
    the steps will be the same across all types of this module (reorienting 
    base image, cropping, merging). This creates a parent class keep the same 
    steps, but overload the areas that differ across methods
    
    The public attributes that are important:
    wf - the nipype.Workflow
    """
    DEFAULT_PARAMS = {
        'name' : 'mcflirt_moco',
        'ref_vol' : 8,
        'smooth' : 4,
        'crop_start' : False,
        'crop_end' : False,
        'cost' : 'corratio',
        'mean' : False,
        'search_angle' : 0,
        'report' : True,
    }
    DEFAULT_INFLOWS = {
        'in_file' : None
    }
    
    def __init__(self, params, inflows):
        """
        Parameters
        ----------
        params - dict
            key/value pairs of the keyword's optional parameters. See the 
            above DEFAULT_PARAMS constant for a list of all available keys
        inflows - dict
            the inflows to the workflow, {"inflow name" : file-like str}. See 
            the above DEFAULT_INFLOWS constant for a list of available keys
        """
        self.params = copy.deepcopy(self.DEFAULT_PARAMS)
        self.params.update(params)
        self.inflows = copy.deepcopy(self.DEFAULT_INFLOWS)
        self.inflows.update(inflows)
    
    def build_workflow(self, sink_directory):
        """ create a nipype workflow to run freesurfer's reconall
        
        Parameters
        ----------
        sink_directory - file-like str
            The sink filepath or ''
        
        returns - custom_workflow_constructors.NipibipyWorkflow obj
        """
        self.wf = NipibipyWorkflow(
            name = self.params['name'],
            outflows = {},
            sink_directory = sink_directory
        )
        
        # the workflow steps
        self.reorient_in_file()
        self.crop_image()
        self.motion_correct()
        '''
        if self.params['celtc'] > 0:
            self.apply_celtc()
        '''
        self.rename_outputs()
        if self.params['report']:
            self.create_report()
        
        return self.wf
    
    def reorient_in_file(self):
        """ make sure the base image given to the motion correction module is 
        a nifti and in a diagonal affine
        """
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'in_file'
                ],
                output_names = [
                    'new_image_path'
                ],
                function = _reorient_image
            ),
            name = 'reorient_in_file',
            inflows = {
                'in_file' : self.inflows['in_file']
            },
            outflows = (
                'new_image_path',
            )
        )
    
    def crop_image(self):
        """ use nibabel to crop the image
        """
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'in_file',
                    'crop_start',
                    'crop_end'
                ],
                output_names = [
                    'new_image_path'
                ],
                function = _crop_image
            ),
            name = 'crop_image',
            inflows = {
                'in_file' : '@reorient_in_file',
                'crop_start' : self.params['crop_start'],
                'crop_end' : self.params['crop_end']
            },
            outflows = (
                'new_image_path',
            )
        )
    
    def motion_correct(self):
        """ this will be overloaded by all its children
        """
        pass
    
                
    def rename_outputs(self):
        """ standardize the filenames to the workflow name
        """
        # search for an associated json
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'in_filepaths'
                ],
                output_names = [
                    'sidecar'
                ],
                function = _find_associated_sidecar
            ),
            name = 'find_sidecar',
            inflows = {
                'in_filepaths' : [self.inflows['in_file']]
            },
            outflows = (
                'sidecar',
            )
        )
        
        # standardize the mask name
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'basename',
                    'in_file',
                    'sidecar'
                ],
                output_names = [
                    'new_image_path',
                    'new_sidecar'
                ],
                function = _rename_image
            ),
            name = 'standarized_filenames',
            inflows = {
                'basename' : self.params['name'],
                'in_file' : '@get_motion_corrected_file',
                'sidecar' : '@find_sidecar'
            },
            outflows = (
                'new_image_path',
                'new_sidecar'
            ),
            to_sink = [
                'new_image_path',
                'new_sidecar'
            ]
        ) 
    
    def create_report(self):
        """ create a report
        """
        # need to put the out image as a list obj
        self.wf.add_node(
            interface = Merge(3),
            name = 'report_merge',
            inflows = {
                'in1' : '@reorient_in_file',
                'in2' : '@standarized_filenames.new_image_path',
                'in3' : '@centralize_xfm_mats.all_mats'
            },
            outflows = (
                'out',
            )
        )
        
        # report images
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'type_',
                    'in_files',
                    'additional_args'
                ],
                output_names = [
                    'reports'
                ],
                function = _create_report
            ),
            name = 'create_report',
            inflows = {
                'type_' : 'motion correction',
                'in_files' : '@report_merge',
                'additional_args' : [
                    self.params['ref_vol'],
                    'motion_correction'
                ]
            },
            outflows = (
                'reports',
            ),
            to_sink = [
                'reports'
            ]
        )
        
        self.wf.add_node(
            interface = Function(
                input_names = [
                    'html_template',
                    'parameters'
                ],
                output_names = [
                    'html'
                ],
                function = _fill_report_template
            ),
            name = 'report_template',
            inflows = {
                'html_template' : REPORT_TEMPLATE_PATH,
                'parameters' :{
                    'type' : self.params['type'],
                    'ref_vol' : self.params['ref_vol'],
                    'smooth' : self.params['smooth'],
                    'crop_start' : self.params['crop_start'],
                    'crop_end' : self.params['crop_end'],
                    'cost' : self.params['cost'],
                    'mean' : self.params['mean'],
                    'search_angle' : self.params['search_angle'],
                }
            },
            outflows = (
                'html',
            ),
            to_sink = [
                'html'
            ]
        )
    
class FlirtMocoWorkflow(MotionCorrectionWorkflow):
    """ child object using flirt to motion correct
    """
    def __init__(self, params, inflows):
        """
        Parameters
        ----------
        params - dict
            key/value pairs of the keyword's optional parameters.
        inflows - list
            list of file-like strs
        """
        params['type'] = 'flirt'
        super().__init__(params, inflows)
    
    def motion_correct(self):
        """ use FLIRT to motion correct each frame to a reference, either 
        single volume or mean image
        """

        from nipype.interfaces import fsl

        # smooth the image
        last_node_name = '@crop_image'
        if self.params['smooth'] > 0:
            self.wf.add_node(
                interface = fsl.IsotropicSmooth(),
                name = 'smooth',
                inflows = {
                    'in_file' : '@crop_image',
                    'fwhm' : self.params['smooth']
                },
                outflows = (
                    'out_file',
                )
            )
            last_node_name = '@smooth'
        
        # get the reference volume, either mean or a frame
        if self.params['mean'] is True:
            self.wf.add_node(
                interface = fsl.MeanImage(),
                name = 'get_reference_volume',
                inflows = {
                    'dimension' : 'T',
                    'in_file' : last_node_name
                },
                outflows = (
                    'out_file',
                )
            )
        else:
            self.wf.add_node(
                interface = fsl.ExtractROI(),
                name = 'get_reference_volume',
                inflows = {
                    't_min' : self.params['ref_vol'] - self.params['crop_start'],
                    't_size' : 1,
                    'in_file' : last_node_name
                },
                outflows = (
                    'roi_file',
                )
            )
        
        # split the 4d image into a list of 3d images
        self.wf.add_node(
            interface = fsl.Split(),
            name = 'split_4d',
            inflows = {
                'dimension' : 't',
                'in_file' : '@crop_image'
            },
            outflows = (
                'out_files',
            )
        )
        
        # adjust the inflow to account for all the flirt options
        flirt_inflows = {
            'bins' : 256,
            'dof' : 6,
            'in_file' : '@split_4d',
            'reference' : '@get_reference_volume'
        }
        if self.params['cost']:
            flirt_inflows['cost'] = self.params['cost']
        if self.params['search_angle'] > 0:
            flirt_inflows['coarse_search'] = self.params['search_angle']
            flirt_inflows['fine_search'] = self.params['search_angle'] // 3
            flirt_inflows['searchr_x'] = [-self.params['search_angle'], self.params['search_angle']]
            flirt_inflows['searchr_y'] = [-self.params['search_angle'], self.params['search_angle']]
            flirt_inflows['searchr_z'] = [-self.params['search_angle'], self.params['search_angle']]
            if self.params['cost']:
                flirt_inflows['cost_func'] = self.params['cost']
        else:
            flirt_inflows['no_search'] = True
        
        # use flirt to acquire the rigid transformations
        self.wf.add_mapnode(
            interface = fsl.FLIRT(),
            name = 'flirt_registration',
            inflows = flirt_inflows,
            outflows = (
                'out_matrix_file',
            ),
            iterfield = [
                'in_file'
            ]
        )
        
        # centralize all the transforms
        self.wf.add_node(
            Function(
                input_names = [
                    'in_mat_files',
                    'crop_start',
                    'original_image'
                ],
                output_names = [
                    'mat_dir',
                    'all_mats'
                ],
                function = _grab_flirt_transforms
            ),
            name = 'centralize_xfm_mats',
            inflows = {
                'in_mat_files' : '@flirt_registration',
                'crop_start' : self.params['crop_start'],
                'original_image' : '@reorient_in_file'
            },
            outflows = (
                'mat_dir',
                'all_mats'
            ),
            to_sink = [
                'all_mats'
            ]
        )
        
        # use the applyxfm4d executable
        self.wf.add_node(
            interface = ApplyXfm4D(),
            name = 'get_motion_corrected_file',
            inflows = {
                'four_digit' : True,
                'xfm_dir' : '@centralize_xfm_mats.mat_dir',
                'in_file' : '@reorient_in_file',
                'ref_vol' : '@reorient_in_file'
            },
            outflows = (
                'out_file',
            )
        )

class McflirtMocoWorkflow(MotionCorrectionWorkflow):
    """ child object using flirt to motion correct
    """
    def __init__(self, params, inflows):
        """
        Parameters
        ----------
        params - dict
            key/value pairs of the keyword's optional parameters.
        inflows - list
            list of file-like strs
        """
        params['type'] = 'mcflirt'
        super().__init__(params, inflows)
    
    def motion_correct(self):
        """ use FLIRT to motion correct each frame to a reference, either 
        single volume or mean image
        """

        from nipype.interfaces import fsl

        # change blank or incomplete parameters to the defaults
        if not self.params['cost']:
            self.params['cost'] = 'normcorr'
        if self.params['smooth'] == 0:
            self.params['smooth'] = 1.0
        
        # use mcflirt to motion correct
        self.wf.add_node(
            interface = fsl.MCFLIRT(),
            name = 'mcflirt_registration',
            inflows = {
                'in_file' : '@crop_image',  # something
                'ref_vol' : self.params['ref_vol'],
                'mean_vol' : self.params['mean'],
                'cost' : self.params['cost'],
                'save_mats' : True,
                'smooth' : self.params['smooth']
            },
            outflows = (
                'mat_file',
                'out_file'
            )
        )
        
        # centralize all the transforms
        self.wf.add_node(
            Function(
                input_names = [
                    'in_mat_files',
                    'crop_start',
                    'original_image'
                ],
                output_names = [
                    'mat_dir',
                    'all_mats'
                ],
                function = _grab_flirt_transforms
            ),
            name = 'centralize_xfm_mats',
            inflows = {
                'in_mat_files' : '@mcflirt_registration.mat_file',
                'crop_start' : self.params['crop_start'],
                'original_image' : '@reorient_in_file'
            },
            outflows = (
                'mat_dir',
                'all_mats'
            ),
            to_sink = [
                'all_mats'
            ]
        )
        
        # use the applyxfm4d executable
        self.wf.add_node(
            interface = ApplyXfm4D(),
            name = 'get_motion_corrected_file',
            inflows = {
                'four_digit' : True,
                'xfm_dir' : '@centralize_xfm_mats.mat_dir',
                'in_file' : '@reorient_in_file',
                'ref_vol' : '@reorient_in_file'
            },
            outflows = (
                'out_file',
            )
        )

class TwoStepMocoWorkflow(MotionCorrectionWorkflow):
    """ child object using flirt to motion correct
    """
    def __init__(self, params, inflows):
        """
        Parameters
        ----------
        params - dict
            key/value pairs of the keyword's optional parameters.
        inflows - list
            list of file-like strs
        """
        params['type'] = 'twostep'
        super().__init__(params, inflows)
    
    def motion_correct(self):
        """ use FLIRT to motion correct each frame to a reference, either 
        single volume or mean image
        """

        from nipype.interfaces import fsl

        # change blank or incomplete parameters to the defaults
        if not self.params['cost']:
            self.params['cost'] = 'normcorr'
        if self.params['smooth'] == 0:
            self.params['smooth'] = 1.0
        
        # get the tmean of the cropped image
        self.wf.add_node(
            interface = fsl.MeanImage(),
            name = 'get_tmean',
            inflows = {
                'dimension' : 'T',
                'in_file' : '@crop_image'
            },
            outflows = (
                'out_file',
            )
        )
        
        # split the 4d image into a list of 3d images
        self.wf.add_node(
            interface = fsl.Split(),
            name = 'split_4d',
            inflows = {
                'dimension' : 't',
                'in_file' : '@crop_image'
            },
            outflows = (
                'out_files',
            )
        )
        
        # adjust the inflow to account for all the flirt options
        flirt_inflows = {
            'bins' : 256,
            'dof' : 6,
            'in_file' : '@split_4d',
            'reference' : '@get_tmean'
        }
        if self.params['cost']:
            flirt_inflows['cost'] = self.params['cost']
        if self.params['search_angle'] > 0:
            flirt_inflows['coarse_search'] = self.params['search_angle']
            flirt_inflows['fine_search'] = self.params['search_angle'] // 3
            flirt_inflows['searchr_x'] = [-self.params['search_angle'], self.params['search_angle']]
            flirt_inflows['searchr_y'] = [-self.params['search_angle'], self.params['search_angle']]
            flirt_inflows['searchr_z'] = [-self.params['search_angle'], self.params['search_angle']]
            if self.params['cost']:
                flirt_inflows['cost_func'] = self.params['cost']
        else:
            flirt_inflows['no_search'] = True
        
        # use flirt to acquire the rigid transformations
        self.wf.add_mapnode(
            interface = fsl.FLIRT(),
            name = 'flirt_registration',
            inflows = flirt_inflows,
            outflows = (
                'out_matrix_file',
            ),
            iterfield = [
                'in_file'
            ]
        )
        
        # centralize the first transforms
        self.wf.add_node(
            Function(
                input_names = [
                    'in_mat_files',
                    'crop_start',
                    'original_image'
                ],
                output_names = [
                    'mat_dir',
                    'all_mats'
                ],
                function = _grab_flirt_transforms
            ),
            name = 'centralize_first_mats',
            inflows = {
                'in_mat_files' : '@flirt_registration',
                'crop_start' : 0,
                'original_image' : '@crop_image'
            },
            outflows = (
                'mat_dir',
                'all_mats'
            )
        )
        
        # use the applyxfm4d executable
        self.wf.add_node(
            interface = ApplyXfm4D(),
            name = 'get_first_correction_file',
            inflows = {
                'four_digit' : True,
                'xfm_dir' : '@centralize_first_mats.mat_dir',
                'in_file' : '@crop_image',
                'ref_vol' : '@crop_image'
            },
            outflows = (
                'out_file',
            )
        )
        
        # use mcflirt to motion correct
        self.wf.add_node(
            interface = fsl.MCFLIRT(),
            name = 'mcflirt_registration',
            inflows = {
                'in_file' : '@get_first_correction_file',
                'ref_vol' : self.params['ref_vol'],
                'mean_vol' : self.params['mean'],
                'cost' : self.params['cost'],
                'save_mats' : True,
                'smooth' : self.params['smooth']
            },
            outflows = (
                'mat_file',
                'out_file'
            )
        )
        
        # centralize the second transforms
        self.wf.add_node(
            Function(
                input_names = [
                    'in_mat_files',
                    'crop_start',
                    'original_image'
                ],
                output_names = [
                    'mat_dir',
                    'all_mats'
                ],
                function = _grab_flirt_transforms
            ),
            name = 'centralize_second_mats',
            inflows = {
                'in_mat_files' : '@mcflirt_registration.mat_file',
                'crop_start' : 0,
                'original_image' : '@crop_image'
            },
            outflows = (
                'mat_dir',
                'all_mats'
            )
        )
        
        # combine the first and second transforms
        self.wf.add_mapnode(
            interface = fsl.ConvertXFM(),
            name = 'combine_xfms',
            inflows = {
                'in_file' : '@centralize_first_mats.all_mats',
                'concat_xfm' : True,
                'in_file2' : '@centralize_second_mats.all_mats'
            },
            outflows = (
                'out_file',
            ),
            iterfield = [
                'in_file',
                'in_file2'
            ]
        )
        
        # centralize the combined transforms
        self.wf.add_node(
            Function(
                input_names = [
                    'in_mat_files',
                    'crop_start',
                    'original_image'
                ],
                output_names = [
                    'mat_dir',
                    'all_mats'
                ],
                function = _grab_flirt_transforms
            ),
            name = 'centralize_xfm_mats',
            inflows = {
                'in_mat_files' : '@combine_xfms',
                'crop_start' : self.params['crop_start'],
                'original_image' : '@reorient_in_file'
            },
            outflows = (
                'mat_dir',
                'all_mats'
            ),
            to_sink = [
                'all_mats'
            ]
        )
        
        # use the applyxfm4d executable
        self.wf.add_node(
            interface = ApplyXfm4D(),
            name = 'get_motion_corrected_file',
            inflows = {
                'four_digit' : True,
                'xfm_dir' : '@centralize_xfm_mats.mat_dir',
                'in_file' : '@reorient_in_file',
                'ref_vol' : '@reorient_in_file'
            },
            outflows = (
                'out_file',
            )
        )


# =======================================
# Functions

# =======================================
# Nipype Specific Functions
def _grab_flirt_transforms(in_mat_files, crop_start, original_image):
    """ a nipype function used to take all the xfm matrices and put them in one 
    place with a standardized naming convention
    
    Parameters
    ----------
    in_mat_files - list, tuple
        a list of transform matrices
    crop_start - int
        how many frames we crop out of the start of image
    original_image - file-like str
        the original, un-motion corrected image. This determines how many frames
        we need
    """

    import os
    import shutil
    import glob
    import nibabel as nib

    # if tuple, force to be list
    if not isinstance(in_mat_files, list):
        in_mat_files = [in_mat_files]
    
    # set up flags
    check_dir = os.getcwd()
    idx = 0
    
    # use the first transformation matrix for all the beginning skipped frames
    while idx < crop_start:
        _ = shutil.copy(in_mat_files[0], os.path.join(check_dir, 'MAT_'+str(idx).zfill(4)))
        idx += 1
    
    # loop over all the transformation matrices and copy them to the working dir
    for fn in in_mat_files:
        _ = shutil.copy(fn, os.path.join(check_dir, 'MAT_'+str(idx).zfill(4)))
        idx += 1

    # use the last transformation matrix for all the ending skipped frames
    image = nib.load(original_image)
    while idx < image.shape[3]:
        _ = shutil.copy(in_mat_files[-1], os.path.join(check_dir, 'MAT_'+str(idx).zfill(4)))
        idx += 1
    
    all_mats = glob.glob('MAT_*')
    all_mats = [os.path.join(os.getcwd(), m) for m in all_mats]
    
    return check_dir, all_mats
