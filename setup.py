# -*- coding: utf-8 -*-
"""
@author: Vladya
"""

import svc_py
from distutils.core import setup

setup(
    name='svc_py',
    version=svc_py.__version__,
    author="Vladya",
    packages=("svc_py",),
    install_requires=(
        "ffmpeg",
        "librosa",
        "soundfile"
    )
)
