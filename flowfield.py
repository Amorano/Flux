import dearpygui.dearpygui as dpg
from opensimplex import random_seed, noise3, noise3array
from particle import Particle
import numpy as np
from util import timeit

random_seed()

_scale = 40
_cols = 20
_rows = 20
particles_total = 2500
x_coords, y_coords = np.meshgrid(np.linspace(0, 1, _cols), np.linspace(0, 1, _rows))

_width = _cols * _scale
_height = _rows * _scale
_bg_color = [0,0,0,255]
dpg.create_context()
dpg.create_viewport(title='Custom Title', width=_width, height=_height, resizable=False)
dpg.setup_dearpygui()

def recalc_particles(flowfield, flowfield_z, z):
    if z - flowfield_z >= 0.01:
        flowfield = _flowfield(_cols, _rows, z)
        flowfield_z = z

    for particle in particles:
        x = (particle.pos[0] // _scale) % _cols
        y = particle.pos[1] // _scale
        if x < 0 or x >= _cols or y < 0 or y >= _rows:
            continue
        idx = int(x + y * _cols)
        force = flowfield[idx]
        particle.apply_force(force)
        particle.update()
        particle.warp_around_edges(_width, _height)
    return flowfield, flowfield_z

z = 0
inc = 0.01
flowfield = []
flowfield_z = -1

def _handle_frame_buffer(sender, buffer):
    with dpg.mutex():
        if dpg.does_item_exist("flowfield"):
            if dpg.does_item_exist('prev_frame'):
                dpg.set_value('prev_frame', buffer)
            else:
                with dpg.texture_registry():
                    width = dpg.get_viewport_client_width()
                    height = dpg.get_viewport_client_height()
                    dpg.add_raw_texture(width=width, height=height, default_value=buffer, format=dpg.mvFormat_Float_rgba, tag="prev_frame")
                dpg.add_image('prev_frame', parent='flowfield', pos=(0,0))
                # Adding a dimmer - once and for good
                _background(opacity=10)

            # We've stored current picture into the background texture and
            # are now ready to move particles around.
            global flowfield, flowfield_z, z, inc
            flowfield, flowfield_z = recalc_particles(flowfield, flowfield_z, z)
            z += inc
            # Run the next update as soon as we can - something needs an extra frame
            # to render correctly; might be the texture.  That's why we skip a frame.
            dpg.set_frame_callback(dpg.get_frame_count()+2, callback=lambda: dpg.output_frame_buffer(callback=_handle_frame_buffer))

TAU = np.pi * 2

@timeit
# original -- more or less
def _flowfield(cols, rows, z) -> list:
    flowfield = []
    # x_coords, y_coords = np.meshgrid(np.linspace(0, 1, cols), np.linspace(0, 1, rows))
    for y in range(rows):
        for x in range(cols):
            r = noise3(x_coords[x, y], y_coords[x, y], z)
            angle = r * TAU
            flowfield.append((np.cos(angle), np.sin(angle)))
    return flowfield

def _background(clr=_bg_color[:3], opacity=255):
    x, y = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    clr.append(opacity)
    background = dpg.draw_rectangle(pmin=(0,0), pmax=(x, y), parent='flowfield', fill=clr, color=clr)
    return background

with dpg.window(label="FlowField", tag='flowfield', width=_width, height=_height):
    dpg.set_primary_window('flowfield', True)

    with dpg.theme() as flowfield_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _bg_color, category=dpg.mvThemeCat_Core)
    dpg.bind_item_theme('flowfield', flowfield_theme)

    particles = []
    for _ in range(particles_total):
        pos = [np.random.random() * _width, np.random.random() * _height]
        vel = [np.random.random(), np.random.random()]
        p = Particle('flowfield', pos, vel)
        particles.append(p)

dpg.show_viewport()
dpg.set_frame_callback(5, callback=lambda: dpg.output_frame_buffer(callback=_handle_frame_buffer))
dpg.start_dearpygui()
#dpg.show_metrics()
#dpg.set_viewport_vsync(False)
dpg.destroy_context()