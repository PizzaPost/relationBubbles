# THIS IS A MODIFIED VERSION OF CTkColorPicker
# https://github.com/Akascape/CTkColorPicker
# Original Author: Akash Bora (Akascape)


import math
import os
import tkinter
from typing import Optional, Tuple

import customtkinter
from PIL import Image, ImageTk

PATH = os.path.dirname(os.path.realpath(__file__))


class AskColor(customtkinter.CTkToplevel):
    """A color picker dialog for customtkinter applications."""

    def __init__(
            self,
            button_color: str,
            button_hover_color: str,
            button_hover_color2: str,
            width: int = 300,
            title: str = "Choose Color",
            initial_color: Optional[str] = None,
            bg_color: Optional[str] = None,
            fg_color: Optional[str] = None,
            corner_radius: int = 24,
            slider_border: int = 1,
            **button_kwargs
    ):
        super().__init__()

        # Initialize configuration
        self._setup_config(width, title, bg_color)

        # Initialize color variables
        self.default_rgb = [255, 255, 255]
        self.rgb_color = self.default_rgb.copy()
        self._color = None

        # Initialize theme colors
        self._init_colors(button_color, button_hover_color, button_hover_color2,
                          fg_color, corner_radius, slider_border)

        # Create UI
        self._create_widgets()

        # Set initial color if provided
        if initial_color:
            self.set_initial_color(initial_color)

        # Final setup
        self.after(150, lambda: self.button.focus())
        self.grab_set()

    def _setup_config(self, width: int, title: str, bg_color: Optional[str]) -> None:
        """Configure window properties."""
        self.title(title)
        width = max(width, 200)  # Ensure minimum width
        height = width + 95

        self.image_dimension = self._apply_window_scaling(width - 100)
        self.target_dimension = self._apply_window_scaling(20)

        self.maxsize(width, height)
        self.minsize(width, height)
        self.resizable(False, False)
        self.transient(self.master)
        self.lift()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Set background color
        bg = bg_color or self._apply_appearance_mode(
            customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        self.configure(bg=bg)

    def _init_colors(
            self,
            button_color: str,
            button_hover_color: str,
            button_hover_color2: str,
            fg_color: Optional[str],
            corner_radius: int,
            slider_border: int
    ) -> None:
        """Initialize color settings."""
        self.button_color = button_color
        self.button_hover_color = button_hover_color
        self.button_hover_color2 = button_hover_color2
        self.corner_radius = corner_radius
        self.slider_border = min(10, max(1, slider_border))  # Clamp between 1 and 10

        self.bg_color = self.cget("bg")
        self.fg_color = fg_color or self._apply_appearance_mode(
            customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"]
        )

    def _create_widgets(self) -> None:
        """Create and arrange all UI widgets."""
        # Main frame
        self.frame = customtkinter.CTkFrame(
            master=self,
            fg_color=self.fg_color,
            bg_color=self.bg_color
        )
        self.frame.grid(padx=20, pady=20, sticky="nswe")

        # Color wheel canvas
        self._create_color_wheel()

        # Brightness slider
        self._create_brightness_slider()

        # OK button
        self._create_ok_button()

    def _create_color_wheel(self) -> None:
        """Create the color wheel canvas."""
        self.canvas = tkinter.Canvas(
            self.frame,
            height=self.image_dimension,
            width=self.image_dimension,
            highlightthickness=0,
            bg=self.fg_color
        )
        self.canvas.pack(pady=20)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        # Load images
        self.img1 = Image.open(os.path.join(PATH, 'color_wheel.png')).resize(
            (self.image_dimension, self.image_dimension),
            Image.Resampling.LANCZOS
        )
        self.img2 = Image.open(os.path.join(PATH, 'target.png')).resize(
            (self.target_dimension, self.target_dimension),
            Image.Resampling.LANCZOS
        )

        self.wheel = ImageTk.PhotoImage(self.img1)
        self.target = ImageTk.PhotoImage(self.img2)

        self.canvas.create_image(self.image_dimension / 2, self.image_dimension / 2, image=self.wheel)
        self.target_x, self.target_y = self.image_dimension / 2, self.image_dimension / 2
        self.canvas.create_image(self.target_x, self.target_y, image=self.target)

    def _create_brightness_slider(self) -> None:
        """Create the brightness slider."""
        self.brightness_slider_value = customtkinter.IntVar(value=255)

        self.slider = customtkinter.CTkSlider(
            master=self.frame,
            height=20,
            border_width=self.slider_border,
            button_length=15,
            progress_color=self.button_color,
            from_=0,
            to=255,
            variable=self.brightness_slider_value,
            number_of_steps=256,
            button_corner_radius=self.corner_radius,
            corner_radius=self.corner_radius,
            button_color=self.button_hover_color,
            button_hover_color=self.button_hover_color2,
            command=self.update_colors
        )
        self.slider.pack(fill="both", pady=(0, 15), padx=20 - self.slider_border)

    def _create_ok_button(self) -> None:
        """Create the OK button."""
        self.button = customtkinter.CTkButton(
            master=self.frame,
            text="OK",
            height=50,
            corner_radius=self.corner_radius,
            text_color="black",
            fg_color=self.button_color,
            hover_color=self.button_hover_color,
            command=self._ok_event
        )
        self.button.pack(fill="both", padx=10, pady=20)

    @staticmethod
    def adjust_color(rgb: Tuple[int, int, int], factor: float = 1.2) -> Tuple[int, int, int]:
        """Adjust color brightness by a factor."""
        return tuple(max(0, min(255, int(c * factor))) for c in rgb)

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color string."""
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def get_hover_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Calculate hover color based on RGB values."""
        lighter = self.adjust_color(rgb, 1.2)
        return self.adjust_color(rgb, 0.8) if sum(lighter) > 700 else lighter

    def get(self) -> Optional[str]:
        """Show the dialog and return the selected color."""
        self.master.wait_window(self)
        return self._color

    def _ok_event(self, event=None) -> None:
        """Handle OK button click."""
        self._color = self.button._fg_color
        self.grab_release()
        self.destroy()
        self._cleanup_resources()

    def _on_closing(self) -> None:
        """Handle window closing."""
        self._color = None
        self.grab_release()
        self.destroy()
        self._cleanup_resources()

    def _cleanup_resources(self) -> None:
        """Clean up image resources."""
        if hasattr(self, 'img1'):
            del self.img1
        if hasattr(self, 'img2'):
            del self.img2
        if hasattr(self, 'wheel'):
            del self.wheel
        if hasattr(self, 'target'):
            del self.target

    def on_mouse_drag(self, event) -> None:
        """Handle mouse drag on color wheel."""
        x, y = event.x, event.y
        self.canvas.delete("all")
        self.canvas.create_image(self.image_dimension / 2, self.image_dimension / 2, image=self.wheel)

        center_x, center_y = self.image_dimension / 2, self.image_dimension / 2
        radius = self.image_dimension / 2
        d_from_center = math.sqrt((center_x - x) ** 2 + (center_y - y) ** 2)

        if d_from_center < radius:
            self.target_x, self.target_y = x, y
        else:
            self.target_x, self.target_y = self.projection_on_circle(x, y, center_x, center_y, radius - 1)

        self.canvas.create_image(self.target_x, self.target_y, image=self.target)
        self.get_target_color()
        self.update_colors()

    def get_target_color(self) -> None:
        """Get the color at the current target position."""
        try:
            self.rgb_color = self.img1.getpixel((self.target_x, self.target_y))[:3]  # Get only RGB
        except (AttributeError, IndexError):
            self.rgb_color = self.default_rgb.copy()

    def update_colors(self, *args) -> None:
        """Update colors based on current selection and brightness."""
        brightness = self.brightness_slider_value.get()
        self.get_target_color()

        # Apply brightness adjustment
        adjusted_rgb = [
            int(c * (brightness / 255))
            for c in self.rgb_color
        ]

        # Update button and slider colors
        hex_color = self.rgb_to_hex(adjusted_rgb)
        hover_rgb = self.get_hover_color(adjusted_rgb)
        hover_hex = self.rgb_to_hex(hover_rgb)
        hover2_hex = self.rgb_to_hex(self.get_hover_color(hover_rgb))

        self.button.configure(fg_color=hex_color, hover_color=hover_hex)
        self.slider.configure(
            progress_color=hex_color,
            button_color=hover_hex,
            button_hover_color=hover2_hex
        )

        # Adjust text color based on brightness
        text_color = "white" if brightness < 70 or hex_color == "#000000" else "black"
        self.button.configure(text_color=text_color)

    @staticmethod
    def projection_on_circle(point_x: float, point_y: float,
                             circle_x: float, circle_y: float,
                             radius: float) -> Tuple[float, float]:
        """Project a point onto a circle."""
        angle = math.atan2(point_y - circle_y, point_x - circle_x)
        projection_x = circle_x + radius * math.cos(angle)
        projection_y = circle_y + radius * math.sin(angle)
        return projection_x, projection_y

    def set_initial_color(self, initial_color: str) -> None:
        """BROKEN! Set the initial color selection."""
        if not initial_color or not initial_color.startswith("#"):
            return

        try:
            r, g, b = self.hex_to_rgb(initial_color)
        except ValueError:
            return

        # Search for the color in the image
        for i in range(self.image_dimension):
            for j in range(self.image_dimension):
                pixel = self.img1.getpixel((i, j))
                if pixel[:3] == (r, g, b):  # Compare only RGB
                    self.canvas.delete("all")
                    self.canvas.create_image(self.image_dimension / 2, self.image_dimension / 2, image=self.wheel)
                    self.canvas.create_image(i, j, image=self.target)
                    self.target_x, self.target_y = i, j
                    self.get_target_color()
                    self.update_colors()
                    return


# Helper functions for your usage example
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def get_hover_color(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Calculate hover color from base RGB."""
    return AskColor.adjust_color(rgb, 1.2)


if __name__ == "__main__":
    print("This file isn't intended to be run directly.")
