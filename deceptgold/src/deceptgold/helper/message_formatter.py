"""
Centralized message formatting utility for DeceptGold.
Provides consistent boxed message formatting across the entire application.
"""

from typing import List, Optional
import textwrap


class MessageFormatter:
    """Centralized utility for creating elegant boxed messages."""
    
    # Box drawing characters
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    CROSS = "╬"
    T_DOWN = "╦"
    T_UP = "╩"
    T_RIGHT = "╠"
    T_LEFT = "╣"
    
    # Standard box width
    BOX_WIDTH = 62  # Content width inside the box
    TOTAL_WIDTH = 66  # Total width including borders
    
    @classmethod
    def create_box(
        cls,
        title: str,
        content_lines: List[str],
        include_separator: bool = True,
        footer_lines: Optional[List[str]] = None
    ) -> str:
        """
        Create a formatted box message.
        
        Args:
            title: The title to display in the header
            content_lines: List of content lines to display
            include_separator: Whether to include a separator after the title
            footer_lines: Optional footer lines to display at the bottom
            
        Returns:
            Formatted box message as a string
        """
        lines = []
        
        # Top border
        lines.append(f"{cls.TOP_LEFT}{cls.HORIZONTAL * cls.BOX_WIDTH}{cls.TOP_RIGHT}")
        
        # Title
        title_padded = cls._center_text(title, cls.BOX_WIDTH)
        lines.append(f"{cls.VERTICAL}{title_padded}{cls.VERTICAL}")
        
        # Separator
        if include_separator:
            lines.append(f"{cls.T_RIGHT}{cls.HORIZONTAL * cls.BOX_WIDTH}{cls.T_LEFT}")
        
        # Content
        for line in content_lines:
            if line.strip() == "":
                # Empty line
                lines.append(f"{cls.VERTICAL}{' ' * cls.BOX_WIDTH}{cls.VERTICAL}")
            else:
                # Content line(s) (auto-wrap to keep borders aligned)
                for wrapped_line in cls._wrap_text(line, cls.BOX_WIDTH):
                    padded_line = cls._pad_text(wrapped_line, cls.BOX_WIDTH)
                    lines.append(f"{cls.VERTICAL}{padded_line}{cls.VERTICAL}")
        
        # Footer separator and content
        if footer_lines:
            lines.append(f"{cls.T_RIGHT}{cls.HORIZONTAL * cls.BOX_WIDTH}{cls.T_LEFT}")
            for line in footer_lines:
                if line.strip() == "":
                    lines.append(f"{cls.VERTICAL}{' ' * cls.BOX_WIDTH}{cls.VERTICAL}")
                else:
                    for wrapped_line in cls._wrap_text(line, cls.BOX_WIDTH):
                        padded_line = cls._pad_text(wrapped_line, cls.BOX_WIDTH)
                        lines.append(f"{cls.VERTICAL}{padded_line}{cls.VERTICAL}")
        
        # Bottom border
        lines.append(f"{cls.BOTTOM_LEFT}{cls.HORIZONTAL * cls.BOX_WIDTH}{cls.BOTTOM_RIGHT}")
        
        return "\n" + "\n".join(lines) + "\n"
    
    @classmethod
    def _center_text(cls, text: str, width: int) -> str:
        """Center text within the given width."""
        text = text.strip()
        if len(text) >= width:
            return text[:width]
        
        padding = width - len(text)
        left_pad = padding // 2
        right_pad = padding - left_pad
        return " " * left_pad + text + " " * right_pad
    
    @classmethod
    def _pad_text(cls, text: str, width: int) -> str:
        """Pad text to the given width, handling dynamic content."""
        text = text.rstrip()
        if len(text) >= width:
            return text[:width]
        
        # For lines that start with spaces (indented content), preserve the indentation
        if text.startswith("  "):
            return text + " " * (width - len(text))
        else:
            return text + " " * (width - len(text))


    @classmethod
    def _wrap_text(cls, text: str, width: int) -> List[str]:
        """Wrap text to fit inside the box width, preserving indentation when present."""
        if text is None:
            return [""]

        raw = str(text).rstrip("\n")
        if raw.strip() == "":
            return [""]

        indent_len = len(raw) - len(raw.lstrip(" "))
        indent = " " * indent_len

        content = raw.lstrip(" ")

        wrapped = textwrap.wrap(
            content,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
            initial_indent=indent if indent_len > 0 else "",
            subsequent_indent=indent if indent_len > 0 else "",
        )

        return wrapped if wrapped else [""]


# Predefined message templates for common scenarios
class MessageTemplates:
    """Predefined message templates for common DeceptGold scenarios."""
    
    @staticmethod
    def ai_models_not_installed() -> str:
        """Message when AI models are not installed."""
        return MessageFormatter.create_box(
            title="AI MODELS NOT INSTALLED",
            content_lines=[
                "The AI log follower requires an AI model to be installed.",
                "",
                "WHAT THIS COMMAND DOES:",
                "• Monitors honeypot logs in real-time",
                "• Enriches events with AI-powered analysis",
                "• Categorizes attacks and assesses severity",
                "• Provides actionable security recommendations",
                "",
                "INSTALL AI MODEL FIRST:",
                "deceptgold ai install-model",
                "",
                "THEN START AI FOLLOWER:",
                "deceptgold ai start",
                "",
                "ALTERNATIVE: Run without AI analysis",
                "If you just want to tail logs without AI, use:",
                "tail -f /tmp/.deceptgold.log"
            ]
        )
    
    @staticmethod
    def ai_mode_model_not_found(embedded_dir: str) -> str:
        """Message when AI mode is enabled but model not found."""
        return MessageFormatter.create_box(
            title="AI MODE - MODEL NOT FOUND",
            content_lines=[
                "Local AI is enabled, but no GGUF model was found.",
                "",
                "TO USE AI FEATURES:",
                "You must install a local AI model first.",
                "",
                "INSTALL AI MODEL:",
                "deceptgold ai install-model",
                "",
                "ALTERNATIVE OPTIONS:",
                "• Pass model=/path/to/model.gguf",
                "• Install manually to ~/.deceptgold/models/",
                "",
                f"Embedded directory: {embedded_dir}"
            ]
        )
    
    @staticmethod
    def ai_log_follower_ready(log_path: str) -> str:
        """Message when AI log follower is ready and service started."""
        return MessageFormatter.create_box(
            title="AI LOG FOLLOWER - READY FOR ACTION",
            content_lines=[
                "The AI log follower is now active and monitoring!",
                "",
                "STATUS: Service started successfully",
                "MONITORING: Real-time log analysis enabled",
                "AI ENGINE: Ready to analyze security events",
                "",
                "WHAT HAPPENS NEXT:",
                "• Honeypot will create the log file automatically",
                "• AI will start streaming analysis as events occur",
                "• Each attack will be enriched with intelligence",
                "",
                "GENERATE SOME TRAFFIC:",
                "• Visit your honeypot in a browser",
                "• Try some login attempts",
                "• Run a port scan against it",
                "",
                f"Waiting for: {log_path}"
            ]
        )
    
    @staticmethod
    def ai_models_unavailable() -> str:
        """Message when no AI models are available for installation."""
        return MessageFormatter.create_box(
            title="DECEPTGOLD AI MODELS - UNAVAILABLE",
            content_lines=[
                "No AI models are currently available for installation.",
                "",
                "WHY YOU NEED AI MODELS:",
                "• Transform raw attack data into intelligent insights",
                "• Get real-time threat analysis and recommendations",
                "• Receive predictive security alerts",
                "• Automatic attack pattern recognition",
                "",
                "POSSIBLE SOLUTIONS:",
                "• Ensure you're using an official DeceptGold release",
                "• Check if model manifest is packaged correctly",
                "• Download GGUF model manually and configure path",
                "",
                "MANUAL SETUP:",
                "deceptgold ai install-model filename=custom.gguf"
            ]
        )
    
    @staticmethod
    def ai_models_choose_intelligence() -> str:
        """Message for choosing AI intelligence level."""
        return MessageFormatter.create_box(
            title="DECEPTGOLD AI MODELS - CHOOSE YOUR INTELLIGENCE",
            content_lines=[
                "Upgrade your honeypot with AI-powered threat intelligence!",
                "",
                "AVAILABLE MODELS:",
                "• Fast & Lightweight: Quick analysis, minimal resources",
                "• Balanced: Smart analysis with good performance",
                "• Advanced: Deep analysis, detailed insights",
                "",
                "BENEFITS OF AI NOTIFICATIONS:",
                "• Attack categorization (Brute Force, Scanning, Web3)",
                "• Severity assessment with risk scoring",
                "• Actionable security recommendations",
                "• Pattern recognition across multiple events"
            ]
        )
    
    @staticmethod
    def non_interactive_mode_detected() -> str:
        """Message for non-interactive mode detection."""
        return MessageFormatter.create_box(
            title="NON-INTERACTIVE MODE DETECTED",
            content_lines=[
                "For automated installations, use one of these methods:",
                "",
                "EMBEDDED MODEL:",
                "deceptgold ai install-model filename=model.gguf",
                "",
                "CUSTOM MODEL:",
                "• Set environment: DECEPTGOLD_AI_MODEL=<model_key>",
                "• Or configure: ai.model_path=/path/to/model.gguf",
                "",
                "TIP: Run interactively first to see available models"
            ]
        )
    
    @staticmethod
    def ai_models_list_and_selection(models: list) -> str:
        """Message for listing available models and selection instructions."""
        content_lines = [
            "Choose an AI model to install for threat intelligence:",
            "",
            "AVAILABLE MODELS:"
        ]
        
        for i, m in enumerate(models, start=1):
            key = str(m.get("key") or "").strip()
            fname = str(m.get("filename") or "").strip()
            installed = bool(m.get("installed"))
            status = "INSTALLED" if installed else "AVAILABLE"
            
            # Get model descriptions from manifest data (no hardcoding)
            specialty = str(m.get("specialty") or "General AI analysis").strip()
            use_case = str(m.get("use_case") or "Best for: General security analysis").strip()
            description = str(m.get("description") or "AI model for security analysis").strip()
            
            content_lines.extend([
                f"{i}) {key.upper()} - {status}",
                f"   Specialty: {specialty}",
                f"   {use_case}",
                f"   File: {fname}",
                ""
            ])
        
        content_lines.extend([
            "WHAT AI MODELS PROVIDE:",
            "• Automated security report generation",
            "• Real-time attack pattern recognition",
            "• Offensive cybersecurity threat analysis",
            "• Actionable incident response recommendations",
            "",
            "EXAMPLE AI CAPABILITIES:",
            "• Generate detailed attack analysis reports",
            "• Identify advanced persistent threat patterns",
            "• Provide cybersecurity remediation strategies",
            "",
            f"{len(models) + 1}) SKIP - Continue without AI models"
        ])
        
        return MessageFormatter.create_box(
            title="DECEPTGOLD AI MODELS - SELECT YOUR SPECIALIST",
            content_lines=content_lines
        )
    
    @staticmethod
    def select_ai_intelligence_level() -> str:
        """Message for selecting AI intelligence level."""
        return MessageFormatter.create_box(
            title="SELECT YOUR AI INTELLIGENCE LEVEL",
            content_lines=[
                "Choose the AI model that best fits your security needs:",
                "",
                "FAST:     Real-time protection, minimal resources",
                "BALANCED: Smart analysis, optimal performance", 
                "ADVANCED: Deep insights, maximum intelligence"
            ]
        )
    
    @staticmethod
    def notify_default_mode() -> str:
        """Message for default notification mode."""
        return MessageFormatter.create_box(
            title="DEFAULT MODE - ESSENTIAL NOTIFICATIONS",
            content_lines=[
                "You'll receive essential system notifications only.",
                "",
                "WHAT YOU'LL RECEIVE:",
                "• Service start/stop events",
                "• Configuration changes",
                "• Blockchain reward transactions",
                "• System status updates",
                "",
                "NOTE: For intelligent threat analysis, upgrade to AI:",
                "deceptgold notify --mode=ai",
                "",
                "EXAMPLE DEFAULT NOTIFICATIONS:",
                "node-01 - Deceptgold has been initialized",
                "node-01 - Transaction confirmed in block: 12345",
                "node-01 - Deceptgold has been finalized"
            ]
        )
    
    @staticmethod
    def notify_ai_mode_intelligence_required() -> str:
        """Message when AI mode requires intelligence model."""
        return MessageFormatter.create_box(
            title="AI MODE - INTELLIGENCE REQUIRED",
            content_lines=[
                "AI notifications require an installed intelligence model.",
                "",
                "UNLOCK AI POWER:",
                "• Transform raw logs into intelligent threat analysis",
                "• Get real-time attack categorization and severity",
                "• Receive actionable security recommendations",
                "• Automatic pattern recognition across events",
                "",
                "ACTIVATE AI INTELLIGENCE:",
                "deceptgold ai install-model",
                "",
                "WHAT YOU'LL GET WITH AI:",
                "• CRITICAL: Immediate threats requiring action",
                "• ANALYSIS: Attack patterns and TTPs",
                "• INTELLIGENCE: Actor attribution and motivation",
                "• ACTIONS: Specific mitigation steps",
                "",
                "AVAILABLE INTELLIGENCE LEVELS:",
                "• Fast: Real-time protection, minimal resources",
                "• Balanced: Smart analysis, optimal performance",
                "• Advanced: Deep insights, maximum intelligence"
            ]
        )
    
    @staticmethod
    def notify_ai_mode_activated() -> str:
        """Message when AI mode is successfully activated."""
        return MessageFormatter.create_box(
            title="AI MODE ACTIVATED - INTELLIGENCE ONLINE",
            content_lines=[
                "Your honeypot now has AI-powered threat intelligence!",
                "",
                "AI NOTIFICATIONS ENABLED:",
                "• Attack categorization with severity scoring",
                "• Pattern recognition across multiple events",
                "• Actionable security recommendations",
                "• Real-time threat analysis and intelligence",
                "",
                "NEXT STEPS:",
                "1. Start your honeypot: deceptgold service start",
                "2. Generate some traffic or wait for attacks",
                "3. Watch your Telegram for intelligent alerts",
                "",
                "EXAMPLE AI ALERTS YOU'LL RECEIVE:",
                "node-01 - [CRITICAL] Brute force attack detected",
                "node-01 - [ANALYSIS] SSH credential stuffing pattern",
                "node-01 - [ACTIONS] Block IP 192.168.1.100 temporarily"
            ]
        )
    
    @staticmethod
    def ai_model_installed_onboarding() -> str:
        """Onboarding message after AI model installation."""
        return MessageFormatter.create_box(
            title="AI MODEL INSTALLED SUCCESSFULLY",
            content_lines=[
                "Congratulations! Your AI model is now ready for threat intelligence.",
                "",
                "RECOMMENDED SETUP:",
                "To get the most out of your AI-powered honeypot, we recommend",
                "configuring intelligent notifications.",
                "",
                "STEP 1: Configure AI Notifications",
                "This will enable smart threat analysis and actionable alerts.",
                "",
                "STEP 2: Set up Notification Channels", 
                "Configure Telegram, Slack, or Discord for receiving alerts.",
                "",
                "Would you like to configure AI notifications now?",
                "This will automatically enable AI-powered threat analysis."
            ]
        )
    
    @staticmethod
    def onboarding_notification_setup() -> str:
        """Guide user through notification setup."""
        return MessageFormatter.create_box(
            title="NOTIFICATION SETUP GUIDE",
            content_lines=[
                "Let's configure your notification channels for AI alerts.",
                "",
                "AVAILABLE NOTIFICATION METHODS:",
                "• Telegram Bot (Recommended)",
                "• Slack Webhook",
                "• Discord Webhook", 
                "• Custom Webhook",
                "",
                "TELEGRAM SETUP (Most Popular):",
                "1. Create a Telegram bot with @BotFather",
                "2. Get your bot token and chat ID",
                "3. Configure: deceptgold user --telegram-token YOUR_TOKEN",
                "4. Configure: deceptgold user --telegram-chat-id YOUR_CHAT_ID",
                "",
                "After setup, run: deceptgold notify --mode=ai",
                "Then start your honeypot: deceptgold service start"
            ]
        )
    
    @staticmethod
    def onboarding_complete() -> str:
        """Final onboarding completion message."""
        return MessageFormatter.create_box(
            title="SETUP COMPLETE - READY FOR INTELLIGENT THREAT DETECTION",
            content_lines=[
                "Your DeceptGold honeypot is now fully configured with AI!",
                "",
                "WHAT'S CONFIGURED:",
                "• AI model installed and ready for inference",
                "• Intelligent notification mode enabled",
                "• Real-time threat analysis using your chosen model",
                "",
                "AI MODEL REQUIREMENTS:",
                "For optimal performance, install: pip install llama-cpp-python",
                "This enables direct model inference for threat analysis.",
                "",
                "FINAL STEPS:",
                "1. Install AI library: pip install llama-cpp-python",
                "2. Start honeypot: deceptgold service start",
                "3. Monitor your notification channels for AI-powered alerts",
                "",
                "EXAMPLE AI-GENERATED ALERTS:",
                "• [CRITICAL] SSH brute force from 192.168.1.100 - Block IP immediately",
                "• [HIGH] SQL injection attempt - Patch database vulnerabilities", 
                "• [MEDIUM] Web3 wallet probing - Monitor cryptocurrency theft patterns",
                "",
                "Your honeypot now uses real AI for threat intelligence!"
            ]
        )
