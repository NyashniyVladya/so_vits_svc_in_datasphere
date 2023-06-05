# -*- coding: utf-8 -*-
"""
@author: Vladya
"""

import _svc_py
from distutils.core import setup

setup(
    name='_svc_py',
    version=_svc_py.__version__,
    author="Vladya",
    packages=("_svc_py",),
    install_requires=(
        "ffmpeg",
        "librosa",
        "soundfile"
    )
)
