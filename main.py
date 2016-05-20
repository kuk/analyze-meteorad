#!/usr/bin/env python

import re
import sys
import json
import os.path
import datetime
import time
import tempfile
from collections import OrderedDict

import requests
requests.packages.urllib3.disable_warnings()

from skimage import io, draw, morphology, filters, color, img_as_ubyte
import numpy as np
from matplotlib import pyplot as plt
from moviepy import editor as mpy


IMAGES = 'images'
VNUKOVO_URL = 'http://www.meteorad.ru/data/UVKVnukovo.png'
PROFSOUZ_URL = 'http://www.meteorad.ru/data/UVKProfsoyuz.png'
VNUKOVO_DIR = 'vnukovo'
PROFSOUZ_DIR = 'profsouz'
VIZ = 'viz'
TILES = os.path.join(VIZ, 'tiles')
TILES_LIST = os.path.join(VIZ, 'tiles.json')


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
        path = path.replace(':', '_') # если юзаешь винду
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


def join_split(split, colors=COLORS, tile=False):
    height, width = split[BACKGROUND].shape
    if tile:
        image = np.zeros((height, width, 4), dtype=np.uint8)
        for name, layer in split.iteritems():
            red, green, blue = colors[name]
            if name == BACKGROUND:
                opacity = 0
            else:
                opacity = 150
            image[layer] = (red, green, blue, opacity)
    else:
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


def overlay_mask(image, mask, alpha=0.9):
    assert alpha <= 1.0
    hsv = color.rgb2hsv(image)
    hsv[mask, 2] *= alpha
    overlay = color.hsv2rgb(hsv)
    return overlay


def build_animation(overlay_mask, duration=3, fps=5, path='animation.gif'):
    def make_frame(time, overlay_mask=overlay_mask, duration=duration, fps=fps):
        alpha = time / (duration - 1.0 / fps)
        if alpha > 1.0:
            alpha = 1.0
        image = overlay_mask(alpha)
        return img_as_ubyte(image)
    clip = mpy.VideoClip(make_frame, duration=duration)
    clip.write_gif(path, fps=fps)


def get_bad_weather_images():
    dir = 'images/vnukovo/'
    start = '2015-07-31T19:00:23.506671.png'
    stop = '2015-08-01T20:14:04.604683.png'
    return [os.path.join(dir, _)
            for _ in os.listdir(dir)
            if (start <= _ <= stop)]


def make_tile(input, output):
    image = io.imread(input)
    roi = get_roi(image)
    split = OrderedDict(split_colors(roi))
    split[BACKGROUND] = expand_background(split[BACKGROUND])
    guess = guess_unknown(split)
    unknown = get_unknown(split)
    restored = join_split(guess, tile=True)
    io.imsave(output, restored)


def make_reference_tile(mask, output):
    height, width = mask.shape[:2]
    refence = np.zeros((height, width, 4), dtype=np.uint8)
    refence[mask] = (0, 0, 0, 200)
    refence[~mask] = (255, 255, 255, 0)
    io.imsave(output, refence)


def make_tiles(inputs, dir=TILES):
    for path in inputs:
        print >>sys.stderr, path
        filename = os.path.basename(path)
        make_tile(path, os.path.join(dir, filename))


def dump_tiles_list(dir=TILES, output=TILES_LIST):
    list = {}
    for filename in os.listdir(dir):
        match = re.search('(\d\d\d\d-\d\d-\d\dT\d\d:\d\d)', filename)
        if match:
            timestamp = match.group(1)
            base = os.path.relpath(TILES, VIZ)
            path = os.path.join(base, filename)
            list[timestamp] = path
    with open(output, 'w') as file:
        json.dump(list, file)


if __name__ == '__main__':
    monitor()
