import unittest
from unittest.mock import patch, MagicMock
from verity_check.perception import extract_data

class TestPerceptionMock(unittest.TestCase):
    
    @patch("verity_check.perception.requests.post")
    def test_auto_categorization_identity(self, mock_post):
        # Mock response for Categorization
        mock_cat_response = MagicMock()
        mock_cat_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '```json\n{"category": "Identity", "confidence": 0.95}\n```'
                }
            }]
        }
        
        # Mock response for Extraction
        mock_extract_response = MagicMock()
        mock_extract_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '```json\n{"surname": "Mustermann"}\n```'
                }
            }]
        }
        
        # Configure side_effect to return cat response first, then extract response
        mock_post.side_effect = [mock_cat_response, mock_extract_response]
        
        result = extract_data("fake_base64_string")
        
        self.assertEqual(result["category"], "Identity")
        self.assertEqual(result["data"]["surname"], "Mustermann")
        self.assertEqual(mock_post.call_count, 2)
        
    @patch("verity_check.perception.requests.post")
    def test_provided_category(self, mock_post):
        # Mock response for Extraction only (no categorization call)
        mock_extract_response = MagicMock()
        mock_extract_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"net_income": 2000}'
                }
            }]
        }
        
        mock_post.return_value = mock_extract_response
        
        result = extract_data("fake_base64_string", doc_category="Livelihood")
        
        self.assertEqual(result["category"], "Livelihood")
        self.assertEqual(result["data"]["net_income"], 2000)
        self.assertEqual(mock_post.call_count, 1)

if __name__ == "__main__":
    unittest.main()
