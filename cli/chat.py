"""Interactive chat session for mini-cursor-cli.

Handles the main conversation loop, command processing, and
rich terminal output for user interactions.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown

from cli.client import MiniCursorClient, ServerConnectionError, ClientError


class ChatMessage:
    """Represents a chat message in the conversation history."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.role}: {self.content}"


class ChatSession:
    """Interactive chat session manager."""
    
    def __init__(
        self, 
        client: MiniCursorClient, 
        project_root: str, 
        project_name: str,
        debug: bool = False
    ):
        """
        Initialize chat session.
        
        Args:
            client: HTTP client for server communication
            project_root: Absolute path to project root  
            project_name: Name of the project
            debug: Whether debug mode is enabled
        """
        self.client = client
        self.project_root = project_root
        self.project_name = project_name
        self.debug = debug
        self.console = Console()
        
        # Chat state
        self.history: List[ChatMessage] = []
        self.current_model = "gpt-4.1-nano"
        self.session_start = datetime.now()
        
        # Available commands
        self.commands = {
            "/help": self._show_help,
            "/model": self._change_model,
            "/history": self._show_history,
            "/clear": self._clear_history,
            "/status": self._show_status,
            "/projects": self._list_projects,
            "/sync": self._sync_project,
            "/exit": self._exit_session,
            "/quit": self._exit_session,
        }
    
    async def start(self):
        """Start the interactive chat loop."""
        try:
            while True:
                # Get user input
                try:
                    user_input = Prompt.ask(
                        f"[bold blue]{self.project_name}[/bold blue] [dim]({self.current_model})[/dim]",
                        console=self.console
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    await self._exit_session()
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                else:
                    # Handle regular chat message
                    await self._handle_chat_message(user_input)
                    
        except Exception as e:
            error_msg = f"Chat session error: {str(e)}"
            self.console.print(f"[bold red]❌ {error_msg}[/bold red]")
            if self.debug:
                self.console.print_exception()
    
    async def _handle_command(self, command_input: str):
        """Handle special commands starting with /."""
        parts = command_input.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                await self.commands[command](args)
            except Exception as e:
                self.console.print(f"[bold red]Command error:[/bold red] {str(e)}")
                if self.debug:
                    self.console.print_exception()
        else:
            self.console.print(f"[bold red]Unknown command:[/bold red] {command}")
            self.console.print("[dim]Type /help for available commands[/dim]")
    
    async def _handle_chat_message(self, message: str):
        """Handle regular chat messages (to be implemented in Stage 8)."""
        # Add to history
        self.history.append(ChatMessage("user", message))
        
        # For now, just echo back (Stage 8 will implement LLM integration)
        self.console.print(f"[bold green]🤖 Assistant:[/bold green] I received your message: '{message}'")
        self.console.print("[dim]Note: LLM integration will be implemented in Stage 8[/dim]")
        
        # Add assistant response to history
        response = f"Echo: {message} (LLM integration pending)"
        self.history.append(ChatMessage("assistant", response))
    
    async def _show_help(self, args: List[str]):
        """Show available commands."""
        help_text = """[bold]Available Commands:[/bold]

[bold blue]/help[/bold blue] - Show this help message
[bold blue]/model --<name>[/bold blue] - Change AI model (e.g., /model --gpt-4, /model --claude-3)  
[bold blue]/history[/bold blue] - Show conversation history
[bold blue]/clear[/bold blue] - Clear conversation history
[bold blue]/status[/bold blue] - Show session and project status
[bold blue]/projects[/bold blue] - List server projects
[bold blue]/sync[/bold blue] - Synchronize project with server
[bold blue]/exit[/bold blue] or [bold blue]/quit[/bold blue] - Exit the chat session

[bold]Usage:[/bold]
- Type your questions about the codebase normally
- Commands start with / and can have arguments
- Use Ctrl+C or /exit to quit
"""
        self.console.print(Panel(help_text, title="Mini Cursor CLI Help", border_style="blue"))
    
    async def _change_model(self, args: List[str]):
        """Change the AI model."""
        if not args or not args[0].startswith('--'):
            self.console.print("[bold red]Usage:[/bold red] /model --<model_name>")
            self.console.print("[dim]Examples: /model --gpt-4, /model --claude-3, /model --gpt-3.5-turbo[/dim]")
            return
        
        new_model = args[0][2:]  # Remove '--' prefix
        if not new_model:
            self.console.print("[bold red]Error:[/bold red] Model name cannot be empty")
            return
        
        old_model = self.current_model
        self.current_model = new_model
        
        self.console.print(f"[bold green]✅ Model changed:[/bold green] {old_model} → {new_model}")
    
    async def _show_history(self, args: List[str]):
        """Show conversation history."""
        if not self.history:
            self.console.print("[dim]No conversation history yet[/dim]")
            return
        
        # Limit history display
        limit = 10
        if args and args[0].isdigit():
            limit = int(args[0])
        
        history_text = f"[bold]Last {min(limit, len(self.history))} messages:[/bold]\n\n"
        
        for message in self.history[-limit:]:
            role_color = "blue" if message.role == "user" else "green"
            role_icon = "👤" if message.role == "user" else "🤖"
            time_str = message.timestamp.strftime("%H:%M:%S")
            
            history_text += f"[bold {role_color}]{role_icon} {message.role.title()}[/bold {role_color}] [dim]({time_str})[/dim]\n"
            history_text += f"{message.content}\n\n"
        
        self.console.print(Panel(history_text, title="Conversation History", border_style="yellow"))
    
    async def _clear_history(self, args: List[str]):
        """Clear conversation history."""
        count = len(self.history)
        self.history.clear()
        self.console.print(f"[bold green]✅ Cleared {count} messages from history[/bold green]")
    
    async def _show_status(self, args: List[str]):
        """Show session and project status."""
        session_duration = datetime.now() - self.session_start
        duration_str = f"{session_duration.seconds // 60}m {session_duration.seconds % 60}s"
        
        table = Table(title="Session Status", border_style="blue")
        table.add_column("Property", style="bold blue")
        table.add_column("Value", style="green")
        
        table.add_row("Project", self.project_name)
        table.add_row("Project Path", self.project_root)
        table.add_row("Current Model", self.current_model)
        table.add_row("Session Duration", duration_str)
        table.add_row("Messages", str(len(self.history)))
        table.add_row("Debug Mode", "Enabled" if self.debug else "Disabled")
        
        self.console.print(table)
    
    async def _list_projects(self, args: List[str]):
        """List all projects on the server."""
        try:
            with self.console.status("[bold blue]Fetching projects..."):
                projects_data = await self.client.list_projects()
            
            if projects_data['projects_count'] == 0:
                self.console.print("[dim]No projects registered on server[/dim]")
                return
            
            table = Table(title=f"Server Projects ({projects_data['projects_count']})", border_style="green")
            table.add_column("Project Name", style="bold blue")
            table.add_column("Path", style="dim")
            table.add_column("Files", justify="right")
            table.add_column("Last Sync", style="dim")
            
            for project in projects_data['projects']:
                # Format last sync time
                last_sync = datetime.fromisoformat(project['last_sync'].replace('Z', '+00:00'))
                sync_str = last_sync.strftime("%H:%M:%S")
                
                table.add_row(
                    project['project_name'],
                    project['project_path'],
                    str(project['file_count']),
                    sync_str
                )
            
            self.console.print(table)
            
        except (ServerConnectionError, ClientError) as e:
            self.console.print("[bold red]❌ Failed to list projects[/bold red]")
            self.console.print(self.client.format_server_error(e))
    
    async def _sync_project(self, args: List[str]):
        """Synchronize current project with server."""
        try:
            with self.console.status("[bold blue]Synchronizing project..."):
                sync_result = await self.client.sync_project(self.project_root)
            
            if sync_result['trees_match']:
                self.console.print("[bold green]✅ Project is already synchronized[/bold green]")
            else:
                changed_count = len(sync_result['changed_files'])
                self.console.print(f"[bold green]✅ Synchronized {changed_count} changed files[/bold green]")
                
                if self.debug and changed_count > 0:
                    self.console.print("[bold]Changed files:[/bold]")
                    for file_path in sync_result['changed_files'][:10]:  # Show first 10
                        self.console.print(f"  • {file_path}")
                    
                    if changed_count > 10:
                        self.console.print(f"  ... and {changed_count - 10} more")
                        
        except (ServerConnectionError, ClientError) as e:
            self.console.print("[bold red]❌ Failed to sync project[/bold red]")
            self.console.print(self.client.format_server_error(e))
    
    async def _exit_session(self, args: List[str] = None):
        """Exit the chat session."""
        session_duration = datetime.now() - self.session_start
        duration_str = f"{session_duration.seconds // 60}m {session_duration.seconds % 60}s"
        
        goodbye_text = f"""[bold green]Session Summary:[/bold green]
• Duration: {duration_str}
• Messages: {len(self.history)}
• Project: {self.project_name}

[dim]👋 Thanks for using mini-cursor-cli![/dim]"""
        
        self.console.print(Panel(goodbye_text, title="Goodbye", border_style="green"))
        exit(0) 