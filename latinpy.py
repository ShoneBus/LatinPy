from bs4.element import ResultSet, Tag
import requests
from bs4 import BeautifulSoup
from re import sub


class language_item:
    language_key: str
    language_name: str
    language_url: str

    def __init__(self, language_key: str, language_name: str, language_url: str):
        self.language_key = language_key
        self.language_name = language_name
        self.language_url = language_url

    def get_translation_url(self, target_word: str) -> str:
        return f'{self.language_url}?parola={target_word}'


class translation_item:
    translation_language_key: str
    translation_target_word: str
    translation_data: str

    def __init__(self, translation_language_key: str, translation_target_word: str):
        self.translation_language_key = translation_language_key
        self.translation_target_word = translation_target_word

    def get_translation_url(self, target_word: str) -> str:
        return f'{self.language_url}?parola={target_word}'


class translation_html_item:
    translation_html_index: int
    translation_html_class: str
    translation_html_text: str

    def __init__(self, translation_html_index: int, translation_html_class: str, translation_html_text: str):
        self.translation_html_index = translation_html_index
        self.translation_html_class = translation_html_class
        self.translation_html_text = translation_html_text


class dictionary_engine:
    languages = {
        'it': language_item('it', 'Italiano', 'https://www.dizionario-latino.com/dizionario-latino-italiano.php'),
        'en': language_item('en', 'English', 'https://www.online-latin-dictionary.com/latin-english-dictionary.php'),
        'fr': language_item('fr', 'Française', 'https://www.grand-dictionnaire-latin.com/dictionnaire-latin-francais.php')
    }

    def __get_translation_url(self, target_word: str, target_language_key: str) -> str:
        if target_language_key not in self.languages.keys():
            available = '\n'.join(
                map(lambda x: f'{x.language_key} - {x.language_name}', self.languages.values()))
            raise KeyError(
                f'Language {target_language_key} not supported.\nAvailable languages: {available}')
        else:
            target_language_item = self.languages[target_language_key]
            return target_language_item.get_translation_url(target_word)

    def __get_html_from_url(self, url: str) -> str:
        r = requests.get(url)
        r.raise_for_status()
        return r.text

    def get_html_from_word(self, word: str, target_language_key: str) -> str:
        return self.__get_html_from_url(self.__get_translation_url(word, target_language_key))

    def get_translation(self, word: str, target_language_key: str) -> str:
        translation_response = self.get_html_from_word(
            word, target_language_key)
        # Request and search translation on online dictionary Olivetti
        soup = BeautifulSoup(translation_response, 'lxml')

        # If there's only one definition
        res: ResultSet[Tag] = soup.select("div#myth > span")

        selection = list(map(lambda x: translation_html_item(0, x.attrs.get('class'), x.text), res))

        print(selection)
        return ''


""""
---------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------

   /$$$$$$  /$$                                     /$$$$$$$
  /$$__  $$| $$                                    | $$__  $$
 | $$  \__/| $$$$$$$   /$$$$$$  /$$$$$$$   /$$$$$$ | $$  \ $$ /$$   /$$  /$$$$$$$
 |  $$$$$$ | $$__  $$ /$$__  $$| $$__  $$ /$$__  $$| $$$$$$$ | $$  | $$ /$$_____/
  \____  $$| $$  \ $$| $$  \ $$| $$  \ $$| $$$$$$$$| $$__  $$| $$  | $$|  $$$$$$
  /$$  \ $$| $$  | $$| $$  | $$| $$  | $$| $$_____/| $$  \ $$| $$  | $$ \____  $$
 |  $$$$$$/| $$  | $$|  $$$$$$/| $$  | $$|  $$$$$$$| $$$$$$$/|  $$$$$$/ /$$$$$$$/
  \______/ |__/  |__/ \______/ |__/  |__/ \_______/|_______/  \______/ |_______/

---------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------
                                - LatinPy v 0.0.1 -
"""
# basic usage example
engine= dictionary_engine()
try:
    target_url= engine.get_translation('puella', 'it')
    print(f'Target Url: {target_url}')
except KeyError as e:
    print(e.args[0])
    print()
