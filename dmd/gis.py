#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
from math import radians, cos, sin, asin, sqrt

from PIL import Image, ImageDraw, ImageFont
import pandas as pd

from dmd.models.DataRecords import DataRecord

logger = logging.getLogger(__name__)

EXPORT_SIZE = 2048
OUTLINE_COLOR = "#FFFFFF"
COLORS = ["#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f"]
COLORS = ["rgb(254,240,217)", "rgb(253,204,138)",
          "rgb(242,141,89)", "rgb(215,48,31)"]
COLOR_INITIAL = "#09192A"
THICKNESS = 1
FONTS_DIR = 'fonts'
TITLE_COLOR = "#000000"
SCALE_COLOR = "#000000"


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


class QuantileScale(object):

    def __init__(self, values, colors):
        self.colors = colors
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
            return []

    def color_for_value(self, value):
        if value < self.boundaries[0]:
            return self.colors[0]

        for index, bound in enumerate(self.boundaries):
            if value < bound:
                return self.colors[index - 1]

        return self.colors[-1]

    def available_colors(self):
        return self.colors


def fname_for(entity, period, indicator):
    return "{period}_{entity}_{indicator}.png".format(
        entity=entity.uuids,
        period=period.strid,
        indicator=indicator.slug)


def gen_map_for(entity, period, indicator, save_as=None,
                with_title=True, with_legend=True,
                with_index=True, with_scale=True):

    logger.info(entity)
    logger.info(period)
    logger.info(indicator)

    children = entity.get_children()
    bbox = children_bounds(entity)

    data = DataRecord.get_for(period, entity, indicator)

    scale = QuantileScale(values=[x['value'] for x in data.values()],
                          colors=COLORS)

    def color_for(e):
        try:
            return scale.color_for_value(data[e.uuids]['value'])
        except KeyError:
            return COLOR_INITIAL

    # setup coordinate system
    xdist = bbox[2] - bbox[0]
    ydist = bbox[3] - bbox[1]
    iwidth = EXPORT_SIZE
    iheight = EXPORT_SIZE
    xratio = iwidth / xdist
    yratio = iheight / ydist

    # blank (transparent) sheet
    image = Image.new("RGBA", (EXPORT_SIZE, EXPORT_SIZE), (255, 0, 0, 0))
    image.format = "PNG"

    # draw each feature independently
    for child in children:
        if not child.geojson.get('geometry'):
            continue
        pixels = []

        if child.geojson['geometry']['type'] == 'MultiPolygon':
            coordinates = child.geojson['geometry']['coordinates']
        else:
            coordinates = [child.geojson['geometry']['coordinates']]
        for feature_coord in coordinates:
            for x, y in feature_coord[0]:
                px = int(iwidth - ((bbox[2] - x) * xratio))
                py = int((bbox[3] - y) * yratio)
                pixels.append((px, py))

        feature_draw = ImageDraw.Draw(image)
        feature_draw.polygon(pixels,
                             outline=OUTLINE_COLOR,
                             fill=color_for(child))

    if with_title:
        title = "{ind} pour {period} / {entity}".format(
            ind=indicator.name,
            period=period.name,
            entity=entity.short_name)
        font = ImageFont.truetype(
            os.path.join(FONTS_DIR, "Roboto-Medium.ttf"),
            int(EXPORT_SIZE / 30))
        options = {
            'font': font,
            'fill': TITLE_COLOR
        }

        title_draw = ImageDraw.Draw(image)

        # text wrapping and positioning
        tpadding = int(EXPORT_SIZE / 100)
        tw, th = title_draw.textsize(title, font=font)
        lackingw = tw - (EXPORT_SIZE - (2 * tpadding))
        if lackingw > 0:
            nb_chars = len(title)
            char_ratio = tw / nb_chars
            line_cap = (tw - lackingw) / char_ratio

            import textwrap
            titles = textwrap.wrap(title, line_cap)
        else:
            titles = [title]
        for index, title in enumerate(titles):
            xpos = tpadding
            ypos = th * index + tpadding
            title_draw.text((xpos, ypos), title, **options)

    if with_legend:
        pass
        legend_width = int(EXPORT_SIZE / 7)
        legend_height = int(legend_width * .8)

        legend_bg = pil_round_rectangle(
            (legend_width, legend_height), 10, "white")

        lpadding = int(EXPORT_SIZE / 100)
        xpos = EXPORT_SIZE - legend_width - lpadding
        ypos = EXPORT_SIZE - legend_height - lpadding

        # paste bg onto main map
        image.paste(legend_bg, (xpos, ypos))

        font = ImageFont.truetype(
            os.path.join(FONTS_DIR, "Roboto-Thin.ttf"),
            int(EXPORT_SIZE / 75))

        legend_draw = ImageDraw.Draw(image)
        spacer = lpadding
        tspacer = int(spacer / 2)
        # draw colors
        lower_bound = 0

        for index, color in enumerate(scale.available_colors()):
            ltw = 30
            lth = 30
            cxpos = xpos + lpadding
            cypos = ypos + (ltw + spacer) * index + lpadding
            legend_draw.rectangle([(cxpos, cypos),
                                   (cxpos + ltw, cypos + lth)],
                                  fill=color, outline=color)
            # draw range
            upper_bound = scale.boundaries_for_color(color)
            print("boundaries_for_color", color, upper_bound)
            color_text = "{lb} – {ub}".format(lb=lower_bound, ub=upper_bound)
            print("color_text", color, color_text)

            ctw, cth = legend_draw.textsize(color_text, font=font)
            legend_draw.text((cxpos + ltw + tspacer, cypos),
                             color_text,
                             font=font, fill=SCALE_COLOR)

            lower_bound = upper_bound

    if with_index:
        pass

    if with_scale:
        # figure out distance and size
        bbox_distance = distance(*bbox)
        approx_scale_width = int(EXPORT_SIZE / 10)
        approx_scale_distance = approx_scale_width \
            * bbox_distance / EXPORT_SIZE
        scale_distance = roundup(approx_scale_distance)
        scale_size = scale_distance * EXPORT_SIZE / bbox_distance

        # positioning of scale on map
        spadding = int(EXPORT_SIZE / 100)
        xpos = spadding
        ypos = int(EXPORT_SIZE - spadding)

        # drawing scale line
        scale_draw = ImageDraw.Draw(image)
        scale_draw.line([(xpos, ypos), (xpos + scale_size, ypos)],
                        fill=SCALE_COLOR)

        # buds around scale
        scale_draw.line([(xpos, ypos - spadding),
                         (xpos, ypos)],
                        fill=SCALE_COLOR)
        scale_draw.line([(xpos + scale_size, ypos - spadding),
                         (xpos + scale_size, ypos)],
                        fill=SCALE_COLOR)

        # distance text
        scale_text = "{} km".format(scale_distance)
        font = ImageFont.truetype(
            os.path.join(FONTS_DIR, "Roboto-Thin.ttf"),
            int(EXPORT_SIZE / 75))
        stw, sth = scale_draw.textsize(scale_text, font=font)
        scale_draw.text((xpos + spadding, ypos - sth - spadding / 5),
                        scale_text,
                        font=font, fill=SCALE_COLOR)

    # save end result to file or buffer
    if save_as:
        image.save(save_as, "PNG")
    else:
        return image


def show(image):
    import os
    import time
    import tempfile
    import subprocess
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    image.save(f.name)
    subprocess.call(['open', f.name])
    time.sleep(5000)
    os.unlink(f.name)


def test_png():
    from dmd.models.Entities import Entity
    from dmd.models.Periods import MonthPeriod
    from dmd.models.Indicators import Indicator

    entity = Entity.get_root()
    period = MonthPeriod.get_or_create(2015, 9)
    indicator = Indicator.get_by_number('57')

    img = gen_map_for(entity, period, indicator)

    show(img)
