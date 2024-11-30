from typing import Dict, List, Optional

from pydantic import BaseModel

from django.core.management import BaseCommand, call_command


class CallableCommand(BaseModel):
    command: str
    args: Optional[List[str]] = []
    kwargs: Dict[str, str] = dict()


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("[+] Running setup commands...", style_func=self.style.SUCCESS)

        commands = [
            CallableCommand(command="makemigrations", args=["auth", "graphql_auth"]),
            CallableCommand(command="migrate"),
            CallableCommand(command="sync-schedulers"),
            CallableCommand(command="import-initial-data"),
            CallableCommand(command="synchronize-tasks"),
            CallableCommand(command="collectstatic", args=["--noinput"]),
        ]

        for cmd in commands:
            self.stdout.write("[+] Running command", style_func=self.style.SUCCESS)
            self.stdout.write(cmd.command.upper(), style_func=self.style.NOTICE)
            call_command(cmd.command, *cmd.args, **cmd.kwargs)
            self.stdout.write(f"{"+" * 50}", style_func=self.style.HTTP_INFO)
