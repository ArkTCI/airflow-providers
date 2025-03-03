from typing import Optional, Dict, Any
import requests

class FileMakerHook:
    def get_odata_response(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        accept_format: str = "application/json",
    ) -> Dict[str, Any]:
        """
        Get response from OData API.

        Args:
            endpoint: The endpoint to query
            params: Query parameters
            accept_format: Accept header format

        Returns:
            Dict[str, Any]: The response data
        """
        # Get token for authorization
        token = self.get_token()

        # Prepare headers
        headers = {"Authorization": f"FMID {token}", "Accept": accept_format}

        # Execute request
        self.log.info(f"Making request to: {endpoint}")
        response = requests.get(endpoint, headers=headers, params=params)

        # Check response
        if response.status_code >= 400:
            raise Exception(f"OData API error: {response.status_code} - {response.text}")

        # Return appropriate format based on accept header
        if accept_format == "application/xml" or "xml" in response.headers.get("Content-Type", ""):
            self.log.info("Received XML response")
            return {"data": response.text}
        else:
            try:
                self.log.info("Parsing JSON response")
                response_data = response.json()
                if isinstance(response_data, dict):
                    return response_data
                else:
                    # Convert string or other types to dict
                    return {"data": response_data}
            except Exception as e:
                self.log.error(f"Error parsing response as JSON: {str(e)}")
                # Return the raw text if JSON parsing fails
                return {"data": response.text} 