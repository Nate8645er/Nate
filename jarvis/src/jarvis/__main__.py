"""JARVIS command-line interface.

Commands:

* ``jarvis serve``  - start the HTTP/WebSocket API server
* ``jarvis chat``   - interactive terminal chat
* ``jarvis gui``    - launch the Iron-Man style HUD (requires the ``gui`` extra)
* ``jarvis voice``  - headless voice assistant loop (requires the ``voice`` extra)
* ``jarvis status`` - show configuration, providers and subsystem status
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jarvis import __version__
from jarvis.app import JarvisApp
from jarvis.core.config import load_config

cli = typer.Typer(name="jarvis", help="JARVIS - your personal AI assistant", no_args_is_help=True)
console = Console()


def _config(config_file: Path | None):
    return load_config(config_file)


@cli.command()
def serve(
    host: str = typer.Option(None, help="Bind host (overrides config)"),
    port: int = typer.Option(None, help="Bind port (overrides config)"),
    config_file: Path = typer.Option(None, "--config", help="Path to config.yaml"),
) -> None:
    """Start the JARVIS API server."""
    import uvicorn

    from jarvis.api.server import create_api

    async def main() -> None:
        app = await JarvisApp.create(_config(config_file))
        app.start_hot_reload()
        api = create_api(app)
        server = uvicorn.Server(
            uvicorn.Config(
                api,
                host=host or app.config.api.host,
                port=port or app.config.api.port,
                log_level=app.config.log_level.lower(),
            )
        )
        try:
            await server.serve()
        finally:
            await app.aclose()

    asyncio.run(main())


@cli.command()
def chat(
    config_file: Path = typer.Option(None, "--config", help="Path to config.yaml"),
    orchestrate: bool = typer.Option(False, help="Use the multi-agent orchestrator"),
) -> None:
    """Interactive terminal chat with streaming output."""

    async def main() -> None:
        app = await JarvisApp.create(_config(config_file))
        app.start_hot_reload()

        async def terminal_confirmer(capability: str, description: str) -> bool:
            console.print(
                Panel(f"[bold yellow]Permission requested[/]: {capability}\n{description}")
            )
            return typer.confirm("Allow?", default=False)

        app.permissions.set_confirmer(terminal_confirmer)
        console.print(
            Panel(
                f"[bold cyan]{app.config.assistant_name}[/] v{__version__} online. "
                "Type 'exit' to quit.",
                border_style="cyan",
            )
        )
        try:
            while True:
                text = await asyncio.to_thread(console.input, "[bold green]You:[/] ")
                if text.strip().lower() in ("exit", "quit", "bye"):
                    break
                if not text.strip():
                    continue
                console.print(f"[bold cyan]{app.config.assistant_name}:[/] ", end="")
                if orchestrate:
                    result = await app.ask(text)
                    console.print(result.output)
                else:
                    from jarvis.agents.base import AgentResult

                    async for item in app.ask_stream(text):
                        if isinstance(item, AgentResult):
                            console.print()
                        else:
                            console.print(item, end="")
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            await app.aclose()
            console.print("\n[dim]JARVIS offline.[/]")

    asyncio.run(main())


@cli.command()
def gui(config_file: Path = typer.Option(None, "--config", help="Path to config.yaml")) -> None:
    """Launch the Iron-Man style HUD (PySide6)."""
    try:
        from jarvis.gui.main import run_gui
    except ImportError as exc:
        console.print(f"[red]GUI dependencies missing:[/] {exc}\nInstall with: uv pip install 'jarvis-assistant[gui]'")
        raise typer.Exit(code=1) from exc
    run_gui(_config(config_file))


@cli.command()
def voice(config_file: Path = typer.Option(None, "--config", help="Path to config.yaml")) -> None:
    """Run the always-on voice assistant (wake word → STT → answer → TTS)."""

    async def main() -> None:
        config = _config(config_file)
        config.voice.enabled = True
        app = await JarvisApp.create(config)
        try:
            from jarvis.voice.service import VoiceService
        except ImportError as exc:
            console.print(
                f"[red]Voice dependencies missing:[/] {exc}\n"
                "Install with: uv pip install 'jarvis-assistant[voice]'"
            )
            raise typer.Exit(code=1) from exc
        service = await app.container.aresolve(VoiceService)
        try:
            await service.run_forever()
        finally:
            await app.aclose()

    asyncio.run(main())


@cli.command()
def status(config_file: Path = typer.Option(None, "--config", help="Path to config.yaml")) -> None:
    """Show providers, subsystems, agents and tools."""

    async def main() -> None:
        app = await JarvisApp.create(_config(config_file))
        try:
            healthy = await app.providers.healthy_providers()
            info = app.status()
            table = Table(title=f"JARVIS v{__version__}", border_style="cyan")
            table.add_column("Component", style="bold")
            table.add_column("Value")
            table.add_row("Healthy providers", ", ".join(healthy) or "none configured")
            table.add_row("Subsystems", ", ".join(info["subsystems"]) or "core only")
            table.add_row("Agents", ", ".join(info["agents"]))
            table.add_row("Tools", str(len(info["tools"])))
            table.add_row("Plugins", ", ".join(info["plugins"]) or "none")
            table.add_row("Data dir", str(app.config.data_dir))
            console.print(table)
        finally:
            await app.aclose()

    asyncio.run(main())


@cli.command()
def version() -> None:
    """Print the JARVIS version."""
    console.print(f"JARVIS v{__version__}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
