from controller import Controller

controller = Controller(default_interface=False)
controller.initalize_interface(tools=True, variables=True)

while(True):
    controller.prompt()
    