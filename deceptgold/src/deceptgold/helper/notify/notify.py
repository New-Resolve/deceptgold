from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.configuration.opecanary import get_config_value
from deceptgold.helper.fingerprint import get_machine_fingerprint
from deceptgold.helper.notify.webhook import send_message_custom_webhook
from deceptgold.helper.notify.slack import send_message_webhook_slack
from deceptgold.helper.notify.discord import send_message_webhook_discord
from deceptgold.configuration.config_manager import get_config
import time
from collections import defaultdict

# Global variables for event aggregation and debouncing
_last_notification_time = defaultdict(float)
_event_counters = defaultdict(int)
_DEBOUNCE_SECONDS = 30  # Don't send similar notifications within 30 seconds


def check_send_notify(message, event_data=None):
    fingerprint = get_machine_fingerprint()
    mode = get_config('webhook', 'notify_mode', 'default')
    
    if mode == 'ai':
        if not _check_ai_model_available():
            mode = 'default'
    
    # Apply debouncing for AI notifications to reduce spam
    if mode == 'ai' and event_data:
        # Create a key for debouncing based on attack type and source
        attack_type = event_data.get('attack_type', 'unknown')
        src_host = event_data.get('src_host', 'unknown')
        debounce_key = f"{attack_type}_{src_host}"
        
        current_time = time.time()
        last_time = _last_notification_time[debounce_key]
        
        # Skip if we sent a similar notification recently
        if current_time - last_time < _DEBOUNCE_SECONDS:
            _event_counters[debounce_key] += 1
            return  # Skip this notification
        
        # Generate intelligent AI notification
        message = _generate_ai_notification(event_data)
        
        # Include event count if there were aggregated events
        if _event_counters[debounce_key] > 0:
            count = _event_counters[debounce_key] + 1
            message += f" (x{count} events)"
            _event_counters[debounce_key] = 0
        
        # Update last notification time
        _last_notification_time[debounce_key] = current_time
    
    message = f"{get_config_value('device', 'node_id')} - {message}"

    try:
        # Use markdown formatting for AI notifications to match statistics format
        parse_mode = "Markdown" if mode == 'ai' else None
        send_message_telegram(message, fingerprint, parse_mode=parse_mode)
    except Exception as e:
        raise Exception(f"Error in send message telegram: {e}")

    try:
        send_message_custom_webhook(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message custom webhook: {e}")

    try:
        send_message_webhook_slack(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message slack webhook: {e}")

    try:
        send_message_webhook_discord(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message discord webhook: {e}")


def _check_ai_model_available():
    try:
        from deceptgold.helper.ai_model import check_ai_model_available_silent
        return check_ai_model_available_silent()
    except Exception:
        return False


def _generate_ai_notification(event_data):
    attack_type = event_data.get('attack_type', 'unknown')
    severity = event_data.get('severity', 'medium')
    src_host = event_data.get('src_host', 'unknown')
    service = event_data.get('service', 'unknown')
    logtype = event_data.get('logtype', 0)
    
    try:
        # Use the user's downloaded AI model for real threat intelligence
        ai_analysis = _run_ai_model_inference(attack_type, src_host, service, severity, logtype, event_data)
    except Exception as e:
        # Fallback to intelligent rule-based analysis only if model fails
        ai_analysis = _generate_rule_based_analysis(attack_type, src_host, service, severity, event_data)
    
    # Format the notification in an elegant, standardized way
    return _format_threat_notification(ai_analysis, event_data)


def _format_threat_notification(ai_analysis, event_data):
    """Format threat analysis into an elegant, standardized notification"""
    from deceptgold.configuration.opecanary import get_config_value
    import datetime
    
    # Extract threat level from AI analysis
    threat_level = "MEDIUM"
    if ai_analysis.startswith('['):
        end_bracket = ai_analysis.find(']')
        if end_bracket > 0:
            threat_level = ai_analysis[1:end_bracket]
    
    # Get basic attack information
    attack_type = event_data.get('attack_type', 'unknown').replace('_', ' ').title()
    src_host = event_data.get('src_host', 'unknown')
    service = event_data.get('service', 'unknown')
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Build the formatted notification
    message_lines = [
        f"*Threat Analysis ({timestamp})*",
        f"- *Source IP:* `{src_host}`",
        f"- *Attack Type:* `{attack_type}`",
        f"- *Target Service:* `{service}`",
        f"- *Threat Level:* `{threat_level}`",
        "",
        f"*Analysis:* {ai_analysis}"
    ]
    
    # Add additional context if available
    if event_data.get('username') and event_data.get('password'):
        message_lines.insert(-2, f"- *Credentials:* `{event_data['username']}/{event_data['password']}`")
    
    if event_data.get('dst_port'):
        message_lines.insert(-2, f"- *Target Port:* `{event_data['dst_port']}`")
    
    return "\n".join(message_lines)


def _run_ai_model_inference(attack_type, src_host, service, severity, logtype, event_data):
    """Run inference using the user's downloaded AI model"""
    from deceptgold.helper.ai_model import get_default_model_target_path
    from pathlib import Path
    import subprocess
    import tempfile
    import os
    
    model_path = get_default_model_target_path()
    if not model_path.exists():
        raise Exception("AI model not found")
    
    # Create detailed prompt for the AI model
    additional_context = ""
    if attack_type == "brute_force_login" and event_data:
        username = event_data.get('username', 'unknown')
        password = event_data.get('password', 'unknown')
        additional_context = f"\\nCredentials attempted: {username}/{password}"
    elif event_data.get('logdata'):
        logdata = event_data.get('logdata', {})
        if isinstance(logdata, dict) and logdata:
            additional_context = f"\\nAdditional data: {str(logdata)[:100]}"
    
    prompt = f"""You are an expert cybersecurity threat analyst. Analyze this honeypot attack and provide actionable intelligence.

ATTACK DETAILS:
- Type: {attack_type}
- Source IP: {src_host}
- Target Service: {service}
- Severity Level: {severity}
- Log Type Code: {logtype}{additional_context}

ANALYSIS REQUIREMENTS:
1. Assess the threat level (LOW/MEDIUM/HIGH/CRITICAL)
2. Identify likely attacker motivation and techniques
3. Provide specific actionable recommendations

RESPONSE FORMAT:
[THREAT_LEVEL] Brief threat analysis - Action: specific_security_recommendation

EXAMPLES:
[CRITICAL] SSH brute force using common passwords - Action: Block IP immediately and enable fail2ban
[HIGH] SQL injection attempt detected - Action: Patch database and implement WAF rules
[MEDIUM] Web3 wallet reconnaissance - Action: Monitor for cryptocurrency theft patterns

Provide your analysis now (max 150 characters):"""

    # Create temporary files for input/output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prompt_file:
        prompt_file.write(prompt)
        prompt_path = prompt_file.name
    
    try:
        # Try to use llama-cpp-python if available
        try:
            result = _run_llama_cpp_inference(model_path, prompt)
            if result and len(result.strip()) > 10:
                return result.strip()
        except Exception:
            pass
        
        # Fallback: Try using llama.cpp binary if available
        try:
            result = _run_llama_cpp_binary(model_path, prompt_path)
            if result and len(result.strip()) > 10:
                return result.strip()
        except Exception:
            pass
        
        # If no LLM inference works, raise exception to use fallback
        raise Exception("LLM inference failed")
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(prompt_path)
        except:
            pass


def _run_llama_cpp_inference(model_path, prompt):
    """Try to run inference using llama-cpp-python library"""
    try:
        from llama_cpp import Llama
        
        # Load model with conservative settings for notifications
        llm = Llama(
            model_path=str(model_path),
            n_ctx=512,  # Small context for fast inference
            n_threads=2,  # Limited threads to not block system
            verbose=False
        )
        
        # Generate response with strict limits
        response = llm(
            prompt,
            max_tokens=50,  # Short response for notifications
            temperature=0.3,  # Low temperature for consistent analysis
            top_p=0.9,
            stop=["\\n\\n", "ANALYSIS:", "EXAMPLE:"],
            echo=False
        )
        
        if response and 'choices' in response and len(response['choices']) > 0:
            text = response['choices'][0]['text'].strip()
            # Clean up the response
            if text.startswith('['):
                return text
            else:
                return f"[MEDIUM] {text}"
        
        return None
        
    except ImportError:
        # llama-cpp-python not installed
        return None
    except Exception as e:
        # Model loading or inference failed
        return None


def _run_llama_cpp_binary(model_path, prompt_path):
    """Try to run inference using llama.cpp binary"""
    try:
        import subprocess
        
        # Try common llama.cpp binary locations
        binary_names = ['llama-cli', 'llama', 'main']
        llama_binary = None
        
        for binary in binary_names:
            try:
                result = subprocess.run(['which', binary], capture_output=True, text=True)
                if result.returncode == 0:
                    llama_binary = binary
                    break
            except:
                continue
        
        if not llama_binary:
            return None
        
        # Run inference with strict parameters
        cmd = [
            llama_binary,
            '-m', str(model_path),
            '-f', prompt_path,
            '-n', '50',  # Max 50 tokens
            '-t', '2',   # 2 threads
            '--temp', '0.3',  # Low temperature
            '--top-p', '0.9',
            '--no-display-prompt'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout
        )
        
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            # Clean up the response
            lines = text.split('\\n')
            for line in lines:
                line = line.strip()
                if line and line.startswith('['):
                    return line
            
            # If no formatted line found, format the first meaningful line
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    return f"[MEDIUM] {line}"
        
        return None
        
    except Exception:
        return None


def _generate_rule_based_analysis(attack_type, src_host, service, severity, event_data=None):
    """Generate intelligent threat analysis using rule-based logic"""
    
    # HTTP-based attacks
    if attack_type == "http_probe":
        return f"[LOW] HTTP reconnaissance from {src_host} - Action: Monitor for follow-up exploitation attempts"
    
    elif attack_type == "brute_force_login":
        if event_data:
            username = event_data.get('username', 'unknown')
            password = event_data.get('password', 'unknown')
            service_port = event_data.get('service', 'unknown')
            
            password_analysis = _analyze_password_pattern(password)
            credential_risk = _assess_credential_risk(username, password)
            
            return f"[CRITICAL] Brute force attack from {src_host} targeting {service_port} - Credentials: {username}/{password_analysis} - Risk: {credential_risk} - Action: Block IP immediately"
        else:
            return f"[CRITICAL] HTTP credential attack from {src_host} - Action: Immediate IP blocking and credential rotation"
    
    # Network scanning
    elif attack_type == "port_scan":
        return f"[HIGH] Network reconnaissance from {src_host} - Action: Block IP and monitor for exploitation attempts"
    
    # SSH attacks
    elif attack_type == "ssh_connection":
        return f"[MEDIUM] SSH connection attempt from {src_host} - Action: Monitor for brute force patterns"
    elif attack_type == "ssh_login_attempt":
        return f"[HIGH] SSH login attempt from {src_host} - Action: Strengthen SSH authentication and monitor credentials"
    elif attack_type == "ssh_brute_force":
        return f"[CRITICAL] SSH brute force attack from {src_host} - Action: Block IP immediately and review SSH configuration"
    elif attack_type == "ssh_command_execution":
        return f"[CRITICAL] SSH command execution attempt from {src_host} - Action: Block IP and investigate compromise"
    elif attack_type == "ssh_file_transfer":
        return f"[HIGH] SSH file transfer attempt from {src_host} - Action: Monitor for data exfiltration"
    
    # FTP attacks
    elif attack_type == "ftp_connection":
        return f"[MEDIUM] FTP connection attempt from {src_host} - Action: Monitor for unauthorized access"
    elif attack_type == "ftp_login_attempt":
        return f"[HIGH] FTP login attempt from {src_host} - Action: Review FTP credentials and access controls"
    elif attack_type == "ftp_file_access":
        return f"[HIGH] FTP file access attempt from {src_host} - Action: Monitor for data theft or malware upload"
    
    # Database attacks
    elif attack_type == "database_connection":
        return f"[MEDIUM] Database connection attempt from {src_host} - Action: Monitor for SQL injection patterns"
    elif attack_type == "database_injection_attempt":
        return f"[CRITICAL] SQL injection attempt from {src_host} - Action: Block IP and patch database vulnerabilities"
    elif attack_type == "database_enumeration":
        return f"[HIGH] Database enumeration from {src_host} - Action: Restrict database access and monitor queries"
    
    # Web3/Blockchain attacks
    elif attack_type == "connection_made" and service == "web3_wallet_service":
        return f"[MEDIUM] Web3 wallet service targeted by {src_host} - Action: Analyze for cryptocurrency theft patterns"
    elif attack_type == "data_received" and service == "web3_wallet_service":
        return f"[LOW] Web3 protocol interaction from {src_host} - Action: Analyze payload for wallet exploitation"
    elif "web3" in attack_type or "rpc" in attack_type:
        return f"[HIGH] Web3 blockchain attack from {src_host} - Action: Monitor for cryptocurrency theft attempts"
    elif "wallet" in attack_type:
        return f"[CRITICAL] Cryptocurrency wallet attack from {src_host} - Action: Block IP and secure wallet services"
    elif "defi" in attack_type:
        return f"[HIGH] DeFi protocol attack from {src_host} - Action: Monitor for flash loan and reentrancy attacks"
    elif "nft" in attack_type:
        return f"[MEDIUM] NFT marketplace attack from {src_host} - Action: Monitor for wash trading and approval exploits"
    
    # Generic Web3 attacks
    elif attack_type in ["connection_made", "data_received"]:
        if service == "web3_wallet_service":
            return f"[MEDIUM] Web3 service interaction from {src_host} - Action: Analyze for blockchain exploitation"
        else:
            return f"[LOW] Service interaction from {src_host} - Action: Monitor for suspicious patterns"
    
    # Unknown or new attack types
    elif attack_type.startswith("unknown_logtype_"):
        logtype = attack_type.replace("unknown_logtype_", "")
        return f"[MEDIUM] Unknown attack type {logtype} from {src_host} - Action: Investigate new attack vector and update detection rules"
    
    # Fallback for any other attack types
    else:
        return f"[MEDIUM] {attack_type.upper()} activity from {src_host} - Action: Investigate attack vector and implement countermeasures"


def _analyze_password_pattern(password):
    """Analyze password to identify attack patterns"""
    if not password or password == 'unknown':
        return "unknown_pattern"
    
    password_lower = password.lower()
    
    # Common weak passwords
    common_passwords = ['admin', 'password', '123456', '12345', '1234', 'root', 'guest']
    if password_lower in common_passwords:
        return f"common_weak_password({password})"
    
    # Sequential numbers
    if password.isdigit():
        if len(password) <= 6:
            return f"simple_numeric({password})"
        else:
            return f"long_numeric({len(password)}_digits)"
    
    # Pattern analysis
    if len(password) < 6:
        return f"short_password({password})"
    elif password.isalpha():
        return f"alphabetic_only({len(password)}_chars)"
    elif any(char.isdigit() for char in password) and any(char.isalpha() for char in password):
        return f"alphanumeric({len(password)}_chars)"
    else:
        return f"complex_pattern({len(password)}_chars)"


def _assess_credential_risk(username, password):
    """Assess the risk level of credential combination"""
    if username == 'admin' and password in ['admin', 'password', '123456']:
        return "EXTREME_default_admin_credentials"
    elif username in ['admin', 'root', 'administrator']:
        return "HIGH_privileged_account_targeted"
    elif password in ['admin', 'password', '123456', '12345', '1234']:
        return "HIGH_common_password_used"
    else:
        return "MEDIUM_custom_credentials_attempted"
