Slack History Exporter
======================

This script dumps listed Slack private channels and prepares
Slack-compatible import bundle.

### Getting Slack API token

You can get get Slack API token [here](https://api.slack.com/custom-integrations/legacy-tokens).

### Usage

Run locally

```
pip install -r requirements.txt
python slack.py --token <slack API token> [--output <zip file path>] <private channels>
```

Run in Docker

```
docker build -t velovec/slack-exporter:0.1 .
docker run -it --rm -v $(pwd):/slack velovec/slack-exporter:0.1 --token <slack API token> <private channels>
```