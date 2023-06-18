# -*- coding: utf-8 -*-
"""
@author: Vladya
"""

import os
import tempfile
import ffmpeg
import librosa
import soundfile
from os import path


class InseparableFile(Exception):
    pass


def convert_folder(folder, out_folder, cmd, debug=False, ff_log_level=None):
    folder, out_folder = map(path.abspath, (folder, out_folder))
    for audio_file in map(path.abspath, librosa.util.find_files(folder)):
        _out, _ = path.splitext(path.relpath(audio_file, folder))
        _out = "{0}.wav".format(_out.replace(os.sep, '_'))
        out_path = path.abspath(path.join(out_folder, _out))
        try:
            prepare_audio_to_generate(audio_file, out_path, cmd, ff_log_level)
        except InseparableFile as ex:
            if debug:
                raise ex


def _create_dir(dirname):
    dirname = path.abspath(dirname)
    if not path.isdir(dirname):
        os.makedirs(dirname)


def _create_dir_for_file(filename):
    filename = path.abspath(filename)
    return _create_dir(path.dirname(filename))


def _get_tmp_name(_ext, _dir):
    _counter = 0
    while True:
        _counter += 1
        name = path.join(_dir, "_tmp_file{0}{1}".format(_counter, _ext))
        name = path.abspath(name)
        if not path.isfile(name):
            return name


def crop_audio(y_array, sr, max_duration=9.):

    _frame_length = .5
    _hop_length = .05
    while True:

        if (_frame_length < .01) and (_hop_length < .005):
            raise InseparableFile()

        result = []
        for start_i, end_i in librosa.effects.split(
            y_array,
            top_db=35,
            frame_length=librosa.time_to_samples(_frame_length, sr=sr),
            hop_length=librosa.time_to_samples(_hop_length, sr=sr)
        ):

            part = y_array[start_i:end_i]
            dur = librosa.get_duration(y=part, sr=sr)

            if dur > max_duration:
                _frame_length *= .9
                _hop_length *= .9
                break

            elif dur < 1.:
                continue

            result.append(part)

        else:

            return result


def prepare_audio_to_generate(_from, _to, cmd, ff_log_level=None):

    _from, _to = map(path.abspath, (_from, _to))
    out_name, out_ext = path.splitext(_to)
    out_ext = out_ext.strip().lower()
    name_now = _from

    with tempfile.TemporaryDirectory() as _tmp_dir:

        for kw in (
            # Последовательно конвертируем с новыми параметрами.
            {
                "q:a": 0,  # Постоянный битрейт.
                "ar": "44100",  # Ресемплинг до 44.1к.
                "af": "loudnorm=I=-24, highpass=f=40"  # Нормализация и HP
            }, {
                "af": (
                    "agate=release=300:attack=30:threshold=-35dB, "
                    "speechnorm=l=1"
                )
            }, {
                "af": "silenceremove=stop_periods=-1:stop_threshold=-40dB"
            }
        ):

            if ff_log_level:
                kw["ff_log_level"] = ff_log_level

            kw["cmd"] = cmd

            name_now = convert(
                name_now,
                _get_tmp_name(out_ext, _tmp_dir),
                **kw
            )

        with open(name_now, "rb") as _file:

            y, sr = librosa.load(_file, sr=44100)
            y, _ = librosa.effects.trim(y, top_db=35)

            try:
                for i, part in enumerate(crop_audio(y, sr), 1):
                    fn = "{0}_{1}{2}".format(out_name, i, out_ext)
                    _create_dir_for_file(fn)
                    soundfile.write(fn, part, sr)
            except InseparableFile:
                raise InseparableFile(_from)


def convert(_from, _to, **kwargs):

    ff_log_level = kwargs.pop("ff_log_level", "error")
    cmd = kwargs.pop("cmd", "ffmpeg")

    _from, _to = map(path.abspath, (_from, _to))

    if not kwargs:
        kwargs = {"q:a": 0}

    stream = ffmpeg.input(_from)
    stream = stream.output(_to, **kwargs)
    stream = stream.global_args("-loglevel", ff_log_level)

    _create_dir_for_file(_to)
    stream.run(overwrite_output=True, cmd=cmd)

    return _to
