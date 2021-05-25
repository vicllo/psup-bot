from dataclasses import *

all_event_kinds = {"Accepted": AcceptEvent,
                   "UserRefused": UserRefuseEvent,
                   "SchoolRefused": SchoolRefuseEvent,
                   "Waiting": WaitingListEvent,
                   "Proposition": PropositionEvent}