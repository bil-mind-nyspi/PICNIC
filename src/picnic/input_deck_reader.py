#!/usr/bin/env python3

# =======================================
# Imports
import sys
import os
import json
import string
import logging

from picnic.cards import get_path_to_json


# =======================================
# Constants
INPUT_DECK_EXTENSION = '.inp'
commenter = '#'

# =======================================
# Classes
class InputDeck():
    """ Input deck reader
    
    InputDeck expects a filename string or a file object.
    
    This will read in an input deck file, check its syntax and create an 
    ordered dictionary of its star cards. This dictionary is the spine of the 
    pipeline. It defines the optional parameters and data lines for each star 
    card controlling which operations the pipeline will do.
    
    The public attributes that are important:
        cards - a list of all the cards as Card obj; [Card, Card]

    Examples
    --------
    >>> inp = InputDeck('example.inp')
    """
    def __init__(self, fn=None):
        """
        :Parameters:
          -. `fn` : a file-like str or File obj, the input deck file
        """
        self.fn = fn
        try: # test if we are getting a File or str
            self.filename = self.fn.name
        except AttributeError:
            self.filename = self.fn
        self.cards = []
        
        if self.fn is not None:
            self.check_inp()
            self.read_inp()
        
    def check_inp(self):
        """
        check that the input deck is an inp file type and that it exists
        """
        logging.info('  Checking the file location')
        if not check_file_extension(self.filename, INPUT_DECK_EXTENSION):
            logging.warning('  ' + self.filename + ' is not a ' + INPUT_DECK_EXTENSION + ' file type, this is an unsupported file format input decks')
        if not check_file_exists(self.filename):
            logging.error('  Error: The file ' + self.filename + ' was not found.')
            raise InputDeckSyntaxError('Error: The file ' + self.filename + ' was not found.')
            
            
    def read_inp(self):
        """
        read in the input deck and assign data for all the star keywords
        """
        print('  Opening file '+self.filename)
        user_defined_parameters = {}
        # loop over all the data, start reading with *start
        with open(self.filename, 'r') as f:
            for line in f:
                if line.lower().strip().startswith('*start'):
                    print('    Reader:    *start')
                    for line in f: # python iterator will continue its iteration until consumed
                        try:
                            line = string.Template(line.strip()).substitute(user_defined_parameters)
                        except KeyError:
                            print(f"ERROR while reading the input deck at {self.filename}: "
                                  f"\n'{line.strip()}' is missing a parameter. "
                                  f"Available parameters are: {user_defined_parameters.keys()}."
                                  f"Did you forget to define a variable?")
                            raise
                        if line.lower().startswith('*end'): # stop reading and exit method at *end
                            print('    Reader:    *end\n\n')
                            return
                        elif not line: # if the line is empty, skip it
                            continue
                        elif line.lower().startswith(commenter):
                            continue
                            
                        # *parameter card is a special card. It always goes at 
                        #   the beginning and it has special rules
                        if line.lower().startswith('*parameter'):
                            parameter_lines = []
                            for line in f: # same deal, continue the iterator until we break
                                line = line.strip()
                                if not line.startswith('*'):
                                    parameter_lines.append(line)
                                else:
                                    # use exec to run the psudo python code for parameters
                                    # Here, we finished accruing parameters and hit a line with a *,
                                    # indicating it's time to move parameters to user_defined_parameters and keep moving down the file.
                                    user_defined_parameters = read_parameter_card(parameter_lines)
                                    
                                    # I personally don't like this, but I can't think of a better way to
                                    #   exit the iterator. Load the first card after *parameter
                                    try:
                                        line = string.Template(line.strip()).substitute(user_defined_parameters)
                                    except KeyError:
                                        print(f"ERROR while reading the input deck at {self.filename}: "
                                              f"\n'{line.strip()}' is missing a parameter. "
                                              f"Available parameters are: {user_defined_parameters.keys()}."
                                              f"Did you forget to define a variable?")
                                        raise
                                    print('    Reader:    ' + line.lower())
                                    print(f"      {len(line.lower().split(','))} items")
                                    self.cards.append(Card(*[itm.strip() for itm in line.lower().split(',')]))
                                    break
                                
                        # create a Card obj for every * keyword, even the ones that are not supported
                        elif line.startswith('*'):
                            print('    Reader:    ' + line.lower())
                            self.cards.append(Card(*[itm.strip() for itm in line.lower().split(',')]))
                                                                        
                        # if the line does not start with * nor is blank, assume it is a data line
                        else:
                            print('    Reader:      '+line)
                            self.cards[-1].add_dataline(line)
        
        # if we get to this point the reader has not found either a *start or *end, exit the pipeline
        logging.error('  Error: Input deck does not contain the either the keyword "*start" or "*end"')
        raise InputDeckSyntaxError('Error: Input deck does not contain the either the keyword "*start" or "*end"')
    
    def add_card(self, cardname, parameters, datalines):
        r""" A public option for adding cards without a separate file
        
        :Parameters:
          -. `cardname` : str, the card's name as a string; \*pet
          -. `parameters` : a tuple of strings or a single dict, the optional
            parameters for the card; ('para_key=para_val', 'para_key=para_val')
            or {'para_key':'para_val', 'para_key':'para_val', ...}
          -. `line` : a list split by ',' or a str, the data line is where the
            user provided information is dictated in the input deck.
        """
        self.cards.append(Card(cardname, parameters))
        for dataline in datalines:
            self.cards[-1].add_dataline = dataline


class Card():
    r"""
    An object storing all the relevant information for '\*' cards
    
    Card expects a name and a tuple of parameters. The tuple can be empty
    
    This will add the parameters and data lines for the card. It will check 
    the syntax of the optional parameters and data lines. It will also read 
    in the defaults from a .json file (keyword.json) and override the 
    default where applicable.
    
    The public attributes that are important:
        :cardname: the name of the card; '\*image'
        :parameters: a dictionary of the parameters; {'para_key': 'para_val'}
        :datalines: a nested list of the data lines for each card;
                    [['filepath'],['arg 1', 'arg 2']]
    
    Examples
    --------
    >>> card = Card(*line.lower().split(','))
    """

    def __init__(self, cardname, *parameters):
        """
        :Parameters:
            -. `cardname` : str, the name of the card; *pet
            -. `parameters` : an unpacked tuple, packed tuple, list or single
                dictionary the optional parameters for the card;
                'para_key=para_val', 'para_key=para_val', ... or
                ('para_key=para_val', 'para_key=para_val', ...) or
                ['para_key=para_val', 'para_key=para_val', ...] or
                {'para_key':'para_val', 'para_key':'para_val', ...}
                the optional parameter is where the user defines how the *card
                should expect to behave or what its attributes may look like
        """

        self.cardname = cardname
        self.parameters = parameters
        
        # load in the default parameters, then overwrite the with the user 
        #  defined parameters
        default_parameters = self._load_defaults()
        self.parameters = self.check_parameter_syntax(default_parameters)
        assert len(self.parameters) == len(default_parameters), (
            f"Error: The optional parameter "
            f"{tuple(set(self.parameters.keys()).difference(default_parameters.keys()))[0]}"
            f" is not supported for the card '{self.cardname}"
        )

        # initialize the dataline list
        self.datalines = []
    
    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, all_paras):
        # change the data type to a dictionary containing para_key: para_value
        if isinstance(all_paras, tuple) or isinstance(all_paras, list):
            try:
                self._parameters = dict([s.split('=') for s in all_paras])
            except AttributeError:
                # we enter this exception because tuple and list do not have a 
                #  split method, this will happen when the user passes a list 
                #  or tuple into Card and the initialization packs it
                self._parameters = dict([s.split('=') for s in all_paras[0]])
            except ValueError:
                # we enter this exception when there is no '=' to split the str
                raise InputDeckSyntaxError('Error: Unexpected syntax for the optional parameters for "' + self.cardname + '"')
        elif isinstance(all_paras, dict):
            self._parameters = all_paras
        else:
            raise TypeError('Error: Unexpected data type passed to Card.parameters must be a tuple or dict')
            
    def _load_defaults(self):
        """
        Set aside in a method so we can change the json if necessary

        :Parameters:
          -. `defaults_path` : file-like str, path to a json file where the
            default values are stored
        """

        # Load the json
        json_path = get_path_to_json(self.cardname[1:].replace(' ', '_'))
        with open(json_path, 'r') as f:
            data = json.load(f)

        # if the card doesn't have a type or the user doesn't provide one, use
        #  the first option in the json
        try:
            for d in data:
                if d['type'] == self.parameters['type']:
                    return d
        except KeyError:
            return data[0]

        # if for some reason we made it through that try statement, default to
        #  empty parameters
        return {}

    def check_parameter_syntax(self, default_parameters):
        """
        Check all the parameters associated with the module
        
        :Parameters:
          -. `default_parameters` : dict, the default parameters associated to
            the type defined by the user
        """
        new_parameters = {}
        # loop over all the default parameters
        for key in default_parameters.keys():
            default_value = default_parameters[key]
            # if the user does not give a parameter for the given card, set it
            #  to the default
            try:
                actual_value = self.parameters[key]
            except KeyError:
                actual_value = default_value

            # if the default value is int, make sure the value given is int
            if isinstance(default_value, int):
                try:
                    new_parameters[key] = int(actual_value)
                # throw error if not an int
                except ValueError:
                    InputDeckSyntaxError('Error: Parameter `' + key + '` from `' + self.cardname + '` expects an integer')

            # if the default value is True/False, make the given value boolean
            elif isinstance(default_value, bool):
                try:
                    if actual_value.lower() in ('true', 'yes', 'y', 'false', 'no', 'n', '.', '-'):
                        new_parameters[key] = actual_value.lower() in ('true', 'yes', 'y')
                    else:
                        InputDeckSyntaxError('Error: Parameter `' + key + '` from `' + self.cardname + '` expects a boolean')
                except AttributeError:
                    new_parameters[key] = bool(actual_value)

            # if the default is a list of available options, make sure the
            #  given is one of them
            elif isinstance(default_value, list):
                if isinstance(actual_value, list):
                    new_parameters[key] = actual_value[0]
                elif isinstance(actual_value, str):
                    if actual_value in default_value:
                        new_parameters[key] = actual_value
                    else:
                        InputDeckSyntaxError('Error: Parameter `' + key + '` from `' + self.cardname + '` must be one of the options: ' + str(default_value))
                else:
                    InputDeckSyntaxError('Error: Parameter `' + key + '` from `' + self.cardname + '` must be one of the options: ' + str(default_value))

            # this control is entered if it is a string (like name or desc)
            else:
                new_parameters[key] = actual_value
        return new_parameters

    def add_dataline(self, line):
        """
        Add to the datalines
        
        :Parameters:
          -. `line` : a list split by ',' or a str, the data line is where the
            user provided information is dictated in the input deck.
        """
        if isinstance(line, str):
            self.datalines.append([itm.strip() for itm in line.strip().split(',')])
        elif hasattr(line, '__iter__'):
            self.datalines.append(line)
        else:
            raise InputDeckSyntaxError('Error: Unexpected data type when setting dataline for card ' + self.cardname)

    @property
    def datalines(self):
        return self._datalines

    @datalines.setter
    def datalines(self, line):
        # confirm the data type is a list, and if not force it to be one
        if not line:
            self._datalines = []
        elif isinstance(line, str):
            self._datalines =[[itm.strip() for itm in line.strip().split(',')]]
        elif hasattr(line, '__iter__'):
            # if the user tries to initalize datalines with multiple datalines
            self._datalines = []
            for l in line:
                if hasattr(l, '__iter__'):
                    self._datalines.append(l)
                else:
                    self._datalines.append([itm.strip() for itm in l.strip().split(',')])
        else:
            raise InputDeckSyntaxError('Error: Unexpected data type when setting dataline for card ' + self.cardname)


class InputDeckSyntaxError(Exception):
    """
    Custom error to trap input deck specific errors
    """
    pass


# =======================================
# Functions
def check_file_extension(filename, extension):
    """
    Check that the file given is the correct extension

    :Parameters:
      -. `filename` : str, the input deck file
      -. `extension` : str, the file extension type (most likely '.inp')
    """
    return os.path.splitext(filename)[-1].lower() == extension


def check_file_exists(filename):
    """
    Check that the file exists where the user thinks it does

    :Parameters:
      -. `filename` : str, the input deck file
    """
    return os.path.exists(filename)


def read_parameter_card(all_the_parameter_lines):
    r"""
    A function built to read and execute the \*parameter keyword. This has to be
    in built in a local space outside the typical object structure to try and
    mitigate some of the danger of using the exec command.
    all_the_parameter_lines = lines of str; this CANNOT be used as a parameter
    name
    """
    # Create a dictionary to hold the parameters
    parameters = {}
    
    # loop over all the parameter lines
    for line in all_the_parameter_lines:
        # Check if the line is not a comment or empty
        if line.strip() and not line.strip().startswith(commenter):
            exec(line, {}, parameters)
    
    return parameters
    

def read_input_deck(input_deck):
    """
    A function that will call the InputDeck class and fill it given a file
    """
    return InputDeck(input_deck)


def make_card(cardname, parameters=None, datalines=None):
    """
    create a Card class on the fly

    :Parameters:
      -. `cardname` : str, the card used, ex: *import, *reconall
      -. `parameters` : list, dict or tuple, the card parameters
      -. `datalines` : list of str, the instance or file-like str
    """
    # make sure the keyword starts with a star indicator
    if not cardname.startswith('*'):
        cardname = '*' + cardname
    
    # if there are user defined parameters, load those in
    if parameters is not None:
        card = Card(cardname, *parameters)
    else:
        card = Card(cardname)
    
    # add the datalines
    if datalines is not None:
        for line in datalines:
            card.add_dataline(line)
    return card


# =======================================
# Main
def main():
    # assume the user is passing in an inp
    if len(sys.argv) < 1:
        logging.error('Error: No input deck file found')
    return read_input_deck(sys.argv[0])

if __name__ == '__main__':
    main()
    