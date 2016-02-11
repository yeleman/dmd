#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import string
import copy
from math import radians, cos, sqrt

from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from babel.numbers import format_decimal
import textwrap

from dmd.models.DataRecords import DataRecord

logger = logging.getLogger(__name__)

CANVAS_SIZE = 2048
OUTLINE_COLOR = "#FFFFFF"
MAP_COLORS = ["#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f"]
# MAP_COLORS = ["rgb(254,240,217)", "rgb(253,204,138)",
#               "rgb(242,141,89)", "rgb(215,48,31)"]
COLOR_INITIAL = "#09192A"
THICKNESS = 1
FONTS_DIR = os.path.join('dmd', 'static', 'fonts')
TITLE_COLOR = "#000000"
SCALE_COLOR = "#000000"
INDEX_COLOR = "#555555"
LEGEND_FORMAT = "#,##0.#;-#"
SCALE_PADDING = CANVAS_SIZE // 100
LEGEND_PADDING = CANVAS_SIZE // 100
TITLE_PADDING = CANVAS_SIZE // 100
INDEX_PADDING = CANVAS_SIZE // 100


# def distance(pointa, pointb):
def distance(lon1, lat1, lon2, lat2):
    # lon1, lat1 = pointa
    # lon2, lat2 = pointb
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    R = 6371  # radius of the earth in km
    x = (lon2 - lon1) * cos(0.5 * (lat2 + lat1))
    y = lat2 - lat1
    return R * sqrt(x * x + y * y)


def roundup(x):
    if x > 1000:
        power = 1000
    elif x > 100:
        power = 100
    elif x > 10:
        power = 10
    else:
        return x
    return x if x % power == 0 else int(x + power - x % power)


def pil_round_corner(radius, fill):
    """Draw a round corner"""
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
    return corner


def pil_round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('RGBA', size, fill)
    corner = pil_round_corner(radius, fill)
    rectangle.paste(corner, (0, 0))
    # Rotate the corner and paste it
    rectangle.paste(corner.rotate(90), (0, height - radius))
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle


def explode(coords):
    """ Explode a GeoJSON geometry's coordinates object and
        yield coordinate tuples.
        As long as the input is conforming, the type of
        the geometry doesn't matter. """
    for e in coords:
        if isinstance(e, (float, int, long)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def bounds_of(feature):
    return get_bounds(feature['geometry']['coordinates'])


def get_bounds(coordinates):
    x, y = zip(*list(explode(coordinates)))
    return min(x), min(y), max(x), max(y)


def children_bounds(entity):
    return get_bounds([f.get('geometry', {}).get('coordinates', [])
                       for f in entity.children_geojson.get('features', {})
                       if f.get('geometry', {})])


def display_right(entity):
    ''' whether to display index on the right

        required for entities with many small children on the top left '''

    return entity.short_name in ("Kinshasa DPS",
                                 "Lualaba DPS",
                                 "Nord Ubangi DPS",
                                 "Tanganika DPS",
                                 "Kwango DPS",
                                 "Kasai Oriental DPS",
                                 "Haut Uele DPS",
                                 "Haut Lomami DPS",
                                 "Haut Katanga DPS")


class QuantileScale(object):

    def __init__(self, values, colors):
        self.colors = copy.copy(colors)
        self.serie = pd.Series(values)

        # when there's no data
        if not len(self.serie):
            self._boundaries = []
            return

        # when there's less than 4 data
        if len(self.serie) < len(self.colors):
            self.colors = self.colors[:len(self.serie)]

        self._min = self.serie.min()
        self._max = self.serie.max()
        self.nb_breaks = len(self.colors)

        # single value
        if self.nb_breaks == 1:
            self._boundaries = [self.serie[0]]
            return

        x = 1 / (self.nb_breaks - 1)
        self.breaks = [x * i for i in range(1, self.nb_breaks)]
        self.quantile = self.serie.quantile([0, .33, .66, 1])

        try:
            self._boundaries = self.quantile.tolist()
        except:
            self._boundaries = []

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def boundaries(self):
        return self._boundaries

    def boundaries_for_color(self, color):
        try:
            return self.boundaries[self.colors.index(color)]
        except:
            if color == self.available_colors()[0]:
                return self.min
            if color == self.available_colors()[-1]:
                return self.max
            return None

    def color_for_value(self, value):
        if value < self.boundaries[0]:
            return self.colors[0]

        for index, bound in enumerate(self.boundaries):
            if value < bound:
                return self.colors[index - 1]

        return self.colors[-1]

    def available_colors(self):
        return self.colors


def letter_for(index):
    if index > 25:
        return string.ascii_uppercase[0] + string.ascii_uppercase[index - 25]
    return string.ascii_uppercase[index]


def get_image(width, height, alpha=0):
    i = Image.new("RGBA", (width, height), (255, 255, 255, alpha))
    i.format = "PNG"
    return i


def get_font(variant, size, mono=False):
    return ImageFont.truetype(
        os.path.join(FONTS_DIR,
                     "Roboto{mono}-{variant}.ttf"
                     .format(variant=variant.title(),
                             mono="Mono" if mono else '')), size)


def build_title_for(indicator, periods, entity):
    if len(periods) == 1:
        title_fmt = "{ind} pour {period} / {entity}"
    else:
        title_fmt = "{ind} entre {perioda} et {periodb} / {entity}"
    title = title_fmt.format(
        ind=indicator.name,
        perioda=periods[0].name,
        periodb=periods[-1].name,
        period=periods[-1].name,
        entity=entity.short_name)
    font = get_font('Medium', CANVAS_SIZE // 30)
    options = {
        'font': font,
        'fill': TITLE_COLOR,
    }

    image = get_image(CANVAS_SIZE - (TITLE_PADDING * 2),
                      CANVAS_SIZE)
    image_draw = ImageDraw.Draw(image)

    # text wrapping and positioning
    tw, th = image_draw.textsize(title, font=font)
    lackingw = tw - image.size[0]
    if lackingw > 0:
        nb_chars = len(title)
        char_ratio = tw / nb_chars
        line_cap = (tw - lackingw) / char_ratio

        titles = textwrap.wrap(title, line_cap)
    else:
        titles = [title]

    # actualy draw title
    for index, title in enumerate(titles):
        xpos = TITLE_PADDING
        ypos = th * index + TITLE_PADDING
        image_draw.text((xpos, ypos), title, **options)

    tw, th = image_draw.textsize(title, font=font)
    height = ypos + th
    return image.crop((0, 0, image.size[0], height))
    return image


def build_scale_for(bbox):

    # figure out distance and size
    bbox_distance = distance(*bbox)
    approx_scale_width = CANVAS_SIZE // 10
    approx_scale_distance = approx_scale_width \
        * bbox_distance / CANVAS_SIZE
    scale_distance = roundup(approx_scale_distance)
    scale_size = int(scale_distance * CANVAS_SIZE // bbox_distance)

    # setup image
    scale_width = scale_size + 2
    scale_height = SCALE_PADDING * 2
    image = get_image(scale_width, scale_height)

    xpos = 0
    ypos = scale_height - 2

    # drawing scale line
    scale_draw = ImageDraw.Draw(image)
    scale_draw.line([(xpos, ypos), (xpos + scale_size, ypos)],
                    fill=SCALE_COLOR)

    # buds around scale
    scale_draw.line([(xpos, ypos - scale_height),
                     (xpos, ypos)],
                    fill=SCALE_COLOR)
    scale_draw.line([(xpos + scale_size, ypos - scale_height),
                     (xpos + scale_size, ypos)],
                    fill=SCALE_COLOR)

    # distance text
    scale_text = "{} km".format(scale_distance)
    font = get_font('Medium', CANVAS_SIZE // 50)
    stw, sth = scale_draw.textsize(scale_text, font=font)
    scale_draw.text((xpos + SCALE_PADDING, ypos - sth - SCALE_PADDING / 5),
                    scale_text,
                    font=font, fill=SCALE_COLOR)

    return image


def build_legend_for(scale):
    font = get_font('Thin', CANVAS_SIZE // 75)

    # color square dimensions
    ltw = 30
    lth = 30

    # legend spacers
    spacer = LEGEND_PADDING
    tspacer = spacer // 2

    # sandbox to write text to for measurements only
    sandbox = get_image(CANVAS_SIZE, CANVAS_SIZE)
    sandbox_draw = ImageDraw.Draw(sandbox)
    text_width = lambda text: sandbox_draw.textsize(text, font=font)[0]

    # prepare labels and find out required text width
    labels = []
    lower_bound = 0
    ltext_width = 0
    avail_colors = []
    avail_colors = scale.available_colors() if scale.boundaries else []
    for index, color in enumerate(avail_colors):
        upper_bound = scale.boundaries_for_color(color)
        color_text = "{lb} – {ub}".format(
            lb=format_decimal(lower_bound, format=LEGEND_FORMAT),
            ub=format_decimal(upper_bound, format=LEGEND_FORMAT))
        ltext_width = max([ltext_width, text_width(color_text)])
        lower_bound = upper_bound
        labels.append(color_text)
    # missing data
    labels.append("manquant")
    ltext_width = max([ltext_width, text_width("manquant")])
    avail_colors.append(COLOR_INITIAL)

    # draw background
    legend_width = LEGEND_PADDING + ltw + tspacer \
        + ltext_width + LEGEND_PADDING
    legend_height = LEGEND_PADDING + \
        (len(avail_colors)) * (lth + spacer) \
        - spacer + LEGEND_PADDING

    image = get_image(legend_width, legend_height)
    legend_draw = ImageDraw.Draw(image)

    legend_bg = pil_round_rectangle(
        (legend_width, legend_height), 10, "white")

    # paste bg onto main map
    image.paste(legend_bg, (0, 0))

    # draw colors and text
    for index, color in enumerate(avail_colors):
        cxpos = LEGEND_PADDING
        cypos = (ltw + spacer) * index + LEGEND_PADDING
        legend_draw.rectangle([(cxpos, cypos),
                               (cxpos + ltw, cypos + lth)],
                              fill=color, outline=color)
        # draw range
        legend_draw.text((cxpos + ltw + tspacer, cypos),
                         labels[index],
                         font=font, fill=SCALE_COLOR)

    return image


def build_index_for(indicator, periods, children):

    def value_text_for(indicator, periods, child):
        if len(periods) == 1:
            dr = DataRecord.get_or_none(
                indicator=indicator,
                period=periods[-1],
                entity=child,
                only_validated=True)
            if dr is None:
                return "-"
            return dr.human()
        else:
            dr = indicator.data_for(periods=periods, entity=child)
            return dr['human']

    font = get_font('Regular', CANVAS_SIZE // 75, mono=True)

    # legend spacers
    spacer = INDEX_PADDING
    hspacer = 30
    tspacer = spacer // 2

    # sandbox to write text to for measurements only
    sandbox = get_image(CANVAS_SIZE, CANVAS_SIZE)
    sandbox_draw = ImageDraw.Draw(sandbox)
    text_width = lambda text: sandbox_draw.textsize(text, font=font)[0]

    # prepare labels and find out required text width
    text_fmt = "{name}{sp}{value}"
    sp = " "
    labels = []
    itext_width = 0
    spaced_text = lambda mxl, label, name, value: text_fmt.format(
        name=name,
        sp=" ".join(['' for _ in range(mxl - len(label) + 2)]),
        value=value)

    for index, child in enumerate(children):
        name = "{}. {}".format(letter_for(index), child.short_name)
        value = value_text_for(indicator, periods, child)
        child_text = text_fmt.format(name=name, sp=sp, value=value)
        itext_width = max([itext_width, text_width(child_text)])
        labels.append((child_text, name, value))
    max_chars = max([len(s[0]) for s in labels])
    labels = [spaced_text(max_chars, *label) for label in labels]

    # draw background
    index_width = INDEX_PADDING + tspacer \
        + itext_width + INDEX_PADDING
    index_height = INDEX_PADDING + \
        len(labels) * hspacer + INDEX_PADDING

    image = get_image(index_width, index_height)
    legend_draw = ImageDraw.Draw(image)

    legend_bg = pil_round_rectangle(
        (index_width, index_height), 10, "white")

    # paste bg onto main map
    image.paste(legend_bg, (0, 0))

    # draw colors and text
    for index, label in enumerate(labels):
        cxpos = INDEX_PADDING
        cypos = hspacer * index + INDEX_PADDING
        # draw range
        legend_draw.text((cxpos + tspacer, cypos),
                         labels[index],
                         font=font, fill=SCALE_COLOR)

    return image


def fname_for(entity, periods, indicator):
    return "{perioda}_{periodb}_{entity}_indic{indicator}.png".format(
        entity=entity.short_name,
        perioda=periods[0].strid,
        periodb=periods[-1].strid,
        indicator=indicator.number)


def gen_map_for(entity, periods, indicator, save_as=None,
                with_title=True, with_legend=True,
                with_index=True, with_scale=True):

    children = sorted(entity.get_children(), key=lambda x: x.short_name)
    bbox = children_bounds(entity)

    # data = indicator.data_for(periods=periods, entity=entity)
    data = DataRecord.get_for(periods[-1], entity, indicator)
    # from pprint import pprint as pp ; pp(data.values())
    scale = QuantileScale(values=[x['value'] for x in data.values()],
                          colors=MAP_COLORS)

    def color_for(e):
        if data is None:
            return COLOR_INITIAL
        try:
            return scale.color_for_value(data[e.uuids]['value'])
        except KeyError:
            return COLOR_INITIAL

    # setup coordinate system
    xdist = bbox[2] - bbox[0]
    ydist = bbox[3] - bbox[1]
    iwidth = CANVAS_SIZE
    iheight = CANVAS_SIZE
    xratio = iwidth / xdist
    yratio = iheight / ydist

    def mmap(x, y):
        return int(iwidth - ((bbox[2] - x) * xratio)), \
            int((bbox[3] - y) * yratio)

    # blank (transparent) sheet
    image = get_image(CANVAS_SIZE, CANVAS_SIZE)

    # draw each feature independently
    for index, child in enumerate(children):
        if not child.geojson.get('geometry'):
            continue
        pixels = []

        if child.geojson['geometry']['type'] == 'MultiPolygon':
            coordinates = child.geojson['geometry']['coordinates']
        else:
            coordinates = [child.geojson['geometry']['coordinates']]

        pixels = [mmap(x, y)
                  for feature_coord in coordinates
                  for x, y in feature_coord[0]]

        feature_draw = ImageDraw.Draw(image)
        feature_draw.polygon(pixels,
                             outline=OUTLINE_COLOR,
                             fill=color_for(child))

        # draw a letter
        if with_index and child.gps:
            coords = mmap(*child.gps)
            negpad = CANVAS_SIZE // 80 // 2
            index_font = get_font('Regular', CANVAS_SIZE // 80, mono=True)
            feature_draw.text(
                (coords[0] - negpad, coords[1] - negpad),
                letter_for(index),
                font=index_font, fill=INDEX_COLOR)

    if with_legend:
        legend = build_legend_for(scale)
        image.paste(legend, (CANVAS_SIZE - LEGEND_PADDING - legend.size[0],
                             CANVAS_SIZE - LEGEND_PADDING - legend.size[1]),
                    mask=legend)

    if with_title:
        title = build_title_for(indicator, periods, entity)
        export_width = image.size[0] + title.size[1]
        export_height = CANVAS_SIZE + title.size[1]
        export_image = get_image(export_width, export_height)
        export_image.paste(title, (0, 0), mask=title)
        export_image.paste(image, (title.size[1], title.size[1]), mask=image)

        # replace main image with new one (larger with title)
        image = export_image

    if with_index:
        index = build_index_for(indicator, periods, children)
        ileft_coords = (INDEX_PADDING, title.size[1] + INDEX_PADDING)
        iright_coords = (image.size[0] - index.size[0] - INDEX_PADDING,
                         title.size[1] + INDEX_PADDING)
        index_coords = iright_coords if display_right(entity) else ileft_coords
        image.paste(index, index_coords,
                    mask=index)

    if with_scale:
        visual_scale = build_scale_for(bbox)
        image.paste(visual_scale,
                    (SCALE_PADDING,
                     image.size[1] - SCALE_PADDING - visual_scale.size[1]),
                    mask=visual_scale)

    # save end result to file or buffer
    if save_as:
        image.save(save_as, "PNG", mode="RGBA")
    else:
        return image
