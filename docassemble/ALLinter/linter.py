import textstat
import mako.template
import mako.runtime
import mako.exceptions
import docassemble.webapp.screenreader
import docassemble.base.filter
from typing import List, Tuple

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
    if 'question' in doc:
      if 'id' in doc:
        headings[doc.get('id')] = doc.get('question')
      else:
        headings[f'question: {doc.get("question")}'] = doc.get('question')
  return headings

def get_heading_width(heading_text:str) -> int:
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
  stages = [540, 381, 290]
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

def get_all_text(yaml_parsed:List[dict]):
  """identify all questions that set a variable in the interview
  they will be added as a dictionary of label: field, with other modifiers"""
  words_temp = []
  for doc in yaml_parsed:
    if doc:
      for text_section in ['question', 'subquestion', 'under', 'pre', 'post', 'right']:
        if text_section in doc:
          words_temp.append(doc.get(text_section))
      if 'help' in doc:
        help_section = doc.get('help')
        # TODO(brycew) is a help dict valid w/o both content and label?
        if isinstance(help_section, dict):
          words_temp.append(help_section.get('content', ''))
          words_temp.append(help_section.get('label', ''))
        elif isinstance(help_section, str):
          words_temp.append(help_section)
      if 'terms' in doc:
        terms_section = doc.get('terms')
        if isinstance(terms_section, dict):
          for term, definition in terms_section.items():
            words_temp.append(definition)
        elif isinstance(terms_section, list):
          for term_item in terms_section:
            if 'definition' in term_item:
              words_temp.append(term_item.get('definition'))
      # TODO(brycew): handle all the different types of questions
      for field_type in ['yesno', 'noyes']:
        if field_type in doc:
          words_temp.append('yes')
          words_temp.append('no')
      for field_type in ['yesnomaybe', 'noyesmaybe']:
        if field_type in doc:
          words_temp.append('yes')
          words_temp.append('no')
          word_temp.append('maybe')
      # TODO(brycew): buttons is parsed separately in DA core: why?
      for field_type in ['choices', 'dropdown', 'combobox', 'buttons']:
        if field_type in doc:
          # TODO(brycew): doesn't get `code` layout of fields
          if isinstance(doc.get(field_type), list):
            # NOTE: check out parse.py:parse_fields() (5973)
            for field_item in doc.get(field_type):
              if isinstance(field_item, str):
                words_temp.append(field_item)
                continue
              if 'help' in field_item:
                words_temp.append(field_item.get('help'))
              for field_attr in field_item:
                if field_attr not in ['help', 'default']:
                  words_temp.append(field_item.get(field_attr))
                if field_attr == 'code':
                  continue
                elif field_attr == 'no label':
                  continue
                else:
                  words_temp.append(field_attr)        
      if 'fields' in doc:
        fields_section = doc.get('fields')
        if isinstance(fields_section, dict):
          fields_section = [fields_section]
        for field in fields_section:
          if 'code' in field:
            continue
          for field_attr in field:
            if field_attr == 'validation_message':
              continue
            elif field_attr == 'help' or field_attr == 'hint':
              continue
            elif field_attr == 'label':
              words_temp.append(field_attr.get(field_attr))
            elif field_attr == 'note' or field_attr == 'html':
              words_temp.append(field.get(field_attr))
            elif field_attr == 'choices':
              for choice in field.get('choices'):
                if len(choice) == 1:
                  words_temp.append(choice)
                elif 'label' in choice:
                  words_temp.append(choice.get('label'))
            elif field_attr not in mega_list:
              words_temp.append(field_attr)
          
  return words_temp