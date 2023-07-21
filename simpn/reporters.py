class Reporter:
    """
    A reporter can be passed to the simpn.simulator.SimProblem.simulate function to report on what happens during the simulator.
    To this end, a reported must implement the callback function.
    """
    def callback(self, timed_binding):
        """
        A function that is invoked by a simpn.simulator.SimProblem each time a event happened.
        It receives a timed_binding, which is a triple (binding, time, event):
        - binding = [(v1: SimVar, t1: SimToken), (v2: SimVar, t2: SimToken), ...] of the variable values that caused the event.
        - time is the simulation time at which the event happened.
        - event: SimEvent is the event that happened.

        :param timed_binding: the triple (binding, time, event) that described the event that happened with its variable values and the time at which it happened.
        """
        raise NotImplementedError


class SimpleReporter(Reporter):
    """
    A simple reporter that just prints the occurring events to the standard output.
    """
    def callback(self, timed_binding):
        result = str(timed_binding[2]) + "{"
        i = 0
        for var, token in timed_binding[0]:
            result += str(var) + ": " + str(token.value)
            if i < len(timed_binding[0])-1:
                result += ", "
            i += 1
        result += "}" + "@t=" + str(timed_binding[1])
        print(result)


class ProcessReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events. It measures:
    - the number of started cases
    - the number of completed cases
    - the cycle time of completed cases (the time between their start and end event)
    - the processing time of completed cases (the time between a case's start and end during which a task was being performed)
    - the waiting time of completed cases (the time between a case's start and end during which no task was being performed)
    """

    def __init__(self):
        self.status = dict()  # case_id -> (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change); time_last_busy_change is the time nr_busy_tasks last went from 0 to 1 or from 1 to 0
        self.nr_started = 0
        self.nr_completed = 0
        self.total_wait_time = 0  # only of completed cases
        self.total_proc_time = 0  # only of completed cases
        self.total_cycle_time = 0  # only of completed cases

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.status[case_id] = (0, time, 0, 0, time)
            self.nr_started += 1
        elif event.get_id().endswith("<task:start>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            if nr_busy_tasks == 0:
                sum_wait_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks += 1
            self.status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            if nr_busy_tasks == 1:
                sum_proc_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks -= 1
            self.status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            del self.status[case_id]
            self.nr_completed += 1
            self.total_wait_time += sum_wait_times
            self.total_proc_time += sum_proc_times
            self.total_cycle_time += time - arrival_time

    def print_result(self):
        print("Nr. cases started:            ", self.nr_started)
        print("Nr. cases completed:          ", self.nr_completed)
        print("Avg. waiting time per case:   ", round(self.total_wait_time/self.nr_completed, 3))
        print("Avg. processing time per case:", round(self.total_proc_time/self.nr_completed, 3))
        print("Avg. cycle time per case:     ", round(self.total_cycle_time/self.nr_completed, 3))
