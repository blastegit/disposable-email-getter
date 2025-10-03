# Disposable Email Domain Aggregator

This script consolidates disposable email domains from several public blocklists, removes any domains explicitly allowlisted, and writes the cleaned list to `output.txt`. It can also monitor the sources on an interval to keep the list fresh.

## Prerequisites
- Python 3.8 or newer
- Internet access (the script downloads source lists on each run)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```

2. **Run a one-time sync**
   ```bash
   python blacklist-email.py
   ```

   The script downloads domains, applies the allowlist from `ALLOWLIST_URL`, and saves the final set to `output.txt`.

## Continuous Monitoring

To keep the list updated automatically (default: every 30 minutes), let the script run without interruption:

```bash
python blacklist-email.py
```

Press `Ctrl+C` to stop monitoring. Each cycle logs progress and shows the next scheduled refresh time.

## Customization

- **Source URLs**: adjust `SOURCE_URLS` to add or remove domain feeds.
- **Allowlist**: set `ALLOWLIST_URL` to your own allowlist or to `None` to skip allowlisting.
- **Refresh Interval**: change `REFRESH_MINUTES` to suit your update frequency.

## Output

- `output.txt`: sorted list of normalized disposable domains.
- Console logs: timestamped messages showing fetch status, additions, and skipped allowlisted domains.

Feel free to open issues or submit pull requests with improvements or new source suggestions.
