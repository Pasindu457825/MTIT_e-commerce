"""Product-service integration helpers used by review-service."""

import httpx
from fastapi import HTTPException, status


class ProductCatalogClient:
    """Validate product references against product-service."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        enabled: bool,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._enabled = enabled

    async def assert_product_exists(self, product_id: str) -> None:
        """Validate that a product exists before allowing review creation."""
        if not self._enabled:
            return

        url = f"{self._base_url}/api/v1/products/{product_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(url, headers={"accept": "application/json"})
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product validation timed out. Please try again.",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not validate product due to product-service connectivity issue.",
            ) from exc

        if response.status_code == status.HTTP_200_OK:
            return
        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found for product_id '{product_id}'.",
            )
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product_id. Provide a valid product identifier.",
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product validation failed due to product-service response.",
        )