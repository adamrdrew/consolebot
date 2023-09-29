import unittest
from unittest.mock import patch, MagicMock
from consolebot.query import determine_repo_name, generate_combinations, cached_github_data, get_language,get_recent_activity, get_contributors, get_wordnet_pos, preprocess_text, determine_intent, get_summary, generate_combinations, disambiguate_repo_name
import nltk
from unittest.mock import patch, Mock

nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

class MockGithubData:
    @classmethod
    def get_formatted_repos(cls):
        return {
            "apple-fruit": {},
            "apple-phone": {},
            "grape": {}
        }
    
    @classmethod
    def get_repo(cls, repo_name):
        return {
            "apple-fruit": {},
            "apple-phone": {},
            "grape": {}
        }[repo_name]
    
    @classmethod
    def get_readme_content(cls, repo):
        if repo["name"] == "EmptyRepo":
            return None
        return "# Title\nJohn Jingleheimer Schmidt, his name is my name too"
    
    @classmethod
    def get_commits(cls, repo):
        if isinstance(repo, dict):
            if repo["name"]  == "EmptyRepo":
                return []
        return [
            {"message": "commit1"},
            {"message": "commit2"},
            {"message": "commit3"},
            {"message": "commit4"},
            {"message": "commit5"},
            {"message": "commit6"}
        ]
    
    @classmethod
    def get_repo_contributors(cls, repo):
        return ["Alice", "Bob", "Github", "Charlie"]

    @classmethod
    def get_repo_languages(cls, repo):
        if repo["name"] == "EmptyRepo":
            return ["Unknown"]
        return ["Python", "JavaScript"]



class TestPreprocessText(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        nltk.download('punkt')
        nltk.download('wordnet')
        nltk.download('stopwords')
    
    @patch('consolebot.query.data_source', MockGithubData)
    def test_preprocess_text_basic(self):
        text = "The quick brown fox jumps over the lazy dog."
        result = preprocess_text(text)
        self.assertEqual(result, "quick brown fox jump lazy dog .")

    @patch('consolebot.query.data_source', MockGithubData)
    def test_preprocess_text_without_stopwords(self):
        text = "This is a simple test."
        result = preprocess_text(text, remove_stopwords=False)
        self.assertEqual(result, "This is a simple test .")

    @patch('consolebot.query.data_source', MockGithubData)
    def test_preprocess_text_empty_string(self):
        text = ""
        result = preprocess_text(text)
        self.assertEqual(result, "")

    @patch('consolebot.query.data_source', MockGithubData)
    def test_preprocess_text_only_stopwords(self):
        text = "The is are were was and or if"
        result = preprocess_text(text)
        self.assertEqual(result, "wa")

    def test_preprocess_text_with_punctuation(self):
        text = "Hello! How are you doing?"
        result = preprocess_text(text)
        self.assertEqual(result, "Hello ! ?")

    @patch('consolebot.query.data_source', MockGithubData)
    def test_preprocess_text_with_stopwords(self):
        text = "This is a sample sentence, showing off the stop words filtration."
        result = preprocess_text(text)
        self.assertEqual(result, "sample sentence , showing stop word filtration .")

class TestDetermineIntent(unittest.TestCase):

    def setUp(self):
        self.intents = {
            'description': ['describe', 'details about', 'information on'],
            'contributing': ['how to contribute', 'contribution guide'],
            'license': ['license info', 'type of license']
        }

    @patch('consolebot.query.data_source', MockGithubData)
    def test_perfect_match(self):
        self.assertEqual(determine_intent('describe', 'TestRepo', self.intents), 'description')

    @patch('consolebot.query.data_source', MockGithubData)
    def test_no_match(self):
        self.assertIsNone(determine_intent('random query that matches nothing', 'TestRepo', self.intents))

    @patch('consolebot.query.data_source', MockGithubData)
    def test_partial_match_above_threshold(self):
        self.assertEqual(determine_intent('info on', 'TestRepo', self.intents), 'description')

    @patch('consolebot.query.data_source', MockGithubData)
    def test_partial_match_below_threshold(self):
        self.assertIsNone(determine_intent('contra', 'TestRepo', self.intents))

    @patch('consolebot.query.data_source', MockGithubData)
    def test_query_with_repo_name(self):
        self.assertEqual(determine_intent('describe TestRepo', 'TestRepo', self.intents), 'description')

class TestGetSummary(unittest.TestCase):

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {"TestRepo": {"name": "TestRepo", "readme": "# Title\nOver the meadow and through the wood to grandomter's house we go", "description": "A test repo."}})
    def test_repo_with_readme(self):
        summary = get_summary("TestRepo")
        self.assertTrue("A test repo.\nTitle John Jingleheimer Schmidt, his name is my name too" in summary)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {"EmptyRepo": {"readme": "", "name":"EmptyRepo", "description": "A test repo."}})
    def test_repo_without_readme(self):
        summary = get_summary("EmptyRepo")
        self.assertEqual(summary, "No summary available.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {})
    def test_repo_not_found(self):
        summary = get_summary("TestRepo")
        self.assertEqual(summary, "Repository not found.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {"TestRepo": {"name": "TestRepo", "readme": "# Title\n:image: my_image.png\nThis is a sample readme. It explains stuff. :note-caption: It's very informative.", "description": "A test repo."}})
    def test_remove_patterns_and_tags(self):
        summary = get_summary("TestRepo")
        for pattern in ['image:', ':note-caption:', ':informationsource:', 'adoc[Learn More]']:
            self.assertNotIn(pattern, summary)
        self.assertNotIn("my_image.png", summary)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {"TestRepo": {"readme": "# Title\nJohn Jingleheimer Schmidt, his name is my name too.", "description": "A test repo.", "name": "TestRepo"}})
    def test_extract_correct_sentences(self):
        summary = get_summary("TestRepo")
        self.assertTrue("A test repo.\nTitle John Jingleheimer Schmidt, his name is my name too" in summary)

    # Mocking the Summarizer so that it doesn't call the actual model for summarization
    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.Summarizer', return_value=Mock(spec=[], side_effect=lambda x, num_sentences: "Summarized content."))
    @patch('consolebot.query.cached_github_data', {"TestRepo": {"name": "TestRepo", "readme": "# Title\nThis is a sample readme.", "description": "A test repo."}})
    def test_nlp_summary(self, mock_summarizer):
        summary = get_summary("TestRepo")
        self.assertTrue("Summarized content." in summary)

class TestRepoMethods(unittest.TestCase):

    mock_data = {
        "TestRepo": {
            "commits": [{"message": "commit1"}, {"message": "commit2"}, {"message": "commit3"}, {"message": "commit4"}, {"message": "commit5"}, {"message": "commit6"}],
            "contributors": ["Alice", "Bob", "Github", "Charlie"],
            "languages": ["Python", "JavaScript"],
            "name": "TestRepo",
            "description": "A test repo.",
            "commits_url": "https://api.github.com/repos/username/TestRepo/commits",

        },
        "EmptyRepo": {
            "name": "EmptyRepo",
        }
    }

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_recent_activity_valid_repo(self):
        result = get_recent_activity("TestRepo")
        self.assertEqual(result, "commit1\ncommit2\ncommit3")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_recent_activity_invalid_repo(self):
        result = get_recent_activity("InvalidRepo")
        self.assertEqual(result, "Repository not found.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_recent_activity_no_commits(self):
        result = get_recent_activity("EmptyRepo")
        self.assertEqual(result, "No recent commits found.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_contributors_valid_repo(self):
        result = get_contributors("TestRepo")
        self.assertEqual(result, "Alice, Bob, Charlie")  # Github should be filtered out

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_contributors_invalid_repo(self):
        result = get_contributors("InvalidRepo")
        self.assertEqual(result, "Repository not found.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_language_valid_repo(self):
        result = get_language("TestRepo")
        self.assertEqual(result, "Python, JavaScript")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_language_invalid_repo(self):
        result = get_language("InvalidRepo")
        self.assertEqual(result, "Repository not found.")

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', mock_data)
    def test_get_language_no_language(self):
        result = get_language("EmptyRepo")
        self.assertEqual(result, "Unknown")

class TestGenerateCombinations(unittest.TestCase):

    @patch('consolebot.query.data_source', MockGithubData)
    def test_generate_combinations_basic(self):
        query = "apple banana cherry"
        expected_combinations = [
            "apple-banana",
            "apple-cherry",
            "banana-cherry",
            "apple-banana-cherry"
        ]
        self.assertCountEqual(generate_combinations(query), expected_combinations)  # Order does not matter

    @patch('consolebot.query.data_source', MockGithubData)
    def test_generate_combinations_with_stopwords(self):
        # Assuming the word 'is' is a stop word
        query = "apple is banana"
        expected_combinations = ["apple-banana"]
        self.assertCountEqual(generate_combinations(query), expected_combinations)

    @patch('consolebot.query.data_source', MockGithubData)
    def test_generate_combinations_single_word(self):
        query = "apple"
        self.assertCountEqual(generate_combinations(query), [])  # No combinations for single word

    @patch('consolebot.query.data_source', MockGithubData)
    def test_generate_combinations_single_word_with_stopwords(self):
        # Assuming the words 'is' and 'an' are stopwords
        query = "apple is an"
        self.assertCountEqual(generate_combinations(query), [])  # No combinations for single word with stopwords

class TestDetermineRepoName(unittest.TestCase):

    def mock_disambiguator(self, matches):
        return matches[1][0]

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {
        "apple-fruit": {},
        "apple-phone": {},
        "grape": {}
    })
    def test_fuzzy_match_with_disambiguation(self):
        query = "aple frt"
        expected_repo_name = "apple-fruit"
        result = determine_repo_name(query, self.mock_disambiguator)
        self.assertEqual(result, expected_repo_name)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {
        "apple-banana": {},
        "apple-cherry": {},
        "grape": {}
    })
    def test_exact_multiword_match(self):
        query = "about apple banana"
        expected_repo_name = "apple-banana"
        self.assertEqual(determine_repo_name(query), expected_repo_name)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {
        "apple": {},
        "banana": {},
        "cherry": {}
    })
    def test_exact_singleword_match(self):
        query = "about apple"
        expected_repo_name = "apple"
        self.assertEqual(determine_repo_name(query), expected_repo_name)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {
        "apple-fruit": {},
        "apple-phone": {},
        "grape": {}
    })
    def test_fuzzy_match_without_disambiguation(self):
        query = "apl frut"
        expected_repo_name = "apple-fruit"
        self.assertEqual(determine_repo_name(query), expected_repo_name)

    @patch('consolebot.query.data_source', MockGithubData)
    @patch('consolebot.query.cached_github_data', {
        "apple": {},
        "banana": {},
        "cherry": {}
    })
    def test_no_appropriate_match(self):
        query = "unknownrepo"
        with self.assertRaises(Exception) as context:
            determine_repo_name(query)
        self.assertTrue("Could not identify a repository" in str(context.exception))


if __name__ == '__main__':
    unittest.main()
