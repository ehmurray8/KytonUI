from program import Page, ProgramType, BAKING_ID

class BakingPage(Page):
    def __init__(self, parent, master):
        baking_type = ProgramType(BAKING_ID)
        super().__init__(parent, master, baking_type)

    
