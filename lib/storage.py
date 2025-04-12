from typing import List
import os
from glob import glob
import json

from appdirs import user_data_dir

from .data import PTOCollection


PATH = user_data_dir('ptocalc')


def load() -> List[PTOCollection]:
    out = []
    for fname in glob(os.path.join(PATH, '*.json')):
        with open(fname, 'r') as fp:
            obj = PTOCollection(**json.load(fp))
            obj.filename = os.path.basename(fname)
            for i, v in enumerate(obj.entries):
                v._id = i + 1
            out.append(obj)
    return list(sorted(out, key=lambda o: o.start))


def save(obj: PTOCollection):
    os.makedirs(PATH, exist_ok=True)
    fname = None
    if not obj.filename:
        num = 0
        while True:
            fname = str(obj.start.year)
            if num:
                fname += '-' + str(num)
            fname = os.path.join(PATH, fname + '.json')
            if os.path.exists(fname):
                num += 1
                continue
            obj.filename = os.path.basename(fname)
            break
    else:
        fname = os.path.join(PATH, obj.filename)

    with open(fname + '.TEMP', 'w') as fp:
        json.dump(obj.model_dump(), fp, indent=4)

    if os.path.exists(fname):
        os.unlink(fname)

    os.rename(fname + '.TEMP', fname)
