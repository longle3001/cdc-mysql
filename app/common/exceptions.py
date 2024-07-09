"""Common exception classes used by modern Streaming services."""


class StreamingServiceException(Exception):
    """Base class of all exceptions raised by classes in Streaming services.

    Use this class instead of `Exception` as a base class for anything that
    is passed between classes and functions. This allows catching
    `StreamingServiceException` in places where one wants to, e.g., re-try
    errors, without having to catch `Exception` and accidentlaly catching
    errors caused by various bugs like `AttributeError`, `TypeError`, etc.
    """


class BootstrapServersKafkaException(StreamingServiceException):
    """Raised when Bootstrap Service not available."""


class GroupIdKafkaException(StreamingServiceException):
    """Raised when Bootstrap Service not available."""


class TopicKafkaException(StreamingServiceException):
    """Raised when Kafka Topic not available."""


class CreateConsumerKafkaException(StreamingServiceException):
    """Raised when cannot create Consummer Kafka Topic."""


class SubscribeKafkaTopicException(StreamingServiceException):
    """Raised when cannot subscribe Kafka Topic."""
