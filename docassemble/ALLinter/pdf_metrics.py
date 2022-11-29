from formfyxer.pdf_wrangling import *

def _pdf_readabliity_scores(pdf_obj):
    """Return readability stats for the PDF.
    Include the classics"""
    pass

def _pdf_readability_word_lists(pdf_obj):
    """Dale-chall specifically"""
    pass

def _pdf_legal_citations(pdf_obj):
    """Return if there are legal citations"""
    pass

def _pdf_legal_vocab(pdf_obj):
    """Return if there are legal specific vocab in the pdf"""
    pass

def _pdf_multi_barrelled_qs(pdf_obj):
    pass

def _pdf_total_fields(pdf_obj):
    return len(get_existing_pdf_fields(pdf_obj))

def _pdf_avg_fields_per_page(pdf_obj):
    return _pdf_total_fields(pdf_obj) / _pdf_total_pages(pdf_obj)

def _pdf_total_pages(pdf_obj):
    return len(pdf_obj.pages)

def _pdf_total_length_of_answers(pdf_obj):
    pass

def _pdf_conditional_question(pdf_obj):
    pass

def _pdf_redundant_question(pdf_obj):
    pass

def _pdf_exact_question(pdf_obj):
    """i.e. date or dollar figure"""
    pass

def _pdf_calculation(pdf_obj):
    """calculation"""
    pass
