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

    def __str__(self):
        return f'Index: {self.translation_html_index} - Class: {self.translation_html_class} - Text: {self.translation_html_text}'


class citation_item:
    latin: str
    translation: str

    def __init__(self, latin_i: str, translation_i: str) -> None:
        self.latin = latin_i
        self.translation = translation_i


class multiple_translation_result_item:
    lemma: str
    description: str

    def __init__(self, tag: Tag):
        self.lemma = tag.select_one('b').text
        self.description = tag.select_one('i').text


class translation_result_item:
    lemma: str
    paradigm: str
    grammatics: str
    translations: list[str]
    citations: list[citation_item]
    has_desinences: bool

    def __init__(self, tags: list[translation_html_item]):
        self.paradigm = ''
        self.translations = []
        self.citations = []
        cita_1: list[str] = []
        cita_2: list[str] = []
        for tag in tags:
            if tag.translation_html_class == 'lemma':
                self.lemma = tag.translation_html_text
            elif tag.translation_html_class == 'paradigma':
                self.paradigm = tag.translation_html_text
            elif tag.translation_html_class == 'grammatica':
                self.grammatics = tag.translation_html_text
            elif tag.translation_html_class == 'cita_1':
                cita_1.append(tag.translation_html_text)
            elif tag.translation_html_class == 'cita_2':
                cita_2.append(tag.translation_html_text)
            else:
                self.translations.append(tag.translation_html_text)
        if len(cita_1) == len(cita_2):
            for i in range(len(cita_1)):
                self.citations.append(citation_item(cita_1[i], cita_2[i]))
        if len(self.paradigm) > 0:
            self.has_desinences = len(self.paradigm.split(',')) <= 3


class translation_result:
    target_word: str
    found_translations: bool
    found_multiple_translations: bool
    translation_results: translation_result_item
    multiple_translation_results: list[multiple_translation_result_item]


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

    def __make_translation_html_item(self, x: Tag) -> translation_html_item:
        return translation_html_item(0, x.attrs.get('class')[0], x.text)

    def get_html_from_word(self, word: str, target_language_key: str) -> str:
        return self.__get_html_from_url(self.__get_translation_url(word, target_language_key))

    # def __make_translation_result(self, tags: list(translation_html_item)) -> translation_result:

    def get_translation(self, word: str, target_language_key: str) -> translation_result:
        response = translation_result()
        response.target_word = word

        translation_response = self.get_html_from_word(
            word, target_language_key)

        soup = BeautifulSoup(translation_response, 'lxml')
        res: ResultSet[Tag] = soup.select("div#myth > span")
        selection: list[translation_html_item]
        if len(res) > 0:
            selection = list(map(self.__make_translation_html_item, res))
            response.found_multiple_translations = False
            response.multiple_translation_results = []
            response.translation_results = translation_result_item(selection)
            response.found_translations = len(
                response.translation_results.translations) > 0
            response.target_word = response.translation_results.lemma if response.found_translations == True else word
            if response.found_translations and len(response.translation_results.paradigm) < 1 and target_language_key != 'it':
                resp_temp = self.get_translation(response.target_word, 'it')
                response.translation_results.paradigm = resp_temp.translation_results.paradigm
                response.translation_results.has_desinences = resp_temp.translation_results.has_desinences
        else:
            res = soup.select_one(
                "div#container > table#content").find_all('table')
            target_table: Tag = None
            for table in res:
                if table.has_attr('width') and table.attrs['width'] == '100%' and table.find(width='80%') is not None and len(table.find(width='80%')) > 0:
                    target_table = table
                    break
            if target_table is not None and len(target_table) > 0:
                multiple_translation: list[multiple_translation_result_item] = [
                ]
                for trow in target_table.select('tr'):
                    multiple_translation.append(
                        multiple_translation_result_item(trow.select('td')[1]))

                response.multiple_translation_results = multiple_translation
                response.found_multiple_translations = len(
                    response.multiple_translation_results) > 0
                response.translation_results = []
                response.found_translations = response.found_multiple_translations
            else:
                response.found_multiple_translations = False
                response.multiple_translation_results = []
                response.translation_results = []
                response.found_translations = False

        return response


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
engine = dictionary_engine()
try:
    translation = engine.get_translation('laudaveris', 'fr')

    if translation.found_translations:
        if translation.found_multiple_translations:
            print('Multiple translations found!')
            for multiple_translation in translation.multiple_translation_results:
                print(
                    f'{multiple_translation.lemma} - {multiple_translation.description}')
            # facciamo finta che clicco sul primo
            target_new_word = translation.multiple_translation_results[0].lemma
            new_word_result = engine.get_translation(target_new_word, 'en')
            block = 1
        else:
            print('Single translation found!')
            print(f'{translation.translation_results.lemma}:')
            for single_translation in translation.translation_results.translations:
                print(f'{single_translation}')

    else:
        print(f'Translation not found for {translation.target_word}')

except KeyError as e:
    print(e.args[0])
    print()
