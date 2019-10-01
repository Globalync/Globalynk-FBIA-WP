# (c) 2012-2016 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.
'''
We use the following conventions in this module:

    dist:        canonical package name, e.g. 'numpy-1.6.2-py26_0'

    ROOT_PREFIX: the prefix to the root environment, e.g. /opt/anaconda

    PKGS_DIR:    the "package cache directory", e.g. '/opt/anaconda/pkgs'
                 this is always equal to ROOT_PREFIX/pkgs

    prefix:      the prefix of a particular environment, which may also
                 be the root environment

Also, this module is directly invoked by the (self extracting) tarball
installer to create the initial environment, therefore it needs to be
standalone, i.e. not import any other parts of `conda` (only depend on
the standard library).
'''
import os
import re
import sys
import json
import shutil
import stat
from os.path import abspath, dirname, exists, isdir, isfile, islink, join
from optparse import OptionParser


on_win = bool(sys.platform == 'win32')
try:
    FORCE = bool(int(os.getenv('FORCE', 0)))
except ValueError:
    FORCE = False

LINK_HARD = 1
LINK_SOFT = 2  # never used during the install process
LINK_COPY = 3
link_name_map = {
    LINK_HARD: 'hard-link',
    LINK_SOFT: 'soft-link',
    LINK_COPY: 'copy',
}
SPECIAL_ASCII = '$!&\%^|{}[]<>~`"\':;?@*#'

# these may be changed in main()
ROOT_PREFIX = sys.prefix
PKGS_DIR = join(ROOT_PREFIX, 'pkgs')
SKIP_SCRIPTS = False
IDISTS = {
  "_license-1.1-py36_1": {
    "md5": "4022c5b4a1ac109885b4ed56ef0b3c6a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/_license-1.1-py36_1.tar.bz2"
  }, 
  "alabaster-0.7.10-py36_0": {
    "md5": "aa56a094f5de76f4a4b4053dc2975474", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/alabaster-0.7.10-py36_0.tar.bz2"
  }, 
  "anaconda-4.4.0-np112py36_0": {
    "md5": "81f9c560228ab493f466b0a6696531b1", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/anaconda-4.4.0-np112py36_0.tar.bz2"
  }, 
  "anaconda-client-1.6.3-py36_0": {
    "md5": "1bddf4b02f73bcd1eb9d9a52a4df2e79", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/anaconda-client-1.6.3-py36_0.tar.bz2"
  }, 
  "anaconda-navigator-1.6.2-py36_0": {
    "md5": "87420ca2ed46becdd8f7d63e90cbb7bb", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/anaconda-navigator-1.6.2-py36_0.tar.bz2"
  }, 
  "anaconda-project-0.6.0-py36_0": {
    "md5": "47d9be589c200d5c435487bc12963845", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/anaconda-project-0.6.0-py36_0.tar.bz2"
  }, 
  "asn1crypto-0.22.0-py36_0": {
    "md5": "751c43ece1bc72797d7e8e0d2cb7fdab", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/asn1crypto-0.22.0-py36_0.tar.bz2"
  }, 
  "astroid-1.4.9-py36_0": {
    "md5": "ef2a3b89bd5281e4c52ed804471fa5e5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/astroid-1.4.9-py36_0.tar.bz2"
  }, 
  "astropy-1.3.2-np112py36_0": {
    "md5": "ff4cc2122b9d78530d1d3a001fb552de", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/astropy-1.3.2-np112py36_0.tar.bz2"
  }, 
  "babel-2.4.0-py36_0": {
    "md5": "c1704afa6aac688a6c13ba9095c93831", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/babel-2.4.0-py36_0.tar.bz2"
  }, 
  "backports-1.0-py36_0": {
    "md5": "b5b3ac5b173e8681100fca1a058cce16", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/backports-1.0-py36_0.tar.bz2"
  }, 
  "beautifulsoup4-4.6.0-py36_0": {
    "md5": "cc48daf8a1a64fc242d74b7364ab23a7", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/beautifulsoup4-4.6.0-py36_0.tar.bz2"
  }, 
  "bitarray-0.8.1-py36_1": {
    "md5": "5acfeff346836766c2839e3ae96b550d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/bitarray-0.8.1-py36_1.tar.bz2"
  }, 
  "blaze-0.10.1-py36_0": {
    "md5": "5e53298951be7e626fe77767ff53ab87", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/blaze-0.10.1-py36_0.tar.bz2"
  }, 
  "bleach-1.5.0-py36_0": {
    "md5": "85973100bee40e2a38f091519231b747", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/bleach-1.5.0-py36_0.tar.bz2"
  }, 
  "bokeh-0.12.5-py36_1": {
    "md5": "722bf62eb3998dbd981971d9d8f11520", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/bokeh-0.12.5-py36_1.tar.bz2"
  }, 
  "boto-2.46.1-py36_0": {
    "md5": "4551237e6c7b09f2a55568b34b4e466d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/boto-2.46.1-py36_0.tar.bz2"
  }, 
  "bottleneck-1.2.1-np112py36_0": {
    "md5": "13497734a81bf3a405a9c03321629788", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/bottleneck-1.2.1-np112py36_0.tar.bz2"
  }, 
  "bzip2-1.0.6-vc14_3": {
    "md5": "954849ad2fc1317ab794ce6774745c8b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/bzip2-1.0.6-vc14_3.tar.bz2"
  }, 
  "cffi-1.10.0-py36_0": {
    "md5": "96468f7824dee1b3f10a2037d1df79b9", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cffi-1.10.0-py36_0.tar.bz2"
  }, 
  "chardet-3.0.3-py36_0": {
    "md5": "c9f18d4d4c4f0c3439625c39002f2acd", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/chardet-3.0.3-py36_0.tar.bz2"
  }, 
  "click-6.7-py36_0": {
    "md5": "98d4b1842f3e738a734adf265eb062a6", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/click-6.7-py36_0.tar.bz2"
  }, 
  "cloudpickle-0.2.2-py36_0": {
    "md5": "4e34b2f335de59036046dc84cc23043a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cloudpickle-0.2.2-py36_0.tar.bz2"
  }, 
  "clyent-1.2.2-py36_0": {
    "md5": "798e47c2cbb5eaca89f4e5637d9dd75c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/clyent-1.2.2-py36_0.tar.bz2"
  }, 
  "colorama-0.3.9-py36_0": {
    "md5": "a56b065f28c919b6eef94ae7e5a650bc", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/colorama-0.3.9-py36_0.tar.bz2"
  }, 
  "comtypes-1.1.2-py36_0": {
    "md5": "e88de37d6f7e902dca025d7a2938430a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/comtypes-1.1.2-py36_0.tar.bz2"
  }, 
  "conda-4.3.21-py36_0": {
    "md5": "4624e7bd84d4afc09efd5b62763eb7a8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/conda-4.3.21-py36_0.tar.bz2"
  }, 
  "conda-env-2.6.0-0": {
    "md5": "11cd1221fd2b3d7b84d51175b92ccf15", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/conda-env-2.6.0-0.tar.bz2"
  }, 
  "console_shortcut-0.1.1-py36_1": {
    "md5": "0aff2f4780f34c539136d0a724af58f7", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/console_shortcut-0.1.1-py36_1.tar.bz2"
  }, 
  "contextlib2-0.5.5-py36_0": {
    "md5": "8b1b77a09e1e213a98e9b6161766b32d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/contextlib2-0.5.5-py36_0.tar.bz2"
  }, 
  "cryptography-1.8.1-py36_0": {
    "md5": "139150fc7885a4ae5a0e4888fc852f94", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cryptography-1.8.1-py36_0.tar.bz2"
  }, 
  "curl-7.52.1-vc14_0": {
    "md5": "85dcfa9cab0b42d6fa932e9cac92c707", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/curl-7.52.1-vc14_0.tar.bz2"
  }, 
  "cycler-0.10.0-py36_0": {
    "md5": "b0296d3eab628127158e34490bf9e343", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cycler-0.10.0-py36_0.tar.bz2"
  }, 
  "cython-0.25.2-py36_0": {
    "md5": "5fbd891d1290385de96b31ac04fa49cf", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cython-0.25.2-py36_0.tar.bz2"
  }, 
  "cytoolz-0.8.2-py36_0": {
    "md5": "0591faf6c4d9056a5da8b2cfc80722e1", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/cytoolz-0.8.2-py36_0.tar.bz2"
  }, 
  "dask-0.14.3-py36_1": {
    "md5": "62db4d41a0958ca8ffeaa5ef32632697", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/dask-0.14.3-py36_1.tar.bz2"
  }, 
  "datashape-0.5.4-py36_0": {
    "md5": "228e513302322f056532f2676da24c4c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/datashape-0.5.4-py36_0.tar.bz2"
  }, 
  "decorator-4.0.11-py36_0": {
    "md5": "c2a83b6b329d62fd35776a7a22a3d2ef", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/decorator-4.0.11-py36_0.tar.bz2"
  }, 
  "distributed-1.16.3-py36_0": {
    "md5": "47b864cb186c2b67aaf8295e13a1fdd3", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/distributed-1.16.3-py36_0.tar.bz2"
  }, 
  "docutils-0.13.1-py36_0": {
    "md5": "0dba4adef0ca9ec3109909f66568ddb0", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/docutils-0.13.1-py36_0.tar.bz2"
  }, 
  "entrypoints-0.2.2-py36_1": {
    "md5": "498202590497916437354523652f1d17", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/entrypoints-0.2.2-py36_1.tar.bz2"
  }, 
  "et_xmlfile-1.0.1-py36_0": {
    "md5": "d0217cd8bb8eb078aa784cdc1461e669", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/et_xmlfile-1.0.1-py36_0.tar.bz2"
  }, 
  "fastcache-1.0.2-py36_1": {
    "md5": "0979661118a6a61b1d9c45c376db55f8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/fastcache-1.0.2-py36_1.tar.bz2"
  }, 
  "flask-0.12.2-py36_0": {
    "md5": "c66c4d8f2faeffdb3fd10af3426804d8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/flask-0.12.2-py36_0.tar.bz2"
  }, 
  "flask-cors-3.0.2-py36_0": {
    "md5": "3ff513259e1ad40d7f82b02a1468442e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/flask-cors-3.0.2-py36_0.tar.bz2"
  }, 
  "freetype-2.5.5-vc14_2": {
    "md5": "00d22e2546fa5ed62739331419eb8606", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/freetype-2.5.5-vc14_2.tar.bz2"
  }, 
  "get_terminal_size-1.0.0-py36_0": {
    "md5": "b876b5a8ac3c51f9ff308cb14bbd9d2c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/get_terminal_size-1.0.0-py36_0.tar.bz2"
  }, 
  "gevent-1.2.1-py36_0": {
    "md5": "996dbac238a08b794e7dbcbe9bc59d25", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/gevent-1.2.1-py36_0.tar.bz2"
  }, 
  "greenlet-0.4.12-py36_0": {
    "md5": "911d2d8d6c710b8c965fb73122c6f641", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/greenlet-0.4.12-py36_0.tar.bz2"
  }, 
  "h5py-2.7.0-np112py36_0": {
    "md5": "47e7c365b4e987bbbaa233e173f5aa53", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/h5py-2.7.0-np112py36_0.tar.bz2"
  }, 
  "hdf5-1.8.15.1-vc14_4": {
    "md5": "7fb4055ab0af78754044f18b1cee8f04", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/hdf5-1.8.15.1-vc14_4.tar.bz2"
  }, 
  "heapdict-1.0.0-py36_1": {
    "md5": "470d20d272739df34eb004fee8c8860f", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/heapdict-1.0.0-py36_1.tar.bz2"
  }, 
  "html5lib-0.999-py36_0": {
    "md5": "bee05d0bedb6b2fcbdd3f7c18c0e109b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/html5lib-0.999-py36_0.tar.bz2"
  }, 
  "icu-57.1-vc14_0": {
    "md5": "0d00881b544aa5822eb91f1ecac17e3d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/icu-57.1-vc14_0.tar.bz2"
  }, 
  "idna-2.5-py36_0": {
    "md5": "c85c3d3f77aaa241c52e1004ce719396", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/idna-2.5-py36_0.tar.bz2"
  }, 
  "imagesize-0.7.1-py36_0": {
    "md5": "121c6a275264238a7f3eb8c78be97aba", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/imagesize-0.7.1-py36_0.tar.bz2"
  }, 
  "ipykernel-4.6.1-py36_0": {
    "md5": "4e58d1e9dcf5d1ec5dc2c5f7b243fa01", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ipykernel-4.6.1-py36_0.tar.bz2"
  }, 
  "ipython-5.3.0-py36_0": {
    "md5": "929bfd78ad4d2ec86de4086519c55ee5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ipython-5.3.0-py36_0.tar.bz2"
  }, 
  "ipython_genutils-0.2.0-py36_0": {
    "md5": "57f96aef81b489e012503a6ae9196ac9", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ipython_genutils-0.2.0-py36_0.tar.bz2"
  }, 
  "ipywidgets-6.0.0-py36_0": {
    "md5": "4b354c2e072d05908ad058a6a4c2b592", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ipywidgets-6.0.0-py36_0.tar.bz2"
  }, 
  "isort-4.2.5-py36_0": {
    "md5": "b1f9a00a60da800e05b54aaa7668ad57", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/isort-4.2.5-py36_0.tar.bz2"
  }, 
  "itsdangerous-0.24-py36_0": {
    "md5": "8ac9095b7975888c45d4a3b18b3e1bbd", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/itsdangerous-0.24-py36_0.tar.bz2"
  }, 
  "jdcal-1.3-py36_0": {
    "md5": "579304a38f82c0be6181335aaeba5e8c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jdcal-1.3-py36_0.tar.bz2"
  }, 
  "jedi-0.10.2-py36_2": {
    "md5": "0c1b99701c8963dd9b0a19d8e4ec7d59", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jedi-0.10.2-py36_2.tar.bz2"
  }, 
  "jinja2-2.9.6-py36_0": {
    "md5": "521ccb7141fcdc6e2b0ad7f6674011f7", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jinja2-2.9.6-py36_0.tar.bz2"
  }, 
  "jpeg-9b-vc14_0": {
    "md5": "f789916eb70543d9fcd0593a9ba29d1b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jpeg-9b-vc14_0.tar.bz2"
  }, 
  "jsonschema-2.6.0-py36_0": {
    "md5": "21668ff83b6e2028513b4c0abc35d600", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jsonschema-2.6.0-py36_0.tar.bz2"
  }, 
  "jupyter-1.0.0-py36_3": {
    "md5": "3f825d3fd59f7e937a6b035e106faf52", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jupyter-1.0.0-py36_3.tar.bz2"
  }, 
  "jupyter_client-5.0.1-py36_0": {
    "md5": "4c8b8c049cbdc2575100b288dc31461a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jupyter_client-5.0.1-py36_0.tar.bz2"
  }, 
  "jupyter_console-5.1.0-py36_0": {
    "md5": "7454138f19a2e579def6d83faac91cc5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jupyter_console-5.1.0-py36_0.tar.bz2"
  }, 
  "jupyter_core-4.3.0-py36_0": {
    "md5": "bd7495756ca2dc1d2c69415357a34697", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/jupyter_core-4.3.0-py36_0.tar.bz2"
  }, 
  "lazy-object-proxy-1.2.2-py36_0": {
    "md5": "050b7b300370ce7e48e070cbedcd31f4", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/lazy-object-proxy-1.2.2-py36_0.tar.bz2"
  }, 
  "libpng-1.6.27-vc14_0": {
    "md5": "9a7800b906e5e672e030634d4e5507b6", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/libpng-1.6.27-vc14_0.tar.bz2"
  }, 
  "libtiff-4.0.6-vc14_3": {
    "md5": "ce733733698e7244227dcd6e530a1615", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/libtiff-4.0.6-vc14_3.tar.bz2"
  }, 
  "llvmlite-0.18.0-py36_0": {
    "md5": "58afed0ae28023075479122339c11a9a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/llvmlite-0.18.0-py36_0.tar.bz2"
  }, 
  "locket-0.2.0-py36_1": {
    "md5": "7ded24606cecdf7f2a13ffa11213367c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/locket-0.2.0-py36_1.tar.bz2"
  }, 
  "lxml-3.7.3-py36_0": {
    "md5": "409e602a5accf2fb03c53aac6676a4c0", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/lxml-3.7.3-py36_0.tar.bz2"
  }, 
  "markupsafe-0.23-py36_2": {
    "md5": "6f797f317dae6b7fa4b0a00e957e6945", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/markupsafe-0.23-py36_2.tar.bz2"
  }, 
  "matplotlib-2.0.2-np112py36_0": {
    "md5": "e2425f38d3427eb76d831478069aeb6f", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/matplotlib-2.0.2-np112py36_0.tar.bz2"
  }, 
  "menuinst-1.4.7-py36_0": {
    "md5": "a48452d4091a45310214d6006e6e7cc0", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/menuinst-1.4.7-py36_0.tar.bz2"
  }, 
  "mistune-0.7.4-py36_0": {
    "md5": "73c00d97b7d98e8f7894365973f2e960", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/mistune-0.7.4-py36_0.tar.bz2"
  }, 
  "mkl-2017.0.1-0": {
    "md5": "024de81bcf413684908a50989a7c246d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/mkl-2017.0.1-0.tar.bz2"
  }, 
  "mkl-service-1.1.2-py36_3": {
    "md5": "6a10850911a2f1ddac36ba1a5dbf2311", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/mkl-service-1.1.2-py36_3.tar.bz2"
  }, 
  "mpmath-0.19-py36_1": {
    "md5": "17867eedc51e6451a0ff9630857dca39", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/mpmath-0.19-py36_1.tar.bz2"
  }, 
  "msgpack-python-0.4.8-py36_0": {
    "md5": "7986ec954d8582ed2c1e965fdaa461ee", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/msgpack-python-0.4.8-py36_0.tar.bz2"
  }, 
  "multipledispatch-0.4.9-py36_0": {
    "md5": "fbac482e27e35800ec614fe8a814e26a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/multipledispatch-0.4.9-py36_0.tar.bz2"
  }, 
  "navigator-updater-0.1.0-py36_0": {
    "md5": "07b4e7b5eb7be936514ab9f33f730643", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/navigator-updater-0.1.0-py36_0.tar.bz2"
  }, 
  "nbconvert-5.1.1-py36_0": {
    "md5": "61021f6c1a6c197573e5d8f866961ff8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/nbconvert-5.1.1-py36_0.tar.bz2"
  }, 
  "nbformat-4.3.0-py36_0": {
    "md5": "238154a0a23ab18a7db593060bd59b56", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/nbformat-4.3.0-py36_0.tar.bz2"
  }, 
  "networkx-1.11-py36_0": {
    "md5": "03a600be6028393af0f2e85888f4b82c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/networkx-1.11-py36_0.tar.bz2"
  }, 
  "nltk-3.2.3-py36_0": {
    "md5": "c54d04afe941a8798b9ecf917cf63eae", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/nltk-3.2.3-py36_0.tar.bz2"
  }, 
  "nose-1.3.7-py36_1": {
    "md5": "01bcc941b67c388f00913e0e3310377d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/nose-1.3.7-py36_1.tar.bz2"
  }, 
  "notebook-5.0.0-py36_0": {
    "md5": "9cf872b9a6f54580e7c75e0d77de015e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/notebook-5.0.0-py36_0.tar.bz2"
  }, 
  "numba-0.33.0-np112py36_0": {
    "md5": "ee6e14f9e741ea6c5b4aa51cc3866c4d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/numba-0.33.0-np112py36_0.tar.bz2"
  }, 
  "numexpr-2.6.2-np112py36_0": {
    "md5": "029e127643e67db138e5a5b06c74ae72", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/numexpr-2.6.2-np112py36_0.tar.bz2"
  }, 
  "numpy-1.12.1-py36_0": {
    "md5": "205e92ff2e1646a40e7a795c2ae2c2bc", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/numpy-1.12.1-py36_0.tar.bz2"
  }, 
  "numpydoc-0.6.0-py36_0": {
    "md5": "f07d08d1a0b9ef794bca45f65405943b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/numpydoc-0.6.0-py36_0.tar.bz2"
  }, 
  "odo-0.5.0-py36_1": {
    "md5": "183ca9a19781cdd23270c50cf8a09fff", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/odo-0.5.0-py36_1.tar.bz2"
  }, 
  "olefile-0.44-py36_0": {
    "md5": "25ffbf94c8369e46b638da8238f29ed6", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/olefile-0.44-py36_0.tar.bz2"
  }, 
  "openpyxl-2.4.7-py36_0": {
    "md5": "add698c3d78e511b57a76273082fe4c1", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/openpyxl-2.4.7-py36_0.tar.bz2"
  }, 
  "openssl-1.0.2l-vc14_0": {
    "md5": "9c05fe14daba876b699f5251b2eb3524", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/openssl-1.0.2l-vc14_0.tar.bz2"
  }, 
  "packaging-16.8-py36_0": {
    "md5": "9e5cfd27f5b9095f7115a033a8d670ee", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/packaging-16.8-py36_0.tar.bz2"
  }, 
  "pandas-0.20.1-np112py36_0": {
    "md5": "f4d2a4e6d59cd5b3089b8eba7932e1bf", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pandas-0.20.1-np112py36_0.tar.bz2"
  }, 
  "pandocfilters-1.4.1-py36_0": {
    "md5": "774c1877e265aeb167f3e370c251c55a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pandocfilters-1.4.1-py36_0.tar.bz2"
  }, 
  "partd-0.3.8-py36_0": {
    "md5": "c3bcd4509c98dc4e289c0f1acca03111", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/partd-0.3.8-py36_0.tar.bz2"
  }, 
  "path.py-10.3.1-py36_0": {
    "md5": "2c2abde6d9e074620a15f3ee1b548d2d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/path.py-10.3.1-py36_0.tar.bz2"
  }, 
  "pathlib2-2.2.1-py36_0": {
    "md5": "d56cf28ac96fa96f54d9a0653eb5d400", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pathlib2-2.2.1-py36_0.tar.bz2"
  }, 
  "patsy-0.4.1-py36_0": {
    "md5": "38ae34c94ea0773ed2e0046d59264d80", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/patsy-0.4.1-py36_0.tar.bz2"
  }, 
  "pep8-1.7.0-py36_0": {
    "md5": "0f6f02ec9cbb90b1a3a4b63d4186562b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pep8-1.7.0-py36_0.tar.bz2"
  }, 
  "pickleshare-0.7.4-py36_0": {
    "md5": "251db0c78a67491aa4bb841b751850b3", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pickleshare-0.7.4-py36_0.tar.bz2"
  }, 
  "pillow-4.1.1-py36_0": {
    "md5": "10be176b33afc00adfe9031c4dc24c5f", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pillow-4.1.1-py36_0.tar.bz2"
  }, 
  "pip-9.0.1-py36_1": {
    "md5": "5ab66bd488e5f57f291942fd02cbdac5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pip-9.0.1-py36_1.tar.bz2"
  }, 
  "ply-3.10-py36_0": {
    "md5": "4d40c5c09cc83b7dfeb958979e4a0b7e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ply-3.10-py36_0.tar.bz2"
  }, 
  "prompt_toolkit-1.0.14-py36_0": {
    "md5": "60d7908c5ca3de244dbac52d31f00132", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/prompt_toolkit-1.0.14-py36_0.tar.bz2"
  }, 
  "psutil-5.2.2-py36_0": {
    "md5": "170d8b8ebb839ff81909c49d3b4b9175", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/psutil-5.2.2-py36_0.tar.bz2"
  }, 
  "py-1.4.33-py36_0": {
    "md5": "36214ff51872f363995be708b811bbd7", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/py-1.4.33-py36_0.tar.bz2"
  }, 
  "pycosat-0.6.2-py36_0": {
    "md5": "fb34dcb29966360a37ac34077603b063", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pycosat-0.6.2-py36_0.tar.bz2"
  }, 
  "pycparser-2.17-py36_0": {
    "md5": "09383bd56775a775628df24709373720", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pycparser-2.17-py36_0.tar.bz2"
  }, 
  "pycrypto-2.6.1-py36_6": {
    "md5": "43fdbd99e7a0aa60bbb47410edf0fe94", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pycrypto-2.6.1-py36_6.tar.bz2"
  }, 
  "pycurl-7.43.0-py36_2": {
    "md5": "b1497d4f2f625877659fe827ccc5c7c0", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pycurl-7.43.0-py36_2.tar.bz2"
  }, 
  "pyflakes-1.5.0-py36_0": {
    "md5": "516d398f070e92bc6dbaa6934310256e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyflakes-1.5.0-py36_0.tar.bz2"
  }, 
  "pygments-2.2.0-py36_0": {
    "md5": "1ed09e31ac45a42ba86b6e797332dcda", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pygments-2.2.0-py36_0.tar.bz2"
  }, 
  "pylint-1.6.4-py36_1": {
    "md5": "132ea7920ae72e6b14c7919161b8fc62", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pylint-1.6.4-py36_1.tar.bz2"
  }, 
  "pyodbc-4.0.16-py36_0": {
    "md5": "442f610c801865d6baa6109b15c1b590", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyodbc-4.0.16-py36_0.tar.bz2"
  }, 
  "pyopenssl-17.0.0-py36_0": {
    "md5": "c1771588a8d8e6465388beca61b37b56", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyopenssl-17.0.0-py36_0.tar.bz2"
  }, 
  "pyparsing-2.1.4-py36_0": {
    "md5": "b207d0e4b7b75269b3257ec12ebc3b40", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyparsing-2.1.4-py36_0.tar.bz2"
  }, 
  "pyqt-5.6.0-py36_2": {
    "md5": "b43a698e0e0b3536550cc258598cbb59", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyqt-5.6.0-py36_2.tar.bz2"
  }, 
  "pytables-3.2.2-np112py36_4": {
    "md5": "d6df926a06760acd8cc0acdf97a06718", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pytables-3.2.2-np112py36_4.tar.bz2"
  }, 
  "pytest-3.0.7-py36_0": {
    "md5": "6f4a3fdd2cc7f3b475f5106447f6efd8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pytest-3.0.7-py36_0.tar.bz2"
  }, 
  "python-3.6.1-2": {
    "md5": "2e8e18cef13cecda1f0f8318daef0077", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/python-3.6.1-2.tar.bz2"
  }, 
  "python-dateutil-2.6.0-py36_0": {
    "md5": "5542edeb648f7603c79d0f068af88a9d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/python-dateutil-2.6.0-py36_0.tar.bz2"
  }, 
  "pytz-2017.2-py36_0": {
    "md5": "87fb8b1d67e8fbc5a2c775b2adbf77c5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pytz-2017.2-py36_0.tar.bz2"
  }, 
  "pywavelets-0.5.2-np112py36_0": {
    "md5": "0a315d94973178e2aafd01f7e8b50a05", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pywavelets-0.5.2-np112py36_0.tar.bz2"
  }, 
  "pywin32-220-py36_2": {
    "md5": "ea9ca2d7faf77590bfc7a91bb3a3e66c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pywin32-220-py36_2.tar.bz2"
  }, 
  "pyyaml-3.12-py36_0": {
    "md5": "67adf9c28caeb4568b39b89e4dc6644d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyyaml-3.12-py36_0.tar.bz2"
  }, 
  "pyzmq-16.0.2-py36_0": {
    "md5": "c8ace9d012677d57950ec49aa95e845a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/pyzmq-16.0.2-py36_0.tar.bz2"
  }, 
  "qt-5.6.2-vc14_4": {
    "md5": "4fb8483e91c1d37394cbd79a341f2d5e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/qt-5.6.2-vc14_4.tar.bz2"
  }, 
  "qtawesome-0.4.4-py36_0": {
    "md5": "d78681341f533e211dc18523a0c575ec", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/qtawesome-0.4.4-py36_0.tar.bz2"
  }, 
  "qtconsole-4.3.0-py36_0": {
    "md5": "7fdefa18c8b63932cd453181cc28309e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/qtconsole-4.3.0-py36_0.tar.bz2"
  }, 
  "qtpy-1.2.1-py36_0": {
    "md5": "de1ce8d6bde797e70a1c0424a9c07d61", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/qtpy-1.2.1-py36_0.tar.bz2"
  }, 
  "requests-2.14.2-py36_0": {
    "md5": "79468af2ae1743611268b7b5ab24a94b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/requests-2.14.2-py36_0.tar.bz2"
  }, 
  "rope-0.9.4-py36_1": {
    "md5": "3348ae7f66a8f1f2f55f25202a6c68fe", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/rope-0.9.4-py36_1.tar.bz2"
  }, 
  "ruamel_yaml-0.11.14-py36_1": {
    "md5": "0774a9be0169daafabfdf411816c30d5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/ruamel_yaml-0.11.14-py36_1.tar.bz2"
  }, 
  "scikit-image-0.13.0-np112py36_0": {
    "md5": "81e7c00f083555181e9a8a2c3236f044", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/scikit-image-0.13.0-np112py36_0.tar.bz2"
  }, 
  "scikit-learn-0.18.1-np112py36_1": {
    "md5": "c1404fa627629eb5200d4628fc73a34b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/scikit-learn-0.18.1-np112py36_1.tar.bz2"
  }, 
  "scipy-0.19.0-np112py36_0": {
    "md5": "ad03674310fa0238308f127728392693", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/scipy-0.19.0-np112py36_0.tar.bz2"
  }, 
  "seaborn-0.7.1-py36_0": {
    "md5": "cd032eb8d1439a7111657b86e8acca4c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/seaborn-0.7.1-py36_0.tar.bz2"
  }, 
  "setuptools-27.2.0-py36_1": {
    "md5": "db0bfe0a3e4f006c38fd201e1ec1143d", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/setuptools-27.2.0-py36_1.tar.bz2"
  }, 
  "simplegeneric-0.8.1-py36_1": {
    "md5": "aef46a4fff1e06d765cda34066215174", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/simplegeneric-0.8.1-py36_1.tar.bz2"
  }, 
  "singledispatch-3.4.0.3-py36_0": {
    "md5": "2291863e7abd14b25062b07ea5957a5e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/singledispatch-3.4.0.3-py36_0.tar.bz2"
  }, 
  "sip-4.18-py36_0": {
    "md5": "746078f6898babae47654768adad7fd2", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sip-4.18-py36_0.tar.bz2"
  }, 
  "six-1.10.0-py36_0": {
    "md5": "71321b9b3633bced8c5a014f03b12628", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/six-1.10.0-py36_0.tar.bz2"
  }, 
  "snowballstemmer-1.2.1-py36_0": {
    "md5": "ab16731d1bb210fb665f467339e7cf09", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/snowballstemmer-1.2.1-py36_0.tar.bz2"
  }, 
  "sortedcollections-0.5.3-py36_0": {
    "md5": "cd62fd255cc903ea0c3d6efffec0e548", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sortedcollections-0.5.3-py36_0.tar.bz2"
  }, 
  "sortedcontainers-1.5.7-py36_0": {
    "md5": "1e4c036254133689fedb30d7a8d6e141", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sortedcontainers-1.5.7-py36_0.tar.bz2"
  }, 
  "sphinx-1.5.6-py36_0": {
    "md5": "fbe38f2342af1838d5c09a73fcf75ae4", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sphinx-1.5.6-py36_0.tar.bz2"
  }, 
  "spyder-3.1.4-py36_0": {
    "md5": "2fe584eab8a1cad4e51c9ca951eb9e1b", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/spyder-3.1.4-py36_0.tar.bz2"
  }, 
  "sqlalchemy-1.1.9-py36_0": {
    "md5": "d125e87ea2cb94b8d21de8c89c047cec", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sqlalchemy-1.1.9-py36_0.tar.bz2"
  }, 
  "statsmodels-0.8.0-np112py36_0": {
    "md5": "f1f2409163ee1bc041905e52115ae666", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/statsmodels-0.8.0-np112py36_0.tar.bz2"
  }, 
  "sympy-1.0-py36_0": {
    "md5": "890070bf94bc2aded7040a1408b735ad", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/sympy-1.0-py36_0.tar.bz2"
  }, 
  "tblib-1.3.2-py36_0": {
    "md5": "f8014dc43a6bde1f193e75e3bbe5bd8a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/tblib-1.3.2-py36_0.tar.bz2"
  }, 
  "testpath-0.3-py36_0": {
    "md5": "64b1502b10809e7ace2cc90ed54b850a", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/testpath-0.3-py36_0.tar.bz2"
  }, 
  "tk-8.5.18-vc14_0": {
    "md5": "894fc74b8402494a83adf0e4145af2c6", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/tk-8.5.18-vc14_0.tar.bz2"
  }, 
  "toolz-0.8.2-py36_0": {
    "md5": "13eb1c771e8f6ae73d37788e689b7bb3", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/toolz-0.8.2-py36_0.tar.bz2"
  }, 
  "tornado-4.5.1-py36_0": {
    "md5": "234f16fbecaf7f2c733d79c1f0b3b2c5", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/tornado-4.5.1-py36_0.tar.bz2"
  }, 
  "traitlets-4.3.2-py36_0": {
    "md5": "b9f977a121a836e0795106b5e2829119", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/traitlets-4.3.2-py36_0.tar.bz2"
  }, 
  "unicodecsv-0.14.1-py36_0": {
    "md5": "fd62a38edb6a14d9426d5e8c4882b1e4", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/unicodecsv-0.14.1-py36_0.tar.bz2"
  }, 
  "vs2015_runtime-14.0.25123-0": {
    "md5": "7cb8e392179dd01154f77e12e2135838", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/vs2015_runtime-14.0.25123-0.tar.bz2"
  }, 
  "wcwidth-0.1.7-py36_0": {
    "md5": "3b65e78870ea0f364de224ba3686a4f8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/wcwidth-0.1.7-py36_0.tar.bz2"
  }, 
  "werkzeug-0.12.2-py36_0": {
    "md5": "2a2768fba47a082193af1746d1e57505", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/werkzeug-0.12.2-py36_0.tar.bz2"
  }, 
  "wheel-0.29.0-py36_0": {
    "md5": "1ef9becd997934a01951798268408139", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/wheel-0.29.0-py36_0.tar.bz2"
  }, 
  "widgetsnbextension-2.0.0-py36_0": {
    "md5": "ea1eef669aadbdb39fe68ec39cb3b0a8", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/widgetsnbextension-2.0.0-py36_0.tar.bz2"
  }, 
  "win_unicode_console-0.5-py36_0": {
    "md5": "1a9224fe9c5e1ccc4638cd75498d5604", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/win_unicode_console-0.5-py36_0.tar.bz2"
  }, 
  "wrapt-1.10.10-py36_0": {
    "md5": "1dac8611d3a238e9b7f49e5359e2ea14", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/wrapt-1.10.10-py36_0.tar.bz2"
  }, 
  "xlrd-1.0.0-py36_0": {
    "md5": "c1bec4e36a432d865f8110eb8ebfef0f", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/xlrd-1.0.0-py36_0.tar.bz2"
  }, 
  "xlsxwriter-0.9.6-py36_0": {
    "md5": "42a1ea42eabb4b2633e418033fb331ac", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/xlsxwriter-0.9.6-py36_0.tar.bz2"
  }, 
  "xlwings-0.10.4-py36_0": {
    "md5": "f7e6d1bdb460cd6f89755032f1fc8840", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/xlwings-0.10.4-py36_0.tar.bz2"
  }, 
  "xlwt-1.2.0-py36_0": {
    "md5": "61268f7231df77bda5411121bb13d001", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/xlwt-1.2.0-py36_0.tar.bz2"
  }, 
  "zict-0.1.2-py36_0": {
    "md5": "6e0789c7aa38e54e736dc3ad12c0b74e", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/zict-0.1.2-py36_0.tar.bz2"
  }, 
  "zlib-1.2.8-vc14_3": {
    "md5": "d18e56750b5d191b0454918b659d1c6c", 
    "url": "https://repo.continuum.io/pkgs/free/win-64/zlib-1.2.8-vc14_3.tar.bz2"
  }
}
C_ENVS = {
  "root": [
    "python-3.6.1-2", 
    "_license-1.1-py36_1", 
    "alabaster-0.7.10-py36_0", 
    "anaconda-client-1.6.3-py36_0", 
    "anaconda-navigator-1.6.2-py36_0", 
    "anaconda-project-0.6.0-py36_0", 
    "asn1crypto-0.22.0-py36_0", 
    "astroid-1.4.9-py36_0", 
    "astropy-1.3.2-np112py36_0", 
    "babel-2.4.0-py36_0", 
    "backports-1.0-py36_0", 
    "beautifulsoup4-4.6.0-py36_0", 
    "bitarray-0.8.1-py36_1", 
    "blaze-0.10.1-py36_0", 
    "bleach-1.5.0-py36_0", 
    "bokeh-0.12.5-py36_1", 
    "boto-2.46.1-py36_0", 
    "bottleneck-1.2.1-np112py36_0", 
    "bzip2-1.0.6-vc14_3", 
    "cffi-1.10.0-py36_0", 
    "chardet-3.0.3-py36_0", 
    "click-6.7-py36_0", 
    "cloudpickle-0.2.2-py36_0", 
    "clyent-1.2.2-py36_0", 
    "colorama-0.3.9-py36_0", 
    "comtypes-1.1.2-py36_0", 
    "console_shortcut-0.1.1-py36_1", 
    "contextlib2-0.5.5-py36_0", 
    "cryptography-1.8.1-py36_0", 
    "curl-7.52.1-vc14_0", 
    "cycler-0.10.0-py36_0", 
    "cython-0.25.2-py36_0", 
    "cytoolz-0.8.2-py36_0", 
    "dask-0.14.3-py36_1", 
    "datashape-0.5.4-py36_0", 
    "decorator-4.0.11-py36_0", 
    "distributed-1.16.3-py36_0", 
    "docutils-0.13.1-py36_0", 
    "entrypoints-0.2.2-py36_1", 
    "et_xmlfile-1.0.1-py36_0", 
    "fastcache-1.0.2-py36_1", 
    "flask-0.12.2-py36_0", 
    "flask-cors-3.0.2-py36_0", 
    "freetype-2.5.5-vc14_2", 
    "get_terminal_size-1.0.0-py36_0", 
    "gevent-1.2.1-py36_0", 
    "greenlet-0.4.12-py36_0", 
    "h5py-2.7.0-np112py36_0", 
    "hdf5-1.8.15.1-vc14_4", 
    "heapdict-1.0.0-py36_1", 
    "html5lib-0.999-py36_0", 
    "icu-57.1-vc14_0", 
    "idna-2.5-py36_0", 
    "imagesize-0.7.1-py36_0", 
    "ipykernel-4.6.1-py36_0", 
    "ipython-5.3.0-py36_0", 
    "ipython_genutils-0.2.0-py36_0", 
    "ipywidgets-6.0.0-py36_0", 
    "isort-4.2.5-py36_0", 
    "itsdangerous-0.24-py36_0", 
    "jdcal-1.3-py36_0", 
    "jedi-0.10.2-py36_2", 
    "jinja2-2.9.6-py36_0", 
    "jpeg-9b-vc14_0", 
    "jsonschema-2.6.0-py36_0", 
    "jupyter-1.0.0-py36_3", 
    "jupyter_client-5.0.1-py36_0", 
    "jupyter_console-5.1.0-py36_0", 
    "jupyter_core-4.3.0-py36_0", 
    "lazy-object-proxy-1.2.2-py36_0", 
    "libpng-1.6.27-vc14_0", 
    "libtiff-4.0.6-vc14_3", 
    "llvmlite-0.18.0-py36_0", 
    "locket-0.2.0-py36_1", 
    "lxml-3.7.3-py36_0", 
    "markupsafe-0.23-py36_2", 
    "matplotlib-2.0.2-np112py36_0", 
    "menuinst-1.4.7-py36_0", 
    "mistune-0.7.4-py36_0", 
    "mkl-2017.0.1-0", 
    "mkl-service-1.1.2-py36_3", 
    "mpmath-0.19-py36_1", 
    "msgpack-python-0.4.8-py36_0", 
    "multipledispatch-0.4.9-py36_0", 
    "navigator-updater-0.1.0-py36_0", 
    "nbconvert-5.1.1-py36_0", 
    "nbformat-4.3.0-py36_0", 
    "networkx-1.11-py36_0", 
    "nltk-3.2.3-py36_0", 
    "nose-1.3.7-py36_1", 
    "notebook-5.0.0-py36_0", 
    "numba-0.33.0-np112py36_0", 
    "numexpr-2.6.2-np112py36_0", 
    "numpy-1.12.1-py36_0", 
    "numpydoc-0.6.0-py36_0", 
    "odo-0.5.0-py36_1", 
    "olefile-0.44-py36_0", 
    "openpyxl-2.4.7-py36_0", 
    "openssl-1.0.2l-vc14_0", 
    "packaging-16.8-py36_0", 
    "pandas-0.20.1-np112py36_0", 
    "pandocfilters-1.4.1-py36_0", 
    "partd-0.3.8-py36_0", 
    "path.py-10.3.1-py36_0", 
    "pathlib2-2.2.1-py36_0", 
    "patsy-0.4.1-py36_0", 
    "pep8-1.7.0-py36_0", 
    "pickleshare-0.7.4-py36_0", 
    "pillow-4.1.1-py36_0", 
    "pip-9.0.1-py36_1", 
    "ply-3.10-py36_0", 
    "prompt_toolkit-1.0.14-py36_0", 
    "psutil-5.2.2-py36_0", 
    "py-1.4.33-py36_0", 
    "pycosat-0.6.2-py36_0", 
    "pycparser-2.17-py36_0", 
    "pycrypto-2.6.1-py36_6", 
    "pycurl-7.43.0-py36_2", 
    "pyflakes-1.5.0-py36_0", 
    "pygments-2.2.0-py36_0", 
    "pylint-1.6.4-py36_1", 
    "pyodbc-4.0.16-py36_0", 
    "pyopenssl-17.0.0-py36_0", 
    "pyparsing-2.1.4-py36_0", 
    "pyqt-5.6.0-py36_2", 
    "pytables-3.2.2-np112py36_4", 
    "pytest-3.0.7-py36_0", 
    "python-dateutil-2.6.0-py36_0", 
    "pytz-2017.2-py36_0", 
    "pywavelets-0.5.2-np112py36_0", 
    "pywin32-220-py36_2", 
    "pyyaml-3.12-py36_0", 
    "pyzmq-16.0.2-py36_0", 
    "qt-5.6.2-vc14_4", 
    "qtawesome-0.4.4-py36_0", 
    "qtconsole-4.3.0-py36_0", 
    "qtpy-1.2.1-py36_0", 
    "requests-2.14.2-py36_0", 
    "rope-0.9.4-py36_1", 
    "ruamel_yaml-0.11.14-py36_1", 
    "scikit-image-0.13.0-np112py36_0", 
    "scikit-learn-0.18.1-np112py36_1", 
    "scipy-0.19.0-np112py36_0", 
    "seaborn-0.7.1-py36_0", 
    "setuptools-27.2.0-py36_1", 
    "simplegeneric-0.8.1-py36_1", 
    "singledispatch-3.4.0.3-py36_0", 
    "sip-4.18-py36_0", 
    "six-1.10.0-py36_0", 
    "snowballstemmer-1.2.1-py36_0", 
    "sortedcollections-0.5.3-py36_0", 
    "sortedcontainers-1.5.7-py36_0", 
    "sphinx-1.5.6-py36_0", 
    "spyder-3.1.4-py36_0", 
    "sqlalchemy-1.1.9-py36_0", 
    "statsmodels-0.8.0-np112py36_0", 
    "sympy-1.0-py36_0", 
    "tblib-1.3.2-py36_0", 
    "testpath-0.3-py36_0", 
    "tk-8.5.18-vc14_0", 
    "toolz-0.8.2-py36_0", 
    "tornado-4.5.1-py36_0", 
    "traitlets-4.3.2-py36_0", 
    "unicodecsv-0.14.1-py36_0", 
    "vs2015_runtime-14.0.25123-0", 
    "wcwidth-0.1.7-py36_0", 
    "werkzeug-0.12.2-py36_0", 
    "wheel-0.29.0-py36_0", 
    "widgetsnbextension-2.0.0-py36_0", 
    "win_unicode_console-0.5-py36_0", 
    "wrapt-1.10.10-py36_0", 
    "xlrd-1.0.0-py36_0", 
    "xlsxwriter-0.9.6-py36_0", 
    "xlwings-0.10.4-py36_0", 
    "xlwt-1.2.0-py36_0", 
    "zict-0.1.2-py36_0", 
    "zlib-1.2.8-vc14_3", 
    "anaconda-4.4.0-np112py36_0", 
    "conda-4.3.21-py36_0", 
    "conda-env-2.6.0-0"
  ]
}



def _link(src, dst, linktype=LINK_HARD):
    if on_win:
        raise NotImplementedError

    if linktype == LINK_HARD:
        os.link(src, dst)
    elif linktype == LINK_COPY:
        # copy relative symlinks as symlinks
        if islink(src) and not os.readlink(src).startswith('/'):
            os.symlink(os.readlink(src), dst)
        else:
            shutil.copy2(src, dst)
    else:
        raise Exception("Did not expect linktype=%r" % linktype)


def rm_rf(path):
    """
    try to delete path, but never fail
    """
    try:
        if islink(path) or isfile(path):
            # Note that we have to check if the destination is a link because
            # exists('/path/to/dead-link') will return False, although
            # islink('/path/to/dead-link') is True.
            os.unlink(path)
        elif isdir(path):
            shutil.rmtree(path)
    except (OSError, IOError):
        pass


def yield_lines(path):
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        yield line


prefix_placeholder = ('/opt/anaconda1anaconda2'
                      # this is intentionally split into parts,
                      # such that running this program on itself
                      # will leave it unchanged
                      'anaconda3')

def read_has_prefix(path):
    """
    reads `has_prefix` file and return dict mapping filenames to
    tuples(placeholder, mode)
    """
    import shlex

    res = {}
    try:
        for line in yield_lines(path):
            try:
                placeholder, mode, f = [x.strip('"\'') for x in
                                        shlex.split(line, posix=False)]
                res[f] = (placeholder, mode)
            except ValueError:
                res[line] = (prefix_placeholder, 'text')
    except IOError:
        pass
    return res


def exp_backoff_fn(fn, *args):
    """
    for retrying file operations that fail on Windows due to virus scanners
    """
    if not on_win:
        return fn(*args)

    import time
    import errno
    max_tries = 6  # max total time = 6.4 sec
    for n in range(max_tries):
        try:
            result = fn(*args)
        except (OSError, IOError) as e:
            if e.errno in (errno.EPERM, errno.EACCES):
                if n == max_tries - 1:
                    raise Exception("max_tries=%d reached" % max_tries)
                time.sleep(0.1 * (2 ** n))
            else:
                raise e
        else:
            return result


class PaddingError(Exception):
    pass


def binary_replace(data, a, b):
    """
    Perform a binary replacement of `data`, where the placeholder `a` is
    replaced with `b` and the remaining string is padded with null characters.
    All input arguments are expected to be bytes objects.
    """
    def replace(match):
        occurances = match.group().count(a)
        padding = (len(a) - len(b)) * occurances
        if padding < 0:
            raise PaddingError(a, b, padding)
        return match.group().replace(a, b) + b'\0' * padding

    pat = re.compile(re.escape(a) + b'([^\0]*?)\0')
    res = pat.sub(replace, data)
    assert len(res) == len(data)
    return res


def update_prefix(path, new_prefix, placeholder, mode):
    if on_win:
        # force all prefix replacements to forward slashes to simplify need
        # to escape backslashes - replace with unix-style path separators
        new_prefix = new_prefix.replace('\\', '/')

    path = os.path.realpath(path)
    with open(path, 'rb') as fi:
        data = fi.read()
    if mode == 'text':
        new_data = data.replace(placeholder.encode('utf-8'),
                                new_prefix.encode('utf-8'))
    elif mode == 'binary':
        if on_win:
            # anaconda-verify will not allow binary placeholder on Windows.
            # However, since some packages might be created wrong (and a
            # binary placeholder would break the package, we just skip here.
            return
        new_data = binary_replace(data, placeholder.encode('utf-8'),
                                  new_prefix.encode('utf-8'))
    else:
        sys.exit("Invalid mode:" % mode)

    if new_data == data:
        return
    st = os.lstat(path)
    # unlink in case the file is memory mapped
    exp_backoff_fn(os.unlink, path)
    with open(path, 'wb') as fo:
        fo.write(new_data)
    os.chmod(path, stat.S_IMODE(st.st_mode))


def name_dist(dist):
    return dist.rsplit('-', 2)[0]


def create_meta(prefix, dist, info_dir, extra_info):
    """
    Create the conda metadata, in a given prefix, for a given package.
    """
    # read info/index.json first
    with open(join(info_dir, 'index.json')) as fi:
        meta = json.load(fi)
    # add extra info
    meta.update(extra_info)
    # write into <prefix>/conda-meta/<dist>.json
    meta_dir = join(prefix, 'conda-meta')
    if not isdir(meta_dir):
        os.makedirs(meta_dir)
        with open(join(meta_dir, 'history'), 'w') as fo:
            fo.write('')
    with open(join(meta_dir, dist + '.json'), 'w') as fo:
        json.dump(meta, fo, indent=2, sort_keys=True)


def run_script(prefix, dist, action='post-link'):
    """
    call the post-link (or pre-unlink) script, and return True on success,
    False on failure
    """
    path = join(prefix, 'Scripts' if on_win else 'bin', '.%s-%s.%s' % (
            name_dist(dist),
            action,
            'bat' if on_win else 'sh'))
    if not isfile(path):
        return True
    if SKIP_SCRIPTS:
        print("WARNING: skipping %s script by user request" % action)
        return True

    if on_win:
        try:
            args = [os.environ['COMSPEC'], '/c', path]
        except KeyError:
            return False
    else:
        shell_path = '/bin/sh' if 'bsd' in sys.platform else '/bin/bash'
        args = [shell_path, path]

    env = os.environ
    env['PREFIX'] = prefix

    import subprocess
    try:
        subprocess.check_call(args, env=env)
    except subprocess.CalledProcessError:
        return False
    return True


url_pat = re.compile(r'''
(?P<baseurl>\S+/)                 # base URL
(?P<fn>[^\s#/]+)                  # filename
([#](?P<md5>[0-9a-f]{32}))?       # optional MD5
$                                 # EOL
''', re.VERBOSE)

def read_urls(dist):
    try:
        data = open(join(PKGS_DIR, 'urls')).read()
        for line in data.split()[::-1]:
            m = url_pat.match(line)
            if m is None:
                continue
            if m.group('fn') == '%s.tar.bz2' % dist:
                return {'url': m.group('baseurl') + m.group('fn'),
                        'md5': m.group('md5')}
    except IOError:
        pass
    return {}


def read_no_link(info_dir):
    res = set()
    for fn in 'no_link', 'no_softlink':
        try:
            res.update(set(yield_lines(join(info_dir, fn))))
        except IOError:
            pass
    return res


def linked(prefix):
    """
    Return the (set of canonical names) of linked packages in prefix.
    """
    meta_dir = join(prefix, 'conda-meta')
    if not isdir(meta_dir):
        return set()
    return set(fn[:-5] for fn in os.listdir(meta_dir) if fn.endswith('.json'))


def link(prefix, dist, linktype=LINK_HARD):
    '''
    Link a package in a specified prefix.  We assume that the packacge has
    been extra_info in either
      - <PKGS_DIR>/dist
      - <ROOT_PREFIX>/ (when the linktype is None)
    '''
    if linktype:
        source_dir = join(PKGS_DIR, dist)
        info_dir = join(source_dir, 'info')
        no_link = read_no_link(info_dir)
    else:
        info_dir = join(prefix, 'info')

    files = list(yield_lines(join(info_dir, 'files')))
    has_prefix_files = read_has_prefix(join(info_dir, 'has_prefix'))

    if linktype:
        for f in files:
            src = join(source_dir, f)
            dst = join(prefix, f)
            dst_dir = dirname(dst)
            if not isdir(dst_dir):
                os.makedirs(dst_dir)
            if exists(dst):
                if FORCE:
                    rm_rf(dst)
                else:
                    raise Exception("dst exists: %r" % dst)
            lt = linktype
            if f in has_prefix_files or f in no_link or islink(src):
                lt = LINK_COPY
            try:
                _link(src, dst, lt)
            except OSError:
                pass

    for f in sorted(has_prefix_files):
        placeholder, mode = has_prefix_files[f]
        try:
            update_prefix(join(prefix, f), prefix, placeholder, mode)
        except PaddingError:
            sys.exit("ERROR: placeholder '%s' too short in: %s\n" %
                     (placeholder, dist))

    if not run_script(prefix, dist, 'post-link'):
        sys.exit("Error: post-link failed for: %s" % dist)

    meta = {
        'files': files,
        'link': ({'source': source_dir,
                  'type': link_name_map.get(linktype)}
                 if linktype else None),
    }
    try:    # add URL and MD5
        meta.update(IDISTS[dist])
    except KeyError:
        meta.update(read_urls(dist))
    meta['installed_by'] = 'Anaconda3-4.4.0-Windows-x86_64'
    create_meta(prefix, dist, info_dir, meta)


def duplicates_to_remove(linked_dists, keep_dists):
    """
    Returns the (sorted) list of distributions to be removed, such that
    only one distribution (for each name) remains.  `keep_dists` is an
    interable of distributions (which are not allowed to be removed).
    """
    from collections import defaultdict

    keep_dists = set(keep_dists)
    ldists = defaultdict(set) # map names to set of distributions
    for dist in linked_dists:
        name = name_dist(dist)
        ldists[name].add(dist)

    res = set()
    for dists in ldists.values():
        # `dists` is the group of packages with the same name
        if len(dists) == 1:
            # if there is only one package, nothing has to be removed
            continue
        if dists & keep_dists:
            # if the group has packages which are have to be kept, we just
            # take the set of packages which are in group but not in the
            # ones which have to be kept
            res.update(dists - keep_dists)
        else:
            # otherwise, we take lowest (n-1) (sorted) packages
            res.update(sorted(dists)[:-1])
    return sorted(res)


def remove_duplicates():
    idists = []
    for line in open(join(PKGS_DIR, 'urls')):
        m = url_pat.match(line)
        if m:
            fn = m.group('fn')
            idists.append(fn[:-8])

    keep_files = set()
    for dist in idists:
        with open(join(ROOT_PREFIX, 'conda-meta', dist + '.json')) as fi:
            meta = json.load(fi)
        keep_files.update(meta['files'])

    for dist in duplicates_to_remove(linked(ROOT_PREFIX), idists):
        print("unlinking: %s" % dist)
        meta_path = join(ROOT_PREFIX, 'conda-meta', dist + '.json')
        with open(meta_path) as fi:
            meta = json.load(fi)
        for f in meta['files']:
            if f not in keep_files:
                rm_rf(join(ROOT_PREFIX, f))
        rm_rf(meta_path)


def link_idists():
    src = join(PKGS_DIR, 'urls')
    dst = join(ROOT_PREFIX, '.hard-link')
    assert isfile(src), src
    assert not isfile(dst), dst
    try:
        _link(src, dst, LINK_HARD)
        linktype = LINK_HARD
    except OSError:
        linktype = LINK_COPY
    finally:
        rm_rf(dst)

    for env_name in sorted(C_ENVS):
        dists = C_ENVS[env_name]
        assert isinstance(dists, list)
        if len(dists) == 0:
            continue

        prefix = prefix_env(env_name)
        for dist in dists:
            assert dist in IDISTS
            link(prefix, dist, linktype)

        for dist in duplicates_to_remove(linked(prefix), dists):
            meta_path = join(prefix, 'conda-meta', dist + '.json')
            print("WARNING: unlinking: %s" % meta_path)
            try:
                os.rename(meta_path, meta_path + '.bak')
            except OSError:
                rm_rf(meta_path)


def prefix_env(env_name):
    if env_name == 'root':
        return ROOT_PREFIX
    else:
        return join(ROOT_PREFIX, 'envs', env_name)


def post_extract(env_name='root'):
    """
    assuming that the package is extracted in the environment `env_name`,
    this function does everything link() does except the actual linking,
    i.e. update prefix files, run 'post-link', creates the conda metadata,
    and removed the info/ directory afterwards.
    """
    prefix = prefix_env(env_name)
    info_dir = join(prefix, 'info')
    with open(join(info_dir, 'index.json')) as fi:
        meta = json.load(fi)
    dist = '%(name)s-%(version)s-%(build)s' % meta
    if FORCE:
        run_script(prefix, dist, 'pre-unlink')
    link(prefix, dist, linktype=None)
    shutil.rmtree(info_dir)


def main():
    global ROOT_PREFIX, PKGS_DIR

    p = OptionParser(description="conda link tool used by installers")

    p.add_option('--root-prefix',
                 action="store",
                 default=abspath(join(__file__, '..', '..')),
                 help="root prefix (defaults to %default)")

    p.add_option('--post',
                 action="store",
                 help="perform post extract (on a single package), "
                      "in environment NAME",
                 metavar='NAME')

    opts, args = p.parse_args()
    if args:
        p.error('no arguments expected')

    ROOT_PREFIX = opts.root_prefix.replace('//', '/')
    PKGS_DIR = join(ROOT_PREFIX, 'pkgs')

    if opts.post:
        post_extract(opts.post)
        return

    if FORCE:
        print("using -f (force) option")

    link_idists()


def main2():
    global SKIP_SCRIPTS

    p = OptionParser(description="conda post extract tool used by installers")

    p.add_option('--skip-scripts',
                 action="store_true",
                 help="skip running pre/post-link scripts")

    p.add_option('--rm-dup',
                 action="store_true",
                 help="remove duplicates")

    opts, args = p.parse_args()
    if args:
        p.error('no arguments expected')

    if opts.skip_scripts:
        SKIP_SCRIPTS = True

    if opts.rm_dup:
        remove_duplicates()
        return

    post_extract()


def warn_on_special_chrs():
    if on_win:
        return
    for c in SPECIAL_ASCII:
        if c in ROOT_PREFIX:
            print("WARNING: found '%s' in install prefix." % c)


if __name__ == '__main__':
    if IDISTS:
        main()
        warn_on_special_chrs()
    else: # common usecase
        main2()
