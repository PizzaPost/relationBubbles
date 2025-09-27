import math
import time

import customtkinter as ct


class AnimatedPillNavigation:
    def __init__(self, parent, labels, initial_index=0, config=None):
        """
        Animated Pill Navigation Widget

        Args:
            parent: The parent widget
            labels: List of button labels (e.g., ["Home", "New", "Profile"])
            initial_index: Starting selected index (default: 0)
            config: Optional configuration dictionary to customize appearance
        """
        self.parent = parent
        self.labels = labels
        self.current_selection_idx = initial_index
        self.animation_start_time = 0
        self.start_bubble_x = 0
        self.target_bubble_x = 0
        self.config = {
            "active_bg_color": "#ff6b77",
            "inactive_bg_color": "#111216",
            "text_active": "white",
            "text_inactive": "#bfc3c8",
            "pill_width": 360,
            "pill_height": 48,
            "pill_corner_radius": 24,
            "bubble_corner_radius": 22,
            "button_visual_width": 80,
            "button_height": 34,
            "text_padding": 10,
            "font": ct.CTkFont(size=12, weight="bold"),
            "slide_duration_ms": 300,
            "fps": 120,
        }
        if config:
            self.config.update(config)

        self.button_count = len(labels)
        self.button_slot_width = self.config["pill_width"] / self.button_count
        self.button_y_pos = (self.config["pill_height"] - self.config["button_height"]) / 2
        self.delay_ms = 1000 // self.config["fps"]

        self.create_widgets()
        self.set_initial_state(initial_index)

    def create_widgets(self):
        """Create all the UI elements"""
        self.pill = ct.CTkFrame(
            self.parent,
            corner_radius=self.config["pill_corner_radius"],
            fg_color=self.config["inactive_bg_color"],
            height=self.config["pill_height"],
            width=self.config["pill_width"]
        )
        self.pill.place(relx=0.5, rely=0.5, anchor="center")
        self.pill.pack_propagate(False)

        for i, label_text in enumerate(self.labels):
            label = ct.CTkLabel(
                master=self.pill,
                text=label_text,
                width=self.config["button_visual_width"],
                height=self.config["button_height"],
                fg_color="transparent",
                text_color=self.config["text_inactive"],
                cursor="hand2",
                font=self.config["font"]
            )
            label.bind("<Button-1>", lambda event, i=i: self.select_tab(i))
            label.place(x=self.calculate_center_x(i), y=self.button_y_pos)

        self.bubble = ct.CTkFrame(
            master=self.pill,
            fg_color=self.config["active_bg_color"],
            corner_radius=self.config["bubble_corner_radius"],
            width=self.config["button_visual_width"],
            height=self.config["button_height"]
        )

        self.text_container = ct.CTkFrame(
            master=self.bubble,
            fg_color="transparent",
            width=self.config["pill_width"],
            height=self.config["button_height"]
        )
        self.text_container.place(x=0, y=0)

        for i, label_text in enumerate(self.labels):
            label = ct.CTkLabel(
                master=self.text_container,
                text=label_text,
                width=self.config["button_visual_width"] - (self.config["text_padding"] * 2),
                height=self.config["button_height"],
                fg_color="transparent",
                text_color=self.config["text_active"],
                font=self.config["font"]
            )
            label.place(x=self.calculate_center_x(i) + self.config["text_padding"], y=0)

    def calculate_center_x(self, index):
        """Calculate x position for button at given index"""
        return (index * self.button_slot_width) + (self.button_slot_width / 2) - (
                self.config["button_visual_width"] / 2)

    def ease_in_out_sine(self, t):
        """Easing function for smooth animation"""
        return -(math.cos(math.pi * t) - 1) / 2

    def animate_slide(self):
        """Animate the bubble sliding to new position"""
        elapsed = time.time() * 1000 - self.animation_start_time
        t = min(1.0, elapsed / self.config["slide_duration_ms"])
        eased_t = self.ease_in_out_sine(t)
        new_x = self.start_bubble_x + (self.target_bubble_x - self.start_bubble_x) * eased_t
        self.bubble.place(x=new_x, y=self.button_y_pos)
        self.text_container.place(x=-new_x, y=0)
        if t < 1.0:
            self.parent.after(self.delay_ms, self.animate_slide)
        else:
            self.bubble.place(x=self.target_bubble_x, y=self.button_y_pos)
            self.text_container.place(x=-self.target_bubble_x, y=0)

    def select_tab(self, idx):
        """Select a tab with animation"""
        if idx == self.current_selection_idx:
            return
        self.target_bubble_x = self.calculate_center_x(idx)
        self.start_bubble_x = self.calculate_center_x(self.current_selection_idx)
        self.animation_start_time = time.time() * 1000
        self.current_selection_idx = idx
        self.animate_slide()
        if hasattr(self, 'on_tab_selected'):
            self.on_tab_selected(idx)

    def set_initial_state(self, idx):
        """Set initial selected tab without animation"""
        self.current_selection_idx = idx
        initial_x = self.calculate_center_x(idx)
        self.bubble.place(x=initial_x, y=self.button_y_pos)
        self.text_container.place(x=-initial_x, y=0)

    def get_current_selection(self):
        """Get currently selected tab index"""
        return self.current_selection_idx

    def get(self):
        """Get currently selected tab label"""
        return self.labels[self.current_selection_idx]

    def set_callback(self, callback_function):
        """Set a callback function to be called when tab is selected"""
        self.on_tab_selected = callback_function

    def pack(self, **kwargs):
        """Pack the widget with custom parameters"""
        self.pill.pack(**kwargs)

    def place(self, **kwargs):
        """Place the widget with custom parameters"""
        self.pill.place(**kwargs)

    def grid(self, **kwargs):
        """Grid the widget with custom parameters"""
        self.pill.grid(**kwargs)


def create_animated_pill_navigation(parent, labels, initial_index=0, config=None, **placement_kwargs):
    """
    Function to create and place an animated pill navigation

    Args:
        parent: Parent widget
        labels: List of button labels
        initial_index: Starting selected index
        config: Custom configuration dictionary
        **placement_kwargs: Placement arguments (pack, place, or grid)

    Returns:
        AnimatedPillNavigation instance
    """
    nav = AnimatedPillNavigation(parent, labels, initial_index, config)
    if placement_kwargs:
        if 'pack' in placement_kwargs:
            nav.pack(**placement_kwargs['pack'])
        elif 'place' in placement_kwargs:
            nav.place(**placement_kwargs['place'])
        elif 'grid' in placement_kwargs:
            nav.grid(**placement_kwargs['grid'])
    return nav


if __name__ == "__main__":
    ct.set_appearance_mode("dark")
    ct.set_default_color_theme("dark-blue")
    root = ct.CTk()
    root.title("Animated Pill Navigation - Scaled")
    root.geometry("520x220")

    labels = ["Home", "Discover", "Library", "Settings"]

    small_config = {
        "pill_width": 360,
        "pill_height": 48,
        "pill_corner_radius": 24,
        "bubble_corner_radius": 16,
        "button_visual_width": 80,
        "button_height": 34,
        "font": ct.CTkFont(size=12, weight="bold"),
    }

    nav = create_animated_pill_navigation(
        root,
        labels,
        initial_index=2,
        placement_kwargs={'pack': {'pady': 5}}
    )

    def on_tab_selected(index):
        print(f"Tab selected: {index} - {labels[index]}")

    nav.set_callback(on_tab_selected)
    root.mainloop()