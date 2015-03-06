#!/usr/bin/env python

#import Inkscape_helper.inkscape_helper as helper
import Inkscape_helper.inkscape_helper as doc

#import simplestyle


#Note: keep in mind that SVG coordinates start in the top-left corner i.e. with an inverted y-axis


class Shelves(doc.Effect):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        doc.Effect.__init__(self)

        self.OptionParser.add_option('--unit', action = 'store',
          type = 'string', dest = 'unit', default = 'cm',
          help = 'Unit, should be one of ')

        self.OptionParser.add_option('--tool_diameter', action = 'store',
          type = 'float', dest = 'tool_diameter', default = '0.3',
          help = 'Tool diameter')

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

    def effect(self):
        """
        Draws a shelved cupboard, based on provided parameters
        """

        # input sanity check and unit conversion
        error = False

        if self.options.unit not in self.knownUnits:
            doc.errormsg('Error: unknown unit. '+ self.options.unit)
            error = True
        unit = self.options.unit

        if min(self.options.height, self.options.width, self.options.depth) == 0:
            doc.errormsg('Error: Dimensions must be non zero')
            error = True

        shelves = []

        for s in self.options.shelve_list.split(';'):
            try:
                shelves.append(self.unittouu(str(s).strip() + unit))
            except ValueError:
                doc.errormsg('Error: nonnumeric value in shelves (' + s + ')')
                error = True

        if error:
            exit()

        height = self.unittouu(str(self.options.height) + unit)
        width = self.unittouu(str(self.options.width) + unit)
        depth = self.unittouu(str(self.options.depth) + unit)
        thickness = self.unittouu(str(self.options.thickness) + unit)
        groove_depth = self.unittouu(str(self.options.groove_depth) + unit)
        tab_size = self.unittouu(str(self.options.tab_size) + unit)
        tolerance = self.unittouu(str(self.options.tolerance) + unit)
        tool_diameter = self.unittouu(str(self.options.tool_diameter) + unit)

        doc_root = self.document.getroot()
        docWidth = self.unittouu(doc_root.get('width'))
        docHeigh = self.unittouu(doc_root.attrib['height'])

        layer = doc.layer(doc_root, 'Shelves')

        def H(x):
            return doc.Coordinate(x, 0)

        def V(x):
            return doc.Coordinate(0, x)

        def tab_count(dist, desired_tab_size):
            F = int(dist // desired_tab_size)
            if F / 2 % 2 == 0:  # make sure we have an odd number of tabs
                n = F // 2
            else:
                n = (F - 1) // 2

            return 2 * n + 1

        # create groups for the different parts
        g_l_side = doc.group(layer)
        g_r_side = doc.group(layer)
        g_top = doc.group(layer)
        g_bottom = doc.group(layer)
        g_back = doc.group(layer)
        g_divider = doc.group(layer)

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
            start = edge_start + (inset if invert else doc.Coordinate(0, 0))
            for i in range(count):
                if (i % 2 == 0) != invert:
                    t_offset = inset
                else:
                    t_offset = doc.Coordinate(0, 0)
                end = start + tab
                #inkex.debug(str((i, start, end, t_offset)))
                doc.draw_line(parent, start, end)
                if i < count - 1:   # skip last one
                    start = edge_start + t_offset + tab * (i + 1)
                    doc.draw_line(parent, end, start)

        # top
        doc.draw_line(g_top, top_origin, top_origin + H(width))
        draw_tabbed_edge(g_top, top_origin, V(d_tab_size), H(thickness), d_tab_count, False)
        draw_tabbed_edge(g_top, top_origin + H(width) , V(d_tab_size), H(-thickness), d_tab_count, False)
        draw_tabbed_edge(g_top, top_origin + V(depth), h_tab, V(-thickness), h_tab_count, True)
        # groove
        groove_style = doc.groove_style
        center_v_groove_l = (width - thickness) / 2 - tolerance
        groove_l_side = top_origin + H(center_v_groove_l)
        groove_r_side = groove_l_side + H(thickness + tolerance * 2)
        doc.draw_line(g_top, groove_l_side, groove_l_side + V(depth), groove_style)
        doc.draw_line(g_top, groove_r_side, groove_r_side + V(depth), groove_style)


        # left
        doc.draw_line(g_l_side, left_side_origin, left_side_origin + V(height))
        draw_tabbed_edge(g_l_side, left_side_origin + H(depth), v_tab, H(-thickness), v_tab_count, True)
        draw_tabbed_edge(g_l_side, left_side_origin, H(d_tab_size), V(thickness), d_tab_count, True)
        draw_tabbed_edge(g_l_side, left_side_origin + V(height), H(d_tab_size), V(-thickness), d_tab_count, True)

        # back
        draw_tabbed_edge(g_back, back_origin, v_tab, H(thickness), v_tab_count, False)
        draw_tabbed_edge(g_back, back_origin + H(width), v_tab, H(-thickness), v_tab_count, False)
        draw_tabbed_edge(g_back, back_origin, h_tab, V(thickness), h_tab_count, False)
        draw_tabbed_edge(g_back, back_origin + V(height), h_tab, V(-thickness), h_tab_count, False)
        # groove
        groove_l_side = back_origin + H(center_v_groove_l)
        groove_r_side = groove_l_side + H(thickness + tolerance * 2)
        doc.draw_line(g_back, groove_l_side, groove_l_side + V(height), groove_style)
        doc.draw_line(g_back, groove_r_side, groove_r_side + V(height), groove_style)

        # right
        doc.draw_line(g_r_side, right_side_origin + H(depth), right_side_origin + H(depth) + V(height))
        draw_tabbed_edge(g_r_side, right_side_origin, v_tab, H(thickness), v_tab_count, True)
        draw_tabbed_edge(g_r_side, right_side_origin, H(d_tab_size), V(thickness), d_tab_count, True)
        draw_tabbed_edge(g_r_side, right_side_origin + V(height), H(d_tab_size), V(-thickness), d_tab_count, True)

        # bottom
        doc.draw_line(g_bottom, bottom_origin + V(depth), bottom_origin + V(depth) + H(width))
        draw_tabbed_edge(g_bottom, bottom_origin, V(d_tab_size), H(thickness), d_tab_count, False)
        draw_tabbed_edge(g_bottom, bottom_origin + H(width) , V(d_tab_size), H(-thickness), d_tab_count, False)
        draw_tabbed_edge(g_bottom, bottom_origin, h_tab, V(thickness), h_tab_count, True)
        # groove
        groove_l_side = bottom_origin + H(center_v_groove_l)
        groove_r_side = groove_l_side + H(thickness + tolerance * 2)
        doc.draw_line(g_bottom, groove_l_side, groove_l_side + V(depth), groove_style)
        doc.draw_line(g_bottom, groove_r_side, groove_r_side + V(depth), groove_style)

        #shelves
        prev_top = 0
        gr_short = thickness - groove_depth + tool_diameter / 2     # avoid that the grooves are visible from the outside
        for s in shelves:
            s_top = prev_top + thickness + s - tolerance
            s_bottom = s_top + thickness + tolerance * 2

            doc.draw_line(g_l_side, left_side_origin + V(s_top), left_side_origin + V(s_top) + H(depth - gr_short), groove_style)
            doc.draw_line(g_l_side, left_side_origin + V(s_bottom), left_side_origin + V(s_bottom) + H(depth - gr_short), groove_style)

            doc.draw_line(g_r_side, right_side_origin + V(s_top) + H(gr_short), right_side_origin + V(s_top) + H(depth), groove_style)
            doc.draw_line(g_r_side, right_side_origin + V(s_bottom) + H(gr_short), right_side_origin + V(s_bottom) + H(depth), groove_style)

            doc.draw_line(g_back, back_origin + V(s_top) + H(gr_short), back_origin + V(s_top) + H(width - gr_short), groove_style)
            doc.draw_line(g_back, back_origin + V(s_bottom)  + H(gr_short), back_origin + V(s_bottom) + H(width - gr_short), groove_style)

            prev_top = s_top

# Create effect instance and apply it.
effect = Shelves()
effect.affect()
