#!/usr/bin/python
# -*- coding: utf-8 -*-
import io
import os
import re

from datetime import datetime
from dateutil import relativedelta

import pandas as pd

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from . import keywords as kw


def extract_text_from_pdf(pdf_path):
    '''
    Helper function to extract the plain text from .pdf files

    :param pdf_path: path to PDF file to be extracted (remote or local)
    :return: iterator of string of extracted text
    '''

    # https://www.blog.pythonlibrary.org/2018/05/03/exporting-data-from-pdfs-with-python/
    if not isinstance(pdf_path, io.BytesIO):

        # extract text from local pdf file

        with open(pdf_path, 'rb') as fh:
            try:
                for page in PDFPage.get_pages(fh, caching=True,
                        check_extractable=True):
                    resource_manager = PDFResourceManager()
                    fake_file_handle = io.StringIO()
                    converter = TextConverter(resource_manager,
                            fake_file_handle, codec='utf-8',
                            laparams=LAParams())
                    page_interpreter = \
                        PDFPageInterpreter(resource_manager, converter)
                    page_interpreter.process_page(page)

                    text = fake_file_handle.getvalue()
                    yield text

                    # close open handles
                    converter.close()
                    fake_file_handle.close()
            except PDFSyntaxError:
                return
    else:

        # extract text from remote pdf file

        try:
            for page in PDFPage.get_pages(pdf_path, caching=True,
                    check_extractable=True):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                converter = TextConverter(resource_manager,
                        fake_file_handle, codec='utf-8',
                        laparams=LAParams())
                page_interpreter = PDFPageInterpreter(resource_manager,
                        converter)
                page_interpreter.process_page(page)

                text = fake_file_handle.getvalue()
                yield text

                # close open handles

                converter.close()
                fake_file_handle.close()
        except PDFSyntaxError:
            return


def extract_text(file_path, extension):
    '''
    Wrapper function to detect the file extension and call text
    extraction function accordingly

    :param file_path: path of file of which text is to be extracted
    :param extension: extension of file `file_name`
    '''

    text = ''
    if extension == '.pdf':
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page

    return text


def extract_entities(nlp_text):
    '''
    Helper function to extract different entities with custom
    trained model using SpaCy's NER

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :return: dictionary of entities
    '''

    entities = {}
    for ent in nlp_text.ents:
        if ent.label_ not in entities.keys():
            entities[ent.label_] = [ent.text]
        else:
            entities[ent.label_].append(ent.text)
    for key in entities.keys():
        entities[key] = list(set(entities[key]))
    return entities


def extract_email(text):
    '''
    Helper function to extract email id from text

    :param text: plain text extracted from resume file
    '''

    email = re.findall(r"([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None


def extract_name(nlp_text, matcher):
    '''
    Helper function to extract name from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param matcher: object of `spacy.matcher.Matcher`
    :return: string of full name
    '''

    pattern = [kw.NAME_PATTERN]

    matcher.add('NAME', None, *pattern)

    matches = matcher(nlp_text)

    for (_, start, end) in matches:
        span = nlp_text[start:end]
        if 'name' not in span.text.lower():
            return span.text


def extract_skills(nlp_text, noun_chunks):
    '''
    Helper function to extract skills from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: list of skills extracted
    '''

    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv(os.path.join(os.path.dirname(__file__),
                       'data/skills.csv'))

    skills = list(data.columns.values)
    skillset = []

    # check for one-grams
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)

    # check for bi-grams and tri-grams
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)

        return [i.capitalize() for i in set([i.lower() for i in
                skillset])]


def extract_sections(text):
    '''
    Helper function to extract all the raw text from sections of
    file

    :param text: Raw text
    :return: dictionary of entities
    '''

    text_split = [i.strip() for i in text.split('\n')]

    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(kw.SECTIONS)
			
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
			
        if p_key in kw.SECTIONS:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)

    return entities


def get_total_experience(experience_list):
    '''
    Wrapper function to extract total months of experience from a resume

    :param experience_list: list of experience text extracted
    :return: total months of experience
    '''

    exp_ = []
    for line in experience_list:
        experience = \
            re.search(r'(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present)'
                      , line, re.I)
        if experience:
            exp_.append(experience.groups())
    total_exp = sum([get_number_of_months_from_dates(i[0], i[2])
                    for i in exp_])
    total_experience_in_months = total_exp
    return total_experience_in_months


def get_number_of_months_from_dates(date1, date2):
    '''
    Helper function to extract total months of experience from a resume

    :param date1: Starting date
    :param date2: Ending date
    :return: months of experience from date1 to date2
    '''

    if date2.lower() == 'present':
        date2 = datetime.now().strftime('%b %Y')

    try:
        if len(date1.split()[0]) > 3:
            date1 = date1.split()
            date1 = (date1[0])[:3] + ' ' + date1[1]
        if len(date2.split()[0]) > 3:
            date2 = date2.split()
            date2 = (date2[0])[:3] + ' ' + date2[1]
    except IndexError:
        return 0
    
    try:
        date1 = datetime.strptime(str(date1), '%b %Y')
        date2 = datetime.strptime(str(date2), '%b %Y')
        months_of_experience = relativedelta.relativedelta(date2, date1)
        months_of_experience = months_of_experience.years * 12 \
            + months_of_experience.months
    except ValueError:
        return 0
    
    return months_of_experience
