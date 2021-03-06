"""Overrides the default matplotlib tkinter toolbar to add play and pause to the graph animation."""
from tkinter.ttk import Frame

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


class Toolbar(NavigationToolbar2TkAgg):
    """
    Overrides the default Matplotlib toolbar to add play and pause animation buttons.

    :ivar Graphing graphing_helper: Graphing helper object that controls the graphing screen
    """

    def __init__(self, figure_canvas: FigureCanvasTkAgg, parent: Frame):
        """
        Override the default matplotlib toolbar for the tkinter canvas.

        :param figure_canvas: the canvas to add the toolbar to.
        :param parent: the parent frame of the canvas
        """
        self.toolitems = (('Home', 'Reset original view', 'home', 'home'),
                          ('Back', 'Back to  previous view', 'back', 'back'),
                          ('Forward', 'Forward to next view',
                           'forward', 'forward'),
                          (None, None, None, None),
                          ('Pan', 'Pan axes with left mouse, zoom with right',
                           'move', 'pan'),
                          ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                          (None, None, None, None),
                          ('Subplots', 'Configure subplots',
                           'subplots', 'configure_subplots'),
                          ('Save', 'Save the figure',
                           'filesave', 'save_figure'),
                          (None, None, None, None),
                          ('Pause', 'Pause the animation', 'pause', 'pause'),
                          ('Play', 'Play the animation', 'play', 'play'))

        self.figure_canvas = figure_canvas
        self.parent = parent
        self.graphing_helper = None
        super().__init__(self.figure_canvas, self.parent)

    def set_gh(self, graphing_helper):
        """
        Sets the graphing helper.

        :param graphing_helper: The graphing helper class controlling the graphing screen
        """
        self.graphing_helper = graphing_helper

    def play(self):
        """Plays graph animation linked to play button on toolbar."""
        self.graphing_helper.play()

    def pause(self):
        """Pauses graph animation linked to button on toolbar."""
        self.graphing_helper.pause()
