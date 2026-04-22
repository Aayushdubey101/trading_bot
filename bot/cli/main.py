import argparse
import uvicorn
import sys
from ..core.config import settings
from ..core.logging import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Quant Trading System CLI")
    parser.add_argument("command", choices=["serve"], help="Command to run")
    parser.add_argument("--host", default=settings.api_host, help="API Host")
    parser.add_argument("--port", type=int, default=settings.api_port, help="API Port")
    
    args = parser.parse_args()
    
    # Initialize logging
    setup_logging()
    
    if args.command == "serve":
        print(f"Starting API Server on {args.host}:{args.port}")
        uvicorn.run("bot.api.server:app", host=args.host, port=args.port, log_level=settings.log_level.lower())
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
