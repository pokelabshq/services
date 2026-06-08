# Poke CLI — Service Management Tool

## What it does
Command-line tool to list, start, stop, restart, and check status of all Poke Labs services.
One tool to rule them all.

## Usage
```bash
# List all services with status
python3 /home/alx/services/cli/poke.py list

# Start all services
python3 /home/alx/services/cli/poke.py start all

# Start one service
python3 /home/alx/services/cli/poke.py start poke-hub

# Stop everything
python3 /home/alx/services/cli/poke.py stop all

# Restart a service
python3 /home/alx/services/cli/poke.py restart health-aggregator

# Check status
python3 /home/alx/services/cli/poke.py status
python3 /home/alx/services/cli/poke.py status poke-hub

# View logs
python3 /home/alx/services/cli/poke.py logs poke-hub

# Health summary with uptime bar
python3 /home/alx/services/cli/poke.py health

# Dashboard URL
python3 /home/alx/services/cli/poke.py dashboard
```

## Services managed
| Service | Port | Description |
|---------|------|-------------|
| link-preview | 8765 | URL metadata API |
| pokelabs-site | 8766 | Landing page |
| poke-bot | 8770 | GitHub auto-triage |
| poke-hub | 8775 | GitHub all-in-one |
| telegram-bot | 8777 | Telegram integration |
| skills-hub | 8780 | Skills directory |
| skills-marketplace | 8781 | Skills marketplace v2 |
| registry | 8785 | Agent registry |
| billing | 8795 | Billing service |
| health-aggregator | 8799 | Health monitoring |

## Dependencies
Zero — Python stdlib only.
