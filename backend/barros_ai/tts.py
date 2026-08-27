from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import escape

from .providers import ProviderError, ProviderSettings


@dataclass(frozen=True, slots=True)
class AgentVoice:
    agent: str
    voice: str
    locale: str
    label: str
    gender: str = ""


VOICE_LIBRARY = (
    AgentVoice("", "en-US-AvaNeural", "en-US", "Ava · US", "female"),
    AgentVoice("", "en-US-AndrewNeural", "en-US", "Andrew · US", "male"),
    AgentVoice("", "en-US-JennyNeural", "en-US", "Jenny · US", "female"),
    AgentVoice("", "en-US-GuyNeural", "en-US", "Guy · US", "male"),
    AgentVoice("", "en-GB-SoniaNeural", "en-GB", "Sonia · UK", "female"),
    AgentVoice("", "en-GB-RyanNeural", "en-GB", "Ryan · UK", "male"),
    AgentVoice("", "en-GB-MaisieNeural", "en-GB", "Maisie · UK", "female"),
    AgentVoice("", "en-GB-ThomasNeural", "en-GB", "Thomas · UK", "male"),
    AgentVoice("", "en-AU-NatashaNeural", "en-AU", "Natasha · Australia", "female"),
    AgentVoice("", "en-AU-WilliamNeural", "en-AU", "William · Australia", "male"),
    AgentVoice("", "en-AU-CarlyNeural", "en-AU", "Carly · Australia", "female"),
    AgentVoice("", "en-AU-DarrenNeural", "en-AU", "Darren · Australia", "male"),
    AgentVoice("", "en-CA-ClaraNeural", "en-CA", "Clara · Canada", "female"),
    AgentVoice("", "en-CA-LiamNeural", "en-CA", "Liam · Canada", "male"),
    AgentVoice("", "en-IN-NeerjaNeural", "en-IN", "Neerja · India", "female"),
    AgentVoice("", "en-IN-PrabhatNeural", "en-IN", "Prabhat · India", "male"),
    AgentVoice("", "en-IE-EmilyNeural", "en-IE", "Emily · Ireland", "female"),
    AgentVoice("", "en-IE-ConnorNeural", "en-IE", "Connor · Ireland", "male"),
    AgentVoice("", "en-NZ-MollyNeural", "en-NZ", "Molly · New Zealand", "female"),
    AgentVoice("", "en-NZ-MitchellNeural", "en-NZ", "Mitchell · New Zealand", "male"),
    AgentVoice("", "en-ZA-LeahNeural", "en-ZA", "Leah · South Africa", "female"),
    AgentVoice("", "en-ZA-LukeNeural", "en-ZA", "Luke · South Africa", "male"),
    AgentVoice("", "en-SG-LunaNeural", "en-SG", "Luna · Singapore", "female"),
    AgentVoice("", "en-SG-WayneNeural", "en-SG", "Wayne · Singapore", "male"),
)

VOICE_BY_NAME = {profile.voice.casefold(): profile for profile in VOICE_LIBRARY}

AGENT_VOICES = {
    "flavor chef": AgentVoice("Flavor Chef", "en-GB-MaisieNeural", "en-GB", "Maisie · UK", "female"),
    "cost manager": AgentVoice("Cost Manager", "en-AU-DarrenNeural", "en-AU", "Darren · Australia", "male"),
    "customer scout": AgentVoice("Customer Scout", "en-GB-RyanNeural", "en-GB", "Ryan · UK", "male"),
    "creative director": AgentVoice("Creative Director", "en-AU-CarlyNeural", "en-AU", "Carly · Australia", "female"),
}


def voice_for_agent(agent: str, requested_voice: str = "") -> AgentVoice:
    profile = AGENT_VOICES.get(str(agent or "").strip().casefold())
    if profile is None:
        raise ProviderError("Unknown design-crew agent voice.")
    requested = str(requested_voice or "").strip().casefold()
    if not requested:
        return profile
    selected = VOICE_BY_NAME.get(requested)
    if selected is None:
        raise ProviderError("The requested voice is not in the approved 24-voice English roster.")
    return AgentVoice(profile.agent, selected.voice, selected.locale, selected.label, selected.gender)


def safe_speech_text(value: str) -> str:
    """Keep spoken feedback short and avoid reading code, URLs, or local paths aloud."""
    text = str(value or "")
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"https?://\S+", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:[A-Za-z]:\\|/)[^\s]+", " ", text)
    text = re.sub(r"\b(?:sk|key|token)[-_][A-Za-z0-9_-]{12,}\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600]


class AzureSpeechService:
    def __init__(self, settings: ProviderSettings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        provider = str(self.settings.tts_provider or "").strip().casefold()
        has_route = bool(str(self.settings.tts_endpoint or "").strip() or str(self.settings.tts_region or "").strip())
        return provider == "azure" and has_route and bool(self.settings.resolved_tts_key())

    @property
    def endpoint(self) -> str:
        explicit = str(self.settings.tts_endpoint or "").strip()
        if explicit:
            return explicit
        region = str(self.settings.tts_region or "").strip()
        if not region:
            return ""
        return "https://%s.tts.speech.microsoft.com/cognitiveservices/v1" % region

    def status(self) -> dict[str, object]:
        return {
            "provider": "azure" if str(self.settings.tts_provider).casefold() == "azure" else "disabled",
            "configured": self.configured,
            "region": str(self.settings.tts_region or "").strip(),
            "endpoint_configured": bool(self.endpoint),
            "key_configured": bool(self.settings.resolved_tts_key()),
            "reachability": "not_probed",
            "voices": [
                {
                    "voice": profile.voice,
                    "locale": profile.locale,
                    "label": profile.label,
                    "gender": profile.gender,
                }
                for profile in VOICE_LIBRARY
            ],
            "agent_defaults": [
                {
                    "agent": profile.agent,
                    "voice": profile.voice,
                    "locale": profile.locale,
                    "label": profile.label,
                    "gender": profile.gender,
                }
                for profile in AGENT_VOICES.values()
            ],
        }

    def synthesize(
        self, agent: str, message: str, requested_voice: str = "", rate: float = 1.0
    ) -> tuple[bytes, AgentVoice, str]:
        if not self.configured:
            raise ProviderError(
                "Azure agent voices are not configured. Set tts_provider, tts_region (or tts_endpoint), "
                "and the AZURE_SPEECH_KEY environment variable."
            )
        profile = voice_for_agent(agent, requested_voice)
        clean = safe_speech_text(message)
        if not clean:
            raise ProviderError("There is no safe agent feedback to speak.")
        safe_rate = max(0.8, min(1.2, float(rate)))
        rate_percent = int(round((safe_rate - 1.0) * 100.0))
        ssml = (
            "<speak version='1.0' xml:lang='%s'>"
            "<voice name='%s'><prosody rate='%+d%%'>%s</prosody></voice></speak>"
            % (profile.locale, profile.voice, rate_percent, escape(clean, quote=False))
        )
        request = urllib.request.Request(
            self.endpoint,
            data=ssml.encode("utf-8"),
            headers={
                "Ocp-Apim-Subscription-Key": self.settings.resolved_tts_key(),
                "Content-Type": "application/ssml+xml; charset=utf-8",
                "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
                "User-Agent": "BarrosPizzaCreator/1.6",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=int(self.settings.timeout_seconds)) as response:
                audio = response.read()
        except urllib.error.HTTPError as exc:
            raise ProviderError("Azure speech returned HTTP %d." % exc.code) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ProviderError("Azure speech request failed: %s" % exc) from exc
        if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            raise ProviderError("Azure speech did not return a valid WAV response.")
        return audio, profile, clean
