from .NFA import NFA

EPSILON = ''
SPECIAL_CHARS = ['*', '+', '?', '|', '(', ')', '[', ']']

class ParseError(Exception):
    pass
class Regex:
    def thompson(self) -> NFA[int]:
        raise NotImplementedError('the thompson method of the Regex class should never be called')

# you should extend this class with the type constructors of regular expressions and overwrite the 'thompson' method
# with the specific nfa patterns. for example, parse_regex('ab').thompson() should return something like:

# >(0) --a--> (1) -epsilon-> (2) --b--> ((3))

# extra hint: you can implement each subtype of regex as a @dataclass extending Regex
class Caracter(Regex):
    def __init__(self, caracter):
        self.caracter = caracter

    def thompson(self) -> NFA[int]:
        q0 = 0
        q1 = 1
        alphabet = {self.caracter}
        transitions = {(q0, self.caracter): {q1}} # tranzitie de la q0 la q1 pe caracter
        return NFA(alphabet, {q0, q1}, q0, transitions, {q1}) # returnare NFA creat


class BigLetters(Regex):
    def __init__(self):
        characters = [Caracter(chr(char)) for char in range(ord('A'), ord('Z') + 1)]
        self.regex = characters[0] # luam prima litera din range
        for char in characters[1:]: # parcurgem restul literelor
            self.regex = Union(self.regex, char) # facem un union cu restul literelor

    def thompson(self) -> NFA[int]:
        return self.regex.thompson() # returnam NFA-ul creat



class SmallLetters(Regex):
    def __init__(self):
        characters = [Caracter(chr(char)) for char in range(ord('a'), ord('z') + 1)]
        self.regex = characters[0]
        for char in characters[1:]:
            self.regex = Union(self.regex, char)

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()
    # asemanator cu BigLetters

class Digits(Regex):
    def __init__(self):
        characters = [Caracter(chr(char)) for char in range(ord('0'), ord('9') + 1)]
        self.regex = characters[0]
        for char in characters[1:]:
            self.regex = Union(self.regex, char)

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()
    # asemanator cu BigLetters



class Concat(Regex):
    def __init__(self, regex1, regex2):
        self.regex1 = regex1
        self.regex2 = regex2

    def thompson(self) -> NFA[int]:
        nfa1 = self.regex1.thompson() # cream NFA pentru primul regex
        nfa2 = self.regex2.thompson() # cream NFA pentru al doilea regex

        # Transformam starile lui nfa2 pentru a nu avea conflicte cu starile lui nfa1
        nfa2_states_transformed = self._transform_states(nfa2.K, nfa1.K)

        # Apply the transformation to the transition states of nfa2
        nfa2_transitions_transformed = {
            (self._transform_state(state, nfa1.K), symbol): self._transform_state_set(next_states, nfa1.K)
            for (state, symbol), next_states in nfa2.d.items()
        }

        # Create the set of states and alphabet for the Concat NFA
        states = nfa1.K.union(nfa2_states_transformed)
        alphabet = nfa1.S.union(nfa2.S)

        # Create the new transitions dictionary
        transitions = nfa1.d.copy()
        transitions.update(nfa2_transitions_transformed)

        # Epsilon transitions from the final states of nfa1 to the initial state of nfa2
        for final_state in nfa1.F:
            transitions.setdefault((final_state, EPSILON), set()).add(self._transform_state(nfa2.q0, nfa1.K))

        start_state = nfa1.q0
        final_states = self._transform_state_set(nfa2.F, nfa1.K)

        return NFA(alphabet, states, start_state, transitions, final_states)

    def _transform_states(self, states, existing_states):
        # transforma starile lui nfa2 pentru a nu avea conflicte cu starile lui nfa1, adaugand un offset
        max_existing_state = max(existing_states)
        return {state + max_existing_state + 1 for state in states}

    def _transform_state(self, state, existing_states):
        # la fel dar pentru o stare
        max_existing_state = max(existing_states)
        return state + max_existing_state + 1

    def _transform_state_set(self, state_set, existing_states):
        return {self._transform_state(state, existing_states) for state in state_set}



class Union(Regex):
    def __init__(self, regex1, regex2):
        self.regex1 = regex1
        self.regex2 = regex2

    def thompson(self) -> NFA[int]:
        nfa1 = self.regex1.thompson()
        nfa2 = self.regex2.thompson()

        nfa2_states_transformed = self._transform_states(nfa2.K, nfa1.K)

        # Apply the transformation to the transition states of nfa2
        nfa2_transitions_transformed = {
            (self._transform_state(state, nfa1.K), symbol): self._transform_state_set(next_states, nfa1.K)
            for (state, symbol), next_states in nfa2.d.items()
        }

        # Create a new start state for the Union NFA
        new_start_state = self._new_start_state(nfa1.K, nfa2_states_transformed)

        # Create the set of states and alphabet for the Union NFA
        states = nfa1.K.union(nfa2_states_transformed).union({new_start_state})
        alphabet = nfa1.S.union(nfa2.S)

        # Create the new transitions dictionary unpacking care permite extragerea și includerea tuturor perechilor cheie-valoare
        # dintr-un dictionar in altul
        transitions = {**nfa1.d, **nfa2_transitions_transformed}
        transitions[(new_start_state, EPSILON)] = {nfa1.q0, self._transform_state(nfa2.q0, nfa1.K)}

        final_states = nfa1.F.union(self._transform_state_set(nfa2.F, nfa1.K))

        return NFA(alphabet, states, new_start_state, transitions, final_states)

    def _transform_states(self, states, existing_states):
        max_existing_state = max(existing_states)
        return {state + max_existing_state + 1 for state in states}

    def _transform_state(self, state, existing_states):
        max_existing_state = max(existing_states)
        return state + max_existing_state + 1

    def _transform_state_set(self, state_set, existing_states):
        return {self._transform_state(state, existing_states) for state in state_set}

    def _new_start_state(self, states_nfa1, states_nfa2_transformed):
        return max(states_nfa1.union(states_nfa2_transformed)) + 1


class Star(Regex):
    def __init__(self, regex):
        self.regex = regex

    def thompson(self) -> NFA[int]:
        inner_nfa = self.regex.thompson()

        new_start_state = max(inner_nfa.K) + 1
        new_final_state = new_start_state + 1

        new_states = self._create_new_states(inner_nfa.K, new_start_state, new_final_state)
        new_alphabet = self._create_new_alphabet(inner_nfa.S)
        new_transitions = self._create_new_transitions(inner_nfa, new_start_state, new_final_state)

        new_final_states = {new_final_state}

        return NFA(new_alphabet, new_states, new_start_state, new_transitions, new_final_states)

    def _create_new_states(self, existing_states, new_start, new_final) -> set:
        return existing_states.union({new_start, new_final})

    def _create_new_alphabet(self, existing_alphabet) -> set:
        return existing_alphabet.union({EPSILON})

    def _create_new_transitions(self, inner_nfa, new_start, new_final) -> dict:
        transitions = inner_nfa.d.copy()
        transitions[(new_start, EPSILON)] = {inner_nfa.q0, new_final}

        for final_state in inner_nfa.F:
            existing_transitions = transitions.get((final_state, EPSILON), set())
            existing_transitions.update({new_final, inner_nfa.q0})
            transitions[(final_state, EPSILON)] = existing_transitions

        return transitions


class Plus(Regex):
    def __init__(self, regex):
        self.regex = regex

    def thompson(self) -> NFA[int]:
        nfa = self.regex.thompson()

        # New start_state and accept_state
        new_start_state = max(nfa.K) + 1
        new_accept_state = max(nfa.K) + 2

        # Epsilon transitions from the final states of the old NFA to the new accept state
        transitions = {(final_state, EPSILON): {new_start_state, new_accept_state} for final_state in nfa.F}
        transitions.update(nfa.d)

        # New epsilon transitions from the new start state to the old start state
        transitions[(new_start_state, EPSILON)] = {nfa.q0}

        return NFA(nfa.S, nfa.K.union({new_start_state, new_accept_state}), new_start_state, transitions, {new_accept_state})


class Optional(Regex):
    def __init__(self, regex):
        super().__init__()  # Initialize the parent class
        self.regex = regex

    def thompson(self) -> NFA[int]:
        # Construiește NFA-ul pentru regex-ul actual
        base_nfa = self.regex.thompson()

        # Creați un nou NFA pentru regex-ul opțional
        # Includeți toate stările și tranzitiile din NFA-ul de bază
        new_states = base_nfa.K
        new_transitions = base_nfa.d
        new_alphabet = base_nfa.S

        # Starea inițială a noului NFA este starea inițială a NFA-ului de bază
        new_initial_state = base_nfa.q0

        # Stările de acceptare includ stările de acceptare ale NFA-ului de bază
        # plus starea inițială, deoarece regex-ul este opțional
        new_accept_states = base_nfa.F | {new_initial_state}

        # Returnează noul NFA
        return NFA(new_alphabet, new_states, new_initial_state, new_transitions, new_accept_states)



def process_regular_and_escape_characters(char, regex, i, expression_elements, operations, is_previous_element):
    if is_previous_element:
        operations.append('.') # adaugam operatia de concatenare
    is_previous_element = True

    if char == '\\' and i + 1 < len(regex): # daca avem un caracter de escape
        i += 1  # trecem peste caracterul de escape
        char = regex[i] # luam urmatorul caracter

    expression_elements.append(Caracter(char)) # adaugam caracterul in lista de elemente
    return i + 1, is_previous_element # returnam pozitia urmatorului caracter si daca este sau nu un caracter precedent

def process_special_characters(char, regex, i, expression_elements, operations, is_previous_element):
    if char == '(':
        if is_previous_element:
            operations.append('.') # adaugam operatia de concatenare
        operations.append('(') # adaugam paranteza deschisa
        is_previous_element = False # resetare stare caracter precedent
        i += 1
    elif char == ')':
        while operations[-1] != '(':
            operation = operations.pop() # scoatem operatia dinn stiva
            element2 = expression_elements.pop() # scoatem primul element din lista de elemente
            element1 = expression_elements.pop() # scoatem al doilea element din lista de elemente
            if operation == '|':
                expression_elements.append(Union(element1, element2))
            else:
                expression_elements.append(Concat(element1, element2))
        operations.pop() # scoatem paranteza deschisa din stiva
        is_previous_element = True # resetare stare caracter precedent
        i += 1
        # comtinuare restul functiei pentru alte caractere speciale
    elif char in ['*', '+', '?']:
        el = expression_elements.pop()
        if char == '*':
            expression_elements.append(Star(el))
        elif char == '+':
            expression_elements.append(Plus(el))
        else:
            expression_elements.append(Optional(el))
        is_previous_element = True
        i += 1
    elif char == '|':
        while operations and operations[-1] == '.':
            operations.pop()
            element2 = expression_elements.pop()
            element1 = expression_elements.pop()
            expression_elements.append(Concat(element1, element2))
        operations.append('|')
        is_previous_element = False
        i += 1
    elif char == '[':
        if is_previous_element:
            operations.append('.')
        closing_bracket_pos = regex.find(']', i)
        if closing_bracket_pos != -1 and closing_bracket_pos > i + 2:
            range_str = regex[i + 1:closing_bracket_pos]
            if range_str == 'a-z':
                expression_elements.append(SmallLetters())
            elif range_str == 'A-Z':
                expression_elements.append(BigLetters())
            elif range_str == '0-9':
                expression_elements.append(Digits())
            else:
                raise ValueError("Error in range expression")
            i = closing_bracket_pos + 1
            is_previous_element = True
        else:
            raise ValueError("Error")
    return i, is_previous_element

def parse_regex(regex: str) -> Regex:
    # parseaza o expresie regulata si construieste un arbore corespunzator acesteia
    expression_elements, operations = [], [] # initializare stive pentru eleemente si operatii
    is_previous_element = False
    i = 0 # index pentru parcurgerea expresiei regulate
    special_characters = ['*', '+', '?', '|', '(', ')', '[', ']']

    while i < len(regex):
        # ignoram spatiile din expresia regulata
        if regex[i] == ' ':
            i += 1
            continue
        if regex[i] not in special_characters:
            i, is_previous_element = process_regular_and_escape_characters(regex[i], regex, i, expression_elements, operations, is_previous_element)
        else:
            i, is_previous_element = process_special_characters(regex[i], regex, i, expression_elements, operations, is_previous_element)
    # procesare orice operatie ramasa in stiva pentru a completa arborele
    while operations:
        operation = operations.pop() # scoatem operatia din stiva

        element2 = expression_elements.pop()
        element1 = expression_elements.pop()
        if operation == '|':
            expression_elements.append(Union(element1, element2))
        else:
            expression_elements.append(Concat(element1, element2))

    return expression_elements[0] # returneaza arborele construit


