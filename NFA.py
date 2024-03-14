from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs


@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # Calculeaza inchiderea epsilon a unei stari intr-un automat finit nedeterminist (NFA).
        # Inchiderea epsilon a unei stari include starea insasi si toate starile accesibile
        # prin tranzitii epsilon (tranzitii care nu consuma niciun simbol de intrare).

        closure, stack = set(), [state]  # Initializeaza inchiderea si stiva cu starea data.

        while stack:
            current = stack.pop()  # Scoate o stare din stiva.
            closure.add(current)  # Adauga starea scoasa in inchiderea epsilon.

            # Verifica daca exista tranzitii epsilon pentru starea curenta si adauga starile accesibile in stiva.
            if (current, EPSILON) in self.d:
                epsilon_transitions = self.d[(current, EPSILON)]  # Obtine tranzitiile epsilon.
                for epsilon_state in epsilon_transitions:
                    # Daca starea accesata prin tranzitia epsilon nu este in inchidere, adauga-o in stiva.
                    if epsilon_state not in closure:
                        stack.append(epsilon_state)
        return closure

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # Converteste acest NFA intr-un DFA (Automat Finit Determinist) folosind algoritmul de constructie a subseturilor.
        dfa_states = set()  # Initializeaza starile DFA.
        dfa_delta = {}  # Initializeaza functia de tranzitie DFA.
        dfa_initial = frozenset(self.epsilon_closure(self.q0))  # Calculeaza starea initiala DFA.
        dfa_states.add(dfa_initial)
        stack = [dfa_initial]
        alfabet = self.S - {EPSILON}  # Excludem tranzitiile epsilon din alfabet.
        function = self.d  # Functia de tranzitie a NFA.

        while stack:
            current = stack.pop()  # Scoate o stare DFA din stiva.
            for symbol in alfabet:
                next_states = set()  # Initializeaza starile urmatoare.
                for state in current:
                    couple = (state, symbol)
                    if couple in function:
                        # Pentru fiecare tranzitie valida, calculeaza inchiderea epsilon si actualizeaza starile urmatoare.
                        for state in function[(state, symbol)]:
                            epsilon_closure = self.epsilon_closure(state)
                            next_states.update(epsilon_closure)

                next_states = frozenset(next_states)

                # Daca starile urmatoare nu sunt in DFA, adauga-le si pune-le in stiva.
                stack.extend(
                    [next_states] * (dfa_states.add(next_states) or True) if next_states not in dfa_states else [])

                dfa_delta[(current, symbol)] = next_states  # Actualizeaza functia de tranzitie DFA.
            dfa_final_states = {state for state in dfa_states if state & self.F}  # Calculeaza starile finale DFA.

        return DFA(self.S, dfa_states, dfa_initial, dfa_delta, dfa_final_states)

    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        pass
