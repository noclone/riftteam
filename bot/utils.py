import aiohttp


def format_api_error(exc: Exception) -> str:
    if isinstance(exc, aiohttp.ClientResponseError):
        if exc.status == 429:
            return "Trop de requêtes. Réessaie dans quelques minutes."
        if exc.status in (502, 503):
            return "Service temporairement indisponible. Réessaie plus tard."
        if exc.status == 500:
            return "Erreur interne du serveur. Réessaie plus tard."
        if exc.status == 403:
            return "Action non autorisée."
    if isinstance(exc, aiohttp.ClientError):
        return "Impossible de contacter le serveur. Réessaie plus tard."
    return "Erreur inattendue. Réessaie plus tard."
