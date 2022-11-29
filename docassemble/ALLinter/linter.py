import textstat
import re
import ruamel.yaml
import mako.template
import mako.runtime
import mako.exceptions
import docassemble.webapp.screenreader
import docassemble.base.filter
from typing import List, Tuple, Dict, Mapping, Set, Union
from spellchecker import SpellChecker

__all__ = [
    "get_misspelled_words",
    "get_corrections",
    "load_interview",
    "remove_mako",
    "get_all_headings",
    "get_heading_width",
    "headings_violations",
    "text_violations",
    "get_all_text",
]

def get_misspelled_words(text:str, language:str="en")->Set[str]:
    spell = SpellChecker(language=language)
    return spell.unknown(re.findall(r'\w+', text))
    
def get_corrections(misspelled:Union[Set[str], List[str]], language:str="en")->Mapping[str, Set[str]]:
    spell = SpellChecker(language=language)
    return [
        {
            misspelled_word: spell.corrections(misspelled_word)
        }
       for misspelled_word in misspelled
    ]

mega_list = ('default', 'input type', 'using', 'keep for training',
      'validation messages', 'validate', 'rows', 'maximum image size',
      'image upload type', 'accept', 'allow privileges', 'allow users',
      'persistent', 'private', 'object labeler', 'help generator',
      'image generator', 'required', 'js show if', 'js hide if',
      'js disable if', 'js enable if', 'enable if', 'disable if',
      'show if', 'hide if', 'default', 'hint', 'disable others',
      'uncheck others', 'datatype', 'code', 'address autocomplete',
      'action', 'trigger at', 'exclude', 'choices', 'field metadata',
      'min', 'max', 'minlength', 'maxlength', 'step', 'scale', 'inline',
      'inline width', 'currency symbol', 'shuffle', 'none of the above',
      'field')

def load_interview(content):
  fix_tabs = re.compile(r'\t')
  content = fix_tabs.sub('  ', content)
  return list(ruamel.yaml.safe_load_all(content))

def remove_mako(text:str):
  try: 
    mytemplate = mako.template.Template(text)
    mkdown_text = mytemplate.render()
    html_text = docassemble.base.filter.markdown_to_html(mkdown_text)
    final_text = docassemble.webapp.screenreader.to_text(html_text)
    return final_text
  except Exception as ex:
    return '' 

def get_all_headings(yaml_parsed:List[dict]):
  headings = {}
  for doc in yaml_parsed:
    if not doc:
      continue
    if 'question' in doc and doc['question']:
      if 'id' in doc:
        headings[doc.get('id')] = doc.get('question')
      else:
        headings[f'question: {doc.get("question")}'] = doc.get('question')
  return headings

def get_heading_width(heading_text:str) -> int:
  if not heading_text:
    return 0
  # TODO(bryce): this is _very_ ad hoc: on a DA header, I added all ASCII letters and numbers, and
  # hand counted pixels. Not rigorus, or probably stable, compared to different CSS anything
  # Font was Roboto, at 1.75 rem size.
  char_widths = {
    'a': 13,
    'b': 14,
    'f': 11,
    'i': 4,
    'j': 7,
    'l': 4,
    'm': 23,
    ' ': 9,
    'A': 19,
    'B': 15,
    'F': 13,
    'G': 17,
    'M': 22,
  }
  total_width = 0
  for char in heading_text:
    if char in char_widths:
      total_width += char_widths.get(char, 0)
    elif char.isupper():
      total_width += 18
    elif char.islower():
      total_width += 15
    else:
      # What exactly are these chars?
      total_width += 10
  return total_width

def headings_violations(headings):
  # The widest DA headers get (in px), on a standard mobile device, and on a narrow mobile device
  # (firefox, Pixel 2, and iPhone 5SE)
  violations = []
  stages = [540 * 2, 381 * 2, 290 * 2]
  for key, heading in headings.items():
    heading_width = get_heading_width(heading)
    longer_than_count = sum([heading_width > stage for stage in stages])
    # TODO(brycew): turns out, literally all headers are too big for mobile. Reconsider
    if longer_than_count >= 3:
      if longer_than_count == 1:
        violation_warning = f'Screen `{key}` has a heading that will be multiple lines on narrow devices. You should shorten it: "{heading}"'
      elif longer_than_count == 2:
        violation_warning = f'Screen `{key}` has a heading that will be multiple lines on most mobile devices. You should shorten it: "{heading}"'
      else:
        violation_warning = f'Screen `{key}` has a heading that will be multiple lines. You should shorten it: "{heading}"'
      violations.append(violation_warning)
  return violations

def text_violations(interview_texts:List[str]) -> List[Tuple[str, str]]:
  base_docs_url = 'https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/style_guide'
  # TODO(brycew): read in these lists from a separate data file, shouldn't be in Python
  # https://www.plainlanguage.gov/guidelines/words/use-simple-words-phrases/
  contractions = ("can't", "won't", "don't", "wouldn't", "shouldn't", "couldn't", "y'all", "you've")
  idioms = ("get the hang of", "sit tight", "up in the air", "on the ball", "rule of thumb")
  big_words = {'obtain': 'get', 'receive': 'get', 'whether': 'if', 
               'such as': 'like', 'provide': 'give', 'assist': 'help',
              }
  warnings = []
  for text in interview_texts:
    lower_text = text.lower()
    if '/' in lower_text:
      warnings.append(('Write out "or" rather than using "/" to separate related concepts.',
                     f'{base_docs_url}/readability#target-reading-level'))
    if 'please' in lower_text:
      warnings.append(('Avoid using "please"', f'{base_docs_url}/respect#please'))
    for contraction in contractions:
      if contraction in lower_text:
        warnings.append((f'Avoid contractions like "{contraction}"',
                         f'{base_docs_url}/readability#avoid-contractions'))
    for idiom in idioms:
      if idiom in lower_text:
        warnings.append((f'Avoid idioms, such as {idiom}', 
                         f'{base_docs_url}/readability#avoid-idioms'))
    for big_word, little_word in big_words.items():
      if big_word in lower_text:
        warnings.append((f'Use simple words, such as {little_word}, instead of {big_word}',
                         f'{base_docs_url}/readability#simple-words'))
  return warnings
