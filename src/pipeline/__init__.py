"""Pipeline module for end-to-end prescription processing (V6)."""

__all__ = [
    "PrescriptionExtractorV6",
    "PrescriptionExtractor",  # backward-compatible alias
    "DetectedField",
    "StructuredPrescriptionExtractor",
    "get_extractor",
    "get_structured_extractor",
]

def __getattr__(name):
    if name in ("PrescriptionExtractorV6", "PrescriptionExtractor", "DetectedField", "get_extractor"):
        from .extractor import PrescriptionExtractorV6, PrescriptionExtractor, DetectedField, get_extractor
        mapping = {
            "PrescriptionExtractorV6": PrescriptionExtractorV6,
            "PrescriptionExtractor": PrescriptionExtractor,
            "DetectedField": DetectedField,
            "get_extractor": get_extractor,
        }
        return mapping[name]
    elif name in ("StructuredPrescriptionExtractor", "get_structured_extractor"):
        from .structured_extractor import StructuredPrescriptionExtractor, get_structured_extractor
        mapping = {
            "StructuredPrescriptionExtractor": StructuredPrescriptionExtractor,
            "get_structured_extractor": get_structured_extractor,
        }
        return mapping[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
