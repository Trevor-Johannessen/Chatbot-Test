from controller import Controller

controller = Controller(default_interface=False)
controller.custom_interface(tools=True, variables=True)
#controller.custom_interface()

while(True):
    controller.prompt()
    