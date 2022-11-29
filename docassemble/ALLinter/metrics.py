import abc
from enum import Enum
from typing import Iterable, NewType
from pikepdf import Pdf

from spacy.lang.en import English

class FormUnit(Enum):
  WHOLE_FORM = 1
  QUESTION_WITH_SURROUND = 2 # just a page in a PDF
  QUESTION = 3 # not really present in PDF, can't split well
  FIELD = 4
  SENTENCE = 5
  WORD = 6

class DesiredOutcome(Enum):
  QUICK_COMPLETION = 1
  # Really readable and comprehendible
  READABLE = 2
  # topics challenging to answer
  # sensitivity
  BUILD_TRUST = 3
  QUESTION_FLOW = 4
  RESPECT_PRIVACY = 5
  FEEL_HEARD = 6

class HowUsed(Enum):
  TO_IMPROVE = 1
  IRREDUCIBLE = 2

def make_spacy_pipeline():
  nlp = English()
  nlp.add_pipe('sentencizer')
  return nlp

nlp = make_spacy_pipeline()

# Assuming code-in-fields have been parsed
InterviewWholeForm = NewType(Iterable[dict])
# The same type techinally, but the list should be much shorter and more
# organized, ideally the current question, followed by the previous and the next
InterviewQuestionWithSurround = NewType(Iterable[dict])
InterviewQuestion = NewType(dict)
# Also a subset of the question: should have the field label, type, and options
class InterviewField(TypedDict):
  label: str
  datatype: str
  inputtype: str # like area, dropdown, radio, etc.
  options: Iterable[str] # the iterables has the labels
  required: bool
# Just the whole sentence
InterviewSentence = NewType(str)
# just a single word (ignoring puncuation)
InterviewWord = NewType(str)

def _get_all_text(yaml_parsed:InterviewWholeForm):
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
          words_temp.append('maybe')
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
                if field_attr == 'code' or field_attr == 'no label':
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
            if field_attr in ['validation_message', 'help', 'hint']:
              continue
            elif field_attr in ['label', 'note', 'html']:
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

def get_whole_form(yaml_parsed:InterviewWholeForm):
  return yaml_parsed

def get_all_questions(yaml_parsed:InterviewWholeForm) -> Iterable[InterviewQuestion]:
  questions = []
  for doc in yaml_parsed:
    if doc and 'question' in doc:
      questions.append(Question(doc))
  return questions

def get_all_fields(yaml_parsed:InterviewWholeForm):
  fields = []
  def option_label(opt):
    if isinstance(opt, list) or isinstance(opt, tuple):
      return opt[0] if len(opt) > 0 else None
    elif isinstance(opt, dict):
      if 'label' in opt:
        return opt['label']
      else:
        for key in opt.keys():
          # TODO(brycew): do something with images?
          if key not in ['label', 'value', 'default', 'help', 'image', 'code']:
            return key
        return None
    elif isinstance(opt, str):
      return opt
    return None

  for doc in yaml_parsed:
    if doc:
      for field_type in ['yesno', 'noyes', 'yesnomaybe', 'noyesmaybe']:
        if field_type in doc:
          if field_type in ['yesno', 'noyes']:
            options = ['yes', 'no']
          else:
            options = ['yes', 'no', 'maybe']
          label = doc.get('question', '')
          required = True
          datatype = 'boolean'
          inputtype = 'buttons'
          fields.append({'label': label, 'options': options, 
              'required': required, 'datatype': datatype, 'inputtype': inputtype})
          break
      # TODO(brycew): buttons: are the question / subquestion the labels for those?
      for field_type in ['choices', 'dropdown', 'combobox', 'buttons']:
        if field_type in doc:
          # TODO(brycew): doesn't get `code` layout of fields
          options = []
          if isinstance(doc[field_type], list):
            options = [option_label(opt) for opt in doc[field_type]]
          elif isinstance(doc[field_type], dict):
            options = [option_label(opt) for opt in doc[field_type].items()]
        label = doc.get('question', '')
        required = True
        datatype = 'text'
        inputtype = 'radio' if field_type == 'choices' else field_type
        fields.append({'label': label, 'options': options, 
            'required': required, 'datatype': datatype, 'inputtype': inputtype})
        break
      if 'signature' in doc:
        label = doc.get('question', '')
        required = True
        datatype = 'signature'
        inputtype = 'signature'
        options = []
        fields.append({'label': label, 'options': options, 
            'required': required, 'datatype': datatype, 'inputtype': inputtype})
        continue
      if 'fields' in doc:
        fields_section = doc.get('fields')
        if isinstance(fields_section, dict):
          fields_section = [fields_section]
        for field in fields_section:
          if 'code' in field:
            continue
          label = None
          if 'label' in field:
            label = field['label']
          else:
            for field_attr in field:
              if field_attr not in mega_list:
                label = field_attr
          datatype = field.get('datatype', 'text')
          inputtype = field.get('input type', None)
          required = field.get('required', True)
          options = []
          if datatype in ['checkboxes']:
            options_val = field['choices']
            if isinstance(options_val, list):
              options = [option_label(opt) for opt in options_val]
            elif isinstance(doc[field_type], dict):
              options = [option_label(opt) for opt in options_val.items()]
          fields.append({'label': label, 'options': options, 
              'required': required, 'datatype': datatype, 'inputtype': inputtype})
          continue
  return fields

def get_all_sentences(yaml_parsed:InterviewWholeForm):
  all_text = _get_all_text(yaml_parsed)
  doc = nlp(all_text)
  return doc.sents

def get_all_words(yaml_parsed:InterviewWholeForm):
  all_text = _get_all_text(yaml_parsed)
  doc = nlp(all_text)
  return doc

class Metric(abc.ABC):
  def __init__(self, desired_outcome, how_used):
    self.base_unit = ...
    # above this value, we show the error
    self.violation_value = ...
    # self.output_over_base_unit
    self.desired_outcome = desired_outcome
    self.how_used = how_used

  def process_base_unit(self, unit):
    pass

  def process_pdf_base_unit(self, unit):
    pass

  def aggregate(self, agg_unit, unit):
    pass

  def aggregate_pdf(self, agg_unit, unit):
    pass

  def suggestion(self, unit):
    pass

class UncommonWords(Metric):
  def __init__(self):
    self.base_unit = FormUnit.WORD
    # glanced at things around this range, and it's entirely mispellings and wacky words
    self.violation_value = 40000
    self.desired_outcome = DesiredOutcome.READABLE
    self.how_used = HowUsed.TO_IMPROVE

    with open('data/sources/court_1w.txt') as f:
      self._all_words = {line.split('\t')[0]: int(line.split('\t')[1]) for line in f.read().split('\n')}

  def process_base_unit(self, word):
    """unit is a single word at a time"""
    # TODO(brycew): clean up the word
    return (self._all_words.get(word, 10), 1) # 10 is a very low score, maybe raise?
  
  def aggregate(self, agg_unit, unit):
    self.process_base_unit(unit)
    return 

class TotalFields(Metric):
  def __init__(self):
    self.base_unit = FormUnit.FIELD
    self.desired_outcome = DesiredOutcome.QUICK_COMPLETION
    self.how_used = HowUsed.TO_IMPROVE

  def process_base_unit(self, field):
    return 1

  def aggregate(self, agg_unit, unit):
    return 


class MetricRunner:
  def __init__(self, metrics, interview=None, pdf_file=None):
    self.metrics = metrics
    self.metrics_by_unit = {}
    for metric in self.metrics:
      if metric.base_unit in self.metrics_by_unit:
        self.metrics_by_unit[metric.base_unit].append(metric)
      else:
        self.metrics_by_unit[metric.base_unit] = [metric]
    #TODO(brycew): continue here
    if interview and pdf_file:
      raise Exception("Should only have one of YAML interview or PDF file")

    if interview:
      self.yaml_parsed = load_interview(interview)
    
    if pdf_file:
      self.pdf_obj = Pdf.read(pdf_file)

  def get_stats(self):
    pass

  def calculate_score(self):
    all_stats = self.get_stats()
    pass
