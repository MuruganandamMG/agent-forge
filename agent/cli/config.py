import click
import json
import os

CONFIG_FILE = ".agent_config.json"

def load_config(project_dir: str) -> dict:
    config_path = os.path.join(project_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(project_dir: str, config: dict):
    config_path = os.path.join(project_dir, CONFIG_FILE)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

@click.group("config")
def config_cmd():
    """Manage workspace configuration."""
    pass

@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    config[key] = value
    save_config(project_dir, config)
    click.echo(f"✅ Set {key} = {value}")

@config_cmd.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key):
    """Get a configuration value."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    val = config.get(key)
    if val is not None:
        click.echo(f"{key} = {val}")
    else:
        click.echo(f"❌ Key '{key}' not found.")

@config_cmd.command("list")
@click.pass_context
def config_list(ctx):
    """List all configuration values."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    if not config:
        click.echo("No configuration found.")
        return
    click.echo("⚙️ Current Configuration:")
    for k, v in config.items():
        click.echo(f"  {k}: {v}")
