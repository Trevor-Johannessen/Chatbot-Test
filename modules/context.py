class Context():
    def __init__(self):
        pass

    def save_context(self, filename: str):
        """Saves the current context as the given filename."""
        self.interface.saveContext(filename)
    save_context.variables={"filename":"The name of the file to save the context as."}
    
    def load_context(self, filename: str):
        """Overwrites the current context with the context in the given file."""
        self.interface.loadContext(filename)
    load_context.variables={"filename":"The name of the file to load the context from."}

    def clear_context(self):
        """Clears the current context window."""
        self.interface.say("Clearing context.")
        self.interface.clear_context()