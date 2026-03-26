import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm_service import OpenRouterClient, get_client, generate_question, evaluate_answer
from src.models import Question, Evaluation


class TestOpenRouterClientInit:
    """Testy inicjalizacji OpenRouterClient"""
    
    def test_init_with_explicit_api_key(self):
        """Powinno zaakceptować api_key przekazany bezpośrednio"""
        client = OpenRouterClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.model == "openai/gpt-5-mini"

    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'env-key-456'})
    def test_init_with_env_variable(self):
        """Powinno wczytać api_key ze zmiennej środowiskowej"""
        client = OpenRouterClient()
        assert client.api_key == "env-key-456"

    def test_init_without_api_key_raises_error(self):
        """Powinno rzucić ValueError jeśli api_key nie jest dostępny"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY nie ustawiony"):
                OpenRouterClient()


class TestParseJsonResponse:
    """Testy parsowania odpowiedzi JSON"""
    
    def test_parse_valid_json(self):
        """Powinno sparsować poprawny JSON"""
        client = OpenRouterClient(api_key="test-key")
        response_content = '{"topic": "Python", "difficulty": "easy", "question_text": "Co to Python?", "hint": "Snake"}'
        
        result = client._parse_json_response(response_content, Question)
        
        assert isinstance(result, Question)
        assert result.topic == "Python"
        assert result.difficulty == "easy"
        assert result.question_text == "Co to Python?"
        assert result.hint == "Snake"

    def test_parse_json_with_extra_text(self):
        """Powinno sparsować JSON nawet ze zdłością tekstem wokół niego"""
        client = OpenRouterClient(api_key="test-key")
        response_content = 'Oto odpowiedź: {"topic": "SQL", "difficulty": "medium", "question_text": "SELECT *?", "hint": "WHERE"} Koniec.'
        
        result = client._parse_json_response(response_content, Question)
        
        assert isinstance(result, Question)
        assert result.topic == "SQL"

    def test_parse_none_content_raises_error(self):
        """Powinno rzucić ValueError jeśli content to None"""
        client = OpenRouterClient(api_key="test-key")
        
        with pytest.raises(ValueError, match="content is None"):
            client._parse_json_response(None, Question)

    def test_parse_invalid_json_raises_error(self):
        """Powinno rzucić ValueError dla niepoprawnego JSON"""
        client = OpenRouterClient(api_key="test-key")
        response_content = '{"topic": "Python", invalid json'
        
        with pytest.raises(ValueError, match="Błąd parsowania JSON"):
            client._parse_json_response(response_content, Question)

    def test_parse_json_without_braces_raises_error(self):
        """Powinno rzucić ValueError jeśli nie ma nawiasów klamrowych"""
        client = OpenRouterClient(api_key="test-key")
        response_content = 'To nie jest JSON!'
        
        with pytest.raises(ValueError, match="Nie znaleziono JSON"):
            client._parse_json_response(response_content, Question)


class TestGenerateQuestion:
    """Testy generowania pytań"""
    
    @patch('httpx.post')
    def test_generate_question_success(self, mock_post):
        """Powinno pomyślnie wygenerować pytanie"""
        # Mock odpowiedzi API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"topic": "Python", "difficulty": "easy", "question_text": "Pytanie?", "hint": "Podpowiedź"}'
                }
            }]
        }
        mock_post.return_value = mock_response

        client = OpenRouterClient(api_key="test-key")
        result = client.generate_question("Python", "easy")

        assert isinstance(result, Question)
        assert result.topic == "Python"
        assert result.difficulty == "easy"
        mock_post.assert_called_once()

    @patch('httpx.post')
    def test_generate_question_api_error(self, mock_post):
        """Powinno rzucić ValueError na błąd HTTP"""
        mock_post.side_effect = Exception("Connection error")

        client = OpenRouterClient(api_key="test-key")
        with pytest.raises(Exception):
            client.generate_question("Python", "easy")


class TestEvaluateAnswer:
    """Testy oceniania odpowiedzi"""
    
    @patch('httpx.post')
    def test_evaluate_answer_success(self, mock_post):
        """Powinno pomyślnie ocenić odpowiedź"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_correct": true, "score": 10, "explanation": "Poprawnie!", "correct_answer": "Python", "learning_tip": "Pamiętaj"}'
                }
            }]
        }
        mock_post.return_value = mock_response

        client = OpenRouterClient(api_key="test-key")
        result = client.evaluate_answer("Pytanie?", "Odpowiedź")

        assert isinstance(result, Evaluation)
        assert result.is_correct is True
        assert result.score == 10
        assert result.explanation == "Poprawnie!"

    @patch('httpx.post')
    def test_evaluate_answer_http_error(self, mock_post):
        """Powinno obsłużyć błędy HTTP"""
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
        mock_post.side_effect = error

        client = OpenRouterClient(api_key="test-key")
        
        with pytest.raises(ValueError, match="Błąd API"):
            client.evaluate_answer("Pytanie?", "Odpowiedź")

    @patch('httpx.post')
    def test_evaluate_answer_connection_error(self, mock_post):
        """Powinno obsłużyć błędy połączenia"""
        import httpx
        error = httpx.RequestError("Connection timeout")
        mock_post.side_effect = error

        client = OpenRouterClient(api_key="test-key")
        
        with pytest.raises(ValueError, match="Błąd połączenia"):
            client.evaluate_answer("Pytanie?", "Odpowiedź")


class TestModuleFunctions:
    """Testy funkcji modułowych"""
    
    @patch('src.llm_service.OpenRouterClient')
    def test_get_client_returns_singleton(self, mock_client_class):
        """get_client powinno zwracać tę samą instancję"""
        import src.llm_service
        src.llm_service._client = None  # Reset singleton
        
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        client1 = get_client()
        client2 = get_client()
        
        assert client1 is client2
        mock_client_class.assert_called_once()

    @patch('src.llm_service.get_client')
    def test_generate_question_wrapper(self, mock_get_client):
        """generate_question powinno wywoływać metodę klienta"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_question = Question(
            topic="Python",
            difficulty="easy",
            question_text="Test?",
            hint="Hint"
        )
        mock_client.generate_question.return_value = mock_question

        result = generate_question("Python", "easy")

        assert result == mock_question
        mock_client.generate_question.assert_called_once_with("Python", "easy")

    @patch('src.llm_service.get_client')
    def test_evaluate_answer_wrapper(self, mock_get_client):
        """evaluate_answer powinno wywoływać metodę klienta"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_evaluation = Evaluation(
            is_correct=True,
            score=10,
            explanation="Good",
            correct_answer="Answer",
            learning_tip="Tip"
        )
        mock_client.evaluate_answer.return_value = mock_evaluation

        result = evaluate_answer("Question", "Answer")

        assert result == mock_evaluation
        mock_client.evaluate_answer.assert_called_once_with("Question", "Answer")