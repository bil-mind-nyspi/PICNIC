---
title: 'PICNIC: an open-source Python library for preprocessing of dynamic Positron Emission Tomography (PET) brain imaging data'
tags:
  - Python
  - PET
  - brain imaging
  - pet preprocessing
  - open-source
  - PICNIC
authors:
  - name: Mike Schmidt
    orcid: 0000-0003-4721-1457
    affiliation: "1, 2"
  - name: Jeffrey M Miller
    orcid: 0000-0002-2206-9311
    affiliation: "1, 2"
  - name: Eric Hauser
    affiliation: "1, 2"
  - name: Dheeraj Puthiya Veedu
    affiliation: "2"
  - name: Elizabeth A Bartlett
    orcid: 0000-0002-9174-9951
    affiliation: "1, 2"
  - name: Francesca Zanderigo
    orcid: 0000-0001-6510-0676
    affiliation: "1, 2"
affiliations:
 - name: Department of Psychiatry, Columbia University Medical Center, New York, NY, United States
   index: 1
 - name: Molecular Imaging and Neuropathology Area, New York State Psychiatric Institute, New York, NY, United States
   index: 2
date: 15 October 2026
bibliography: paper.bib

---

# Summary

PICNIC (Pipeline Initializing Container for Neuro-Imaging Computations) is an
open-source Python-based coding library that facilitates ad hoc/non-standardized
analyses of brain Positron Emission Tomography (PET) data by performing most
standard preprocessing steps for PET data quantification, including brain
extraction, tissue segmentation, automatic anatomical parcellation, and
motion correction. PICNIC uniquely allows full, transparent modular control over the selection of
strategy/software package and associated parameters for each preprocessing step
throughout the pipeline. Therefore, the user is provided with the flexibility to
select different methods depending on the target of interest and/or radiotracer
properties, study population, or other preferences. These settings can be saved
as a text-based “input deck” file to support consistent preprocessing across
scans, participants, and projects. Furthermore, PICNIC supports freezing
software versions within Docker containers, ensuring robust reproducibility.

PICNIC does not require Brain Imaging Data Structure (BIDS) source-level data,
but instead takes reconstructed PET static or dynamic data in industry-standard
imaging file types (e.g., DICOM, NIfTI, ANALYZE), and converts them to be
BIDS-compliant [@Knudsen2020Guidelines]. PICNIC employs the most commonly used
brain imaging software packages, including Advanced Normalization Tools
[@Avants2008Symmetric], Analysis of Functional NeuroImages [@Cox1996AFNI],
FSL [@Jenkinson2012Fsl], FreeSurfer [@Fischl2012FreeSurfer],
dcm2niix [@Li2016DICOM], and SPM [@SPM12].
PICNIC was designed with PET in mind, but includes steps involving data from
multiple imaging modalities, most prominently structural magnetic resonance
imaging (sMRI). PICNIC preprocessing capabilities include image reorientation
(to force all images into a standard orientation regardless of scanner defaults),
brain extraction (to perform skull-stripping of associated sMRI images),
tissue segmentation (to classify sMRI voxels within the brain boundary as grey
matter vs. white matter vs. cerebrospinal fluid),
automatic anatomical parcellation (to identify regions
of interest using any available atlas/parcellation), post-reconstruction
rigid-body motion-correction (to correct inter-frame participant motion over the
duration of the scan), PET-sMRI co-registration (with 20 different PET-sMRI
rigid-body transformations that are automatically ranked based on mutual
information), and extraction of time-activity-curves (curves that represent the
PET signal over the duration of the scan in delineated regions of interest or in
each brain voxel).

PICNIC can be run from the command line or through the provided graphical user
interface. An HTML summary output with interactive quality control features
allows the user to inspect, comment, and approve/disapprove each module for each
participant upon completion. Pre-loaded templates have been provided for
commonly used workflows. The user can add, remove or edit pre-processing steps
to fully customize their pipeline with regards to their dataset. PICNIC
currently supports over 100,000 module/parameter combinations.

PICNIC is designed for in vivo brain investigations by expert PET researchers,
and has already been applied to preprocess data for recent scientific
publications from [our Lab](https://www.columbiapsychiatry.org/research-labs/brain-imaging-lab)
[@Mann2022Neuroinflammation; @Miller2022Relationships; @Bartlett2023Vivo;
@Bartlett2023Relationships; @Bartlett2023Investigation; @Graves2024Gut;
@Bartlett2024TSPO; @Matheson2024Biologically; @Bartlett2024Dual;
@Bartlett2024Quantification; @Herzog2024ER176; @Herzog2025Neuroinflammation;
@Zanderigo2025MicrotubuleTRT; @Zanderigo2025TSPOSIME; @Zanderigo2026MicrotubulesTRT;
@Bartlett2026TSPOMAOA; @Bartlett2026OpenNeuroSTARE; @Laurell2026MCP6827;
@Laurell2026ER176; @Restifo2026Celecoxib; @Bartlett2026NonbrainTSPO]
and is being validated externally alongside other pipelines [@Haver2026Comparison]. PICNIC’s
modular nature enables extensive customization of preprocessing for a variety of
brain PET studies, and its design may allow future extension to preprocessing of
data from imaging modalities other than PET. The source code for PICNIC is
available at the following link: https://github.com/bil-mind-nyspi/PICNIC.

# Statement of need

PET is a valuable tool used in research and clinical settings to noninvasively image the human brain _in vivo_ and can quantify up to nanomolar levels of specific components of brain metabolic and neurochemical processes. Rigorous preprocessing of raw PET data [@Norgaard2019Optimization] is key to obtaining accurate quantification. Although software packages exist that execute each component of brain PET pre-processing, and several of these have even been combined into pipelines, no software exists to support a fully open-source, customizable pre-processing pipeline from start through human quality control (QC).

# State of the field

A variety of software exists for preprocessing brain PET data, but none offer PICNIC's strengths in a single package. PMOD [@Mikolajczyk1998PMOD] requires purchase of a license. Both PMOD and CapAIBL [@Bourgeat2015CapAIBL] are closed-source. MIAKAT [@Gunn2016MIAKAT] and MAGIA [@Karjalainen2020MAGIA] are open-source, but depend on MATLAB, requiring a purchased license. Clinica [@Routier2021Clinica] and Neuropypes [@Savio2017Neuropypes] both depend on SPM, which requires a closed-source MATLAB runtime. NiftyPET [@Markiewicz2017NiftyPET] and PETsurfer [@Greve2014Cortical; @Greve2016PVC] contain useful PET preprocessing tools, but are not complete pipelines. APPIAN [@Funck2018APPIAN] is open-source and based on nipype [@gorgolewski_2016_50186], like PICNIC, but uses BEaST brain extraction and ANIMAL segmentation tools, which would create different regions from the commonly used FreeSurfer individualized regions. Tools from PETsurfer are used in PETPrep [@Norgaard2026petprep] and PETSurfer-bids [@Wighton2026petsurferbids], which uses PETPrep output for additional analyses. PETPrep has been developed concurrently with PICNIC, uses nipype to manage steps, and is a reasonable alternative for standard PET preprocessing objectives. PICNIC offers fully open-source and complete pre-processing pipelines, with SPM available but not required, standard FreeSurfer segmentation, and the added ability to customize or extend the pipeline by altering the input deck. Moreover, PICNIC writes an HTML-based report with interactive image viewers, images, and videos to guide QC.

# Software design

PICNIC was written with Python3 and uses nipype to orchestrate the execution of well-supported external neuroimaging utilities like ANTs [@Avants2008Symmetric], AFNI [@Cox1996AFNI], Connectome Workbench [@Marcus2011HCPCW], FreeSurfer, PETPVC [@Thomas2016PETPVC], and FSL. PICNIC is intended to be run as a [Docker container](https://hub.docker.com/repository/docker/mfschmidt/picnic) to provide all dependencies pre-built in a working environment. However, PICNIC and its dependencies can alternatively be installed and run locally. PICNIC also implements the interactive Papaya neuroimaging viewer [@papaya_viewer] alongside prepared images and video within its HTML reports to guide QC, supporting thorough manual review.

# AI Usage Disclosure

AI was used to find and correct errors in autodoc scripting for creation of documentation. AI was used to verify bibtex citations in this document. AI has not been used to create or maintain PICNIC code or in the writing of this document.

# References
