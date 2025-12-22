.. autodoc:

.. contents::

.. _usage:

Usage
=====

PICNIC allows you to design a pipeline for neuroimaging data
in an input deck, which is a raw text file, and execute that
workflow on your data. After your input deck is ready, there are
two methods for executing your pipeline.

Step 1. (for either method)
---------------------------

Download the PICNIC code.

.. code-block:: bash

   git clone https://github.com/bil-mind-nyspi/PICNIC.git
   cd PICNIC


Step 2. (the docker method, recommended)
----------------------------------------

Pass your input deck to PICNIC's docker container.

.. code-block:: bash

   ./scripts/run_picnic_in_docker \
   /path/to/input_deck.inp \
   /path/to/your/read_only_input_data \
   /path/to/write/picnic_results \
   /path/to/freesurfer/license.txt


The script, `run_picnic_in_docker`, does several things for you.

First, and most importantly, the docker container has all of
PICNIC's dependencies pre-installed. These include FreeSurfer 7.3.2,
AFNI, Connectome Workbench, Convert3d, SPM12 with a Matlab
2024b runtime, ANTs, and Python3. You don't have to install any
of them to your local environment. This is why we strongly recommend
running PICNIC in docker.

Second, it sets up volume mounts so docker can read your input
data from your host system, write your outputs to your host system,
and map the those two paths on your host into the docker container
correctly. To do this, you specify the paths as they exist in your
host environment. But in your input deck, you need to specify the
paths as they exist inside the docker container. If you need to
read input data from `/home/username/pet_data/rawdata/sub-01/` and
write it to `/home/username/pet_data/derivatives/picnic_0.1.4/sub-01/`, and
execute the commands in input deck `/home/username/sub-01_processing.inp`,
you could use the following command:

.. code-block:: bash

   ./scripts/run_picnic_in_docker \
   /home/username/sub-01_processing.inp \
   /home/username/pet_data/rawdata \
   /home/username/pet_data/derivatives/picnic_0.1.4 \
   /usr/local/freesurfer/license.txt

In this case, your input deck should refer to `/input/sub-01` and
`/output/sub-01`, because the paths above would be mounted into the
docker container as `/input` and `/output`.

By default, docker runs as root, and writes files as root.
If you have specific needs to run docker as yourself, you can use
the alternative script, `./scripts/run_picnic_remapped_in_docker_as_user`.


Step 2. (the direct method)
---------------------------

To run PICNIC directly, you need to run it on a machine with all
of PICNIC's dependencies already installed. If you intend to run
FreeSurfer's recon-all on your data, but you don't have FreeSurfer
installed, PICNIC will fail. If you don't have all of PICNIC's python
libraries installed (see requirements.txt), PICNIC will fail.

.. code-block:: bash

   python3 src/picnic/run.py /path/to/input_deck.inp


One benefit of running directly is that your paths in the input deck
remain the same, making it more straight-forward to figure out any
problems that may arise.

Finding Results
---------------

PICNIC will have saved the output from every step in the pipeline
to the "Sink" specified in the input deck. A final html report
will also be available to review the pipeline and do quality
assessments.
