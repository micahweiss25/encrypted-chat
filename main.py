import asyncio
import logging
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from chat_menu import ChatMenu
from server import Server
from client import Client
import config
import ipaddress

log_level = config.get_settings().LOG_LEVEL
logging.basicConfig(
    level=log_level,
    format='%(levelname)s - %(message)s'
)


class MainMenu():
    """Command line interface for the main menu."""
    intro = "Welcome to the Encrypted Chat. Type help to list commands.\n"
    prompt = "(encrypted-chat) "

    def __init__(self):
        self.server = Server()

    async def start(self):
        """Show the main menu."""
        print(self.intro)
        self.listener = asyncio.create_task(self.server.start())

        # TODO: Add nested autocomplete for chat to list registered peers to chat with
        completer = WordCompleter(
            ['list_peers', 'chat', 'exit'], ignore_case=True)
        # TODO: Add history autocompletion to the main menu
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
                    if command == "register":
                        await self.do_register(words)
                    elif command == "list_peers":
                        self.do_list_peers()
                    elif command == "help":
                        self.do_help()
                    elif command == "chat":
                        await self.do_chat(words)
                    elif command == "exit":
                        await self.do_exit()
                        break
                    else:
                        print(f"Unknown command: {command}")

            except (KeyboardInterrupt, EOFError):
                await self.do_exit()
                break

    def do_help(self):
        """Show commands and their descriptions."""
        for method_name in dir(self):
            if method_name.startswith('do_'):
                method = getattr(self, method_name)
                command = method_name[3:]
                doc = method.__doc__ or ''
                print(f"{command}: {doc.strip()}")

    def do_list_peers(self):
        """List all registered peers."""
        if not self.server.clients:
            print("No registered peers.")
            return
        print("Registered peers:")
        for host in self.server.clients:
            print(f"- {host}")

    async def do_chat(self, arg):
        """Open a chat with a registered peer or initate a chat with a new peer: chat <host>"""
        if len(arg) != 2:
            print("Usage: chat <host>")
            return

        host = arg[1]

        try:
            ipaddress.IPv4Address(host)
        except Exception:
            print("Invalid host. Host must be a valid IPv4 address (e.g. 192.168.1.10).")
            return

        chat_menu = ChatMenu(host, self.server)
        await chat_menu.start()

    async def do_exit(self):
        """Exit the chat application."""
        print("Exiting...")
        self.server.end()


if __name__ == "__main__":
    # Launch tui
    menu = MainMenu()
    asyncio.run(menu.start())
