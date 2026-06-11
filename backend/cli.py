import argparse
from rich.console import Console
from rich.table import Table

import asyncio
import logging

# Suppress noisy asyncio exceptions for DNS lookup failures on dead domains
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

from collectors.username_collector import run_username_collection
from collectors.email_collector import run_email_collection
from collectors.phone_collector import run_phone_collection

import sys

console = Console()

def print_custom_help():
    console.print("\n[bold red]Raven CLI[/bold red]\n")
    table = Table(show_header=True, header_style="bold red", box=None)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Explanation")
    table.add_column("Example", style="green")
    
    table.add_row("-h, -help, --help", "Show this help message and exit", "raven -help")
    table.add_row("-u, --username", "Search by username", "raven -u username")
    table.add_row("-e, --email", "Search by email", "raven -e test@example.com")
    table.add_row("-p, --phone", "Search by phone number", "raven -p +1234567890")
    table.add_row("-web, --web", "Start the web server", "raven -web")
    
    console.print(table)
    console.print()

def main():
    if "-help" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
        print_custom_help()
        sys.exit(0)
        
    parser = argparse.ArgumentParser(description="Raven CLI", add_help=False)
    parser.add_argument("-u", "--username", help="Search by username")
    parser.add_argument("-e", "--email", help="Search by email")
    parser.add_argument("-p", "--phone", help="Search by phone number")
    parser.add_argument("-web", "--web", action="store_true", help="Start the web server")

    args = parser.parse_args()

    if args.web:
        from api import app as flask_app
        port = 8000
        console.print(f"[*] Starting web server on port {port}...")
        flask_app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)
        return

    if not any([args.username, args.email, args.phone]):
        print_custom_help()
        return

    results = []
    if args.username:
        console.print(f"[*] Starting direct OSINT collection for username: [bold]{args.username}[/bold]...")
        results = asyncio.run(run_username_collection(args.username))
    elif args.email:
        console.print(f"[*] Starting direct OSINT collection for email: [bold]{args.email}[/bold]...")
        results = asyncio.run(run_email_collection(args.email))
    elif args.phone:
        console.print(f"[*] Starting direct OSINT collection for phone: [bold]{args.phone}[/bold]...")
        results = asyncio.run(run_phone_collection(args.phone))
        
    # Filter for only positive findings to prevent terminal spam
    positive_results = [res for res in results if res.get('exists') and not res.get('error')]
    
    console.print(f"\n[green]Searched {len(results)} sources. Found {len(positive_results)} positive hits.[/green]")
    
    if positive_results:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Source", style="cyan")
        table.add_column("Result")
        table.add_column("Confidence")
        table.add_column("Status")
        
        for res in positive_results:
            val = res.get('url') or res.get('email') or res.get('phone') or res.get('note') or "Account Found (API Verified)"
            conf = str(res.get('confidence', 'N/A'))
            status = "[green]Found[/green]"
                
            table.add_row(res.get('source', 'Unknown'), val, conf, status)
            
        console.print(table)

if __name__ == "__main__":
    main()
