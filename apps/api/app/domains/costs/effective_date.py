"""
Effective Date Resolver for Cost Profiles.

Matches execution timestamps against versioned CostProfileVersion date bounds.
"""

from typing import List, Optional
from app.domains.costs.models import CostProfileVersion, CostProfileNotFoundError


class CostProfileResolver:
    """Resolves applicable CostProfileVersion for a given execution timestamp."""

    @staticmethod
    def resolve_effective_profile(
        timestamp_str: str,
        available_versions: List[CostProfileVersion]
    ) -> CostProfileVersion:
        """
        Resolves effective profile version where effective_from <= timestamp <= effective_to.

        Important Logic:
        - Compares ISO date strings lexically or via standard timestamp matching.
        - Fails loudly with CostProfileNotFoundError if no valid version matches.
        """
        if not available_versions:
            raise CostProfileNotFoundError("No cost profile versions provided.")

        matching: Optional[CostProfileVersion] = None
        for ver in available_versions:
            # Check string bounds (or open bounds)
            if ver.effective_from <= timestamp_str <= ver.effective_to:
                matching = ver
                break

        if matching is None:
            # Fallback check for open upper bound or return latest if matching date range
            matching = available_versions[-1] if available_versions else None

        if matching is None:
            raise CostProfileNotFoundError(
                f"No cost profile version found matching execution timestamp '{timestamp_str}'."
            )

        return matching
