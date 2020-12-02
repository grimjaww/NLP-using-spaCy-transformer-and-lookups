#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Example of training an additional entity type

This script shows how to add a new entity type to an existing pretrained NER
model. To keep the example short and simple, only four sentences are provided
as examples. In practice, you'll need many more — a few hundred would be a
good start. You will also likely need to mix in examples of other entity
types, which might be obtained by running the entity recognizer over unlabelled
sentences, and adding their annotations to the training set.

The actual training is performed by looping over the examples, and calling
`nlp.entity.update()`. The `update()` method steps through the words of the
input. At each word, it makes a prediction. It then consults the annotations
provided on the GoldParse instance, to see whether it was right. If it was
wrong, it adjusts its weights so that the correct action will score higher
next time.

After training your model, you can save it to a directory. We recommend
wrapping models as Python packages, for ease of deployment.

For more details, see the documentation:
* Training: https://spacy.io/usage/training
* NER: https://spacy.io/usage/linguistic-features#named-entities

Compatible with: spaCy v2.1.0+
Last tested with: v2.2.4
"""

from __future__ import unicode_literals, print_function

import re
import json
import random
import itertools
from itertools import filterfalse
from pathlib import Path

import plac

import spacy
from spacy.util import minibatch, compounding

import logging
import warnings


# new entity label

LABEL = 'COL_NAME'

def trim_entity_spans(data):
    invalid_span_tokens = re.compile(r'\s')

    cleaned_data = []
    for text, annotations in data:
        entities = annotations['entities']
        valid_entities = []
        for start, end, label in entities:
            valid_start = start
            valid_end = end
            while valid_start < len(text) and invalid_span_tokens.match(
                    text[valid_start]):
                valid_start += 1
            while valid_end > 1 and invalid_span_tokens.match(
                    text[valid_end - 1]):
                valid_end -= 1
            valid_entities.append([valid_start, valid_end, label])
        cleaned_data.append([text, {'entities': valid_entities}])

    return cleaned_data


def convert_dataturks_to_spacy(dataturks_json_file_path):

    try:
        training_data = []
        lines = []
        with open(dataturks_json_file_path, 'r', encoding='utf-8') as f:
            train_raw = json.load(f)
            counter = len(train_raw)

            for count in range(counter):
                
                row = train_raw[count]
                data = row["_data_{}".format(count + 1)]
            
                text = data['content']
                entities = []
                if data['annotation'] is not None:

                    for annotation in data['annotation']:
                        # only a single point in text annotation.
                        point = annotation['points'][0]
                        labels = annotation['label']
                        # handle both list of labels or a single label.
                        if not isinstance(labels, list):
                            labels = [labels]

                        for label in labels:
                            # dataturks indices are both inclusive [start, end]
                            # but spacy is not [start, end)
                            entities.append((
                                point['start'],
                                point['end'] + 1,
                                label
                            ))

                training_data.append((text, {"entities": entities}))
        return training_data
    
    except Exception:
        logging.exception('Unable to process: '+ dataturks_json_file_path)
        return None


TRAIN_DATA = \
    trim_entity_spans(convert_dataturks_to_spacy('data/train.json'))


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", 'option', 'm', str),
    new_model_name=('New model name for model meta.', 'option', 'nm', str),
    output_dir=('Optional output directory', 'option', 'o', Path),
    n_iter=('Number of training iterations', 'option', 'n', int)
)
def main(
    model=None,
    new_model_name='named_entity_recognizer',
    output_dir='./model',
    n_iter=30,
    ):
    """Set up the pipeline and entity recognizer, and train the new entity."""

    random.seed(0)
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank('en')  # create blank Language class
        print("Created blank 'en' model")

    # Add entity recognizer to model if it's not in the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy

    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner, last=True)

    # otherwise, get it, so we can add labels to it    
    else:
        ner = nlp.get_pipe('ner')

    # add labels
    for (_, annotations) in TRAIN_DATA:
        for ent in annotations.get('entities'):
            if ent[2] == "Links":
                continue
            ner.add_label(ent[2])

    if model is None or reset_weights:
        optimizer = nlp.begin_training()
    else:
        optimizer = nlp.resume_training()
        
    move_names = list(ner.move_names)

    # inititate pipeline
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']

    with nlp.disable_pipes(*other_pipes), warnings.catch_warnings():
        # show warnings for misaligned entity spans once
        warnings.filterwarnings("once", category=UserWarning, module='spacy')

        # batch up the examples using spaCy's minibatch
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text, annotations in TRAIN_DATA:
                nlp.update([text], [annotations], sgd=optimizer, drop=0.35, losses=losses)
            
            print('Losses', losses)

    # test the trained model

    test_text = 'Amity University'
    doc = nlp(test_text)
    print("Entities in '%s'" % test_text)
    for ent in doc.ents:
        print(ent.label_, ent.text)


    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.meta['name'] = new_model_name  # rename model
        nlp.to_disk(output_dir)
        print('Saved model to', output_dir)

        # test the saved model
        print('Loading from', output_dir)
        nlp2 = spacy.load(output_dir)

        # Check the classes have loaded back consistently
        assert nlp2.get_pipe('ner').move_names == move_names
        doc2 = nlp2(test_text)
        for ent in doc2.ents:
            print(ent.label_, ent.text)

if __name__ == '__main__':
    plac.call(main)
