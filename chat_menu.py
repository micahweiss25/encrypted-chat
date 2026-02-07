import asyncio
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from message import Message

class ChatMenu():
    """Command line interface for the chat menu."""
    intro = "Chat with ADDRESS"
    prompt = "> "

    def __init__(self, host, server):
        self.server = server
        self.host = host
        self.client = self.server.clients.get(host)

    async def start(self):
        """process chat commands."""
        completer = WordCompleter(['send', 'help', 'exit'], ignore_case=True)
        session = PromptSession(
            completer=completer,
            history=FileHistory('.history.txt'),
            auto_suggest=AutoSuggestFromHistory()
        )

        print(self.intro)
        # If the client doesn't exist, prompt for port and attempt to register
        if not self.client:
            print("Client not registered.")
            port = input("Enter hosts port to begin registration: ")
            if not port.isdigit():
                print("Invalid port. Exiting chat.")
                return
            # initiate registration
            else:
                await self.server.send_message(self.host, int(port), Message.MsgID.REGISTER.value)
                print(self.server.clients)
            self.client = self.server.clients.get(self.host)
            print(f"host name {self.host}")
            
        self.reader_loop = asyncio.create_task(self.client.reader_loop())

        while True:
            try:
                user_input = await session.prompt_async(self.prompt)
                words = shlex.split(user_input)

                if not words:
                    self.do_help()
                else:
                    command = words[0]
                    if command == "send":
                        if len(words) != 2:
                            print("Usage: send '<message>'")
                            continue
                        else:
                            print("Client listener port: ", self.client.listener_port)
                            await self.server.send_message(self.host, self.client.listener_port, Message.MsgID.TEXT.value, words[1])
                    elif command == "help":
                        self.do_help()
                    elif command == "exit":
                        self.do_exit()
                        break
                    else:
                        print(f"Unknown command: {command}")

            except (KeyboardInterrupt, EOFError):
                self.do_exit()
                break

    def do_help(self):
        """Show commands and their descriptions."""
        for method_name in dir(self):
            if method_name.startswith('do_'):
                method = getattr(self, method_name)
                command = method_name[3:]
                doc = method.__doc__ or ''
                print(f"{command}: {doc.strip()}")

    async def do_send(self, arg):
        """Send a message to the peer: send '<message>'"""
        if len(arg) != 2:
            print("Usage: send '<message>'")
            return
        message = arg[1]
        print(f"Sending message: {message}")

    def do_exit(self):
        """Exit the chat."""
        print("Leaving chat...")
        self.reader_loop.cancel()

