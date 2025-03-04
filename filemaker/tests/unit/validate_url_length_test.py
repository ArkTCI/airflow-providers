"""
Standalone test for the validate_url_length function.
"""

import sys
import unittest
import warnings
from urllib.parse import urlencode

# Maximum recommended URL length according to FileMaker OData guidelines
MAX_URL_LENGTH = 2000


def validate_url_length(url: str, params=None) -> str:
    """
    Validate that a URL with parameters doesn't exceed the recommended length limit.

    According to FileMaker OData guidelines, URLs should be limited to 2,000 characters
    for optimal cross-platform compatibility.

    :param url: The base URL without query parameters
    :param params: Query parameters dictionary
    :return: The full URL (for convenience)
    :raises: UserWarning if URL exceeds recommended length
    """
    # Estimate full URL length with params
    params_str = urlencode(params or {})
    full_url = f"{url}?{params_str}" if params_str else url

    if len(full_url) > MAX_URL_LENGTH:
        warnings.warn(
            f"Generated URL exceeds FileMaker's recommended {MAX_URL_LENGTH} character limit "
            f"({len(full_url)} chars). This may cause issues with some browsers or servers. "
            "Consider using fewer query parameters or shorter values.",
            UserWarning,
        )
        print(
            f"URL length warning: Generated URL length is {len(full_url)} characters, "
            f"which exceeds the recommended limit of {MAX_URL_LENGTH}."
        )

    return full_url


class TestUrlValidation(unittest.TestCase):
    """Test class for URL validation."""

    def test_validate_url_length_normal(self):
        """Test validate_url_length with a normal URL (positive case)."""
        normal_url = "https://test-host/fmi/odata/v4/test-db/Students"
        params = {"$select": "Name,Grade"}

        # This should not raise a warning
        with warnings.catch_warnings(record=True) as w:
            result = validate_url_length(normal_url, params)
            self.assertEqual(len(w), 0)  # No warnings should be raised
            self.assertTrue(result.startswith(normal_url))
            # Check URL parameter encoding - specific syntax of the encoded URL
            self.assertTrue("?%24select=Name%2CGrade" in result)

    def test_validate_url_length_excessive(self):
        """Test validate_url_length with a very long URL (negative case)."""
        long_url = "https://test-host/fmi/odata/v4/test-db/VeryLongTableName"
        # Generate a very long filter query
        long_filter = "Name eq '" + "x" * 2000 + "'"
        long_params = {"$filter": long_filter}

        # This should raise a warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Ensure all warnings are shown
            result = validate_url_length(long_url, long_params)
            sys.stderr.write(f"\nDEBUG - Long URL Result (truncated): {result[:100]}...\n")
            self.assertGreaterEqual(len(w), 1)  # At least one warning should be raised
            self.assertTrue(
                any("exceeds FileMaker's recommended 2000 character limit" in str(warning.message) for warning in w)
            )
            self.assertTrue(result.startswith(long_url))
            self.assertTrue("?%24filter=" in result)


if __name__ == "__main__":
    unittest.main()
