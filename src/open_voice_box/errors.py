class OpenVoiceBoxError(Exception):
    """Base error that can be shown to a user."""


class AudioInputError(OpenVoiceBoxError):
    pass


class TranscriptionError(OpenVoiceBoxError):
    pass


class ProviderUnavailableError(OpenVoiceBoxError):
    pass


class MissingModelError(OpenVoiceBoxError):
    pass


class MissingCredentialError(OpenVoiceBoxError):
    pass


class SpeechError(OpenVoiceBoxError):
    pass
