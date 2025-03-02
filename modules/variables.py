import json

class Variables():
    def __init__(self, config):
        self.interface = config['interface']
    
    def context(self, config):
        variables = [
            {
                "name": "listen_duration",
                "type": "NUMBER",
                "value": config['listen_duration']
            },
            {
                "name": "ambient_noise_timeout",
                "type": "NUMBER",
                "value": config['ambient_noise_timeout']
            }
        ]
        return f'Below is a JSON containing an array of variables and their datatypes. You may use these values when making function calls.\n{json.dumps(variables)}'

    def set_variable(self, var: str, value: any):
        """Sets the given variable to the given value."""
        self.interface.clear_recent_context()
        setattr(self, var, value)
    set_variable.variables={"var":"The name of the variable.","value":"The value to set."}
    
    def get_variable(self, var: str):
        """Gets the given variable to the given value."""
        self.interface.clear_recent_context()
        self.interface.say(f"The value of {var} is {getattr(self, var)}.")
    get_variable.variables={"var":"The name of the variable."}

    def add_variable(self, var: str, value: int|float):
        """Adds the {value} parameter to the given variable."""
        self.interface.clear_recent_context()
        setattr(self, var, getattr(self,var) + value)
    add_variable.variables={"var": "The name of the variable.","value":"The value to add."}

    def subtract_variable(self, var: str, value: int|float):
        """Subtracts the {value} parameter to the given variable."""
        self.interface.clear_recent_context()
        setattr(self, var, getattr(self,var) - value)
    subtract_variable.variables={"var": "The name of the variable.","value":"The value to subtract."}