import json
import io
import os
import inspect
import traceback
import tiktoken
import openai

class CLI:
    commands = None
    inputstream = None
    context = None
    message_tokens = 0
    content_tokens = 0
    total_tokens = 0
    max_context_length = 4097
    model = "gpt-3.5-turbo"
    encoding_base = "p50k_base"
    context_file = None
    chat_file = None
    pwd = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.chat_file = self.pwd + "/chat.output"
        self.context_file = self.pwd + "/context.json"

        if os.path.exists(self.context_file):
            with open(self.context_file, 'r') as f:
                self.context = json.load(f)
        else:
            self.context = []

    def execute(self):
        if self.commands[1] == "chat":

            openai.api_key = os.environ["OPENAI_API_KEY"]

            if self.inputstream != None:
                inputstream = self.inputstream.read().decode('utf-8')
                if inputstream != "":
                    question = { "role" : "user", "content" : inputstream }
                    self.add(question)
                    self.trim()

                    if self.total_tokens != 0:
                        try:
                            response = openai.ChatCompletion.create(   
                                                                       model=self.model,
                                                                       messages=self.context,
                                                                       temperature=0.5,
                                                                       max_tokens=2048,
                                                                       n=1,
                                                                       stop=None,
                                                                       frequency_penalty=0.5,
                                                                       presence_penalty=0.5,
                                                                   )
                        except Exception as e:
                            return io.BytesIO(traceback.format_exc().encode("utf-8"))
                    else:
                        error = "ERROR: The token trim backoff reached 0. This means that you sent a stream that was too large to fit within the total allowable context limit of " + str(self.max_context_length) + " tokens, and the last trimming operation ended up completely wiping out the conversation context.\n"
                        return io.BytesIO(error.encode("utf-8"))

                    # Output for context retention
                    output_response = response["choices"][0]["message"]
                    self.add(output_response)

                    output = response["choices"][0]["message"]["content"]
                    output = output + "\n"
                    
                    # Ouput for human consumption and longstanding conversation tracking
                    with io.open(self.chat_file, 'a') as f:
                        f.write("----Question:\n\n")
                        f.write(inputstream + "\n")
                        f.write("----Answer:\n\n")
                        f.write(output + "\n")
                        f.close()

                    with open(self.context_file, 'w') as f:
                        json.dump(self.context, f)

                    return io.BytesIO(output.encode("utf-8"))

        if self.commands[1] == "clear":        
            if os.path.exists(self.chat_file):
                os.remove(self.chat_file)

            if os.path.exists(self.context_file):
                with open(self.context_file, 'w') as f:
                    self.context = []
                    json.dump(self.context, f)

        if self.commands[1] == "dump":        
            if os.path.exists(self.chat_file):
                f = open(self.chat_file, "rb")
                return io.BytesIO(f.read())

        return None

    def add(self, entry):
        self.context.append(entry)

    def count(self):
        with open(self.context_file, 'r') as f:
            encoding = tiktoken.get_encoding(self.encoding_base)

            self.message_tokens = 0
            for item in self.context:
                if "content" in item:
                    self.message_tokens += len(encoding.encode(item["content"]))

            self.context_tokens = 0
            for item in self.context:
                self.context_tokens += len(encoding.encode(json.dumps(item)))

            # counting tokens isn't straightforward so we add an adjustment factor of 1800 tokens
            self.total_tokens = self.message_tokens + self.context_tokens
            print("Total tokens: " + str(self.total_tokens))

            if self.total_tokens > self.max_context_length:
                return True
            else:
                return False

    def trim(self):
        while(self.count()):
            self.context.pop(0)
            print("Context tokens: " + str(self.total_tokens) + ". Trimming the context to remain under " + str(self.max_context_length) + ".")
