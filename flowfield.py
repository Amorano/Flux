
import dearpygui.dearpygui as dpg
from opensimplex import random_seed, noise3array
from particle import Particle
import numpy as np
from PIL import Image
from util import timeit

random_seed()

TAU = np.pi * 2

_scale = 45
_cols = 10
_rows = 10
particles_total = 2000
x_coords, y_coords = np.meshgrid(np.linspace(0, 1, _cols), np.linspace(0, 1, _rows))

_width = _cols * _scale
_height = _rows * _scale
_x = np.arange(_cols)/_cols
_y = np.arange(_rows)/_rows

_bg_color = [0,0,0,255]
dpg.create_context()
dpg.create_viewport(title='Custom Title', width=_width, height=_height, resizable=False)
dpg.setup_dearpygui()

def recalc_particles(vector_field: list, vector_field_z: float, zt: float) -> tuple[list, float]:
    if z - vector_field_z >= 0.01:
        vector_field = _flowfield(zt)
        vector_field_z = zt

    force = [(np.cos(vector_field[int(particle.pos[1] // _scale)][int((particle.pos[0] // _scale) % _cols)]),
            np.sin(vector_field[int(particle.pos[1] // _scale)][int((particle.pos[0] // _scale) % _cols)]))
            for particle in particles]

    for idx, particle in enumerate(particles):
        particle.apply_force(force[idx])
        particle.update()
        particle.warp_around_edges(_width, _height)
    return vector_field, vector_field_z

z = 0
flowfield = []
flowfield_z = -1

def _handle_frame_buffer(sender, buffer) -> None:
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
                #with open("alex.txt", "w", encoding="utf-8") as f:
                #    f.write(buffer)

                #img = Image.fromarray(buffer)
                # img.save()

            global flowfield, flowfield_z, z
            flowfield, flowfield_z = recalc_particles(flowfield, flowfield_z, z)
            z += np.random.random() * 0.02

            # Run the next update as soon as we can - something needs an extra frame
            # to render correctly; might be the texture.  That's why we skip a frame.
            dpg.set_frame_callback(dpg.get_frame_count()+2, callback=lambda: dpg.output_frame_buffer(callback=_handle_frame_buffer))

# @timeit
def _flowfield(z) -> list:
    global _x, _y
    return noise3array(_x, _y, np.array([z]))[0] * TAU

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
dpg.set_viewport_vsync(False)
#dpg.show_metrics()
dpg.set_frame_callback(5, callback=lambda: dpg.output_frame_buffer(callback=_handle_frame_buffer))
dpg.start_dearpygui()
dpg.destroy_context()