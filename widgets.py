import tkinter as tk
import colours as cl

# BUTTONS
class ButtonTab(tk.Button):
    """
    Button used for the swatches tabs.
    """
    def __init__(self, parent, **kwargs):
        defaults = {
            'fg': cl.CC_BLACK,
            'bg': cl.CC_WHITE,
            "highlightbackground": cl.CC_WHITE,
            'font': ('arial', 14, 'normal'),
            'borderwidth': 0,
            'cursor': 'hand2',  # Hand cursor on hover
            'padx': 20,
            'width': 10,
            'activebackground': cl.CC_BLACK
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Tracks whether this tab is the currently selected one, so hover
        # events don't overwrite the "active" styling.
        self.is_active = False

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        ''' Update the background colour to indicate hovering. '''
        if not self.is_active:
            self.config(bg = cl.CC_GREY)
        
    def on_leave(self, event):
        ''' Update the background colour to the default. '''
        if not self.is_active:
            self.config(bg = cl.CC_WHITE)

    def set_active(self, active):
        ''' Style this tab as selected/unselected. '''
        self.is_active = active
        if active:
            self.config(bg = cl.CC_BLACK, fg = cl.CC_BLACK)
        else:
            self.config(bg = cl.CC_WHITE, fg = cl.CC_GREY)

class ButtonNewTab(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            'fg': cl.CC_BLACK,
            'bg': cl.CC_WHITE,
            "highlightbackground": cl.CC_WHITE,
            'font': ('arial', 14, 'normal'),
            'borderwidth': 0,
            'cursor': 'hand2',  # Hand cursor on hover
            'activebackground': cl.CC_BLACK,
            'text': "+"
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

class ButtonNewSwatch(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            "text": "+",
            "font": ("arial", 32, "bold"),
            "fg": cl.CC_GREY,
            "bg": cl.CC_WHITE,
            "borderwidth": 0
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# LABELS
class LabelHeading(tk.Label):
    """
    Label used for headings.
    """
    def __init__(self, parent, **kwargs):
        defaults = {
            'font': ('arial', 32, 'bold'),
            'fg': cl.CC_BLACK,
            'bg': cl.CC_WHITE,
            'anchor': 'w'
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

class LabelBody(tk.Label):
    """
    Label used for body text.
    """
    def __init__(self, parent, placeholder="", **kwargs):

        self.placeholder = placeholder
        self.placeholder_colour = cl.CC_GREY

        defaults = {
            'font': ('arial', 16, 'normal'),
            'fg': cl.CC_BLACK,
            'bg': cl.CC_WHITE,
            'anchor': 'w'
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Show placeholder initially
        if self.placeholder:
            self.cl(text=self.placeholder)
            self.cl(fg=self.placeholder_colour)

class LabelFooter(tk.Label):
    """
    Label used in the footer.
    """
    def __init__(self, parent, **kwargs):
        defaults = {
            'font': ('arial', 12, 'normal'),
            'fg': cl.CC_GREY,
            'bg': cl.CC_WHITE,
            'anchor': 'center'
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class Swatch(tk.Frame):
    def __init__(self, parent, label_text, hex_code, on_delete=None, **kwargs):
        defaults = {
            "bg": hex_code,
            "height": 20,
            "width": 20
        }

        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Optional callback fired after this swatch has been deleted, so the
        # owning tab can reflow its layout and mark itself as unsaved.
        self.on_delete = on_delete

        # Create the colour variables.
        self.label_text = label_text
        self.hex_code = hex_code
        self.rgb_code = self._hex_to_rgb(hex_code)
        self.cmyk_code = self._rgb_to_cmyk(*self.rgb_code)

        # Create the card UI widgets.
        self._create_widgets()

    def _hex_to_rgb(self, hex_code):
        """Converts a #RRGGBB string to an (R, G, B) tuple."""
        hex_str = hex_code.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_cmyk(self, r, g, b):
        """Converts RGB values (0-255) to CMYK percentages."""
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100
            
        # Convert RGB to a 0-1 range
        r_prime = r / 255.0
        g_prime = g / 255.0
        b_prime = b / 255.0
        
        # Calculate Black (K)
        k = 1 - max(r_prime, g_prime, b_prime)
        
        # Calculate Cyan, Magenta, Yellow
        c = (1 - r_prime - k) / (1 - k)
        m = (1 - g_prime - k) / (1 - k)
        y = (1 - b_prime - k) / (1 - k)
        
        # Convert to clean rounded percentages
        return (round(c * 100), round(m * 100), round(y * 100), round(k * 100))
    
    def _create_widgets(self):
        # Determine text colour based on background brightness for readability
        # (Dark backgrounds get white text, light backgrounds get black text)
        r, g, b = self.rgb_code
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = cl.CC_WHITE if brightness < 125 else cl.CC_BLACK
        
        # UI Styling configurations
        lbl_opts = {"bg": self.hex_code, "fg": text_color, "anchor": "w"}
        
        # Main Custom Label
        lbl_title = tk.Label(self, text=self.label_text, font=("Arial", 20, "bold"), **lbl_opts)
        lbl_title.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 15))

        # Delete button
        delete_button = tk.Button(self, text = "✕", font = ("Arial", 14), highlightbackground = self.hex_code, fg = cl.CC_BLACK, command=self.close_swatch)
        delete_button.grid(row = 0, column = 1, sticky = "e", padx = (0, 10), pady = (10, 15))
        
        # Hex Code Label
        lbl_hex = tk.Label(self, text="HEX: ", font=("Arial", 12), **lbl_opts)
        lbl_hex.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=2)

        hex_value = tk.Label(self, text = f"{self.hex_code}", font=("Arial", 14), **lbl_opts)
        hex_value.grid(row = 1, column = 1, sticky = "ne", padx = (0, 10), pady = 2)
        
        # RGB Code Label
        rgb_text = f"({r}, {g}, {b})"
        lbl_rgb = tk.Label(self, text="RGB: ", font=("Arial", 12), **lbl_opts)
        lbl_rgb.grid(row=2, column=0, sticky="ew", padx=(10, 0), pady=2)

        rgb_value = tk.Label(self, text = rgb_text, font = ("Arial", 14), **lbl_opts)
        rgb_value.grid(row = 2, column = 1, sticky = "e", padx = (0,10), pady=2)
        
        # CMYK Code Label
        c, m, y, k = self.cmyk_code
        cmyk_text = f"({c}, {m}, {y}, {k})"
        lbl_cmyk = tk.Label(self, text="CMYK: ", font=("Arial", 12), **lbl_opts)
        lbl_cmyk.grid(row=3, column=0, sticky="ew", padx=(10,0), pady=(2, 10))

        cmyk_value = tk.Label(self, text = cmyk_text, font=("Arial", 14), **lbl_opts)
        cmyk_value.grid(row=3, column=1, sticky="e", padx=(0,10), pady=2)

    def close_swatch(self):
        self.destroy()
        if self.on_delete:
            self.on_delete()