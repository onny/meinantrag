#!/usr/bin/env python3
import imaplib2
import smtplib
import yaml
import json
import os
import threading
import argparse
from email.mime.text import MIMEText
from datetime import datetime, timedelta

CONFIG_FILE = "config.yml"
STATE_FILE = "quota_state.json"

# TODO
# - load config from file
# - override with env vars

def get_config_value(config, env_var, config_key, default_value, value_type=int):
    """Get configuration value from environment variable or config file, with fallback to default"""
    env_value = os.environ.get(env_var)
    if env_value is not None:
        try:
            return value_type(env_value)
        except ValueError:
            log(f"Invalid value for {env_var}: {env_value}, using config/default")
    
    return config.get(config_key, default_value)

def parse_args():
    parser = argparse.ArgumentParser(description="Email quota monitoring script")
    parser.add_argument(
        "--config", 
        default="config.yml",
        help="Path to config.yml file (default: config.yml in current directory)"
    )
    return parser.parse_args()

def load_config(config_file):
    if not os.path.exists(config_file):
        log(f"Config file not found: {config_file}")
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, "r") as f:
        return yaml.safe_load(f)

def load_state():
    state_file = "quota_state.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    state_file = "quota_state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def format_bytes(kb):
    """Convert KB to human readable format"""
    if kb >= 1024 * 1024:  # GB
        return f"{kb / (1024 * 1024):.1f} GB"
    elif kb >= 1024:  # MB
        return f"{kb / 1024:.1f} MB"
    else:  # KB
        return f"{kb} KB"

def check_quota(account):
    """
    Uses IMAP QUOTA command (RFC 2087) to get mailbox usage with imaplib2.
    Tries multiple approaches to get quota information.
    Returns dict with quota info or None if not supported.
    """
    try:
        log(f"Checking quota for account: {account['name']} ({account['username']})")
        
        # Create imaplib2 connection
        mail = imaplib2.IMAP4_SSL(account['imap_server'], account['imap_port'])
        
        # Login
        typ, data = mail.login(account['username'], account['password'])
        if typ != 'OK':
            log(f"Login failed for {account['name']}: {data}")
            return None
        
        # Try different quota roots (quietly)
        quota_roots = ["INBOX", account['username'], f"user/{account['username']}", f"user.{account['username']}"]
        
        for quota_root in quota_roots:
            try:
                typ, data = mail.getquota(quota_root)
                
                if typ == "OK" and data and data[0]:
                    # Parse quota response
                    quota_info = data[0].decode() if isinstance(data[0], bytes) else str(data[0])
                    
                    # Handle different response formats
                    # Format 1: (STORAGE used limit) or (MESSAGE used limit)
                    if quota_info.startswith('('):
                        parts = quota_info.replace("(", "").replace(")", "").split()
                        if len(parts) >= 3:
                            resource_type = parts[0]  # STORAGE or MESSAGE
                            used = int(parts[1])
                            limit = int(parts[2])
                            
                            if limit > 0 and resource_type == "STORAGE":
                                percent_used = (used / limit) * 100
                                log(f"Quota usage: {percent_used:.1f}% ({format_bytes(used)} of {format_bytes(limit)})")
                                mail.logout()
                                return {
                                    'percent_used': percent_used,
                                    'used_kb': used,
                                    'limit_kb': limit
                                }
                    
                    # Format 2: Multiple resources in one response
                    elif "STORAGE" in quota_info:
                        import re
                        storage_match = re.search(r'STORAGE\s+(\d+)\s+(\d+)', quota_info)
                        if storage_match:
                            used = int(storage_match.group(1))
                            limit = int(storage_match.group(2))
                            if limit > 0:
                                percent_used = (used / limit) * 100
                                log(f"Quota usage: {percent_used:.1f}% ({format_bytes(used)} of {format_bytes(limit)})")
                                mail.logout()
                                return {
                                    'percent_used': percent_used,
                                    'used_kb': used,
                                    'limit_kb': limit
                                }
                
            except imaplib2.IMAP4.error:
                # Silently try next quota root
                continue
        
        # Try GETQUOTAROOT command as alternative
        try:
            typ, data = mail.getquotaroot("INBOX")
            if typ == "OK" and data:
                # Parse quotaroot response which might give us quota info
                for item in data:
                    item_str = item.decode() if isinstance(item, bytes) else str(item)
                    if "STORAGE" in item_str:
                        import re
                        storage_match = re.search(r'STORAGE\s+(\d+)\s+(\d+)', item_str)
                        if storage_match:
                            used = int(storage_match.group(1))
                            limit = int(storage_match.group(2))
                            if limit > 0:
                                percent_used = (used / limit) * 100
                                log(f"Quota usage: {percent_used:.1f}% ({format_bytes(used)} of {format_bytes(limit)})")
                                mail.logout()
                                return {
                                    'percent_used': percent_used,
                                    'used_kb': used,
                                    'limit_kb': limit
                                }
        except imaplib2.IMAP4.error:
            pass
        
        mail.logout()
        log(f"No quota data available for {account['name']}")
        return None
        
    except imaplib2.IMAP4.error as e:
        log(f"IMAP error checking quota for {account['name']}: {e}")
    except Exception as e:
        log(f"Error checking quota for {account['name']}: {e}")
    
    return None

def should_send_warning(state, account_name, interval_days):
    last_sent_str = state.get(account_name)
    if not last_sent_str:
        return True
    
    last_sent = datetime.fromisoformat(last_sent_str)
    return datetime.now() - last_sent >= timedelta(days=interval_days)

def send_warning(config, triggered_accounts, all_quotas, threshold):
    mail_cfg = config["mail"]
    
    # Create subject based on number of accounts
    if len(triggered_accounts) == 1:
        account_name, quota_info = list(triggered_accounts.items())[0]
        subject = f"[Quota Warning] {account_name} mailbox usage at {quota_info['percent_used']:.1f}%"
    else:
        subject = f"[Quota Warning] {len(triggered_accounts)} mailbox(es) over threshold"
    
    # Build email body
    body_lines = []
    
    if len(triggered_accounts) == 1:
        account_name, quota_info = list(triggered_accounts.items())[0]
        body_lines.append(f"The mailbox for account '{account_name}' has reached {quota_info['percent_used']:.1f}% of its quota.")
        body_lines.append(f"Usage: {format_bytes(quota_info['used_kb'])} of {format_bytes(quota_info['limit_kb'])}")
    else:
        body_lines.append(f"The following mailboxes have exceeded the quota threshold ({threshold}%):")
        body_lines.append("")
        for account_name, quota_info in triggered_accounts.items():
            body_lines.append(f"• {account_name}: {quota_info['percent_used']:.1f}% ({format_bytes(quota_info['used_kb'])} of {format_bytes(quota_info['limit_kb'])})")
    
    body_lines.append("")
    body_lines.append("--- All Account Summary ---")
    
    # Sort accounts by usage percentage (descending)
    sorted_quotas = sorted(all_quotas.items(), key=lambda x: x[1]['percent_used'] if x[1] else 0, reverse=True)
    
    for account_name, quota_info in sorted_quotas:
        if quota_info:
            status = "⚠️ " if account_name in triggered_accounts else "✓ "
            body_lines.append(f"{status}{account_name}: {quota_info['percent_used']:.1f}% ({format_bytes(quota_info['used_kb'])} of {format_bytes(quota_info['limit_kb'])})")
        else:
            body_lines.append(f"? {account_name}: Quota info unavailable")
    
    body_lines.append("")
    body_lines.append("Please take action to free up space for accounts over the threshold.")
    
    body = "\n".join(body_lines)
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = mail_cfg["from_address"]
    msg["To"] = ", ".join(mail_cfg["recipients"])
    
    try:
        server = smtplib.SMTP(mail_cfg["smtp_server"], mail_cfg["smtp_port"])
        server.starttls()
        server.login(mail_cfg["smtp_username"], mail_cfg["smtp_password"])
        server.sendmail(mail_cfg["from_address"], mail_cfg["recipients"], msg.as_string())
        server.quit()
        account_names = ", ".join(triggered_accounts.keys())
        log(f"Warning email sent for: {account_names}")
    except Exception as e:
        log(f"Error sending warning email: {e}")

def check_account_quota(account, config, state, threshold, interval_days):
    """
    Check quota for a single account (can be run in thread)
    """
    quota_info = check_quota(account)
    if quota_info is None:
        log(f"Quota info not available for {account['name']}")
        return None, None
    
    percent_used = quota_info['percent_used']
    
    if percent_used >= threshold:
        if should_send_warning(state, account["name"], interval_days):
            return account["name"], quota_info
        else:
            log(f"Warning already sent recently for {account['name']}, skipping.")
    else:
        log(f"Quota usage for {account['name']} is below threshold ({percent_used:.1f}%).")
    
    return None, quota_info

def main():
    args = parse_args()
    config = load_config(args.config)
    state = load_state()
    interval_days = get_config_value(config, "CHECK_INTERVAL_DAYS", "check_interval_days", 7, int)
    threshold = get_config_value(config, "QUOTA_WARNING_THRESHOLD_PERCENT", "quota_warning_threshold_percent", 80, int)
    
    # For thread-safe state updates
    state_lock = threading.Lock()
    
    # Track all accounts and those that need warnings
    triggered_accounts = {}  # account_name: quota_info
    all_quotas = {}  # account_name: quota_info (or None)
    
    for account in config["accounts"]:
        warning_result, quota_info = check_account_quota(account, config, state, threshold, interval_days)
        
        # Store quota info for summary
        all_quotas[account["name"]] = quota_info
        
        # Track accounts that need warnings
        if warning_result:
            triggered_accounts[account["name"]] = quota_info
            with state_lock:
                state[account["name"]] = datetime.now().isoformat()
    
    # Send consolidated warning email if any accounts triggered
    if triggered_accounts:
        send_warning(config, triggered_accounts, all_quotas, threshold)
    
    save_state(state)

if __name__ == "__main__":
    main()
