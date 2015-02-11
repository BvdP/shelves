#!/usr/bin/env python

import inkex
import simplestyle

from math import *
from collections import namedtuple

#Note: keep in mind that SVG coordinates start in the top-left corner i.e. with an inverted y-axis


default_style = simplestyle.formatStyle(
    {'stroke': '#000000',
    'stroke-width': '1',
    'fill': 'none'
    })


def draw_SVG_square(parent, w, h, x, y, style=default_style):
    attribs = {
        'style': style,
        'height': str(h),
        'width': str(w),
        'x': str(x),
        'y': str(y)
    }
    inkex.etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)

def draw_SVG_ellipse(parent, rx, ry, center, start_end=(0, 2*pi), style=default_style, transform=''):
    ell_attribs = {'style': style,
        inkex.addNS('cx', 'sodipodi'): str(center.x),
        inkex.addNS('cy', 'sodipodi'): str(center.y),
        inkex.addNS('rx', 'sodipodi'): str(rx),
        inkex.addNS('ry', 'sodipodi'): str(ry),
        inkex.addNS('start', 'sodipodi'): str(start_end[0]),
        inkex.addNS('end', 'sodipodi'): str(start_end[1]),
        inkex.addNS('open', 'sodipodi'): 'true',  #all ellipse sectors we will draw are open
        inkex.addNS('type', 'sodipodi'): 'arc',
        'transform': transform
    }
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), ell_attribs)


def draw_SVG_arc(parent, rx, ry, x_axis_rot, style=default_style):
    arc_attribs = {'style': style,
        'rx': str(rx),
        'ry': str(ry),
        'x-axis-rotation': str(x_axis_rot),
        'large-arc': '',
        'sweep': '',
        'x': '',
        'y': ''
        }
        #name='part'
    style = {'stroke': '#000000', 'fill': 'none'}
    drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), drw)
    inkex.addNS('', 'svg')

def draw_SVG_text(parent, coordinate, txt, style=default_style):
    text = inkex.etree.Element(inkex.addNS('text', 'svg'))
    text.text = txt
    text.set('x', str(coordinate.x))
    text.set('y', str(coordinate.y))
    style = {'text-align': 'center', 'text-anchor': 'middle'}
    text.set('style', simplestyle.formatStyle(style))
    parent.append(text)

#draw an SVG line segment between the given (raw) points
def draw_SVG_line(parent, start, end, style = default_style):
    line_attribs = {'style': style,
                    'd': 'M '+str(start.x)+','+str(start.y)+' L '+str(end.x)+','+str(end.y)}

    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), line_attribs)


def SVG_move_to(x, y):
    return "M %d %d" % (x, y)

def SVG_line_to(x, y):
    return "L %d %d" % (x, y)

def SVG_arc_to(rx, ry, x, y):
    la = sw = 0
    return "A %d %d 0 %d %d" % (rx, ry, la, sw, x, y)

def SVG_path(components):
    return '<path d="' + ' '.join(components) + '">'

def SVG_curve(parent, segments, style, closed=True):
    #pathStr = 'M '+ segments[0]
    pathStr = ' '.join(segments)
    if closed:
        pathStr += ' z'
    attributes = {
      'style': style,
      'd': pathStr}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), attributes)


class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "(%f, %f)" % (self.x, self.y)

    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y)

    # def __radd__(self, other):
    #    return self + other

    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y)

    def __mul__(self, factor):
        return Coordinate(self.x * factor, self.y * factor)

    # def __rmul__(self, other):
    #     return self * other

    def __div__(self, quotient):
        return Coordinate(self.x / quotient, self.y / quotient)


class Shelves(inkex.Effect):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        inkex.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']

        self.OptionParser.add_option('--unit', action = 'store',
          type = 'string', dest = 'unit', default = 'cm',
          help = 'Unit, should be one of ')

        self.OptionParser.add_option('--tolerance', action = 'store',
          type = 'float', dest = 'tolerance', default = '0.05',
          help = '')

        self.OptionParser.add_option('--thickness', action = 'store',
          type = 'float', dest = 'thickness', default = '1.2',
          help = 'Material thickness')

        self.OptionParser.add_option('--width', action = 'store',
          type = 'float', dest = 'width', default = '3.0',
          help = 'Box width')

        self.OptionParser.add_option('--height', action = 'store',
          type = 'float', dest = 'height', default = '10.0',
          help = 'Box height')

        self.OptionParser.add_option('--depth', action = 'store',
          type = 'float', dest = 'depth', default = '3.0',
          help = 'Box depth')

        self.OptionParser.add_option('--shelves', action = 'store',
          type = 'string', dest = 'shelve_list', default = '',
          help = 'semicolon separated list of shelve heigths')

        self.OptionParser.add_option('--groove_depth', action = 'store',
          type = 'float', dest = 'groove_depth', default = '0.5',
          help = 'Groove depth')

        self.OptionParser.add_option('--tab_size', action = 'store',
          type = 'float', dest = 'tab_size', default = '10',
          help = 'Approximate tab width (tabs will be evenly spaced along the length of the edge)')

    try:
        inkex.Effect.unittouu   # unitouu has moved since Inkscape 0.91
    except AttributeError:
        try:
            def unittouu(self, unit):
                return inkex.unittouu(unit)
        except AttributeError:
            pass

    def effect(self):
        """
        Draws a shelved cupboard, based on provided parameters
        """

        # input sanity check and unit conversion
        error = False

        if self.options.unit not in self.knownUnits:
            inkex.errormsg('Error: unknown unit. '+ self.options.unit)
            error = True
        unit = self.options.unit

        if min(self.options.height, self.options.width, self.options.depth) == 0:
            inkex.errormsg('Error: Dimensions must be non zero')
            error = True

        shelves = []

        for s in self.options.shelve_list.split(';'):
            try:
                float(s)
                shelves.append(self.unittouu(str(s) + unit))
            except ValueError:
                inkex.errormsg('Error: nonnumeric value in shelves (' + s + ')')
                error = True

        if error:
            exit()

        height = self.unittouu(str(self.options.height) + unit)
        width = self.unittouu(str(self.options.width) + unit)
        depth = self.unittouu(str(self.options.depth) + unit)
        thickness = self.unittouu(str(self.options.thickness) + unit)
        groove_depth = self.unittouu(str(self.options.groove_depth) + unit)
        tab_size = self.unittouu(str(self.options.tab_size) + unit)

        svg = self.document.getroot()
        docWidth = self.unittouu(svg.get('width'))
        docHeigh = self.unittouu(svg.attrib['height'])

        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Shelves')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')


        def H(x):
            return Coordinate(x, 0)

        def V(x):
            return Coordinate(0, x)

        def tab_count(dist, desired_tab_size):
            F = int(dist // desired_tab_size)
            if F / 2 % 2 == 0:  # make sure we have an odd number of tabs
                n = F // 2
            else:
                n = (F - 1) // 2

            return 2 * n + 1

        # create groups for the different parts
        g_l_side = inkex.etree.SubElement(layer, 'g')
        g_r_side = inkex.etree.SubElement(layer, 'g')
        g_top = inkex.etree.SubElement(layer, 'g')
        g_bottom = inkex.etree.SubElement(layer, 'g')
        g_back = inkex.etree.SubElement(layer, 'g')
        g_divider = inkex.etree.SubElement(layer, 'g')


        h_spacing = H(10 + thickness)
        v_spacing = V(10 + thickness)

        v_tab_count = tab_count(height, tab_size)
        v_tab = V(height / v_tab_count)
        h_tab_count = tab_count(width, tab_size)
        h_tab = H(width / h_tab_count)
        d_tab_count = tab_count(depth, tab_size)
        d_tab_size = depth / d_tab_count

        h_tab_height = V(thickness)

        top_origin = h_spacing * 2 + v_spacing + H(depth)
        left_side_origin = h_spacing + v_spacing * 2 + V(depth)
        back_origin = left_side_origin +  h_spacing + H(depth)
        right_side_origin = back_origin + h_spacing + H(width)
        bottom_origin = back_origin + v_spacing + V(height)

        def draw_tabbed_edge(parent, edge_start, tab, inset, count, invert = False):
            start = edge_start + (inset if invert else Coordinate(0, 0))
            for i in range(count):
                if (i % 2 == 0) != invert:
                    t_offset = inset
                else:
                    t_offset = Coordinate(0, 0)
                end = start + tab
                #inkex.debug(str((i, start, end, t_offset)))
                draw_SVG_line(parent, start, end)
                if i < count - 1:   # skip last one
                    start = edge_start + t_offset + tab * (i + 1)
                    draw_SVG_line(parent, end, start)

        # top
        draw_SVG_line(g_top, top_origin, top_origin + H(width))
        draw_tabbed_edge(g_top, top_origin, V(d_tab_size), H(thickness), d_tab_count, False)
        draw_tabbed_edge(g_top, top_origin + H(width) , V(d_tab_size), H(-thickness), d_tab_count, False)
        draw_tabbed_edge(g_top, top_origin + V(depth), h_tab, V(-thickness), h_tab_count, True)


        # left
        draw_SVG_line(g_l_side, left_side_origin, left_side_origin + V(height))
        draw_tabbed_edge(g_l_side, left_side_origin + H(depth), v_tab, H(-thickness), v_tab_count, True)
        draw_tabbed_edge(g_l_side, left_side_origin, H(d_tab_size), V(thickness), d_tab_count, True)
        draw_tabbed_edge(g_l_side, left_side_origin + V(height), H(d_tab_size), V(-thickness), d_tab_count, True)

        # back
        draw_tabbed_edge(g_back, back_origin, v_tab, H(thickness), v_tab_count, False)
        draw_tabbed_edge(g_back, back_origin + H(width), v_tab, H(-thickness), v_tab_count, False)
        draw_tabbed_edge(g_back, back_origin, h_tab, V(thickness), h_tab_count, False)
        draw_tabbed_edge(g_back, back_origin + V(height), h_tab, V(-thickness), h_tab_count, False)

        # right
        draw_SVG_line(g_r_side, right_side_origin + H(depth), right_side_origin + H(depth) + V(height))
        draw_tabbed_edge(g_r_side, right_side_origin, v_tab, H(thickness), v_tab_count, True)
        draw_tabbed_edge(g_r_side, right_side_origin, H(d_tab_size), V(thickness), d_tab_count, True)
        draw_tabbed_edge(g_r_side, right_side_origin + V(height), H(d_tab_size), V(-thickness), d_tab_count, True)

        # bottom
        draw_SVG_line(g_bottom, bottom_origin + V(depth), bottom_origin + V(depth) + H(width))
        draw_tabbed_edge(g_bottom, bottom_origin, V(d_tab_size), H(thickness), d_tab_count, False)
        draw_tabbed_edge(g_bottom, bottom_origin + H(width) , V(d_tab_size), H(-thickness), d_tab_count, False)
        draw_tabbed_edge(g_bottom, bottom_origin, h_tab, V(thickness), h_tab_count, True)



# Create effect instance and apply it.
effect = Shelves()
effect.affect()