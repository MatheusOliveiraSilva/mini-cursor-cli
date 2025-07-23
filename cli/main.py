"""Main CLI entry point for mini-cursor-cli.

Provides the command-line interface for starting chat sessions,
detecting projects, and managing server connections.
"""

import asyncio
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from cli.client import MiniCursorClient, ServerConnectionError, ClientError, detect_project_root
from cli.chat import ChatSession


console = Console()


def print_banner():
    """Print the mini-cursor-cli banner."""
    banner = Text.from_markup(
        "[bold blue]mini-cursor-cli[/bold blue] [dim]v0.1.0[/dim]"
    )
    console.print(Panel(banner, border_style="blue"))


def print_error(message: str):
    """Print an error message with formatting."""
    console.print(f"[bold red]❌ Error:[/bold red] {message}")


def print_success(message: str):
    """Print a success message with formatting."""
    console.print(f"[bold green]✅ Success:[/bold green] {message}")


def print_info(message: str):
    """Print an info message with formatting."""
    console.print(f"[bold blue]ℹ️  Info:[/bold blue] {message}")


@click.command()
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode with verbose logging"
)
@click.option(
    "--server-url",
    default="http://localhost:8000",
    help="Server URL (default: http://localhost:8000)"
)
@click.option(
    "--project-path",
    type=click.Path(exists=True),
    help="Project path (auto-detected if not specified)"
)
def main(debug: bool, server_url: str, project_path: str):
    """
    Mini Cursor CLI - Chat with your codebase using Merkle trees.
    
    Start the interactive chat session after connecting to the server
    and registering your project.
    """
    # Print banner
    print_banner()
    
    if debug:
        print_info("Debug mode enabled")
    
    # Detect project root
    if project_path:
        project_root = os.path.abspath(project_path)
    else:
        project_root = detect_project_root()
        if not project_root:
            print_error(
                "Could not detect project root. Please run from a project directory "
                "or specify --project-path"
            )
            sys.exit(1)
    
    project_name = Path(project_root).name
    print_info(f"Detected project: [bold]{project_name}[/bold] at {project_root}")
    
    # Start async session
    try:
        asyncio.run(start_session(server_url, project_root, project_name, debug))
    except KeyboardInterrupt:
        console.print("\n[dim]👋 Goodbye![/dim]")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        if debug:
            console.print_exception()
        sys.exit(1)


async def start_session(server_url: str, project_root: str, project_name: str, debug: bool):
    """
    Start the main chat session.
    
    Args:
        server_url: URL of the server
        project_root: Absolute path to project root
        project_name: Name of the project
        debug: Whether debug mode is enabled
    """
    async with MiniCursorClient(server_url) as client:
        
        # Check server health
        try:
            with console.status("[bold blue]Connecting to server..."):
                health = await client.check_server_health()
            
            print_success(f"Connected to server - {health['message']}")
            if debug:
                print_info(f"Server uptime: {health['uptime']}, Projects: {health['projects_count']}")
                
        except (ServerConnectionError, ClientError) as e:
            print_error("Cannot connect to server")
            console.print(client.format_server_error(e))
            console.print("\n[bold yellow]📖 Setup Instructions:[/bold yellow]")
            console.print("1. Make sure Docker is running")
            console.print("2. Start the server: [code]docker run -p 8000:8000 mini-cursor-cli-server[/code]")
            console.print("3. Or check README.md for detailed setup")
            sys.exit(1)
        
        # Register project
        try:
            with console.status("[bold blue]Registering project..."):
                registration = await client.register_project(project_root, project_name)
            
            print_success(f"Project registered: {registration['message']}")
            if debug:
                print_info(f"Project ID: {registration['project_id']}")
                
        except (ServerConnectionError, ClientError) as e:
            print_error("Failed to register project")
            console.print(client.format_server_error(e))
            sys.exit(1)
        
        # Initial sync
        try:
            with console.status("[bold blue]Synchronizing project files..."):
                sync_result = await client.sync_project(project_root)
            
            if sync_result['trees_match']:
                print_success("Project is synchronized")
            else:
                changed_count = len(sync_result['changed_files'])
                print_success(f"Synchronized {changed_count} changed files")
                if debug and changed_count > 0:
                    print_info(f"Changed files: {', '.join(sync_result['changed_files'][:5])}")
                    
        except (ServerConnectionError, ClientError) as e:
            print_error("Failed to sync project")
            console.print(client.format_server_error(e))
            sys.exit(1)
        
        # Start chat session
        console.print("\n[bold green]🚀 Starting chat session...[/bold green]")
        console.print("[dim]Type your questions about the codebase. Use /help for commands.[/dim]\n")
        
        chat_session = ChatSession(
            client=client,
            project_root=project_root,
            project_name=project_name,
            debug=debug
        )
        
        await chat_session.start()


if __name__ == "__main__":
    main() 