from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
import simpn.prototypes as prototype
from simpn.reporters import ProcessReporter
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
call_terminated = agency.add_var("call_terminated")
accepted_offer = agency.add_var("accepted")
rejected_offer = agency.add_var("rejected")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
def new_call():
    return [SimToken({'is_new': 1})] #tokens with value 1 are new customers, tokens with value 0 are returning customers

prototype.BPMNStartEvent(agency, [], [waiting], "arrive", interarrival_time= lambda: exp(7)*60, behavior=new_call)

prototype.BPMNTask(agency, [waiting, employee], [call_terminated, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

def choose_offer(c):
    token_value = c[1] #c[0] contains the token ID, c[1] the token value (in this case, a dictionary with key 'is_new')
    if token_value['is_new'] == 1: # new call
        choose_now = uniform(0, 1) > 0.6 # 40% of the new calls accept or reject immediately
        if choose_now:
            accept = uniform(0, 1) > 0.7 # 30% of the new calls accept
            if accept:
                return [None, SimToken(c), None] #the queue must be returned even if not changed, a new token is created in accepted_offer, no new tokens in rejected_offer
            else:
                return [None, None, SimToken(c)]
        else: # if the customer does not choose immediately, it is put in the queue
            is_new = 0 # the customer is not new anymore
            new_token_value = (c[0], {'is_new': is_new}) #the customer is not new anymore (but its ID stays unchanged): c[0] contains the token ID (necessary to keep track of the various times in the ProcessReporter), while c[1] is modified
            #NOTE: c[1] CAN'T BE MODIFIED DIRECTLY! It is necessary to create a new token with the modified value
            new_token_delay = uniform(30, 60) # the customer is delayed with a uniform random variable beteween 30 and 60
            return [SimToken(value=new_token_value, delay=new_token_delay), None, None]
    else: # returning call
        accept = uniform(0, 1) > 0.75 # 25% of the returning calls accept
        if accept:
            return [None, SimToken(c), None] # put the token in accepted_offer
        else:
            return [None, None, SimToken(c)] # put the token in rejected_offer

agency.add_event([call_terminated], [waiting, accepted_offer, rejected_offer], behavior=choose_offer, name="choose_offer")

prototype.BPMNEndEvent(agency, [accepted_offer], [], "accept")
prototype.BPMNEndEvent(agency, [rejected_offer], [], "reject")

# Simulate once with a visualisation.
my_reporter = ProcessReporter()

agency.simulate(1000, my_reporter)

my_reporter.print_result()