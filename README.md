# PICNIC

PICNIC is a general purpose neuroimaging preprocessing pipeline.
It is flexible enough to be used for orchestrating many neuroimaging-related
tasks, but it was developed for preprocessing PET and structural MRI.
Please see the provided [example input deck](sample_input_decks/example_ds004513_sub-s012.inp)
for a typical use case for our lab involving a full FreeSurfer recon-all run on
a structural T1-weighted MRI, motion correction on a PET image,
co-registration of the PET image to the structural MRI, and
extraction of time activity curves from FreeSurfer regions.

Because of the dependence of any neuroimaging pipeline on various utilities,
we recommend using the PICNIC docker container, which has the dependencies
pre-installed. However, you are welcome to install the dependencies locally
and run PICNIC that way as well. Issuing the `RUN` commands in the
[Dockerfile](Dockerfile) is a good way to set this up.

## Run PICNIC in docker (easiest)

You need to have docker installed already, then you can download the docker
image and run it on your data. The major benefit of docker is that
Python, FSL, FreeSurfer, AFNI, Connectome Workbench, and PICNIC are
already installed inside the docker container, so you don't have to
deal with those dependencies on your own. You will also need a Freesurfer license, if you don't have one, you can get one for free from [FreeSurfer registration page](https://surfer.nmr.mgh.harvard.edu/registration.html)

You can use a provided wrapper script for the simplest interface.
We have also provided an example input deck
([_sample_input_decks/example_ds004513_sub-s012.inp](_sample_input_decks/example_ds004513_sub-s012.inp))
to process one subject from the downloadable
[The energetic costs of the human connectome](https://doi.org/10.18112/openneuro.ds004513.v1.0.0)
dataset. Edit the paths in the input deck to match it to your system.

```bash
/path/to/picnic/scripts/run_picnic_in_docker \
  /path/to/input_deck.inp \
  /path/to/your/read_only_input_data \
  /path/to/write/picnic_results \
  /path/to/freesurfer/license.txt
```

Or you can bypass the script and use docker directly for more control.

```bash
docker pull mfschmidt/picnic:latest
docker run --rm \
  -v /path/to/your/data:/input:ro \
  -v /path/to/your/results:/output:rw \
  -v /path/to/your/input_deck.inp:/input_deck.inp:ro \
  -v /path/to/your/freesurfer/license.txt:/opt/freesurfer/license.txt:ro \
  mfschmidt/picnic:latest /input_deck.inp
```
Either way, docker sees your data at /input and writes results to /output, so the paths inside your input deck need to point to those locations rather than to the paths on your own system.


## Run PICNIC directly

To run picnic directly, you don't need docker, but you do need to have all of
its dependencies already installed. We don't provide documentation for
dependencies, but you may find the [Dockerfile](Dockerfile) useful as a recipe.

```bash
git clone https://github.com/bil-mind-nyspi/PICNIC.git
cd PICNIC
pip install -U .
./src/picnic/run.py my_input_deck.inp
```

## Results

PICNIC saves the output from every step in the pipeline to the `*Sink`
directory specified in your input deck, along with a `full_report.html`
you can open in a browser to review the run.

## Building input decks

You can write input decks by hand, or build one with Pantry, the graphical input deck builder that is provided with PICNIC (`python src/picnic/pantry.py`).

## Documentation

For more detailed instructions and information about the functions available within
the PICNIC package, see our more complete [documentation](https://bil-mind-nyspi.github.io/PICNIC/).

To report issues, please use the github issues [page](https://github.com/bil-mind-nyspi/PICNIC/issues).
