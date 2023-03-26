import json
import io
import os
import inspect
import openai

class CLI:
    commands = None
    inputstream = None
    pwd = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream

    def execute(self):
        chat = self.pwd + "/chat.output"

        if self.commands[1] == "chat":

            openai.api_key = os.environ["OPENAI_API_KEY"]

            f = None
            context = ""
            if os.path.exists(chat):
                with io.open(chat, 'r') as f:
                    context = f.read()

            if self.inputstream != None:
                prompt = self.inputstream.read().decode('utf-8')
                if prompt != "":
                    inputdata = [{"role": "user", "content": prompt}]

                    response = openai.ChatCompletion.create(   
                                                               model="gpt-3.5-turbo",
                                                               messages=inputdata,
                                                               temperature=0.5,
                                                               max_tokens=2048,
                                                               n=1,
                                                               stop=None,
                                                               frequency_penalty=0.5,
                                                               presence_penalty=0.5,
                                                           )

                    output = response["choices"][0]["message"]["content"]

                    with io.open(chat, 'a') as f:
                        f.write("----Question:\n")
                        f.write(prompt)
                        f.write("----Answer:\n")
                        f.write(output + "\n")

                    f.close()

                    output = output + "\n"
                
                    return io.BytesIO(output.encode("utf-8"))

        if self.commands[1] == "clear":        
            if os.path.exists(chat):
                os.remove(chat)

        if self.commands[1] == "dump":        
            if os.path.exists(chat):
                f = open(chat, "rb")
                return io.BytesIO(f.read())

        return None
