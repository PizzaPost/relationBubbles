try:
    import os
    import math
    import queue
    import threading
    import time
    import tkinter
    import sys
    import urllib.request
except ImportError as e:
    print(f"Error: '{e.name}' not found. Please install it using 'pip install {e.name}'.")
    exit()

necessarry_files = ["batter_saving_icon.png", "bubble.png", "bubble_icon.png", "color_palette.png", "color_wheel.png",
                    "target.png"]
custom_modules=["color_picker", "nav_bar"]
trying=True
while trying:
    try:
        import customtkinter
        import mss
        import pyautogui
        import pygame
        from PIL import Image

        import color_picker
        import nav_bar
        trying=False
    except ImportError as e:
        if not e.name=="tkinter":
            tkinter.messagebox.showinfo("Missing Module", f"Downloading '{e.name}'")
        if not e.name in custom_modules:
            os.system(f"pip install {e.name}")
        else:
            link=f"https://raw.githubusercontent.com/PizzaPost/relationBubbles/master/{e.name}.py"
            urllib.request.urlretrieve(link, f"{e.name}.py")
for file in necessarry_files:
    if not os.path.exists(file):
        tkinter.messagebox.showinfo("Missing File", f"Downloading '{file}'")
        link=f"https://raw.githubusercontent.com/PizzaPost/relationBubbles/master/{file}"
        urllib.request.urlretrieve(link, file)

try:
    bubble_img_original = pygame.image.load("bubble.png")
    batter_saving_icon = pygame.image.load("batter_saving_icon.png")
    half_batter_saving_icon_width = batter_saving_icon.get_width() // 2
    half_batter_saving_icon_height = batter_saving_icon.get_height() // 2
    bubble_icon = pygame.image.load("bubble_icon.png")
except pygame.error:
    print("Warning: 'bubble.png' not found. Using a fallback shape.")
    bubble_img_original = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.rect(bubble_img_original, (255, 255, 255), (0, 0, 100, 100), border_radius=35)

pygame.init()
running = True
tk = None
screen_width = pygame.display.Info().current_w
screen_height = pygame.display.Info().current_h
width = 0
height = 0
tk_queue = queue.Queue()
bubble_queue = queue.Queue()

rmin = 12
rmax = 100
rdef = 24


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


def close_create_menu(save, entry=None, x=width // 2, y=height // 2, color_picker=None, radius_slider=None,
                      alignment_options=None):
    global tk
    if save:
        bubble_data = (entry.get("1.0", "end"), x, y, hex_to_rgb(color_picker.cget("fg_color")), radius_slider.get(),
                       alignment_options.get())
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
    tk.geometry(f"410x350+{screen_width // 2 - 164}+{screen_height // 2 - 150}")
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
    radius_slider = customtkinter.CTkSlider(frame, from_=rmin, to=rmax, number_of_steps=30)
    radius_slider.set(rdef)
    alignment_options = nav_bar.create_animated_pill_navigation(frame, labels=["left", "center", "right"],
                                                                initial_index=1,
                                                                grid={
                                                                    'row': 4,
                                                                    'column': 0,
                                                                    'columnspan': 2,
                                                                    'sticky': "ew",
                                                                    'padx': 8,
                                                                    'pady': 6
                                                                })
    submit_btn = customtkinter.CTkButton(frame, text="submit",
                                         command=lambda: close_create_menu(True, entry, world_x, world_y, color_picker,
                                                                           radius_slider, alignment_options))
    entry.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(6, 8))
    color_picker.grid(row=2, column=0, sticky="e", padx=4, pady=6)
    color_palette.grid(row=2, column=1, sticky="w", pady=6)
    radius_slider.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=6)
    submit_btn.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
    close_btn.grid(row=0, column=1, sticky="ne", padx=6, pady=6)
    tk.protocol("WM_DELETE_WINDOW", close_create_menu)
    tk.mainloop()


def create_bubble(data):
    text = data[0]
    x = data[1]
    y = data[2]
    if not text.replace("\n", "") == "":
        color = data[3]
        radius = data[4]
        alignment = data[5]
        text = text[:-1]
        texts = text.split("\n")
        bubbles.append({
            "name": texts,
            "x": x,
            "y": y,
            "color": color,
            "radius": radius,
            "fm": 1.0,
            "connections": [],
            "rendered_lines": [],
            "text_alignment": alignment
        })


tk_thread = threading.Thread(target=tkinter_thread, daemon=True)
tk_thread.start()


def wrap_lines(bubble):
    original_lines = bubble.get("name", [])
    wrapped_lines = []
    for line in original_lines:
        split_next = False
        for index, letter in enumerate(line):
            if index > 40:
                split_next = True
            if split_next:
                if letter == " ":
                    line = line[:index] + "\n" + line[index:]
                    split_next = False
        wrapped_lines.append(line)
    bubble["rendered_lines"] = [line for line in wrapped_lines if line]


def close_edit_menu(save, bubble, entry, color_picker, radius_slider, alignment_options):
    global tk
    if save:
        text = entry.get("1.0", "end")[:-1]
        texts = text.split("\n")
        bubble["name"] = texts
        bubble["color"] = hex_to_rgb(color_picker.cget("fg_color"))
        bubble["radius"] = radius_slider.get()
        bubble["text_alignment"] = alignment_options.get()
        wrap_lines(bubble)
    tk.destroy()
    tk = None


def create_edit_menu(bubble):
    global tk
    if tk:
        return
    tk = customtkinter.CTk()
    customtkinter.set_default_color_theme("green")
    tk.title("edit bubble")
    tk.geometry(f"410x350+{screen_width // 2 - 164}+{screen_height // 2 - 150}")
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
    radius_slider = customtkinter.CTkSlider(frame, from_=rmin, to=rmax, number_of_steps=30)
    radius_slider.set(bubble["radius"])
    for index, option in enumerate(["left", "center", "right"]):
        if option == bubble["text_alignment"]:
            alignment_options = nav_bar.create_animated_pill_navigation(frame, labels=["left", "center", "right"],
                                                                        initial_index=index,
                                                                        grid={
                                                                            'row': 4,
                                                                            'column': 0,
                                                                            'columnspan': 2,
                                                                            'sticky': "ew",
                                                                            'padx': 8,
                                                                            'pady': 6
                                                                        })
    submit_btn = customtkinter.CTkButton(frame, text="submit",
                                         command=lambda: close_edit_menu(True, bubble, entry, color_picker,
                                                                         radius_slider, alignment_options))
    entry.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(6, 8))
    color_picker.grid(row=2, column=0, sticky="e", padx=4, pady=6)
    color_palette.grid(row=2, column=1, sticky="w", pady=6)
    radius_slider.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=6)
    submit_btn.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
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


def handle_mouse_button_one_down():
    global click_start, moved, dragging_bubble, offset_x, offset_y, dragging_map, last_mouse_pos
    click_start = event.pos
    moved = False
    clicked_on_bubble = False
    for bubble in bubbles:
        distance = math.sqrt((bubble["x"] - world_mx) ** 2 + (bubble["y"] - world_my) ** 2)
        if distance < bubble["radius"]:
            dragging_bubble = bubble
            offset_x = bubble["x"] - world_mx
            offset_y = bubble["y"] - world_my
            clicked_on_bubble = True
            break
    if not clicked_on_bubble:
        dragging_map = True
        last_mouse_pos = event.pos


def handle_mouse_button_three_down():
    global world_mx, world_my
    on_rect = False
    for bubble in bubbles:
        distance = math.sqrt((bubble["x"] - world_mx) ** 2 + (bubble["y"] - world_my) ** 2)
        if distance < bubble["radius"]:
            tk_queue.put(("ce", bubble))
            on_rect = True
            break
    if not on_rect:
        tk_queue.put("cc")


def handle_mouse_button_one_up():
    global connecting_bubble
    mx, my = event.pos
    world_mx = (mx - map_offset_x) / zoom_level
    world_my = (my - map_offset_y) / zoom_level
    clicked_bubble = None
    for bubble in bubbles:
        distance = math.sqrt((bubble["x"] - world_mx) ** 2 + (bubble["y"] - world_my) ** 2)
        if distance < bubble["radius"]:
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


def handle_mouse_motion():
    global batter_saving_cooldown, dragging_bubble, map_offset_x, map_offset_y, dragging_map, last_mouse_pos, click_start, moved
    batter_saving_cooldown = 0
    mx, my = event.pos
    if dragging_bubble:
        world_mx = (mx - map_offset_x) / zoom_level
        world_my = (my - map_offset_y) / zoom_level
        dragging_bubble["x"] = world_mx + offset_x
        dragging_bubble["y"] = world_my + offset_y
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


def draw_connection_line_between_bubble_and_mouse(connecting_bubble):
    radius = connecting_bubble["radius"]
    start_center_screen = (connecting_bubble["x"] * zoom_level + map_offset_x,
                           connecting_bubble["y"] * zoom_level + map_offset_y)
    end_pos = pygame.mouse.get_pos()
    dx = end_pos[0] - start_center_screen[0]
    dy = end_pos[1] - start_center_screen[1]
    if dx != 0 or dy != 0:
        start_w_half = radius * zoom_level / 2
        start_h_half = radius * zoom_level / 2
        t_x = start_w_half / abs(dx) if dx != 0 else float("inf")
        t_y = start_h_half / abs(dy) if dy != 0 else float("inf")
        t = min(t_x, t_y)
        if t < 1.0:
            start_point = (start_center_screen[0] + t * dx, start_center_screen[1] + t * dy)
            pygame.draw.aaline(pg, (200, 200, 200), start_point, end_pos, 2)


def draw_connection_line_between_bubbles():
    for bubble in bubbles:
        for connected_bubble in bubble["connections"]:
            b1r = bubble["radius"]
            b2r = connected_bubble["radius"]
            p1_center_world = (bubble["x"], bubble["y"])
            p2_center_world = (connected_bubble["x"], connected_bubble["y"])
            dx = p2_center_world[0] - p1_center_world[0]
            dy = p2_center_world[1] - p1_center_world[1]
            if dx == 0 and dy == 0:
                continue
            length = math.hypot(dx, dy)
            t1 = b2r / length
            t2 = b1r / length
            start_point = (p1_center_world[0] + t2 * dx, p1_center_world[1] + t2 * dy)
            end_point = (p2_center_world[0] - t1 * dx, p2_center_world[1] - t1 * dy)
            start_screen = (start_point[0] * zoom_level + map_offset_x,
                            start_point[1] * zoom_level + map_offset_y)
            end_screen = (end_point[0] * zoom_level + map_offset_x,
                          end_point[1] * zoom_level + map_offset_y)
            pygame.draw.aaline(pg, (100, 100, 100), start_screen, end_screen, 2)
            force = 0.001
            bubble["x"] += force * dx
            bubble["y"] += force * dy
            connected_bubble["x"] -= force * dx
            connected_bubble["y"] -= force * dy


def handle_bubble_collisions():
    for i in range(len(bubbles)):
        for j in range(i + 1, len(bubbles)):
            bubble1 = bubbles[i]
            bubble2 = bubbles[j]
            if bubble1 is dragging_bubble or bubble2 is dragging_bubble:
                continue
            dx = bubble2["x"] - bubble1["x"]
            dy = bubble2["y"] - bubble1["y"]
            distance = math.hypot(dx, dy)
            bubble1_bbox_radius = bubble1["radius"]
            bubble2_radius = bubble2["radius"]
            min_distance = (bubble1_bbox_radius + bubble2_radius) * min_distance_multiplier
            if 0 < distance < min_distance:
                overlap = min_distance - distance
                nx = dx / distance
                ny = dy / distance
                push_strength = overlap / 2 * easing_factor
                bubble1["x"] -= nx * push_strength
                bubble1["y"] -= ny * push_strength
                bubble2["x"] += nx * push_strength
                bubble2["y"] += ny * push_strength


def render_bubble_text(bubble, bubble_width_screen, text_color, text_block_start_y_screen, line_height_scaled):
    if bubble.get("text_alignment") == "left":
        bubble_center_x_screen = bubble["x"] * zoom_level + map_offset_x
        text_x_pos = bubble_center_x_screen - ((bubble_width_screen / 2) + 10) / 2
    elif bubble.get("text_alignment") == "right":
        bubble_center_x_screen = bubble["x"] * zoom_level + map_offset_x
        text_x_pos = bubble_center_x_screen + ((bubble_width_screen / 2) - 10) / 2
    else:
        text_x_pos = bubble["x"] * zoom_level + map_offset_x
    maxLineWidth = 0
    for index, text in enumerate(bubble["rendered_lines"]):
        text_to_render = text if text.strip() else "‎ "
        rendered = bubble_font.render(text_to_render, True, text_color)
        text_rect = rendered.get_rect()
        if bubble.get("text_alignment") == "left":
            text_rect.left = text_x_pos
        elif bubble.get("text_alignment") == "right":
            text_rect.right = text_x_pos
        else:
            text_rect.centerx = text_x_pos
        maxLineWidth = max(maxLineWidth, text_rect.width)
        text_rect.top = text_block_start_y_screen + (index * line_height_scaled)
        pg.blit(rendered, text_rect)
    return maxLineWidth


def font_scaling(bubble, maxLineWidth):
    maxDiameter = bubble["radius"] * math.sqrt(2) * zoom_level
    minDiameter = bubble["radius"] * zoom_level
    if max(maxLineWidth, line_height * len(bubble["rendered_lines"])) > maxDiameter:
        bubble["fm"] *= 0.99
    elif max(maxLineWidth, line_height * len(bubble["rendered_lines"])) < minDiameter:
        bubble["fm"] *= 1.01


def calc_font_and_line_height(bubble, rdef, zoom_level):
    radius = bubble["radius"]
    font_size_unscaled = max(1, int(24 * radius / rdef * bubble["fm"]))
    font_size_scaled = max(1, int(font_size_unscaled * zoom_level))
    bubble_font = pygame.font.SysFont(None, font_size_scaled)
    line_height_scaled = int(font_size_scaled * 0.8)
    return bubble_font, line_height_scaled


def calc_bubble_screen_rect(bubble, zoom_level, map_offset_x, map_offset_y):
    r = bubble["radius"]
    w = r * zoom_level * 2
    h = r * zoom_level * 2
    x = (bubble["x"] - r) * zoom_level + map_offset_x
    y = (bubble["y"] - r) * zoom_level + map_offset_y
    return x, y, w, h


def is_bubble_offscreen(x, y, w, h, screen_width, screen_height):
    return w < 1 or h < 1 or \
        x > screen_width or y > screen_height or \
        x + w < 0 or y + h < 0


def render_bubble_image(surface, bubble_img_original, x, y, w, h, bubble_color):
    scaled_bubble = pygame.transform.scale(bubble_img_original, (int(w), int(h)))
    tinted_bubble = scaled_bubble.copy()
    tint_surface = pygame.Surface(scaled_bubble.get_size(), pygame.SRCALPHA)
    bubble_bg_color = get_contrasting_bubble_color(bubble_color)
    tint_surface.fill((*bubble_bg_color, 220))
    tinted_bubble.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(tinted_bubble, (x, y))


def calc_bubble_text_layout(bubble, zoom_level, map_offset_y, line_height_scaled):
    total_text_height = len(bubble["rendered_lines"]) * line_height_scaled
    center_y = bubble["y"] * zoom_level + map_offset_y
    text_block_start_y = center_y - (total_text_height / 2)
    return text_block_start_y, total_text_height


def draw_bubbles():
    global bubble_font
    draw_connection_line_between_bubbles()
    handle_bubble_collisions()
    for bubble in bubbles:
        if not bubble.get("rendered_lines"):
            wrap_lines(bubble)
            if not bubble.get("rendered_lines"):
                continue
        bubble_font, line_height_scaled = calc_font_and_line_height(bubble, rdef, zoom_level)
        x, y, w, h = calc_bubble_screen_rect(bubble, zoom_level, map_offset_x, map_offset_y)
        if is_bubble_offscreen(x, y, w, h, width, height):
            continue
        render_bubble_image(pg, bubble_img_original, x, y, w, h, bubble["color"])
        bubble_radius = bubble["radius"]
        bubble_width_screen = bubble_radius * zoom_level * 2
        text_color = bubble["color"]
        text_block_start_y_screen, total_text_height = calc_bubble_text_layout(bubble, zoom_level, map_offset_y,
                                                                               line_height_scaled)
        maxLineWidth = render_bubble_text(bubble, bubble_width_screen, text_color, text_block_start_y_screen, line_height_scaled)
        font_scaling(bubble, maxLineWidth)


pg = pygame.display.set_mode((screen_width // 1.5, screen_height // 1.5 * 1.2), pygame.RESIZABLE)
pygame.display.set_caption("Bubble Net")
bubbles = []
bubble_font = pygame.font.SysFont(None, 24)
basicFont = pygame.font.SysFont(None, 24)
welcomeText = basicFont.render("Nothing here yet. Start to spread your creativity!", True, (255, 255, 255))
halfWelcomeTextWidth = welcomeText.get_width() // 2
halfWelcomeTextHeight = welcomeText.get_height() // 2
batterSavingText = basicFont.render("Interact to stop the battery saving mode.", True, (255, 255, 255))
halfbatterSavingTextWidth = batterSavingText.get_width() // 2
halfbatterSavingTextHeight = batterSavingText.get_height() // 2
line_height = 20
dragging_bubble = None
offset_x = 0
offset_y = 0
map_offset_x = 0
map_offset_y = 0
dragging_map = False
last_mouse_pos = (0, 0)
easing_factor = 0.1
min_distance_multiplier = 1.1
click_start = None
moved = False
connecting_bubble = None
zoom_level = 1
min_zoom = 0.3
max_zoom = 3
zoom_speed = 0.1
zoom = 0
batter_saving_cooldown = 0
clock = pygame.time.Clock()
while running:
    pg.fill((0, 0, 0))
    events = pygame.event.get()
    if batter_saving_cooldown > 2000:
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        if events:
            batter_saving_cooldown = 0
        pg.blit(batter_saving_icon, (width // 2 - half_batter_saving_icon_width,
                                     height // 2 - half_batter_saving_icon_height - half_batter_saving_icon_height * 2))
        pg.blit(batterSavingText, (width // 2 - halfbatterSavingTextWidth, height // 2 - halfbatterSavingTextHeight))
        pygame.display.set_icon(batter_saving_icon)
    else:
        width = pg.get_width()
        height = pg.get_height()
        pygame.display.set_icon(bubble_icon)
        try:
            bubble_data = bubble_queue.get(block=False)
            create_bubble(bubble_data)
        except queue.Empty:
            pass
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                batter_saving_cooldown = 0
                if event.key == pygame.K_SPACE:
                    tk_queue.put("cc")
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_CTRL and event.key == pygame.K_s:
                    print(bubbles)
                elif mods and pygame.KMOD_CTRL and event.key == pygame.K_o:
                    bubbles = list(input("Send your code here: "))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                batter_saving_cooldown = 0
                mx, my = event.pos
                world_mx = (mx - map_offset_x) / zoom_level
                world_my = (my - map_offset_y) / zoom_level
                if event.button == 1:
                    handle_mouse_button_one_down()
                elif event.button == 3:
                    handle_mouse_button_three_down()
            elif event.type == pygame.MOUSEBUTTONUP:
                batter_saving_cooldown = 0
                dragging_bubble = None
                click_start = None
                dragging_map = False
                if event.button == 1 and not moved:
                    handle_mouse_button_one_up()
            elif event.type == pygame.MOUSEMOTION:
                handle_mouse_motion()
            elif event.type == pygame.MOUSEWHEEL:
                batter_saving_cooldown = 0
                handle_zoom(event)
        if not events:
            batter_saving_cooldown += 1
        for event in pygame.event.get(pump=False):
            if event.type == pygame.MOUSEWHEEL:
                handle_zoom(event)
        if connecting_bubble:
            draw_connection_line_between_bubble_and_mouse(connecting_bubble)
        if len(bubbles) > 0:
            draw_bubbles()
        elif tk_queue.empty() and tk is None:
            pg.blit(welcomeText, (width // 2 - halfWelcomeTextWidth, height // 2 - halfWelcomeTextHeight))
        zoom_text = basicFont.render(f"Zoom: {zoom_level:.2f}x", True, (200, 200, 200))
        pg.blit(zoom_text, (10, 10))
    pygame.display.update()
    clock.tick(120)
pygame.quit()
