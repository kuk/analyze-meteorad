#!/usr/bin/env python

import sys
import os.path
import datetime
import time
import tempfile
from collections import OrderedDict

import requests
requests.packages.urllib3.disable_warnings()

from skimage import io, draw, morphology, filters, color
import numpy as np
from matplotlib import pyplot as plt


IMAGES = 'images'
VNUKOVO_URL = 'http://www.meteorad.ru/data/UVKVnukovo.png'
PROFSOUZ_URL = 'http://www.meteorad.ru/data/UVKProfsoyuz.png'
VNUKOVO_DIR = 'vnukovo'
PROFSOUZ_DIR = 'profsouz'

BACKGROUND = 'background'
COLORS = OrderedDict([
    (BACKGROUND, (208, 208, 208)),
    ('clouds', (156, 170, 177)),
    ('stratus_clouds', (162, 198, 255)),
    ('light_rain', (70, 255, 147)),
    ('medium_rain', (0, 194, 90)),
    ('heavy_rain', (0, 152, 0)),
    ('cumulus', (255, 255, 128)),
    ('light_shower', (62, 136, 255)),
    ('medium_shower', (1, 56, 255)),
    ('heavy_shower', (0, 0, 116)),
    ('thunder1', (255, 170, 127)),
    ('thunder2', (255, 85, 127)),
    ('thunder3', (255, 0, 0)),
    ('light_hail', (205, 101, 0)),
    ('medium_hail', (136, 68, 0)),
    ('heavy_hail', (94, 1, 0)),
    ('light_gust', (255, 174, 255)),
    ('medium_gust', (255, 85, 255)),
    ('heavy_gust', (199, 0, 199)),
    ('tornado', (62, 62, 94)),
])


def get_path(dir=VNUKOVO_DIR):
    timestamp = get_timestamp()
    return os.path.join(IMAGES, dir, timestamp + '.png')


def download_image(url, path):
    response = requests.get(url)
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)


def get_timestamp():
    return datetime.datetime.now().isoformat()


def monitor(timeout=10 * 60):
    while True:
        url = VNUKOVO_URL
        path = get_path(dir=VNUKOVO_DIR)
        print >>sys.stderr, url, '->', path
        download_image(url, path)
        
        url = PROFSOUZ_URL
        path = get_path(dir=PROFSOUZ_DIR)
        print >>sys.stderr, url, '->', path
        download_image(url, path)
        
        time.sleep(timeout)


def get_roi(image):
    return image[55:-22,277:-578]


def imshow(image, dpi=56):
    height, width = image.shape[:2]
    figsize = width / dpi, height / dpi
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.axis('off')
    io.imshow(image, interpolation='none')


def split_colors(image, colors=COLORS):
    for index, name in enumerate(colors):
        masks = ((image[:, :, index] == channel)
                 for index, channel in enumerate(colors[name]))
        mask = reduce(np.logical_and, masks)
        yield name, mask


def show_split(split):
    plt.figure(figsize=(20, 25))
    for index, name in enumerate(split):
        plt.subplot(5, 4, index + 1)
        plt.title(name)
        plt.imshow(split[name], cmap=plt.cm.gray, interpolation='none')
        plt.axis('off')
    plt.tight_layout()


def expand_background(background):
    height, width = background.shape
    mask = np.zeros((width, width), dtype=np.bool)
    circle = draw.circle(width / 2, width / 2, width / 2)
    mask[circle] = True
    border = (width - height) / 2
    mask = mask[border:height + border,:]
    background[~mask] = True
    return background


def join_split(split, colors=COLORS):
    height, width = split[BACKGROUND].shape
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for name, layer in split.iteritems():
        image[layer] = colors[name]
    return image


def get_unknown(split):
    masks = split.itervalues()
    unknown = ~reduce(np.logical_or, masks)
    return unknown


def guess_unknown(split, radius=9):
    smooth = OrderedDict(
        (
            name,
            filters.rank.sum(
                mask.astype(np.uint8),
                morphology.square(radius)
            )
        )
        for name, mask in split.iteritems()
    )

    masks = smooth.itervalues()
    maxes = reduce(np.maximum, masks)
    assert np.min(maxes) > 0

    guess = {}
    unknown = get_unknown(split)
    for name, layer in smooth.iteritems():
        equal = (layer == maxes)
        update = equal & unknown
        guess[name] = split[name] | update
    return guess


def overlay_mask(image, mask):
    hsv = color.rgb2hsv(image)
    hsv[mask, 2] *= 0.9
    overlay = color.hsv2rgb(hsv)
    return overlay


def get_bad_weather_images():
    dir = 'images/vnukovo/'
    start = '2015-07-31T19:00:23.506671.png'
    stop = '2015-08-01T20:14:04.604683.png'
    return [os.path.join(dir, _)
            for _ in os.listdir(dir)
            if (start <= _ <= stop)]





if __name__ == '__main__':
    monitor()
