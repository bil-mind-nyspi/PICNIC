# PICNIC Docker Container
# This staged build borrowed heavily from fMRIPrep's Dockerfile
# at https://github.com/nipreps/fmriprep/blob/master/Dockerfile.base

# Ubuntu 24.04 LTS - Noble Numbat - Default python in this release is 3.12
ARG BASE_IMAGE=ubuntu:noble-20260930.1

#
# Build PICNIC wheel
#
FROM ${BASE_IMAGE} AS src
COPY . /src
RUN apt-get update && \
    apt-get install -y --no-install-recommends git python3 python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    /usr/bin/python3 -m venv /opt/build && \
    /opt/build/bin/pip install --no-cache-dir build && \
    /opt/build/bin/python3 -m build --wheel /src

#
# Download stages
#

# Utilities for downloading packages
FROM ${BASE_IMAGE} AS downloader
# Bump the date to current to refresh curl/certificates/etc
RUN echo "2026.10.18"
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    binutils \
                    bzip2 \
                    ca-certificates \
                    curl \
                    unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# FreeSurfer 7.4.1
FROM downloader AS freesurfer
RUN echo "2026.10.18"
COPY docker/files/freesurfer_7.3.2_exclude.txt /usr/local/etc/freesurfer_7.3.2_exclude.txt
RUN curl -sSL https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz \
     | tar zxv --no-same-owner -C /opt --exclude-from=/usr/local/etc/freesurfer_7.3.2_exclude.txt

# AFNI
FROM downloader AS afni
# Bump the date to current to update AFNI
RUN echo "2026.10.18"
RUN mkdir -p /opt/afni-latest \
    && curl -fsSL --retry 5 https://afni.nimh.nih.gov/pub/dist/tgz/linux_openmp_64.tgz \
    | tar -xz -C /opt/afni-latest --strip-components 1 \
    --exclude "linux_openmp_64/*.gz" \
    --exclude "linux_openmp_64/funstuff" \
    --exclude "linux_openmp_64/shiny" \
    --exclude "linux_openmp_64/afnipy" \
    --exclude "linux_openmp_64/lib/RetroTS" \
    --exclude "linux_openmp_64/lib_RetroTS" \
    --exclude "linux_openmp_64/meica.libs" \
    && find /opt/afni-latest -type f -not \( \
        -name "3dTshift" -or \
        -name "3dUnifize" -or \
        -name "3dAutomask" -or \
        -name "3dvolreg" \) -delete

# Connectome Workbench 2.2.1
FROM downloader AS workbench
RUN echo "2026.10.18"
RUN mkdir /opt/workbench && \
    curl -sSLO https://www.humanconnectome.org/storage/app/media/workbench/workbench-linux64-v2.2.1.zip && \
    unzip workbench-linux64-v2.2.1.zip -d /opt && \
    rm workbench-linux64-v2.2.1.zip

# Convert3d 1.4.0
FROM downloader AS c3d
RUN echo "2026.10.18"
RUN mkdir /opt/convert3d && \
    curl -fsSL --retry 5 https://sourceforge.net/projects/c3d/files/c3d/Experimental/c3d-1.4.4-Linux-gcc64.tar.gz/download \
    | tar -xz -C /opt/convert3d --strip-components 1

# Matlab MCR and SPM
FROM downloader AS spm
RUN echo "2026.10.18"
# Architecture of spm docker container based on github spm/spm-docker
# These args are repeated in the final image, so make changes in both places.
ARG MATLAB_VERSION=R2024b
ARG AGREE_TO_MATLAB_RUNTIME_LICENSE=yes
ARG SPM_VERSION=25
ARG SPM_RELEASE=${SPM_VERSION}.01
ARG SPM_REVISION=02
ENV SPM_TAG=${SPM_RELEASE}${SPM_REVISION:+.${SPM_REVISION}}

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    unzip xorg wget \
    && apt-get clean \
    && rm -rf \
    /tmp/hsperfdata* \
    /var/*/apt/*/partial \
    /var/lib/apt/lists/* \
    /var/log/apt/term*

ENV LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/sys/opengl/lib/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/extern/bin/glnxa64
ENV MCR_INHIBIT_CTF_LOCK=1
ENV SPM_HTML_BROWSER=0

RUN wget --no-check-certificate --progress=bar:force -P /opt https://github.com/spm/spm/releases/download/${SPM_TAG}/spm_standalone_${SPM_TAG}_Linux.zip \
    && unzip -q /opt/spm_standalone_${SPM_TAG}_Linux.zip -d /opt \
    && rm -f /opt/spm_standalone_${SPM_TAG}_Linux.zip \
    && mv /opt/spm_standalone /opt/spm \
    && /opt/runtime_installer/Runtime_${MATLAB_VERSION}_for_spm_standalone_${SPM_TAG}.install -agreeToLicense ${AGREE_TO_MATLAB_RUNTIME_LICENSE} \
    && chmod +w /opt/spm \
    && /opt/spm/spm${SPM_VERSION} function exit \
    && chmod +x /opt/spm/spm${SPM_VERSION}

FROM downloader AS ants
RUN echo "2026.10.18"
ARG CC=gcc-11
ARG CXX=g++-11
ARG BUILD_SHARED_LIBS=ON

RUN \
    --mount=type=cache,sharing=private,target=/var/cache/apt \
    apt-get update && apt-get install -y ${CXX} cmake make ninja-build git bc

WORKDIR /usr/local/src
RUN git config --global url.'https://'.insteadOf 'git://' \
    && git clone https://github.com/ANTsX/ANTs.git

WORKDIR /build
RUN cmake \
    -GNinja \
    -DBUILD_TESTING=ON \
    -DRUN_LONG_TESTS=OFF \
    -DRUN_SHORT_TESTS=ON \
    -DBUILD_SHARED_LIBS=${BUILD_SHARED_LIBS} \
    -DCMAKE_INSTALL_PREFIX=/opt/ants \
    /usr/local/src/ANTs
RUN cmake --build . --parallel
WORKDIR /build/ANTS-build
RUN cmake --install .

ENV PATH="/opt/ants/bin:$PATH" \
    LD_LIBRARY_PATH=/opt/ants/lib

RUN cmake --build . --target test

# Micromamba
FROM downloader AS micromamba
RUN echo "2026.10.18"
# Install a C compiler to build extensions when needed.
# traits<6.4 wheels are not available for Python 3.11+, but build easily.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /
# Bump the date to current to force update micromamba
RUN echo "2026.10.18"
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

ENV MAMBA_ROOT_PREFIX="/opt/conda"
COPY env.yml /tmp/env.yml
COPY requirements.txt /tmp/requirements.txt
WORKDIR /tmp
RUN micromamba create -y -f /tmp/env.yml && \
    micromamba clean -y -a

# =============================================================================
# Main stage
#
FROM ${BASE_IMAGE} AS picnic

# Configure apt
ENV DEBIAN_FRONTEND="noninteractive" \
    LANGUAGE="en_US.UTF-8" \
    LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# Some baseline tools, needed before even setting up PPAs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bc \
        ca-certificates \
        curl \
        git \
        gnupg \
        lsb-release \
        netbase \
        xvfb

# Configure PPAs for libpng12 and libxp6
RUN GNUPGHOME=/tmp gpg --keyserver hkps://keyserver.ubuntu.com --no-default-keyring --keyring /usr/share/keyrings/linuxuprising.gpg --recv 0xEA8CACC073C3DB2A \
    && GNUPGHOME=/tmp gpg --keyserver hkps://keyserver.ubuntu.com --no-default-keyring --keyring /usr/share/keyrings/zeehio.gpg --recv 0xA1301338A3A48C4A \
    && echo "deb [signed-by=/usr/share/keyrings/linuxuprising.gpg] https://ppa.launchpadcontent.net/linuxuprising/libpng12/ubuntu jammy main" > /etc/apt/sources.list.d/linuxuprising.list \
    && echo "deb [signed-by=/usr/share/keyrings/zeehio.gpg] https://ppa.launchpadcontent.net/zeehio/libxp/ubuntu jammy main" > /etc/apt/sources.list.d/zeehio.list

# Dependencies
# AFNI requires a discontinued multiarch-support package from bionic (18.04)
# FreeSurfer and ANTs both need bc
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
        ed \
        gsl-bin \
        libglib2.0-0 \
        libglu1-mesa-dev \
        libglw1-mesa \
        libgomp1 \
        libjpeg62 \
        libpng12-0 \
        libxm4 \
        libxp6 \
        locales \
        netpbm \
        tcsh \
        xfonts-base \
        xvfb \
        ffmpeg \
    && curl -sSL --retry 5 -o /tmp/multiarch.deb http://archive.ubuntu.com/ubuntu/pool/main/g/glibc/multiarch-support_2.27-3ubuntu1.5_amd64.deb \
    && dpkg -i /tmp/multiarch.deb \
    && rm /tmp/multiarch.deb \
    && apt-get install -f \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && gsl2_path="$(find / -name 'libgsl.so.19' || printf '')" \
    && if [ -n "$gsl2_path" ]; then \
         ln -sfv "$gsl2_path" "$(dirname $gsl2_path)/libgsl.so.0"; \
       fi \
    && locale-gen "$LC_ALL" \
    && ldconfig

# Install files from stages
COPY --from=freesurfer /opt/freesurfer /opt/freesurfer
COPY --from=afni /opt/afni-latest /opt/afni-latest
COPY --from=workbench /opt/workbench /opt/workbench
COPY --from=c3d /opt/convert3d/bin/c3d_affine_tool /usr/bin/c3d_affine_tool
COPY --from=spm /opt/spm /opt/spm
COPY --from=spm /usr/local/MATLAB /usr/local/MATLAB
COPY --from=ants /opt/ants /opt/ants
COPY --from=micromamba /bin/micromamba /bin/micromamba
COPY --from=micromamba /opt/conda/envs/picnic /opt/conda/envs/picnic

# Simulate SetUpFreeSurfer.sh & FSL & AFNI & Workbench & SPM & ANTs configs
ARG FREESURFER_HOME="/opt/freesurfer"
ARG MATLAB_VERSION=R2024b
ARG SPM_VERSION=25
ENV OS="Linux" \
    IS_DOCKER_PICNIC=1 \
    FS_OVERRIDE=0 \
    FIX_VERTEX_AREA="" \
    FSF_OUTPUT_FORMAT="nii.gz" \
    FREESURFER_HOME="${FREESURFER_HOME}" \
    SUBJECTS_DIR="${FREESURFER_HOME}/subjects" \
    FUNCTIONALS_DIR="${FREESURFER_HOME}/sessions" \
    MNI_DIR="${FREESURFER_HOME}/mni" \
    LOCAL_DIR="${FREESURFER_HOME}/local" \
    MINC_BIN_DIR="${FREESURFER_HOME}/mni/bin" \
    MINC_LIB_DIR="${FREESURFER_HOME}/mni/lib" \
    MNI_DATAPATH="${FREESURFER_HOME}/mni/data" \
    PERL5LIB="${FREESURFER_HOME}/mni/lib/perl5/5.8.5" \
    MNI_PERL5LIB="${FREESURFER_HOME}/mni/lib/perl5/5.8.5" \
    PYTHONNOUSERSITE=1 \
    FSLDIR="/opt/conda/envs/picnic" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q" \
    AFNI_IMSAVE_WARNINGS="NO" \
    AFNI_PLUGINPATH="/opt/afni-latest" \
    MCRSPMCMD="/usr/local/bin/spm" \
    FORCE_SPMMCR="TRUE" \
    MCR_INHIBIT_CTF_LOCK=1 \
    SPM_HTML_BROWSER=0 \
    CPATH="/opt/conda/envs/picnic/include" \
    MAMBA_ROOT_PREFIX="/opt/conda" \
    MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/sys/opengl/lib/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/${MATLAB_VERSION}/extern/bin/glnxa64:/opt/workbench/lib_linux64" \
    PATH="/opt/conda/envs/picnic/bin:/opt/afni-latest:${FREESURFER_HOME}/bin:${FREESURFER_HOME}/tktools:${FREESURFER_HOME}/mni/bin:/opt/workbench/bin_linux64:${PATH}" \
    HOME="/home/picnic"

# SPM config
RUN chmod a+w /opt/spm && \
    ln -s /opt/spm/spm${SPM_VERSION} ${MCRSPMCMD}

# Create a shared $HOME directory
RUN useradd -m -s /bin/bash -G users picnic
WORKDIR /home/picnic
RUN micromamba shell init -s bash && \
    echo "micromamba activate picnic" >> $HOME/.bashrc

# Precaching atlases
COPY scripts/fetch_templates.py fetch_templates.py
RUN python fetch_templates.py && \
    rm fetch_templates.py && \
    find $HOME/.cache/templateflow -type d -exec chmod go=u {} + && \
    find $HOME/.cache/templateflow -type f -exec chmod go=u {} +

# MSM HOCR (Nov 19, 2019 release)
RUN curl -L -H "Accept: application/octet-stream" https://api.github.com/repos/ecr05/MSM_HOCR/releases/assets/16253707 -o /usr/local/bin/msm \
    && chmod +x /usr/local/bin/msm

# Installing PICNIC
COPY --from=src /src/dist/*.whl .
RUN pip install --no-cache-dir $( ls *.whl ) \
    && find $HOME -type d -exec chmod go=u {} \; \
    && find $HOME -type f -exec chmod go=u {} \; \
    && rm -rf $HOME/.npm $HOME/.conda $HOME/.empty \
    && ldconfig

WORKDIR /tmp
ENTRYPOINT ["/opt/conda/envs/picnic/bin/python3", "/opt/conda/envs/picnic/bin/run.py"]

ARG BUILD_DATE=2026-10-18
ARG PICNIC_VERSION=0.2.0
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="PICNIC" \
      org.label-schema.description="PICNIC - A modular PET preprocessing tool" \
      org.label-schema.url="https://github.com/bil-mind-nyspi/PICNIC" \
      org.label-schema.vcs-ref=v$PICNIC_VERSION \
      org.label-schema.vcs-url="https://github.com/bil-mind-nyspi/PICNIC" \
      org.label-schema.version=$PICNIC_VERSION \
      org.label-schema.schema-version="1.0"
