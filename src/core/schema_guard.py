"""
Schema Guard - canonical data enforcement layer for AutoSE Platform.

Every agent that produces or consumes a Product, Requirement, or Solution
MUST pass its data through the corresponding validate_* function before use.

The guard:
  1. Accepts either a Pydantic model instance or a raw dict.
  2. Auto-converts legacy dicts to the canonical schema where possible.
  3. Logs every validation failure with full context (never silently passes).
  4. Returns a GuardResult carrying the cleaned object, a boolean valid flag,
     and a list of human-readable error strings.

Usage::

    from src.core.schema_guard import validate_product, validate_requirement

    result = validate_product(raw_catalog_dict)
    if not result.valid:
        raise ValueError(result.errors)

    product = result.data   # canonical Product instance
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Import canonical schemas - try both absolute and relative paths
# ---------------------------------------------------------------------------
try:
    from src.schemas.solution_schema import Product, Requirement, Solution
except ImportError:
    try:
        from schemas.solution_schema import Product, Requirement, Solution  # type: ignore[no-redef]
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from src.schemas.solution_schema import Product, Requirement, Solution  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("autose.schema_guard")

if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# GuardResult
# ---------------------------------------------------------------------------

T = TypeVar("T")


@dataclass
class GuardResult(Generic[T]):
    """
    Return value from every validate_* function.

    Attributes
    ----------
    data:
        The cleaned, validated Pydantic model instance.
        None only when valid is False and conversion was impossible.
    valid:
        True if the input was accepted (possibly after auto-conversion).
        False if Pydantic validation failed.
    errors:
        Human-readable error strings. Empty when valid is True.
    source_type:
        The Python type name of the original input (for diagnostics).
    """

    data: Optional[T]
    valid: bool
    errors: List[str] = field(default_factory=list)
    source_type: str = ""

    def raise_if_invalid(self) -> T:
        """
        Raise ValueError if validation failed, otherwise return cleaned data.

        Raises
        ------
        ValueError
            Contains all error strings joined by newlines.
        """
        if not self.valid or self.data is None:
            raise ValueError(
                "Schema validation failed for {}:\n{}".format(
                    self.source_type, "\n".join(self.errors)
                )
            )
        return self.data


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pydantic_errors_to_strings(exc: ValidationError) -> List[str]:
    """Convert a Pydantic ValidationError into a flat list of readable strings."""
    messages: List[str] = []
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "unknown error")
        inp = err.get("input", "<no input>")
        messages.append("[{}] {}  (got: {!r})".format(loc, msg, inp))
    return messages


def _log_failure(
    object_type: str,
    source_type: str,
    errors: List[str],
    raw_input: Any,
) -> None:
    """Emit a structured ERROR log entry for a validation failure."""
    logger.error(
        "Schema validation FAILED | object_type=%s | source_type=%s | "
        "error_count=%d | errors=%s | raw_input_preview=%s",
        object_type,
        source_type,
        len(errors),
        errors,
        repr(raw_input)[:300],
    )


def _log_conversion(object_type: str, source_type: str) -> None:
    """Emit a DEBUG log when a legacy dict is auto-converted."""
    logger.debug(
        "Schema auto-conversion | object_type=%s | source_type=%s -> canonical model",
        object_type,
        source_type,
    )


def _log_success(object_type: str, source_type: str) -> None:
    """Emit a DEBUG log on successful validation."""
    logger.debug(
        "Schema validation OK | object_type=%s | source_type=%s",
        object_type,
        source_type,
    )


# ---------------------------------------------------------------------------
# validate_product
# ---------------------------------------------------------------------------

def validate_product(
    product: Union[Dict[str, Any], "Product", Any],
) -> "GuardResult[Product]":
    """
    Validate and normalise a product value to the canonical Product schema.

    Accepted inputs
    ---------------
    - Product instance  -> validated as-is (re-runs Pydantic validators).
    - dict              -> auto-converted via Product.from_catalog_dict(),
                          which handles legacy key aliases (gpu/gpu_count,
                          ports/port_count, flat vs nested capacity).
    - Any other type    -> duck-typed via vars() / __dict__.

    Returns
    -------
    GuardResult[Product]
    """
    source_type = type(product).__name__

    # Already a canonical Product
    if isinstance(product, Product):
        try:
            cleaned = Product.model_validate(product.model_dump(by_alias=False))
            _log_success("Product", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except ValidationError as exc:
            errors = _pydantic_errors_to_strings(exc)
            _log_failure("Product", source_type, errors, product)
            return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Dict (legacy catalog format or arbitrary mapping)
    if isinstance(product, dict):
        # Strategy 1: use the schema's dedicated from_catalog_dict converter
        try:
            _log_conversion("Product", source_type)
            cleaned = Product.from_catalog_dict(product)
            _log_success("Product", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except (KeyError, ValidationError, TypeError) as exc1:
            # Strategy 2: direct Pydantic model_validate (handles nested capacity dict)
            try:
                cleaned = Product.model_validate(product)
                _log_success("Product", source_type)
                return GuardResult(data=cleaned, valid=True, source_type=source_type)
            except ValidationError as exc2:
                errors = _pydantic_errors_to_strings(exc2)
                errors.insert(0, "from_catalog_dict also failed: {}".format(exc1))
                _log_failure("Product", source_type, errors, product)
                return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Unknown type - attempt duck-typing via __dict__
    try:
        as_dict = vars(product) if hasattr(product, "__dict__") else dict(product)
        return validate_product(as_dict)
    except Exception as exc:
        errors = ["Cannot convert {} to dict: {}".format(source_type, exc)]
        _log_failure("Product", source_type, errors, product)
        return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)


# ---------------------------------------------------------------------------
# validate_requirement
# ---------------------------------------------------------------------------

def validate_requirement(
    req: Union[Dict[str, Any], "Requirement", Any],
) -> "GuardResult[Requirement]":
    """
    Validate and normalise a requirement value to the canonical Requirement schema.

    Accepted inputs
    ---------------
    - Requirement instance          -> validated as-is.
    - StructuredRequirements model  -> auto-converted (technical fields only;
                                       business fields default to empty/zero).
    - dict                          -> direct model_validate first, then
                                       Requirement.from_structured() fallback
                                       for dicts that only contain the four
                                       StructuredRequirements keys.
    - Any other type                -> duck-typed via vars().

    Returns
    -------
    GuardResult[Requirement]
    """
    source_type = type(req).__name__

    # Already canonical
    if isinstance(req, Requirement):
        try:
            cleaned = Requirement.model_validate(req.model_dump())
            _log_success("Requirement", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except ValidationError as exc:
            errors = _pydantic_errors_to_strings(exc)
            _log_failure("Requirement", source_type, errors, req)
            return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Dict
    if isinstance(req, dict):
        # Strategy 1: direct model_validate (works for canonical dicts)
        try:
            _log_conversion("Requirement", source_type)
            cleaned = Requirement.model_validate(req)
            _log_success("Requirement", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except ValidationError as exc1:
            # Strategy 2: treat as StructuredRequirements-style dict
            try:
                cleaned = Requirement.from_structured(req)
                _log_success("Requirement", source_type)
                return GuardResult(data=cleaned, valid=True, source_type=source_type)
            except (ValidationError, TypeError, KeyError) as exc2:
                errors = _pydantic_errors_to_strings(exc1)
                errors.append("from_structured fallback also failed: {}".format(exc2))
                _log_failure("Requirement", source_type, errors, req)
                return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Pydantic model with compatible fields (e.g. StructuredRequirements)
    if hasattr(req, "model_dump") or hasattr(req, "dict"):
        try:
            _log_conversion("Requirement", source_type)
            cleaned = Requirement.from_structured(req)
            _log_success("Requirement", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except (ValidationError, TypeError, AttributeError) as exc:
            errors = ["from_structured conversion failed: {}".format(exc)]
            _log_failure("Requirement", source_type, errors, req)
            return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Unknown type
    try:
        as_dict = vars(req) if hasattr(req, "__dict__") else dict(req)
        return validate_requirement(as_dict)
    except Exception as exc:
        errors = ["Cannot convert {} to dict: {}".format(source_type, exc)]
        _log_failure("Requirement", source_type, errors, req)
        return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)


# ---------------------------------------------------------------------------
# validate_solution
# ---------------------------------------------------------------------------

def validate_solution(
    sol: Union[Dict[str, Any], "Solution", Any],
) -> "GuardResult[Solution]":
    """
    Validate and normalise a solution value to the canonical Solution schema.

    Accepted inputs
    ---------------
    - Solution instance -> validated as-is (re-runs model validators,
                           including derived-field recomputation).
    - dict              -> model_validate first; if that fails and the dict
                           looks like a pipeline result dict (has products /
                           selected_products key), from_pipeline_result() is
                           attempted.
    - Any other type    -> duck-typed via vars().

    Returns
    -------
    GuardResult[Solution]
    """
    source_type = type(sol).__name__

    # Already canonical
    if isinstance(sol, Solution):
        try:
            cleaned = Solution.model_validate(sol.model_dump())
            _log_success("Solution", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except ValidationError as exc:
            errors = _pydantic_errors_to_strings(exc)
            _log_failure("Solution", source_type, errors, sol)
            return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Dict
    if isinstance(sol, dict):
        # Strategy 1: direct model_validate
        try:
            _log_conversion("Solution", source_type)
            cleaned = Solution.model_validate(sol)
            _log_success("Solution", source_type)
            return GuardResult(data=cleaned, valid=True, source_type=source_type)
        except ValidationError as exc1:
            # Strategy 2: pipeline-result dict
            # Expected shape: {requirements/requirement, products/selected_products, ...}
            try:
                req_raw = sol.get("requirement") or sol.get("requirements") or {}
                req_result = validate_requirement(req_raw)
                if not req_result.valid or req_result.data is None:
                    raise ValueError(
                        "Nested requirement invalid: {}".format(req_result.errors)
                    )

                products_raw: List[Dict[str, Any]] = (
                    sol.get("selected_products")
                    or sol.get("products")
                    or []
                )

                # Resolve validation_status from multiple possible locations
                validation_raw = sol.get("validation", {})
                validation_status: str = (
                    sol.get("validation_status")
                    or (
                        validation_raw.get("power_check", "PASS")
                        if isinstance(validation_raw, dict)
                        else "PASS"
                    )
                )

                warnings: List[str] = (
                    sol.get("validation_warnings")
                    or (
                        validation_raw.get("warnings", [])
                        if isinstance(validation_raw, dict)
                        else []
                    )
                )

                cleaned = Solution.from_pipeline_result(
                    requirement=req_result.data,
                    products=products_raw,
                    validation_status=validation_status,
                    validation_warnings=warnings,
                    assumptions=sol.get("assumptions", []),
                    session_id=sol.get("session_id"),
                )
                _log_success("Solution", source_type)
                return GuardResult(data=cleaned, valid=True, source_type=source_type)

            except (ValidationError, ValueError, TypeError, KeyError) as exc2:
                errors = _pydantic_errors_to_strings(exc1)
                errors.append(
                    "from_pipeline_result fallback also failed: {}".format(exc2)
                )
                _log_failure("Solution", source_type, errors, sol)
                return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)

    # Unknown type
    try:
        as_dict = vars(sol) if hasattr(sol, "__dict__") else dict(sol)
        return validate_solution(as_dict)
    except Exception as exc:
        errors = ["Cannot convert {} to dict: {}".format(source_type, exc)]
        _log_failure("Solution", source_type, errors, sol)
        return GuardResult(data=None, valid=False, errors=errors, source_type=source_type)


# ---------------------------------------------------------------------------
# validate_product_list  (batch helper)
# ---------------------------------------------------------------------------

def validate_product_list(
    products: List[Any],
    strict: bool = False,
) -> "GuardResult[List[Product]]":
    """
    Validate a list of products, returning a single GuardResult.

    Parameters
    ----------
    products:
        List of items to validate (dicts, Product instances, or mixed).
    strict:
        If True, the result is invalid if any item fails.
        If False (default), invalid items are skipped and logged, but
        the result is still valid as long as at least one item passes.

    Returns
    -------
    GuardResult[List[Product]]
        data contains only the successfully validated products.
    """
    if not isinstance(products, list):
        error = "Expected a list, got {}".format(type(products).__name__)
        logger.error(
            "Schema validation FAILED | object_type=ProductList | %s", error
        )
        return GuardResult(data=None, valid=False, errors=[error], source_type="list")

    cleaned: List[Product] = []
    all_errors: List[str] = []

    for idx, item in enumerate(products):
        result = validate_product(item)
        if result.valid and result.data is not None:
            cleaned.append(result.data)
        else:
            prefixed = ["[index {}] {}".format(idx, e) for e in result.errors]
            all_errors.extend(prefixed)
            logger.warning(
                "Product at index %d failed validation: %s",
                idx,
                result.errors,
            )

    if strict and all_errors:
        _log_failure(
            "ProductList", "list", all_errors,
            "<list of {} items>".format(len(products))
        )
        return GuardResult(data=None, valid=False, errors=all_errors, source_type="list")

    if not cleaned and products:
        # Every item failed
        _log_failure(
            "ProductList", "list", all_errors,
            "<list of {} items>".format(len(products))
        )
        return GuardResult(data=None, valid=False, errors=all_errors, source_type="list")

    if all_errors:
        logger.warning(
            "ProductList partial validation: %d/%d items valid, %d errors",
            len(cleaned),
            len(products),
            len(all_errors),
        )

    return GuardResult(
        data=cleaned,
        valid=True,
        errors=all_errors,
        source_type="list",
    )
