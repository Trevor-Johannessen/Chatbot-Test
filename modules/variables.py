class Variables():
    def __init__(self):
        pass
    
    def __context(self):
        additional_context = 'Below is a JSON containing an array of variables and their datatypes. You may use these values when making function calls.\n'
        additional_context += self.__get_variables()
        return additional_context

    def __get_variables(self):
        return f'[{{"name": "listen_duration","type": "NUMBER","value":{self.listen_duration}}},{{"name": "ambient_noise_timeout","type": "NUMBER","value": {self.ambient_noise_timeout}}}]'

    def set_variable(self, var: str, value: any):
        """Sets the given variable to the given value."""
        setattr(self, var, value)
    set_variable.variables={"var":"The name of the variable.","value":"The value to set."}
    
    def get_variable(self, var: str):
        """Gets the given variable to the given value."""
        self.interface.say(f"The value of {var} is {getattr(self, var)}.")
    get_variable.variables={"var":"The name of the variable."}

    def add_variable(self, var: str, value: int|float):
        """Adds the {value} parameter to the given variable."""
        setattr(self, var, getattr(self,var) + value)
    add_variable.variables={"var": "The name of the variable.","value":"The value to add."}

    def subtract_variable(self, var: str, value: int|float):
        """Subtracts the {value} parameter to the given variable."""
        setattr(self, var, getattr(self,var) - value)
    subtract_variable.variables={"var": "The name of the variable.","value":"The value to subtract."}