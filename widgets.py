import tkinter as tk
from tkinter import PhotoImage, messagebox

import colours as cl

def centre_launch_popup(root_window, popup_window, window_width, window_height):
        # Get the current position of the window
        root_x = root_window.winfo_x()
        root_y = root_window.winfo_y()

        # Get the current window width and height
        root_width = root_window.winfo_width()
        root_height = root_window.winfo_height()
        
        # Calculate the exact offsets to center the popup
        x_coord = int(root_x + (root_width - window_width) / 2)
        y_coord = int(root_y + (root_height - window_height) / 2)
        
        # Apply the geometry string (coordinates must be integers)
        popup_window.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")

def create_popup(parent_widget, title="", width=260, height=150):
    '''
    Create a popup above the main window in the center.
    '''
    main_window = parent_widget.winfo_toplevel()

    popup = tk.Toplevel(main_window, bg=cl.CC_WHITE)
    popup.title(title)
    popup.resizable(False, False)
    popup.config(padx=15, pady=15)

    # Launch the popup in the centre of the root window.
    centre_launch_popup(main_window, popup, width, height)
    
    # Make the popup modal (blocks interaction with main window)
    popup.transient(parent_widget)   
    popup.grab_set()

    return popup

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
            'font': ("futura-book", 14, 'normal'),
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
            'font': ("futura", 14, 'normal'),
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
            "font": ("futura", 32, "bold"),
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
            'font': ("futura", 32, 'bold'),
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
            'font': ("futura", 16, 'normal'),
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
            'font': ("futura-book", 12, 'normal'),
            'fg': cl.CC_GREY,
            'bg': cl.CC_WHITE,
            'anchor': 'center'
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class Swatch(tk.Frame):
    def __init__(self, parent, app_root, label_text, hex_code, on_delete=None, on_reorder=None, active_format="hex", **kwargs):
        defaults = {
            "bg": hex_code,
            "height": 20,
            "width": 20
        }

        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self.root_window = app_root

        # Optional callback fired after this swatch has been deleted, so the
        # owning tab can reflow its layout and mark itself as unsaved.
        self.on_delete = on_delete
        self.on_reorder = on_reorder

        # Create the colour variables.
        self.label_text = label_text
        self.hex_code   = hex_code
        self.rgb_code   = self._hex_to_rgb(hex_code)
        self.cmyk_code  = self._rgb_to_cmyk(*self.rgb_code)
        self.hsl_code   = self._hex_to_hsl(hex_code)

        self.formats = ["hex", "rgb", "cmyk", "hsl", "css"]
        self.active_format = active_format

        self.icon_copy_light = PhotoImage(file="Light_copy_icon.png")
        self.icon_copy_dark  = PhotoImage(file="Dark_copy_icon.png")

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
    
    def _hex_to_hsl(self, hex_code):
        hex_string = self.hex_code[1:]
        # 1. Clean the hex string and convert to RGB integers (0-255)
        r, g, b = tuple(int(hex_string[i:i+2], 16) for i in (0, 2, 4))
        
        # 2. Scale RGB values to a 0.0 - 1.0 range
        r /= 255.0
        g /= 255.0
        b /= 255.0
        
        # 3. Find the minimum and maximum color channel values
        c_max = max(r, g, b)
        c_min = min(r, g, b)
        delta = c_max - c_min
        
        # 4. Calculate Lightness (L)
        l = (c_max + c_min) / 2
        
        # 5. Calculate Saturation (S) and Hue (H)
        if delta == 0:
            h = 0
            s = 0
        else:
            # Calculate Saturation based on Lightness levels
            s = delta / (1 - abs(2 * l - 1))
            
            # Calculate Hue based on which color channel is dominant
            if c_max == r:
                h = ((g - b) / delta) % 6
            elif c_max == g:
                h = ((b - r) / delta) + 2
            else:  # c_max == b
                h = ((r - g) / delta) + 4
                
            h *= 60  # Convert Hue to degrees on a 360° color wheel
            if h < 0:
                h += 360

        # 6. Format into clean, rounded integers
        h_deg = round(h)
        s_pct = round(s * 100)
        l_pct = round(l * 100)
        
        return h_deg, s_pct, l_pct
    
    def update_colour_tint(self, tint_percentage=100):
        '''
        Pass in a multiplier which is applied to the hex code to make it more white. 
        Similar to making a colour more transparent but keeping it opaque.
        100 = Original Color, 0 = Pure White (or Black if negative).
        '''
        r,g,b = self.rgb_code

        # 100% means keep the original colour value.
        tint_factor = (100 - abs(tint_percentage)) / 100.0

        if tint_percentage > 0:
            # Tint: Move the current RGB values closer to 255 (White)
            r = int(r + ((255 - r) * tint_factor))
            g = int(g + ((255 - g) * tint_factor))
            b = int(b + ((255 - b) * tint_factor))

        elif tint_percentage < 0:
            # Shade: Move the current RGB values closer to 0 (Black)
            r = int(r * tint_factor)
            g = int(g * tint_factor)
            b = int(b * tint_factor)
            
        # 4. Clamp the values to ensure they stay strictly within the 0-255 range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        new_hex_code = f"#{r:02x}{g:02x}{b:02x}"
        self.colour_code_value.config(text= self.convert_hex_code(new_hex_code, self.active_format))

        text_colour = self.select_by_brightness(cl.CC_WHITE, cl.CC_BLACK, self.calculate_brightness(*self._hex_to_rgb(new_hex_code)))
        # Update widget backgrounds to the new colour
        self.config(bg= new_hex_code)
        self.swatch_name.config(bg=new_hex_code, fg=text_colour)
        self.delete_button.config(bg=new_hex_code, fg=text_colour)
        self.colour_code_value.config(bg=new_hex_code, fg=text_colour)
        self.left_button.config(bg=new_hex_code, fg=text_colour)
        self.right_button.config(bg=new_hex_code, fg=text_colour)

        icon_label = self.select_by_brightness(self.icon_copy_light, self.icon_copy_dark, self.calculate_brightness(*self._hex_to_rgb(new_hex_code)))
        self.icon_copy_label.config(bg=new_hex_code, image=icon_label)

    
    def _create_widgets(self):
        # Determine text colour based on background brightness for readability
        # (Dark backgrounds get white text, light backgrounds get black text)
        brightness = self.calculate_brightness(*self.rgb_code)
        text_colour = self.select_by_brightness(cl.CC_WHITE, cl.CC_BLACK, brightness)
        
        # UI Styling configurations
        label_style_options = {"bg": self.hex_code, "fg": text_colour, "anchor": "w"}
        
        # Add a padding for column 1
        self.columnconfigure(1, weight=2)

        # Swatch Name Label
        # Reduce the font size if there are more than 10 characters in the swatch name.
        font_size = 20
        pad_y = (10,15)
        if len(self.label_text) > 10:
            font_size = 14
            pad_y = (13,20)

        self.swatch_name = tk.Label(
            self,
            text=self.label_text,
            font=("futura-bold", font_size, "bold"),
            **label_style_options)
        self.swatch_name.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=pad_y)

        # Delete button
        self.delete_button = tk.Label(self, text = "✕", font = ("futura", 14), **label_style_options)
        self.delete_button.bind("<Button-1>", lambda event: self.close_swatch())
        self.delete_button.grid(row = 0, column = 2, sticky = "e", padx = (0, 10), pady = (10, 15))
        
        # Colour Code Label
        active_colour_code = self._get_active_colour_code()

        self.colour_code_value = tk.Label(self, text = f"{active_colour_code}", font=("futura-book", 14), **label_style_options)
        self.colour_code_value.grid(row = 1, column = 0, sticky = "w", padx = (10, 0), pady = (4,0))

        # Copy Icon
        icon_copy = self.select_by_brightness(self.icon_copy_light, self.icon_copy_dark, brightness)

        self.icon_copy_label = tk.Label(self, image=icon_copy, **label_style_options)
        self.icon_copy_label.image = icon_copy 
        self.icon_copy_label.grid(row=1, column=2, sticky="e", padx = (0, 10), pady = (4,0))

        # Swatch position management widgets
        self.left_button = tk.Label(self, text = "←", font=("futura", 14), **label_style_options)
        self.left_button.grid(row=2, column=0, sticky="w", padx = (10, 0), pady = (0,10))
        
        self.right_button = tk.Label(self, text="→", font=("futura", 14), **label_style_options)
        self.right_button.grid(row=2, column=2, sticky="e", padx = (0, 10), pady = (0,10))

        # Bind inputs
        self.swatch_name.bind("<Button-1>", lambda event: self.update_swatch_name())
        self.bind("<Button-1>", lambda event: copy_to_clipboard(self.colour_code_value))

        self.colour_code_value.bind("<Button-1>", lambda e: copy_to_clipboard(self.colour_code_value))
        self.icon_copy_label.bind("<Button-1>", lambda event: copy_to_clipboard(self.colour_code_value))
        

        self.left_button.bind("<Button-1>", lambda event: self.move_left())
        self.right_button.bind("<Button-1>", lambda event: self.move_right())
    
        def copy_to_clipboard(widget):
            """
            Copy `value` to the system clipboard and briefly flash the widget's
            text to "Copied!" as visual confirmation.

            `widget` should be the Label (or any widget) that was clicked — it's
            used both to reach the root Tk window and to show the feedback.
            """
            # By default copy the hex code
            colour_code_to_copy = self.hex_code

            match self.active_format:
                case "hex":
                    colour_code_to_copy = self.hex_code
                case "rgb":
                    colour_code_to_copy = self.rgb_code
                case "cmyk":
                    colour_code_to_copy = self.cmyk_code
                case "hsl":
                    colour_code_to_copy = self.hsl_code
                case _:
                    colour_code_to_copy = self.hex_code

            root = widget.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(colour_code_to_copy)
            root.update()

            original_text = widget.cget("text")
            widget.config(text="Copied!")
            widget.after(700, lambda: widget.config(text=original_text))

    def move_left(self):
        """Swaps this swatch with the one to its left in stacking order."""
        parent_tab = self.master
        # Get all sibling swatches inside the active tab frame
        swatches = [w for w in parent_tab.winfo_children() if isinstance(w, Swatch)]
        
        try:
            idx = swatches.index(self)
        except ValueError:
            return
            
        if idx > 0:
            # lower(widget) places this widget BELOW its left sibling in the stacking order,
            # which moves it leftwards (earlier) in the winfo_children() list.
            self.lower(swatches[idx - 1])
            if self.on_reorder:
                self.on_reorder()

    def move_right(self):
        """Swaps this swatch with the one to its right in stacking order."""
        parent_tab = self.master
        # Get all sibling swatches inside the active tab frame
        swatches = [w for w in parent_tab.winfo_children() if isinstance(w, Swatch)]
        
        try:
            idx = swatches.index(self)
        except ValueError:
            return
            
        if idx < len(swatches) - 1:
            # tkraise(widget) places this widget ABOVE its right sibling in the stacking order,
            # which moves it rightwards (later) in the winfo_children() list.
            self.tkraise(swatches[idx + 1])
            if self.on_reorder:
                self.on_reorder()

    def update_colour_code_label(self, code_type):
        match code_type:
            case "hex":
                self.colour_code_value.config(text=self.hex_code)
                self.active_format = "hex"
            case "rgb":
                self.colour_code_value.config(text=self.rgb_code)
                self.active_format = "rgb"
            case "cmyk":
                self.colour_code_value.config(text=self.cmyk_code)
                self.active_format = "cmyk"
            case "hsl":
                self.colour_code_value.config(text=self.hsl_code)
                self.active_format = "hsl"
            case _:
                self.colour_code_value.config(text=self.hex_code)
    
    def calculate_brightness(self, r, g, b):
        return (r * 299 + g * 587 + b * 114) / 1000
    
    def select_by_brightness(self, option_one, option_two, brightness):
        return option_one if brightness < 125 else option_two

    def update_swatch_name(self):
        '''
        When the user clicks on the name label, open a popup where the
        user can type a new name for the swatch.
        '''
        popup = create_popup(self.root_window, "Update Name", 300, 130)

        # Create a label for what the user has to input.
        lbl_name = tk.Label(popup, text="Name:")
        lbl_name.grid(row=0, column=0, sticky="w", pady=10, padx=10)

        # Create an entry widget 
        ent_name = tk.Entry(popup)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        ent_name.focus_set()

        # If the user confirms try and update the swatch label
        def update_name(event=None):
            name = ent_name.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a project name!", parent=popup)
                return
            
            # Check for name length
            if len(name) > 20:
                messagebox.showwarning("Warning", "Name too long. Please keep the name under 20 characters", parent=popup)
                return
            
            # Update font size based on name length
            font_size = 20
            if len(name) > 10:
                font_size = 14

            self.swatch_name.config(text=name, font=("futura", font_size, "bold"))
            popup.destroy()
        
        def close_popup(self):
            popup.destroy()

        # Create confirm and quit buttons
        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        btn_frame.columnconfigure(0, weight=1)

        btn_close = tk.Button(btn_frame, text="Cancel", font=("futura-book", 12), command=popup.destroy)
        btn_close.grid(row=0, column=1, padx=5, pady=0)

        btn_create = tk.Button(btn_frame, text="Update", font=("futura-book", 12), command=update_name)
        btn_create.grid(row=0, column=2, padx=5, pady=0)

        # Bind keyboard inputs
        popup.bind("<Escape>", close_popup)
        popup.bind("<Return>", update_name)

    def _get_active_colour_code(self):
        match self.active_format:
            case "hex":
                return self.hex_code
            case "rgb":
                return self.rgb_code
            case "cmyk":
                return self.cmyk_code
            case "hsl":
                return self.hsl_code
            case _:
                return self.hex_code
            
    def convert_hex_code(self, hex_code, new_format):
        match new_format:
            case "hex":
                return hex_code
            case "rgb":
                return self._hex_to_rgb(hex_code)
            case "cmyk":
                return self._rgb_to_cmyk(*self._hex_to_rgb(hex_code))
            case "hsl":
                return self._hex_to_hsl(hex_code)
            case _:
                return hex_code

    def close_swatch(self):
        self.destroy()
        if self.on_delete:
            self.on_delete()

class CursorFollowerLabel:
    def __init__(self, target_widget, text, offset_x=16, offset_y=16):
        self.target_widget = target_widget
        self.text = text
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.tooltip_window = None

        # Bind cursor events to the frame
        self.target_widget.bind("<Enter>", self._on_enter, add="+")
        self.target_widget.bind("<Motion>", self._on_move, add="+")
        self.target_widget.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, event):
        if self.tooltip_window is not None:
            return

        # 1. Create a borderless floating window
        self.tooltip_window = tk.Toplevel(self.target_widget)
        self.tooltip_window.overrideredirect(True)  # Removes window title bar/borders
        
        # Ensures floating label stays on top of the main app window
        self.tooltip_window.wm_attributes("-topmost", True) 

        # 2. Add the custom styled label inside the window
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            bg=cl.CC_BLACK,
            fg=cl.CC_WHITE,
            font=("futura-book", 12),
            padx=8,
            pady=4,
            bd=0,
            justify="left"
        )
        label.pack()

        # Set initial position
        self._update_position(event)

    def _on_move(self, event):
        self._update_position(event)

    def _on_leave(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def _update_position(self, event):
        if self.tooltip_window:
            # event.x_root and event.y_root give screen-relative coordinates
            x = event.x_root + self.offset_x
            y = event.y_root + self.offset_y
            self.tooltip_window.geometry(f"+{x}+{y}")