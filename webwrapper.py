import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from interface import Interface
from controller import Controller
import pydub
from pydub import AudioSegment
import tempfile
import io
import os
import shutil
from datetime import datetime

class WebWrapper:
    def __init__(self, config):
        self._app = FastAPI()
        self._port = config['web_server_port']
        self._addr = '0.0.0.0'
        self.request_audio_history = config['web_server_request_history_directory']
        if 'web_server_addr' in config:
            self.addr = config['web_server_addr']
        self.controller = Controller(config)

        @self._app.post("/prompt")
        async def prompt(request: Request):
            content_type = request.headers.get('content-type')
            requested_response_type = request.headers.get('requested-response-type')
            self.controller.interface.mode = requested_response_type
            body = await request.body()
            if content_type == 'text/plain':
                body = body.decode('utf-8')
                response = self.controller.prompt(text=body)
            elif content_type == "audio/mpeg":
                response = self.controller.prompt(audio=body)
            elif content_type == "audio/mp4":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
                    temp_file.write(body)
                    temp_file_path = temp_file.name
                audio = AudioSegment.from_file(temp_file_path, format="m4a")
                wav_temp_file_path = temp_file_path.replace(".m4a", ".wav")
                audio.export(wav_temp_file_path, format="wav")
                response = self.controller.prompt(audio_file=wav_temp_file_path)
                shutil.move(wav_temp_file_path, f"{self.request_audio_history}/{datetime.now()}.wav")
            else:
                print(content_type)
                return "Unrecognized content-type", 401
            if response == None:
                return "Function triggered.", 200
            if requested_response_type == 'text':
                return response, 200
            elif requested_response_type == 'voice':
                _, filepath = self.controller.interface.generate_voice(response)
                return FileResponse(filepath, media_type='audio/mpeg')
            else:
                return "Unrecognized response type requested", 401

    def run(self):
        uvicorn.run(self._app, host=self._addr, port=self._port)
