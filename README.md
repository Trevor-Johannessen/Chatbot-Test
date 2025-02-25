# Name pending
A small project I'm working on to increase efficiency by implementing an AI assistant with physical integrations.

---

## Configuration Settings

The `config.json` file contains various settings that configure the behavior of the AI assistant. Below is a detailed explanation of each setting:

- **names**: An array of strings that specifies the names the AI assistant will respond to. Example: `["monika", "monica"]`.

- **type**: A list of strings that defines the type of AI assistants.
  - sentry: The AI will listen in the background and respond if it hears its name.
  - webserver: Sets up a web server which can be called by sending a POST request to the /prompt endpoint.

- **web_server_port**: A string representing the port number on which the web server will run. Default: `"8989"`.

- **mode**: A string that specifies the operational mode of the AI.
  - voice: Communicate with the AI via a microphone. This mode will listen in the background for the AI's name.
  - text: Communicate with the AI through text. This mode will prompt the console for input.

- **voice_id**: The ID provided by elevenlabs for whichever model to use.

- **voice_history_directory**: A string specifying the directory path where voice interaction history will be stored. Example: `"./audio/history"`.

- **web_server_request_history_directory**: A string specifying the directory path where client voicelines will be stored. Example: `"./audio/webserver/history"`.

- **listen_duration**: An integer that defines the duration (in seconds) for which the AI will listen for voice input. Default: `5`.

- **ambient_noise_timeout**: A float that sets the timeout (in seconds) for detecting ambient noise before the AI stops listening. Default: `0.2`.

- **context_window**: An integer for the number of minutes an AI should wait without interaction before clearing it's context. Default: `5`.

- **modules**: An array of strings listing the modules to be loaded by the AI. These modules define the functionalities and contexts the AI can handle. The "Default" module should **always** be included.

- **context**: A string that provides a brief description of the AI's role and communication style.

- **minecraft_server_addr**: A string specifying the address and port of the Minecraft server the AI will interact with.

- **minecraft_api_addr**: A string specifying the address and port of the Minecraft API server.

---

# Versions
* **v0.0.3**
  * Web server mode added
  * Further separated out the AI interface to provide more granular access
  * Added support for parsing audio filepaths
  
* **v0.0.2**
  * Function calling implemented
  * Dynamically loaded modules added to refine what context the AI uses
  * Config file added to further customize the AI
  * Elevenlabs text to speech implemented

* **v0.0.1**
  * First release containing a simple interface for talking in real-time to chat-gpt