import math
import queue
import threading
import time

import customtkinter
import mss
import pyautogui
import pygame
from PIL import Image

import color_picker

pygame.init()
running = True
tk = None
screen_width = pygame.display.Info().current_w
screen_height = pygame.display.Info().current_h
width = 0
height = 0
tk_queue = queue.Queue()
bubble_queue = queue.Queue()


def tkinter_thread():
    global tk_queue, bubble_queue

    customtkinter.set_default_color_theme("green")

    while running:
        try:
            command = tk_queue.get(block=False)
            if isinstance(command, tuple):
                cmd_name, cmd_arg = command
                if cmd_name == "ce":
                    create_edit_menu(cmd_arg)
            elif command == "cc":
                create_create_window()
        except queue.Empty:
            pass
        time.sleep(0.05)


def ask_color(button, color1, color2, color3):
    pick_color = color_picker.AskColor(button=button, button_color=color1, button_hover_color=color2,
                                       button_hover_color2=color3)
    color = pick_color.get()
    if not color: return
    base_rgb = hex_to_rgb(color)
    hover_rgb = get_hover_color(base_rgb)
    hover_hex = rgb_to_hex(hover_rgb)
    button.configure(fg_color=color, hover_color=hover_hex)


def adjust_color(rgb, factor=1.2):
    return tuple(
        max(0, min(255, int(c * factor)))
        for c in rgb
    )


def get_hover_color(rgb):
    lighter = adjust_color(rgb, 1.2)
    if sum(lighter) > 700:
        return adjust_color(rgb, 0.8)
    return lighter


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def get_contrasting_bubble_color(text_color):
    r, g, b = text_color
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return (40, 40, 40) if brightness > 128 else (240, 240, 240)


def get_color_at_mouse(event, color_picker):
    with mss.mss() as sct:
        x, y = pyautogui.position()
        monitor = {"top": y, "left": x, "width": 1, "height": 1}
        img = sct.grab(monitor)
        rgb_color = img.pixel(0, 0)
    hex_color = rgb_to_hex(rgb_color)
    hover_rgb = get_hover_color(hex_to_rgb(hex_color))
    hover_hex = rgb_to_hex(hover_rgb)
    color_picker.configure(fg_color=hex_color, hover_color=hover_hex)


def close_create_menu(save, entry=None, x=width // 2, y=height // 2, color_picker=None, zoom_slider=None):
    global tk
    if save:
        bubble_data = (entry.get("1.0", "end"), x, y, hex_to_rgb(color_picker.cget("fg_color")), zoom_slider.get())
        bubble_queue.put(bubble_data)
    tk.destroy()
    tk = None


def create_create_window():
    global tk
    if tk:
        return
    x, y = pygame.mouse.get_pos()
    world_x = (x - map_offset_x) / zoom_level
    world_y = (y - map_offset_y) / zoom_level
    tk = customtkinter.CTk()
    customtkinter.set_default_color_theme("green")
    tk.title("add new bubble")
    tk.geometry(f"410x300+{screen_width // 2 - 164}+{screen_height // 2 - 150}")
    tk.resizable(False, False)
    tk.attributes("-alpha", 0.85)
    tk.overrideredirect(True)
    tk.attributes("-topmost", True)
    frame = customtkinter.CTkFrame(tk)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(1, weight=1)
    frame.pack(fill="both", expand=True)
    close_btn = customtkinter.CTkButton(frame, text="x", text_color="red", fg_color="transparent", hover_color="gray25",
                                        width=25, height=25, command=lambda: close_create_menu(False))
    entry = customtkinter.CTkTextbox(frame, height=170, width=300)
    tk.focus_force()
    entry.focus_force()
    hex_color, hover_rgb, hover_hex = "#ffffff", (204, 204, 204), "#cccccc"
    hover2_hex = rgb_to_hex(get_hover_color(hover_rgb))
    color_picker = customtkinter.CTkButton(frame, text="", hover_color=hover_hex, fg_color=hex_color, width=127,
                                           height=28,
                                           command=lambda: ask_color(color_picker, hex_color, hover_hex, hover2_hex))
    palette_img = Image.open("color_palette.png")
    palette_img = palette_img.convert("RGBA")
    image = customtkinter.CTkImage(light_image=palette_img,
                                   dark_image=palette_img,
                                   size=(127, 28))
    color_palette = customtkinter.CTkLabel(frame, text="", image=image, width=127, height=28)
    color_palette.bind("<Button-1>", lambda event: get_color_at_mouse(event, color_picker))
    zoom_slider = customtkinter.CTkSlider(frame, from_=-5, to=10, number_of_steps=30)
    zoom_slider.set(0)
    submit_btn = customtkinter.CTkButton(frame, text="submit",
                                         command=lambda: close_create_menu(True, entry, world_x, world_y, color_picker,
                                                                           zoom_slider))
    entry.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(6, 8))
    color_picker.grid(row=2, column=0, sticky="e", padx=4, pady=6)
    color_palette.grid(row=2, column=1, sticky="w", pady=6)
    zoom_slider.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=6)
    submit_btn.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
    close_btn.grid(row=0, column=1, sticky="ne", padx=6, pady=6)
    tk.protocol("WM_DELETE_WINDOW", close_create_menu)
    tk.mainloop()


def create_bubble(data):
    text = data[0]
    x = data[1]
    y = data[2]
    if not text.replace("\n", "") == "":
        color = data[3]
        zoom = data[4]
        text = text[:-1]
        texts = text.split("\n")
        bubbles.append({
            "name": texts,
            "x": x,
            "y": y,
            "color": color,
            "zoom": zoom,
            "rect": None,
            "connections": [],
            "rendered_lines": []
        })
        bubbles[-1]["rect"] = calc_bubble_rect(bubbles[-1], "rect")[0]


tk_thread = threading.Thread(target=tkinter_thread, daemon=True)
tk_thread.start()


def calc_bubble_rect(bubble, *args):
    to_return = []
    zoom_factor = 1.0 + (bubble["zoom"] * 0.1)
    font_size = int(24 * zoom_factor)
    bubble_font = pygame.font.SysFont(None, font_size)
    max_text_width_world = 350 * (1.0 + (bubble["zoom"] * 0.15))
    original_lines = bubble.get("name", [])
    wrapped_lines = []
    for line in original_lines:
        words = line.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if bubble_font.size(test_line)[0] < max_text_width_world:
                current_line = test_line
            else:
                wrapped_lines.append(current_line.strip())
                current_line = word + " "
        wrapped_lines.append(current_line.strip())
    bubble["rendered_lines"] = [line for line in wrapped_lines if line]
    lines = bubble["rendered_lines"] or [" "]
    line_height = int(font_size * 0.8)
    max_text_width = max(bubble_font.size(line)[0] for line in lines)
    total_text_height = len(lines) * line_height
    padding_x = font_size * 1.2
    padding_y = font_size * 0.8
    bubble_width = max_text_width + padding_x
    bubble_height = total_text_height + padding_y
    side_length = max(bubble_width, bubble_height)
    rect = pygame.Rect(bubble["x"] - side_length / 2, bubble["y"] - side_length / 2, side_length, side_length)
    if "maxw" in args:
        to_return.append(side_length)
    if "h" in args:
        to_return.append(side_length)
    if "rect" in args:
        to_return.append(rect)
    return to_return


def close_edit_menu(save, bubble, entry, color_picker, zoom_slider):
    global tk
    if save:
        text = entry.get("1.0", "end")[:-1]
        texts = text.split("\n")
        bubble["name"] = texts
        bubble["color"] = hex_to_rgb(color_picker.cget("fg_color"))
        bubble["zoom"] = zoom_slider.get()
        bubble["rect"] = calc_bubble_rect(bubble, "rect")[0]
    tk.destroy()
    tk = None


def create_edit_menu(bubble):
    global tk
    if tk:
        return
    tk = customtkinter.CTk()
    customtkinter.set_default_color_theme("green")
    tk.title("edit bubble")
    tk.geometry(f"410x300+{screen_width // 2 - 164}+{screen_height // 2 - 150}")
    tk.resizable(False, False)
    tk.attributes("-alpha", 0.85)
    tk.overrideredirect(True)
    tk.attributes("-topmost", True)
    frame = customtkinter.CTkFrame(tk)
    frame.pack(fill="both", expand=True)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(1, weight=1)
    close_btn = customtkinter.CTkButton(frame, text="x", text_color="red", fg_color="transparent", hover_color="gray25",
                                        width=25, height=25, command=lambda: close_create_menu(False))
    entry = customtkinter.CTkTextbox(frame, height=170, width=300)
    entry.insert("1.0", "\n".join(bubble["name"]))
    tk.focus_force()
    entry.focus_force()
    base_rgb = bubble["color"]
    hex_color = rgb_to_hex(base_rgb)
    hover_rgb = get_hover_color(base_rgb)
    hover_hex = rgb_to_hex(hover_rgb)
    hover2_hex = rgb_to_hex(get_hover_color(hover_rgb))
    color_picker = customtkinter.CTkButton(frame, text="", fg_color=hex_color, hover_color=hover_hex, width=127,
                                           height=28,
                                           command=lambda: ask_color(color_picker, hex_color, hover_hex, hover2_hex))
    palette_img = Image.open("color_palette.png")
    palette_img = palette_img.convert("RGBA")
    image = customtkinter.CTkImage(light_image=palette_img,
                                   dark_image=palette_img,
                                   size=(127, 28))
    color_palette = customtkinter.CTkLabel(frame, text="", image=image, width=127, height=28)
    color_palette.bind("<Button-1>", lambda event: get_color_at_mouse(event, color_picker))
    zoom_slider = customtkinter.CTkSlider(frame, from_=-5, to=10, number_of_steps=30)
    zoom_slider.set(bubble["zoom"])
    submit_btn = customtkinter.CTkButton(frame, text="submit",
                                         command=lambda: close_edit_menu(True, bubble, entry, color_picker,
                                                                         zoom_slider))

    entry.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(6, 8))
    color_picker.grid(row=2, column=0, sticky="e", padx=4, pady=6)
    color_palette.grid(row=2, column=1, sticky="w", pady=6)
    zoom_slider.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=6)
    submit_btn.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
    close_btn.grid(row=0, column=1, sticky="ne", padx=6, pady=6)

    tk.protocol("WM_DELETE_WINDOW", close_edit_menu)
    tk.mainloop()


def handle_zoom(event):
    global zoom_level, map_offset_x, map_offset_y
    if event.type == pygame.MOUSEWHEEL:
        mx, my = pygame.mouse.get_pos()
        world_mx_before = (mx - map_offset_x) / zoom_level
        world_my_before = (my - map_offset_y) / zoom_level
        if event.y > 0:
            zoom_level = min(max_zoom, zoom_level * (1 + zoom_speed))
        elif event.y < 0:
            zoom_level = max(min_zoom, zoom_level * (1 - zoom_speed))
        world_mx_after = (mx - map_offset_x) / zoom_level
        world_my_after = (my - map_offset_y) / zoom_level
        map_offset_x += (world_mx_after - world_mx_before) * zoom_level
        map_offset_y += (world_my_after - world_my_before) * zoom_level
        return True
    return False


pg = pygame.display.set_mode((screen_width // 1.5, screen_height // 1.5 * 1.2), pygame.RESIZABLE)
pygame.display.set_caption("Bubble Net")
bubbles = []
welcomeFont = pygame.font.SysFont(None, 24)
welcomeText = welcomeFont.render("Nothing here yet. Start to spread your creativity!", True, (255, 255, 255))
halfWelcomeTextWidth = welcomeText.get_width() // 2
halfWelcomeTextHeight = welcomeText.get_height() // 2
bubble_font = pygame.font.SysFont(None, 24)
line_height = 20
dragging = None
offset_x = 0
offset_y = 0
map_offset_x = 0
map_offset_y = 0
dragging_map = False
last_mouse_pos = (0, 0)
easing_factor = 0.1
min_distance_multiplier = 0.9
click_start = None
moved = False
connecting_bubble = None
zoom_level = 1
min_zoom = 0.3
max_zoom = 3
zoom_speed = 0.1
zoom = 0
try:
    bubble_img_original = pygame.image.load("bubble.png")
except pygame.error:
    print("Warning: 'bubble.png' not found. Using a fallback shape.")
    bubble_img_original = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.rect(bubble_img_original, (255, 255, 255), (0, 0, 100, 100), border_radius=35)
clock = pygame.time.Clock()
while running:
    pg.fill((0, 0, 0))
    width = pg.get_width()
    height = pg.get_height()
    try:
        bubble_data = bubble_queue.get(block=False)
        create_bubble(bubble_data)
    except queue.Empty:
        pass
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                tk_queue.put("cc")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            world_mx = (mx - map_offset_x) / zoom_level
            world_my = (my - map_offset_y) / zoom_level
            if event.button == 1:
                click_start = event.pos
                moved = False
                clicked_on_bubble = False
                for bubble in bubbles:
                    rect = calc_bubble_rect(bubble, "rect")[0]
                    if rect.collidepoint(world_mx, world_my):
                        dragging = bubble
                        offset_x = bubble["x"] - world_mx
                        offset_y = bubble["y"] - world_my
                        clicked_on_bubble = True
                        break
                if not clicked_on_bubble:
                    dragging_map = True
                    last_mouse_pos = event.pos
            elif event.button == 3:
                on_rect = False
                for bubble in bubbles:
                    rect = calc_bubble_rect(bubble, "rect")[0]
                    if rect.collidepoint(world_mx, world_my):
                        tk_queue.put(("ce", bubble))
                        on_rect = True
                        break
                if not on_rect:
                    tk_queue.put("cc")
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = None
            click_start = None
            dragging_map = False
            if event.button == 1 and not moved:
                mx, my = event.pos
                world_mx = (mx - map_offset_x) / zoom_level
                world_my = (my - map_offset_y) / zoom_level
                clicked_bubble = None
                for bubble in bubbles:
                    rect = calc_bubble_rect(bubble, "rect")[0]
                    if bubble["rect"].collidepoint(mx, my):
                        clicked_bubble = bubble
                        break
                if connecting_bubble is None:
                    if clicked_bubble:
                        connecting_bubble = clicked_bubble
                else:
                    if clicked_bubble and clicked_bubble is not connecting_bubble:
                        if clicked_bubble not in connecting_bubble["connections"]:
                            connecting_bubble["connections"].append(clicked_bubble)
                    connecting_bubble = None
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if dragging:
                world_mx = (mx - map_offset_x) / zoom_level
                world_my = (my - map_offset_y) / zoom_level
                dragging["x"] = world_mx + offset_x
                dragging["y"] = world_my + offset_y
                dragging["rect"] = calc_bubble_rect(dragging, "rect")[0]
            elif dragging_map:
                last_mx, last_my = last_mouse_pos
                dx = mx - last_mx
                dy = my - last_my
                map_offset_x += dx
                map_offset_y += dy
                last_mouse_pos = event.pos
            if click_start:
                if math.hypot(event.pos[0] - click_start[0], event.pos[1] - click_start[1]) > 5:
                    moved = True
        elif event.type == pygame.MOUSEWHEEL:
            handle_zoom(event)
    for event in pygame.event.get(pump=False):
        if event.type == pygame.MOUSEWHEEL:
            handle_zoom(event)
    if connecting_bubble:
        rect = calc_bubble_rect(connecting_bubble, "rect")[0]
        start_center_world = rect.center
        start_center_screen = (start_center_world[0] * zoom_level + map_offset_x,
                               start_center_world[1] * zoom_level + map_offset_y)
        end_pos = pygame.mouse.get_pos()
        dx = end_pos[0] - start_center_screen[0]
        dy = end_pos[1] - start_center_screen[1]
        if dx != 0 or dy != 0:
            start_w_half = rect.width * zoom_level / 2
            start_h_half = rect.height * zoom_level / 2
            t_x = start_w_half / abs(dx) if dx != 0 else float("inf")
            t_y = start_h_half / abs(dy) if dy != 0 else float("inf")
            t = min(t_x, t_y)
            if t < 1.0:
                start_point = (start_center_screen[0] + t * dx, start_center_screen[1] + t * dy)
                pygame.draw.aaline(pg, (200, 200, 200), start_point, end_pos, 2)
    if len(bubbles) > 0:
        for bubble in bubbles:
            for connected_bubble in bubble["connections"]:
                b1_rect = calc_bubble_rect(bubble, "rect")[0]
                b2_rect = calc_bubble_rect(connected_bubble, "rect")[0]
                p1_center_world = b1_rect.center
                p2_center_world = b2_rect.center
                dx = p2_center_world[0] - p1_center_world[0]
                dy = p2_center_world[1] - p1_center_world[1]
                if dx == 0 and dy == 0:
                    continue
                t1x = (b1_rect.width / 2) / abs(dx) if dx != 0 else float("inf")
                t1y = (b1_rect.height / 2) / abs(dy) if dy != 0 else float("inf")
                t1 = min(t1x, t1y)
                t2x = (b2_rect.width / 2) / abs(dx) if dx != 0 else float("inf")
                t2y = (b2_rect.height / 2) / abs(dy) if dy != 0 else float("inf")
                t2 = min(t2x, t2y)
                if t1 + t2 < 1.0:
                    start_point = (p1_center_world[0] + t1 * dx, p1_center_world[1] + t1 * dy)
                    end_point = (p2_center_world[0] - t2 * dx, p2_center_world[1] - t2 * dy)
                    start_screen = (start_point[0] * zoom_level + map_offset_x,
                                    start_point[1] * zoom_level + map_offset_y)
                    end_screen = (end_point[0] * zoom_level + map_offset_x,
                                  end_point[1] * zoom_level + map_offset_y)
                    pygame.draw.aaline(pg, (100, 100, 100), start_screen, end_screen, 2)
        for i in range(len(bubbles)):
            for j in range(i + 1, len(bubbles)):
                bubble1 = bubbles[i]
                bubble2 = bubbles[j]
                if bubble1 is dragging or bubble2 is dragging:
                    continue
                dx = bubble2["x"] - bubble1["x"]
                dy = bubble2["y"] - bubble1["y"]
                distance = math.hypot(dx, dy)
                bubble1_bbox_width = bubble1["rect"].width
                bubble2_bbox_width = bubble2["rect"].width
                min_distance = (bubble1_bbox_width / 2 + bubble1_bbox_width / 2) * min_distance_multiplier
                if 0 < distance < min_distance:
                    nx = dx / distance
                    ny = dy / distance
                    overlap = min_distance - distance
                    push_strength = math.sqrt(overlap) * easing_factor
                    bubble1["x"] -= nx * push_strength
                    bubble1["y"] -= ny * push_strength
                    bubble2["x"] += nx * push_strength
                    bubble2["y"] += ny * push_strength
                    bubble1["rect"] = calc_bubble_rect(bubble1, "rect")[0]
                    bubble2["rect"] = calc_bubble_rect(bubble2, "rect")[0]
        for bubble in bubbles:
            zoom_factor = 1.0 + (bubble["zoom"] * 0.1)
            font_size_unscaled = int(24 * zoom_factor)
            font_size_scaled = int(font_size_unscaled * zoom_level)
            if font_size_scaled < 1:
                continue
            bubble_font = pygame.font.SysFont(None, font_size_scaled)
            line_height_scaled = int(font_size_scaled * 0.8)
            bubble_rect_world = bubble["rect"]
            bubble_width_screen = bubble_rect_world.width * zoom_level
            bubble_height_screen = bubble_rect_world.height * zoom_level
            bubble_x_screen = bubble_rect_world.x * zoom_level + map_offset_x
            bubble_y_screen = bubble_rect_world.y * zoom_level + map_offset_y
            if bubble_width_screen < 1 or bubble_height_screen < 1 or \
                    bubble_x_screen > width or bubble_y_screen > height or \
                    bubble_x_screen + bubble_width_screen < 0 or \
                    bubble_y_screen + bubble_height_screen < 0:
                continue
            scaled_bubble = pygame.transform.scale(bubble_img_original,
                                                   (int(bubble_width_screen), int(bubble_height_screen)))
            tinted_bubble = scaled_bubble.copy()
            tint_surface = pygame.Surface(scaled_bubble.get_size(), pygame.SRCALPHA)
            bubble_bg_color = get_contrasting_bubble_color(bubble["color"])
            tint_surface.fill((*bubble_bg_color, 220))
            tinted_bubble.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            pg.blit(tinted_bubble, (bubble_x_screen, bubble_y_screen))
            text_color = bubble["color"]
            total_text_height_screen = len(bubble["rendered_lines"]) * line_height_scaled
            bubble_center_y_screen = bubble["y"] * zoom_level + map_offset_y
            text_block_start_y_screen = bubble_center_y_screen - (total_text_height_screen / 2)
            for index, text in enumerate(bubble["rendered_lines"]):
                rendered = bubble_font.render(text, True, text_color)
                text_rect = rendered.get_rect()
                text_rect.centerx = bubble["x"] * zoom_level + map_offset_x
                text_rect.top = text_block_start_y_screen + (index * line_height_scaled)
                pg.blit(rendered, text_rect)
    elif tk_queue.empty() and tk == None:
        pg.blit(welcomeText, (width // 2 - halfWelcomeTextWidth, height // 2 - halfWelcomeTextHeight))
    pygame.display.update()
    clock.tick(120)
pygame.quit()
