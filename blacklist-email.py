import os
import time
from datetime import datetime, timedelta
from typing import Iterable, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

SOURCE_URLS = [
    "https://raw.githubusercontent.com/disposable/disposable-email-domains/refs/heads/master/domains.txt",
    "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/refs/heads/main/disposable_email_blocklist.conf",
    "https://raw.githubusercontent.com/7c/fakefilter/refs/heads/main/txt/data.txt",
    "https://raw.githubusercontent.com/wesbos/burner-email-providers/refs/heads/master/emails.txt",
]
ALLOWLIST_URL = "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/refs/heads/main/allowlist.conf"
REFRESH_MINUTES = 30
OUTPUT_FILENAME = "output.txt"


def log(message: str, level: str = "INFO") -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def resolve_path(filename: str) -> str:
    """Convert a filename into an absolute path next to this script."""
    return os.path.join(os.path.dirname(__file__), filename)


def normalize_domain(entry: str) -> str:
    """Normalize raw entries into lowercase domain names."""
    domain = entry.strip()
    if not domain:
        return ""
    domain = domain.replace("## ", "")
    if domain.startswith("#"):
        return ""
    if "#" in domain:
        domain = domain.split("#", 1)[0].strip()
    if not domain:
        return ""
    if "@" in domain:
        domain = domain.split("@", 1)[1]
    cleaned = ".".join(segment for segment in domain.split(".") if segment)
    if not cleaned:
        return ""
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = ".".join(parts[-2:])
    return cleaned.lower()


def load_existing_domains(output_path: str) -> Set[str]:
    """Read domains from disk and normalize entries."""
    domains: Set[str] = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as file:
            for line in file:
                domain = normalize_domain(line)
                if domain:
                    domains.add(domain)
    return domains


def fetch_domains_from_url(url: str) -> Set[str]:
    """Download domains from a single source URL."""
    domains: Set[str] = set()
    try:
        with urlopen(url, timeout=30) as response:
            for raw_line in response:
                domain = normalize_domain(raw_line.decode("utf-8", errors="ignore"))
                if domain:
                    domains.add(domain)
    except (HTTPError, URLError, OSError) as exc:
        log(f"Unable to load {url}: {exc}", "WARN")
    return domains


def fetch_multiple_sources(urls: Iterable[str]) -> Set[str]:
    """Aggregate normalized domains from all configured URLs."""
    aggregated: Set[str] = set()
    for url in urls:
        aggregated |= fetch_domains_from_url(url)
    return aggregated


def apply_allowlist(domains: Set[str], allowlist: Set[str]) -> Tuple[Set[str], int]:
    """Remove allowlisted domains and return the filtered set with removal count."""
    if not domains or not allowlist:
        return set(domains), 0
    filtered = domains - allowlist
    return filtered, len(domains) - len(filtered)


def write_domains(domains: Set[str], output_path: str) -> None:
    """Persist domains to disk in sorted order."""
    with open(output_path, "w", encoding="utf-8") as file:
        for domain in sorted(domains):
            file.write(f"{domain}\n")


def process_sources(urls: Iterable[str], output_filename: str) -> int:
    """Synchronize output with remote sources while honoring the allowlist."""
    output_path = resolve_path(output_filename)
    persisted_domains = load_existing_domains(output_path)

    allowlist_domains = fetch_domains_from_url(ALLOWLIST_URL) if ALLOWLIST_URL else set()
    if ALLOWLIST_URL and not allowlist_domains:
        log("Allowlist retrieval returned no entries; verification skipped.", "WARN")

    sanitized_existing, removed_existing = apply_allowlist(persisted_domains, allowlist_domains)
    if removed_existing:
        log(f"Removed {removed_existing} allowlisted domains from existing output.")

    fetched_domains = fetch_multiple_sources(urls)
    filtered_fetched, skipped = apply_allowlist(fetched_domains, allowlist_domains)
    if skipped:
        log(f"Skipped {skipped} domains because they are explicitly allowlisted.")

    if not filtered_fetched and not removed_existing:
        log("No domains fetched; output file unchanged.")
        return 0

    new_domains = filtered_fetched - sanitized_existing
    final_domains = sanitized_existing | filtered_fetched

    if final_domains != persisted_domains:
        write_domains(final_domains, output_path)
        if new_domains:
            log(f"Added {len(new_domains)} new disposable domains.")
        elif removed_existing:
            log("Output refreshed after removing allowlisted domains.")
    else:
        log("No new domains detected.")
    return len(new_domains)


def monitor_sources(urls: Iterable[str], output_filename: str, interval_minutes: int = 30) -> None:
    """Continuously refresh the disposable domain list at the configured interval."""
    interval_seconds = max(1, int(interval_minutes * 60))
    while True:
        process_sources(urls, output_filename)
        next_run = datetime.now() + timedelta(seconds=interval_seconds)
        log(f"Next check at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            log("Monitoring stopped by user.")
            break


if __name__ == "__main__":
    try:
        monitor_sources(SOURCE_URLS, OUTPUT_FILENAME, REFRESH_MINUTES)
    except KeyboardInterrupt:
        log("Monitoring stopped by user.")