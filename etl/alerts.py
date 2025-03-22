import structlog

logger = structlog.get_logger()


class AlertHandler:
    @staticmethod
    def alert(event: str, **kwargs):
        logger.error(event, **kwargs)
        # Extend this for Slack, Email, Sentry, etc.
