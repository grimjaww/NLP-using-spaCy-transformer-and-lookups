#!/usr/bin/python
# -*- coding: utf-8 -*-
import io
import os
import pprint

import spacy
from spacy.matcher import Matcher

from . import utilities

class Parser(object):

    def __init__(self, input_file):
        nlp = spacy.load('en_core_web_sm')

        # load custom trained model
        root = os.path.dirname(os.path.abspath(__file__))
        model = os.path.join(root, 'model')
        trained_entity_recognizer = spacy.load(model)

        self.__matcher = Matcher(nlp.vocab)

        self.__details = {
            'name': None,
            'email': None,
            'skills': None,
            'education': None,
            'qualification': None,
            'profile': None,
            'previous_associations': None,
            'total_experience': None,
            }

        self.__raw_file = input_file
        if not isinstance(self.__raw_file, io.BytesIO):
            ext = os.path.splitext(self.__raw_file)[1].split('.')[1]
        else:
            ext = self.__raw_file.name.split('.')[1]

        self.__text_raw = utilities.extract_text(self.__raw_file, '.'+ ext)
        self.__text = ' '.join(self.__text_raw.split())

        self.__spacy_nlp_token = nlp(self.__text)
        self.__noun_chunks = list(self.__spacy_nlp_token.noun_chunks)

        self.__trained_nlp_token = \
            trained_entity_recognizer(self.__text_raw)

        self.__get_basic_details()

        
    def get_extracted_data(self):
        return self.__details

    def __get_basic_details(self):

        # extraction based on simple regex matching

        # extract email
        email = utilities.extract_email(self.__text)
        self.__details['email'] = email



        # get domain specific entites from the trained model

        specific_entites = \
            utilities.extract_entities(self.__trained_nlp_token)


        # extraction based on spacy pattern matching and trained entity recognizer

        # extract name

        name = utilities.extract_name(self.__spacy_nlp_token,
                matcher=self.__matcher)

        try:
            self.__details['name'] = specific_entites['name'][0]
        except (IndexError, KeyError):
            self.__details['name'] = name

        # extraction based on spacy tokenization and noun chunks

        # extract skills

        skills = utilities.extract_skills(self.__spacy_nlp_token,
                self.__noun_chunks)
        self.__details['skills'] = skills

        # extraction using trained entity recognizer

        # extract profile

        try:
            self.__details['profile'] = specific_entites['profile']
        except KeyError:
            pass

        # extract academic qualification

        try:
            self.__details['qualification'] = \
                specific_entites['qualification']
        except KeyError:
            pass

        # extract previous companies

        try:
            self.__details['previous_associations'] = \
                specific_entites['companies']
        except KeyError:
            pass

        # To extract content specific sections/entites from the file

        sections = utilities.extract_sections(self.__text_raw)

        # extraction using spacy default entity recognizer
        # can be extended to extract more information as mentioned in the keywords file.

        # extract education details

        try:
            self.__details['education'] = sections['education']
        except KeyError:
            pass

        # extract total experience

        try:
            exp = \
                  round(utilities.get_total_experience(sections['experience']) / 12, 2)
            self.__details['total_experience'] = exp
        except KeyError:
            self.__details['total_experience'] = 0

        return


def extraction_wrapper(input_file):
    parser = Parser(input_file)
    return parser.get_extracted_data()
