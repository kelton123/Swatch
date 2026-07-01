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
            'font': ('arial', 14, 'normal'),
            'borderwidth': 0,
            'cursor': 'hand2',  # Hand cursor on hover
            'padx': 20,
            'width': 10,
            'activebackground': cl.CC_BLACK
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        ''' Update the background colour to indicate hovering. '''
        self.config(bg = cl.CC_GREY)
        
    def on_leave(self, event):
        ''' Update the background colour to the default. '''
        self.config(bg = cl.CC_WHITE)

class ButtonNewTab(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            'fg': cl.CC_BLACK,
            'bg': cl.CC_WHITE,
            'font': ('arial', 14, 'normal'),
            'borderwidth': 0,
            'cursor': 'hand2',  # Hand cursor on hover
            'activebackground': cl.CC_BLACK,
            'text': "+"
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