import asyncio
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

class ChatMenu():
    """Command line interface for the chat menu."""
    intro = "Chat with ADDRESS"
    prompt = "> "

    def __init__(self, client):
        self.client = client

    async def start(self):
        """process chat commands."""
        print(self.intro)
        self.reader_loop = asyncio.create_task(self.client.reader_loop())

        completer = WordCompleter(['send', 'help', 'exit'], ignore_case=True)
        session = PromptSession(
            completer=completer,
            history=FileHistory('.history.txt'),
            auto_suggest=AutoSuggestFromHistory()
        )

        while True:
            try:
                user_input = await session.prompt_async(self.prompt)
                words = shlex.split(user_input)

                if not words:
                    self.do_help()
                else:
                    command = words[0]
                    if command == "send":
                        await self.do_send(words)
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

