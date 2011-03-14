from igraph import *

class GraphSen(Graph):
    def __init__(self, *args, **kwds):
        Graph.__init__(self, *args, **kwds)
    def __plot__(self, context, bbox, palette, *args, **kwds):
        import igraph.colors
        import cairo

        directed = self.is_directed()
        margin = kwds.get("margin", [0., 0., 0., 0.])
        try:
            margin = list(margin)
        except TypeError:
            margin = [margin]
        while len(margin)<4: margin.extend(margin)
        margin = tuple(map(float, margin[:4]))

        vertex_colors = drawing.collect_attributes(self.vcount(), "vertex_color", \
            "color", kwds, self.vs, config, "blue", palette.get)
        vertex_stroke_colors = drawing.collect_attributes(self.vcount(), "vertex_stroke_color", \
            "stroke_color", kwds, self.vs, config, "black", palette.get)
        vertex_sizes = drawing.collect_attributes(self.vcount(), "vertex_size", \
            "size", kwds, self.vs, config, 10, float)
        vertex_shapes = [drawing.known_shapes.get(x, drawing.NullDrawer) \
            for x in drawing.collect_attributes(self.vcount(), "vertex_shape", \
            "shape", kwds, self.vs, config, "circle")]

        #layer is a variable which is basically -- do we want to have a layer?
        #   True allows us to layer
        #   Define colors2 and sizes2
        vertex_layer = drawing.collect_attributes(self.vcount(), "vertex_layer", \
            "layer", kwds, self.vs, config, False, bool)
        vertex_colors2 = drawing.collect_attributes(self.vcount(), "vertex_color2", \
            "color2", kwds, self.vs, config, "pink", palette.get)
        vertex_sizes2 = drawing.collect_attributes(self.vcount(), "vertex_size2", \
            "size2", kwds, self.vs, config, 10, float)


        max_vertex_size = max(vertex_sizes)

        layout = kwds.get("layout", None)
        if isinstance(layout, Layout):
            layout = Layout(layout.coords)
        elif isinstance(layout, str) or layout is None:
            layout = self.layout(layout)
        else:
            layout = Layout(layout)

        sl, st, sr, sb = layout.bounding_box()
        sw, sh = sr-sl, sb-st
        if sw == 0 and sh == 0: sw, sh = 1, 1
        if sw == 0: sw = sh
        if sh == 0: sh = sw
        rx, ry = float(bbox.width-max_vertex_size-margin[1]-margin[3])/sw, \
          float(bbox.height-max_vertex_size-margin[0]-margin[2])/sh
        layout.scale(rx, ry)
        layout.translate(-sl*rx+max_vertex_size/2.+margin[1]+bbox.coords[0], \
          -st*ry+max_vertex_size/2.+margin[0]+bbox.coords[1])
        context.set_line_width(1)

        edge_colors = drawing.collect_attributes(self.ecount(), "edge_color", \
            "color", kwds, self.es, config, "gray", palette.get)
        edge_widths = drawing.collect_attributes(self.ecount(), "edge_width", \
            "width", kwds, self.es, config, 1, float)
        edge_arrow_sizes = drawing.collect_attributes(self.ecount(), \
            "edge_arrow_size", "arrow_size", kwds, self.es, config, 1, float)
        edge_arrow_widths = drawing.collect_attributes(self.ecount(), \
            "edge_arrow_width", "arrow_width", kwds, self.es, config, 1, float)

        # Draw the edges
        for idx, e in enumerate(self.es):
            context.set_source_rgb(*edge_colors[idx])
            context.set_line_width(edge_widths[idx])

            src, tgt = e.tuple
            if src == tgt:
                # Loop edge
                r = vertex_sizes[src]*2
                cx, cy = layout[src][0]+math.cos(math.pi/4)*r/2, \
                  layout[src][1]-math.sin(math.pi/4)*r/2
                context.arc(cx, cy, r/2., 0, math.pi*2)
            else:
                # Determine where the edge intersects the circumference of the
                # vertex shape. TODO: theoretically this need not to be done
                # if there are no arrowheads on the edge, but maybe it's not worth
                # testing for
                p1 = vertex_shapes[src].intersection_point( \
                    layout[src][0], layout[src][1], layout[tgt][0], layout[tgt][1],
                    vertex_sizes[src])
                p2 = vertex_shapes[tgt].intersection_point( \
                    layout[tgt][0], layout[tgt][1], layout[src][0], layout[src][1],
                    vertex_sizes[tgt])
                context.move_to(*p1)
                context.line_to(*p2)
            context.stroke()

            if directed and src != tgt:
                # Draw an arrowhead
                angle = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
                arrow_size = 15.*edge_arrow_sizes[idx]
                arrow_width = 10./edge_arrow_widths[idx]
                a1 = (p2[0]-arrow_size*math.cos(angle-math.pi/arrow_width),
                  p2[1]-arrow_size*math.sin(angle-math.pi/arrow_width))
                a2 = (p2[0]-arrow_size*math.cos(angle+math.pi/arrow_width),
                  p2[1]-arrow_size*math.sin(angle+math.pi/arrow_width))
                context.move_to(*p2)
                context.line_to(*a1)
                context.line_to(*a2)
                context.line_to(*p2)
                context.fill()

        del edge_colors
        del edge_widths

##        vertex_layer = drawing.collect_attributes(self.vcount(), "vertex_layer", \
##            "layer", kwds, self.vs, config, False, bool)
##        vertex_colors2 = drawing.collect_attributes(self.vcount(), "vertex_color2", \
##            "color2", kwds, self.vs, config, "black", palette.get)
##        vertex_sizes2 = drawing.collect_attributes(self.vcount(), "vertex_size2", \
##            "size2", kwds, self.vs, config, 15, float)



        # Draw the vertices
        context.set_line_width(1)
        for idx, v in enumerate(self.vs):

            if (vertex_layer[idx]):
                if (vertex_sizes2[idx] >= vertex_sizes[idx]):
                    vertex_shapes[idx].draw_path(context, layout[idx][0], layout[idx][1], vertex_sizes2[idx])
                    context.set_source_rgb(*vertex_colors2[idx])
                    context.fill_preserve()
                    context.set_source_rgb(*vertex_stroke_colors[idx])
                    context.stroke()
                    
                    vertex_shapes[idx].draw_path(context, layout[idx][0], layout[idx][1], vertex_sizes[idx])
                    context.set_source_rgb(*vertex_colors[idx])
                    context.fill_preserve()
                    context.stroke()
                else:
                    vertex_shapes[idx].draw_path(context, layout[idx][0], layout[idx][1], vertex_sizes[idx])
                    context.set_source_rgb(*vertex_colors[idx])
                    context.fill_preserve()
                    context.set_source_rgb(*vertex_stroke_colors[idx])
                    context.stroke()
                    
                    vertex_shapes[idx].draw_path(context, layout[idx][0], layout[idx][1], vertex_sizes2[idx])
                    context.set_source_rgb(*vertex_colors2[idx])
                    context.fill_preserve()
                    context.stroke()
            else:
                vertex_shapes[idx].draw_path(context, layout[idx][0], layout[idx][1], vertex_sizes[idx])
                context.set_source_rgb(*vertex_colors[idx])
                context.fill_preserve()                
                context.set_source_rgb(*vertex_stroke_colors[idx])
                context.stroke()
                
        #RL ADD
        del vertex_stroke_colors
        del vertex_colors
        del vertex_shapes
        del vertex_layer
        del vertex_colors2
        del vertex_sizes2

        # Draw the vertex labels
        if not kwds.has_key("vertex_label") and "label" not in self.vs.attribute_names():
            vertex_labels = map(str, xrange(self.vcount()))
        elif kwds.has_key("vertex_label") and kwds["vertex_label"] is None:
            vertex_labels = [""] * self.vcount()
        else:
            vertex_labels = drawing.collect_attributes(self.vcount(), "vertex_label", \
                "label", kwds, self.vs, config, None)
        vertex_dists = drawing.collect_attributes(self.vcount(), "vertex_label_dist", \
            "label_dist", kwds, self.vs, config, 1, float)
        vertex_degrees = drawing.collect_attributes(self.vcount(), \
            "vertex_label_angle", "label_angle", kwds, self.vs, config, \
            -math.pi/4, float)
        vertex_label_colors = drawing.collect_attributes(self.vcount(), \
            "vertex_label_color", "label_color", kwds, self.vs, config, \
            "black", palette.get)
        vertex_label_sizes = drawing.collect_attributes(self.vcount(), \
            "vertex_label_size", "label_size", kwds, self.vs, \
            config, 14, float)

        context.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, \
            cairo.FONT_WEIGHT_BOLD)
        
        for idx, v in enumerate(self.vs):
            xb, yb, w, h = context.text_extents(vertex_labels[idx])[:4]
            cx, cy = layout[idx]
            cx += math.cos(vertex_degrees[idx]) * vertex_dists[idx] * vertex_sizes[idx]
            cy += math.sin(vertex_degrees[idx]) * vertex_dists[idx] * vertex_sizes[idx]
            cx -= w/2. + xb
            cy -= h/2. + yb
            context.move_to(cx, cy)
            #RL ADD
            context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            context.set_font_size(vertex_label_sizes[idx])
            context.set_source_rgb(*vertex_label_colors[idx])
            context.text_path(vertex_labels[idx])
            context.fill()
